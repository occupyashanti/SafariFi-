from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('dashboard/', views.wifi_dashboard, name='wifi_dashboard'),
    path('purchase/', views.purchase_voucher, name='purchase_voucher'),
    path('payment-callback/', views.payment_callback, name='payment_callback'),
]