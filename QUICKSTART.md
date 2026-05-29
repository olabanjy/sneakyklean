# Quick Start Guide

## Sneaky Klean - Django Backend Setup

### Prerequisites
- Docker Desktop installed and running
- Port 8000 available

### Quick Setup (Automated)

```bash
# Make setup script executable (if not already)
chmod +x setup.sh

# Run setup script
./setup.sh

# Create superuser for admin access
docker-compose run --rm web python manage.py createsuperuser
```

### Manual Setup

```bash
# 1. Build containers
docker-compose build

# 2. Start database
docker-compose up -d db

# 3. Run migrations
docker-compose run --rm web python manage.py migrate

# 4. Create superuser
docker-compose run --rm web python manage.py createsuperuser

# 5. Create discount code
docker-compose run --rm web python manage.py shell
>>> from orders.models import DiscountCode
>>> from decimal import Decimal
>>> DiscountCode.objects.create(code='SNKYLN', discount_amount=Decimal('2000'), is_active=True)
>>> exit()

# 6. Start all services
docker-compose up -d
```

### Access Points

- **Landing Page**: http://localhost:8000/
- **Admin Panel**: http://localhost:8000/admin/
- **Login**: http://localhost:8000/login/
- **Dashboard**: http://localhost:8000/dashboard/ (requires login)

### Testing the Application

#### 1. Test Landing Page
- Visit http://localhost:8000/
- Click "Book" button
- Service selection modal should open

#### 2. Test Order Creation
- Select a service (e.g., Basic Cleaning)
- Fill in booking form:
  - Full Name: Test User
  - Phone: +234 800 000 0000
  - Email: test@example.com
  - Address: Test Address, Lagos
  - Location: Mainland
  - Pickup Date: Select future date
  - Quantity: 1
  - Discount Code: SNKYLN (₦2,000 off)
- Accept terms and submit
- Should redirect to login page

#### 3. Test Authentication
- Visit http://localhost:8000/login/
- Enter email used in order creation
- Check email for OTP code (if email configured)
- Verify OTP on /verify-otp/ page
- Should redirect to dashboard

#### 4. Test Dashboard
- View order metrics: Total Orders, Pending, Free Cleaning Progress
- Check order table for created order
- Test logout

#### 5. Test Admin Panel
- Visit http://localhost:8000/admin/
- Login with superuser credentials
- Navigate to Orders section
- Change order status (will trigger email)
- Test bulk actions

### Common Commands

```bash
# View logs
docker-compose logs -f web

# Stop services
docker-compose stop

# Stop and remove containers
docker-compose down

# Restart services
docker-compose restart

# Access Django shell
docker-compose run --rm web python manage.py shell

# Create migrations
docker-compose run --rm web python manage.py makemigrations

# Run migrations
docker-compose run --rm web python manage.py migrate

# Collect static files
docker-compose run --rm web python manage.py collectstatic
```

### Troubleshooting

#### Port 8000 already in use
```bash
# Find and kill process
lsof -ti:8000 | xargs kill -9

# Or change port in docker-compose.yml
ports:
  - "8001:8000"  # Use port 8001 instead
```

#### Database connection error
```bash
# Restart database
docker-compose restart db

# Check database health
docker-compose ps db
```

#### Email not sending (Development)
```env
# Use Django console backend for testing
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# Or configure Zoho Mail in .env
EMAIL_HOST=smtp.zoho.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@domain.com
EMAIL_HOST_PASSWORD=your-password
EMAIL_USE_TLS=True
```

#### Static files not loading
```bash
# Rebuild containers
docker-compose build

# Collect static files again
docker-compose run --rm web python manage.py collectstatic --noinput

# Restart services
docker-compose restart
```

### Features Implemented

✅ Passwordless OTP authentication with rate limiting
✅ Order management system
✅ Email notifications (OTP, status updates, delivery codes)
✅ Django admin with custom actions
✅ Free cleaning logic (every 15th order)
✅ Discount code system
✅ Rating system
✅ Order cancellation requests
✅ Dashboard with metrics
✅ Delivery code generation

### Default Credentials

**Discount Code**: SNKYLN (₦2,000 off)

**Superuser**: Create with command above

### Email Configuration

For development, emails are sent to console. To configure real email:

1. Update `.env` file:
```env
EMAIL_HOST=smtp.zoho.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@yourdomain.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=noreply@sneakyklean.com
ADMIN_EMAIL=admin@sneakyklean.com
```

2. Restart services:
```bash
docker-compose restart
```

### Production Deployment

See [README.md](README.md) for DigitalOcean deployment instructions.

### Support

For issues, check logs:
```bash
docker-compose logs -f web
```

Contact: care@sneakyklean.com
