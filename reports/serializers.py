from rest_framework import serializers
from .models import Report

class ReportSerializer(serializers.ModelSerializer):
    reporter = serializers.StringRelatedField(source='user.username', read_only=True)
    missing_person = serializers.StringRelatedField(read_only=True)


    class Meta:
        model = Report
        fields = ['id', 'reporter', 'missing_person', 'note', 'date_submitted', 'report_status']
        read_only_fields = ['id', 'user', 'date_submitted']
