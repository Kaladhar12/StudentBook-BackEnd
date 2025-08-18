from django.urls import path
from studentbookfrontend.views.user_views import *


urlpatterns = [
 
    path('login', CustomTokenObtainPairView.as_view()),
    path('logout', LogoutView.as_view()),
    path('user-forgot-password', ForgotPasswordAPIView.as_view()),
    path('student-register', StudentRegisterAPIView.as_view()),
    path('student-activation', StudentActivationAPIView.as_view()),
    path('student-list', StudentListAPIView.as_view()),
    path('student-detail/<int:pk>', StudentDetailAPI.as_view()),
    path('class-list', ClassListAPIView.as_view()),

]