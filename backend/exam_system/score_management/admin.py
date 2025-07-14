from django.contrib import admin
from django.utils import timezone
from django.db.models import Q
from .models import (
    ScoringCriteria, ScoringRule, ScoreSheet, ScoreItem,
    ScoreDistribution, ScoreStatistics, ScoreAppeal
)


class ScoringRuleInline(admin.TabularInline):
    model = ScoringRule
    extra = 1


@admin.register(ScoringCriteria)
class ScoringCriteriaAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_by', 'created_at', 'updated_at']
    list_filter = ['created_by', 'created_at']
    search_fields = ['name', 'description']
    date_hierarchy = 'created_at'
    inlines = [ScoringRuleInline]


@admin.register(ScoringRule)
class ScoringRuleAdmin(admin.ModelAdmin):
    list_display = ['criteria', 'question_type', 'full_score', 'partial_score_allowed', 'auto_score']
    list_filter = ['criteria', 'question_type', 'auto_score', 'partial_score_allowed']
    search_fields = ['criteria__name', 'question_type', 'description']


class ScoreItemInline(admin.TabularInline):
    model = ScoreItem
    extra = 0
    readonly_fields = ['question', 'answer', 'max_score', 'auto_scored', 'marked_at']
    fields = ['question', 'score', 'max_score', 'auto_scored', 'marker', 'marked_at', 'comments']


@admin.register(ScoreSheet)
class ScoreSheetAdmin(admin.ModelAdmin):
    list_display = ['exam', 'exam_record', 'status', 'total_score', 'is_passed', 'marker', 'marked_at']
    list_filter = ['status', 'is_passed', 'marker', 'reviewer', 'created_at']
    search_fields = ['exam__name', 'exam_record__student__username', 'comments']
    date_hierarchy = 'created_at'
    readonly_fields = ['exam', 'exam_record', 'total_score', 'is_passed', 'marked_at', 'reviewed_at']
    inlines = [ScoreItemInline]
    actions = ['auto_score_selected', 'complete_selected', 'review_selected']
    
    def auto_score_selected(self, request, queryset):
        """对选中的评分表执行自动评分"""
        from .serializers import ScoreSheetCreateSerializer
        
        count = 0
        for score_sheet in queryset.filter(status__in=['pending', 'in_progress']):
            serializer = ScoreSheetCreateSerializer()
            serializer.auto_score(score_sheet)
            count += 1
        
        self.message_user(request, f'成功对 {count} 个评分表执行自动评分')
    auto_score_selected.short_description = '自动评分所选评分表'
    
    def complete_selected(self, request, queryset):
        """完成选中的评分表评分"""
        count = 0
        for score_sheet in queryset.filter(status__in=['pending', 'in_progress']):
            # 检查是否所有题目都已评分
            unscored_items = score_sheet.score_items.filter(score__isnull=True).count()
            if unscored_items == 0:
                score_sheet.status = 'completed'
                score_sheet.marker = request.user
                score_sheet.marked_at = timezone.now()
                score_sheet.save()
                score_sheet.calculate_total_score()
                count += 1
        
        # 更新考试统计数据
        if count > 0:
            exams = set(queryset.values_list('exam', flat=True))
            for exam_id in exams:
                if ScoreStatistics.objects.filter(exam_id=exam_id).exists():
                    ScoreStatistics.objects.get(exam_id=exam_id).update_statistics()
                else:
                    ScoreStatistics.objects.create(exam_id=exam_id).update_statistics()
        
        self.message_user(request, f'成功完成 {count} 个评分表的评分')
    complete_selected.short_description = '完成所选评分表评分'
    
    def review_selected(self, request, queryset):
        """复核选中的评分表"""
        count = 0
        for score_sheet in queryset.filter(status='completed'):
            score_sheet.status = 'reviewed'
            score_sheet.reviewer = request.user
            score_sheet.reviewed_at = timezone.now()
            score_sheet.save()
            count += 1
        
        self.message_user(request, f'成功复核 {count} 个评分表')
    review_selected.short_description = '复核所选评分表'


@admin.register(ScoreItem)
class ScoreItemAdmin(admin.ModelAdmin):
    list_display = ['score_sheet', 'question', 'score', 'max_score', 'auto_scored', 'marker', 'marked_at']
    list_filter = ['auto_scored', 'marked_at', 'score_sheet__status']
    search_fields = ['score_sheet__exam__name', 'question__question__content', 'comments']
    readonly_fields = ['score_sheet', 'question', 'answer', 'max_score', 'auto_scored', 'marked_at']
    actions = ['auto_score_selected']
    
    def auto_score_selected(self, request, queryset):
        """对选中的评分项执行自动评分"""
        from .views import ScoreItemViewSet
        
        count = 0
        for score_item in queryset.filter(score_sheet__status__in=['pending', 'in_progress']):
            # 获取评分标准
            criteria = score_item.score_sheet.criteria
            if not criteria:
                continue
            
            # 获取题目类型
            question_type = score_item.question.question.question_type.name
            
            # 获取评分规则
            try:
                rule = criteria.rules.get(question_type=question_type)
            except ScoringRule.DoesNotExist:
                continue
            
            # 只处理允许自动评分的规则
            if not rule.auto_score:
                continue
            
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
                count += 1
        
        self.message_user(request, f'成功对 {count} 个评分项执行自动评分')
    auto_score_selected.short_description = '自动评分所选评分项'


@admin.register(ScoreDistribution)
class ScoreDistributionAdmin(admin.ModelAdmin):
    list_display = ['exam', 'score_range_min', 'score_range_max', 'count', 'percentage']
    list_filter = ['exam', 'created_at']
    search_fields = ['exam__name']
    readonly_fields = ['count', 'percentage', 'created_at', 'updated_at']


@admin.register(ScoreStatistics)
class ScoreStatisticsAdmin(admin.ModelAdmin):
    list_display = ['exam', 'total_students', 'scored_students', 'passed_students', 'pass_rate', 'average_score']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['exam__name']
    readonly_fields = ['total_students', 'scored_students', 'passed_students', 'pass_rate', 
                      'highest_score', 'lowest_score', 'average_score', 'median_score', 'standard_deviation',
                      'created_at', 'updated_at']
    actions = ['update_statistics_selected']
    
    def update_statistics_selected(self, request, queryset):
        """更新选中的统计数据"""
        count = 0
        for statistics in queryset:
            statistics.update_statistics()
            count += 1
        
        self.message_user(request, f'成功更新 {count} 个统计数据')
    update_statistics_selected.short_description = '更新所选统计数据'


@admin.register(ScoreAppeal)
class ScoreAppealAdmin(admin.ModelAdmin):
    list_display = ['student', 'score_item', 'original_score', 'expected_score', 'adjusted_score', 'status', 'created_at']
    list_filter = ['status', 'created_at', 'handled_at']
    search_fields = ['student__username', 'reason', 'response']
    readonly_fields = ['student', 'score_item', 'original_score', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    actions = ['approve_selected', 'reject_selected']
    
    def approve_selected(self, request, queryset):
        """批准选中的申诉"""
        count = 0
        for appeal in queryset.filter(status__in=['pending', 'processing']):
            if appeal.expected_score is not None:
                appeal.status = 'approved'
                appeal.adjusted_score = appeal.expected_score
                appeal.handler = request.user
                appeal.handled_at = timezone.now()
                appeal.response = '申诉已批准，分数已调整。'
                appeal.save()
                
                # 更新评分项
                score_item = appeal.score_item
                score_item.score = appeal.adjusted_score
                score_item.comments = f"{score_item.comments or ''}\n[申诉调整] {appeal.response}"
                score_item.save()
                
                # 重新计算总分
                score_item.score_sheet.calculate_total_score()
                
                # 更新考试统计数据
                if hasattr(score_item.score_sheet.exam, 'score_statistics'):
                    score_item.score_sheet.exam.score_statistics.update_statistics()
                
                count += 1
        
        self.message_user(request, f'成功批准 {count} 个申诉')
    approve_selected.short_description = '批准所选申诉'
    
    def reject_selected(self, request, queryset):
        """拒绝选中的申诉"""
        count = 0
        for appeal in queryset.filter(status__in=['pending', 'processing']):
            appeal.status = 'rejected'
            appeal.handler = request.user
            appeal.handled_at = timezone.now()
            appeal.response = '申诉已拒绝，分数保持不变。'
            appeal.save()
            count += 1
        
        self.message_user(request, f'成功拒绝 {count} 个申诉')
    reject_selected.short_description = '拒绝所选申诉'
