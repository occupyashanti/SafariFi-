import requests
import base64
from django.conf import settings
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portal.settings')
django.setup()

def test_mpesa_credentials():
    """Test M-Pesa API credentials by attempting to get an access token"""
    print("\nTesting M-Pesa API Credentials...")
    print("-" * 50)
    
    # Get credentials from settings
    consumer_key = settings.MPESA_CONSUMER_KEY
    consumer_secret = settings.MPESA_CONSUMER_SECRET
    base_url = settings.MPESA_BASE_URL
    
    print(f"Base URL: {base_url}")
    print(f"Consumer Key: {consumer_key}")
    print(f"Consumer Secret: {consumer_secret[:8]}...")  # Only show first 8 chars for security
    
    # Prepare the request
    url = f"{base_url}/oauth/v1/generate?grant_type=client_credentials"
    auth_string = f"{consumer_key}:{consumer_secret}"
    encoded_auth = base64.b64encode(auth_string.encode()).decode()
    
    headers = {
        "Authorization": f"Basic {encoded_auth}"
    }
    
    try:
        print("\nMaking request to M-Pesa API...")
        response = requests.get(url, headers=headers)
        
        print(f"\nResponse Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print("\nSuccess! Access token obtained:")
            print(f"Access Token: {data.get('access_token', '')[:20]}...")  # Only show first 20 chars
            print(f"Expires In: {data.get('expires_in', 'N/A')} seconds")
            return True
        else:
            print("\nError! Failed to get access token")
            print(f"Response Body: {response.text}")
            return False
            
    except Exception as e:
        print(f"\nException occurred: {str(e)}")
        return False

if __name__ == "__main__":
    test_mpesa_credentials() 