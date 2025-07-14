from rest_framework import serializers
from django.utils import timezone
from django.db import transaction
from django.db.models import Q

from exam_system.user_management.serializers import UserSerializer
from exam_system.exam_monitoring.serializers import ExamSerializer, ExamRecordSerializer
from exam_system.paper_management.serializers import PaperQuestionSerializer

from .models import (
    ScoringCriteria, ScoringRule, ScoreSheet, ScoreItem,
    ScoreDistribution, ScoreStatistics, ScoreAppeal
)


class ScoringRuleSerializer(serializers.ModelSerializer):
    """评分规则序列化器"""
    class Meta:
        model = ScoringRule
        fields = '__all__'


class ScoringCriteriaSerializer(serializers.ModelSerializer):
    """评分标准序列化器"""
    rules = ScoringRuleSerializer(many=True, read_only=True)
    created_by_info = UserSerializer(source='created_by', read_only=True)
    
    class Meta:
        model = ScoringCriteria
        fields = '__all__'


class ScoringCriteriaCreateSerializer(serializers.ModelSerializer):
    """评分标准创建序列化器"""
    rules = ScoringRuleSerializer(many=True, required=False)
    
    class Meta:
        model = ScoringCriteria
        fields = '__all__'
    
    @transaction.atomic
    def create(self, validated_data):
        rules_data = validated_data.pop('rules', [])
        criteria = ScoringCriteria.objects.create(**validated_data)
        
        for rule_data in rules_data:
            ScoringRule.objects.create(criteria=criteria, **rule_data)
        
        return criteria


class ScoreItemSerializer(serializers.ModelSerializer):
    """评分项序列化器"""
    question_info = PaperQuestionSerializer(source='question', read_only=True)
    marker_info = UserSerializer(source='marker', read_only=True)
    
    class Meta:
        model = ScoreItem
        fields = '__all__'


class ScoreItemUpdateSerializer(serializers.ModelSerializer):
    """评分项更新序列化器"""
    class Meta:
        model = ScoreItem
        fields = ['score', 'comments', 'marker']
    
    def validate(self, attrs):
        # 检查评分表状态
        score_sheet = self.instance.score_sheet
        if score_sheet.status not in ['pending', 'in_progress']:
            raise serializers.ValidationError("只能修改待评分或评分中状态的评分项")
        
        # 设置评分时间
        if 'score' in attrs and attrs['score'] is not None:
            attrs['marked_at'] = timezone.now()
            attrs['auto_scored'] = False
        
        return attrs
    
    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        
        # 如果设置了分数，更新评分表总分
        if 'score' in validated_data and validated_data['score'] is not None:
            instance.score_sheet.calculate_total_score()
        
        return instance


class ScoreSheetSerializer(serializers.ModelSerializer):
    """评分表序列化器"""
    exam_info = ExamSerializer(source='exam', read_only=True)
    exam_record_info = ExamRecordSerializer(source='exam_record', read_only=True)
    criteria_info = ScoringCriteriaSerializer(source='criteria', read_only=True)
    marker_info = UserSerializer(source='marker', read_only=True)
    reviewer_info = UserSerializer(source='reviewer', read_only=True)
    score_items = ScoreItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = ScoreSheet
        fields = '__all__'


class ScoreSheetUpdateSerializer(serializers.ModelSerializer):
    """评分表更新序列化器"""
    class Meta:
        model = ScoreSheet
        fields = ['status', 'comments', 'marker', 'reviewer', 'passing_score']
    
    def validate(self, attrs):
        # 检查状态变更
        if 'status' in attrs:
            current_status = self.instance.status
            new_status = attrs['status']
            
            # 状态流转验证
            valid_transitions = {
                'pending': ['in_progress'],
                'in_progress': ['completed'],
                'completed': ['reviewed'],
                'reviewed': [],
            }
            
            if new_status not in valid_transitions.get(current_status, []):
                raise serializers.ValidationError(f"无法从 {current_status} 状态转换为 {new_status} 状态")
            
            # 完成评分时，检查是否所有题目都已评分
            if new_status == 'completed':
                unscored_items = self.instance.score_items.filter(score__isnull=True).count()
                if unscored_items > 0:
                    raise serializers.ValidationError(f"还有 {unscored_items} 个评分项未完成评分")
                
                # 设置评分人和评分时间
                attrs['marker'] = self.context['request'].user
                attrs['marked_at'] = timezone.now()
            
            # 复核完成时，设置复核人和复核时间
            if new_status == 'reviewed':
                attrs['reviewer'] = self.context['request'].user
                attrs['reviewed_at'] = timezone.now()
        
        return attrs
    
    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        
        # 如果状态变为已完成，重新计算总分
        if 'status' in validated_data and validated_data['status'] == 'completed':
            instance.calculate_total_score()
            
            # 更新考试统计数据
            if hasattr(instance.exam, 'score_statistics'):
                instance.exam.score_statistics.update_statistics()
            else:
                ScoreStatistics.objects.create(exam=instance.exam).update_statistics()
        
        return instance


class ScoreSheetCreateSerializer(serializers.ModelSerializer):
    """评分表创建序列化器"""
    class Meta:
        model = ScoreSheet
        fields = ['exam', 'exam_record', 'criteria', 'passing_score']
    
    def validate(self, attrs):
        # 检查是否已存在评分表
        if ScoreSheet.objects.filter(exam_record=attrs['exam_record']).exists():
            raise serializers.ValidationError("该考试记录已存在评分表")
        
        # 检查考试记录状态
        if attrs['exam_record'].status != 'submitted':
            raise serializers.ValidationError("只能为已提交的考试记录创建评分表")
        
        # 检查考试记录是否属于指定的考试
        if attrs['exam_record'].exam != attrs['exam']:
            raise serializers.ValidationError("考试记录与考试不匹配")
        
        return attrs
    
    @transaction.atomic
    def create(self, validated_data):
        # 创建评分表
        score_sheet = ScoreSheet.objects.create(**validated_data)
        
        # 获取考试记录的所有答案
        exam_record = validated_data['exam_record']
        answers = exam_record.answers.all()
        
        # 为每个答案创建评分项
        for answer in answers:
            # 获取题目的满分
            paper_question = answer.question
            max_score = paper_question.score
            
            # 创建评分项
            ScoreItem.objects.create(
                score_sheet=score_sheet,
                question=paper_question,
                answer=answer,
                max_score=max_score
            )
        
        # 自动评分
        self.auto_score(score_sheet)
        
        return score_sheet
    
    def auto_score(self, score_sheet):
        """自动评分"""
        # 获取评分标准
        criteria = score_sheet.criteria
        if not criteria:
            return
        
        # 获取所有评分项
        score_items = score_sheet.score_items.all()
        
        for item in score_items:
            # 获取题目类型
            question_type = item.question.question.question_type.name
            
            # 获取评分规则
            try:
                rule = criteria.rules.get(question_type=question_type)
            except ScoringRule.DoesNotExist:
                continue
            
            # 只处理允许自动评分的规则
            if not rule.auto_score:
                continue
            
            # 获取答案
            answer = item.answer
            
            # 根据题目类型进行自动评分
            if question_type in ['单选题', '判断题']:
                # 单选题和判断题，答案完全正确得满分，否则得0分
                correct_option = item.question.question.correct_option
                if answer.answer_content == correct_option:
                    item.score = rule.full_score
                else:
                    item.score = 0
                
            elif question_type == '多选题':
                # 多选题，根据规则决定是否允许部分得分
                correct_options = set(item.question.question.correct_options.split(','))
                selected_options = set(answer.answer_content.split(','))
                
                if correct_options == selected_options:
                    # 完全正确
                    item.score = rule.full_score
                elif rule.partial_score_allowed:
                    # 允许部分得分
                    correct_count = len(correct_options.intersection(selected_options))
                    wrong_count = len(selected_options - correct_options)
                    
                    # 计算得分：正确选项得分 - 错误选项扣分
                    score = correct_count * rule.score_per_point
                    if wrong_count > 0:
                        score = max(0, score - wrong_count * rule.score_per_point)
                    
                    item.score = min(score, rule.full_score)
                else:
                    # 不允许部分得分
                    item.score = 0
            
            # 填空题可以部分自动评分，但通常需要人工复核
            elif question_type == '填空题' and rule.partial_score_allowed:
                correct_answers = item.question.question.correct_answer.split('|')
                user_answers = answer.answer_content.split('|')
                
                # 计算正确的空数
                correct_count = 0
                for i, (correct, user) in enumerate(zip(correct_answers, user_answers)):
                    if correct.strip() == user.strip():
                        correct_count += 1
                
                # 计算得分
                if len(correct_answers) > 0:
                    item.score = (correct_count / len(correct_answers)) * rule.full_score
                else:
                    item.score = 0
            
            # 更新评分项
            if item.score is not None:
                item.auto_scored = True
                item.marked_at = timezone.now()
                item.save()
        
        # 计算总分
        score_sheet.calculate_total_score()


class ScoreDistributionSerializer(serializers.ModelSerializer):
    """分数分布序列化器"""
    class Meta:
        model = ScoreDistribution
        fields = '__all__'


class ScoreStatisticsSerializer(serializers.ModelSerializer):
    """分数统计序列化器"""
    exam_info = ExamSerializer(source='exam', read_only=True)
    distributions = ScoreDistributionSerializer(source='exam.score_distributions', many=True, read_only=True)
    
    class Meta:
        model = ScoreStatistics
        fields = '__all__'


class ScoreAppealSerializer(serializers.ModelSerializer):
    """分数申诉序列化器"""
    student_info = UserSerializer(source='student', read_only=True)
    handler_info = UserSerializer(source='handler', read_only=True)
    score_item_info = ScoreItemSerializer(source='score_item', read_only=True)
    
    class Meta:
        model = ScoreAppeal
        fields = '__all__'


class ScoreAppealCreateSerializer(serializers.ModelSerializer):
    """分数申诉创建序列化器"""
    class Meta:
        model = ScoreAppeal
        fields = ['score_item', 'reason', 'expected_score']
    
    def validate(self, attrs):
        # 获取当前用户
        user = self.context['request'].user
        
        # 设置学生为当前用户
        attrs['student'] = user
        
        # 检查评分项是否属于当前用户的考试记录
        score_item = attrs['score_item']
        if score_item.score_sheet.exam_record.student != user:
            raise serializers.ValidationError("无法为其他学生的评分项创建申诉")
        
        # 检查是否已存在未处理的申诉
        if ScoreAppeal.objects.filter(
            score_item=score_item,
            status__in=['pending', 'processing']
        ).exists():
            raise serializers.ValidationError("该评分项已存在未处理的申诉")
        
        # 检查期望分数是否超过满分
        if attrs['expected_score'] > score_item.max_score:
            raise serializers.ValidationError(f"期望分数不能超过满分 {score_item.max_score}")
        
        # 检查评分表状态
        if score_item.score_sheet.status not in ['completed', 'reviewed']:
            raise serializers.ValidationError("只能对已完成评分的评分项提出申诉")
        
        # 检查分数是否已设置
        if score_item.score is None:
            raise serializers.ValidationError("该评分项尚未评分，无法申诉")
        
        # 检查期望分数是否与当前分数相同
        if attrs['expected_score'] == score_item.score:
            raise serializers.ValidationError("期望分数与当前分数相同，无需申诉")
        
        return attrs


class ScoreAppealHandleSerializer(serializers.ModelSerializer):
    """分数申诉处理序列化器"""
    class Meta:
        model = ScoreAppeal
        fields = ['status', 'response', 'adjusted_score']
    
    def validate(self, attrs):
        # 检查申诉状态
        if self.instance.status not in ['pending', 'processing']:
            raise serializers.ValidationError("只能处理待处理或处理中状态的申诉")
        
        # 检查新状态
        if 'status' in attrs:
            if attrs['status'] == 'approved':
                # 如果批准申诉，必须提供调整后的分数
                if 'adjusted_score' not in attrs or attrs['adjusted_score'] is None:
                    raise serializers.ValidationError("批准申诉时必须提供调整后的分数")
                
                # 检查调整后的分数是否超过满分
                if attrs['adjusted_score'] > self.instance.score_item.max_score:
                    raise serializers.ValidationError(f"调整后的分数不能超过满分 {self.instance.score_item.max_score}")
            
            # 如果拒绝或取消申诉，必须提供回复
            if attrs['status'] in ['rejected', 'cancelled'] and ('response' not in attrs or not attrs['response']):
                raise serializers.ValidationError(f"{attrs['status']} 申诉时必须提供回复")
        
        # 设置处理人和处理时间
        if 'status' in attrs and attrs['status'] in ['approved', 'rejected']:
            attrs['handler'] = self.context['request'].user
            attrs['handled_at'] = timezone.now()
        
        return attrs
    
    @transaction.atomic
    def update(self, instance, validated_data):
        # 更新申诉
        instance = super().update(instance, validated_data)
        
        # 如果批准申诉，更新评分项分数
        if 'status' in validated_data and validated_data['status'] == 'approved' and 'adjusted_score' in validated_data:
            # 更新评分项
            score_item = instance.score_item
            score_item.score = validated_data['adjusted_score']
            score_item.comments = f"{score_item.comments or ''}\n[申诉调整] {instance.response}"
            score_item.save()
            
            # 重新计算总分
            score_item.score_sheet.calculate_total_score()
            
            # 更新考试统计数据
            if hasattr(score_item.score_sheet.exam, 'score_statistics'):
                score_item.score_sheet.exam.score_statistics.update_statistics()
        
        return instance
