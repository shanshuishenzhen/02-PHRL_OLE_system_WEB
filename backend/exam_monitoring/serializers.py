from rest_framework import serializers
from exam_system.exam_monitoring.models import ExamRecord

class ExamSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamRecord
        fields = [
            'id',
            'exam',
            'start_time',
            'end_time',
            'status',
            'remaining_time',
            'is_cheating'
        ]
        read_only_fields = ['id', 'start_time', 'status']