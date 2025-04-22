from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import MissingPerson


class MissingPersonSerializer(serializers.ModelSerializer):
    current_age = serializers.ReadOnlyField()

    class Meta:
        model = MissingPerson
        fields = [
            'id',
            'first_name',
            'last_name',
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
        ]
        read_only_fields = ['id', 'current_age', 'reporter', 'date_reported']


  