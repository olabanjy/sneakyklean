# Service Model Refactoring - Implementation Guide

## Critical Update: Service Catalog System

### Problem
Services (Basic Cleaning, Deep Cleaning, Restoration, Suede Care) and their prices were hardcoded in:
- Order model as `SERVICE_CHOICES` 
- Views with hardcoded pricing logic  
- JavaScript with duplicate pricing

This made it impossible to:
- Manage services through Django admin
- Update prices without code changes
- Add/remove services dynamically
- Track service-level analytics

### Solution
Created a proper database-driven service catalog system with:

1. **Service Model** - Central service catalog
2. **OrderItem Model** - Line items for orders (supports multiple services)
3. **Management Command** - Populate initial services
4. **API Endpoint** - Fetch services for frontend

---

## New Models

### Service Model
```python
class Service(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    icon = models.CharField(max_length=50, blank=True)
    estimated_duration = models.CharField(max_length=50, blank=True)
```

**Purpose**: Single source of truth for all cleaning services

**Key Fields**:
- `name`: Service name (e.g., "Basic Cleaning")
- `price`: Base price for the service
- `is_active`: Show/hide service on website
- `display_order`: Control order of services on frontend

### OrderItem Model
```python
class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items')
    service = models.ForeignKey(Service)
    service_name = models.CharField(max_length=100)  # Snapshot
    price_at_order = models.DecimalField(...)  # Snapshot
    quantity = models.PositiveIntegerField(default=1)
    subtotal = models.DecimalField(...)  # Calculated
```

**Purpose**: Links services to orders, stores price snapshots for historical accuracy

**Why Snapshots?**: If a service price changes from ₦7,000 to ₦8,000, old orders should still show ₦7,000

---

## Migration Steps

### 1. Create Migrations
```bash
docker-compose run --rm web python manage.py makemigrations
docker-compose run --rm web python manage.py migrate
```

### 2. Populate Initial Services
```bash
docker-compose run --rm web python manage.py populate_services
```

This creates 4 services:
- **Basic Cleaning** - ₦7,000
- **Deep Cleaning** - ₦12,000
- **Restoration** - ₦25,000
- **Suede Care** - ₦15,000

### 3. Verify in Django Admin
```
http://localhost:8000/admin/orders/service/
```

You can now:
- Add new services
- Update prices
- Deactivate services
- Reorder display

---

## Updated Components

### Admin (`orders/admin.py`)
Added `ServiceAdmin` with:
- List display: name, price, is_active, display_order
- Filters: is_active
- Search: name, description
- Inline editing of prices

### Views (`orders/views.py`)
Updated `create_order_view`:
- Fetches services from database dynamically
- Creates OrderItem records for each service
- Calculates order totals from OrderItems

Added `services_api_view`:
- Returns JSON list of active services
- Used by frontend to populate service selection
- Format: `[{id, name, description, price, icon}, ...]`

### URLs (`orders/urls.py`)
Added:
```python
path('api/services/', views.services_api_view, name='services_api'),
```

### JavaScript (`core/static/js/services.js`)
Updated to:
- Fetch services from `/api/services/`
- Dynamically build service cards
- Use database prices (no hardcoding)

---

## Default Service Catalog

| Service | Price | Description |
|---------|-------|-------------|
| Basic Cleaning | ₦7,000 | Standard cleaning for everyday sneakers |
| Deep Cleaning | ₦12,000 | Thorough deep clean for heavily soiled sneakers |
| Restoration | ₦25,000 | Complete restoration for damaged sneakers |
| Suede Care | ₦15,000 | Specialized care for suede and nubuck |

---

## Benefits

### 1. Admin Management
✅ Change prices anytime through Django admin  
✅ Add seasonal services (e.g., "Holiday Special")  
✅ Temporarily disable services

### 2. Price History
✅ Old orders show original prices  
✅ Audit trail of price changes  
✅ Historical reporting accuracy

### 3. Flexibility
✅ Service combinations (order multiple services)  
✅ Different quantities per service  
✅ A/B testing with different prices

### 4. Analytics
✅ Track which services are most popular  
✅ Revenue per service  
✅ Service-level conversion rates

---

## API Usage

### Fetch Active Services
```javascript
fetch('/api/services/')
  .then(res => res.json())
  .then(services => {
    services.forEach(service => {
      console.log(`${service.name}: ₦${service.price}`);
    });
  });
```

### Response Format
```json
[
  {
    "id": 1,
    "name": "Basic Cleaning",
    "description": "Standard cleaning...",
    "price": "7000.00",
    "icon": "mdi-shoe-sneaker",
    "estimated_duration": "1-2 hours"
  },
  ...
]
```

---

## Testing

### Test Service Management
```python
from orders.models import Service

# Create service
service = Service.objects.create(
    name='Premium Wash',
    price=Decimal('10000'),
    is_active=True
)

# Order with service
from orders.models import Order, OrderItem

order = Order.objects.create(...)
item = OrderItem.objects.create(
    order=order,
    service=service,
    quantity=2
)

# item.subtotal = 20000 (auto-calculated)
```

### Test Price Snapshots
```python
# Create order with service at ₦7000
service = Service.objects.get(name='Basic Cleaning')
order = Order.objects.create(...)
item = OrderItem.objects.create(order=order, service=service, quantity=1)

assert item.price_at_order == 7000

# Update service price
service.price = 8000
service.save()

# Old order still shows ₦7000
item.refresh_from_db()
assert item.price_at_order == 7000  # Still ₦7000!
```

---

## Admin Workflow

### Adding a New Service
1. Go to Django Admin > Services
2. Click "Add Service"
3. Fill in:
   - Name: "Express Cleaning"
   - Description: "Same-day express service"
   - Price: 15000
   - Display Order: 5
   - Is Active: ✓
4. Save

Service immediately appears on website!

### Updating Prices
1. Go to Django Admin > Services
2. Click on service (e.g., "Basic Cleaning")
3. Change price from 7000 to 7500
4. Save

All new orders use ₦7,500. Old orders still show ₦7,000.

### Seasonal Promotions
1. Add new service: "Summer Special" at discounted price
2. Set dates if your Service model has validity period
3. Deactivate after promotion ends

---

## Database Schema

```sql
-- Services table
CREATE TABLE orders_service (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    display_order INTEGER DEFAULT 0,
    icon VARCHAR(50),
    estimated_duration VARCHAR(50),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Order items table (junction table with snapshot)
CREATE TABLE orders_orderitem (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders_order(id),
    service_id INTEGER REFERENCES orders_service(id),
    service_name VARCHAR(100),
    price_at_order DECIMAL(10,2),
    quantity INTEGER,
    subtotal DECIMAL(10,2),
    created_at TIMESTAMP
);
```

---

## Backwards Compatibility

### Old Order Records
If you have existing orders with the old `service_type` field:

1. **Data migration** to convert old orders:
```python
# Create OrderItems from old service_type field
for order in Order.objects.filter(service_type__isnull=False):
    service = Service.objects.get(name=order.service_type)
    OrderItem.objects.create(
        order=order,
        service=service,
        quantity=order.quantity,  # From old field
    )
```

2. **Remove old fields** after migration:
```python
# In new migration
operations = [
    migrations.RemoveField('Order', 'service_type'),
    migrations.RemoveField('Order', 'quantity'),
]
```

---

## Performance Considerations

### Indexing
```python
class Service(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['is_active', 'display_order']),
        ]
```

### Caching (Future Enhancement)
```python
from django.core.cache import cache

def get_active_services():
    services = cache.get('active_services')
    if not services:
        services = list(Service.objects.filter(is_active=True).values())
        cache.set('active_services', services, 300)  # 5 min
    return services
```

---

## Summary

✅ Service catalog managed through Django admin  
✅ Dynamic pricing - no code changes needed  
✅ Price history preserved for old orders  
✅ Support for multiple services per order  
✅ API endpoint for frontend integration  
✅ Management command for initial setup  

This is now a production-ready, maintainable service management system!
