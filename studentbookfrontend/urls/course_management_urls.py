from django.urls import path
from studentbookfrontend.views.course_management_views import *


urlpatterns = [
    path("subjects/", SubjectListCreateView.as_view(), name="subject-list-create"),
    path("subjects/<int:pk>/", SubjectDetailView.as_view(), name="subject-detail"),
]
