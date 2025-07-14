from rest_framework import serializers
from .models import (
    QuestionBank, QuestionType, DifficultyLevel, KnowledgePoint,
    Question, QuestionOption, QuestionImage, QuestionImport
)


class QuestionBankSerializer(serializers.ModelSerializer):
    """题库序列化器"""
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    question_count = serializers.SerializerMethodField()
    
    class Meta:
        model = QuestionBank
        fields = ['id', 'name', 'subject', 'description', 'created_by', 'created_by_username',
                 'created_at', 'updated_at', 'is_active', 'question_count']
        read_only_fields = ['created_by', 'created_at', 'updated_at', 'question_count']
    
    def get_question_count(self, obj):
        return obj.questions.count()
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class QuestionTypeSerializer(serializers.ModelSerializer):
    """题目类型序列化器"""
    name_display = serializers.CharField(source='get_name_display', read_only=True)
    
    class Meta:
        model = QuestionType
        fields = ['id', 'name', 'name_display', 'description']


class DifficultyLevelSerializer(serializers.ModelSerializer):
    """难度级别序列化器"""
    level_display = serializers.CharField(source='get_level_display', read_only=True)
    
    class Meta:
        model = DifficultyLevel
        fields = ['id', 'level', 'level_display', 'description']


class KnowledgePointSerializer(serializers.ModelSerializer):
    """知识点序列化器"""
    parent_name = serializers.CharField(source='parent.name', read_only=True, allow_null=True)
    
    class Meta:
        model = KnowledgePoint
        fields = ['id', 'name', 'subject', 'parent', 'parent_name', 'description']


class QuestionOptionSerializer(serializers.ModelSerializer):
    """题目选项序列化器"""
    class Meta:
        model = QuestionOption
        fields = ['id', 'option_key', 'option_content', 'is_correct']


class QuestionImageSerializer(serializers.ModelSerializer):
    """题目图片序列化器"""
    class Meta:
        model = QuestionImage
        fields = ['id', 'image', 'description']


class QuestionSerializer(serializers.ModelSerializer):
    """题目序列化器"""
    question_type_name = serializers.CharField(source='question_type.get_name_display', read_only=True)
    difficulty_level = serializers.CharField(source='difficulty.get_level_display', read_only=True)
    knowledge_point_names = serializers.SerializerMethodField()
    options = QuestionOptionSerializer(many=True, read_only=True)
    images = QuestionImageSerializer(many=True, read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Question
        fields = ['id', 'question_bank', 'question_type', 'question_type_name', 'difficulty',
                 'difficulty_level', 'knowledge_points', 'knowledge_point_names', 'content',
                 'answer', 'analysis', 'score', 'options', 'images', 'created_by',
                 'created_by_username', 'created_at', 'updated_at', 'is_active']
        read_only_fields = ['created_by', 'created_at', 'updated_at']
    
    def get_knowledge_point_names(self, obj):
        return [kp.name for kp in obj.knowledge_points.all()]
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class QuestionDetailSerializer(QuestionSerializer):
    """题目详情序列化器"""
    options = QuestionOptionSerializer(many=True)
    images = QuestionImageSerializer(many=True, required=False)
    
    class Meta(QuestionSerializer.Meta):
        pass
    
    def create(self, validated_data):
        options_data = validated_data.pop('options')
        images_data = validated_data.pop('images', [])
        knowledge_points = validated_data.pop('knowledge_points', [])
        
        # 创建题目
        validated_data['created_by'] = self.context['request'].user
        question = Question.objects.create(**validated_data)
        
        # 添加知识点
        if knowledge_points:
            question.knowledge_points.set(knowledge_points)
        
        # 创建选项
        for option_data in options_data:
            QuestionOption.objects.create(question=question, **option_data)
        
        # 创建图片
        for image_data in images_data:
            QuestionImage.objects.create(question=question, **image_data)
        
        return question
    
    def update(self, instance, validated_data):
        options_data = validated_data.pop('options', None)
        images_data = validated_data.pop('images', None)
        knowledge_points = validated_data.pop('knowledge_points', None)
        
        # 更新题目基本信息
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # 更新知识点
        if knowledge_points is not None:
            instance.knowledge_points.set(knowledge_points)
        
        # 更新选项
        if options_data is not None:
            # 删除现有选项
            instance.options.all().delete()
            # 创建新选项
            for option_data in options_data:
                QuestionOption.objects.create(question=instance, **option_data)
        
        # 更新图片
        if images_data is not None:
            # 删除现有图片
            instance.images.all().delete()
            # 创建新图片
            for image_data in images_data:
                QuestionImage.objects.create(question=instance, **image_data)
        
        return instance


class QuestionImportSerializer(serializers.ModelSerializer):
    """题目导入序列化器"""
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = QuestionImport
        fields = ['id', 'question_bank', 'file', 'status', 'status_display', 'total_count',
                 'success_count', 'error_message', 'created_by', 'created_by_username',
                 'created_at', 'completed_at']
        read_only_fields = ['status', 'total_count', 'success_count', 'error_message',
                          'created_by', 'created_at', 'completed_at']
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)
