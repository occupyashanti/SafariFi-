#  SafariFi

> A Django-based captive portal for WiFi hotspots with M-Pesa payment integration.

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-4.x-success.svg)](https://www.djangoproject.com/)
[![M-Pesa Integration](https://img.shields.io/badge/M--Pesa-Daraja--API-orange.svg)](https://developer.safaricom.co.ke/)
[![Made in Kenya](https://img.shields.io/badge/Made%20in-Kenya-black.svg?logo=flag&logoColor=white)](https://github.com/occupyashanti/safarifi)

---

SafariFi lets you monetize WiFi access by redirecting users to a login and payment portal when they connect to your hotspot. Built with Django and integrated with Safaricom’s Daraja API, it provides a simple and secure way to sell internet access using M-Pesa payments.


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