from rest_framework import serializers
from studentbookfrontend.models import *

class SubjectSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source="course.name", read_only=True)  # To show class name instead of just id
    icon_url = serializers.SerializerMethodField()  # To return full URL of icon

    class Meta:
        model = Subject
        fields = ["id", "name", "icon_url", "course", "course_name"]

    def get_icon_url(self, obj):
        request = self.context.get("request")
        if obj.icon and request:
            return request.build_absolute_uri(obj.icon.url)
        elif obj.icon:
            return obj.icon.url
        return None
