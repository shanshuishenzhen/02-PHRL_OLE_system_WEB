from django.contrib import admin
from .models import PaperTemplate, PaperSection, SectionRule, Paper, PaperQuestion, PaperGeneration


class PaperSectionInline(admin.TabularInline):
    model = PaperSection
    extra = 1


class SectionRuleInline(admin.TabularInline):
    model = SectionRule
    extra = 1


class PaperQuestionInline(admin.TabularInline):
    model = PaperQuestion
    extra = 0
    readonly_fields = ('question', 'section_name', 'order', 'score')
    can_delete = False
    max_num = 0
    fields = ('order', 'section_name', 'question', 'score')


@admin.register(PaperTemplate)
class PaperTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject', 'total_score', 'passing_score', 'duration', 'created_by', 'is_active', 'created_at')
    list_filter = ('subject', 'is_active', 'created_at')
    search_fields = ('name', 'description', 'subject')
    readonly_fields = ('created_by', 'created_at', 'updated_at')
    inlines = [PaperSectionInline]
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'subject')
        }),
        ('考试设置', {
            'fields': ('total_score', 'passing_score', 'duration', 'is_active')
        }),
        ('创建信息', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # 只在创建时设置创建人
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(PaperSection)
class PaperSectionAdmin(admin.ModelAdmin):
    list_display = ('template', 'name', 'question_type', 'question_count', 'score_per_question', 'total_score', 'order')
    list_filter = ('template', 'question_type')
    search_fields = ('name', 'description', 'template__name')
    inlines = [SectionRuleInline]


@admin.register(SectionRule)
class SectionRuleAdmin(admin.ModelAdmin):
    list_display = ('section', 'rule_type', 'question_bank', 'question_count', 'difficulty')
    list_filter = ('rule_type', 'question_bank', 'difficulty')
    search_fields = ('section__name', 'section__template__name')


@admin.register(Paper)
class PaperAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'template', 'total_score', 'passing_score', 'duration', 'status', 'created_by', 'created_at')
    list_filter = ('subject', 'status', 'created_at')
    search_fields = ('title', 'description', 'subject')
    readonly_fields = ('created_by', 'created_at', 'updated_at', 'published_at')
    inlines = [PaperQuestionInline]
    actions = ['publish_papers', 'archive_papers']
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'subject', 'template')
        }),
        ('考试设置', {
            'fields': ('total_score', 'passing_score', 'duration', 'status')
        }),
        ('时间信息', {
            'fields': ('created_by', 'created_at', 'updated_at', 'published_at')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # 只在创建时设置创建人
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def publish_papers(self, request, queryset):
        for paper in queryset.filter(status='draft'):
            if paper.questions.exists():
                paper.publish()
        self.message_user(request, f"已发布选中的试卷（仅处理草稿状态且包含题目的试卷）")
    publish_papers.short_description = "发布选中的试卷"
    
    def archive_papers(self, request, queryset):
        queryset.exclude(status='archived').update(status='archived')
        self.message_user(request, f"已归档选中的试卷")
    archive_papers.short_description = "归档选中的试卷"


@admin.register(PaperQuestion)
class PaperQuestionAdmin(admin.ModelAdmin):
    list_display = ('paper', 'order', 'section_name', 'question', 'score')
    list_filter = ('paper', 'section_name')
    search_fields = ('paper__title', 'question__content')
    ordering = ('paper', 'order')


@admin.register(PaperGeneration)
class PaperGenerationAdmin(admin.ModelAdmin):
    list_display = ('paper', 'template', 'status', 'created_by', 'created_at', 'completed_at')
    list_filter = ('status', 'created_at')
    search_fields = ('paper__title', 'template__name')
    readonly_fields = ('paper', 'template', 'status', 'created_by', 'created_at', 'completed_at', 'error_message')
    fieldsets = (
        (None, {
            'fields': ('paper', 'template', 'status')
        }),
        ('时间信息', {
            'fields': ('created_by', 'created_at', 'completed_at')
        }),
        ('错误信息', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
    )
