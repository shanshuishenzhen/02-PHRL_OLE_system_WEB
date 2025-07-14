from rest_framework import viewsets, status, filters, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db import transaction
from django.db.models import Q

from .models import (
    Exam, ExamRoom, ExamRegistration, ExamRecord, 
    ExamAnswer, ExamSnapshot, ExamNotification
)
from .serializers import (
    ExamSerializer, ExamCreateSerializer, ExamDetailSerializer,
    ExamRoomSerializer, ExamRoomCreateSerializer,
    ExamRegistrationSerializer, ExamRegistrationCreateSerializer, ExamRegistrationApproveSerializer,
    ExamRecordSerializer, ExamRecordCreateSerializer, ExamRecordUpdateSerializer,
    ExamAnswerSerializer, ExamSnapshotSerializer,
    ExamNotificationSerializer, ExamNotificationCreateSerializer
)
from exam_system.user_management.permissions import (
    IsAdminUser, IsTeacherUser, IsStudentUser, IsAdminOrTeacherUser
)


class ExamViewSet(viewsets.ModelViewSet):
    """考试视图集"""
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'subject', 'is_active']
    search_fields = ['name', 'description', 'subject']
    ordering_fields = ['start_time', 'end_time', 'created_at']
    ordering = ['-start_time']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.role == 'admin':
            return Exam.objects.all()
        elif user.role == 'teacher':
            return Exam.objects.filter(created_by=user)
        elif user.role == 'student':
            # 学生只能看到已报名的考试
            registered_exams = ExamRegistration.objects.filter(student=user).values_list('exam_id', flat=True)
            return Exam.objects.filter(id__in=registered_exams, is_active=True)
        return Exam.objects.none()
    
    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update' or self.action == 'partial_update':
            return ExamCreateSerializer
        elif self.action == 'retrieve' or self.action == 'rooms' or self.action == 'registrations':
            return ExamDetailSerializer
        return ExamSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAuthenticated, IsAdminOrTeacherUser]
        elif self.action in ['list', 'retrieve']:
            self.permission_classes = [IsAuthenticated]
        else:
            self.permission_classes = [IsAuthenticated, IsAdminOrTeacherUser]
        return super().get_permissions()
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['get'])
    def rooms(self, request, pk=None):
        """获取考试的考场列表"""
        exam = self.get_object()
        rooms = exam.rooms.all()
        serializer = ExamRoomSerializer(rooms, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def registrations(self, request, pk=None):
        """获取考试的报名列表"""
        exam = self.get_object()
        registrations = exam.registrations.all()
        serializer = ExamRegistrationSerializer(registrations, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def records(self, request, pk=None):
        """获取考试的考试记录列表"""
        exam = self.get_object()
        records = exam.records.all()
        serializer = ExamRecordSerializer(records, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """开始考试"""
        exam = self.get_object()
        if exam.status != 'pending':
            return Response({"detail": "只有未开始的考试才能开始"}, status=status.HTTP_400_BAD_REQUEST)
        
        exam.status = 'in_progress'
        exam.save(update_fields=['status'])
        return Response({"detail": "考试已开始"}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def end(self, request, pk=None):
        """结束考试"""
        exam = self.get_object()
        if exam.status != 'in_progress':
            return Response({"detail": "只有进行中的考试才能结束"}, status=status.HTTP_400_BAD_REQUEST)
        
        exam.status = 'completed'
        exam.save(update_fields=['status'])
        return Response({"detail": "考试已结束"}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """取消考试"""
        exam = self.get_object()
        if exam.status == 'completed':
            return Response({"detail": "已完成的考试不能取消"}, status=status.HTTP_400_BAD_REQUEST)
        
        exam.status = 'cancelled'
        exam.save(update_fields=['status'])
        return Response({"detail": "考试已取消"}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def update_status(self, request):
        """更新所有考试状态"""
        exams = self.get_queryset()
        updated_count = 0
        
        for exam in exams:
            old_status = exam.status
            new_status = exam.update_status()
            if old_status != new_status:
                updated_count += 1
        
        return Response({"detail": f"已更新{updated_count}个考试的状态"}, status=status.HTTP_200_OK)


class ExamRoomViewSet(viewsets.ModelViewSet):
    """考场视图集"""
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['exam']
    search_fields = ['name', 'location']
    ordering_fields = ['name', 'capacity']
    ordering = ['exam', 'name']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.role == 'admin':
            return ExamRoom.objects.all()
        elif user.role == 'teacher':
            # 教师只能看到自己创建的考试的考场
            created_exams = Exam.objects.filter(created_by=user).values_list('id', flat=True)
            return ExamRoom.objects.filter(exam_id__in=created_exams)
        elif user.role == 'student':
            # 学生只能看到自己报名的考试的考场
            registrations = ExamRegistration.objects.filter(student=user, status='approved')
            return ExamRoom.objects.filter(id__in=registrations.values_list('room_id', flat=True))
        return ExamRoom.objects.none()
    
    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update' or self.action == 'partial_update':
            return ExamRoomCreateSerializer
        return ExamRoomSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAuthenticated, IsAdminOrTeacherUser]
        else:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()
    
    @action(detail=True, methods=['get'])
    def registrations(self, request, pk=None):
        """获取考场的报名列表"""
        room = self.get_object()
        registrations = room.registrations.all()
        serializer = ExamRegistrationSerializer(registrations, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def invigilators(self, request, pk=None):
        """获取考场的监考人员列表"""
        room = self.get_object()
        from exam_system.user_management.serializers import UserSerializer
        serializer = UserSerializer(room.invigilators.all(), many=True)
        return Response(serializer.data)


class ExamRegistrationViewSet(viewsets.ModelViewSet):
    """考试报名视图集"""
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['exam', 'student', 'status', 'room']
    search_fields = ['student__username', 'student__name', 'notes']
    ordering_fields = ['registered_at', 'approved_at']
    ordering = ['-registered_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.role == 'admin':
            return ExamRegistration.objects.all()
        elif user.role == 'teacher':
            # 教师只能看到自己创建的考试的报名
            created_exams = Exam.objects.filter(created_by=user).values_list('id', flat=True)
            return ExamRegistration.objects.filter(exam_id__in=created_exams)
        elif user.role == 'student':
            # 学生只能看到自己的报名
            return ExamRegistration.objects.filter(student=user)
        return ExamRegistration.objects.none()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ExamRegistrationCreateSerializer
        elif self.action == 'approve':
            return ExamRegistrationApproveSerializer
        return ExamRegistrationSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = [IsAuthenticated, IsStudentUser]
        elif self.action in ['update', 'partial_update', 'destroy', 'approve']:
            self.permission_classes = [IsAuthenticated, IsAdminOrTeacherUser]
        else:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()
    
    def perform_create(self, serializer):
        # 学生只能为自己报名
        if self.request.user.role == 'student':
            serializer.save(student=self.request.user)
        else:
            serializer.save()
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """审核报名"""
        registration = self.get_object()
        serializer = self.get_serializer(registration, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """取消报名"""
        registration = self.get_object()
        
        # 验证是否可以取消
        if registration.status == 'approved' and registration.exam.start_time <= timezone.now():
            return Response({"detail": "考试已开始，无法取消报名"}, status=status.HTTP_400_BAD_REQUEST)
        
        registration.status = 'cancelled'
        registration.save(update_fields=['status'])
        return Response({"detail": "报名已取消"}, status=status.HTTP_200_OK)


class ExamRecordViewSet(viewsets.ModelViewSet):
    """考试记录视图集"""
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['exam', 'student', 'status']
    search_fields = ['student__username', 'student__name']
    ordering_fields = ['start_time', 'submit_time', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.role == 'admin':
            return ExamRecord.objects.all()
        elif user.role == 'teacher':
            # 教师只能看到自己创建的考试的记录
            created_exams = Exam.objects.filter(created_by=user).values_list('id', flat=True)
            return ExamRecord.objects.filter(exam_id__in=created_exams)
        elif user.role == 'student':
            # 学生只能看到自己的考试记录
            return ExamRecord.objects.filter(student=user)
        return ExamRecord.objects.none()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ExamRecordCreateSerializer
        elif self.action in ['update', 'partial_update', 'submit']:
            return ExamRecordUpdateSerializer
        return ExamRecordSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = [IsAuthenticated, IsStudentUser]
        elif self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAuthenticated, IsAdminOrTeacherUser]
        elif self.action == 'submit':
            self.permission_classes = [IsAuthenticated, IsStudentUser]
        else:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()
    
    def perform_create(self, serializer):
        # 学生只能为自己创建考试记录
        if self.request.user.role == 'student':
            serializer.save(student=self.request.user)
        else:
            serializer.save()
    
    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """提交考试"""
        record = self.get_object()
        
        # 验证是否可以提交
        if record.status != 'in_progress':
            return Response({"detail": "只有进行中的考试才能提交"}, status=status.HTTP_400_BAD_REQUEST)
        
        # 验证提交人是否为考试记录的学生
        if record.student != request.user and not (request.user.is_staff or request.user.role in ['admin', 'teacher']):
            return Response({"detail": "只有考试的学生或管理员/教师才能提交考试"}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = self.get_serializer(record, data={'status': 'submitted'}, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(submit_time=timezone.now())
        
        # 创建提交快照
        ExamSnapshot.objects.create(
            exam_record=record,
            action='submit',
            details="考试已提交"
        )
        
        return Response({"detail": "考试已提交"}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'])
    def answers(self, request, pk=None):
        """获取考试记录的答案列表"""
        record = self.get_object()
        answers = record.answers.all()
        serializer = ExamAnswerSerializer(answers, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def snapshots(self, request, pk=None):
        """获取考试记录的快照列表"""
        record = self.get_object()
        snapshots = record.snapshots.all()
        serializer = ExamSnapshotSerializer(snapshots, many=True)
        return Response(serializer.data)


class ExamAnswerViewSet(viewsets.ModelViewSet):
    """考生答案视图集"""
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['exam_record', 'question_id', 'is_correct']
    ordering_fields = ['question_id', 'created_at']
    ordering = ['question_id']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.role == 'admin':
            return ExamAnswer.objects.all()
        elif user.role == 'teacher':
            # 教师只能看到自己创建的考试的答案
            created_exams = Exam.objects.filter(created_by=user).values_list('id', flat=True)
            return ExamAnswer.objects.filter(exam_record__exam_id__in=created_exams)
        elif user.role == 'student':
            # 学生只能看到自己的答案
            return ExamAnswer.objects.filter(exam_record__student=user)
        return ExamAnswer.objects.none()
    
    def get_serializer_class(self):
        return ExamAnswerSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update']:
            self.permission_classes = [IsAuthenticated, IsStudentUser]
        elif self.action == 'destroy':
            self.permission_classes = [IsAuthenticated, IsAdminOrTeacherUser]
        else:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()
    
    def perform_create(self, serializer):
        # 验证学生是否为考试记录的学生
        exam_record = serializer.validated_data.get('exam_record')
        if exam_record.student != self.request.user and not (self.request.user.is_staff or self.request.user.role in ['admin', 'teacher']):
            raise serializers.ValidationError("只有考试的学生或管理员/教师才能提交答案")
        
        # 验证考试记录状态
        if exam_record.status != 'in_progress':
            raise serializers.ValidationError("只有进行中的考试才能提交答案")
        
        serializer.save()
        
        # 创建修改答案快照
        ExamSnapshot.objects.create(
            exam_record=exam_record,
            action='change_answer',
            details=f"修改了题目{serializer.validated_data.get('question_id')}的答案"
        )


class ExamSnapshotViewSet(viewsets.ModelViewSet):
    """考试快照视图集"""
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['exam_record', 'action', 'is_violation']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.role == 'admin':
            return ExamSnapshot.objects.all()
        elif user.role == 'teacher':
            # 教师只能看到自己创建的考试的快照
            created_exams = Exam.objects.filter(created_by=user).values_list('id', flat=True)
            return ExamSnapshot.objects.filter(exam_record__exam_id__in=created_exams)
        elif user.role == 'student':
            # 学生只能看到自己的快照
            return ExamSnapshot.objects.filter(exam_record__student=user)
        return ExamSnapshot.objects.none()
    
    def get_serializer_class(self):
        return ExamSnapshotSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = [IsAuthenticated]
        elif self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAuthenticated, IsAdminOrTeacherUser]
        else:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()
    
    def perform_create(self, serializer):
        # 验证学生是否为考试记录的学生
        exam_record = serializer.validated_data.get('exam_record')
        if exam_record.student != self.request.user and not (self.request.user.is_staff or self.request.user.role in ['admin', 'teacher']):
            raise serializers.ValidationError("只有考试的学生或管理员/教师才能创建快照")
        
        serializer.save()


class ExamNotificationViewSet(viewsets.ModelViewSet):
    """考试通知视图集"""
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['exam', 'room', 'student', 'type', 'is_read']
    search_fields = ['title', 'content']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.role == 'admin':
            return ExamNotification.objects.all()
        elif user.role == 'teacher':
            # 教师只能看到自己创建的考试的通知或自己发送的通知
            created_exams = Exam.objects.filter(created_by=user).values_list('id', flat=True)
            return ExamNotification.objects.filter(
                Q(exam_id__in=created_exams) | Q(sender=user)
            )
        elif user.role == 'student':
            # 学生只能看到发给自己的通知或发给自己考场的通知
            student_rooms = ExamRegistration.objects.filter(
                student=user, status='approved'
            ).values_list('room_id', flat=True)
            
            return ExamNotification.objects.filter(
                Q(student=user) | Q(room_id__in=student_rooms) | Q(student=None, room=None)
            )
        return ExamNotification.objects.none()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ExamNotificationCreateSerializer
        return ExamNotificationSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAuthenticated, IsAdminOrTeacherUser]
        else:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """标记通知为已读"""
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        return Response({"detail": "通知已标记为已读"}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        """标记所有通知为已读"""
        queryset = self.filter_queryset(self.get_queryset())
        count = queryset.filter(is_read=False).update(is_read=True)
        return Response({"detail": f"已将{count}条通知标记为已读"}, status=status.HTTP_200_OK)
