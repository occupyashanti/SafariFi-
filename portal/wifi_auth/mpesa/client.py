"""
MPesa client implementation for the WiFi captive portal.
"""
import base64
import json
import requests
from datetime import datetime
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class MpesaClient:
    """
    A client for interacting with the Safaricom M-PESA API.
    """
    
    def __init__(self):
        self.base_url = settings.MPESA_BASE_URL
        self.consumer_key = settings.MPESA_CONSUMER_KEY
        self.consumer_secret = settings.MPESA_CONSUMER_SECRET
        self.business_short_code = settings.MPESA_BUSINESS_SHORT_CODE
        self.passkey = settings.MPESA_PASSKEY
        self.callback_url = settings.MPESA_CALLBACK_URL
        self.merchant_number = settings.MPESA_MERCHANT_NUMBER
        self.access_token = self._get_access_token()
        
    def _get_access_token(self):
        """
        Get OAuth access token from Safaricom.
        """
        url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
        auth = base64.b64encode(f"{self.consumer_key}:{self.consumer_secret}".encode()).decode("utf-8")
        headers = {
            "Authorization": f"Basic {auth}"
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            return result.get("access_token")
        except Exception as e:
            logger.error(f"Error getting access token: {str(e)}")
            raise Exception("Could not connect to M-PESA API. Please try again later.")
    
    def _generate_password(self):
        """
        Generate the M-PESA API password using the provided shortcode and passkey.
        """
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        password_str = f"{self.business_short_code}{self.passkey}{timestamp}"
        password_bytes = base64.b64encode(password_str.encode())
        return {
            "password": password_bytes.decode("utf-8"),
            "timestamp": timestamp
        }
    
    def stk_push(self, phone_number, amount, account_reference, transaction_desc):
        """
        Initiate an STK push request to the customer's phone.
        
        Args:
            phone_number (str): Customer's phone number in format 254XXXXXXXXX
            amount (int/float): Amount to charge
            account_reference (str): Reference ID for the transaction
            transaction_desc (str): Description of the transaction
            
        Returns:
            dict: Response from the M-PESA API
        """
        if not self.access_token:
            logger.error("No access token available for M-PESA API")
            self.access_token = self._get_access_token()  # Try to get a new token
            if not self.access_token:
                raise Exception("Could not authenticate with M-PESA API")
        
        url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        password_data = self._generate_password()
        
        # Make sure amount is at least 1 KES (M-PESA minimum)
        amount = max(1, int(amount))
        
        # For sandbox testing, use these specific values
        if self.base_url == 'https://sandbox.safaricom.co.ke':
            # In sandbox, we must use the standard test values
            payload = {
                "BusinessShortCode": self.business_short_code,  # Must be 174379 for sandbox
                "Password": password_data["password"],
                "Timestamp": password_data["timestamp"],
                "TransactionType": "CustomerPayBillOnline",
                "Amount": amount,
                "PartyA": phone_number,
                "PartyB": self.business_short_code,  # In sandbox, PartyB must be the shortcode
                "PhoneNumber": phone_number,
                "CallBackURL": self.callback_url,
                "AccountReference": account_reference[:12] if len(account_reference) > 12 else account_reference,
                "TransactionDesc": transaction_desc[:13] if len(transaction_desc) > 13 else transaction_desc
            }
        else:
            # Production values
            payload = {
                "BusinessShortCode": self.business_short_code,
                "Password": password_data["password"],
                "Timestamp": password_data["timestamp"],
                "TransactionType": "CustomerPayBillOnline",
                "Amount": amount,
                "PartyA": phone_number,
                "PartyB": self.merchant_number,  # Use the merchant number to be credited
                "PhoneNumber": phone_number,
                "CallBackURL": self.callback_url,
                "AccountReference": account_reference,
                "TransactionDesc": transaction_desc
            }
        
        # Log the request payload for debugging (excluding sensitive data)
        debug_payload = payload.copy()
        debug_payload["Password"] = "[REDACTED]"
        logger.info(f"STK Push Request: {json.dumps(debug_payload)}")
        
        try:
            print(f"Making STK push request to: {url}")
            print(f"Headers: Authorization: Bearer {self.access_token[:10]}...")
            print(f"Payload (partial): BusinessShortCode={payload['BusinessShortCode']}, Amount={payload['Amount']}, PartyA={payload['PartyA']}, PartyB={payload['PartyB']}")
            
            response = requests.post(url, json=payload, headers=headers)
            
            # Print raw response for debugging
            print(f"Raw response status: {response.status_code}")
            print(f"Raw response text: {response.text[:200]}...")
            
            try:
                response_data = response.json()
                
                # Log the response for debugging
                print(f"STK Push Response: {json.dumps(response_data)}")
                logger.info(f"STK Push Response: {json.dumps(response_data)}")
                
                # Check for API errors even if HTTP status is 200
                if 'errorCode' in response_data:
                    error_message = response_data.get('errorMessage', 'Unknown M-PESA API error')
                    print(f"M-PESA API Error: {error_message} (Code: {response_data.get('errorCode')})")
                    logger.error(f"M-PESA API Error: {error_message}")
                    raise Exception(f"M-PESA API Error: {error_message}")
                elif response_data.get('ResponseCode') != '0':
                    error_message = response_data.get('ResponseDescription', 'Unknown M-PESA API error')
                    print(f"M-PESA API Error: {error_message} (Code: {response_data.get('ResponseCode')})")
                    logger.error(f"M-PESA API Error: {error_message}")
                    raise Exception(f"M-PESA API Error: {error_message}")
                
                return response_data
            except json.JSONDecodeError:
                print("Failed to parse JSON response")
                raise Exception("Invalid response from M-PESA API: Not a valid JSON response")
                
        except requests.exceptions.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
            # Try to get more details from the response
            error_message = "Payment request failed"
            try:
                error_data = response.json()
                error_message = error_data.get("errorMessage", error_message)
            except:
                pass
            raise Exception(error_message)
        except Exception as e:
            logger.error(f"Error initiating STK push: {str(e)}")
            raise Exception("Could not process payment request. Please try again later.")
    
    def check_payment_status(self, checkout_request_id):
        """
        Check the status of a payment.
        
        Args:
            checkout_request_id (str): The checkout request ID returned by the STK push
            
        Returns:
            dict: Response from the M-PESA API
        """
        if not self.access_token:
            raise Exception("Could not authenticate with M-PESA API")
        
        url = f"{self.base_url}/mpesa/stkpushquery/v1/query"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        password_data = self._generate_password()
        
        payload = {
            "BusinessShortCode": self.business_short_code,
            "Password": password_data["password"],
            "Timestamp": password_data["timestamp"],
            "CheckoutRequestID": checkout_request_id
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error checking payment status: {str(e)}")
            raise Exception("Could not check payment status. Please try again later.")
