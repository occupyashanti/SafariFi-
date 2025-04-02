from django.shortcuts import render
from django.http import JsonResponse
from .client import MpesaClient

def initiate_stk(request):
    if request.method == 'POST':
        phone = request.POST.get('phone')
        amount = request.POST.get('amount')
        
        client = MpesaClient()
        try:
            response = client.stk_push(
                phone_number=phone,
                amount=amount,
                account_reference="PAYMENT",
                transaction_desc="Payment"
            )
            return JsonResponse(response)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return render(request, 'payment.html')
