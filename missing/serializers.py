from rest_framework import serializers
from .models import MissingPerson
from django.utils import timezone


class MissingPersonSerializer(serializers.ModelSerializer):
    current_age = serializers.ReadOnlyField()
    reporter = serializers.ReadOnlyField(source='reporter.username')

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
            'reporter',
            'date_reported',
            'days_missing'
        ]
        
    def create(self, validated_data):
        return MissingPerson.objects.create(
            reporter=self.context['request'].user,
            **validated_data
        )