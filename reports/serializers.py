from rest_framework import serializers
from .models import Report

class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ['id', 'user', 'missing_person', 'note', 'date_submitted', 'report_status']
        read_only_fields = ['user', 'date_submitted']
