from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    target_model = serializers.SerializerMethodField()
    target_id    = serializers.IntegerField(source='object_id')
    class Meta:
        model = Notification
        fields = ['id', 'user', 'target_id', 'target_model', 'message', 'is_read', 'date_created']
        read_only_fields = ['id', 'user', 'date_created']


    def get_target_model(self, obj):
          if obj.content_type:
             return obj.content_type.model
          return None
