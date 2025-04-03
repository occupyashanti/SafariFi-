import requests
import base64
from datetime import datetime
from django.conf import settings
import os
import django
import json
import socket

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portal.settings')
django.setup()

def test_stk_push():
    """Test STK push with a test phone number"""
    print("\nTesting M-Pesa STK Push...")
    print("-" * 50)
    
    # Get credentials from settings
    consumer_key = settings.MPESA_CONSUMER_KEY
    consumer_secret = settings.MPESA_CONSUMER_SECRET
    business_short_code = settings.MPESA_BUSINESS_SHORT_CODE
    passkey = settings.MPESA_PASSKEY
    
    # Use sandbox URL
    base_url = "https://sandbox.safaricom.co.ke"
    callback_url = "https://webhook.site/your-unique-url"  # Replace with your webhook.site URL
    
    print(f"Base URL: {base_url}")
    print(f"Business Short Code: {business_short_code}")
    print(f"Callback URL: {callback_url}")
    
    # Test phone number - using standard test number
    phone_number = "254708374149"  # Standard Safaricom test number
    amount = 1  # 1 KES for testing
    
    try:
        # Step 1: Get access token
        print("\n1. Getting access token...")
        auth_url = f"{base_url}/oauth/v1/generate?grant_type=client_credentials"
        auth_string = f"{consumer_key}:{consumer_secret}"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()
        
        print(f"Making request to: {auth_url}")
        print(f"Using credentials - Key: {consumer_key}")
        
        session = requests.Session()
        session.verify = False  # Skip SSL verification for testing
        
        auth_response = session.get(
            auth_url,
            headers={
                "Authorization": f"Basic {encoded_auth}",
                "Content-Type": "application/json"
            }
        )
        
        print(f"Auth Response Status: {auth_response.status_code}")
        print(f"Auth Response Headers: {dict(auth_response.headers)}")
        
        auth_response.raise_for_status()
        access_token = auth_response.json()['access_token']
        print("✓ Access token obtained successfully")
        
        # Step 2: Prepare STK push
        print("\n2. Preparing STK push...")
        stk_url = f"{base_url}/mpesa/stkpush/v1/processrequest"
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        password = base64.b64encode(
            f"{business_short_code}{passkey}{timestamp}".encode()
        ).decode()
        
        payload = {
            "BusinessShortCode": business_short_code,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone_number,
            "PartyB": business_short_code,
            "PhoneNumber": phone_number,
            "CallBackURL": callback_url,
            "AccountReference": "TEST",
            "TransactionDesc": "Test Payment"
        }
        
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        # Step 3: Send STK push request
        print("\n3. Sending STK push request...")
        print(f"Making request to: {stk_url}")
        stk_response = session.post(
            stk_url,
            json=payload,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
        )
        
        print(f"STK Response Status: {stk_response.status_code}")
        print(f"STK Response Headers: {dict(stk_response.headers)}")
        
        stk_response.raise_for_status()
        result = stk_response.json()
        
        print(f"\nResponse: {json.dumps(result, indent=2)}")
        
        if result.get('ResponseCode') == '0':
            print("\n✓ STK push initiated successfully!")
            print(f"CheckoutRequestID: {result.get('CheckoutRequestID')}")
            return True
        else:
            print("\n✗ STK push failed!")
            print(f"Error Code: {result.get('ResponseCode')}")
            print(f"Error Message: {result.get('ResponseDescription')}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"\n✗ Network error occurred: {str(e)}")
        if hasattr(e.response, 'text'):
            print(f"Error response: {e.response.text}")
        return False
    except Exception as e:
        print(f"\n✗ Exception occurred: {str(e)}")
        return False

if __name__ == "__main__":
    # Disable SSL warnings for testing
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    test_stk_push() 