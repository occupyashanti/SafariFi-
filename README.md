# SafariFi

**SafariFi** is a Django-based captive portal system designed for WiFi hotspot providers. It integrates seamlessly with **M-Pesa** (via Safaricom's Daraja API) to allow users to purchase internet access through mobile payments.

---

##  Features

-  **Secure Django backend** with configurable environment settings
-  **Captive portal redirection** for Android, iOS, Windows, and Linux
-  **M-Pesa integration** for real-time voucher purchase and validation
-  **Device-aware** login flows
-  Admin dashboard to manage users, vouchers, and payment logs

---

##  Updates Made

###  Security Enhancements
- Environment-based `SECRET_KEY` and `DEBUG` settings
- Proper `ALLOWED_HOSTS` configuration
- Sample `.env` file for safer secret management

###  Captive Portal Improvements
- Improved OS/device detection
- Wider support for captive portal triggers (e.g., `http://captive.apple.com`, `connectivitycheck.gstatic.com`)

###  M-Pesa Integration
- Fully functional M-Pesa client with:
  - STK push
  - Callback validation
  - Transaction status checks
- Environment-variable-driven configuration

###  Code Fixes
- Added missing `os` import in `settings.py`
- Fixed missing `include()` in `urls.py`
- Modularized and cleaned up M-Pesa client logic

---

##  Getting Started

### 1. Environment Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt