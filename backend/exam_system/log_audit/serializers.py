from rest_framework import serializers
from .models import Log
from exam_system.user_management.serializers import UserSerializer

class LogSerializer(serializers.ModelSerializer):
    """日志序列化器"""
    user = UserSerializer(read_only=True)
    action_type_display = serializers.CharField(source='get_action_type_display', read_only=True)

    class Meta:
        model = Log
        fields = [
            'id',
            'user',
            'action_time',
            'action_type',
            'action_type_display',
            'target_model',
            'target_id',
            'description',
            'status',
            'ip_address',
            'user_agent',
        ]
