"""
Test cases for accounts app - User authentication and OTP functionality
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta
from unittest.mock import patch, MagicMock
from accounts.models import User, OTP


class UserModelTests(TestCase):
    """Test User model functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            full_name='Test User',
            phone='+2348012345678'
        )
    
    def test_user_creation(self):
        """Test user is created with correct attributes"""
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertEqual(self.user.full_name, 'Test User')
        self.assertEqual(self.user.phone, '+2348012345678')
        self.assertEqual(self.user.total_orders, 0)
        self.assertEqual(self.user.free_cleaning_count, 0)
        self.assertFalse(self.user.is_staff)
        self.assertTrue(self.user.is_active)
    
    def test_user_string_representation(self):
        """Test __str__ method"""
        self.assertEqual(str(self.user), 'test@example.com')
    
    def test_email_is_username(self):
        """Test email is used as username field"""
        self.assertEqual(User.USERNAME_FIELD, 'email')
    
    def test_superuser_creation(self):
        """Test superuser creation"""
        admin = User.objects.create_superuser(
            email='admin@example.com',
            password='admin123'
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_active)
    
    def test_free_cleaning_counter_increment(self):
        """Test free cleaning counter increments correctly"""
        self.user.total_orders = 10
        self.user.free_cleaning_count = 10
        self.user.save()
        
        self.assertEqual(self.user.free_cleaning_count, 10)
        
        # Increment to 15
        self.user.total_orders = 15
        self.user.free_cleaning_count = 15
        self.user.save()
        
        self.assertEqual(self.user.free_cleaning_count, 15)


class OTPModelTests(TestCase):
    """Test OTP model functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            full_name='Test User'
        )
        self.otp = OTP.objects.create(
            user=self.user,
            code='123456'
        )
    
    def test_otp_creation(self):
        """Test OTP is created correctly"""
        self.assertEqual(self.otp.user, self.user)
        self.assertEqual(self.otp.code, '123456')
        self.assertFalse(self.otp.is_used)
        self.assertIsNotNone(self.otp.created_at)
    
    def test_otp_generate_code(self):
        """Test OTP code generation"""
        code = OTP.generate_code()
        self.assertEqual(len(code), 6)
        self.assertTrue(code.isdigit())
    
    def test_otp_not_expired_within_5_minutes(self):
        """Test OTP is not expired within 5 minutes"""
        self.assertFalse(self.otp.is_expired())
    
    def test_otp_expired_after_5_minutes(self):
        """Test OTP expires after 5 minutes"""
        # Set created_at to 6 minutes ago
        self.otp.created_at = timezone.now() - timedelta(minutes=6)
        self.otp.save()
        self.assertTrue(self.otp.is_expired())
    
    def test_otp_string_representation(self):
        """Test __str__ method"""
        expected = f"OTP for {self.user.email} - 123456"
        self.assertEqual(str(self.otp), expected)
    
    def test_otp_marked_as_used(self):
        """Test OTP can be marked as used"""
        self.assertFalse(self.otp.is_used)
        self.otp.is_used = True
        self.otp.save()
        self.assertTrue(self.otp.is_used)


class LoginViewTests(TestCase):
    """Test login view and OTP email sending"""
    
    def setUp(self):
        self.client = Client()
        self.login_url = reverse('accounts:login')
        cache.clear()  # Clear cache before each test
    
    @patch('accounts.views.send_otp_email')
    def test_login_page_get(self, mock_send_email):
        """Test login page renders correctly"""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')
    
    @patch('accounts.views.send_otp_email')
    def test_login_creates_user_if_not_exists(self, mock_send_email):
        """Test login creates new user if email doesn't exist"""
        self.assertEqual(User.objects.count(), 0)
        
        response = self.client.post(self.login_url, {
            'email': 'newuser@example.com'
        })
        
        self.assertEqual(User.objects.count(), 1)
        user = User.objects.first()
        self.assertEqual(user.email, 'newuser@example.com')
    
    @patch('accounts.views.send_otp_email')
    def test_login_generates_otp(self, mock_send_email):
        """Test login generates OTP code"""
        response = self.client.post(self.login_url, {
            'email': 'test@example.com'
        })
        
        user = User.objects.get(email='test@example.com')
        otp = OTP.objects.filter(user=user, is_used=False).latest('created_at')
        
        self.assertIsNotNone(otp)
        self.assertEqual(len(otp.code), 6)
        self.assertTrue(otp.code.isdigit())
    
    @patch('accounts.views.send_otp_email')
    def test_login_sends_email(self, mock_send_email):
        """Test login sends OTP email"""
        response = self.client.post(self.login_url, {
            'email': 'test@example.com'
        })
        
        user = User.objects.get(email='test@example.com')
        mock_send_email.assert_called_once()
        # Check that user was passed to email function
        call_args = mock_send_email.call_args[0]
        self.assertEqual(call_args[0], user)
    
    @patch('accounts.views.send_otp_email')
    def test_login_rate_limiting(self, mock_send_email):
        """Test OTP rate limiting (3 per hour)"""
        email = 'ratelimit@example.com'
        
        # Send 3 OTPs successfully
        for i in range(3):
            response = self.client.post(self.login_url, {'email': email})
            self.assertEqual(response.status_code, 302)  # Redirect to verify OTP
        
        # 4th attempt should be rate limited
        response = self.client.post(self.login_url, {'email': email})
        messages = list(response.wsgi_request._messages)
        
        # Check for rate limit message
        self.assertTrue(
            any('Too many' in str(m) or 'limit' in str(m).lower() 
                for m in messages)
        )
    
    @patch('accounts.views.send_otp_email')
    def test_login_invalid_email(self, mock_send_email):
        """Test login with invalid email format"""
        response = self.client.post(self.login_url, {
            'email': 'invalid-email'
        })
        
        # Should still be on login page or show error
        self.assertIn(response.status_code, [200, 302])


class VerifyOTPViewTests(TestCase):
    """Test OTP verification view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            full_name='Test User'
        )
        self.otp = OTP.objects.create(
            user=self.user,
            code='123456'
        )
        self.verify_url = reverse('accounts:verify_otp')
        
        # Store email in session (simulating login flow)
        session = self.client.session
        session['otp_email'] = self.user.email
        session.save()
    
    def test_verify_otp_get(self):
        """Test verify OTP page renders"""
        response = self.client.get(self.verify_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/verify_otp.html')
    
    def test_verify_otp_success(self):
        """Test successful OTP verification"""
        response = self.client.post(self.verify_url, {
            'otp': '123456'
        })
        
        # Should redirect to dashboard
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('orders:dashboard'))
        
        # OTP should be marked as used
        self.otp.refresh_from_db()
        self.assertTrue(self.otp.is_used)
        
        # User should be logged in
        self.assertIn('_auth_user_id', self.client.session)
    
    def test_verify_otp_invalid_code(self):
        """Test OTP verification with invalid code"""
        response = self.client.post(self.verify_url, {
            'otp': '999999'
        })
        
        # Should stay on verify page with error
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertTrue(len(messages) > 0)
    
    def test_verify_otp_expired(self):
        """Test OTP verification with expired code"""
        # Set OTP as expired
        self.otp.created_at = timezone.now() - timedelta(minutes=6)
        self.otp.save()
        
        response = self.client.post(self.verify_url, {
            'otp': '123456'
        })
        
        # Should show error
        messages = list(response.wsgi_request._messages)
        self.assertTrue(
            any('expired' in str(m).lower() for m in messages)
        )
    
    def test_verify_otp_already_used(self):
        """Test OTP verification with already used code"""
        self.otp.is_used = True
        self.otp.save()
        
        response = self.client.post(self.verify_url, {
            'otp': '123456'
        })
        
        # Should show error
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertTrue(len(messages) > 0)


class LogoutViewTests(TestCase):
    """Test logout functionality"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            full_name='Test User'
        )
        self.logout_url = reverse('accounts:logout')
        
        # Log user in
        self.client.force_login(self.user)
    
    def test_logout(self):
        """Test user logout"""
        # Verify user is logged in
        self.assertIn('_auth_user_id', self.client.session)
        
        # Logout
        response = self.client.get(self.logout_url)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        
        # User should be logged out
        self.assertNotIn('_auth_user_id', self.client.session)
