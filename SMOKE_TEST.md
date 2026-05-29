# Smoke Test Checklist

Run this checklist to verify all features are working end-to-end.

## Pre-Test Setup

```bash
# 1. Start all services
make up

# 2. Check health
make health

# 3. Apply migrations
make migrate

# 4. Populate services
make populate

# 5. Watch logs (in separate terminal)
make logs-web
```

---

## ✅ Test 1: Landing Page

**URL**: `http://localhost:8000/`

- [ ] Page loads without errors
- [ ] Service cards render dynamically (not hardcoded)
- [ ] Four services visible: Basic, Deep, Restoration, Suede
- [ ] Prices display correctly
- [ ] Booking form visible

**Verify API**:
```bash
curl http://localhost:8000/api/services/ | python -m json.tool
```
- [ ] Returns JSON array with 4 services
- [ ] Each service has: id, name, price, description, display_order

---

## ✅ Test 2: Service Selection

- [ ] Click "Select Service" button
- [ ] Service grid expands
- [ ] Click on a service card
- [ ] Card highlights with "active" class
- [ ] Button text changes to "Remove"
- [ ] Selected service name appears in summary
- [ ] Price updates in summary

**Test Combo Rules**:
- [ ] Select "Restoration"
- [ ] Cleaning services become dimmed (opacity: 0.4)
- [ ] Try to select "Basic Cleaning"
- [ ] Toast shows: "Invalid combination"

---

## ✅ Test 3: Form Submission

**Fill booking form**:
- Full Name: "Test User"
- Email: "test@example.com"
- Phone: "+234 800 123 4567"
- Address: "123 Test Street, Lagos"
- Location: "Island"
- Pickup Date: Tomorrow's date
- Quantity: 2
- Discount Code: Leave blank for now

- [ ] Submit button enabled after all fields filled
- [ ] Click "REQUEST PICKUP"
- [ ] Redirect to login page within 500ms (fast!)
- [ ] Success message shows order number

**Check logs**:
```bash
make logs-celery
```
- [ ] See: "send_order_confirmation_email_task"
- [ ] See: "send_admin_notification_task"

---

## ✅ Test 4: Email Confirmation (Celery)

**Check Celery processed emails**:
```bash
make logs-celery | grep "succeeded"
```
- [ ] Task "send_order_confirmation_email_task" succeeded
- [ ] Task "send_admin_notification_task" succeeded

**If using real email**:
- [ ] Customer receives order confirmation email
- [ ] Email shows correct order details
- [ ] Email shows selected services
- [ ] Email shows total amount
- [ ] Admin receives notification email

---

## ✅ Test 5: OTP Login

**URL**: `http://localhost:8000/accounts/login/`

- [ ] Enter email: "test@example.com"
- [ ] Click "Send OTP"
- [ ] Success message appears
- [ ] Redirect to OTP verification page

**Check OTP generation**:
```bash
make shell
>>> from accounts.models import OTP
>>> otp = OTP.objects.latest('created_at')
>>> print(f"OTP Code: {otp.code}")
>>> exit()
```

**Enter OTP**:
- [ ] Enter the 6-digit OTP code
- [ ] Click "Verify"
- [ ] Success message appears
- [ ] Redirect to dashboard

---

## ✅ Test 6: Dashboard View

**URL**: `http://localhost:8000/orders/dashboard/`

- [ ] Page loads
- [ ] Welcome message with user name
- [ ] Total Orders shows: 1
- [ ] Pending Orders shows: 1
- [ ] Free Cleaning Progress shows: 1/15
- [ ] Orders table visible
- [ ] Created order appears in table
- [ ] Order number matches
- [ ] Status shows "Scheduled"
- [ ] Amount displays correctly
- [ ] Rating stars show (empty, not clickable for non-delivered)

---

## ✅ Test 7: Django Admin

**URL**: `http://localhost:8000/admin/`

**Create superuser if needed**:
```bash
make createsuperuser
```

- [ ] Login with superuser credentials
- [ ] Navigate to Orders
- [ ] See created test order
- [ ] Click on order to edit
- [ ] See OrderItem inline (services)
- [ ] Services listed correctly

---

## ✅ Test 8: Order Status Change (Email Trigger)

**In Django Admin**:
- [ ] Change order status to "CLEANING"
- [ ] Click "Save"

**Check Celery**:
```bash
make logs-celery
```
- [ ] See: "✉️ Status update email queued"
- [ ] Task "send_order_status_email_task" succeeded

**Email Check**:
- [ ] Customer receives status update email
- [ ] Email shows "Cleaning in Progress"
- [ ] Email shows order details

---

## ✅ Test 9: Delivery Code Generation

**In Django Admin**:
- [ ] Change order status to "OUT_FOR_DELIVERY"
- [ ] Click "Save"

**Verify Delivery Code**:
```bash
make shell
>>> from orders.models import DeliveryCode
>>> code = DeliveryCode.objects.latest('created_at')
>>> print(f"Code: {code.code}, Order: {code.order.order_number}")
>>> exit()
```

- [ ] Delivery code created (4 digits)
- [ ] Email queued successfully

**Email Check**:
- [ ] Customer receives delivery code email
- [ ] Email shows 4-digit code
- [ ] Email shows order number

---

## ✅ Test 10: Dashboard Quick Rating

**In Django Admin**:
- [ ] Change order status to "DELIVERED"
- [ ] Click "Save"

**Back to Dashboard**:
- [ ] Refresh dashboard page
- [ ] Order status shows "Delivered"
- [ ] Rating stars are clickable (hover changes color)
- [ ] Hover over stars - they light up
- [ ] Click 5th star
- [ ] Toast shows: "Thank you for your feedback!"
- [ ] Stars remain highlighted
- [ ] Stars no longer clickable

**Verify in Database**:
```bash
make shell
>>> from orders.models import Rating
>>> rating = Rating.objects.latest('created_at')
>>> print(f"Rating: {rating.rating} stars for {rating.order.order_number}")
>>> exit()
```

---

## ✅ Test 11: Discount Code

**Create discount in admin**:
- [ ] Go to Discount Codes in admin
- [ ] Add new: Code="WELCOME", Amount=2000, Active=Yes
- [ ] Save

**Create new order**:
- [ ] Logout from dashboard
- [ ] Go to landing page
- [ ] Fill booking form
- [ ] Use email: "test2@example.com"
- [ ] Enter discount code: "WELCOME"
- [ ] Click "Apply" button
- [ ] Total amount decreases by ₦2,000
- [ ] Submit order

**Verify discount applied**:
```bash
make shell
>>> from orders.models import Order
>>> order = Order.objects.latest('created_at')
>>> print(f"Discount: ₦{order.discount_amount}")
>>> exit()
```

---

## ✅ Test 12: 15th Free Cleaning

**Create 14 orders via shell**:
```bash
make shell
```

```python
from accounts.models import User
from orders.models import Order, Service
from decimal import Decimal
from datetime import date

# Get user
user = User.objects.get(email="test@example.com")
service = Service.objects.first()

# Create 13 more orders (already have 1)
for i in range(13):
    order = Order.objects.create(
        user=user,
        full_name="Test User",
        email="test@example.com",
        phone="+234 800 123 4567",
        address="123 Test Street",
        location="island",
        pickup_date=date.today(),
        subtotal=Decimal('7000'),
        vat=Decimal('525'),
        delivery_fee=Decimal('3500'),
        total_amount=Decimal('11025'),
    )
    user.free_cleaning_count += 1
    user.total_orders += 1
    user.save()

print(f"Total orders: {user.total_orders}")
print(f"Free cleaning count: {user.free_cleaning_count}")
exit()
```

**Create 15th order**:
- [ ] Go to landing page
- [ ] Fill form with same email
- [ ] Submit order
- [ ] Order created

**Verify free cleaning**:
```bash
make shell
>>> from orders.models import Order
>>> order = Order.objects.latest('created_at')
>>> print(f"Is Free: {order.is_free_cleaning}")
>>> print(f"Total Amount: ₦{order.total_amount}")
>>> exit()
```
- [ ] `is_free_cleaning` = True
- [ ] `total_amount` = 0

---

## ✅ Test 13: Redis & Celery Health

**Check Redis**:
```bash
make redis-cli
> ping
> exit
```
- [ ] Response: "PONG"

**Check Celery active tasks**:
```bash
make celery-tasks
```
- [ ] Shows active/past tasks or empty if none running

**Check task queue**:
```bash
make redis-cli
> LLEN celery
> exit
```
- [ ] Returns 0 (all tasks processed)

---

## ✅ Test 14: Service API Performance

**Test API response time**:
```bash
time curl http://localhost:8000/api/services/
```
- [ ] Response time < 200ms

**Test order creation speed**:
- [ ] Create order via website
- [ ] Note time to redirect
- [ ] Should be < 500ms

---

## ✅ Test 15: Database Persistence

**Stop and restart services**:
```bash
make down
make up
```

- [ ] All data persists
- [ ] Orders still visible in dashboard
- [ ] Services still in database
- [ ] Users still exist

---

## 🎯 Final Verification

```bash
make health
```

**Should show**:
- [x] Web: OK
- [x] Database: OK
- [x] Redis: OK
- [x] Celery: OK

---

## 📊 Test Results Summary

Total Tests: 15

- [ ] All tests passing
- [ ] No errors in logs
- [ ] All features working
- [ ] Emails sending async
- [ ] Fast response times

---

## 🐛 Common Issues

### Services not loading
```bash
make shell
>>> from orders.models import Service
>>> Service.objects.count()
```
If 0, run: `make populate`

### Emails not sending
```bash
make logs-celery
```
Check for errors. Restart if needed: `make restart`

### OTP not working
Check `.env` has `ZEPTOMAIL_TOKEN` set

### Database connection failed
```bash
make logs-db
```
Ensure PostgreSQL is running

---

## 🧹 Cleanup After Testing

```bash
# Remove test data (optional)
make flush

# Or complete cleanup
make prune
make build
make quickstart
```

---

**Smoke Test Complete** ✅

If all tests pass, the application is production-ready! 🚀
