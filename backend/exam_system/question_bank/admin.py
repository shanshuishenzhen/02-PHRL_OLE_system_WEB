from django.contrib import admin
from .models import (
    QuestionBank, QuestionType, DifficultyLevel, KnowledgePoint,
    Question, QuestionOption, QuestionImage, QuestionImport
)


class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption
    extra = 4


class QuestionImageInline(admin.TabularInline):
    model = QuestionImage
    extra = 1


@admin.register(QuestionBank)
class QuestionBankAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject', 'description', 'is_active', 'created_at', 'updated_at')
    list_filter = ('subject', 'is_active', 'created_at')
    search_fields = ('name', 'subject', 'description')
    ordering = ('-created_at',)


@admin.register(QuestionType)
class QuestionTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')


@admin.register(DifficultyLevel)
class DifficultyLevelAdmin(admin.ModelAdmin):
    list_display = ('level', 'get_level_display', 'description')
    list_filter = ('level',)
    search_fields = ('description',)
    ordering = ('level',)


@admin.register(KnowledgePoint)
class KnowledgePointAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject', 'parent', 'description')
    list_filter = ('subject', 'parent')
    search_fields = ('name', 'description')
    ordering = ('subject', 'name')


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'question_bank', 'question_type', 'content_preview', 'difficulty', 'score', 'is_active')
    list_filter = ('question_bank', 'question_type', 'difficulty', 'is_active', 'created_at')
    search_fields = ('content', 'answer', 'analysis')
    ordering = ('-created_at',)
    filter_horizontal = ('knowledge_points',)
    inlines = [QuestionOptionInline, QuestionImageInline]
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = '题目内容预览'


@admin.register(QuestionOption)
class QuestionOptionAdmin(admin.ModelAdmin):
    list_display = ('question', 'option_key', 'content_preview', 'is_correct')
    list_filter = ('is_correct',)
    search_fields = ('question__content', 'content')
    
    def content_preview(self, obj):
        return obj.content[:30] + '...' if len(obj.content) > 30 else obj.content
    content_preview.short_description = '选项内容预览'


@admin.register(QuestionImage)
class QuestionImageAdmin(admin.ModelAdmin):
    list_display = ('question', 'image', 'description')
    search_fields = ('question__content', 'description')


@admin.register(QuestionImport)
class QuestionImportAdmin(admin.ModelAdmin):
    list_display = ('question_bank', 'file', 'status', 'total_count', 'success_count', 'created_at', 'completed_at')
    list_filter = ('status', 'question_bank', 'created_at')
    search_fields = ('question_bank__name', 'file')
    ordering = ('-created_at',)
    readonly_fields = ('status', 'total_count', 'success_count', 'error_message', 'completed_at')
