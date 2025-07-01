from rest_framework import serializers
from .models import AIMatch
from missing.serializers import MissingPersonSerializer

class AIMatchSerializer(serializers.ModelSerializer):
    original_case_details = MissingPersonSerializer(source='original_case', read_only=True)
    matched_case_details = MissingPersonSerializer(source='matched_case', read_only=True)
    confidence_level = serializers.ReadOnlyField()
  #  reviewed_by_username = serializers.CharField(source='reviewed_by.username', read_only=True)
    processing_date_formatted = serializers.SerializerMethodField()
    review_date_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = AIMatch
        fields = [
            'id', 'original_case', 'matched_case', 'confidence_score', 
            'confidence_level', 'status', 
            #'algorithm_used', 
            'face_distance',
            'processing_date', 'processing_date_formatted', 
            #'reviewed_by', 
            #'reviewed_by_username', 
            'review_date', 'review_date_formatted',
            #'admin_notes', 
            'original_case_details', 'matched_case_details'
        ]
        read_only_fields = [
            'id', 'processing_date', 'confidence_level', 
            #'reviewed_by_username',
            'processing_date_formatted', 'review_date_formatted'
        ]
    
    def get_processing_date_formatted(self, obj):
        return obj.processing_date.strftime('%Y-%m-%d') if obj.processing_date else None
    
    def get_review_date_formatted(self, obj):
        return obj.review_date.strftime('%Y-%m-%d') if obj.review_date else None

class AIMatchActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['confirm', 'reject', 'under_review', 'pending'])
  #  admin_notes = serializers.CharField(required=False, allow_blank=True)