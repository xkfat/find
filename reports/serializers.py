from rest_framework import serializers

from missing.models import MissingPerson
from .models import Report

class ReportSerializer(serializers.ModelSerializer):
    reporter = serializers.SerializerMethodField(read_only=True)
   

    def get_reporter(self, obj):
        if obj.user:
            return obj.user.username
        return "Anonymous"
    class Meta:
        model = Report
        fields = ['id', 'reporter', 'missing_person', 'note', 'date_submitted', 'report_status']
        read_only_fields = ['id', 'date_submitted', 'reporter']
