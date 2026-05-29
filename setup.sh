#!/bin/bash

# Sneaky Klean Setup Script

echo "🚀 Setting up Sneaky Klean..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

echo "✅ Docker is running"

# Build containers
echo "📦 Building Docker containers..."
docker-compose build

# Start database
echo "🗄️  Starting database..."
docker-compose up -d db

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 10

# Run migrations
echo "🔄 Running database migrations..."
docker-compose run --rm web python manage.py migrate

# Collect static files
echo "📁 Collecting static files..."
docker-compose run --rm web python manage.py collectstatic --noinput

# Create default discount code
echo "🎫 Creating default discount code SNKYLN..."
docker-compose run --rm web python manage.py shell <<EOF
from orders.models import DiscountCode
from decimal import Decimal

# Create SNKYLN discount code if it doesn't exist
if not DiscountCode.objects.filter(code='SNKYLN').exists():
    DiscountCode.objects.create(
        code='SNKYLN',
        discount_amount=Decimal('2000'),
        is_active=True
    )
    print("✅ Discount code SNKYLN created successfully")
else:
    print("ℹ️  Discount code SNKYLN already exists")

exit()
EOF

# Start all services
echo "🚀 Starting all services..."
docker-compose up -d

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Create a superuser: docker-compose run --rm web python manage.py createsuperuser"
echo "2. Access the application:"
echo "   - Landing Page: http://localhost:8000/"
echo "   - Admin Panel: http://localhost:8000/admin/"
echo "   - Login: http://localhost:8000/login/"
echo ""
echo "📝 View logs: docker-compose logs -f web"
echo "🛑 Stop services: docker-compose down"
echo ""
