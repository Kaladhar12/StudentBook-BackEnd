from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from studentbookfrontend.models import Class,Student
from helper.payment import *
from razorpay.errors import SignatureVerificationError
from rest_framework.response import Response
from studentbookfrontend.models import StudentPackage
from django.utils import timezone
from datetime import timedelta
from helper.api_response import api_response

rz_client = RazorpayClient()

class RazorpayOrderAPIView(APIView):
    """This API will create an order"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        student_class_id = request.data.get("student_class")
        amount = request.data.get("price")

  


        if not student_class_id:
     

            return api_response(
                message="Class id is required",
                message_type="error",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        try:

            student_class = Class.objects.get(id = student_class_id)
            amount = student_class.amount
            order_response = rz_client.create_order(
                amount=int(amount),
                currency="INR"
            )
            user = Student.objects.get(email=user)
 
            
 
            return api_response(
                message="Order created",
                message_type="created",
                status_code=status.HTTP_201_CREATED,
                data = order_response
            )
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TransactionAPIView(APIView):
    """This API will complete the order and save the transaction"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        try:
            # Verify payment
            rz_client.utility.verify_payment_signature({
                'razorpay_order_id': data.get("order_id"),
                'razorpay_payment_id': data.get("payment_id"),
                'razorpay_signature': data.get("signature")
            })

            student = request.user

            course_id = data.get("course_id")
            price = data.get("price")  # Make sure price is sent in request or fetch it from Course

            if not course_id:
                return Response({"message": "Course ID is required"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                course = Class.objects.get(id=course_id)
            except Class.DoesNotExist:
                return Response({"message": "Course not found"}, status=status.HTTP_404_NOT_FOUND)

            purchase_date = timezone.now()
            valid_till = purchase_date + timedelta(days=365)

            # Create new StudentPackage subscription for this purchase
            student_package = StudentPackage.objects.create(
                student=student,
                course=course,
                price=price if price else 0,  # default to 0 if not provided
                subscription_taken_from=purchase_date,
                subscription_valid_till=valid_till
            )

            # Activate student if inactive
            if not student.is_active:
                student.is_active = True
                student.save()

            return Response({
                "status_code": status.HTTP_201_CREATED,
                "message": "Transaction verified and course added to student packages",
                "student_package_id": student_package.id
            }, status=status.HTTP_201_CREATED)

        except SignatureVerificationError:
            return Response({
                "status_code": status.HTTP_400_BAD_REQUEST,
                "message": "Payment signature verification failed"
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
