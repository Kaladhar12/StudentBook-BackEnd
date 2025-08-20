from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from studentbookfrontend.models import Class,Student
from studentbookfrontend.helper.payment import *
from razorpay.errors import SignatureVerificationError
from rest_framework.response import Response
from studentbookfrontend.models import *
from django.utils import timezone
from datetime import timedelta
from studentbookfrontend.helper.api_response import api_response

rz_client = RazorpayClient()

class RazorpayOrderAPIView(APIView):
    """This API will create an order"""

    # permission_classes = [IsAuthenticated]

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

            order_response = rz_client.create_order(
                amount=int(amount),
                currency="INR"
            )
            user = Student.objects.get(phone_number=user)

            subscriptionorder = SubscriptionOrder(
                student = user,
                course = student_class,
                price = amount
            )

            subscriptionorder.save()
  
            
 
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

    # permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        if not data.get("order_id"):
            return api_response(
                message="Order Id Not Given",
                message_type="error",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        elif not data.get("payment_id"):
            return api_response(
                message="Payment Id Not Given",
                message_type="error",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        elif not data.get("signature"):
            return api_response(
                message="Payment Signature Id Not Given",
                message_type="error",
                status_code=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            # Verify payment
            rz_client.verify_payment_signature({
                'razorpay_order_id': data.get("order_id"),
                'razorpay_payment_id': data.get("payment_id"),
                'razorpay_signature': data.get("signature")
            })

            student = request.user

            course_id = data.get("course_id")
            price = data.get("price")  # Make sure price is sent in request or fetch it from Course

            if not course_id:
                return api_response(
                        message="Class id is required",
                        message_type="error",
                        status_code=status.HTTP_400_BAD_REQUEST
                    )

            try:
                course = Class.objects.get(id=course_id)
            except Class.DoesNotExist:
                # return Response({"message": "Course not found"}, status=status.HTTP_404_NOT_FOUND)
                return api_response(
                        message="Course not found",
                        message_type="error",
                        status_code=status.HTTP_404_NOT_FOUND
                    )

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
            subscriptionorder = SubscriptionOrder.objects.filter(student = student).first()
            subscriptionorder.payment_status = 'completed'
            subscriptionorder.save()
            # Activate student if inactive
            if not student.is_active:
                student.is_active = True
                student.save()

            # return Response({
            #     "status_code": status.HTTP_201_CREATED,
            #     "message": "Transaction verified and course added to student packages",
            #     "student_package_id": student_package.id
            # }, status=status.HTTP_201_CREATED)
            data = {
                "student_package_id": student_package.id
            }
            return api_response(
                        message="Transaction verified and course added to student packages",
                        message_type="success",
                        status_code=status.HTTP_201_CREATED,
                        data = data
                    )

        except SignatureVerificationError:
            subscriptionorder.payment_status = 'failed'
            subscriptionorder.save()
            # return Response({
            #     "status_code": status.HTTP_400_BAD_REQUEST,
            #     "message": "Payment signature verification failed"
            # }, status=status.HTTP_400_BAD_REQUEST)
            return api_response(
                        message="Payment signature verification failed",
                        message_type="error",
                        status_code=status.HTTP_400_BAD_REQUEST,
                    )

        except Exception as e:
            # return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return api_response(
                        message=str(e),
                        message_type="error",
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )
        
