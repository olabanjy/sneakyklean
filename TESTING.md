# Sneaky Klean - Testing Documentation

## Overview

Comprehensive test suite for the Sneaky Klean platform covering all features including authentication, order management, email system, and business logic.

## Test Coverage

### Accounts App (`accounts/tests.py`)

#### UserModelTests (7 tests)
- ✅ User creation with correct attributes
- ✅ User string representation
- ✅ Email as username field validation
- ✅ Superuser creation
- ✅ Free cleaning counter increment logic

#### OTPModelTests (7 tests)
- ✅ OTP creation with correct attributes
- ✅ OTP code generation (6-digit)
- ✅ OTP not expired within 5 minutes
- ✅ OTP expired after 5 minutes
- ✅ OTP string representation
- ✅ OTP marked as used functionality

#### LoginViewTests (6 tests)
- ✅ Login page renders correctly
- ✅ Login creates user if email doesn't exist
- ✅ Login generates 6-digit OTP code
- ✅ Login sends OTP email
- ✅ OTP rate limiting (3 per hour)
- ✅ Login with invalid email format

#### VerifyOTPViewTests (5 tests)
- ✅ Verify OTP page renders
- ✅ Successful OTP verification and login
- ✅ Invalid OTP code handling
- ✅ Expired OTP handling
- ✅ Already used OTP handling

#### LogoutViewTests (1 test)
- ✅ User logout functionality

**Total Accounts Tests: 26**

### Orders App (`orders/tests.py`)

#### OrderModelTests (4 tests)
- ✅ Order creation with correct attributes
- ✅ Order number auto-generation with year prefix
- ✅ Order string representation
- ✅ 15th order marked as free cleaning

#### DiscountCodeModelTests (3 tests)
- ✅ Discount code creation
- ✅ Discount code with usage limit
- ✅ Discount code string representation

#### DeliveryCodeModelTests (3 tests)
- ✅ Delivery code creation
- ✅ Delivery code generation (4-digit)
- ✅ Delivery code string representation

#### RatingModelTests (2 tests)
- ✅ Rating creation with order link
- ✅ Rating string representation

#### CreateOrderViewTests (2 tests)
- ✅ Create basic cleaning order
- ✅ Create order with discount code application

#### DashboardViewTests (3 tests)
- ✅ Dashboard requires authentication
- ✅ Dashboard displays user orders
- ✅ Dashboard shows correct metrics (total, pending, free cleaning progress)

#### ValidateDiscountViewTests (3 tests)
- ✅ Valid discount code validation (AJAX)
- ✅ Invalid discount code handling
- ✅ Inactive discount code rejection

#### OrderSignalsTests (2 tests)
- ✅ Order status change triggers email
- ✅ OUT_FOR_DELIVERY status generates delivery code

**Total Orders Tests: 22**

### Core App (`core/tests.py`)

#### LandingPageTests (2 tests)
- ✅ Landing page loads successfully
- ✅ Landing page contains service information

#### EmailUtilsTests (12 tests)
- ✅ Parse single email address
- ✅ Parse email with display name
- ✅ Parse list of email addresses
- ✅ Parse invalid email with quiet mode
- ✅ Parse from address with name
- ✅ Prepare body content (text only)
- ✅ Prepare body content (HTML only)
- ✅ Prepare body content (both text and HTML)
- ✅ Get API config with valid settings
- ✅ Get API config with missing settings
- ✅ Build attachments
- ✅ Build empty attachments

#### ZeptoMailAPITests (4 tests)
- ✅ Send email successfully via API
- ✅ Handle API error response
- ✅ send_email wrapper function
- ✅ Auto-generate HTML from text

#### EmailIntegrationTests (1 test)
- ✅ Full email sending flow integration

**Total Core Tests: 19**

## Test Summary

| App      | Test Classes | Test Methods | Coverage Areas                                    |
|----------|--------------|--------------|---------------------------------------------------|
| Accounts | 5            | 26           | Auth, OTP, Rate Limiting, Login/Logout           |
| Orders   | 8            | 22           | Orders, Discounts, Delivery, Ratings, Signals    |
| Core     | 4            | 19           | Landing Page, Email API, Utils                    |
| **Total**| **17**       | **67**       | **All major features**                            |

## Running Tests

### Run All Tests

```bash
# Using Docker
docker-compose run --rm web python manage.py test

# Or with verbose output
docker-compose run --rm web python manage.py test --verbosity=2
```

### Run Specific App Tests

```bash
# Accounts tests only
docker-compose run --rm web python manage.py test accounts

# Orders tests only
docker-compose run --rm web python manage.py test orders

# Core tests only
docker-compose run --rm web python manage.py test core
```

### Run Specific Test Class

```bash
# Run only UserModelTests
docker-compose run --rm web python manage.py test accounts.tests.UserModelTests

# Run only OrderModelTests
docker-compose run --rm web python manage.py test orders.tests.OrderModelTests
```

### Run Specific Test Method

```bash
# Run single test
docker-compose run --rm web python manage.py test accounts.tests.UserModelTests.test_user_creation
```

### Generate Coverage Report

```bash
# Install coverage
docker-compose run --rm web pip install coverage

# Run with coverage
docker-compose run --rm web coverage run --source='.' manage.py test

# Generate report
docker-compose run --rm web coverage report

# Generate HTML report
docker-compose run --rm web coverage html
# View at htmlcov/index.html
```

## Test Execution Script

A convenience script (`run_tests.sh`) is provided:

```bash
# Make executable
chmod +x run_tests.sh

# Run all tests
./run_tests.sh

# Run with coverage
./run_tests.sh --coverage

# Run specific app
./run_tests.sh accounts
```

## Test Fixtures

### Mock Email Sending

All email tests use `@patch` decorators to mock email sending:

```python
@patch('accounts.views.send_otp_email')
def test_login_sends_email(self, mock_send_email):
    # Email function is mocked - no actual emails sent
    pass
```

### Test Data

Tests create their own data using Django's TestCase:

```python
def setUp(self):
    self.user = User.objects.create_user(
        email='test@example.com',
        full_name='Test User'
    )
```

All test data is automatically cleaned up after each test.

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Build Docker
      run: docker-compose build
    
    - name: Run tests
      run: docker-compose run --rm web python manage.py test
```

## Test Best Practices

### 1. Isolation
Each test is independent and doesn't rely on other tests.

### 2. Mocking
External services (email, API calls) are mocked to avoid dependencies.

### 3. Clear Names
Test names clearly describe what is being tested:
```python
def test_otp_expired_after_5_minutes(self):
    # Clear what this tests
```

### 4. Arrange-Act-Assert
Tests follow AAA pattern:
```python
def test_user_creation(self):
    # Arrange
    user = User.objects.create_user(...)
    
    # Act (implicit in creation)
    
    # Assert
    self.assertEqual(user.email, 'test@example.com')
```

### 5. Coverage
Aim for high coverage of critical paths:
- Authentication flow: 100%
- Order creation: 100%
- Free cleaning logic: 100%
- Email sending: 100%

## Testing Features

### Authentication
- ✅ Passwordless OTP login
- ✅ OTP expiration (5 minutes)
- ✅ OTP rate limiting (3 per hour)
- ✅ Email validation

### Order Management
- ✅ Order creation with pricing
- ✅ Discount code validation
- ✅ Free cleaning every 15th order
- ✅ Order number generation
- ✅ Delivery code generation

### Email System
- ✅ ZeptoMail API integration
- ✅ Email sending with HTML/text
- ✅ Attachment handling
- ✅ Error handling with quiet mode

### Admin Features
- ✅ Status change notifications
- ✅ Admin email notifications
- ✅ Bulk order actions

## Troubleshooting Tests

### Database Errors
Tests use in-memory SQLite by default. If you need PostgreSQL:

```python
# In test settings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'test_db',
        'USER': 'test_user',
        'PASSWORD': 'test_pass',
        'HOST': 'db',
        'PORT': '5432',
    }
}
```

### Import Errors
Ensure all dependencies are installed:
```bash
docker-compose run --rm web pip install -r requirements.txt
```

### Test Failures
Run with verbose output to see details:
```bash
docker-compose run --rm web python manage.py test --verbosity=2 --failfast
```

### Slow Tests
Run tests in parallel:
```bash
docker-compose run --rm web python manage.py test --parallel
```

## Future Test Additions

Planned test coverage:
- [ ] API rate limiting tests
- [ ] File upload tests (if added)
- [ ] Payment integration tests (if added)
- [ ] Performance/load tests
- [ ] Security tests (CSRF, XSS, SQL injection)
- [ ] Browser tests with Selenium (E2E)

## Contributing Tests

When adding new features:

1. **Write tests first** (TDD approach)
2. **Ensure all tests pass** before committing
3. **Aim for 80%+ coverage** on new code
4. **Test edge cases** and error conditions
5. **Document complex test logic**

Example:
```python
def test_new_feature(self):
    """
    Test that new feature works correctly.
    
    This test covers the edge case where...
    """
    # Test implementation
```

## Test Maintenance

- Review tests when requirements change
- Update mocks when external APIs change
- Remove obsolete tests
- Refactor duplicated test code into helpers
- Keep test data realistic but minimal

## Resources

- [Django Testing Docs](https://docs.djangoproject.com/en/5.0/topics/testing/)
- [Python unittest](https://docs.python.org/3/library/unittest.html)
- [Coverage.py](https://coverage.readthedocs.io/)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
