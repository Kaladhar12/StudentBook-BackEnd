import random
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from django.utils import timezone
from django.conf import settings
from twilio.rest import Client
from rest_framework import status
from rest_framework.response import Response


def send_otp_email(user,subject_type, email_field="email"):
    """
    Generates an OTP, saves it to user, and sends an email.
    Works for Student/User model that has fields: otp, otp_created_at
    """

    # 1. Generate OTP
    otp = str(random.randint(100000, 999999))
    user.otp = otp
    user.otp_created_at = timezone.now()
    user.save()

    # 2. Email config
    subject = subject_type
    sender_email = settings.EMAIL_HOST_USER
    receiver_email = getattr(user, email_field)  # get user.email
    body = f"Your OTP for School Book is: {otp}\nThis OTP is valid for 10 minutes."

    # 3. Create message
    message = MIMEMultipart()
    message["From"] = f"School Book <{sender_email}>"
    message["To"] = receiver_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    # 4. Send email via SMTP
    try:
        server = smtplib.SMTP_SSL(settings.EMAIL_HOST, 465)
        server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        server.sendmail(sender_email, receiver_email, message.as_string())
        print(f"✅ OTP sent to {receiver_email}")
    except Exception as e:
        print(f"❌ Error sending OTP: {e}")
    finally:
        server.quit()

    return otp


def send_otp_phone_number(user, phone_number_field="phone_number"):
    """
    Generates an OTP, saves it to user, and sends an email.
    Works for Student/User model that has fields: otp, otp_created_at
    """

    # 1. Generate OTP
    otp = str(random.randint(100000, 999999))
    user.otp = otp
    user.otp_created_at = timezone.now()
    user.save()
    phone_number = getattr(user, phone_number_field)
    print('phone_number',phone_number)
    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=f"Your OTP is: {otp}",
            from_=settings.TWILIO_PHONE_NUMBER,
            to='+91'+str(phone_number)
        )
        return Response({"message": f"OTP sent to {phone_number}", "otp": otp}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
