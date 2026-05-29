#!/bin/bash

# Email System Verification Script
# This script checks if the email migration was successful

echo "================================================"
echo "🔍 Sneaky Klean Email System Verification"
echo "================================================"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check 1: Email utility file exists
echo "1. Checking email utility file..."
if [ -f "core/email_utils.py" ]; then
    echo -e "${GREEN}✓${NC} core/email_utils.py exists"
else
    echo -e "${RED}✗${NC} core/email_utils.py not found"
    exit 1
fi

# Check 2: Python syntax validation
echo ""
echo "2. Validating Python syntax..."
if python3 -m py_compile core/email_utils.py accounts/emails.py orders/emails.py 2>/dev/null; then
    echo -e "${GREEN}✓${NC} All email files have valid syntax"
else
    echo -e "${RED}✗${NC} Syntax errors found in email files"
    exit 1
fi

# Check 3: Check for old SMTP imports
echo ""
echo "3. Checking for old SMTP imports..."
if grep -r "from django.core.mail import send_mail" accounts/emails.py orders/emails.py 2>/dev/null; then
    echo -e "${RED}✗${NC} Old SMTP imports found - migration incomplete"
    exit 1
else
    echo -e "${GREEN}✓${NC} No old SMTP imports found"
fi

# Check 4: Check for new API imports
echo ""
echo "4. Checking for new API imports..."
if grep -q "from core.email_utils import send_email" accounts/emails.py && \
   grep -q "from core.email_utils import send_email" orders/emails.py; then
    echo -e "${GREEN}✓${NC} New API imports found in all email files"
else
    echo -e "${RED}✗${NC} API imports missing in email files"
    exit 1
fi

# Check 5: Verify requests in requirements.txt
echo ""
echo "5. Checking dependencies..."
if grep -q "requests" requirements.txt; then
    echo -e "${GREEN}✓${NC} requests package in requirements.txt"
else
    echo -e "${RED}✗${NC} requests package missing from requirements.txt"
    exit 1
fi

# Check 6: Check .env.example
echo ""
echo "6. Checking environment configuration..."
if grep -q "ZEPTO_API_KEY" .env.example && \
   grep -q "ZEPTO_API_BASE_URL" .env.example; then
    echo -e "${GREEN}✓${NC} ZeptoMail variables in .env.example"
else
    echo -e "${YELLOW}⚠${NC} ZeptoMail variables missing from .env.example"
fi

# Check 7: Verify settings.py
echo ""
echo "7. Checking Django settings..."
if grep -q "ZEPTO_API_KEY" sneakyklean/settings.py && \
   grep -q "ZEPTO_API_BASE_URL" sneakyklean/settings.py; then
    echo -e "${GREEN}✓${NC} ZeptoMail configuration in settings.py"
else
    echo -e "${RED}✗${NC} ZeptoMail configuration missing from settings.py"
    exit 1
fi

# Check 8: Check for old EMAIL_HOST in settings
echo ""
echo "8. Checking for old SMTP configuration..."
if grep -q "EMAIL_HOST = config('EMAIL_HOST'" sneakyklean/settings.py; then
    echo -e "${YELLOW}⚠${NC} Old SMTP configuration still in settings.py"
else
    echo -e "${GREEN}✓${NC} Old SMTP configuration removed"
fi

# Check 9: Documentation files
echo ""
echo "9. Checking documentation..."
doc_files=("EMAIL_MIGRATION.md" "EMAIL_MIGRATION_SUMMARY.md" "README.md")
all_docs_exist=true
for doc in "${doc_files[@]}"; do
    if [ -f "$doc" ]; then
        echo -e "${GREEN}✓${NC} $doc exists"
    else
        echo -e "${YELLOW}⚠${NC} $doc not found"
        all_docs_exist=false
    fi
done

echo ""
echo "================================================"
echo "✅ Email System Migration Verification Complete"
echo "================================================"
echo ""
echo "📋 Next Steps:"
echo "1. Start Docker Desktop"
echo "2. Run: docker-compose build"
echo "3. Create .env file with ZeptoMail API key"
echo "4. Run: docker-compose up -d"
echo "5. Test email sending in Django shell"
echo ""
echo "📖 For detailed instructions, see:"
echo "   - EMAIL_MIGRATION.md (setup guide)"
echo "   - EMAIL_MIGRATION_SUMMARY.md (changes summary)"
echo "   - README.md (updated documentation)"
echo ""
