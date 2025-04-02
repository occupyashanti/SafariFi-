from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings

class CaptivePortalMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Skip middleware for these paths
        if request.path.startswith('/static/') or \
           request.path.startswith('/media/') or \
           request.path.startswith('/login') or \
           request.path.startswith('/register') or \
           request.path.startswith('/payment-callback'):
            return self.get_response(request)
            
        # Check if user is authenticated
        if not request.user.is_authenticated:
            # Check for captive portal detection requests
            captive_portal_urls = [
                '/generate_204',
                '/hotspot-detect.html',
                '/ncsi.txt',
                '/connecttest.txt',
                '/redirect',
                '/success.txt',
                '/check_network_status.txt',
                '/fwlink/',
                '/generate-204',
                '/gen_204',
                '/mobile/status.php',
                '/library/test/success.html',
                '/kindle-wifi/wifistub.html',
                '/connectivity-check.html'
            ]
            
            # Check if the request is a captive portal detection
            if request.path in captive_portal_urls or request.path.startswith('/generate_204'):
                return redirect(reverse('login'))
                
            return redirect(f"{reverse('login')}?next={request.path}")
            
        return self.get_response(request)