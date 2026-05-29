# Email Migration: SMTP to ZeptoMail API

## Overview

The email system has been migrated from Django's SMTP backend to ZeptoMail's REST API for improved reliability, deliverability, and monitoring capabilities.

## Changes Made

### 1. New Email Utility Module
**File**: `core/email_utils.py`

Created a comprehensive ZeptoMail API client with:
- `send_zeptomail_email()`: Main API function with full features
- `send_email()`: Simplified public interface
- Helper functions for parsing recipients, attachments, body content
- Error handling with quiet/verbose modes
- Logging support for debugging
- Base64 encoding for attachments

### 2. Updated Email Functions

#### `accounts/emails.py`
- Replaced `django.core.mail.send_mail` with `core.email_utils.send_email`
- Updated `send_otp_email()` to use ZeptoMail API

#### `orders/emails.py`
- Migrated all email functions to ZeptoMail API:
  - `send_order_confirmation_email()`
  - `send_order_status_email()`
  - `send_delivery_code_email()`
  - `send_admin_notification()`
  - `send_rating_email()`

### 3. Configuration Changes

#### `sneakyklean/settings.py`
**Removed**:
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.zoho.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
```

**Added**:
```python
ZEPTO_API_KEY = config('ZEPTO_API_KEY', default='')
ZEPTO_API_BASE_URL = config('ZEPTO_API_BASE_URL', default='https://api.zeptomail.com/v1.1')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='Sneaky Klean <noreply@sneakyklean.com>')
```

#### `.env.example`
**Removed**:
```env
EMAIL_HOST=smtp.zoho.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@yourdomain.com
EMAIL_HOST_PASSWORD=your-email-password
EMAIL_USE_TLS=True
```

**Added**:
```env
ZEPTO_API_KEY=your-zeptomail-api-key-here
ZEPTO_API_BASE_URL=https://api.zeptomail.com/v1.1
DEFAULT_FROM_EMAIL=Sneaky Klean <noreply@sneakyklean.com>
```

### 4. Dependencies

#### `requirements.txt`
**Added**:
```
requests==2.31.0
```

## Setup Instructions

### Step 1: Install Dependencies

If running locally:
```bash
pip install requests==2.31.0
```

For Docker (automatic on rebuild):
```bash
docker-compose build
```

### Step 2: Configure ZeptoMail

1. **Create ZeptoMail Account**
   - Visit: https://www.zoho.com/zeptomail/
   - Sign up for free tier (10,000 emails/month)

2. **Create Mail Agent**
   - Go to Settings > Mail Agents
   - Create new mail agent
   - Copy API key

3. **Verify Domain** (Production)
   - Add your domain in Sending Domains
   - Add SPF and DKIM DNS records
   - Wait for verification (24-48 hours)

4. **Update .env File**
   ```bash
   cp .env.example .env
   ```
   
   Update these values:
   ```env
   ZEPTO_API_KEY=your-actual-api-key-from-zeptomail
   ZEPTO_API_BASE_URL=https://api.zeptomail.com/v1.1
   DEFAULT_FROM_EMAIL=Sneaky Klean <noreply@yourdomain.com>
   ```

### Step 3: Test Email Sending

```bash
# Start containers
docker-compose up -d

# Access Django shell
docker-compose run --rm web python manage.py shell
```

In the shell:
```python
from core.email_utils import send_email

# Test email
send_email(
    recipient='your-email@example.com',
    subject='Test Email',
    body_text='This is a test email from Sneaky Klean',
    body_html='<h1>Test Email</h1><p>This is a test email from Sneaky Klean</p>',
    quiet=False
)
```

Check your inbox for the test email.

## API Advantages Over SMTP

### 1. Reliability
- No SMTP connection timeouts
- Automatic retry handling
- Better rate limiting

### 2. Deliverability
- Higher inbox placement
- Built-in SPF/DKIM signing
- ISP reputation management

### 3. Monitoring
- Real-time delivery tracking
- Bounce and complaint notifications
- Detailed logs and analytics

### 4. Performance
- Faster sending (no SMTP handshake)
- Connection pooling
- Bulk sending support

### 5. Security
- API key authentication (no password storage)
- TLS encryption by default
- IP whitelisting available

## Email Functions Reference

### `send_email(recipient, subject, body_text, body_html, attachments, quiet)`
**Simplified interface for sending emails**

Parameters:
- `recipient`: String or list of email addresses
- `subject`: Email subject line
- `body_text`: Plain text body (auto-generated from HTML if not provided)
- `body_html`: HTML body
- `attachments`: Optional list of tuples `[(filename, bytes, mimetype), ...]`
- `quiet`: If True, log errors but don't raise exceptions (default: True)

Returns: API response dict or None on failure

### `send_zeptomail_email(...)`
**Full-featured API function with all options**

Same parameters as `send_email()` plus:
- Automatic recipient parsing (supports "Name <email@domain.com>" format)
- Base64 attachment encoding
- HTML/text body normalization
- Comprehensive error handling

## Error Handling

### API Errors
All API errors are logged with details:
```
ZeptoMail API error: 400 {"error": "Invalid recipient"}
```

### Configuration Errors
Missing configuration is logged:
```
ZeptoMail API not configured (ZEPTO_API_KEY / ZEPTO_API_BASE_URL missing)
```

### Network Errors
Connection issues are captured:
```
Error sending email via ZeptoMail API: ConnectionError(...)
```

## Testing Checklist

- [ ] OTP email (login flow)
- [ ] Order confirmation email
- [ ] Order status update emails
- [ ] Delivery code email (when status = OUT_FOR_DELIVERY)
- [ ] Admin notification emails
- [ ] Rating request emails (after delivery)

## Rollback Instructions

If you need to revert to SMTP:

1. **Restore settings.py**
   ```python
   EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
   EMAIL_HOST = config('EMAIL_HOST', default='smtp.zoho.com')
   EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
   EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
   EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
   EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
   ```

2. **Update email functions** to use `send_mail`:
   ```python
   from django.core.mail import send_mail
   
   send_mail(
       subject=subject,
       message=plain_message,
       from_email=settings.DEFAULT_FROM_EMAIL,
       recipient_list=[recipient],
       html_message=html_message,
       fail_silently=False,
   )
   ```

3. **Restore .env variables**
   ```env
   EMAIL_HOST=smtp.zoho.com
   EMAIL_PORT=587
   EMAIL_HOST_USER=your-email@yourdomain.com
   EMAIL_HOST_PASSWORD=your-email-password
   EMAIL_USE_TLS=True
   ```

## Support

For ZeptoMail issues:
- Documentation: https://www.zoho.com/zeptomail/help/
- Support: https://help.zoho.com/portal/en/home
- Status: https://status.zoho.com/

For application issues:
- Check logs: `docker-compose logs -f web`
- Test in Django shell
- Verify API key configuration
