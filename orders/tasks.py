from celery import shared_task
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from core.email_utils import send_email


@shared_task(bind=True, max_retries=3)
def send_order_confirmation_email_task(self, order_id):
    """Async task to send order confirmation email."""
    try:
        from orders.models import Order
        order = Order.objects.get(id=order_id)
        
        subject = f'Order Confirmed - {order.order_number}'
        
        html_message = render_to_string('emails/order_status.html', {
            'order': order,
            'status': 'SCHEDULED',
        })
        
        plain_message = strip_tags(html_message)
        
        send_email(
            recipient=order.email,
            subject=subject,
            body_text=plain_message,
            body_html=html_message,
            quiet=False,
        )
        
        return f'Order confirmation email sent for {order.order_number}'
        
    except Exception as exc:
        # Retry after 30 seconds, 60 seconds, 120 seconds
        raise self.retry(exc=exc, countdown=30 * (2 ** self.request.retries))


@shared_task(bind=True, max_retries=3)
def send_order_status_email_task(self, order_id):
    """Async task to send order status update email."""
    try:
        from orders.models import Order
        order = Order.objects.get(id=order_id)
        
        subject = f'Order Update - {order.order_number}'
        
        html_message = render_to_string('emails/order_status.html', {
            'order': order,
            'status': order.status,
        })
        
        plain_message = strip_tags(html_message)
        
        send_email(
            recipient=order.email,
            subject=subject,
            body_text=plain_message,
            body_html=html_message,
            quiet=False,
        )
        
        return f'Status update email sent for {order.order_number}'
        
    except Exception as exc:
        raise self.retry(exc=exc, countdown=30 * (2 ** self.request.retries))


@shared_task(bind=True, max_retries=3)
def send_delivery_code_email_task(self, order_id, delivery_code):
    """Async task to send delivery verification code email."""
    try:
        from orders.models import Order
        order = Order.objects.get(id=order_id)
        
        subject = f'Delivery Code - {order.order_number}'
        
        html_message = render_to_string('emails/delivery_code.html', {
            'order': order,
            'delivery_code': delivery_code,
        })
        
        plain_message = strip_tags(html_message)
        
        send_email(
            recipient=order.email,
            subject=subject,
            body_text=plain_message,
            body_html=html_message,
            quiet=False,
        )
        
        return f'Delivery code email sent for {order.order_number}'
        
    except Exception as exc:
        raise self.retry(exc=exc, countdown=30 * (2 ** self.request.retries))


@shared_task(bind=True, max_retries=3)
def send_admin_notification_task(self, order_id):
    """Async task to send new order notification to admin."""
    try:
        from orders.models import Order
        order = Order.objects.get(id=order_id)
        
        subject = f'New Order - {order.order_number}'
        
        # Build services list
        services_list = []
        for item in order.items.all():
            service_str = f"  - {item.service.name}"
            if item.quantity > 1:
                service_str += f" (x{item.quantity})"
            service_str += f" - ₦{item.subtotal}"
            services_list.append(service_str)
        
        services_text = "\n".join(services_list) if services_list else "  - No services"
        
        message = f"""
New order received:

Order #: {order.order_number}
Customer: {order.full_name} ({order.email})

Services:
{services_text}

Location: {order.get_location_display()}
Pickup Date: {order.pickup_date}
Subtotal: ₦{order.subtotal}
VAT: ₦{order.vat}
Delivery: ₦{order.delivery_fee}
{'Discount: -₦' + str(order.discount_amount) if order.discount_amount > 0 else ''}
Total: ₦{order.total_amount}
{'🎉 FREE CLEANING (15th Order)' if order.is_free_cleaning else ''}

Address: {order.address}
Phone: {order.phone}

{'=' * 50}
Special Instructions: {order.special_instructions or 'None'}
"""
        
        send_email(
            recipient=settings.ADMIN_EMAIL,
            subject=subject,
            body_text=message,
            body_html=f'<pre>{message}</pre>',
            quiet=True,
        )
        
        return f'Admin notification sent for {order.order_number}'
        
    except Exception as exc:
        # Don't retry admin emails as aggressively
        if self.request.retries < 1:
            raise self.retry(exc=exc, countdown=60)
        return f'Admin notification failed after retries for order {order_id}'


@shared_task(bind=True, max_retries=3)
def send_rating_request_email_task(self, order_id):
    """Async task to send rating request email after delivery."""
    try:
        from orders.models import Order
        order = Order.objects.get(id=order_id)
        
        subject = f'Rate Your Experience - {order.order_number}'
        
        html_message = render_to_string('emails/rating_request.html', {
            'order': order,
        })
        
        plain_message = strip_tags(html_message)
        
        send_email(
            recipient=order.email,
            subject=subject,
            body_text=plain_message,
            body_html=html_message,
            quiet=False,
        )
        
        return f'Rating request email sent for {order.order_number}'
        
    except Exception as exc:
        raise self.retry(exc=exc, countdown=30 * (2 ** self.request.retries))


@shared_task(bind=True, max_retries=3)
def send_otp_email_task(self, user_id, otp_code):
    """Async task to send OTP email for login."""
    try:
        from accounts.models import User
        user = User.objects.get(id=user_id)
        
        subject = 'Your Sneaky Klean Login Code'
        
        html_message = render_to_string('accounts/otp_email.html', {
            'user': user,
            'otp_code': otp_code,
        })
        
        plain_message = strip_tags(html_message)
        
        send_email(
            recipient=user.email,
            subject=subject,
            body_text=plain_message,
            body_html=html_message,
            quiet=False,
        )
        
        return f'OTP email sent to {user.email}'
        
    except Exception as exc:
        raise self.retry(exc=exc, countdown=10 * (2 ** self.request.retries))
