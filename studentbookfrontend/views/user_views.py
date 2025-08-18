from django.shortcuts import render
from studentbookfrontend.serializers.user_serializers import *
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import status, permissions
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from studentbookbackend.settings import EMAIL_HOST_USER,EMAIL_HOST,EMAIL_HOST_PASSWORD
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from rest_framework import status

from django.shortcuts import get_object_or_404

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from studentbookfrontend.helper.api_response import api_response
import random
from studentbookfrontend.models import *
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

# Create your views here.


class EmailOrPhoneBackend(ModelBackend):
    def authenticate(self, request, email=None, password=None, **kwargs):
        UserModel = get_user_model()
        try:
            if email and '@' not in email:
                user = UserModel.objects.get(phone_number=email)
            else:
                user = UserModel.objects.get(email=email)
        except UserModel.DoesNotExist:
            user = None

        if user and user.check_password(password):
            user.update_login_time()  #
            return user
        return None

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

class ClassListAPIView(generics.ListAPIView):
    # permission_classes = [IsAuthenticated]
    queryset = Class.objects.all()
    serializer_class = ClassSerializer
    permission_classes = [AllowAny]



class StudentListAPIView(APIView):
    # permission_classes = [IsAuthenticated]
    def get(self, request, format=None):
        students = Student.objects.all()
        serializer = StudentSerializer(students, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = StudentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class StudentDetailAPI(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, pk, format=None):
        student = get_object_or_404(Student, pk=pk)
        serializer = StudentSerializer(student)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        student = get_object_or_404(Student, pk=pk)
        serializer = StudentSerializer(student, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        student = get_object_or_404(Student, pk=pk)
        student.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class LogoutView(APIView):
    
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            # return Response({"error": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)
            return api_response(
                message="Refresh token is required.",
                message_type="error",
                status_code=status.HTTP_400_BAD_REQUEST
                        )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()

            # return Response({"message": "Logged out successfully."}, status=status.HTTP_205_RESET_CONTENT)
            return api_response(
                message="Logged out successfully.",
                message_type="success",
                status_code=status.HTTP_205_RESET_CONTENT
                        )

        except TokenError:
            # return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)
            return api_response(
                message="Invalid or expired token.",
                message_type="error",
                status_code=status.HTTP_400_BAD_REQUEST
                        )



class ForgotPasswordAPIView(APIView):
    
    def post(self, request, *args, **kwargs):

        json_data = request.data
        email = json_data.get("email")

        user = User.objects.filter(email=email).first()

        if user:

            otp = str(random.randint(100000, 999999))
            user.otp = otp
            user.save()
            subject = 'Password Reset OTP'
            # Email configuration
            sender_email = EMAIL_HOST_USER
            receiver_email = json_data['email']
            body = f"OTP to reset your password: {otp}"

            # Create a MIME multipart message
            message = MIMEMultipart()
            message["From"] = f'Student Book <{sender_email}>'
            message["To"] = receiver_email
            message["Subject"] = subject

            # # Attach plain text version
            message.attach(MIMEText(body, "plain"))
         

            # SMTP server configuration
            smtp_server = EMAIL_HOST
            smtp_port = 465  # SMTP SSL/TLS port

            # Login credentials for SMTP server
            smtp_username = EMAIL_HOST_USER
            smtp_password = EMAIL_HOST_PASSWORD

            # Create an SMTP session
            try:
                server = smtplib.SMTP_SSL(smtp_server, smtp_port)
                server.login(smtp_username, smtp_password)

                # Send the email
                text = message.as_string()
                server.sendmail(sender_email, receiver_email, text)
                print("Email sent successfully!")
            except Exception as e:
                print(f"Error: {e}")
            finally:
                # Close the SMTP session
                server.quit()

            # return Response({"message": "For resetting the password an OTP sent to your email."},
            #                 status=status.HTTP_200_OK)
            return api_response(
                message="For resetting the password an OTP sent to your email.",
                message_type="success",
                status_code=status.HTTP_200_OK
                        )
            
        else:
            # return Response({"message": "User not found."}, status=status.HTTP_404_NOT_FOUND)
            return api_response(
                message="User not found.",
                message_type="error",
                status_code=status.HTTP_400_BAD_REQUEST
                        )

    def put(self, request, *args, **kwargs):
        json_data = request.data
        email = json_data.get("email")
        otp = json_data.get("otp")
        print(otp)
        new_password = json_data.get("new_password")
        confirm_new_password = json_data.get("confirm_new_password")

        # Step 1: Verify OTP
        if otp and not new_password and not confirm_new_password:
            if not all([email, otp]):
                # return Response({"message": "Email and OTP are required."}, status=status.HTTP_400_BAD_REQUEST)
                return api_response(
                message="Email and OTP are required.",
                message_type="error",
                status_code=status.HTTP_400_BAD_REQUEST
                        )

            user = User.objects.filter(email=email, otp=otp).first()
           
            if user:
                # OTP is correct, mark it as verified
                user.otp_verified = True  # Assuming you have this field
                user.save()
                return Response({"message": "OTP verified successfully."}, status=status.HTTP_200_OK)
            else:
                return Response({"message": "Invalid OTP or email."}, status=status.HTTP_400_BAD_REQUEST)

        # Step 2: Update Password
        elif otp and new_password and confirm_new_password:
            if not all([email, otp, new_password, confirm_new_password]):
                # return Response({"message": "All fields are required."}, status=status.HTTP_400_BAD_REQUEST)
                return api_response(
                message="All fields are required.",
                message_type="error",
                status_code=status.HTTP_400_BAD_REQUEST
                        )

            if new_password != confirm_new_password:
                # return Response({"message": "Passwords do not match."}, status=status.HTTP_400_BAD_REQUEST)
                return api_response(
                message="Passwords do not match.",
                message_type="error",
                status_code=status.HTTP_400_BAD_REQUEST
                        )

            user = User.objects.filter(email=email, otp=otp).first()
            print("user",user)
            if user:
                user.set_password(new_password)
                user.otp = None
                user.otp_verified = False 
                user.save()
                # return Response({"message": "Password reset successfully."}, status=status.HTTP_200_OK)
                return api_response(
                message="Password reset successfully.",
                message_type="success",
                status_code=status.HTTP_200_OK
                        )

            else:
                # return Response({"message": "Invalid email or OTP not verified."}, status=status.HTTP_400_BAD_REQUEST)
                return api_response(
                message="Invalid email or OTP not verified.",
                message_type="error",
                status_code=status.HTTP_400_BAD_REQUEST
                        )


        else:
            # return Response({"message": "Invalid request."}, status=status.HTTP_400_BAD_REQUEST)
            return api_response(
                message="Invalid request.",
                message_type="error",
                status_code=status.HTTP_400_BAD_REQUEST
                        )


class StudentRegisterAPIView(APIView):


    def post(self, request, *args, **kwargs):
        json_data = request.data

        try:
            validate_email(json_data['email'])
        except ValidationError as e:
            # return Response({"message": "Invalid email format."}, status=status.HTTP_400_BAD_REQUEST)
            return api_response(
                message="Invalid email format.",
                message_type="error",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # try:
        try:
            customer = User.objects.get(email=json_data['email'])
   
            # return Response({"error": "Email already exists"}, status=status.HTTP_400_BAD_REQUEST)
            return api_response(
                message="Email already exists",
                message_type="error",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except User.DoesNotExist:
            try:
                customer = User.objects.get(phone_number=json_data['phone_number'])
                # if customer:
                    # print("bye")
                # return Response({"error": "Phone number already exists"}, status=status.HTTP_400_BAD_REQUEST)
                return api_response(
                message="Phone number already exists",
                message_type="error",
                status_code=status.HTTP_400_BAD_REQUEST
                        )
            except User.DoesNotExist:
                # If neither email nor phone number exists, proceed with your logic here
                # pass

        # except:

                class_name = json_data['student_class']
                try:
                    class_obj = Class.objects.get(id=class_name)
                except Class.DoesNotExist:
                    # return Response({"error": "Class not found"}, status=400)
                    return api_response(
                                    message="Class not found",
                                    message_type="error",
                                    status_code=status.HTTP_400_BAD_REQUEST
                                )

                customer_register = Student(
                    email=json_data['email'],
                    first_name=json_data['first_name'],
                    last_name=json_data['last_name'],
                    phone_number=json_data['phone_number'],
                    address=json_data['address'],
                    zip_code=json_data['zip_code'],
                    user_type='student',
                    student_class = class_obj,
                    is_active=False
                )
                customer_register.save()

                user = Student.objects.get(email=json_data['email'])

                if user:

                    otp = str(random.randint(100000, 999999))
                    user.otp = otp
                    user.save()
                    subject = 'Registration OTP'
                    # Email configuration
                    sender_email = EMAIL_HOST_USER
                    receiver_email = json_data['email']
                    body = f"OTP to register on School Book : {otp}"

                    # Create a MIME multipart message
                    message = MIMEMultipart()
                    message["From"] = f'School Book <{sender_email}>'
                    message["To"] = receiver_email
                    message["Subject"] = subject

                    # # Attach plain text version
                    message.attach(MIMEText(body, "plain"))

                    smtp_server = EMAIL_HOST
                    smtp_port = 465  # SMTP SSL/TLS port

                    # Login credentials for SMTP server
                    smtp_username = EMAIL_HOST_USER
                    smtp_password = EMAIL_HOST_PASSWORD

                    # Create an SMTP session
                    try:
                        server = smtplib.SMTP_SSL(smtp_server, smtp_port)
                        server.login(smtp_username, smtp_password)

                        # Send the email
                        text = message.as_string()
                        server.sendmail(sender_email, receiver_email, text)
                        print("Email sent successfully!")



                    except Exception as e:
                        print(f"Error: {e}")
                    finally:
                        # Close the SMTP session
                        server.quit()

                    # return Response({"message": "For registering on School Book  an OTP sent to your email."},
                    #                 status=status.HTTP_200_OK)
                    return api_response(
                                    message="For registering on School Book  an OTP sent to your email.",
                                    message_type="success",
                                    status_code=status.HTTP_200_OK
                                )
                else:
                    # return Response({"message": "User not found."}, status=status.HTTP_404_NOT_FOUND)

                    return api_response(
                                    message="User not found.",
                                    message_type="error",
                                    status_code=status.HTTP_404_NOT_FOUND
                                )


class StudentActivationAPIView(APIView):


    def post(self, request, *args, **kwargs):
        json_data = request.data
        otp = json_data.get('otp',None)
        user = Student.objects.get(email=json_data['email'])
        
        if  otp is None:
            # response = {
            #     "message": "provide otp"
            # }
            
            # return Response(response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return api_response(
                            message="Provide OTP",
                            message_type="error",
                            status_code=status.HTTP_400_BAD_REQUEST
                        )
        
            
        if user.otp == json_data['otp']:
           
            user.set_password(json_data['password'])
            user.is_active=True
            user.otp_verified = True
            
            
            user.save()

            subject = 'Welcome to Student Book!'
            context = {
                'customer_name': f"{json_data['first_name']} {json_data['last_name']}",
                'login_id': json_data['email'],
                'password': json_data['password'],
                'phone_number': json_data['phone_number'],
                'address': json_data['address'],
            }
            html_message = render_to_string('welcome_mail.html', context)
            plain_message = strip_tags(html_message)

            # Email configuration
            sender_email = EMAIL_HOST_USER
            receiver_email = json_data['email']
        

            # Create a MIME multipart message
            message = MIMEMultipart()
            message["From"] = f'Student Book <{sender_email}>'
            message["To"] = receiver_email
            message["Subject"] = subject


            html_text_part = MIMEText(html_message, "html")
            message.attach(html_text_part)

            # SMTP server configuration
            smtp_server = EMAIL_HOST
            smtp_port = 465  # SMTP SSL/TLS port

            # Login credentials for SMTP server
            smtp_username = EMAIL_HOST_USER
            smtp_password = EMAIL_HOST_PASSWORD

            # Create an SMTP session
            try:
                server = smtplib.SMTP_SSL(smtp_server, smtp_port)
                server.login(smtp_username, smtp_password)

                # Send the email
                text = message.as_string()
                server.sendmail(sender_email, receiver_email, text)
                print("Email sent successfully!")
            except Exception as e:
                print(f"Error: {e}")
            finally:
                # Close the SMTP session
                server.quit()

            # response = {
            #     "message": "Your registration completed successfully"
            # }

            # return Response(response, status=status.HTTP_201_CREATED)
            return api_response(
                            message="Your registration completed successfully",
                            message_type="success",
                            status_code=status.HTTP_200_OK
                        )
            
        else:
            # response = {
            #     "message": "OTP is incorrect"
            # }

            # return Response(response, status=status.HTTP_400_BAD_REQUEST)
            return api_response(
                            message="OTP is incorrect",
                            message_type="error",
                            status_code=status.HTTP_400_BAD_REQUEST
                        )

