from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
from core.email_utils import send_email


def send_order_confirmation_email(order):
    """Send order confirmation email to customer using ZeptoMail API."""
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


def send_order_status_email(order):
    """Send order status update email to customer using ZeptoMail API."""
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


def send_delivery_code_email(order, delivery_code):
    """Send delivery verification code to customer using ZeptoMail API."""
    subject = f'Delivery Code - {order.order_number}'
    
    html_message = render_to_string('emails/delivery_code.html', {
        'order': order,
        'delivery_code': delivery_code.code,
    })
    
    plain_message = strip_tags(html_message)
    
    send_email(
        recipient=order.email,
        subject=subject,
        body_text=plain_message,
        body_html=html_message,
        quiet=False,
    )


def send_admin_notification(order):
    """Send new order notification to admin using ZeptoMail API."""
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
        quiet=True,  # Don't fail order creation if admin email fails
    )


def send_rating_email(order):
    """Send rating request email after delivery using ZeptoMail API."""
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
