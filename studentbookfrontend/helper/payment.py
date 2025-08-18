import razorpay
from rest_framework import status
from rest_framework.exceptions import ValidationError

from studentbookbackend import settings

client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

class RazorpayClient:
    def create_order(self, amount, currency):
        data = {
            "amount": amount * 100,  # Convert to paisa
            "currency": currency,
        }
        try:
            order = client.order.create(data=data)
            return order
        except Exception as e:
            raise ValidationError(
                {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "message": str(e)
                }
            )

    def verify_payment_signature(self, razorpay_order_id, razorpay_payment_id, razorpay_signature):
        try:
            verify_signature = client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            })
            return verify_signature
        except Exception as e:
            raise ValidationError(
                {
                    "status_code": status.HTTP_400_BAD_REQUEST,
                    "message": str(e)
                }
            )