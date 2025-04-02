import requests
import base64
from datetime import datetime
import json
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

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

    def get_access_token(self):
        if self.access_token and self.token_expiry and self.token_expiry > datetime.now():
            return self.access_token

        url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
        auth_string = f"{self.consumer_key}:{self.consumer_secret}"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()

        headers = {
            "Authorization": f"Basic {encoded_auth}"
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            self.access_token = data['access_token']
            # Set expiry to 55 minutes from now to be safe
            self.token_expiry = datetime.now() + timedelta(minutes=55)
            return self.access_token
        except Exception as e:
            logger.error(f"Error getting access token: {e}")
            raise

    def stk_push(self, phone_number, amount, account_reference, transaction_desc):
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
            "PartyA": phone_number,
            "PartyB": self.business_short_code,
            "PhoneNumber": phone_number,
            "CallBackURL": self.callback_url,
            "AccountReference": account_reference,
            "TransactionDesc": transaction_desc
        }

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error in STK push: {e}")
            raise