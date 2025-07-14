from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import (
    AnalysisTask, ExamAnalysis, StudentAnalysis, QuestionAnalysis,
    KnowledgePointAnalysis, ClassAnalysis, DepartmentAnalysis,
    AnalysisReport, AnalysisTemplate
)


class AnalysisTaskAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'task_type', 'status', 'created_by', 'created_at', 'completed_at', 'has_report']
    list_filter = ['task_type', 'status', 'created_by']
    search_fields = ['name', 'created_by__username']
    readonly_fields = ['created_at', 'updated_at', 'completed_at']
    actions = ['mark_as_pending', 'mark_as_processing', 'mark_as_completed', 'mark_as_failed']
    
    def has_report(self, obj):
        return hasattr(obj, 'report')
    has_report.boolean = True
    has_report.short_description = '有报告'
    
    def mark_as_pending(self, request, queryset):
        queryset.update(status='pending')
    mark_as_pending.short_description = '标记为待处理'
    
    def mark_as_processing(self, request, queryset):
        queryset.update(status='processing')
    mark_as_processing.short_description = '标记为处理中'
    
    def mark_as_completed(self, request, queryset):
        queryset.update(status='completed', completed_at=timezone.now())
    mark_as_completed.short_description = '标记为已完成'
    
    def mark_as_failed(self, request, queryset):
        queryset.update(status='failed')
    mark_as_failed.short_description = '标记为失败'


class ExamAnalysisAdmin(admin.ModelAdmin):
    list_display = ['id', 'exam_name', 'task_status', 'total_students', 'attendance_count', 'pass_count', 'average_score', 'created_at']
    list_filter = ['exam__name', 'task__status']
    search_fields = ['exam__name', 'task__name']
    readonly_fields = ['created_at', 'updated_at']
    
    def exam_name(self, obj):
        return obj.exam.name
    exam_name.short_description = '考试名称'
    
    def task_status(self, obj):
        return obj.task.get_status_display()
    task_status.short_description = '任务状态'


class StudentAnalysisAdmin(admin.ModelAdmin):
    list_display = ['id', 'student_name', 'task_status', 'exam_count', 'attendance_count', 'pass_count', 'average_score', 'created_at']
    list_filter = ['student__username', 'task__status']
    search_fields = ['student__username', 'student__name', 'task__name']
    readonly_fields = ['created_at', 'updated_at']
    
    def student_name(self, obj):
        return f"{obj.student.username} ({obj.student.name})"
    student_name.short_description = '学生'
    
    def task_status(self, obj):
        return obj.task.get_status_display()
    task_status.short_description = '任务状态'


class QuestionAnalysisAdmin(admin.ModelAdmin):
    list_display = ['id', 'question_content', 'task_status', 'usage_count', 'correct_count', 'correct_rate', 'difficulty_index', 'created_at']
    list_filter = ['question__question_type', 'task__status']
    search_fields = ['question__content', 'task__name']
    readonly_fields = ['created_at', 'updated_at']
    
    def question_content(self, obj):
        return format_html("<span title='{}'>{}</span>", obj.question.content, obj.question.content[:30] + '...' if len(obj.question.content) > 30 else obj.question.content)
    question_content.short_description = '题目内容'
    
    def task_status(self, obj):
        return obj.task.get_status_display()
    task_status.short_description = '任务状态'


class KnowledgePointAnalysisAdmin(admin.ModelAdmin):
    list_display = ['id', 'knowledge_point_name', 'task_status', 'question_count', 'usage_count', 'correct_rate', 'difficulty_index', 'created_at']
    list_filter = ['knowledge_point__subject', 'task__status']
    search_fields = ['knowledge_point__name', 'task__name']
    readonly_fields = ['created_at', 'updated_at']
    
    def knowledge_point_name(self, obj):
        return obj.knowledge_point.name
    knowledge_point_name.short_description = '知识点'
    
    def task_status(self, obj):
        return obj.task.get_status_display()
    task_status.short_description = '任务状态'


class ClassAnalysisAdmin(admin.ModelAdmin):
    list_display = ['id', 'class_name', 'task_status', 'student_count', 'exam_count', 'average_attendance_rate', 'average_pass_rate', 'average_score', 'created_at']
    list_filter = ['class_obj__department', 'task__status']
    search_fields = ['class_obj__name', 'task__name']
    readonly_fields = ['created_at', 'updated_at']
    
    def class_name(self, obj):
        return obj.class_obj.name
    class_name.short_description = '班级'
    
    def task_status(self, obj):
        return obj.task.get_status_display()
    task_status.short_description = '任务状态'


class DepartmentAnalysisAdmin(admin.ModelAdmin):
    list_display = ['id', 'department_name', 'task_status', 'class_count', 'student_count', 'exam_count', 'average_attendance_rate', 'average_pass_rate', 'average_score', 'created_at']
    list_filter = ['task__status']
    search_fields = ['department__name', 'task__name']
    readonly_fields = ['created_at', 'updated_at']
    
    def department_name(self, obj):
        return obj.department.name
    department_name.short_description = '院系'
    
    def task_status(self, obj):
        return obj.task.get_status_display()
    task_status.short_description = '任务状态'


class AnalysisReportAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'task_type', 'task_status', 'is_public', 'created_at']
    list_filter = ['is_public', 'task__task_type', 'task__status']
    search_fields = ['title', 'summary', 'task__name']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['make_public', 'make_private']
    
    def task_type(self, obj):
        return obj.task.get_task_type_display()
    task_type.short_description = '任务类型'
    
    def task_status(self, obj):
        return obj.task.get_status_display()
    task_status.short_description = '任务状态'
    
    def make_public(self, request, queryset):
        queryset.update(is_public=True)
    make_public.short_description = '设为公开'
    
    def make_private(self, request, queryset):
        queryset.update(is_public=False)
    make_private.short_description = '设为私有'


class AnalysisTemplateAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'task_type', 'is_system', 'created_by', 'created_at']
    list_filter = ['task_type', 'is_system']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['mark_as_system', 'mark_as_user']
    
    def mark_as_system(self, request, queryset):
        queryset.update(is_system=True)
    mark_as_system.short_description = '标记为系统模板'
    
    def mark_as_user(self, request, queryset):
        queryset.update(is_system=False)
    mark_as_user.short_description = '标记为用户模板'


admin.site.register(AnalysisTask, AnalysisTaskAdmin)
admin.site.register(ExamAnalysis, ExamAnalysisAdmin)
admin.site.register(StudentAnalysis, StudentAnalysisAdmin)
admin.site.register(QuestionAnalysis, QuestionAnalysisAdmin)
admin.site.register(KnowledgePointAnalysis, KnowledgePointAnalysisAdmin)
admin.site.register(ClassAnalysis, ClassAnalysisAdmin)
admin.site.register(DepartmentAnalysis, DepartmentAnalysisAdmin)
admin.site.register(AnalysisReport, AnalysisReportAdmin)
admin.site.register(AnalysisTemplate, AnalysisTemplateAdmin)
