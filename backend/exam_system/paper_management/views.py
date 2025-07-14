from rest_framework import viewsets, status, filters, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from .models import PaperTemplate, PaperSection, SectionRule, Paper, PaperQuestion, PaperGeneration
from .serializers import (
    PaperTemplateSerializer, PaperTemplateCreateSerializer,
    PaperSectionSerializer, PaperSectionCreateSerializer,
    SectionRuleSerializer, PaperSerializer, PaperDetailSerializer,
    PaperCreateSerializer, PaperQuestionSerializer,
    PaperGenerationSerializer, PaperGenerationCreateSerializer
)
from exam_system.question_bank.models import Question
from user_management.permissions import IsAdminOrTeacherUser
import random


class PaperTemplateViewSet(viewsets.ModelViewSet):
    """试卷模板视图集"""
    queryset = PaperTemplate.objects.all()
    permission_classes = [IsAdminOrTeacherUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['subject', 'is_active']
    search_fields = ['name', 'description', 'subject']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return PaperTemplateCreateSerializer
        return PaperTemplateSerializer
    
    @action(detail=True, methods=['post'])
    def clone(self, request, pk=None):
        """克隆试卷模板"""
        template = self.get_object()
        
        with transaction.atomic():
            # 克隆模板
            new_template = PaperTemplate.objects.create(
                name=f"{template.name} - 副本",
                description=template.description,
                subject=template.subject,
                total_score=template.total_score,
                passing_score=template.passing_score,
                duration=template.duration,
                created_by=request.user,
                is_active=template.is_active
            )
            
            # 克隆试卷部分
            for section in template.sections.all():
                new_section = PaperSection.objects.create(
                    template=new_template,
                    name=section.name,
                    description=section.description,
                    question_type=section.question_type,
                    question_count=section.question_count,
                    score_per_question=section.score_per_question,
                    order=section.order
                )
                
                # 克隆抽题规则
                for rule in section.rules.all():
                    SectionRule.objects.create(
                        section=new_section,
                        rule_type=rule.rule_type,
                        question_bank=rule.question_bank,
                        question_count=rule.question_count,
                        difficulty=rule.difficulty,
                        knowledge_points=rule.knowledge_points
                    )
        
        serializer = self.get_serializer(new_template)
        return Response(serializer.data)


class PaperSectionViewSet(viewsets.ModelViewSet):
    """试卷部分视图集"""
    queryset = PaperSection.objects.all()
    permission_classes = [IsAdminOrTeacherUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['template']
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return PaperSectionCreateSerializer
        return PaperSectionSerializer


class SectionRuleViewSet(viewsets.ModelViewSet):
    """抽题规则视图集"""
    queryset = SectionRule.objects.all()
    serializer_class = SectionRuleSerializer
    permission_classes = [IsAdminOrTeacherUser]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['section']


class PaperViewSet(viewsets.ModelViewSet):
    """试卷视图集"""
    queryset = Paper.objects.all()
    permission_classes = [IsAdminOrTeacherUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['subject', 'status', 'template']
    search_fields = ['title', 'description', 'subject']
    ordering_fields = ['title', 'created_at', 'updated_at', 'published_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PaperCreateSerializer
        elif self.action == 'retrieve':
            return PaperDetailSerializer
        return PaperSerializer
    
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """发布试卷"""
        paper = self.get_object()
        
        if paper.status == 'published':
            return Response({'detail': '试卷已经是发布状态'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not paper.questions.exists():
            return Response({'detail': '试卷没有题目，不能发布'}, status=status.HTTP_400_BAD_REQUEST)
        
        paper.publish()
        serializer = self.get_serializer(paper)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """归档试卷"""
        paper = self.get_object()
        
        if paper.status == 'archived':
            return Response({'detail': '试卷已经是归档状态'}, status=status.HTTP_400_BAD_REQUEST)
        
        paper.archive()
        serializer = self.get_serializer(paper)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def clone(self, request, pk=None):
        """克隆试卷"""
        paper = self.get_object()
        
        with transaction.atomic():
            # 克隆试卷
            new_paper = Paper.objects.create(
                title=f"{paper.title} - 副本",
                description=paper.description,
                subject=paper.subject,
                template=paper.template,
                total_score=paper.total_score,
                passing_score=paper.passing_score,
                duration=paper.duration,
                status='draft',
                created_by=request.user
            )
            
            # 克隆试卷题目
            for paper_question in paper.questions.all():
                PaperQuestion.objects.create(
                    paper=new_paper,
                    question=paper_question.question,
                    section_name=paper_question.section_name,
                    order=paper_question.order,
                    score=paper_question.score
                )
        
        serializer = self.get_serializer(new_paper)
        return Response(serializer.data)


class PaperQuestionViewSet(viewsets.ModelViewSet):
    """试卷题目视图集"""
    queryset = PaperQuestion.objects.all()
    serializer_class = PaperQuestionSerializer
    permission_classes = [IsAdminOrTeacherUser]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['paper', 'section_name']
    ordering_fields = ['order']
    ordering = ['order']
    
    def create(self, request, *args, **kwargs):
        # 检查试卷状态
        paper_id = request.data.get('paper')
        if paper_id:
            try:
                paper = Paper.objects.get(id=paper_id)
                if paper.status != 'draft':
                    return Response(
                        {'detail': '只能为草稿状态的试卷添加题目'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except Paper.DoesNotExist:
                pass
        
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.paper.status != 'draft':
            return Response(
                {'detail': '只能修改草稿状态试卷的题目'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.paper.status != 'draft':
            return Response(
                {'detail': '只能删除草稿状态试卷的题目'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)


class PaperGenerationViewSet(viewsets.ModelViewSet):
    """试卷生成视图集"""
    queryset = PaperGeneration.objects.all()
    permission_classes = [IsAdminOrTeacherUser]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['paper', 'status']
    ordering_fields = ['created_at', 'completed_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PaperGenerationCreateSerializer
        return PaperGenerationSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # 获取生成记录
        generation = serializer.instance
        
        # 更新状态为处理中
        generation.status = 'processing'
        generation.save(update_fields=['status'])
        
        try:
            # 生成试卷题目
            self._generate_paper_questions(generation)
            
            # 更新状态为已完成
            generation.status = 'completed'
            generation.completed_at = timezone.now()
            generation.save(update_fields=['status', 'completed_at'])
        except Exception as e:
            # 更新状态为失败
            generation.status = 'failed'
            generation.error_message = str(e)
            generation.save(update_fields=['status', 'error_message'])
            raise
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def _generate_paper_questions(self, generation):
        """生成试卷题目"""
        paper = generation.paper
        template = generation.template
        
        # 清空现有题目
        paper.questions.all().delete()
        
        # 如果没有指定模板，则无法生成
        if not template:
            raise ValueError("未指定试卷模板，无法生成试卷")
        
        # 更新试卷基本信息
        paper.total_score = template.total_score
        paper.passing_score = template.passing_score
        paper.duration = template.duration
        paper.save(update_fields=['total_score', 'passing_score', 'duration'])
        
        # 按照模板生成试卷题目
        question_order = 1
        
        with transaction.atomic():
            for section in template.sections.all():
                # 获取该部分的所有抽题规则
                rules = section.rules.all()
                
                # 如果没有规则，则跳过
                if not rules.exists():
                    continue
                
                # 计算每个规则需要抽取的题目数量
                total_rule_questions = sum(rule.question_count for rule in rules)
                if total_rule_questions < section.question_count:
                    # 规则中的题目数量不足，按比例增加
                    ratio = section.question_count / total_rule_questions
                    for rule in rules:
                        rule.question_count = int(rule.question_count * ratio)
                elif total_rule_questions > section.question_count:
                    # 规则中的题目数量过多，按比例减少
                    ratio = section.question_count / total_rule_questions
                    for rule in rules:
                        rule.question_count = int(rule.question_count * ratio)
                
                # 确保总数正确
                actual_total = sum(rule.question_count for rule in rules)
                if actual_total < section.question_count:
                    # 如果有差异，增加第一个规则的数量
                    rules[0].question_count += (section.question_count - actual_total)
                
                # 根据规则抽取题目
                selected_questions = []
                for rule in rules:
                    questions = self._get_questions_by_rule(rule)
                    
                    # 如果抽取的题目不足，则记录错误
                    if len(questions) < rule.question_count:
                        raise ValueError(f"规则'{rule.get_rule_type_display()}'找不到足够的题目，需要{rule.question_count}题，只找到{len(questions)}题")
                    
                    # 随机选择指定数量的题目
                    selected = random.sample(list(questions), rule.question_count)
                    selected_questions.extend(selected)
                
                # 创建试卷题目
                for question in selected_questions:
                    PaperQuestion.objects.create(
                        paper=paper,
                        question=question,
                        section_name=section.name,
                        order=question_order,
                        score=section.score_per_question
                    )
                    question_order += 1
    
    def _get_questions_by_rule(self, rule):
        """根据规则获取题目"""
        # 基本过滤条件
        filter_kwargs = {
            'question_bank': rule.question_bank,
            'question_type': rule.section.question_type,
            'is_active': True
        }
        
        # 根据规则类型添加过滤条件
        if rule.rule_type == 'fixed':
            # 固定题目，直接返回题库中的题目
            return Question.objects.filter(**filter_kwargs)
        
        elif rule.rule_type == 'difficulty':
            # 按难度抽取
            if rule.difficulty:
                filter_kwargs['difficulty'] = rule.difficulty
            return Question.objects.filter(**filter_kwargs)
        
        elif rule.rule_type == 'knowledge':
            # 按知识点抽取
            if rule.knowledge_points:
                knowledge_point_ids = [int(kp.strip()) for kp in rule.knowledge_points.split(',') if kp.strip().isdigit()]
                if knowledge_point_ids:
                    return Question.objects.filter(**filter_kwargs).filter(knowledge_points__id__in=knowledge_point_ids).distinct()
            return Question.objects.filter(**filter_kwargs)
        
        else:  # 'random' or default
            # 随机抽取
            return Question.objects.filter(**filter_kwargs)
