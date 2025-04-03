from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .client import MpesaClient, MpesaError
import logging

logger = logging.getLogger(__name__)

@require_http_methods(["GET", "POST"])
def initiate_stk(request):
    if request.method == 'POST':
        try:
            phone = request.POST.get('phone')
            amount = request.POST.get('amount')
            
            if not phone or not amount:
                return JsonResponse({
                    'success': False,
                    'error': 'Phone number and amount are required'
                }, status=400)
            
            client = MpesaClient()
            response = client.stk_push(
                phone_number=phone,
                amount=amount,
                account_reference="PAYMENT",
                transaction_desc="Payment"
            )
            
            return JsonResponse({
                'success': True,
                'data': response
            })
            
        except MpesaError as e:
            logger.error(f"M-Pesa error: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
            
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'An unexpected error occurred'
            }, status=500)
            
    return render(request, 'payment.html')
