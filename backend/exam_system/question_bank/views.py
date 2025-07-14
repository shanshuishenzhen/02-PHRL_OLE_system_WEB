from rest_framework import viewsets, status, filters, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from .models import (
    QuestionBank, QuestionType, DifficultyLevel, KnowledgePoint,
    Question, QuestionOption, QuestionImage, QuestionImport
)
from .serializers import (
    QuestionBankSerializer, QuestionTypeSerializer, DifficultyLevelSerializer,
    KnowledgePointSerializer, QuestionSerializer, QuestionDetailSerializer,
    QuestionImportSerializer
)
from user_management.permissions import IsAdminOrTeacherUser


class QuestionBankViewSet(viewsets.ModelViewSet):
    """题库视图集"""
    queryset = QuestionBank.objects.all()
    serializer_class = QuestionBankSerializer
    permission_classes = [IsAdminOrTeacherUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['subject', 'is_active']
    search_fields = ['name', 'subject', 'description']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    @action(detail=True, methods=['get'])
    def questions(self, request, pk=None):
        """获取题库中的所有题目"""
        question_bank = self.get_object()
        questions = question_bank.questions.all()
        
        # 过滤
        question_type = request.query_params.get('question_type')
        difficulty = request.query_params.get('difficulty')
        knowledge_point = request.query_params.get('knowledge_point')
        is_active = request.query_params.get('is_active')
        
        if question_type:
            questions = questions.filter(question_type_id=question_type)
        if difficulty:
            questions = questions.filter(difficulty_id=difficulty)
        if knowledge_point:
            questions = questions.filter(knowledge_points__id=knowledge_point)
        if is_active is not None:
            is_active = is_active.lower() == 'true'
            questions = questions.filter(is_active=is_active)
        
        # 搜索
        search = request.query_params.get('search')
        if search:
            questions = questions.filter(
                Q(content__icontains=search) |
                Q(answer__icontains=search) |
                Q(analysis__icontains=search)
            )
        
        # 分页
        page = self.paginate_queryset(questions)
        if page is not None:
            serializer = QuestionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = QuestionSerializer(questions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """获取题库统计信息"""
        question_bank = self.get_object()
        questions = question_bank.questions.all()
        
        # 按题型统计
        question_type_stats = {}
        for question_type in QuestionType.objects.all():
            count = questions.filter(question_type=question_type).count()
            question_type_stats[question_type.get_name_display()] = count
        
        # 按难度统计
        difficulty_stats = {}
        for difficulty in DifficultyLevel.objects.all():
            count = questions.filter(difficulty=difficulty).count()
            difficulty_stats[difficulty.get_level_display()] = count
        
        # 按知识点统计
        knowledge_point_stats = {}
        for kp in KnowledgePoint.objects.filter(questions__question_bank=question_bank).distinct():
            count = questions.filter(knowledge_points=kp).count()
            knowledge_point_stats[kp.name] = count
        
        return Response({
            'total_questions': questions.count(),
            'active_questions': questions.filter(is_active=True).count(),
            'question_type_stats': question_type_stats,
            'difficulty_stats': difficulty_stats,
            'knowledge_point_stats': knowledge_point_stats
        })


class QuestionTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """题目类型视图集"""
    queryset = QuestionType.objects.all()
    serializer_class = QuestionTypeSerializer
    permission_classes = [permissions.IsAuthenticated]


class DifficultyLevelViewSet(viewsets.ReadOnlyModelViewSet):
    """难度级别视图集"""
    queryset = DifficultyLevel.objects.all().order_by('level')
    serializer_class = DifficultyLevelSerializer
    permission_classes = [permissions.IsAuthenticated]


class KnowledgePointViewSet(viewsets.ModelViewSet):
    """知识点视图集"""
    queryset = KnowledgePoint.objects.all()
    serializer_class = KnowledgePointSerializer
    permission_classes = [IsAdminOrTeacherUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['subject', 'parent']
    search_fields = ['name', 'description']
    
    @action(detail=False, methods=['get'])
    def tree(self, request):
        """获取知识点树结构"""
        subject = request.query_params.get('subject')
        if not subject:
            return Response({'detail': '必须指定科目参数'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 获取指定科目的所有根知识点
        root_points = KnowledgePoint.objects.filter(subject=subject, parent=None)
        
        def build_tree(node):
            children = KnowledgePoint.objects.filter(parent=node)
            return {
                'id': node.id,
                'name': node.name,
                'description': node.description,
                'children': [build_tree(child) for child in children]
            }
        
        tree = [build_tree(root) for root in root_points]
        return Response(tree)


class QuestionViewSet(viewsets.ModelViewSet):
    """题目视图集"""
    queryset = Question.objects.all()
    permission_classes = [IsAdminOrTeacherUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['question_bank', 'question_type', 'difficulty', 'is_active']
    search_fields = ['content', 'answer', 'analysis']
    ordering_fields = ['created_at', 'updated_at', 'score']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update', 'retrieve']:
            return QuestionDetailSerializer
        return QuestionSerializer
    
    @action(detail=False, methods=['get'])
    def random(self, request):
        """随机获取题目"""
        question_bank_id = request.query_params.get('question_bank')
        question_type_id = request.query_params.get('question_type')
        difficulty_id = request.query_params.get('difficulty')
        count = request.query_params.get('count', 10)
        
        try:
            count = int(count)
            if count <= 0 or count > 100:
                count = 10
        except ValueError:
            count = 10
        
        # 构建过滤条件
        filter_kwargs = {'is_active': True}
        if question_bank_id:
            filter_kwargs['question_bank_id'] = question_bank_id
        if question_type_id:
            filter_kwargs['question_type_id'] = question_type_id
        if difficulty_id:
            filter_kwargs['difficulty_id'] = difficulty_id
        
        # 随机获取题目
        questions = Question.objects.filter(**filter_kwargs).order_by('?')[:count]
        serializer = QuestionSerializer(questions, many=True)
        return Response(serializer.data)


class QuestionImportViewSet(viewsets.ModelViewSet):
    """题目导入视图集"""
    queryset = QuestionImport.objects.all()
    serializer_class = QuestionImportSerializer
    permission_classes = [IsAdminOrTeacherUser]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['question_bank', 'status']
    ordering_fields = ['created_at', 'completed_at']
    ordering = ['-created_at']
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # 在实际项目中，这里应该启动一个异步任务来处理导入
        # 为了演示，这里直接更新状态为处理中
        import_record = serializer.instance
        import_record.status = 'processing'
        import_record.save(update_fields=['status'])
        
        # TODO: 启动异步任务处理导入
        # 这里应该调用Celery任务或其他异步处理机制
        # 为了演示，这里直接更新为完成状态
        import_record.status = 'completed'
        import_record.completed_at = timezone.now()
        import_record.total_count = 0
        import_record.success_count = 0
        import_record.save(update_fields=['status', 'completed_at', 'total_count', 'success_count'])
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
