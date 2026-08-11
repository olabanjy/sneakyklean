from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.core.cache import cache
from django.utils import timezone
from django.http import JsonResponse
from .models import User, OTP
from orders.tasks import send_otp_email_task


@require_http_methods(["GET", "POST"])
def login_view(request):
    """Login view - request OTP via email."""
    
    if request.user.is_authenticated:
        return redirect('orders:dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        
        if not email:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'Please enter your email address.'})
            messages.error(request, 'Please enter your email address.')
            return render(request, 'accounts/login.html')
        
        # Check rate limiting - 3 OTPs per email per hour
        cache_key = f'otp_requests_{email}'
        request_count = cache.get(cache_key, 0)
        
        if request_count >= 3:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'Too many OTP requests. Please try again in 1 hour.'})
            messages.error(request, 'Too many OTP requests. Please try again in 1 hour.')
            return render(request, 'accounts/login.html')
        
        # Get or create user
        user, created = User.objects.get_or_create(
            email=email,
            defaults={'full_name': '', 'phone': ''}
        )
        
        # Mark old OTPs as used
        OTP.objects.filter(user=user, is_used=False).update(is_used=True)
        
        # Generate new OTP
        otp_code = OTP.generate_code()
        otp = OTP.objects.create(user=user, code=otp_code)
        
        # Send OTP email asynchronously via Celery
        try:
            send_otp_email_task.delay(user.id, otp_code)
            
            # Increment rate limit counter
            cache.set(cache_key, request_count + 1, timeout=3600)  # 1 hour
            
            # Store email in session for OTP verification
            request.session['otp_email'] = email
            request.session['otp_id'] = otp.id
            
            # Return JSON for AJAX requests
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': f'OTP sent to {email}'})
            
            messages.success(request, f'OTP sent to {email}. Please check your email.')
            return redirect('accounts:verify_otp')
            
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': f'Failed to send OTP: {str(e)}'})
            messages.error(request, f'Failed to send OTP: {str(e)}. Please try again.')
            return render(request, 'accounts/login.html')
    
    return render(request, 'accounts/login.html')


@require_http_methods(["GET", "POST"])
def verify_otp_view(request):
    """Verify OTP and log user in."""
    
    if request.user.is_authenticated:
        return redirect('orders:dashboard')
    
    email = request.session.get('otp_email')
    otp_id = request.session.get('otp_id')
    
    if not email or not otp_id:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Session expired. Please request a new OTP.'})
        messages.error(request, 'Please request a new OTP.')
        return redirect('accounts:login')
    
    if request.method == 'POST':
        entered_code = request.POST.get('otp_code', '').strip()
        
        if not entered_code:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'Please enter the OTP code.'})
            messages.error(request, 'Please enter the OTP code.')
            return render(request, 'accounts/verify_otp.html', {'email': email})
        
        try:
            otp = OTP.objects.get(id=otp_id, user__email=email)
            
            if otp.is_used:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'message': 'This OTP has already been used. Please request a new one.'})
                messages.error(request, 'This OTP has already been used. Please request a new one.')
                return redirect('accounts:login')
            
            if not otp.is_valid():
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'message': 'This OTP has expired. Please request a new one.'})
                messages.error(request, 'This OTP has expired. Please request a new one.')
                return redirect('accounts:login')
            
            if otp.code == entered_code:
                # Mark OTP as used
                otp.is_used = True
                otp.save()
                
                # Log user in
                auth_login(request, otp.user, backend='django.contrib.auth.backends.ModelBackend')
                
                # Clear session data
                del request.session['otp_email']
                del request.session['otp_id']
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': True, 'message': 'Successfully logged in!', 'redirect': '/dashboard/'})
                
                messages.success(request, 'Successfully logged in!')
                return redirect('orders:dashboard')
            else:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'message': 'Invalid OTP code. Please try again.'})
                messages.error(request, 'Invalid OTP code. Please try again.')
                
        except OTP.DoesNotExist:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'Invalid OTP. Please request a new one.'})
            messages.error(request, 'Invalid OTP. Please request a new one.')
            return redirect('accounts:login')
    
    return render(request, 'accounts/verify_otp.html', {'email': email})


@require_http_methods(["POST"])
def resend_otp_view(request):
    """Resend OTP to user's email."""
    email = request.session.get('otp_email')
    
    if not email:
        messages.error(request, 'Session expired. Please start login again.')
        return redirect('accounts:login')
    
    # Check rate limiting - 3 OTPs per email per hour
    cache_key = f'otp_requests_{email}'
    request_count = cache.get(cache_key, 0)
    
    if request_count >= 3:
        messages.error(request, 'Too many OTP requests. Please try again in 1 hour.')
        return redirect('accounts:verify_otp')
    
    try:
        user = User.objects.get(email=email)
        
        # Mark old OTPs as used
        OTP.objects.filter(user=user, is_used=False).update(is_used=True)
        
        # Generate new OTP
        otp_code = OTP.generate_code()
        otp = OTP.objects.create(user=user, code=otp_code)
        
        # Send OTP email asynchronously
        send_otp_email_task.delay(user.id, otp_code)
        
        # Update session with new OTP
        request.session['otp_id'] = otp.id
        
        # Increment rate limit counter
        cache.set(cache_key, request_count + 1, timeout=3600)
        
        messages.success(request, f'New OTP sent to {email}. Please check your email.')
        return redirect('accounts:verify_otp')
        
    except User.DoesNotExist:
        messages.error(request, 'User not found. Please start login again.')
        return redirect('accounts:login')
    except Exception as e:
        messages.error(request, f'Failed to resend OTP: {str(e)}. Please try again.')
        return redirect('accounts:verify_otp')


@login_required
def logout_view(request):
    """Log user out."""
    auth_logout(request)
    messages.success(request, 'Successfully logged out.')
    return redirect('core:index')


@login_required
@require_http_methods(["POST"])
def update_profile_view(request):
    """Update the logged-in user's profile details from the dashboard."""
    user = request.user

    full_name = request.POST.get('full_name', '').strip()
    email = request.POST.get('email', '').strip().lower()
    phone = request.POST.get('phone', '').strip()

    if not email:
        messages.error(request, 'Email is required.')
        return redirect('orders:dashboard')

    if User.objects.exclude(pk=user.pk).filter(email=email).exists():
        messages.error(request, 'That email is already in use by another account.')
        return redirect('orders:dashboard')

    user.full_name = full_name
    user.email = email
    user.phone = phone
    user.save()

    # Keep the session valid after updating the account record.
    update_session_auth_hash(request, user)

    messages.success(request, 'Profile updated successfully.')
    return redirect('orders:dashboard')
