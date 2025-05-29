# SafariFi

A Django-based captive portal for WiFi hotspots with M-Pesa integration for payment processing.

## Updates Made

1. **Security Enhancements**:
   - Added environment variable support for Django secret key
   - Made DEBUG mode configurable via environment variables
   - Added proper ALLOWED_HOSTS configuration

2. **Captive Portal Improvements**:
   - Enhanced detection for various device types (iOS, Android, Windows, etc.)
   - Added support for more captive portal detection URLs

3. **M-Pesa Integration**:
   - Implemented robust M-Pesa client with proper error handling
   - Added payment status checking functionality
   - Improved environment variable configuration

4. **Code Fixes**:
   - Added missing imports (`os` in settings.py, `include` in urls.py)
   - Created proper M-Pesa client implementation

## Setup Instructions

1. **Environment Setup**:
   ```bash
   # Create and activate virtual environment
   python -m venv venv
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Environment Variables**:
   - Copy the `mpesa.env.example` file to `.env`
   - Update the values with your actual credentials
   ```bash
   cp mpesa.env .env
   ```

3. **Database Setup**:
   ```bash
   cd portal
   python manage.py migrate
   python manage.py createsuperuser
   ```

4. **Running the Server**:
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```

5. **For Production Deployment**:
   - Set `DEBUG=False` in your environment variables
   - Update `ALLOWED_HOSTS` with your domain
   - Use a proper web server like Nginx with Gunicorn
   - Set up proper SSL certificates for secure connections

## Testing the Captive Portal

1. Connect to your WiFi network
2. Try to access any website - you should be redirected to the login page
3. Register or login to access the internet
4. Purchase a voucher using M-Pesa to extend your access

## M-Pesa Integration

For the M-Pesa integration to work properly:
1. Register for Safaricom Daraja API access
2. Configure the callback URL to point to your server
3. For local testing, use a tool like ngrok to expose your local server
