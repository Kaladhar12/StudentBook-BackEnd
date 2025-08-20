from django.urls import path
from studentbookfrontend.views.razorpay_views import *


urlpatterns = [
 
    path('payment-create-order', RazorpayOrderAPIView.as_view(), name='create_order'),
    path('verify-payment', TransactionAPIView.as_view(), name='verify_payment'),

]