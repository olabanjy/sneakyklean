# Sneaky Klean - Quick Reference Card

## 🚀 First Time Setup

```bash
make quickstart     # Complete setup: build, migrate, populate, createsuperuser
```

Or manually:
```bash
make build
make migrate
make createsuperuser
make populate
make up
```

## 🔥 Most Used Commands

| Command | Description |
|---------|-------------|
| `make dev` | Start services with live logs |
| `make up` | Start all services in background |
| `make down` | Stop all services |
| `make restart` | Restart all services |
| `make logs` | View all logs |
| `make shell` | Django shell |
| `make bash` | Container bash shell |
| `make health` | Check all services health |

## 📋 Service Management

```bash
make status         # View running containers
make ps             # List all containers
make logs-web       # Web container logs
make logs-celery    # Celery worker logs
make logs-redis     # Redis logs
make logs-db        # Database logs
```

## 🗄️ Database

```bash
make migrate              # Run migrations
make makemigrations      # Create new migrations
make backup-db           # Backup to backups/ folder
make restore-db FILE=... # Restore from backup
```

## 🧪 Testing

```bash
make test           # Run all tests
make coverage       # Generate coverage report
make lint           # Run linting
make format         # Format code
```

## 📧 Celery Tasks

```bash
make celery-tasks   # List active tasks
make celery-purge   # Clear task queue
make redis-cli      # Access Redis shell
```

## 🛠️ Maintenance

```bash
make clean          # Stop and remove containers
make prune          # Full cleanup (containers + volumes + images)
make rebuild        # Nuclear rebuild (clean + build + up)
make install        # Reinstall Python packages
```

## 🌐 Access Points

| URL | Purpose |
|-----|---------|
| http://localhost:8000 | Landing page |
| http://localhost:8000/admin | Django admin |
| http://localhost:8000/login | User login |
| http://localhost:8000/dashboard | User dashboard |

## 📊 Service Ports

| Service | Port | Purpose |
|---------|------|---------|
| Web | 8000 | Django application |
| Database | 5432 | PostgreSQL |
| Redis | 6379 | Task queue broker |

## 🔍 Quick Debugging

```bash
# Check if everything is running
make health

# View recent logs
make logs

# Check Celery is processing emails
make logs-celery | grep "Task orders.tasks.send"

# Check database connection
make logs-db

# Access Django shell to inspect data
make shell
>>> from orders.models import Order
>>> Order.objects.all()

# Access Redis CLI
make redis-cli
> ping
> keys *
> quit
```

## 🚨 Common Issues

| Issue | Solution |
|-------|----------|
| Port 8000 in use | `lsof -ti:8000 \| xargs kill -9` |
| Services not starting | `make restart` |
| Database issues | `make logs-db` |
| Celery not processing | `make logs-celery` |
| Static files missing | `make collectstatic` |
| Need fresh start | `make rebuild` |

## 📦 Docker Compose V2 Commands

If not using Makefile:

```bash
docker compose build              # Build images
docker compose up -d              # Start services
docker compose down               # Stop services
docker compose logs -f web        # View logs
docker compose ps                 # List containers
docker compose restart            # Restart all
docker compose exec web bash      # Access container
```

## 📝 Django Management Commands

```bash
# Run any Django command
docker compose exec web python manage.py <command>

# Examples:
docker compose exec web python manage.py shell
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py populate_services
docker compose exec web python manage.py test
```

## 🎯 Testing Workflow

1. Start services: `make up`
2. Check health: `make health`
3. Run tests: `make test`
4. View coverage: `make coverage`
5. Check logs: `make logs`

## 📚 Full Documentation

- [Makefile Guide](MAKEFILE_GUIDE.md) - All 40+ commands explained
- [Smoke Test](SMOKE_TEST.md) - 15-test comprehensive checklist
- [README](README.md) - Complete project documentation
- [Celery Implementation](CELERY_IMPLEMENTATION.md) - Async task queue details
- [Email System](EMAIL_SYSTEM_GUIDE.md) - Email configuration

## ⚡ Performance Metrics

- **API Response**: <100ms
- **Order Creation**: 300-500ms (was 2-5 seconds before Celery)
- **Email Delivery**: Background processing (no user wait)
- **Dashboard Quick Rating**: <100ms (AJAX)

## 🔑 Default Credentials

**Admin Panel** (after `make createsuperuser`):
- URL: http://localhost:8000/admin
- Username: (set during creation)
- Password: (set during creation)

**Test Discount Code**:
- Code: `SNKYLN`
- Discount: ₦2,000 off

## 💡 Environment Variables

Key variables in `.env`:

```env
DEBUG=True
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=sneakyklean_db
DB_USER=sneakyklean_user
DB_PASSWORD=secure-password

ZEPTO_API_KEY=your-zeptomail-key
DEFAULT_FROM_EMAIL=Sneaky Klean <noreply@arroweye.pro>
ADMIN_EMAIL=admin@sneakyklean.com
```

---

**Need help?** Run `make help` or see [MAKEFILE_GUIDE.md](MAKEFILE_GUIDE.md)

**Quick Start:** `make quickstart && make dev` 🚀
