from django.db import models
from django.conf import settings

class MpesaTransaction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    phone_number = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    receipt_number = models.CharField(max_length=50, blank=True)
    transaction_date = models.DateTimeField(auto_now_add=True)
    is_completed = models.BooleanField(default=False)
    merchant_request_id = models.CharField(max_length=100)
    checkout_request_id = models.CharField(max_length=100)
    result_code = models.IntegerField(null=True)
    result_description = models.TextField(blank=True)
