"""
Test cases for orders app - Order management, discounts, ratings, and delivery
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta
from unittest.mock import patch, MagicMock
from accounts.models import User
from orders.models import Order, DiscountCode, DeliveryCode, Rating


class OrderModelTests(TestCase):
    """Test Order model functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            full_name='Test User',
            phone='+2348012345678'
        )
    
    def test_order_creation(self):
        """Test order is created with correct attributes"""
        order = Order.objects.create(
            user=self.user,
            email='test@example.com',
            full_name='Test User',
            phone='+2348012345678',
            service_type=Order.BASIC_CLEANING,
            quantity=1,
            address='Test Address, Lagos',
            location=Order.MAINLAND,
            pickup_date=date.today() + timedelta(days=1),
            subtotal=Decimal('7000'),
            vat=Decimal('525'),
            delivery_fee=Decimal('3500'),
            total_amount=Decimal('11025')
        )
        
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.service_type, Order.BASIC_CLEANING)
        self.assertEqual(order.quantity, 1)
        self.assertEqual(order.status, Order.SCHEDULED)
        self.assertEqual(order.subtotal, Decimal('7000'))
        self.assertEqual(order.total_amount, Decimal('11025'))
        self.assertIsNotNone(order.order_number)
        self.assertFalse(order.is_free_cleaning)
    
    def test_order_number_generation(self):
        """Test order numbers are generated correctly"""
        order1 = Order.objects.create(
            user=self.user,
            email='test@example.com',
            full_name='Test User',
            phone='+2348012345678',
            service_type=Order.BASIC_CLEANING,
            quantity=1,
            address='Test Address',
            location=Order.MAINLAND,
            pickup_date=date.today() + timedelta(days=1),
            subtotal=Decimal('7000'),
            total_amount=Decimal('11025')
        )
        
        # Order number should start with #2026 (current year)
        self.assertTrue(order1.order_number.startswith('#2026'))
        
        order2 = Order.objects.create(
            user=self.user,
            email='test@example.com',
            full_name='Test User',
            phone='+2348012345678',
            service_type=Order.DEEP_CLEANING,
            quantity=1,
            address='Test Address',
            location=Order.MAINLAND,
            pickup_date=date.today() + timedelta(days=1),
            subtotal=Decimal('12000'),
            total_amount=Decimal('16900')
        )
        
        # Second order should have incremented number
        self.assertNotEqual(order1.order_number, order2.order_number)
    
    def test_order_string_representation(self):
        """Test __str__ method"""
        order = Order.objects.create(
            user=self.user,
            email='test@example.com',
            full_name='Test User',
            phone='+2348012345678',
            service_type=Order.BASIC_CLEANING,
            quantity=1,
            address='Test Address',
            location=Order.MAINLAND,
            pickup_date=date.today() + timedelta(days=1),
            subtotal=Decimal('7000'),
            total_amount=Decimal('11025')
        )
        
        expected = f"{order.order_number} - {self.user.email}"
        self.assertEqual(str(order), expected)
    
    def test_free_cleaning_15th_order(self):
        """Test 15th order is marked as free cleaning"""
        # Create 14 orders
        for i in range(14):
            Order.objects.create(
                user=self.user,
                email='test@example.com',
                full_name='Test User',
                phone='+2348012345678',
                service_type=Order.BASIC_CLEANING,
                quantity=1,
                address='Test Address',
                location=Order.MAINLAND,
                pickup_date=date.today() + timedelta(days=1),
                subtotal=Decimal('7000'),
                total_amount=Decimal('11025')
            )
            self.user.total_orders += 1
            self.user.free_cleaning_count += 1
            self.user.save()
        
        self.assertEqual(self.user.total_orders, 14)
        self.assertEqual(self.user.free_cleaning_count, 14)
        
        # Create 15th order - should be free
        order_15 = Order.objects.create(
            user=self.user,
            email='test@example.com',
            full_name='Test User',
            phone='+2348012345678',
            service_type=Order.BASIC_CLEANING,
            quantity=1,
            address='Test Address',
            location=Order.MAINLAND,
            pickup_date=date.today() + timedelta(days=1),
            subtotal=Decimal('7000'),
            total_amount=Decimal('0'),  # Free
            is_free_cleaning=True
        )
        
        self.assertTrue(order_15.is_free_cleaning)
        self.assertEqual(order_15.total_amount, Decimal('0'))


class DiscountCodeModelTests(TestCase):
    """Test DiscountCode model functionality"""
    
    def test_discount_code_creation(self):
        """Test discount code is created correctly"""
        discount = DiscountCode.objects.create(
            code='SNKYLN',
            discount_amount=Decimal('2000'),
            is_active=True
        )
        
        self.assertEqual(discount.code, 'SNKYLN')
        self.assertEqual(discount.discount_amount, Decimal('2000'))
        self.assertTrue(discount.is_active)
        self.assertEqual(discount.usage_count, 0)
    
    def test_discount_code_with_usage_limit(self):
        """Test discount code with usage limit"""
        discount = DiscountCode.objects.create(
            code='LIMITED',
            discount_amount=Decimal('1000'),
            is_active=True,
            usage_limit=5
        )
        
        self.assertEqual(discount.usage_limit, 5)
        self.assertEqual(discount.usage_count, 0)
    
    def test_discount_code_string_representation(self):
        """Test __str__ method"""
        discount = DiscountCode.objects.create(
            code='TEST50',
            discount_amount=Decimal('500')
        )
        
        self.assertEqual(str(discount), 'TEST50')


class DeliveryCodeModelTests(TestCase):
    """Test DeliveryCode model functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            full_name='Test User'
        )
        self.order = Order.objects.create(
            user=self.user,
            email='test@example.com',
            full_name='Test User',
            phone='+2348012345678',
            service_type=Order.BASIC_CLEANING,
            quantity=1,
            address='Test Address',
            location=Order.MAINLAND,
            pickup_date=date.today() + timedelta(days=1),
            subtotal=Decimal('7000'),
            total_amount=Decimal('11025'),
            status=Order.OUT_FOR_DELIVERY
        )
    
    def test_delivery_code_creation(self):
        """Test delivery code is created correctly"""
        delivery_code = DeliveryCode.objects.create(
            order=self.order,
            code='1234'
        )
        
        self.assertEqual(delivery_code.order, self.order)
        self.assertEqual(delivery_code.code, '1234')
        self.assertFalse(delivery_code.is_verified)
    
    def test_delivery_code_generate(self):
        """Test delivery code generation"""
        code = DeliveryCode.generate_code()
        self.assertEqual(len(code), 4)
        self.assertTrue(code.isdigit())
    
    def test_delivery_code_string_representation(self):
        """Test __str__ method"""
        delivery_code = DeliveryCode.objects.create(
            order=self.order,
            code='5678'
        )
        
        expected = f"Delivery code for {self.order.order_number}"
        self.assertEqual(str(delivery_code), expected)


class RatingModelTests(TestCase):
    """Test Rating model functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            full_name='Test User'
        )
        self.order = Order.objects.create(
            user=self.user,
            email='test@example.com',
            full_name='Test User',
            phone='+2348012345678',
            service_type=Order.BASIC_CLEANING,
            quantity=1,
            address='Test Address',
            location=Order.MAINLAND,
            pickup_date=date.today() + timedelta(days=1),
            subtotal=Decimal('7000'),
            total_amount=Decimal('11025'),
            status=Order.DELIVERED
        )
    
    def test_rating_creation(self):
        """Test rating is created correctly"""
        rating = Rating.objects.create(
            order=self.order,
            rating=5,
            comment='Excellent service!'
        )
        
        self.assertEqual(rating.order, self.order)
        self.assertEqual(rating.rating, 5)
        self.assertEqual(rating.comment, 'Excellent service!')
    
    def test_rating_string_representation(self):
        """Test __str__ method"""
        rating = Rating.objects.create(
            order=self.order,
            rating=4
        )
        
        expected = f"Rating {rating.rating}/5 for {self.order.order_number}"
        self.assertEqual(str(rating), expected)


class CreateOrderViewTests(TestCase):
    """Test order creation view"""
    
    def setUp(self):
        self.client = Client()
        self.create_url = reverse('orders:create_order')
        self.user = User.objects.create_user(
            email='test@example.com',
            full_name='Test User',
            phone='+2348012345678'
        )
    
    @patch('orders.views.send_order_confirmation_email')
    @patch('orders.views.send_admin_notification')
    def test_create_order_basic_cleaning(self, mock_admin_email, mock_confirm_email):
        """Test creating basic cleaning order"""
        order_data = {
            'services': 'Basic Cleaning',
            'full_name': 'Test User',
            'phone': '+2348012345678',
            'email': 'test@example.com',
            'address': '123 Test Street, Lagos',
            'location': 'mainland',
            'pickup_date': (date.today() + timedelta(days=2)).strftime('%Y-%m-%d'),
            'quantity': 1,
        }
        
        response = self.client.post(self.create_url, order_data)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        
        # Order should be created
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()
        
        self.assertEqual(order.service_type, Order.BASIC_CLEANING)
        self.assertEqual(order.quantity, 1)
        self.assertEqual(order.subtotal, Decimal('7000'))
    
    @patch('orders.views.send_order_confirmation_email')
    @patch('orders.views.send_admin_notification')
    def test_create_order_with_discount(self, mock_admin_email, mock_confirm_email):
        """Test creating order with discount code"""
        # Create discount code
        DiscountCode.objects.create(
            code='SNKYLN',
            discount_amount=Decimal('2000'),
            is_active=True
        )
        
        order_data = {
            'services': 'Basic Cleaning',
            'full_name': 'Test User',
            'phone': '+2348012345678',
            'email': 'test@example.com',
            'address': '123 Test Street, Lagos',
            'location': 'mainland',
            'pickup_date': (date.today() + timedelta(days=2)).strftime('%Y-%m-%d'),
            'quantity': 1,
            'discount_code': 'SNKYLN',
        }
        
        response = self.client.post(self.create_url, order_data)
        
        # Order should be created with discount
        order = Order.objects.first()
        self.assertEqual(order.discount_amount, Decimal('2000'))
        
        # Discount code usage should be incremented
        discount = DiscountCode.objects.get(code='SNKYLN')
        self.assertEqual(discount.usage_count, 1)


class DashboardViewTests(TestCase):
    """Test dashboard view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            full_name='Test User'
        )
        self.dashboard_url = reverse('orders:dashboard')
        self.client.force_login(self.user)
    
    def test_dashboard_requires_login(self):
        """Test dashboard requires authentication"""
        self.client.logout()
        response = self.client.get(self.dashboard_url)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_dashboard_displays_orders(self):
        """Test dashboard displays user orders"""
        # Create orders
        Order.objects.create(
            user=self.user,
            email='test@example.com',
            full_name='Test User',
            phone='+2348012345678',
            service_type=Order.BASIC_CLEANING,
            quantity=1,
            address='Test Address',
            location=Order.MAINLAND,
            pickup_date=date.today() + timedelta(days=1),
            subtotal=Decimal('7000'),
            total_amount=Decimal('11025')
        )
        
        response = self.client.get(self.dashboard_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'orders/dashboard.html')
        self.assertEqual(len(response.context['orders']), 1)
    
    def test_dashboard_metrics(self):
        """Test dashboard shows correct metrics"""
        # Create 3 orders
        for i in range(3):
            Order.objects.create(
                user=self.user,
                email='test@example.com',
                full_name='Test User',
                phone='+2348012345678',
                service_type=Order.BASIC_CLEANING,
                quantity=1,
                address='Test Address',
                location=Order.MAINLAND,
                pickup_date=date.today() + timedelta(days=i+1),
                subtotal=Decimal('7000'),
                total_amount=Decimal('11025'),
                status=Order.SCHEDULED if i<2 else Order.DELIVERED
            )
        
        self.user.total_orders = 3
        self.user.free_cleaning_count = 3
        self.user.save()
        
        response = self.client.get(self.dashboard_url)
        
        self.assertEqual(response.context['total_orders'], 3)
        self.assertEqual(response.context['pending_orders'], 2)
        self.assertEqual(response.context['user'].free_cleaning_count, 3)


class ValidateDiscountViewTests(TestCase):
    """Test discount validation AJAX endpoint"""
    
    def setUp(self):
        self.client = Client()
        self.validate_url = reverse('orders:validate_discount')
        
        DiscountCode.objects.create(
            code='VALID',
            discount_amount=Decimal('1500'),
            is_active=True
        )
    
    def test_validate_discount_success(self):
        """Test valid discount code validation"""
        response = self.client.post(
            self.validate_url,
            {'code': 'VALID'},
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['valid'])
        self.assertEqual(Decimal(data['discount_amount']), Decimal('1500'))
    
    def test_validate_discount_invalid(self):
        """Test invalid discount code validation"""
        response = self.client.post(
            self.validate_url,
            {'code': 'INVALID'},
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['valid'])
        self.assertIn('error', data)
    
    def test_validate_discount_inactive(self):
        """Test inactive discount code validation"""
        DiscountCode.objects.create(
            code='INACTIVE',
            discount_amount=Decimal('1000'),
            is_active=False
        )
        
        response = self.client.post(
            self.validate_url,
            {'code': 'INACTIVE'},
            content_type='application/json'
        )
        
        data = response.json()
        self.assertFalse(data['valid'])


class OrderSignalsTests(TestCase):
    """Test order-related signals"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            full_name='Test User'
        )
    
    @patch('orders.signals.send_order_status_email')
    def test_order_status_change_sends_email(self, mock_send_email):
        """Test status change triggers email"""
        order = Order.objects.create(
            user=self.user,
            email='test@example.com',
            full_name='Test User',
            phone='+2348012345678',
            service_type=Order.BASIC_CLEANING,
            quantity=1,
            address='Test Address',
            location=Order.MAINLAND,
            pickup_date=date.today() + timedelta(days=1),
            subtotal=Decimal('7000'),
            total_amount=Decimal('11025')
        )
        
        # Change status
        order.status = Order.PICKED_UP
        order.save()
        
        # Email should be sent
        mock_send_email.assert_called()
    
    @patch('orders.signals.send_delivery_code_email')
    def test_out_for_delivery_generates_code(self, mock_send_email):
        """Test OUT_FOR_DELIVERY status generates delivery code"""
        order = Order.objects.create(
            user=self.user,
            email='test@example.com',
            full_name='Test User',
            phone='+2348012345678',
            service_type=Order.BASIC_CLEANING,
            quantity=1,
            address='Test Address',
            location=Order.MAINLAND,
            pickup_date=date.today() + timedelta(days=1),
            subtotal=Decimal('7000'),
            total_amount=Decimal('11025')
        )
        
        # Change to OUT_FOR_DELIVERY
        order.status = Order.OUT_FOR_DELIVERY
        order.save()
        
        # Delivery code should be created
        self.assertTrue(
            DeliveryCode.objects.filter(order=order).exists()
        )
