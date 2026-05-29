#!/bin/bash

# Service Model Implementation Verification Script

echo "================================================"
echo "🔍 Verifying Service Model Implementation"
echo "================================================"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check 1: Service model exists
echo "1. Checking Service model..."
if grep -q "class Service(models.Model):" orders/models.py; then
    echo -e "${GREEN}✓${NC} Service model found in orders/models.py"
else
    echo -e "${RED}✗${NC} Service model not found"
    exit 1
fi

# Check 2: OrderItem model exists
echo ""
echo "2. Checking OrderItem model..."
if grep -q "class OrderItem(models.Model):" orders/models.py; then
    echo -e "${GREEN}✓${NC} OrderItem model found in orders/models.py"
else
    echo -e "${RED}✗${NC} OrderItem model not found"
    exit 1
fi

# Check 3: Management command exists
echo ""
echo "3. Checking populate_services command..."
if [ -f "orders/management/commands/populate_services.py" ]; then
    echo -e "${GREEN}✓${NC} populate_services.py command exists"
else
    echo -e "${RED}✗${NC} Management command not found"
    exit 1
fi

# Check 4: Admin updates
echo ""
echo "4. Checking ServiceAdmin..."
if grep -q "class ServiceAdmin" orders/admin.py; then
    echo -e "${GREEN}✓${NC} ServiceAdmin found in orders/admin.py"
else
    echo -e "${YELLOW}⚠${NC} ServiceAdmin not found in admin.py"
fi

# Check 5: OrderItemInline
echo ""
echo "5. Checking OrderItemInline..."
if grep -q "class OrderItemInline" orders/admin.py; then
    echo -e "${GREEN}✓${NC} OrderItemInline found for order detail view"
else
    echo -e "${YELLOW}⚠${NC} OrderItemInline not found"
fi

# Check 6: Old SERVICE_CHOICES removed
echo ""
echo "6. Checking old hardcoded services..."
if grep -q "SERVICE_CHOICES" orders/models.py; then
    echo -e "${YELLOW}⚠${NC} Old SERVICE_CHOICES still present (will be removed after migration)"
else
    echo -e "${GREEN}✓${NC} Old SERVICE_CHOICES removed"
fi

# Check 7: Python syntax
echo ""
echo "7. Validating Python syntax..."
if python3 -m py_compile orders/models.py orders/admin.py orders/management/commands/populate_services.py 2>/dev/null; then
    echo -e "${GREEN}✓${NC} All files have valid syntax"
else
    echo -e "${RED}✗${NC} Syntax errors found"
    exit 1
fi

echo ""
echo "================================================"
echo "✅ Service Model Implementation Verified!"
echo "================================================"
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Create migrations:"
echo "   docker-compose run --rm web python manage.py makemigrations"
echo ""
echo "2. Run migrations:"
echo "   docker-compose run --rm web python manage.py migrate"
echo ""
echo "3. Populate initial services:"
echo "   docker-compose run --rm web python manage.py populate_services"
echo ""
echo "4. Verify in admin:"
echo "   http://localhost:8000/admin/orders/service/"
echo ""
echo "📖 Documentation:"
echo "   - SERVICES_IMPLEMENTATION_SUMMARY.md (Quick overview)"
echo "   - SERVICE_MODEL_REFACTORING.md (Complete guide)"
echo ""
