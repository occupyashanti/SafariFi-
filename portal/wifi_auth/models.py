from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class User(AbstractUser):
    phone_number = models.CharField(max_length=15, unique=True)
    is_premium = models.BooleanField(default=False)
    
    # Add related_name attributes to avoid clashes with Django's User model
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='wifi_user_set',
        related_query_name='user'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='wifi_user_set',
        related_query_name='user'
    )
    
    def __str__(self):
        return self.username

class Voucher(models.Model):
    code = models.CharField(max_length=20, unique=True)
    duration_hours = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_used = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    used_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='used_vouchers')
    used_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.code} ({'used' if self.is_used else 'available'})"

class PaymentTransaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    voucher = models.ForeignKey(Voucher, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    mpesa_receipt = models.CharField(max_length=50, null=True, blank=True)
    phone_number = models.CharField(max_length=15)
    transaction_date = models.DateTimeField(auto_now_add=True)
    is_completed = models.BooleanField(default=False)
    response_data = models.TextField(null=True, blank=True, help_text='Raw response data from M-Pesa API')

    def __str__(self):
        return f"Payment {self.mpesa_receipt or 'pending'}"