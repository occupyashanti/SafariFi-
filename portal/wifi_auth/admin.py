from django.contrib import admin
from .models import Voucher, PaymentTransaction, User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'phone_number', 'is_premium')
    search_fields = ('username', 'email', 'phone_number')
    list_filter = ('is_premium', 'is_staff', 'is_active')

@admin.register(Voucher)
class VoucherAdmin(admin.ModelAdmin):
    list_display = ('code', 'duration_hours', 'price', 'is_used', 'created_by', 'created_at')
    search_fields = ('code', 'created_by__username')
    list_filter = ('is_used', 'created_at')
    readonly_fields = ('code', 'created_at')

@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'phone_number', 'is_completed', 'created_at')
    search_fields = ('user__username', 'phone_number', 'mpesa_receipt')
    list_filter = ('is_completed', 'created_at')
    readonly_fields = ('response_data', 'created_at', 'updated_at')