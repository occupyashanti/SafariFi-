from django.contrib import admin
from .models import Voucher, PaymentTransaction, User
from django.contrib.auth.admin import UserAdmin

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'phone_number', 'is_premium', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('phone_number', 'is_premium')}),
    )

@admin.register(Voucher)
class VoucherAdmin(admin.ModelAdmin):
    list_display = ('code', 'duration_hours', 'price', 'is_used', 'created_by', 'created_at')
    list_filter = ('is_used', 'created_at')
    search_fields = ('code', 'created_by__username')
    readonly_fields = ('created_at', 'used_at')

@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ('mpesa_receipt', 'user', 'amount', 'phone_number', 'is_completed', 'transaction_date')
    list_filter = ('is_completed', 'transaction_date')
    search_fields = ('mpesa_receipt', 'user__username', 'phone_number')
    readonly_fields = ('transaction_date',)