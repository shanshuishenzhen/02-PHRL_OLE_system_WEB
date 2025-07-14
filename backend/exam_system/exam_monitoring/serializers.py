from rest_framework import serializers
from django.utils import timezone
from django.db import transaction
from .models import (
    Exam, ExamRoom, ExamRegistration, ExamRecord, 
    ExamAnswer, ExamSnapshot, ExamNotification
)
from exam_system.user_management.serializers import UserSerializer
from exam_system.paper_management.serializers import PaperSerializer


class ExamRoomSerializer(serializers.ModelSerializer):
    """考场序列化器"""
    invigilators_info = UserSerializer(source='invigilators', many=True, read_only=True)
    
    class Meta:
        model = ExamRoom
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class ExamRoomCreateSerializer(serializers.ModelSerializer):
    """考场创建序列化器"""
    class Meta:
        model = ExamRoom
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class ExamSerializer(serializers.ModelSerializer):
    """考试序列化器"""
    created_by_info = UserSerializer(source='created_by', read_only=True)
    paper_info = PaperSerializer(source='paper', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    rooms_count = serializers.SerializerMethodField()
    registrations_count = serializers.SerializerMethodField()
    records_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Exam
        fields = '__all__'
        read_only_fields = ['status', 'created_at', 'updated_at', 'created_by_info', 'paper_info', 
                           'status_display', 'rooms_count', 'registrations_count', 'records_count']
    
    def get_rooms_count(self, obj):
        return obj.rooms.count()
    
    def get_registrations_count(self, obj):
        return obj.registrations.count()
    
    def get_records_count(self, obj):
        return obj.records.count()


class ExamCreateSerializer(serializers.ModelSerializer):
    """考试创建序列化器"""
    class Meta:
        model = Exam
        fields = '__all__'
        read_only_fields = ['status', 'created_at', 'updated_at']
    
    def validate(self, data):
        # 验证开始时间和结束时间
        if data.get('start_time') and data.get('end_time'):
            if data['start_time'] >= data['end_time']:
                raise serializers.ValidationError("结束时间必须晚于开始时间")
            
            # 验证考试时长与开始结束时间的一致性
            if data.get('duration'):
                duration_minutes = (data['end_time'] - data['start_time']).total_seconds() / 60
                if data['duration'] > duration_minutes:
                    raise serializers.ValidationError("考试时长不能超过开始时间和结束时间之间的间隔")
        
        # 验证试卷状态
        if data.get('paper'):
            paper = data['paper']
            if paper.status != 'published':
                raise serializers.ValidationError("只能选择已发布的试卷")
        
        return data


class ExamDetailSerializer(ExamSerializer):
    """考试详情序列化器"""
    rooms = ExamRoomSerializer(many=True, read_only=True)
    
    class Meta(ExamSerializer.Meta):
        fields = ExamSerializer.Meta.fields


class ExamRegistrationSerializer(serializers.ModelSerializer):
    """考试报名序列化器"""
    student_info = UserSerializer(source='student', read_only=True)
    exam_info = ExamSerializer(source='exam', read_only=True)
    room_info = ExamRoomSerializer(source='room', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = ExamRegistration
        fields = '__all__'
        read_only_fields = ['registered_at', 'approved_at', 'approved_by']


class ExamRegistrationCreateSerializer(serializers.ModelSerializer):
    """考试报名创建序列化器"""
    class Meta:
        model = ExamRegistration
        fields = ['exam', 'student', 'notes']
    
    def validate(self, data):
        # 验证考试是否已开始
        exam = data.get('exam')
        if exam and exam.start_time <= timezone.now():
            raise serializers.ValidationError("考试已开始，无法报名")
        
        # 验证学生是否已报名该考试
        student = data.get('student')
        if ExamRegistration.objects.filter(exam=exam, student=student).exists():
            raise serializers.ValidationError("该学生已报名此考试")
        
        return data


class ExamRegistrationApproveSerializer(serializers.ModelSerializer):
    """考试报名审核序列化器"""
    class Meta:
        model = ExamRegistration
        fields = ['status', 'room', 'seat_number', 'notes']
    
    def validate(self, data):
        # 验证状态
        if data.get('status') not in ['approved', 'rejected']:
            raise serializers.ValidationError("状态必须为'已审核'或'已拒绝'")
        
        # 如果状态为已审核，则必须指定考场
        if data.get('status') == 'approved' and not data.get('room'):
            raise serializers.ValidationError("审核通过必须指定考场")
        
        return data
    
    def update(self, instance, validated_data):
        validated_data['approved_at'] = timezone.now()
        validated_data['approved_by'] = self.context['request'].user
        return super().update(instance, validated_data)


class ExamRecordSerializer(serializers.ModelSerializer):
    """考试记录序列化器"""
    student_info = UserSerializer(source='student', read_only=True)
    exam_info = ExamSerializer(source='exam', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = ExamRecord
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
    
    def get_duration(self, obj):
        return obj.calculate_duration()


class ExamRecordCreateSerializer(serializers.ModelSerializer):
    """考试记录创建序列化器"""
    class Meta:
        model = ExamRecord
        fields = ['exam', 'student', 'registration', 'ip_address', 'user_agent']
    
    def validate(self, data):
        # 验证考试状态
        exam = data.get('exam')
        if exam.status != 'in_progress':
            raise serializers.ValidationError("考试未在进行中，无法创建考试记录")
        
        # 验证报名状态
        registration = data.get('registration')
        if registration.status != 'approved':
            raise serializers.ValidationError("报名未审核通过，无法参加考试")
        
        # 验证学生与报名记录是否匹配
        student = data.get('student')
        if registration.student != student:
            raise serializers.ValidationError("学生与报名记录不匹配")
        
        # 验证考试与报名记录是否匹配
        if registration.exam != exam:
            raise serializers.ValidationError("考试与报名记录不匹配")
        
        # 验证是否已存在考试记录
        if ExamRecord.objects.filter(exam=exam, student=student).exists():
            raise serializers.ValidationError("该学生已有此考试的考试记录")
        
        return data
    
    def create(self, validated_data):
        validated_data['start_time'] = timezone.now()
        validated_data['status'] = 'in_progress'
        return super().create(validated_data)


class ExamRecordUpdateSerializer(serializers.ModelSerializer):
    """考试记录更新序列化器"""
    class Meta:
        model = ExamRecord
        fields = ['status']
    
    def validate(self, data):
        # 验证状态
        if data.get('status') not in ['in_progress', 'submitted', 'cancelled']:
            raise serializers.ValidationError("状态必须为'进行中'、'已提交'或'已取消'")
        
        # 如果状态为已提交，则更新提交时间
        if data.get('status') == 'submitted':
            data['submit_time'] = timezone.now()
        
        return data


class ExamAnswerSerializer(serializers.ModelSerializer):
    """考生答案序列化器"""
    class Meta:
        model = ExamAnswer
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'is_correct', 'score']
    
    def validate(self, data):
        # 验证考试记录状态
        exam_record = data.get('exam_record')
        if exam_record and exam_record.status != 'in_progress':
            raise serializers.ValidationError("考试未在进行中，无法提交答案")
        
        return data


class ExamSnapshotSerializer(serializers.ModelSerializer):
    """考试快照序列化器"""
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = ExamSnapshot
        fields = '__all__'
        read_only_fields = ['timestamp']


class ExamNotificationSerializer(serializers.ModelSerializer):
    """考试通知序列化器"""
    sender_info = UserSerializer(source='sender', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    
    class Meta:
        model = ExamNotification
        fields = '__all__'
        read_only_fields = ['created_at']


class ExamNotificationCreateSerializer(serializers.ModelSerializer):
    """考试通知创建序列化器"""
    class Meta:
        model = ExamNotification
        fields = ['exam', 'room', 'student', 'type', 'title', 'content']
    
    def create(self, validated_data):
        validated_data['sender'] = self.context['request'].user
        return super().create(validated_data)
