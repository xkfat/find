from rest_framework import serializers
from .models import Report

class ReportSerializer(serializers.ModelSerializer):
    reporter = serializers.ReadOnlyField(source='user.username')
    missing_person = serializers.ReadOnlyField(source='missing_person.full_name')


    class Meta:
        model = Report
        fields = ['id', 'reporter', 'missing_person', 'note', 'date_submitted', 'report_status']
        read_only_fields = ['id', 'user', 'date_submitted']
