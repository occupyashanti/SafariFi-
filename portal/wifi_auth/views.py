from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Voucher, PaymentTransaction, User
from mpesa.client import MpesaClient
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django import forms
import random
import string
import json
from datetime import timedelta
from django.utils import timezone
import logging
from mpesa.exceptions import MpesaError
from django.views.decorators.http import require_http_methods

logger = logging.getLogger(__name__)

def root_view(request):
    """Root view that redirects to appropriate page based on auth status"""
    if request.user.is_authenticated:
        return redirect('wifi_dashboard')
    return redirect('login')

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
    
    # Only show premium message if user has active premium status and no messages exist
    if request.user.is_premium and not messages.get_messages(request):
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
        phone_number = request.POST.get('phone_number', '').strip()
        
        # Validate duration and get price
        try:
            price = PRICING[duration]
        except KeyError:
            messages.error(request, 'Invalid duration selected')
            return redirect('purchase_voucher')
        
        # Clean and validate phone number
        phone_number = ''.join(filter(str.isdigit, phone_number))
        if phone_number.startswith('0'):
            phone_number = '254' + phone_number[1:]
        elif phone_number.startswith('+'):
            phone_number = phone_number[1:]
        
        if not phone_number.startswith('254') or len(phone_number) != 12:
            messages.error(request, 'Please enter a valid Safaricom phone number')
            return redirect('purchase_voucher')
        
        # Generate voucher (but don't mark as used yet)
        voucher = Voucher.objects.create(
            code=generate_voucher_code(),
            duration_hours=float(duration),  # Convert to float for decimal hours
            price=price,
            created_by=request.user
        )
        
        # Initiate STK push
        mpesa = MpesaClient()
        try:
            # Log the payment attempt
            logger.info(f"Initiating STK push: Phone={phone_number}, Amount={price}, Duration={duration}hrs")
            
            response = mpesa.stk_push(
                phone_number=phone_number,
                amount=price,
                account_reference=f"WIFI-{voucher.code}",
                transaction_desc=f"WIFI voucher {duration}hrs"
            )
            
            # Validate response
            if not response or 'CheckoutRequestID' not in response:
                raise MpesaError("Invalid response from M-Pesa API")
            
            # Create pending payment transaction
            transaction = PaymentTransaction.objects.create(
                user=request.user,
                voucher=voucher,
                amount=price,
                phone_number=phone_number,
                mpesa_receipt=response.get('CheckoutRequestID')
            )
            
            # Store additional response data for debugging
            transaction.response_data = json.dumps(response)
            transaction.save()
            
            success_message = 'Payment initiated. Check your phone to complete the M-Pesa payment.'
            logger.info(f"STK push initiated successfully: {response.get('CheckoutRequestID')}")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success', 
                    'message': success_message,
                    'checkout_request_id': response.get('CheckoutRequestID')
                })
            
            messages.success(request, success_message)
            return redirect('wifi_dashboard')
        
        except MpesaError as e:
            # Delete the voucher if payment failed
            voucher.delete()
            
            error_message = str(e)
            logger.error(f"M-Pesa error: {error_message}")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error', 
                    'message': error_message
                }, status=400)
            
            messages.error(request, f'Payment failed: {error_message}')
            return redirect('purchase_voucher')
        
        except Exception as e:
            # Delete the voucher if payment failed
            voucher.delete()
            
            error_message = f"Unexpected error during payment: {str(e)}"
            logger.error(error_message)
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': 'An unexpected error occurred. Please try again.'
                }, status=500)
            
            messages.error(request, 'An unexpected error occurred. Please try again.')
            return redirect('purchase_voucher')
    
    # GET request - show purchase form
    return render(request, 'wifi_auth/purchase_voucher.html', {
        'pricing': PRICING
    })

@require_http_methods(["POST"])
def payment_callback(request):
    """Handle M-Pesa payment callbacks"""
    try:
        # Parse the callback data
        callback_data = json.loads(request.body)
        logger.info(f"Received M-Pesa callback: {json.dumps(callback_data)}")
        
        # Extract relevant data from callback
        result = callback_data.get('Body', {}).get('stkCallback', {})
        result_code = result.get('ResultCode')
        checkout_request_id = result.get('CheckoutRequestID')
        
        if not checkout_request_id:
            logger.error("Missing CheckoutRequestID in callback")
            return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Invalid callback data'})
        
        try:
            # Find the transaction
            transaction = PaymentTransaction.objects.get(mpesa_receipt=checkout_request_id)
        except PaymentTransaction.DoesNotExist:
            logger.error(f"Transaction not found for CheckoutRequestID: {checkout_request_id}")
            return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Transaction not found'})
        
        # Update transaction with callback data
        transaction.response_data = json.dumps(callback_data)
        
        if result_code == 0:  # Success
            # Extract payment details
            items = result.get('CallbackMetadata', {}).get('Item', [])
            mpesa_receipt = next((item.get('Value') for item in items if item.get('Name') == 'MpesaReceiptNumber'), None)
            
            # Update transaction
            transaction.is_completed = True
            if mpesa_receipt:
                transaction.mpesa_receipt = mpesa_receipt
            transaction.save()
            
            # Activate the voucher
            voucher = transaction.voucher
            if voucher:
                voucher.is_used = True
                voucher.used_by = transaction.user
                voucher.used_at = timezone.now()
                voucher.save()
                
                logger.info(f"Payment successful: Receipt={mpesa_receipt}, Voucher={voucher.code}")
                
                # Send success message to user (you could implement this)
                # notify_user(transaction.user, "Payment successful! Your voucher is now active.")
                
                return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Success'})
        
        else:  # Payment failed
            error_message = result.get('ResultDesc', 'Payment failed')
            logger.error(f"Payment failed: {error_message}")
            
            # Delete the voucher since payment failed
            if transaction.voucher:
                transaction.voucher.delete()
            
            # Update transaction status
            transaction.is_completed = False
            transaction.save()
            
            # Send failure message to user (you could implement this)
            # notify_user(transaction.user, f"Payment failed: {error_message}")
            
            return JsonResponse({'ResultCode': 1, 'ResultDesc': error_message})
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON in callback")
        return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Invalid JSON'}, status=400)
        
    except Exception as e:
        logger.error(f"Error processing callback: {str(e)}")
        return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Server Error'}, status=500)