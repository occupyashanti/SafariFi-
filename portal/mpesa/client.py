import requests
import base64
from datetime import datetime, timedelta
import json
from django.conf import settings
import logging
import re

logger = logging.getLogger(__name__)

class MpesaError(Exception):
    """Custom exception for M-Pesa related errors"""
    pass

class MpesaClient:
    def __init__(self):
        self.consumer_key = settings.MPESA_CONSUMER_KEY
        self.consumer_secret = settings.MPESA_CONSUMER_SECRET
        self.base_url = settings.MPESA_BASE_URL
        self.passkey = settings.MPESA_PASSKEY
        self.business_short_code = settings.MPESA_BUSINESS_SHORT_CODE
        self.callback_url = settings.MPESA_CALLBACK_URL
        self.access_token = None
        self.token_expiry = None
        
        # Log configuration (without sensitive data)
        logger.info(f"Initialized M-Pesa client with base URL: {self.base_url}")
        logger.info(f"Business Short Code: {self.business_short_code}")
        logger.info(f"Callback URL: {self.callback_url}")

    def validate_phone_number(self, phone_number):
        """Validate Kenyan phone number format"""
        # Remove any spaces or special characters
        phone = re.sub(r'\D', '', phone_number)
        # Check if it's a valid Kenyan number (10 digits starting with 254)
        if not re.match(r'^254\d{9}$', phone):
            raise MpesaError("Invalid phone number format. Use format: 254XXXXXXXXX")
        return phone

    def validate_amount(self, amount):
        """Validate amount is a positive integer"""
        try:
            amount = int(float(amount))  # Convert string or float to int
            if amount <= 0:
                raise MpesaError("Amount must be greater than 0")
            return amount
        except ValueError:
            raise MpesaError("Amount must be a valid number")

    def get_access_token(self):
        """Get OAuth access token from M-Pesa"""
        if self.access_token and self.token_expiry and self.token_expiry > datetime.now():
            return self.access_token

        url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
        auth_string = f"{self.consumer_key}:{self.consumer_secret}"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()

        try:
            logger.info("Requesting access token from M-Pesa API")
            session = requests.Session()
            session.verify = False  # Skip SSL verification for testing
            
            response = session.get(
                url,
                headers={
                    "Authorization": f"Basic {encoded_auth}",
                    "Content-Type": "application/json"
                }
            )
            response.raise_for_status()
            data = response.json()
            self.access_token = data['access_token']
            # Set expiry to 55 minutes from now to be safe
            self.token_expiry = datetime.now() + timedelta(minutes=55)
            logger.info("Successfully obtained access token")
            return self.access_token
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error getting access token: {e}")
            raise MpesaError("Failed to connect to M-Pesa API")
        except Exception as e:
            logger.error(f"Error getting access token: {e}")
            raise MpesaError("Failed to authenticate with M-Pesa API")

    def stk_push(self, phone_number, amount, account_reference, transaction_desc):
        """Initiate STK push payment"""
        try:
            # Validate inputs
            phone = self.validate_phone_number(phone_number)
            amount = self.validate_amount(amount)
            
            logger.info(f"Initiating STK push for phone: {phone}, amount: {amount}")
            
            access_token = self.get_access_token()
            url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
            
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            password = base64.b64encode(
                f"{self.business_short_code}{self.passkey}{timestamp}".encode()
            ).decode()

            payload = {
                "BusinessShortCode": self.business_short_code,
                "Password": password,
                "Timestamp": timestamp,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": amount,
                "PartyA": phone,
                "PartyB": self.business_short_code,
                "PhoneNumber": phone,
                "CallBackURL": self.callback_url,
                "AccountReference": account_reference,
                "TransactionDesc": transaction_desc
            }

            logger.info(f"Sending STK push request with payload: {json.dumps(payload)}")
            
            session = requests.Session()
            session.verify = False  # Skip SSL verification for testing
            
            response = session.post(
                url,
                json=payload,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                }
            )
            
            # Log the raw response for debugging
            logger.info(f"Raw response status: {response.status_code}")
            logger.info(f"Raw response headers: {dict(response.headers)}")
            logger.info(f"Raw response body: {response.text}")
            
            response.raise_for_status()
            result = response.json()
            
            # Validate response structure
            if not isinstance(result, dict):
                raise MpesaError("Invalid response format from M-Pesa API")
            
            if result.get('ResponseCode') == '0':
                # Validate required fields
                if 'CheckoutRequestID' not in result:
                    raise MpesaError("Missing CheckoutRequestID in successful response")
                    
                logger.info(f"STK push initiated successfully. CheckoutRequestID: {result['CheckoutRequestID']}")
                return result
            else:
                error_code = result.get('ResponseCode', 'Unknown')
                error_message = result.get('ResponseDescription', 'Unknown error')
                logger.error(f"STK push failed: Code={error_code}, Message={error_message}")
                raise MpesaError(f"Payment failed: {error_message} (Code: {error_code})")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error in STK push: {e}")
            raise MpesaError("Failed to connect to M-Pesa API. Please check your internet connection.")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response: {e}")
            raise MpesaError("Invalid response from M-Pesa API")
        except Exception as e:
            logger.error(f"Unexpected error in STK push: {e}")
            raise MpesaError("Failed to initiate payment. Please try again.") 