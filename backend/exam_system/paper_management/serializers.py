from rest_framework import serializers
from .models import PaperTemplate, PaperSection, SectionRule, Paper, PaperQuestion, PaperGeneration
from exam_system.question_bank.serializers import QuestionSerializer, QuestionTypeSerializer, DifficultyLevelSerializer
from exam_system.question_bank.models import QuestionBank, QuestionType, DifficultyLevel
from exam_system.user_management.serializers import UserSerializer


class SectionRuleSerializer(serializers.ModelSerializer):
    question_bank_name = serializers.ReadOnlyField(source='question_bank.name')
    difficulty_name = serializers.ReadOnlyField(source='difficulty.name', default=None)
    
    class Meta:
        model = SectionRule
        fields = ['id', 'rule_type', 'question_bank', 'question_bank_name', 'question_count', 
                  'difficulty', 'difficulty_name', 'knowledge_points']


class PaperSectionSerializer(serializers.ModelSerializer):
    question_type_name = serializers.ReadOnlyField(source='question_type.name')
    rules = SectionRuleSerializer(many=True, read_only=True)
    total_score = serializers.ReadOnlyField()
    
    class Meta:
        model = PaperSection
        fields = ['id', 'name', 'description', 'question_type', 'question_type_name', 
                  'question_count', 'score_per_question', 'order', 'total_score', 'rules']


class PaperSectionCreateSerializer(serializers.ModelSerializer):
    rules = SectionRuleSerializer(many=True, required=False)
    
    class Meta:
        model = PaperSection
        fields = ['id', 'name', 'description', 'question_type', 'question_count', 
                  'score_per_question', 'order', 'rules']
    
    def create(self, validated_data):
        rules_data = validated_data.pop('rules', [])
        section = PaperSection.objects.create(**validated_data)
        
        for rule_data in rules_data:
            SectionRule.objects.create(section=section, **rule_data)
        
        return section


class PaperTemplateSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    sections = PaperSectionSerializer(many=True, read_only=True)
    
    class Meta:
        model = PaperTemplate
        fields = ['id', 'name', 'description', 'subject', 'total_score', 'passing_score', 
                  'duration', 'created_by', 'is_active', 'created_at', 'updated_at', 'sections']
        read_only_fields = ['created_at', 'updated_at']


class PaperTemplateCreateSerializer(serializers.ModelSerializer):
    sections = PaperSectionCreateSerializer(many=True, required=False)
    
    class Meta:
        model = PaperTemplate
        fields = ['id', 'name', 'description', 'subject', 'total_score', 'passing_score', 
                  'duration', 'is_active', 'sections']
    
    def create(self, validated_data):
        sections_data = validated_data.pop('sections', [])
        template = PaperTemplate.objects.create(
            created_by=self.context['request'].user,
            **validated_data
        )
        
        for section_data in sections_data:
            rules_data = section_data.pop('rules', [])
            section = PaperSection.objects.create(template=template, **section_data)
            
            for rule_data in rules_data:
                SectionRule.objects.create(section=section, **rule_data)
        
        return template


class PaperQuestionSerializer(serializers.ModelSerializer):
    question_detail = QuestionSerializer(source='question', read_only=True)
    
    class Meta:
        model = PaperQuestion
        fields = ['id', 'question', 'question_detail', 'section_name', 'order', 'score']


class PaperSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    template_name = serializers.ReadOnlyField(source='template.name', default=None)
    question_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Paper
        fields = ['id', 'title', 'description', 'subject', 'template', 'template_name', 
                  'total_score', 'passing_score', 'duration', 'status', 'created_by', 
                  'created_at', 'updated_at', 'published_at', 'question_count']
        read_only_fields = ['created_at', 'updated_at', 'published_at']
    
    def get_question_count(self, obj):
        return obj.questions.count()


class PaperDetailSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    template_name = serializers.ReadOnlyField(source='template.name', default=None)
    questions = PaperQuestionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Paper
        fields = ['id', 'title', 'description', 'subject', 'template', 'template_name', 
                  'total_score', 'passing_score', 'duration', 'status', 'created_by', 
                  'created_at', 'updated_at', 'published_at', 'questions']
        read_only_fields = ['created_at', 'updated_at', 'published_at']


class PaperCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Paper
        fields = ['id', 'title', 'description', 'subject', 'template', 
                  'total_score', 'passing_score', 'duration']
    
    def create(self, validated_data):
        return Paper.objects.create(
            created_by=self.context['request'].user,
            **validated_data
        )


class PaperGenerationSerializer(serializers.ModelSerializer):
    paper_title = serializers.ReadOnlyField(source='paper.title')
    template_name = serializers.ReadOnlyField(source='template.name', default=None)
    created_by_name = serializers.ReadOnlyField(source='created_by.username')
    
    class Meta:
        model = PaperGeneration
        fields = ['id', 'paper', 'paper_title', 'template', 'template_name', 'status', 
                  'created_by', 'created_by_name', 'created_at', 'completed_at', 'error_message']
        read_only_fields = ['created_at', 'completed_at', 'error_message']


class PaperGenerationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaperGeneration
        fields = ['id', 'paper', 'template']
    
    def validate(self, data):
        # 检查试卷是否已经有题目
        paper = data.get('paper')
        if paper and paper.questions.exists():
            raise serializers.ValidationError("试卷已经包含题目，不能重新生成")
        
        # 检查是否有正在处理的生成任务
        if paper and PaperGeneration.objects.filter(
            paper=paper, 
            status__in=['pending', 'processing']
        ).exists():
            raise serializers.ValidationError("已有正在处理的生成任务")
        
        return data
    
    def create(self, validated_data):
        return PaperGeneration.objects.create(
            created_by=self.context['request'].user,
            **validated_data
        )
