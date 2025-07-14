from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils import timezone

from exam_system.common.permissions import IsTeacherOrAdmin, IsStudent
from exam_system.exam_monitoring.models import Exam, ExamRecord

from .models import (
    ScoringCriteria, ScoringRule, ScoreSheet, ScoreItem,
    ScoreDistribution, ScoreStatistics, ScoreAppeal
)
from .serializers import (
    ScoringCriteriaSerializer, ScoringCriteriaCreateSerializer, ScoringRuleSerializer,
    ScoreSheetSerializer, ScoreSheetUpdateSerializer, ScoreSheetCreateSerializer,
    ScoreItemSerializer, ScoreItemUpdateSerializer,
    ScoreDistributionSerializer, ScoreStatisticsSerializer,
    ScoreAppealSerializer, ScoreAppealCreateSerializer, ScoreAppealHandleSerializer
)


class ScoringCriteriaViewSet(viewsets.ModelViewSet):
    """评分标准视图集"""
    queryset = ScoringCriteria.objects.all()
    permission_classes = [IsAuthenticated, IsTeacherOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['created_by']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ScoringCriteriaCreateSerializer
        return ScoringCriteriaSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ScoringRuleViewSet(viewsets.ModelViewSet):
    """评分规则视图集"""
    queryset = ScoringRule.objects.all()
    serializer_class = ScoringRuleSerializer
    permission_classes = [IsAuthenticated, IsTeacherOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['criteria', 'question_type', 'auto_score']
    ordering_fields = ['criteria', 'question_type']
    ordering = ['criteria', 'question_type']


class ScoreSheetViewSet(viewsets.ModelViewSet):
    """评分表视图集"""
    queryset = ScoreSheet.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['exam', 'exam_record', 'status', 'marker', 'reviewer', 'is_passed']
    search_fields = ['exam__name', 'exam_record__student__username', 'comments']
    ordering_fields = ['created_at', 'total_score', 'marked_at', 'reviewed_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        
        # 学生只能查看自己的评分表
        if not user.is_staff and not user.is_teacher:
            queryset = queryset.filter(exam_record__student=user)
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ScoreSheetCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ScoreSheetUpdateSerializer
        return ScoreSheetSerializer
    
    @action(detail=True, methods=['post'])
    def auto_score(self, request, pk=None):
        """自动评分"""
        score_sheet = self.get_object()
        
        # 检查权限
        if not request.user.is_staff and not request.user.is_teacher:
            return Response({"detail": "没有权限执行此操作"}, status=status.HTTP_403_FORBIDDEN)
        
        # 检查评分表状态
        if score_sheet.status not in ['pending', 'in_progress']:
            return Response({"detail": "只能对待评分或评分中状态的评分表执行自动评分"}, status=status.HTTP_400_BAD_REQUEST)
        
        # 执行自动评分
        serializer = ScoreSheetCreateSerializer()
        serializer.auto_score(score_sheet)
        
        # 返回更新后的评分表
        return Response(ScoreSheetSerializer(score_sheet).data)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """完成评分"""
        score_sheet = self.get_object()
        
        # 检查权限
        if not request.user.is_staff and not request.user.is_teacher:
            return Response({"detail": "没有权限执行此操作"}, status=status.HTTP_403_FORBIDDEN)
        
        # 检查评分表状态
        if score_sheet.status not in ['pending', 'in_progress']:
            return Response({"detail": "只能完成待评分或评分中状态的评分表"}, status=status.HTTP_400_BAD_REQUEST)
        
        # 检查是否所有题目都已评分
        unscored_items = score_sheet.score_items.filter(score__isnull=True).count()
        if unscored_items > 0:
            return Response({"detail": f"还有 {unscored_items} 个评分项未完成评分"}, status=status.HTTP_400_BAD_REQUEST)
        
        # 更新评分表状态
        score_sheet.status = 'completed'
        score_sheet.marker = request.user
        score_sheet.marked_at = timezone.now()
        score_sheet.save()
        
        # 计算总分
        score_sheet.calculate_total_score()
        
        # 更新考试统计数据
        if hasattr(score_sheet.exam, 'score_statistics'):
            score_sheet.exam.score_statistics.update_statistics()
        else:
            ScoreStatistics.objects.create(exam=score_sheet.exam).update_statistics()
        
        # 返回更新后的评分表
        return Response(ScoreSheetSerializer(score_sheet).data)
    
    @action(detail=True, methods=['post'])
    def review(self, request, pk=None):
        """复核评分"""
        score_sheet = self.get_object()
        
        # 检查权限
        if not request.user.is_staff and not request.user.is_teacher:
            return Response({"detail": "没有权限执行此操作"}, status=status.HTTP_403_FORBIDDEN)
        
        # 检查评分表状态
        if score_sheet.status != 'completed':
            return Response({"detail": "只能复核已完成状态的评分表"}, status=status.HTTP_400_BAD_REQUEST)
        
        # 更新评分表状态
        score_sheet.status = 'reviewed'
        score_sheet.reviewer = request.user
        score_sheet.reviewed_at = timezone.now()
        score_sheet.save()
        
        # 返回更新后的评分表
        return Response(ScoreSheetSerializer(score_sheet).data)
    
    @action(detail=False, methods=['post'])
    def batch_create(self, request):
        """批量创建评分表"""
        # 检查权限
        if not request.user.is_staff and not request.user.is_teacher:
            return Response({"detail": "没有权限执行此操作"}, status=status.HTTP_403_FORBIDDEN)
        
        # 获取参数
        exam_id = request.data.get('exam')
        criteria_id = request.data.get('criteria')
        passing_score = request.data.get('passing_score')
        auto_score = request.data.get('auto_score', True)
        
        # 验证参数
        if not exam_id or not criteria_id:
            return Response({"detail": "缺少必要参数"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            exam = Exam.objects.get(pk=exam_id)
            criteria = ScoringCriteria.objects.get(pk=criteria_id)
        except (Exam.DoesNotExist, ScoringCriteria.DoesNotExist):
            return Response({"detail": "考试或评分标准不存在"}, status=status.HTTP_404_NOT_FOUND)
        
        # 获取所有已提交但未创建评分表的考试记录
        exam_records = ExamRecord.objects.filter(
            exam=exam,
            status='submitted'
        ).exclude(
            id__in=ScoreSheet.objects.filter(exam=exam).values_list('exam_record_id', flat=True)
        )
        
        # 创建评分表
        created_count = 0
        for record in exam_records:
            serializer = ScoreSheetCreateSerializer(data={
                'exam': exam.id,
                'exam_record': record.id,
                'criteria': criteria.id,
                'passing_score': passing_score
            })
            
            if serializer.is_valid():
                score_sheet = serializer.save()
                created_count += 1
                
                # 自动评分
                if auto_score:
                    serializer.auto_score(score_sheet)
        
        # 更新考试统计数据
        if created_count > 0:
            if hasattr(exam, 'score_statistics'):
                exam.score_statistics.update_statistics()
            else:
                ScoreStatistics.objects.create(exam=exam).update_statistics()
        
        return Response({"detail": f"成功创建 {created_count} 个评分表"}, status=status.HTTP_201_CREATED)


class ScoreItemViewSet(viewsets.ModelViewSet):
    """评分项视图集"""
    queryset = ScoreItem.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['score_sheet', 'question', 'auto_scored']
    ordering_fields = ['question__order', 'marked_at']
    ordering = ['question__order']
    
    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        
        # 学生只能查看自己的评分项
        if not user.is_staff and not user.is_teacher:
            queryset = queryset.filter(score_sheet__exam_record__student=user)
        
        return queryset
    
    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return ScoreItemUpdateSerializer
        return ScoreItemSerializer
    
    def update(self, request, *args, **kwargs):
        # 检查权限
        if not request.user.is_staff and not request.user.is_teacher:
            return Response({"detail": "没有权限执行此操作"}, status=status.HTTP_403_FORBIDDEN)
        
        return super().update(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    def auto_score(self, request, pk=None):
        """自动评分单个评分项"""
        score_item = self.get_object()
        
        # 检查权限
        if not request.user.is_staff and not request.user.is_teacher:
            return Response({"detail": "没有权限执行此操作"}, status=status.HTTP_403_FORBIDDEN)
        
        # 检查评分表状态
        if score_item.score_sheet.status not in ['pending', 'in_progress']:
            return Response({"detail": "只能对待评分或评分中状态的评分表执行自动评分"}, status=status.HTTP_400_BAD_REQUEST)
        
        # 获取评分标准
        criteria = score_item.score_sheet.criteria
        if not criteria:
            return Response({"detail": "评分表未设置评分标准"}, status=status.HTTP_400_BAD_REQUEST)
        
        # 获取题目类型
        question_type = score_item.question.question.question_type.name
        
        # 获取评分规则
        try:
            rule = criteria.rules.get(question_type=question_type)
        except ScoringRule.DoesNotExist:
            return Response({"detail": f"评分标准中未找到 {question_type} 的评分规则"}, status=status.HTTP_400_BAD_REQUEST)
        
        # 只处理允许自动评分的规则
        if not rule.auto_score:
            return Response({"detail": f"{question_type} 不允许自动评分"}, status=status.HTTP_400_BAD_REQUEST)
        
        # 获取答案
        answer = score_item.answer
        
        # 根据题目类型进行自动评分
        if question_type in ['单选题', '判断题']:
            # 单选题和判断题，答案完全正确得满分，否则得0分
            correct_option = score_item.question.question.correct_option
            if answer.answer_content == correct_option:
                score_item.score = rule.full_score
            else:
                score_item.score = 0
            
        elif question_type == '多选题':
            # 多选题，根据规则决定是否允许部分得分
            correct_options = set(score_item.question.question.correct_options.split(','))
            selected_options = set(answer.answer_content.split(','))
            
            if correct_options == selected_options:
                # 完全正确
                score_item.score = rule.full_score
            elif rule.partial_score_allowed:
                # 允许部分得分
                correct_count = len(correct_options.intersection(selected_options))
                wrong_count = len(selected_options - correct_options)
                
                # 计算得分：正确选项得分 - 错误选项扣分
                score = correct_count * rule.score_per_point
                if wrong_count > 0:
                    score = max(0, score - wrong_count * rule.score_per_point)
                
                score_item.score = min(score, rule.full_score)
            else:
                # 不允许部分得分
                score_item.score = 0
        
        # 填空题可以部分自动评分，但通常需要人工复核
        elif question_type == '填空题' and rule.partial_score_allowed:
            correct_answers = score_item.question.question.correct_answer.split('|')
            user_answers = answer.answer_content.split('|')
            
            # 计算正确的空数
            correct_count = 0
            for i, (correct, user) in enumerate(zip(correct_answers, user_answers)):
                if correct.strip() == user.strip():
                    correct_count += 1
            
            # 计算得分
            if len(correct_answers) > 0:
                score_item.score = (correct_count / len(correct_answers)) * rule.full_score
            else:
                score_item.score = 0
        
        # 更新评分项
        if score_item.score is not None:
            score_item.auto_scored = True
            score_item.marked_at = timezone.now()
            score_item.save()
            
            # 返回更新后的评分项
            return Response(ScoreItemSerializer(score_item).data)
        else:
            return Response({"detail": f"{question_type} 无法自动评分"}, status=status.HTTP_400_BAD_REQUEST)


class ScoreStatisticsViewSet(viewsets.ReadOnlyModelViewSet):
    """分数统计视图集"""
    queryset = ScoreStatistics.objects.all()
    serializer_class = ScoreStatisticsSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['exam']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-updated_at']
    
    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        
        # 学生只能查看自己参加的考试的统计数据
        if not user.is_staff and not user.is_teacher:
            student_exam_ids = ExamRecord.objects.filter(student=user).values_list('exam_id', flat=True)
            queryset = queryset.filter(exam_id__in=student_exam_ids)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def update_statistics(self, request, pk=None):
        """更新统计数据"""
        statistics = self.get_object()
        
        # 检查权限
        if not request.user.is_staff and not request.user.is_teacher:
            return Response({"detail": "没有权限执行此操作"}, status=status.HTTP_403_FORBIDDEN)
        
        # 更新统计数据
        statistics.update_statistics()
        
        # 返回更新后的统计数据
        return Response(ScoreStatisticsSerializer(statistics).data)
    
    @action(detail=False, methods=['post'])
    def create_for_exam(self, request):
        """为考试创建统计数据"""
        # 检查权限
        if not request.user.is_staff and not request.user.is_teacher:
            return Response({"detail": "没有权限执行此操作"}, status=status.HTTP_403_FORBIDDEN)
        
        # 获取参数
        exam_id = request.data.get('exam')
        
        # 验证参数
        if not exam_id:
            return Response({"detail": "缺少必要参数"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            exam = Exam.objects.get(pk=exam_id)
        except Exam.DoesNotExist:
            return Response({"detail": "考试不存在"}, status=status.HTTP_404_NOT_FOUND)
        
        # 创建或更新统计数据
        statistics, created = ScoreStatistics.objects.get_or_create(exam=exam)
        statistics.update_statistics()
        
        # 返回统计数据
        return Response(ScoreStatisticsSerializer(statistics).data)


class ScoreAppealViewSet(viewsets.ModelViewSet):
    """分数申诉视图集"""
    queryset = ScoreAppeal.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['score_item__score_sheet__exam', 'student', 'status', 'handler']
    search_fields = ['reason', 'response']
    ordering_fields = ['created_at', 'handled_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        
        # 学生只能查看自己的申诉
        if not user.is_staff and not user.is_teacher:
            queryset = queryset.filter(student=user)
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ScoreAppealCreateSerializer
        elif self.action in ['update', 'partial_update', 'handle']:
            return ScoreAppealHandleSerializer
        return ScoreAppealSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(ScoreAppealSerializer(serializer.instance).data, status=status.HTTP_201_CREATED, headers=headers)
    
    def update(self, request, *args, **kwargs):
        # 检查权限
        if not request.user.is_staff and not request.user.is_teacher:
            return Response({"detail": "没有权限执行此操作"}, status=status.HTTP_403_FORBIDDEN)
        
        return super().update(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    def handle(self, request, pk=None):
        """处理申诉"""
        appeal = self.get_object()
        
        # 检查权限
        if not request.user.is_staff and not request.user.is_teacher:
            return Response({"detail": "没有权限执行此操作"}, status=status.HTTP_403_FORBIDDEN)
        
        # 检查申诉状态
        if appeal.status not in ['pending', 'processing']:
            return Response({"detail": "只能处理待处理或处理中状态的申诉"}, status=status.HTTP_400_BAD_REQUEST)
        
        # 更新申诉
        serializer = ScoreAppealHandleSerializer(appeal, data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(handler=request.user, handled_at=timezone.now())
        
        # 返回更新后的申诉
        return Response(ScoreAppealSerializer(appeal).data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """取消申诉"""
        appeal = self.get_object()
        
        # 检查是否是申诉的创建者
        if appeal.student != request.user:
            return Response({"detail": "只有申诉创建者可以取消申诉"}, status=status.HTTP_403_FORBIDDEN)
        
        # 检查申诉状态
        if appeal.status not in ['pending', 'processing']:
            return Response({"detail": "只能取消待处理或处理中状态的申诉"}, status=status.HTTP_400_BAD_REQUEST)
        
        # 更新申诉状态
        appeal.status = 'cancelled'
        appeal.save()
        
        # 返回更新后的申诉
        return Response(ScoreAppealSerializer(appeal).data)
