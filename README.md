

# 🦁 SafariFi

**SafariFi** is a Django-based captive portal system designed for WiFi hotspot providers. It integrates seamlessly with **M-Pesa** (via Safaricom's Daraja API) to allow users to purchase internet access through mobile payments.

---

## ✨ Features

- 🔐 **Secure Django backend** with configurable environment settings
- 🌐 **Captive portal redirection** for Android, iOS, Windows, and Linux
- 💳 **M-Pesa integration** for real-time voucher purchase and validation
- 📱 **Device-aware** login flows
- 📊 Admin dashboard to manage users, vouchers, and payment logs

---

## 🔧 Updates Made

### 🔐 Security Enhancements
- Environment-based `SECRET_KEY` and `DEBUG` settings
- Proper `ALLOWED_HOSTS` configuration
- Sample `.env` file for safer secret management

### 🌍 Captive Portal Improvements
- Improved OS/device detection
- Wider support for captive portal triggers (e.g., `http://captive.apple.com`, `connectivitycheck.gstatic.com`)

### 💰 M-Pesa Integration
- Fully functional M-Pesa client with:
  - STK push
  - Callback validation
  - Transaction status checks
- Environment-variable-driven configuration

### 🧹 Code Fixes
- Added missing `os` import in `settings.py`
- Fixed missing `include()` in `urls.py`
- Modularized and cleaned up M-Pesa client logic

---

## 🚀 Getting Started

### 1. Environment Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt


---

2. Configure Environment Variables

# Copy the example env file
cp mpesa.env.example .env

> Fill in .env with your M-Pesa credentials, Django settings, and callback URLs.




---

3. Database Setup

cd portal
python manage.py migrate
python manage.py createsuperuser


---

4. Run the Server (Dev Mode)

python manage.py runserver 0.0.0.0:8000


---

5. Production Deployment Checklist

DEBUG=False in .env

Add your domain/IP in ALLOWED_HOSTS

Use Gunicorn + Nginx

Use Let's Encrypt or commercial SSL for HTTPS

Enable firewall rules to block traffic bypassing the portal



---

🧪 Testing the Captive Portal

1. Connect to your SafariFi WiFi hotspot


2. Open any web browser and visit a site (e.g., example.com)


3. You should be redirected to the SafariFi login page


4. Login or register


5. Purchase access using M-Pesa


6. Enjoy internet access!




---

🔌 M-Pesa Integration

1. Register at the Safaricom Daraja Portal


2. Set up:

Consumer Key and Secret

Shortcode and Passkey

Callback URLs (/api/payment/callback/)



3. For local testing, use ngrok:



ngrok http 8000

4. Update .env with your ngrok HTTPS tunnel URL for callbacks




---

📁 Project Structure

SafariFi/
├── portal/              # Django app for captive portal
├── mpesa/               # M-Pesa API integration
├── templates/           # HTML templates for login, payment, etc.
├── static/              # CSS/JS files
├── manage.py
└── .env                 # Environment variables


---

🛡️ License

SafariFi is released under the MIT License. See LICENSE for details.


---

🤝 Contributing

Contributions, feature suggestions, and pull requests are welcome!

Fork the repo

Create a feature branch

Submit a pull request with clear description



---

📬 Contact

For questions, support, or collaboration:

Email: support@safarifi.local

GitHub Issues: Open an issue



---

SafariFi – Powering WiFi payments with M-Pesa.

---

