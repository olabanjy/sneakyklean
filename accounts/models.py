from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
import secrets
from datetime import timedelta


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication."""
    
    def create_user(self, email, full_name=None, phone=None, password=None, **extra_fields):
        """Create and return a regular user."""
        if not email:
            raise ValueError('The Email field must be set')
        
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            full_name=full_name or '',
            phone=phone or '',
            **extra_fields
        )
        
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and return a superuser."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password=password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model for passwordless authentication via email OTP."""
    
    email = models.EmailField(unique=True, max_length=255)
    full_name = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    
    # Order tracking
    total_orders = models.IntegerField(default=0)
    free_cleaning_count = models.IntegerField(default=0)  # 0-14 counter, resets at 15
    
    # Permissions
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    
    date_joined = models.DateTimeField(default=timezone.now)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        return self.full_name or self.email
    
    def get_short_name(self):
        return self.full_name.split()[0] if self.full_name else self.email.split('@')[0]


class OTP(models.Model):
    """One-Time Password model for passwordless authentication."""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otps')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'OTP'
        verbose_name_plural = 'OTPs'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"OTP for {self.user.email} - {self.code}"
    
    def save(self, *args, **kwargs):
        """Set expiry time to 5 minutes from creation."""
        if not self.pk:  # Only on creation
            self.expires_at = timezone.now() + timedelta(minutes=5)
        super().save(*args, **kwargs)
    
    def is_valid(self):
        """Check if OTP is still valid (not expired and not used)."""
        return not self.is_used and timezone.now() < self.expires_at
    
    @staticmethod
    def generate_code():
        """Generate a secure 6-digit OTP code."""
        return ''.join([str(secrets.randbelow(10)) for _ in range(6)])
