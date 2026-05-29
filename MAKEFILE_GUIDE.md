# Makefile Commands Guide

This Makefile provides convenient shortcuts for common development tasks.

## Quick Start

```bash
# See all available commands
make help

# First time setup
make quickstart

# Start development
make up
make logs-web

# Stop services
make down
```

---

## 📋 Available Commands

### Service Management

| Command | Description |
|---------|-------------|
| `make build` | Build Docker images |
| `make up` | Start all services in background |
| `make up-logs` | Start services with logs visible |
| `make down` | Stop all services |
| `make restart` | Restart all services |
| `make status` | Show service status |
| `make ps` | Show running containers |

### Logs & Debugging

| Command | Description |
|---------|-------------|
| `make logs` | View all service logs |
| `make logs-web` | View Django logs only |
| `make logs-celery` | View Celery worker logs |
| `make logs-redis` | View Redis logs |
| `make logs-db` | View PostgreSQL logs |

### Django Management

| Command | Description |
|---------|-------------|
| `make shell` | Open Django shell |
| `make bash` | Open bash in web container |
| `make migrate` | Run database migrations |
| `make makemigrations` | Create new migrations |
| `make createsuperuser` | Create Django admin user |
| `make populate` | Populate initial services data |
| `make check` | Check Django configuration |
| `make collectstatic` | Collect static files |

### Database Operations

| Command | Description |
|---------|-------------|
| `make backup-db` | Backup database to SQL file |
| `make restore-db FILE=backup.sql` | Restore database from SQL file |
| `make flush` | Delete all database data (DANGER!) |

### Testing & Quality

| Command | Description |
|---------|-------------|
| `make test` | Run all tests |
| `make coverage` | Run tests with coverage report |
| `make lint` | Run code linting |
| `make format` | Format code with Black |

### Celery Management

| Command | Description |
|---------|-------------|
| `make celery-tasks` | View active Celery tasks |
| `make celery-purge` | Clear Celery task queue |

### Maintenance

| Command | Description |
|---------|-------------|
| `make clean` | Remove Python cache files |
| `make prune` | Remove all containers and volumes |
| `make rebuild` | Full rebuild (prune + build + migrate + populate) |
| `make install` | Rebuild after adding new packages |
| `make health` | Check health of all services |

### Development Shortcuts

| Command | Description |
|---------|-------------|
| `make dev` | Start with live logs (development mode) |
| `make quickstart` | Complete first-time setup |
| `make redis-cli` | Open Redis CLI |
| `make env` | Show environment variables |

---

## 🚀 Common Workflows

### First Time Setup

```bash
# Complete setup with one command
make quickstart

# Or step by step:
make build
make up
make migrate
make populate
make createsuperuser
```

### Daily Development

```bash
# Start services
make up

# Watch logs
make logs-web

# Open Django shell for testing
make shell

# Stop when done
make down
```

### After Code Changes

```bash
# Restart services
make restart

# Or rebuild if dependencies changed
make build
make restart
```

### After Database Model Changes

```bash
# Create and apply migrations
make makemigrations
make migrate
```

### Testing Your Code

```bash
# Run all tests
make test

# Run with coverage
make coverage

# Run linting
make lint
```

### Celery Tasks Debugging

```bash
# Watch Celery logs
make logs-celery

# Check active tasks
make celery-tasks

# Clear stuck tasks
make celery-purge
```

### Database Backup & Restore

```bash
# Backup database
make backup-db

# Restore from backup
make restore-db FILE=backup_20260426_120000.sql
```

### Complete Rebuild

```bash
# Nuclear option - rebuild everything from scratch
make rebuild
```

### Health Check

```bash
# Check if all services are running properly
make health
```

---

## 🔧 Troubleshooting

### Services won't start

```bash
# Check status
make status

# View logs for errors
make logs

# Try rebuilding
make build
make up
```

### Database issues

```bash
# Check database logs
make logs-db

# Try migrating again
make migrate

# Nuclear option: flush and rebuild
make flush
make migrate
make populate
```

### Celery not processing tasks

```bash
# Check Celery logs
make logs-celery

# Check active tasks
make celery-tasks

# Restart Celery
make restart
```

### Redis connection issues

```bash
# Check Redis
make logs-redis

# Test Redis CLI
make redis-cli
> ping
# Should respond: PONG
```

### After git pull

```bash
# Rebuild and restart
make build
make migrate
make restart
```

---

## 📝 Notes

- **Docker Compose V2**: This Makefile uses `docker compose` (V2) not `docker-compose` (V1)
- **Background vs Foreground**: 
  - `make up` - runs in background, frees terminal
  - `make up-logs` - shows logs, blocks terminal
- **Data Persistence**: Database data persists in Docker volumes even after `make down`
- **Removing Data**: Use `make prune` to remove volumes and data
- **Environment Variables**: Loaded from `.env` file automatically

---

## ⚙️ Configuration

The Makefile reads settings from:
- `.env` file (database credentials, etc.)
- `docker-compose.yml` (service configuration)
- Django `settings.py` (application settings)

---

## 🆘 Getting Help

```bash
# Show all available commands
make help

# Or just run make without arguments
make
```

---

## 💡 Tips

1. **Use tab completion**: Type `make` + `TAB` to see available commands
2. **Chain commands**: `make down && make build && make up`
3. **Background services**: Always use `make up` to free your terminal
4. **Quick restart**: `make restart` is faster than `make down && make up`
5. **Save logs**: `make logs-web > debug.log` to save logs to file

---

## 🔗 Related Documentation

- [README.md](README.md) - Project overview
- [QUICKSTART.md](QUICKSTART.md) - Quick start guide
- [CELERY_IMPLEMENTATION.md](CELERY_IMPLEMENTATION.md) - Async tasks
- [EMAIL_SYSTEM_GUIDE.md](EMAIL_SYSTEM_GUIDE.md) - Email configuration
