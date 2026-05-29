# Sneaky Klean - Django Backend

Professional sneaker cleaning service platform with passwordless OTP authentication, order management, and automated email notifications.

## ⚡ Quick Start

```bash
# Using Makefile (recommended)
make quickstart    # Complete first-time setup
make dev           # Start services with logs

# Or manually
docker compose build
docker compose up -d
docker compose exec web python manage.py migrate
docker compose exec web python manage.py populate_services
docker compose exec web python manage.py createsuperuser
```

Visit: `http://localhost:8000`

## 📚 Documentation

- **[Makefile Commands](MAKEFILE_GUIDE.md)** - 40+ convenient commands
- **[Smoke Test](SMOKE_TEST.md)** - End-to-end testing checklist
- **[Quick Start](QUICKSTART.md)** - Detailed setup guide
- **[Email System](EMAIL_SYSTEM_GUIDE.md)** - Email configuration
- **[Celery Tasks](CELERY_IMPLEMENTATION.md)** - Async processing

## 🎯 Features

- **Passwordless Authentication**: Email OTP login with rate limiting (3 attempts/hour)
- **Order Management**: Track orders from scheduling to delivery
- **Free Cleaning**: Automatic free 15th order
- **Email Notifications**: Async status updates, OTP codes, delivery codes (Celery)
- **Django Admin**: Full order and user management
- **Rating System**: Post-delivery feedback + dashboard quick rating
- **Cancellation Requests**: User-initiated with admin approval
- **Discount Codes**: Promo code support (SNKYLN = ₦2,000 off)

## 🛠️ Tech Stack

- **Backend**: Django 5.0.4, Python 3.11
- **Database**: PostgreSQL 15
- **Email**: ZeptoMail API (Transactional emails)
- **Task Queue**: Celery 5.3.6 + Redis 7 (Async email processing)
- **Containerization**: Docker Compose V2
- **Static Files**: WhiteNoise
- **WSGI Server**: Gunicorn

## 📁 Project Structure

```
sneakyklean/
├── accounts/           # User authentication & OTP
├── orders/             # Order management, emails & Celery tasks
├── core/               # Landing page & shared utilities
├── static/             # CSS, JS, images
├── templates/          # HTML templates
├── docker-compose.yml  # Multi-container orchestration (web, db, redis, celery)
├── Dockerfile          # Django app container
├── Makefile            # Development workflow automation
└── requirements.txt    # Python dependencies
```

## Setup Instructions

### 1. Environment Configuration

Copy the example environment file and configure:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
# Django
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Database
DB_NAME=sneakyklean_db
DB_USER=sneakyklean_user
DB_PASSWORD=your-secure-password
DB_HOST=db
DB_PORT=5432

# ZeptoMail API (API-based email sending)
ZEPTO_API_KEY=your-zeptomail-api-key-here
ZEPTO_API_BASE_URL=https://api.zeptomail.com/v1.1
DEFAULT_FROM_EMAIL=Sneaky Klean <noreply@arroweye.pro>

# Admin
ADMIN_EMAIL=admin@sneakyklean.com
```

#### Setting up ZeptoMail API

ZeptoMail is used for reliable transactional email delivery (OTP codes, order updates, delivery notifications).

1. **Create ZeptoMail Account**
   - Sign up at [https://www.zoho.com/zeptomail/](https://www.zoho.com/zeptomail/)
   - Navigate to Settings > Mail Agents
   - Create a new mail agent

2. **Get API Key**
   - In your mail agent, click "Setup Instructions"
   - Copy the API key (starts with `Zoho-enczapikey`)
   - Add to your `.env` file as `ZEPTO_API_KEY`

3. **Verify Sender Domain**
   - Go to Mail Agents > Sending Domains
   - Add your domain (e.g., `sneakyklean.com`)
   - Add DNS records (SPF, DKIM) to your domain registrar
   - Wait for verification (usually 24-48 hours)

4. **Configure From Address**
   - Update `DEFAULT_FROM_EMAIL` in `.env` to use your verified domain
   - Format: `Sneaky Klean <noreply@arroweye.pro>`

**Note**: ZeptoMail requires domain verification before sending emails. For testing, use the default sending domain provided by ZeptoMail.

### 2. Build and Start Containers

``Using Makefile (recommended)
make build          # Build Docker images
make up             # Start all services (web, db, redis, celery)
make logs-web       # View web container logs
make logs-celery    # View celery worker logs

# Or manual Docker Compose V2 commands
docker compose build
docker compose up -d
docker compose logs -f web
```

### 3. Database Setup

```bash
# Using Makefile (recommended)
make migrate        # Run database migrations
make createsuperuser # Create admin account
make populate       # Create initial services and discount code

# Or manual commands
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py populate_services
docker compose execnt code
docker-compose run --rm web python manage.py shell
```

In the Django shell:

```python
from orders.models import DiscountCode
from decimal import Decimal

DiscountCode.objects.create(
    code='SNKYLN',
    discount_amount=Decimal('2000'),
    is_active=True
)
exit()
```
# Using Makefile
make collectstatic

# Or manual command
docker compose exec
### 4. Collect Static Files

```bash
docker-compose run --rm web python manage.py collectstatic --noinput
```

### 5. Access the Application

- **Landing Page**: http://localhost:8000/
- **Admin Panel**: http://localhost:8000/admin/
- **Login**: http://localhost:8000/login/

## 🔧 Development Workflow

### Daily Commands

```bash
# Start and watch
make dev            # Start all services with live logs
make health         # Check service health
make status         # View running containers

# Django management
make shell          # Django shell
make bash           # Container bash
make migrate        # Run migrations
make makemigrations # Create migrations
make test           # Run tests
```

### Viewing Logs

```bash
# All services
make logs

# Specific services
make logs-web       # Web container
make logs-celery    # Celery worker
make logs-redis     # Redis broker
make logs-db        # PostgreSQL
```

### Database Operations

```bash
make backup-db      # Backup database to backups/
make restore-db FILE=backup_file.sql  # Restore from backup
make flush          # Clear database (CAUTION)
```

### Celery Task Queue

```bash
make celery-tasks   # List active tasks
make celery-purge   # Clear task queue
make redis-cli      # Access Redis shell
```

### Stopping Services

```bash
make down           # Stop all containers
make restart        # Restart all services
make clean          # Stop and remove containers
make prune          # Full cleanup (volumes + images)
```

**See [MAKEFILE_GUIDE.md](MAKEFILE_GUIDE.md) for all 40+ commands**

## Order Status Flow

1. **SCHEDULED** - Order created, pickup scheduled
2. **PICKED_UP** - Sneakers collected from customer
3. **CLEANING** - Cleaning in progress
4. **OUT_FOR_DELIVERY** - Ready for delivery (delivery code generated)
5. **DELIVERED** - Order completed
6. **CANCELED** - Order cancelled
7. **DELAYED** - Order delayed

## Email Templates

- **OTP Email**: `accounts/templates/accounts/otp_email.html`
- **Order Status**: `orders/templates/emails/order_status.html`
- **Delivery Code**: `orders/templates/emails/delivery_code.html`

## API Endpoints

### Public
- `GET /` - Landing page
- `GET /login/` - Login page
- `POST /login/` - Request OTP
- `GET /verify-otp/` - OTP verification page
- `POST /verify-otp/` - Verify OTP and login
- `POST /order/create/` - Create order (from booking form)

### Authenticated
- `GET /dashboard/` - User dashboard
- `GET /logout/` - Logout
- `POST /order/<id>/rate/` - Rate order
- `POST /order/<id>/cancel/` - Request cancellation

### AJAX
- `POST /api/validate-discount/` - Validate discount code
- `POST /order/<id>/quick-rate/` - Quick rating from dashboard
- `GET /api/services/` - Fetch available services

## 👨‍💼 Admin Panel Features

### User Management
- View all users with order counts
- Track free cleaning progress
- Search by email, name, phone

### Order Management
- Color-coded status badges
- Bulk status updates
- Cancellation request management
- Filter by status, service, location
- Export orders to CSV
- Quick actions: Mark as Picked Up, Cleaning, Out for Delivery, Delivered, Canceled

### Discount Codes
- Create/edit promo codes
- Set usage limits and expiry dates
- Track redemptions

### Ratings
- View all customer feedback
- Average rating metrics
- Filter by star count
- Quick rating from dashboard (clickable stars)

## 📊 Database Models

### User
- Email-based authentication (no password)
- Tracks total orders and free cleaning count
- Automatically resets counter at 15 orders

### OTP
- 6-digit secure codes
- 5-minute expiration
- Auto-marked as used after verification

### Order
- Auto-generated order numbers (#YYYY format)
- Tracks all customer and service details
- Pricing calculation with VAT (7.5%)
- Cancellation request support

### DiscountCode
- Promo code management
- Usage limits and validity periods

### DeliveryCode
- 4-digit verification codes
- Auto-generated when status = OUT_FOR_DELIVERY

### Rating
- 1-5 star ratings
- Can rate from dashboard or dedicated page

## 📧 Email Notifications (Async via Celery)

### User Emails
- OTP code for login (5-min expiry) ⚡
- Order confirmation ⚡
- Status updates (on every change) ⚡
- Delivery code (when out for delivery) ⚡
- Rating request (after delivery) ⚡

### Admin Emails
- New order notifications with full details ⚡

**⚡💡  All emails processed asynchronously via Celery for sub-500ms response times**
- New order notifications with full details

## Free Cleaning Logic

- Counter increments on every order creation
- 15th order automatically marked as free (total = ₦0)
- Counter resets to 0 after free order
- Displayed in user dashboard as progress (x/15)

## 🔧 Troubleshooting

### Port Already in Use

```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or change port in docker-compose.yml
```

### Celery Worker Not Processing Tasks

```bash
# Check Celery logs
make logs-celery

# Check Redis connection
make redis-cli
> ping  # Should return PONG

# Restart Celery
make restart
```

### Database Connection Issues

```bash
# Check if database is running
make status

# View database logs
make logs-db

# Restart database
docker compose restart db
```

### Running Services Locally (No Docker)

Not recommended, but if needed:

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DEBUG=True
export DATABASE_URL=postgresql://user:pass@localhost/db
export REDIS_URL=redis://localhost:6379/0

# Run migrations
python manage.py migrate

# Start Redis
redis-server

# Start Celery worker
celery -A sneakyklean worker -l info

# Start Django
python manage.py runserver
```
ports:
  - "8001:8000"  # Use port 8001 instead
```

### Database Connection Issues

```bash
# Restart database container
docker-compose restart db

# Check database health
docker-compose ps db
```

### Email Not Sending

```bash
# Check Celery is processing tasks
make logs-celery

# Check Redis is running
make status

# Test Celery task queue
docker compose exec web python manage.py shell
>>> from orders.tasks import send_otp_email_task
>>> send_otp_email_task.delay(1, '123456')

# View email sending errors
make logs-web
```

1. Verify ZeptoMail API key in `.env`
2. Check API key is active in your ZeptoMail account
3. Ensure DEFAULT_FROM_EMAIL uses a verified sender domain
4. Check Celery worker is running: `make logs-celery`
5. Test API connection and check rate limits

### Static Files Not Loading

```bash
# Collect static files
make collectstatic

# Rebuild containers
make rebuild
```

## 🚀 Performance

- **Order Creation**: ~300-500ms (emails queued asynchronously)
- **API Response**: <100ms (services endpoint)
- **Email Delivery**: Processed in background via Celery
- **Dashboard Quick Rating**: <100ms (AJAX submission)

**Before Celery**: 2-5 seconds (blocking email API calls)  
**After Celery**: 300-500ms (10x improvement) ⚡

## 🧪 Testing

Run the comprehensive smoke test:

```bash
# Start services
make up

# Run all 15 tests
# Follow checklist in SMOKE_TEST.md

# Run Django unit tests
make test

# Generate coverage report
make coverage
```

See [SMOKE_TEST.md](SMOKE_TEST.md) for detailed test procedures.

## 📦 Deployment to Production

### Prerequisites
- Docker and Docker Compose V2 installed
- Domain name (optional but recommended)
- SSL certificate (Let's Encrypt recommended)

### Steps

1. **Prepare Server**
   ```bash
   # Install Docker Compose V2 if needed
   sudo apt-get update
   sudo apt-get install docker-compose-plugin
   📄 License

MIT License - See LICENSE file for details

## 🤝 Support

For issues or questions, contact: care@sneakyklean.com

---

**Key Features Summary:**
- ⚡ Async email processing (Celery + Redis)
- 🔐 Passwordless OTP authentication
- 📊 Real-time order tracking
- 🎁 Automatic 15th free cleaning
- ⭐ Quick rating from dashboard
- 🎟️ Discount code support
- 📧 Automated notifications
- 🛠️ 40+ Makefile commands for easy development

**Get Started:** `make quickstart` 🚀
   ```

3. **Configure Environment**
   ```bash
   cp .env.example .env
   nano .env
   ```
   
   - Set `DEBUG=False`
   - Update `ALLOWED_HOSTS` with your domain
   - Set strong `SECRET_KEY` (use `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`)
   - Configure real ZeptoMail API key
   - Set strong database password

4. **Build and Deploy**
   ```bash
   # Using Makefile
   make build
   make migrate
   make createsuperuser
   make collectstatic
   make up

   # Or manually
   docker compose build
   docker compose up -d
   docker compose exec web python manage.py migrate
   docker compose exec web python manage.py createsuperuser
   docker compose exec web python manage.py collectstatic --noinput
   docker compose exec web python manage.py populate_services
   ```

5. **Configure Nginx (Recommended)**
   - Set up reverse proxy to handle SSL termination
   - Configure Let's Encrypt for HTTPS
   - Add rate limiting and security headers
   - See [NGINX_DEPLOYMENT_GUIDE.md](NGINX_DEPLOYMENT_GUIDE.md) for a full server-side setup

6. **Monitor Services**
   ```bash
   make health        # Check all services
   make logs          # View all logs
   make logs-celery   # Monitor task queue
   ```

## License

MIT License - See LICENSE file for details

## Support

For issues or questions, contact: care@sneakyklean.com
