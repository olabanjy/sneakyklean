from django.db import models
from django.utils import timezone
from django.conf import settings
import secrets
from datetime import datetime


class Service(models.Model):
    """Service catalog - cleaning services offered by Sneaky Klean."""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, help_text="Service description for customers")
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Base price for this service")
    is_active = models.BooleanField(default=True, help_text="Display this service on website")
    display_order = models.IntegerField(default=0, help_text="Order for display on frontend (lower = first)")
    
    # Optional features
    icon = models.CharField(max_length=50, blank=True, help_text="CSS icon class")
    estimated_duration = models.CharField(max_length=50, blank=True, help_text="e.g., '2-3 hours'")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    
    def __str__(self):
        return f"{self.name} - ₦{self.price:,.0f}"


class Order(models.Model):
    """Order model for sneaker cleaning services."""
    
    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('PICKED_UP', 'Picked Up'),
        ('CLEANING', 'Cleaning'),
        ('OUT_FOR_DELIVERY', 'Out for Delivery'),
        ('DELIVERED', 'Delivered'),
        ('CANCELED', 'Canceled'),
        ('DELAYED', 'Delayed'),
    ]
    
    SERVICE_CHOICES = [
        ('Basic Cleaning', 'Basic Cleaning'),
        ('Deep Cleaning', 'Deep Cleaning'),
        ('Restoration', 'Restoration'),
        ('Suede Care', 'Suede Care'),
    ]
    
    LOCATION_CHOICES = [
        ('mainland', 'Mainland'),
        ('island', 'Island'),
    ]
    
    # Order identification
    order_number = models.CharField(max_length=20, unique=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    
    # Service details
    service_type = models.CharField(max_length=50, choices=SERVICE_CHOICES)
    quantity = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')
    
    # Customer details
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    location = models.CharField(max_length=20, choices=LOCATION_CHOICES)
    
    # Dates
    pickup_date = models.DateField()
    delivery_date = models.DateField(null=True, blank=True)
    
    # Pricing
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    vat = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=3500)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Additional
    special_instructions = models.TextField(blank=True)
    is_free_cleaning = models.BooleanField(default=False)
    
    # Cancellation
    cancellation_requested = models.BooleanField(default=False)
    cancellation_reason = models.TextField(blank=True)
    cancellation_requested_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.order_number} - {self.user.email}"
    
    def save(self, *args, **kwargs):
        """Generate order number if not exists."""
        if not self.order_number:
            self.order_number = self.generate_order_number()
        
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_order_number():
        """Generate unique order number format: #YYYY{sequential}"""
        current_year = datetime.now().year
        year_prefix = f'#{current_year}'
        
        # Get all orders for current year and find highest sequential number
        orders_this_year = Order.objects.filter(
            order_number__startswith=year_prefix
        ).values_list('order_number', flat=True)
        
        if orders_this_year:
            # Extract sequential numbers and find the maximum
            sequential_numbers = []
            for order_num in orders_this_year:
                try:
                    # Extract number after #YYYY (position 5 onwards)
                    seq_num = int(order_num[5:])
                    sequential_numbers.append(seq_num)
                except (ValueError, IndexError):
                    continue
            
            if sequential_numbers:
                new_num = max(sequential_numbers) + 1
            else:
                new_num = 1
        else:
            new_num = 1
        
        return f'#{current_year}{new_num}'
    
    def get_status_display_color(self):
        """Return color for status display."""
        colors = {
            'SCHEDULED': '#fc6809',
            'PICKED_UP': '#2f80ed',
            'CLEANING': '#2f80ed',
            'OUT_FOR_DELIVERY': '#018b51',
            'DELIVERED': '#000',
            'CANCELED': '#ff0000',
            'DELAYED': '#f2a531',
        }
        return colors.get(self.status, '#000')


class OrderItem(models.Model):
    """Individual service items in an order - allows multiple services per order."""
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    service = models.ForeignKey(Service, on_delete=models.PROTECT, related_name='order_items')
    
    # Snapshot of service details at order time (for historical accuracy if prices change)
    service_name = models.CharField(max_length=100, help_text="Service name at time of order")
    price_at_order = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        help_text="Price when order was placed"
    )
    
    quantity = models.PositiveIntegerField(default=1)
    subtotal = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        help_text="price_at_order * quantity"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['id']
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'
    
    def __str__(self):
        return f"{self.service_name} x{self.quantity} for {self.order.order_number}"
    
    def save(self, *args, **kwargs):
        """Auto-populate snapshot fields and calculate subtotal."""
        if not self.service_name:
            self.service_name = self.service.name
        if not self.price_at_order:
            self.price_at_order = self.service.price
        
        # Calculate subtotal
        self.subtotal = self.price_at_order * self.quantity
        
        super().save(*args, **kwargs)


class DiscountCode(models.Model):
    """Discount code model for promo codes."""
    
    code = models.CharField(max_length=50, unique=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField(null=True, blank=True)
    usage_limit = models.PositiveIntegerField(null=True, blank=True)
    times_used = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = 'Discount Code'
        verbose_name_plural = 'Discount Codes'
    
    def __str__(self):
        return f"{self.code} - ₦{self.discount_amount}"
    
    def is_valid(self):
        """Check if discount code is valid."""
        if not self.is_active:
            return False
        if timezone.now() < self.valid_from:
            return False
        if self.valid_until and timezone.now() > self.valid_until:
            return False
        if self.usage_limit and self.times_used >= self.usage_limit:
            return False
        return True


class DeliveryCode(models.Model):
    """Delivery verification code model."""
    
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='delivery_code')
    code = models.CharField(max_length=4)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Delivery Code'
        verbose_name_plural = 'Delivery Codes'
    
    def __str__(self):
        return f"Delivery code for {self.order.order_number} - {self.code}"
    
    @staticmethod
    def generate_code():
        """Generate a secure 4-digit delivery code."""
        return ''.join([str(secrets.randbelow(10)) for _ in range(4)])


class Rating(models.Model):
    """Rating model for post-delivery feedback."""
    
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='rating')
    rating = models.PositiveSmallIntegerField()  # 1-5 stars
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Rating'
        verbose_name_plural = 'Ratings'
    
    def __str__(self):
        return f"{self.order.order_number} - {self.rating} stars"
    
    def save(self, *args, **kwargs):
        """Validate rating is between 1-5."""
        if self.rating < 1 or self.rating > 5:
            raise ValueError("Rating must be between 1 and 5")
        super().save(*args, **kwargs)
