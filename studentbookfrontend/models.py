from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.utils import timezone
from datetime import timedelta
# Create your models here.


#User models

class School(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Class(models.Model):
    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=2000)
    def __str__(self):
        return self.name
    
class StudentPackage(models.Model):
    student = models.ForeignKey("Student", on_delete=models.CASCADE, related_name="student_packages")
    course = models.ForeignKey("Class", on_delete=models.CASCADE)
    price = models.IntegerField()
    subscription_taken_from = models.DateField(default=timezone.now)
    subscription_valid_till = models.DateField()

    def save(self, *args, **kwargs):
        if not self.subscription_valid_till:
            self.subscription_valid_till = self.subscription_taken_from + timedelta(days=365)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.email} - {self.course.name}"

# class UserManager(BaseUserManager):
#     def create_user(self, email, password=None):
#         """
#         Creates and saves a User with the given email, date of
#         birth and password.
#         """
#         if not email:
#             raise ValueError("Users must have an email address")

#         user = self.model(
#             email=self.normalize_email(email),
#         )

#         user.set_password(password)
#         user.save(using=self._db)
#         return user

#     def create_superuser(self, email, password=None):
#         """
#         Creates and saves a superuser with the given email, date of
#         birth and password.
#         """
#         user = self.create_user(
#             email,
#             password=password,
#         )
#         user.is_superuser = True
#         user.save(using=self._db)
#         return user


class UserManager(BaseUserManager):
    def create_user(self, phone_number, password=None):
        """
        Creates and saves a User with the given email, date of
        birth and password.
        """
        if not phone_number:
            raise ValueError("Users must have an email address")

        user = self.model(
            phone_number=self.normalize_email(phone_number),
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None):
        """
        Creates and saves a superuser with the given email, date of
        birth and password.
        """
        user = self.create_user(
            phone_number,
            password=password,
        )
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    USER_TYPE_CHOICES = [  
        ('student', 'Student'),
        ('instructor', 'Instructor'),
        ('admin', 'Admin')
    ]

    email = models.EmailField(
       
        max_length=255,
        null=True,
        blank=True
        
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    profile_image = models.ImageField(upload_to="profile",blank=True)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    phone_number = models.CharField(max_length=50,unique=True, verbose_name="phone number",)
    address=models.CharField(max_length=300,null=True,blank=True)
    city = models.CharField(max_length=200,null=True,blank=True)
    state = models.CharField(max_length=200,null=True,blank=True)
    zip_code = models.CharField(max_length=50,null=True,blank=True)
    otp = models.CharField(max_length=50,null=True,blank=True)
    user_type = models.CharField(max_length=20, null=True,choices=USER_TYPE_CHOICES)
    login_time = models.DateTimeField(null=True)
    otp_verified = models.BooleanField(default=False)
    registered_date = models.DateTimeField(auto_now_add=True)
    objects = UserManager()

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.phone_number
    def update_login_time(self):
        self.login_time = timezone.now()
        self.save()

    def save(self, *args, **kwargs):
        if self.is_superuser and not self.user_type:
            self.user_type = 'admin'
        super().save(*args, **kwargs)



    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_superuser


class Student(User):
    # registration_id = models.CharField(max_length=20, unique=True, editable=False)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="students", null=True,blank=True)
    student_class = models.ForeignKey(Class, on_delete=models.CASCADE, related_name="main_students")


    def save(self, *args, **kwargs):

        super().save(*args, **kwargs)

    def __str__(self):
        return self.phone_number
    


class SubscriptionOrder(models.Model):
    """
    Represents a subscription order placed by a student for a specific course.
    Handles payment status and subscription validity dates.
    """

    PAYMENT_STATUS = [  
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    student = models.ForeignKey(
        "Student",
        on_delete=models.CASCADE,
        related_name="subscription_orders"
    )
    course = models.ForeignKey(
        "Class",
        on_delete=models.CASCADE,
        related_name="subscription_orders"
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    payment_status = models.CharField(max_length=20,choices=PAYMENT_STATUS,default="pending")

    subscription_start = models.DateField(default=timezone.now)
    subscription_end = models.DateField(blank=True, null=True)

    def save(self, *args, **kwargs):
        """
        Automatically set subscription_end to 1 year (365 days) after
        subscription_start if not provided manually.
        """
        if not self.subscription_end:
            self.subscription_end = self.subscription_start + timedelta(days=365)
        super().save(*args, **kwargs)

    @property
    def is_paid(self) -> bool:
        """
        Returns True if the order has been paid successfully.
        Helps in quick checks for access control or subscription validation.
        """
        return self.payment_status == "completed"

    def __str__(self):
        """Readable representation for admin panel & debugging."""
        return self.student.phone_number
