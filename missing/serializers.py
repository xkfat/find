from rest_framework import serializers
from .models import MissingPerson, CaseUpdate
from django.utils import timezone

class CaseUpdateSerializer(serializers.ModelSerializer):
    formatted_date = serializers.ReadOnlyField()
    
    class Meta:
        model = CaseUpdate
        fields = ['id', 'message', 'timestamp', 'formatted_date']

class MissingPersonSerializer(serializers.ModelSerializer):
    current_age = serializers.ReadOnlyField()
    reporter = serializers.ReadOnlyField(source='reporter.username')
    updates = CaseUpdateSerializer(many=True, read_only=True)
    days_missing = serializers.ReadOnlyField()
    full_name = serializers.ReadOnlyField()
    class Meta:
        model = MissingPerson
        fields = [
            'id',
            'first_name',
            'last_name',
            'full_name',
            'gender',
            'age',
            'current_age',
            'photo',
            'description',
            'last_seen_date',
            'last_seen_location',
            'latitude',
            'longitude',
            'status',
            'submission_status',
            'reporter',
            'date_reported',
            'days_missing',
            'updates'
        ]
        
    def create(self, validated_data):
        return MissingPerson.objects.create(
            reporter=self.context['request'].user,
            **validated_data
        )

class CaseUpdateCreateSerializer(serializers.ModelSerializer):
        class Meta:
            model = CaseUpdate
            fields = ['message']

        def create(self, validated_data):
            case_id = self.context.get('case_id')

            return CaseUpdate.objects.create(
                case_id=case_id,
                **validated_data

            )
        
class SubmittedCaseListSerializer(serializers.ModelSerializer):
    latest_update = serializers.SerializerMethodField()
    class Meta:
        model = MissingPerson
        fields = [
            'id',
            'first_name', 
            'last_name',
            'full_name',
            'submission_status',
            'date_reported',
            'latest_update'
        ]
    def get_latest_update(self, obj):
        latest = obj.updates.first() 
        if latest:
            return {
                'message': latest.message,
                'date': latest.formatted_date,
            }
        return None
