from django.contrib import admin
from .models import MpesaTransaction

@admin.register(MpesaTransaction)
class MpesaTransactionAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'amount', 'is_completed', 'transaction_date')
    list_filter = ('is_completed', 'transaction_date')
    search_fields = ('phone_number', 'receipt_number')
