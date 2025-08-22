import random
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from django.utils import timezone
from django.conf import settings
from twilio.rest import Client
from rest_framework import status
from rest_framework.response import Response
from django.template.loader import render_to_string
from django.utils.html import strip_tags



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


def send_otp_phone_number(user,subject_type, phone_number_field="phone_number"):
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
    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=f"Your OTP is: {otp} for {subject_type}",
            from_=settings.TWILIO_PHONE_NUMBER,
            to='+91'+str(phone_number)
        )
        return Response({"message": f"OTP sent to {phone_number}", "otp": otp}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def send_success_email(user, email_field="email"):
    """
    send success mail
    """
    receiver_email = getattr(user, email_field) 
    subject = 'Welcome to Student Book!'
    context = {
        'customer_name': f"{user.first_name} {user.last_name}",
        'login_id': user.email if user.email else None,
        'phone_number': user.phone_number,
    }
    html_message = render_to_string('welcome_mail.html', context)
    plain_message = strip_tags(html_message)

    # Email configuration
    sender_email = settings.EMAIL_HOST_USER


    # Create a MIME multipart message
    message = MIMEMultipart()
    message["From"] = f'Student Book <{sender_email}>'
    message["To"] = receiver_email
    message["Subject"] = subject


    html_text_part = MIMEText(html_message, "html")
    message.attach(html_text_part)

    # SMTP server configuration
    smtp_server = settings.EMAIL_HOST
    smtp_port = 465  # SMTP SSL/TLS port

    # Login credentials for SMTP server
    smtp_username = settings.EMAIL_HOST_USER
    smtp_password = settings.EMAIL_HOST_PASSWORD

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


def send_succes_message_phone_number(user, phone_number_field="phone_number"):
    """
   
    send success mail on registration
    """

    
    phone_number = getattr(user, phone_number_field)
    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=f"Your Registration  is successfull to Stuedent Book and your user id is {phone_number}",
            from_=settings.TWILIO_PHONE_NUMBER,
            to='+91'+str(phone_number)
        )
        return Response({"message": f"OTP sent to {phone_number}" }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
  
