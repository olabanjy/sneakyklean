from django.template.loader import render_to_string
from django.utils.html import strip_tags
from core.email_utils import send_email


def send_otp_email(user, otp_code):
    """
    Send OTP code to user's email for login verification using ZeptoMail API.
    
    Args:
        user: User instance
        otp_code: 6-digit OTP code string
    """
    subject = 'Your Sneaky Klean Login Code'
    
    # Create HTML email from template
    html_message = render_to_string('accounts/otp_email.html', {
        'otp_code': otp_code,
        'user': user,
    })
    
    # Create plain text version
    plain_message = strip_tags(html_message)
    
    # Send email via ZeptoMail API
    send_email(
        recipient=user.email,
        subject=subject,
        body_text=plain_message,
        body_html=html_message,
        quiet=False,
    )
