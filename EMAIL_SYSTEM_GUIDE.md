# EMAIL SYSTEM - COMPLETE GUIDE

## Overview
Emails are automatically sent using the **ZeptoMail API** (not SMTP) for:
1. Order confirmation (when order is created)
2. Order status updates (when admin changes status)
3. Delivery code (when status → OUT_FOR_DELIVERY)
4. Admin notifications (when new order is placed)

---

## 1. Order Confirmation Email

### When Sent
Automatically when a new order is created via the booking form

### Triggered By
`orders/views.py::create_order_view()` - Line 185

### Email Function
`orders/emails.py::send_order_confirmation_email(order)`

### Template
`orders/templates/emails/order_status.html` with `status='SCHEDULED'`

### Content Includes
- ✅ Personalized greeting
- ✅ Order number
- ✅ Services selected (dynamically from OrderItem)
- ✅ Pickup date and location
- ✅ Price breakdown (services, VAT, delivery, discount)
- ✅ Grand total (or "FREE!" for 15th order)
- ✅ Special instructions (if provided)
- ✅ Current status: Scheduled
- ✅ What's next information
- ✅ Dashboard and rating links

---

## 2. Order Status Update Emails

### When Sent
Automatically when an admin changes the order status in Django admin

### Triggered By
Django Signal: `orders/signals.py::order_status_changed()`

### How It Works
1. **Pre-save signal** tracks old status before saving
2. **Post-save signal** compares old vs new status
3. If status changed → sends email automatically

### Email Function
`orders/emails.py::send_order_status_email(order)`

### Template
`orders/templates/emails/order_status.html` with current `status`

### Status-Specific Content

#### SCHEDULED (Order Confirmed)
- **Subject**: Order Confirmed - #20260001
- **Heading**: Order Confirmed! 🎉
- **Message**: Pickup scheduled for [date]
- **What's Next**: We'll pick up your sneakers on the scheduled date

#### PICKED_UP
- **Subject**: Order Update - #20260001
- **Heading**: Your Sneakers Are On Their Way! 👟
- **Message**: Your sneakers are on their way to our facility
- **What's Next**: Our team will start the cleaning process soon

#### CLEANING
- **Subject**: Order Update - #20260001
- **Heading**: We're Cleaning Your Sneakers! ✨
- **Message**: Our experts are carefully restoring your sneakers
- **What's Next**: Once complete, we'll prepare them for delivery

#### OUT_FOR_DELIVERY
- **Subject**: Order Update - #20260001
- **Heading**: Out for Delivery! 🚚
- **Message**: Expected delivery: [date]
- **What's Next**: You'll receive a delivery code when rider is nearby
- **Bonus**: Automatically generates 4-digit delivery code

#### DELIVERED
- **Subject**: Order Update - #20260001
- **Heading**: Delivered! Enjoy Your Fresh Kicks! 🎊
- **Message**: Your fresh sneakers have been delivered!
- **What's Next**: Rate your experience on the dashboard

#### CANCELED
- **Subject**: Order Update - #20260001
- **Heading**: Order Canceled
- **Message**: This order has been canceled
- **Includes**: Cancellation reason (if provided)

#### DELAYED
- **Subject**: Order Update - #20260001
- **Heading**: Order Delayed ⚠️
- **Message**: There's a slight delay with your order
- **What's Next**: We're working to get your order back on track

---

## 3. Delivery Code Email

### When Sent
Automatically when order status changes to **OUT_FOR_DELIVERY**

### Triggered By
Django Signal: `orders/signals.py::order_status_changed()` detects OUT_FOR_DELIVERY

### Process
1. Signal detects status changed to OUT_FOR_DELIVERY
2. Generates 4-digit code (e.g., "7392")
3. Creates DeliveryCode record in database
4. Sends email with code

### Email Function
`orders/emails.py::send_delivery_code_email(order, delivery_code)`

### Template
`orders/templates/emails/delivery_code.html`

### Content
- Order number
- Large 4-digit code (e.g., **7392**)
- Security message: "Do not share before rider arrives"
- Expires when order completed

---

## 4. Admin Notification Email

### When Sent
Automatically when a customer places a new order

### Triggered By
`orders/views.py::create_order_view()` - Line 186

### Recipient
Admin email from `settings.ADMIN_EMAIL`

### Email Function
`orders/emails.py::send_admin_notification(order)`

### Content
```
New order received:

Order #: #20260001
Customer: Jane Doe (jane@example.com)

Services:
  - Basic Cleaning - ₦7,000
  - Suede Care - ₦25,000

Location: Island
Pickup Date: 2026-05-01
Subtotal: ₦32,000
VAT: ₦2,400
Delivery: ₦3,500
Discount: -₦2,000
Total: ₦35,900

Address: 123 Lagos Street, Victoria Island
Phone: +234 800 123 4567

==================================================
Special Instructions: Please handle with extra care
```

---

## Testing Emails

### 1. Test Order Confirmation
```bash
# Create an order via the booking form
1. Visit http://localhost:8000/
2. Select service
3. Fill form and submit
4. Check email inbox for confirmation
```

### 2. Test Status Update Emails
```bash
# Change order status in admin
1. Login to admin: http://localhost:8000/admin/
2. Go to Orders
3. Open an order
4. Change status (e.g., SCHEDULED → CLEANING)
5. Save
6. Check email inbox for status update
```

### 3. Test Delivery Code Email
```bash
# Change order status to OUT_FOR_DELIVERY
1. In admin, change order status to "Out for Delivery"
2. Save
3. Check email inbox for delivery code
4. Verify delivery code was created in database
```

### 4. Test in Python Shell
```python
# Start Django shell
docker-compose exec web python manage.py shell

# Import models and functions
from orders.models import Order
from orders.emails import send_order_status_email

# Get an order
order = Order.objects.first()

# Send test email
send_order_status_email(order)
# Output: ✉️  Status update email sent for #20260001: SCHEDULED → CLEANING
```

---

## Email Templates

### Dynamic Data Available

All templates have access to:
- `{{ order.order_number }}` - Order number
- `{{ order.full_name }}` - Customer name
- `{{ order.email }}` - Customer email
- `{{ order.phone }}` - Customer phone
- `{{ order.address }}` - Pickup/delivery address
- `{{ order.location }}` - Location (mainland/island)
- `{{ order.pickup_date }}` - Scheduled pickup date
- `{{ order.delivery_date }}` - Expected delivery date
- `{{ order.status }}` - Current status
- `{{ order.items.all }}` - QuerySet of OrderItem objects
- `{{ order.subtotal }}` - Subtotal amount
- `{{ order.vat }}` - VAT amount
- `{{ order.delivery_fee }}` - Delivery fee
- `{{ order.discount_amount }}` - Discount applied
- `{{ order.total_amount }}` - Grand total
- `{{ order.is_free_cleaning }}` - Boolean (15th free cleaning?)
- `{{ order.special_instructions }}` - Customer notes
- `{{ order.cancellation_reason }}` - Why canceled (if applicable)

### OrderItem Loop
```django
{% for item in order.items.all %}
  {{ item.service.name }} {% if item.quantity > 1 %}x{{ item.quantity }}{% endif %} - ₦{{ item.subtotal }}
{% endfor %}
```

---

## Troubleshooting

### Emails Not Sending

**Check ZeptoMail Configuration**:
```python
# In settings.py or .env
ZEPTOMAIL_TOKEN=your_token_here
ADMIN_EMAIL=admin@sneakyklean.com
```

**Check Logs**:
```bash
docker-compose logs web | grep "email"
# Look for: ✉️  Status update email sent
# Or: ❌ Failed to send email
```

### Status Update Emails Sending on Every Save

**Solution**: Already fixed with pre_save signal tracking
```python
# orders/signals.py tracks status change
instance._status_changed  # Only True if status actually changed
```

### Delivery Code Not Generated

**Check**:
1. Status must change **to** OUT_FOR_DELIVERY
2. No existing delivery code for that order
3. Check logs for errors

---

## Architecture

```
📧 EMAIL FLOW

Order Created
├── create_order_view() calls send_order_confirmation_email()
├── send_order_confirmation_email() → ZeptoMail API
└── Admin gets send_admin_notification()

Order Status Changed (via Admin)
├── Pre-save signal tracks old status
├── Post-save signal compares statuses
├── If changed → send_order_status_email()
└── If OUT_FOR_DELIVERY → also send_delivery_code_email()

Email Utilities
├── core/email_utils.py::send_email() - ZeptoMail API wrapper
├── Uses ZEPTOMAIL_TOKEN from settings
└── Returns success/failure
```

---

## Summary

✅ **Order confirmation** - Sent when order created  
✅ **Status updates** - Automatically sent when status changes  
✅ **Delivery codes** - Auto-generated for OUT_FOR_DELIVERY  
✅ **Admin notifications** - Sent on new orders  
✅ **Dynamic templates** - All use real order data  
✅ **Signal-based** - No manual intervention needed  

**Status change workflow:**
1. Admin changes order status in Django admin
2. Pre-save signal captures old status
3. Order saved with new status
4. Post-save signal detects change
5. Email automatically sent via ZeptoMail
6. Customer receives update instantly 📬
