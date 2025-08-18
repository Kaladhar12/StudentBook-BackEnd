from django.contrib import admin
from .models import *
# Register your models here.

#user models register

class UserAdmin(admin.ModelAdmin):
    list_display = ['id','first_name', 'last_name','email','phone_number', 'user_type',
                 'is_superuser', 'is_active']
    list_filter = ('user_type',)


class StudentAdmin(admin.ModelAdmin):
    list_display = ['id','first_name', 'last_name','email','phone_number', 'user_type','student_class']

class SchoolAdmin(admin.ModelAdmin):
    list_display = ['id','name']

class ClassAdmin(admin.ModelAdmin):
    list_display = ['id','name']

class StudentPackageAdmin(admin.ModelAdmin):
    list_display = ['id','student','course','price','subscription_taken_from','subscription_valid_till']

admin.site.register(User,UserAdmin)
admin.site.register(StudentPackage,StudentPackageAdmin)
admin.site.register(Student,StudentAdmin)
admin.site.register(School,SchoolAdmin)
admin.site.register(Class,ClassAdmin)

#user models register end
