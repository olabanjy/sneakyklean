from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Q
from decimal import Decimal
from datetime import datetime
from .models import Service, Order, OrderItem, DiscountCode, Rating
from .tasks import send_order_confirmation_email_task, send_admin_notification_task
from accounts.models import User


@login_required
def dashboard_view(request):
    """User dashboard showing orders and metrics."""
    user = request.user
    orders = Order.objects.filter(user=user).order_by('-created_at')
    notifications = orders.order_by('-updated_at')[:8]
    
    # Calculate metrics
    total_orders = user.total_orders
    pending_orders = orders.filter(status__in=['SCHEDULED', 'PICKED_UP', 'CLEANING', 'OUT_FOR_DELIVERY']).count()
    free_cleaning_progress = user.free_cleaning_count
    
    context = {
        'orders': orders,
        'notifications': notifications,
        'user': user,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'free_cleaning_progress': free_cleaning_progress,
    }
    
    return render(request, 'orders/dashboard.html', context)


@require_http_methods(["POST"])
def create_order_view(request):
    """Create a new order from booking form with services from database."""
    redirect_target = 'orders:dashboard' if request.user.is_authenticated else 'core:index'

    try:
        # Get form data
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()
        location = request.POST.get('location', '')
        pickup_date_str = request.POST.get('pickup_date', '')
        special_instructions = request.POST.get('instructions', '').strip()
        discount_code = request.POST.get('discount_code', '').strip().upper()

        # An authenticated booking must always belong to the signed-in account.
        # Do not trust editable/hidden identity fields sent by the browser.
        if request.user.is_authenticated:
            email = request.user.email
            full_name = request.user.full_name or full_name or request.user.get_short_name()
            phone = request.user.phone or phone
        
        # Get selected service IDs and quantities (can be multiple services)
        service_ids = request.POST.getlist('service_ids[]')  # Array of service IDs
        service_quantities = request.POST.getlist('service_quantities[]')  # Corresponding quantities
        
        # Fallback: single service from 'services' field (for backward compatibility)
        if not service_ids:
            services_str = request.POST.get('services', '').strip()
            if services_str:
                # Map service names to IDs from database
                service_names = [s.strip() for s in services_str.split(',')]
                services_by_name = {
                    service.name: service
                    for service in Service.objects.filter(name__in=service_names, is_active=True)
                }
                # Keep the browser's selection order aligned with its quantities.
                services = [
                    services_by_name[name]
                    for name in service_names
                    if name in services_by_name
                ]
                service_ids = [str(s.id) for s in services]
                if not service_quantities:
                    quantity = request.POST.get('quantity', '1')
                    service_quantities = [quantity] * len(service_ids)
        
        # Validate required fields
        required_fields = [full_name, email, address, location, pickup_date_str]
        if not request.user.is_authenticated:
            required_fields.append(phone)

        if not all(required_fields) or not service_ids:
            messages.error(request, 'Please fill in all required fields and select at least one service.')
            return redirect(redirect_target)
        
        # Parse pickup date
        try:
            pickup_date = datetime.strptime(pickup_date_str, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, 'Invalid pickup date format.')
            return redirect(redirect_target)

        if pickup_date < timezone.localdate():
            messages.error(request, 'Pickup date cannot be in the past.')
            return redirect(redirect_target)
        
        # Get or create user
        if request.user.is_authenticated:
            user = request.user
            created = False
        else:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'full_name': full_name,
                    'phone': phone
                }
            )
        
        # Update user info if exists
        if not created:
            if not user.full_name:
                user.full_name = full_name
            if not user.phone:
                user.phone = phone
            user.save()
        
        # Fetch selected services from database
        selected_services = []
        subtotal = Decimal('0')
        
        for i, service_id in enumerate(service_ids):
            try:
                service = Service.objects.get(id=int(service_id), is_active=True)
                quantity = int(service_quantities[i]) if i < len(service_quantities) else 1
                
                if quantity < 1:
                    quantity = 1
                
                item_subtotal = service.price * quantity
                subtotal += item_subtotal
                
                selected_services.append({
                    'service': service,
                    'quantity': quantity,
                    'subtotal': item_subtotal
                })
            except (Service.DoesNotExist, ValueError, IndexError):
                continue
        
        if not selected_services:
            messages.error(request, 'No valid services selected.')
            return redirect(redirect_target)
        
        # Calculate pricing
        vat = subtotal * Decimal('0.075')  # 7.5% VAT
        delivery_fee = Decimal('3500')
        discount_amount = Decimal('0')
        
        # Apply discount code
        if discount_code:
            try:
                discount = DiscountCode.objects.get(code=discount_code)
                if discount.is_valid():
                    discount_amount = discount.discount_amount
                    discount.times_used += 1
                    discount.save()
            except DiscountCode.DoesNotExist:
                pass
        
        # Check if this is the 15th order for free cleaning
        is_free = user.free_cleaning_count >= 14
        
        if is_free:
            total_amount = Decimal('0')  # Free cleaning!
        else:
            total_amount = subtotal + vat + delivery_fee - discount_amount
            if total_amount < 0:
                total_amount = Decimal('0')
        
        # Create order
        order = Order.objects.create(
            user=user,
            service_type=selected_services[0]['service'].name,
            quantity=sum(item['quantity'] for item in selected_services),
            full_name=full_name,
            email=email,
            phone=phone,
            address=address,
            location=location,
            pickup_date=pickup_date,
            subtotal=subtotal,
            vat=vat,
            delivery_fee=delivery_fee,
            discount_amount=discount_amount,
            total_amount=total_amount,
            special_instructions=special_instructions,
            is_free_cleaning=is_free,
        )
        
        # Create OrderItem records for each service
        for service_data in selected_services:
            OrderItem.objects.create(
                order=order,
                service=service_data['service'],
                quantity=service_data['quantity'],
                # service_name and price_at_order auto-populated in model save()
            )
        
        # Update user free cleaning counter
        if is_free:
            user.free_cleaning_count = 0  # Reset counter
        else:
            user.free_cleaning_count += 1
        
        user.total_orders += 1
        user.save()
        
        # Send confirmation emails asynchronously using Celery
        try:
            send_order_confirmation_email_task.delay(order.id)
            send_admin_notification_task.delay(order.id)
        except Exception as e:
            print(f"Failed to queue emails: {e}")
        
        messages.success(request, f'Order {order.order_number} created successfully! Check your email for confirmation.')
        if request.user.is_authenticated:
            return redirect('orders:dashboard')
        return redirect('accounts:login')
        
    except Exception as e:
        messages.error(request, f'Failed to create order: {str(e)}')
        return redirect(redirect_target)


@require_http_methods(["GET", "POST"])
def rate_order_view(request, order_id):
    """Rate an order after delivery."""
    order = get_object_or_404(Order, id=order_id)
    
    # Check if order is delivered
    if order.status != 'DELIVERED':
        messages.error(request, 'You can only rate delivered orders.')
        return redirect('orders:dashboard')
    
    # Check if already rated
    if hasattr(order, 'rating'):
        messages.info(request, 'You have already rated this order.')
        return redirect('orders:dashboard')
    
    if request.method == 'POST':
        rating_value = int(request.POST.get('rating', 0))
        
        if 1 <= rating_value <= 5:
            Rating.objects.create(
                order=order,
                rating=rating_value
            )
            messages.success(request, 'Thank you for your feedback!')
            return redirect('orders:dashboard')
        else:
            messages.error(request, 'Invalid rating value.')
    
    return render(request, 'orders/rating.html', {'order': order})


@require_POST
@login_required
def quick_rate_order_view(request, order_id):
    """AJAX endpoint for quick rating from dashboard."""
    try:
        order = get_object_or_404(Order, id=order_id, user=request.user)
        
        # Check if order is delivered
        if order.status != 'DELIVERED':
            return JsonResponse({
                'success': False,
                'message': 'You can only rate delivered orders.'
            })
        
        # Check if already rated
        if hasattr(order, 'rating'):
            return JsonResponse({
                'success': False,
                'message': 'You have already rated this order.'
            })
        
        rating_value = int(request.POST.get('rating', 0))
        
        if not (1 <= rating_value <= 5):
            return JsonResponse({
                'success': False,
                'message': 'Rating must be between 1 and 5 stars.'
            })
        
        # Create rating
        Rating.objects.create(
            order=order,
            rating=rating_value
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Thank you for your feedback!',
            'rating': rating_value
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@require_POST
@login_required
def cancel_order_request_view(request, order_id):
    """Request order cancellation."""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Check if order can be cancelled
    if order.status in ['DELIVERED', 'CANCELED']:
        return JsonResponse({
            'success': False,
            'message': 'This order cannot be cancelled.'
        })
    
    if order.cancellation_requested:
        return JsonResponse({
            'success': False,
            'message': 'Cancellation already requested for this order.'
        })
    
    reason = request.POST.get('reason', '').strip()
    
    order.cancellation_requested = True
    order.cancellation_reason = reason
    order.cancellation_requested_at = timezone.now()
    order.save()
    
    return JsonResponse({
        'success': True,
        'message': 'Cancellation request submitted. Admin will review shortly.'
    })


@require_http_methods(["POST"])
def validate_discount_view(request):
    """AJAX endpoint to validate discount code."""
    code = request.POST.get('code', '').strip().upper()
    
    if not code:
        return JsonResponse({
            'valid': False,
            'message': 'Please enter a discount code.'
        })
    
    try:
        discount = DiscountCode.objects.get(code=code)
        
        if discount.is_valid():
            return JsonResponse({
                'valid': True,
                'discount_amount': float(discount.discount_amount),
                'message': f'Discount code applied: ₦{discount.discount_amount}'
            })
        else:
            return JsonResponse({
                'valid': False,
                'message': 'This discount code has expired or reached its usage limit.'
            })
            
    except DiscountCode.DoesNotExist:
        return JsonResponse({
            'valid': False,
            'message': 'Invalid discount code.'
        })


@require_http_methods(["GET"])
def services_api_view(request):
    """API endpoint to fetch active services for frontend."""
    services = Service.objects.filter(is_active=True).order_by('display_order', 'name')
    
    services_data = []
    for service in services:
        services_data.append({
            'id': service.id,
            'name': service.name,
            'description': service.description,
            'price': float(service.price),
            'icon': service.icon,
            'estimated_duration': service.estimated_duration,
        })
    
    return JsonResponse(services_data, safe=False)
