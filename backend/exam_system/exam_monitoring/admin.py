from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Exam, ExamRoom, ExamRegistration, ExamRecord, 
    ExamAnswer, ExamSnapshot, ExamNotification
)


class ExamRoomInline(admin.TabularInline):
    model = ExamRoom
    extra = 0
    fields = ('name', 'location', 'capacity')
    show_change_link = True


class ExamRegistrationInline(admin.TabularInline):
    model = ExamRegistration
    extra = 0
    fields = ('student', 'status', 'room', 'seat_number')
    show_change_link = True


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject', 'paper', 'start_time', 'end_time', 'duration', 'status', 'is_active', 'created_by')
    list_filter = ('status', 'subject', 'is_active', 'created_by')
    search_fields = ('name', 'description', 'subject')
    date_hierarchy = 'start_time'
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'description', 'subject', 'paper')
        }),
        ('时间设置', {
            'fields': ('start_time', 'end_time', 'duration')
        }),
        ('状态信息', {
            'fields': ('status', 'is_active')
        }),
        ('创建信息', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )
    inlines = [ExamRoomInline, ExamRegistrationInline]
    actions = ['update_exam_status', 'start_exams', 'end_exams', 'cancel_exams']
    
    def update_exam_status(self, request, queryset):
        updated_count = 0
        for exam in queryset:
            old_status = exam.status
            new_status = exam.update_status()
            if old_status != new_status:
                updated_count += 1
        self.message_user(request, f"已更新{updated_count}个考试的状态")
    update_exam_status.short_description = "更新所选考试的状态"
    
    def start_exams(self, request, queryset):
        started_count = 0
        for exam in queryset.filter(status='pending'):
            exam.status = 'in_progress'
            exam.save(update_fields=['status'])
            started_count += 1
        self.message_user(request, f"已开始{started_count}个考试")
    start_exams.short_description = "开始所选考试"
    
    def end_exams(self, request, queryset):
        ended_count = 0
        for exam in queryset.filter(status='in_progress'):
            exam.status = 'completed'
            exam.save(update_fields=['status'])
            ended_count += 1
        self.message_user(request, f"已结束{ended_count}个考试")
    end_exams.short_description = "结束所选考试"
    
    def cancel_exams(self, request, queryset):
        cancelled_count = 0
        for exam in queryset.exclude(status='completed'):
            exam.status = 'cancelled'
            exam.save(update_fields=['status'])
            cancelled_count += 1
        self.message_user(request, f"已取消{cancelled_count}个考试")
    cancel_exams.short_description = "取消所选考试"


@admin.register(ExamRoom)
class ExamRoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'exam', 'location', 'capacity', 'get_invigilators')
    list_filter = ('exam',)
    search_fields = ('name', 'location', 'notes')
    filter_horizontal = ('invigilators',)
    
    def get_invigilators(self, obj):
        return ", ".join([invigilator.username for invigilator in obj.invigilators.all()])
    get_invigilators.short_description = "监考人员"


@admin.register(ExamRegistration)
class ExamRegistrationAdmin(admin.ModelAdmin):
    list_display = ('student', 'exam', 'status', 'room', 'seat_number', 'registered_at', 'approved_at', 'approved_by')
    list_filter = ('status', 'exam', 'room')
    search_fields = ('student__username', 'student__name', 'notes')
    readonly_fields = ('registered_at',)
    date_hierarchy = 'registered_at'
    actions = ['approve_registrations', 'reject_registrations', 'cancel_registrations']
    
    def approve_registrations(self, request, queryset):
        from django.utils import timezone
        approved_count = 0
        for registration in queryset.filter(status='registered'):
            registration.status = 'approved'
            registration.approved_at = timezone.now()
            registration.approved_by = request.user
            registration.save(update_fields=['status', 'approved_at', 'approved_by'])
            approved_count += 1
        self.message_user(request, f"已审核通过{approved_count}个报名")
    approve_registrations.short_description = "审核通过所选报名"
    
    def reject_registrations(self, request, queryset):
        from django.utils import timezone
        rejected_count = 0
        for registration in queryset.filter(status='registered'):
            registration.status = 'rejected'
            registration.approved_at = timezone.now()
            registration.approved_by = request.user
            registration.save(update_fields=['status', 'approved_at', 'approved_by'])
            rejected_count += 1
        self.message_user(request, f"已拒绝{rejected_count}个报名")
    reject_registrations.short_description = "拒绝所选报名"
    
    def cancel_registrations(self, request, queryset):
        cancelled_count = 0
        for registration in queryset.exclude(status='cancelled'):
            registration.status = 'cancelled'
            registration.save(update_fields=['status'])
            cancelled_count += 1
        self.message_user(request, f"已取消{cancelled_count}个报名")
    cancel_registrations.short_description = "取消所选报名"


class ExamAnswerInline(admin.TabularInline):
    model = ExamAnswer
    extra = 0
    fields = ('question_id', 'answer_content', 'is_correct', 'score')
    readonly_fields = ('created_at', 'updated_at')
    show_change_link = True


class ExamSnapshotInline(admin.TabularInline):
    model = ExamSnapshot
    extra = 0
    fields = ('action', 'timestamp', 'details', 'is_violation')
    readonly_fields = ('timestamp',)
    show_change_link = True


@admin.register(ExamRecord)
class ExamRecordAdmin(admin.ModelAdmin):
    list_display = ('student', 'exam', 'status', 'start_time', 'submit_time', 'get_duration', 'score', 'is_passed')
    list_filter = ('status', 'exam', 'is_passed')
    search_fields = ('student__username', 'student__name')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'start_time'
    inlines = [ExamAnswerInline, ExamSnapshotInline]
    actions = ['mark_as_submitted', 'mark_as_cancelled']
    
    def get_duration(self, obj):
        duration = obj.calculate_duration()
        if duration is not None:
            return f"{duration}分钟"
        return "-"
    get_duration.short_description = "考试时长"
    
    def mark_as_submitted(self, request, queryset):
        from django.utils import timezone
        submitted_count = 0
        for record in queryset.filter(status='in_progress'):
            record.status = 'submitted'
            record.submit_time = timezone.now()
            record.save(update_fields=['status', 'submit_time'])
            submitted_count += 1
        self.message_user(request, f"已将{submitted_count}个考试记录标记为已提交")
    mark_as_submitted.short_description = "标记所选记录为已提交"
    
    def mark_as_cancelled(self, request, queryset):
        cancelled_count = 0
        for record in queryset.exclude(status='cancelled'):
            record.status = 'cancelled'
            record.save(update_fields=['status'])
            cancelled_count += 1
        self.message_user(request, f"已将{cancelled_count}个考试记录标记为已取消")
    mark_as_cancelled.short_description = "标记所选记录为已取消"


@admin.register(ExamAnswer)
class ExamAnswerAdmin(admin.ModelAdmin):
    list_display = ('exam_record', 'question_id', 'answer_content_preview', 'is_correct', 'score')
    list_filter = ('is_correct', 'exam_record__exam')
    search_fields = ('exam_record__student__username', 'answer_content')
    readonly_fields = ('created_at', 'updated_at')
    
    def answer_content_preview(self, obj):
        if len(obj.answer_content) > 50:
            return obj.answer_content[:50] + '...'
        return obj.answer_content
    answer_content_preview.short_description = "答案内容预览"


@admin.register(ExamSnapshot)
class ExamSnapshotAdmin(admin.ModelAdmin):
    list_display = ('exam_record', 'action', 'timestamp', 'details_preview', 'is_violation')
    list_filter = ('action', 'is_violation', 'exam_record__exam')
    search_fields = ('exam_record__student__username', 'details')
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'
    
    def details_preview(self, obj):
        if obj.details and len(obj.details) > 50:
            return obj.details[:50] + '...'
        return obj.details
    details_preview.short_description = "详细信息预览"


@admin.register(ExamNotification)
class ExamNotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'exam', 'room', 'student', 'type', 'sender', 'is_read', 'created_at')
    list_filter = ('type', 'is_read', 'exam')
    search_fields = ('title', 'content', 'student__username')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        updated_count = queryset.filter(is_read=False).update(is_read=True)
        self.message_user(request, f"已将{updated_count}条通知标记为已读")
    mark_as_read.short_description = "标记所选通知为已读"
    
    def mark_as_unread(self, request, queryset):
        updated_count = queryset.filter(is_read=True).update(is_read=False)
        self.message_user(request, f"已将{updated_count}条通知标记为未读")
    mark_as_unread.short_description = "标记所选通知为未读"
