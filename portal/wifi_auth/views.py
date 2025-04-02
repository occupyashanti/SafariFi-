from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Voucher, PaymentTransaction, User
from .mpesa.client import MpesaClient
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django import forms
import random
import string
import json
from datetime import timedelta
from django.utils import timezone

def generate_voucher_code(length=8):
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def login_view(request):
    if request.user.is_authenticated:
        return redirect('wifi_dashboard')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'wifi_dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password')
            return render(request, 'wifi_auth/login.html', {'error': True})
    
    return render(request, 'wifi_auth/login.html')

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully')
    return redirect('login')


class RegistrationForm(UserCreationForm):
    phone_number = forms.CharField(max_length=15, required=True, help_text='Required. Format: 254XXXXXXXXX')
    email = forms.EmailField(max_length=254, required=False, help_text='Optional.')
    
    class Meta:
        model = User
        fields = ('username', 'email', 'phone_number', 'password1', 'password2')
    
    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        
        # Basic validation for Kenyan phone numbers
        if not phone_number.startswith('254') or len(phone_number) != 12 or not phone_number.isdigit():
            raise forms.ValidationError('Enter a valid phone number in the format 254XXXXXXXXX')
            
        # Check if phone number is already in use
        if User.objects.filter(phone_number=phone_number).exists():
            raise forms.ValidationError('This phone number is already registered')
            
        return phone_number


def register_view(request):
    if request.user.is_authenticated:
        return redirect('wifi_dashboard')
        
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            
            # Log the user in after registration
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            
            messages.success(request, f'Welcome {username}! Your account has been created successfully.')
            return redirect('wifi_dashboard')
    else:
        form = RegistrationForm()
    
    return render(request, 'wifi_auth/register.html', {'form': form})

@login_required
def wifi_dashboard(request):
    active_vouchers = Voucher.objects.filter(
        used_by=request.user,
        is_used=True,
        used_at__gte=timezone.now() - timedelta(hours=24)  # Show vouchers used in last 24 hours
    )
    
    # Check if user has active premium status
    if request.user.is_premium:
        messages.info(request, 'You have unlimited premium access')
    
    return render(request, 'wifi_auth/dashboard.html', {
        'vouchers': active_vouchers,
        'user': request.user
    })

@login_required
def purchase_voucher(request):
    PRICING = {
        '0.5': 5,    # 30 minutes - 5sh
        '1': 9,      # 1 hour - 9sh
        '2': 15,     # 2 hours - 15sh
        '5': 35,     # 5 hours - 35sh
        '12': 65,    # 12 hours - 65sh
        '24': 100,   # 24 hours - 100sh
        '72': 250,   # 3 days - 250sh
        '168': 500   # 1 week - 500sh
    }
    
    if request.method == 'POST':
        duration = request.POST.get('duration')
        phone_number = request.POST.get('phone_number').strip()
        
        # Validate phone number (basic Safaricom validation)
        # Clean the phone number - remove spaces, dashes, etc.
        phone_number = ''.join(filter(str.isdigit, phone_number))
        
        # Convert to international format if needed
        if phone_number.startswith('0'):
            phone_number = '254' + phone_number[1:]
        elif phone_number.startswith('+'):
            phone_number = phone_number[1:]
        
        # Validate the phone number
        if not phone_number.startswith('254') or len(phone_number) != 12:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error', 
                    'message': 'Invalid phone number. Use format 254XXXXXXXXX or 07XXXXXXXX'
                }, status=400)
            messages.error(request, 'Invalid phone number format. Use format 254XXXXXXXXX or 07XXXXXXXX')
            return redirect('purchase_voucher')
        
        # Get price based on duration
        try:
            price = PRICING[duration]
        except KeyError:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error', 
                    'message': 'Invalid duration selected'
                }, status=400)
            messages.error(request, 'Invalid duration selected')
            return redirect('purchase_voucher')
        
        # Generate voucher (but don't mark as used yet)
        voucher = Voucher.objects.create(
            code=generate_voucher_code(),
            duration_hours=duration,
            price=price,
            created_by=request.user
        )
        
        # Initiate STK push
        mpesa = MpesaClient()
        try:
            # Log the payment attempt
            print(f"Initiating STK push: Phone={phone_number}, Amount={price}, Duration={duration}hrs")
            
            response = mpesa.stk_push(
                phone_number=phone_number,
                amount=price,
                account_reference=f"WIFI-{voucher.code}",
                transaction_desc=f"WIFI voucher {duration}hrs"
            )
            
            # Check if STK push was successful
            if response.get('ResponseCode') == '0':
                # Get the CheckoutRequestID for tracking
                checkout_request_id = response.get('CheckoutRequestID')
                print(f"STK push successful: CheckoutRequestID={checkout_request_id}")
                
                # Create pending payment transaction
                transaction = PaymentTransaction.objects.create(
                    user=request.user,
                    voucher=voucher,
                    amount=price,
                    phone_number=phone_number,
                    mpesa_receipt=checkout_request_id
                )
                
                # Store additional response data for debugging
                transaction.response_data = json.dumps(response)
                transaction.save()
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'success', 
                        'message': 'Payment initiated. Check your phone to complete payment.',
                        'checkout_request_id': checkout_request_id
                    })
                
                messages.success(request, 'Payment initiated. Check your phone to complete the M-Pesa payment.')
                return redirect('wifi_dashboard')
            else:
                # Get detailed error information
                error_code = response.get('errorCode', 'Unknown')
                error_message = response.get('errorMessage', 'Payment request failed')
                print(f"STK push failed: ErrorCode={error_code}, ErrorMessage={error_message}")
                raise Exception(f"Payment failed: {error_message} (Code: {error_code})")
                
        except Exception as e:
            # Log the exception
            print(f"Exception during STK push: {str(e)}")
            
            # Delete the voucher if payment failed
            voucher.delete()
            
            # Provide a more user-friendly error message
            user_message = str(e)
            if "authenticate" in user_message.lower():
                user_message = "Could not connect to M-Pesa. Please try again later."
            elif "timeout" in user_message.lower():
                user_message = "Connection to M-Pesa timed out. Please try again."
            elif "json" in user_message.lower():
                user_message = "Invalid response from payment server. Please try again."
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # Ensure we always return a valid JSON response
                response = JsonResponse({
                    'status': 'error', 
                    'message': user_message,
                    'technical_details': str(e) if settings.DEBUG else ''
                }, status=400)
                response['Content-Type'] = 'application/json'
                return response
            
            messages.error(request, f'Payment failed: {user_message}')
            return redirect('purchase_voucher')
    
    # GET request - show purchase form
    return render(request, 'wifi_auth/purchase_voucher.html', {
        'pricing': PRICING
    })

def payment_callback(request):
    if request.method == 'POST':
        try:
            callback_data = json.loads(request.body)
            
            # Safaricom callback structure may vary - adjust accordingly
            result_code = callback_data.get('Body', {}).get('stkCallback', {}).get('ResultCode')
            checkout_request_id = callback_data.get('Body', {}).get('stkCallback', {}).get('CheckoutRequestID')
            mpesa_receipt = callback_data.get('Body', {}).get('stkCallback', {}).get('CallbackMetadata', {}).get('Item', [{}])[0].get('Value')
            
            if result_code == '0' and checkout_request_id:
                # Payment was successful
                transaction = PaymentTransaction.objects.get(
                    mpesa_receipt=checkout_request_id
                )
                
                # Update transaction status
                transaction.is_completed = True
                transaction.mpesa_receipt = mpesa_receipt
                transaction.save()
                
                # Mark voucher as used
                voucher = transaction.voucher
                voucher.is_used = True
                voucher.used_by = transaction.user
                voucher.used_at = timezone.now()
                voucher.save()
                
                # Here you could also trigger WiFi access activation
                
                return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Success'})
            
            return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Failed'})
            
        except Exception as e:
            print(f"Callback processing error: {str(e)}")
            return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Error'})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)