from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Q

from .models import (
    AnalysisTask, ExamAnalysis, StudentAnalysis, QuestionAnalysis,
    KnowledgePointAnalysis, ClassAnalysis, DepartmentAnalysis,
    AnalysisReport, AnalysisTemplate
)
from .serializers import (
    AnalysisTaskSerializer, AnalysisTaskCreateSerializer, AnalysisTaskUpdateSerializer,
    ExamAnalysisSerializer, ExamAnalysisCreateSerializer,
    StudentAnalysisSerializer, StudentAnalysisCreateSerializer,
    QuestionAnalysisSerializer, QuestionAnalysisCreateSerializer,
    KnowledgePointAnalysisSerializer, KnowledgePointAnalysisCreateSerializer,
    ClassAnalysisSerializer, ClassAnalysisCreateSerializer,
    DepartmentAnalysisSerializer, DepartmentAnalysisCreateSerializer,
    AnalysisReportSerializer, AnalysisReportCreateSerializer,
    AnalysisTemplateSerializer, AnalysisTemplateCreateSerializer
)
from exam_system.permissions import IsAdminUser, IsTeacherUser, IsStudentUser


class AnalysisTaskViewSet(viewsets.ModelViewSet):
    """分析任务视图集"""
    queryset = AnalysisTask.objects.all()
    serializer_class = AnalysisTaskSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['task_type', 'status', 'created_by']
    search_fields = ['name']
    ordering_fields = ['created_at', 'updated_at', 'completed_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.role == 'admin':
            return AnalysisTask.objects.all()
        elif user.role == 'teacher':
            return AnalysisTask.objects.filter(created_by=user)
        else:
            # 学生只能查看自己的分析任务或公开的分析报告对应的任务
            return AnalysisTask.objects.filter(
                Q(created_by=user) | 
                Q(report__is_public=True)
            ).distinct()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return AnalysisTaskCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return AnalysisTaskUpdateSerializer
        return AnalysisTaskSerializer
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """取消分析任务"""
        task = self.get_object()
        if task.status not in ['pending', 'processing']:
            return Response({"detail": "只能取消待处理或处理中的任务"}, status=status.HTTP_400_BAD_REQUEST)
        
        task.status = 'failed'
        task.error_message = "用户取消"
        task.save()
        
        return Response({"detail": "任务已取消"}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def restart(self, request, pk=None):
        """重新启动分析任务"""
        task = self.get_object()
        if task.status not in ['failed']:
            return Response({"detail": "只能重启失败的任务"}, status=status.HTTP_400_BAD_REQUEST)
        
        task.status = 'pending'
        task.error_message = None
        task.save()
        
        return Response({"detail": "任务已重新启动"}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'])
    def result(self, request, pk=None):
        """获取分析任务结果"""
        task = self.get_object()
        if task.status != 'completed':
            return Response({"detail": "任务尚未完成"}, status=status.HTTP_400_BAD_REQUEST)
        
        # 根据任务类型返回不同的分析结果
        if task.task_type == 'exam' and hasattr(task, 'exam_analysis'):
            serializer = ExamAnalysisSerializer(task.exam_analysis)
            return Response(serializer.data)
        elif task.task_type == 'student' and hasattr(task, 'student_analysis'):
            serializer = StudentAnalysisSerializer(task.student_analysis)
            return Response(serializer.data)
        elif task.task_type == 'question' and hasattr(task, 'question_analysis'):
            serializer = QuestionAnalysisSerializer(task.question_analysis)
            return Response(serializer.data)
        elif task.task_type == 'knowledge' and hasattr(task, 'knowledge_point_analysis'):
            serializer = KnowledgePointAnalysisSerializer(task.knowledge_point_analysis)
            return Response(serializer.data)
        elif task.task_type == 'class' and hasattr(task, 'class_analysis'):
            serializer = ClassAnalysisSerializer(task.class_analysis)
            return Response(serializer.data)
        elif task.task_type == 'department' and hasattr(task, 'department_analysis'):
            serializer = DepartmentAnalysisSerializer(task.department_analysis)
            return Response(serializer.data)
        else:
            return Response({"detail": "找不到分析结果"}, status=status.HTTP_404_NOT_FOUND)


class ExamAnalysisViewSet(viewsets.ModelViewSet):
    """考试分析视图集"""
    queryset = ExamAnalysis.objects.all()
    serializer_class = ExamAnalysisSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['exam']
    search_fields = ['exam__name']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.role == 'admin':
            return ExamAnalysis.objects.all()
        elif user.role == 'teacher':
            # 教师可以查看自己创建的考试分析或自己参与的考试的分析
            return ExamAnalysis.objects.filter(
                Q(task__created_by=user) | 
                Q(exam__created_by=user) | 
                Q(exam__invigilators=user)
            ).distinct()
        else:
            # 学生只能查看自己参加的考试且有公开报告的分析
            return ExamAnalysis.objects.filter(
                Q(exam__registrations__student=user, task__report__is_public=True)
            ).distinct()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ExamAnalysisCreateSerializer
        return ExamAnalysisSerializer
    
    @action(detail=True, methods=['get'])
    def question_analysis(self, request, pk=None):
        """获取考试题目分析"""
        exam_analysis = self.get_object()
        return Response(exam_analysis.question_analysis)
    
    @action(detail=True, methods=['get'])
    def knowledge_point_analysis(self, request, pk=None):
        """获取考试知识点分析"""
        exam_analysis = self.get_object()
        return Response(exam_analysis.knowledge_point_analysis)
    
    @action(detail=True, methods=['get'])
    def class_comparison(self, request, pk=None):
        """获取考试班级对比"""
        exam_analysis = self.get_object()
        return Response(exam_analysis.class_comparison)
    
    @action(detail=True, methods=['get'])
    def department_comparison(self, request, pk=None):
        """获取考试院系对比"""
        exam_analysis = self.get_object()
        return Response(exam_analysis.department_comparison)
    
    @action(detail=True, methods=['get'])
    def time_spent_analysis(self, request, pk=None):
        """获取考试答题时间分析"""
        exam_analysis = self.get_object()
        return Response(exam_analysis.time_spent_analysis)


class StudentAnalysisViewSet(viewsets.ModelViewSet):
    """学生分析视图集"""
    queryset = StudentAnalysis.objects.all()
    serializer_class = StudentAnalysisSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['student']
    search_fields = ['student__username', 'student__name']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.role == 'admin':
            return StudentAnalysis.objects.all()
        elif user.role == 'teacher':
            # 教师可以查看自己创建的学生分析或自己班级学生的分析
            return StudentAnalysis.objects.filter(
                Q(task__created_by=user) | 
                Q(student__classes__teacher=user)
            ).distinct()
        else:
            # 学生只能查看自己的分析
            return StudentAnalysis.objects.filter(student=user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return StudentAnalysisCreateSerializer
        return StudentAnalysisSerializer
    
    @action(detail=True, methods=['get'])
    def knowledge_point_mastery(self, request, pk=None):
        """获取学生知识点掌握情况"""
        student_analysis = self.get_object()
        return Response(student_analysis.knowledge_point_mastery)
    
    @action(detail=True, methods=['get'])
    def question_type_performance(self, request, pk=None):
        """获取学生题型表现"""
        student_analysis = self.get_object()
        return Response(student_analysis.question_type_performance)
    
    @action(detail=True, methods=['get'])
    def error_pattern_analysis(self, request, pk=None):
        """获取学生错误模式分析"""
        student_analysis = self.get_object()
        return Response(student_analysis.error_pattern_analysis)


class QuestionAnalysisViewSet(viewsets.ModelViewSet):
    """题目分析视图集"""
    queryset = QuestionAnalysis.objects.all()
    serializer_class = QuestionAnalysisSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['question', 'question__question_type']
    search_fields = ['question__content']
    ordering_fields = ['created_at', 'updated_at', 'correct_rate', 'difficulty_index']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.role == 'admin':
            return QuestionAnalysis.objects.all()
        elif user.role == 'teacher':
            # 教师可以查看自己创建的题目分析或自己创建的题目的分析
            return QuestionAnalysis.objects.filter(
                Q(task__created_by=user) | 
                Q(question__created_by=user)
            ).distinct()
        else:
            # 学生只能查看公开报告的题目分析
            return QuestionAnalysis.objects.filter(task__report__is_public=True)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return QuestionAnalysisCreateSerializer
        return QuestionAnalysisSerializer
    
    @action(detail=True, methods=['get'])
    def option_distribution(self, request, pk=None):
        """获取题目选项分布"""
        question_analysis = self.get_object()
        return Response(question_analysis.option_distribution)
    
    @action(detail=True, methods=['get'])
    def class_performance(self, request, pk=None):
        """获取题目班级表现"""
        question_analysis = self.get_object()
        return Response(question_analysis.class_performance)
    
    @action(detail=True, methods=['get'])
    def department_performance(self, request, pk=None):
        """获取题目院系表现"""
        question_analysis = self.get_object()
        return Response(question_analysis.department_performance)


class KnowledgePointAnalysisViewSet(viewsets.ModelViewSet):
    """知识点分析视图集"""
    queryset = KnowledgePointAnalysis.objects.all()
    serializer_class = KnowledgePointAnalysisSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['knowledge_point', 'knowledge_point__subject']
    search_fields = ['knowledge_point__name']
    ordering_fields = ['created_at', 'updated_at', 'correct_rate', 'difficulty_index']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.role == 'admin':
            return KnowledgePointAnalysis.objects.all()
        elif user.role == 'teacher':
            # 教师可以查看自己创建的知识点分析或自己创建的知识点的分析
            return KnowledgePointAnalysis.objects.filter(
                Q(task__created_by=user) | 
                Q(knowledge_point__created_by=user)
            ).distinct()
        else:
            # 学生只能查看公开报告的知识点分析
            return KnowledgePointAnalysis.objects.filter(task__report__is_public=True)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return KnowledgePointAnalysisCreateSerializer
        return KnowledgePointAnalysisSerializer
    
    @action(detail=True, methods=['get'])
    def mastery_distribution(self, request, pk=None):
        """获取知识点掌握程度分布"""
        knowledge_point_analysis = self.get_object()
        return Response(knowledge_point_analysis.mastery_distribution)
    
    @action(detail=True, methods=['get'])
    def class_performance(self, request, pk=None):
        """获取知识点班级表现"""
        knowledge_point_analysis = self.get_object()
        return Response(knowledge_point_analysis.class_performance)
    
    @action(detail=True, methods=['get'])
    def department_performance(self, request, pk=None):
        """获取知识点院系表现"""
        knowledge_point_analysis = self.get_object()
        return Response(knowledge_point_analysis.department_performance)
    
    @action(detail=True, methods=['get'])
    def related_knowledge_points(self, request, pk=None):
        """获取相关知识点表现"""
        knowledge_point_analysis = self.get_object()
        return Response(knowledge_point_analysis.related_knowledge_points)


class ClassAnalysisViewSet(viewsets.ModelViewSet):
    """班级分析视图集"""
    queryset = ClassAnalysis.objects.all()
    serializer_class = ClassAnalysisSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['class_obj', 'class_obj__department']
    search_fields = ['class_obj__name']
    ordering_fields = ['created_at', 'updated_at', 'average_score', 'average_pass_rate']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.role == 'admin':
            return ClassAnalysis.objects.all()
        elif user.role == 'teacher':
            # 教师可以查看自己创建的班级分析或自己负责的班级的分析
            return ClassAnalysis.objects.filter(
                Q(task__created_by=user) | 
                Q(class_obj__teacher=user)
            ).distinct()
        else:
            # 学生只能查看自己所在班级且有公开报告的分析
            return ClassAnalysis.objects.filter(
                Q(class_obj__students=user, task__report__is_public=True)
            ).distinct()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ClassAnalysisCreateSerializer
        return ClassAnalysisSerializer
    
    @action(detail=True, methods=['get'])
    def score_distribution(self, request, pk=None):
        """获取班级分数分布"""
        class_analysis = self.get_object()
        return Response(class_analysis.score_distribution)
    
    @action(detail=True, methods=['get'])
    def knowledge_point_mastery(self, request, pk=None):
        """获取班级知识点掌握情况"""
        class_analysis = self.get_object()
        return Response(class_analysis.knowledge_point_mastery)
    
    @action(detail=True, methods=['get'])
    def question_type_performance(self, request, pk=None):
        """获取班级题型表现"""
        class_analysis = self.get_object()
        return Response(class_analysis.question_type_performance)
    
    @action(detail=True, methods=['get'])
    def student_ranking(self, request, pk=None):
        """获取班级学生排名"""
        class_analysis = self.get_object()
        return Response(class_analysis.student_ranking)
    
    @action(detail=True, methods=['get'])
    def performance_trend(self, request, pk=None):
        """获取班级表现趋势"""
        class_analysis = self.get_object()
        return Response(class_analysis.performance_trend)
    
    @action(detail=True, methods=['get'])
    def comparison_with_other_classes(self, request, pk=None):
        """获取班级与其他班级对比"""
        class_analysis = self.get_object()
        return Response(class_analysis.comparison_with_other_classes)


class DepartmentAnalysisViewSet(viewsets.ModelViewSet):
    """院系分析视图集"""
    queryset = DepartmentAnalysis.objects.all()
    serializer_class = DepartmentAnalysisSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['department']
    search_fields = ['department__name']
    ordering_fields = ['created_at', 'updated_at', 'average_score', 'average_pass_rate']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.role == 'admin':
            return DepartmentAnalysis.objects.all()
        elif user.role == 'teacher':
            # 教师可以查看自己创建的院系分析或自己所在院系的分析
            return DepartmentAnalysis.objects.filter(
                Q(task__created_by=user) | 
                Q(department=user.department)
            ).distinct()
        else:
            # 学生只能查看自己所在院系且有公开报告的分析
            return DepartmentAnalysis.objects.filter(
                Q(department=user.department, task__report__is_public=True)
            ).distinct()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return DepartmentAnalysisCreateSerializer
        return DepartmentAnalysisSerializer
    
    @action(detail=True, methods=['get'])
    def score_distribution(self, request, pk=None):
        """获取院系分数分布"""
        department_analysis = self.get_object()
        return Response(department_analysis.score_distribution)
    
    @action(detail=True, methods=['get'])
    def knowledge_point_mastery(self, request, pk=None):
        """获取院系知识点掌握情况"""
        department_analysis = self.get_object()
        return Response(department_analysis.knowledge_point_mastery)
    
    @action(detail=True, methods=['get'])
    def question_type_performance(self, request, pk=None):
        """获取院系题型表现"""
        department_analysis = self.get_object()
        return Response(department_analysis.question_type_performance)
    
    @action(detail=True, methods=['get'])
    def class_ranking(self, request, pk=None):
        """获取院系班级排名"""
        department_analysis = self.get_object()
        return Response(department_analysis.class_ranking)
    
    @action(detail=True, methods=['get'])
    def student_ranking(self, request, pk=None):
        """获取院系学生排名"""
        department_analysis = self.get_object()
        return Response(department_analysis.student_ranking)
    
    @action(detail=True, methods=['get'])
    def performance_trend(self, request, pk=None):
        """获取院系表现趋势"""
        department_analysis = self.get_object()
        return Response(department_analysis.performance_trend)
    
    @action(detail=True, methods=['get'])
    def comparison_with_other_departments(self, request, pk=None):
        """获取院系与其他院系对比"""
        department_analysis = self.get_object()
        return Response(department_analysis.comparison_with_other_departments)


class AnalysisReportViewSet(viewsets.ModelViewSet):
    """分析报告视图集"""
    queryset = AnalysisReport.objects.all()
    serializer_class = AnalysisReportSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['task__task_type', 'is_public']
    search_fields = ['title', 'summary']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.role == 'admin':
            return AnalysisReport.objects.all()
        elif user.role == 'teacher':
            # 教师可以查看自己创建的报告或公开的报告
            return AnalysisReport.objects.filter(
                Q(task__created_by=user) | 
                Q(is_public=True)
            ).distinct()
        else:
            # 学生只能查看公开的报告
            return AnalysisReport.objects.filter(is_public=True)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return AnalysisReportCreateSerializer
        return AnalysisReportSerializer
    
    @action(detail=True, methods=['post'])
    def toggle_public(self, request, pk=None):
        """切换报告公开状态"""
        report = self.get_object()
        # 检查权限，只有报告创建者或管理员可以切换公开状态
        if request.user != report.task.created_by and not (request.user.is_superuser or request.user.role == 'admin'):
            return Response({"detail": "没有权限执行此操作"}, status=status.HTTP_403_FORBIDDEN)
        
        report.is_public = not report.is_public
        report.save()
        
        return Response({"detail": f"报告已{'公开' if report.is_public else '设为私有'}", "is_public": report.is_public}, status=status.HTTP_200_OK)


class AnalysisTemplateViewSet(viewsets.ModelViewSet):
    """分析模板视图集"""
    queryset = AnalysisTemplate.objects.all()
    serializer_class = AnalysisTemplateSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['task_type', 'is_system', 'created_by']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.role == 'admin':
            return AnalysisTemplate.objects.all()
        elif user.role == 'teacher':
            # 教师可以查看系统模板和自己创建的模板
            return AnalysisTemplate.objects.filter(
                Q(is_system=True) | 
                Q(created_by=user)
            ).distinct()
        else:
            # 学生只能查看系统模板
            return AnalysisTemplate.objects.filter(is_system=True)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return AnalysisTemplateCreateSerializer
        return AnalysisTemplateSerializer
    
    def destroy(self, request, *args, **kwargs):
        template = self.get_object()
        # 系统模板不能删除
        if template.is_system:
            return Response({"detail": "系统模板不能删除"}, status=status.HTTP_400_BAD_REQUEST)
        # 只有创建者或管理员可以删除模板
        if request.user != template.created_by and not (request.user.is_superuser or request.user.role == 'admin'):
            return Response({"detail": "没有权限执行此操作"}, status=status.HTTP_403_FORBIDDEN)
        
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    def use_template(self, request, pk=None):
        """使用模板创建分析任务"""
        template = self.get_object()
        
        # 获取请求参数
        name = request.data.get('name')
        parameters = request.data.get('parameters', {})
        
        if not name:
            return Response({"detail": "任务名称不能为空"}, status=status.HTTP_400_BAD_REQUEST)
        
        # 合并模板参数和请求参数
        merged_parameters = {**template.parameters, **parameters}
        
        # 创建分析任务
        task = AnalysisTask.objects.create(
            name=name,
            task_type=template.task_type,
            status='pending',
            created_by=request.user,
            parameters=merged_parameters
        )
        
        serializer = AnalysisTaskSerializer(task)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
