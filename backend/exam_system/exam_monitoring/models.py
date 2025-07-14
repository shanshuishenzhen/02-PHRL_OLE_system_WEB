from django.db import models
from django.utils import timezone
from exam_system.user_management.models import User
from exam_system.paper_management.models import Paper


class Exam(models.Model):
    """考试"""
    STATUS_CHOICES = (
        ('pending', '未开始'),
        ('in_progress', '进行中'),
        ('completed', '已结束'),
        ('cancelled', '已取消'),
    )
    
    name = models.CharField(max_length=100, verbose_name='考试名称')
    description = models.TextField(blank=True, null=True, verbose_name='考试描述')
    subject = models.CharField(max_length=50, verbose_name='科目')
    paper = models.ForeignKey(Paper, on_delete=models.PROTECT, verbose_name='试卷')
    start_time = models.DateTimeField(verbose_name='开始时间')
    end_time = models.DateTimeField(verbose_name='结束时间')
    duration = models.IntegerField(verbose_name='考试时长(分钟)')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_exams', verbose_name='创建人')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '考试'
        verbose_name_plural = verbose_name
        ordering = ['-start_time']
    
    def __str__(self):
        return self.name
    
    def update_status(self):
        """更新考试状态"""
        now = timezone.now()
        
        if self.status == 'cancelled':
            return
        
        if now < self.start_time:
            self.status = 'pending'
        elif now >= self.start_time and now <= self.end_time:
            self.status = 'in_progress'
        else:
            self.status = 'completed'
        
        self.save(update_fields=['status'])
        return self.status


class ExamRoom(models.Model):
    """考场"""
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='rooms', verbose_name='考试')
    name = models.CharField(max_length=100, verbose_name='考场名称')
    location = models.CharField(max_length=200, blank=True, null=True, verbose_name='考场位置')
    capacity = models.IntegerField(default=30, verbose_name='考场容量')
    invigilators = models.ManyToManyField(User, related_name='invigilated_rooms', verbose_name='监考人员')
    notes = models.TextField(blank=True, null=True, verbose_name='备注')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '考场'
        verbose_name_plural = verbose_name
        ordering = ['exam', 'name']
        unique_together = ['exam', 'name']
    
    def __str__(self):
        return f"{self.exam.name} - {self.name}"


class ExamRegistration(models.Model):
    """考试报名"""
    STATUS_CHOICES = (
        ('registered', '已报名'),
        ('approved', '已审核'),
        ('rejected', '已拒绝'),
        ('cancelled', '已取消'),
    )
    
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='registrations', verbose_name='考试')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exam_registrations', verbose_name='考生')
    room = models.ForeignKey(ExamRoom, on_delete=models.SET_NULL, null=True, blank=True, related_name='registrations', verbose_name='考场')
    seat_number = models.CharField(max_length=20, blank=True, null=True, verbose_name='座位号')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='registered', verbose_name='状态')
    registered_at = models.DateTimeField(auto_now_add=True, verbose_name='报名时间')
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name='审核时间')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_registrations', verbose_name='审核人')
    notes = models.TextField(blank=True, null=True, verbose_name='备注')
    
    class Meta:
        verbose_name = '考试报名'
        verbose_name_plural = verbose_name
        ordering = ['-registered_at']
        unique_together = ['exam', 'student']
    
    def __str__(self):
        return f"{self.student.username} - {self.exam.name}"


class ExamRecord(models.Model):
    """考试记录"""
    STATUS_CHOICES = (
        ('not_started', '未开始'),
        ('in_progress', '进行中'),
        ('submitted', '已提交'),
        ('marked', '已阅卷'),
        ('cancelled', '已取消'),
    )
    
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='records', verbose_name='考试')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exam_records', verbose_name='考生')
    registration = models.OneToOneField(ExamRegistration, on_delete=models.CASCADE, related_name='exam_record', verbose_name='报名记录')
    start_time = models.DateTimeField(null=True, blank=True, verbose_name='开始时间')
    submit_time = models.DateTimeField(null=True, blank=True, verbose_name='提交时间')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started', verbose_name='状态')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP地址')
    user_agent = models.TextField(null=True, blank=True, verbose_name='用户代理')
    score = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, verbose_name='分数')
    is_passed = models.BooleanField(null=True, blank=True, verbose_name='是否通过')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '考试记录'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
        unique_together = ['exam', 'student']
    
    def __str__(self):
        return f"{self.student.username} - {self.exam.name}"
    
    def calculate_duration(self):
        """计算考试时长(分钟)"""
        if self.start_time and self.submit_time:
            duration = (self.submit_time - self.start_time).total_seconds() / 60
            return round(duration, 1)
        return None


class ExamAnswer(models.Model):
    """考生答案"""
    exam_record = models.ForeignKey(ExamRecord, on_delete=models.CASCADE, related_name='answers', verbose_name='考试记录')
    question_id = models.IntegerField(verbose_name='题目ID')
    answer_content = models.TextField(verbose_name='答案内容')
    is_correct = models.BooleanField(null=True, blank=True, verbose_name='是否正确')
    score = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, verbose_name='得分')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '考生答案'
        verbose_name_plural = verbose_name
        ordering = ['exam_record', 'question_id']
        unique_together = ['exam_record', 'question_id']
    
    def __str__(self):
        return f"{self.exam_record.student.username} - 题目{self.question_id}"


class ExamSnapshot(models.Model):
    """考试快照，用于记录考生考试过程中的行为"""
    ACTION_CHOICES = (
        ('enter', '进入考试'),
        ('leave', '离开考试'),
        ('submit', '提交答案'),
        ('change_answer', '修改答案'),
        ('switch_tab', '切换标签页'),
        ('full_screen_exit', '退出全屏'),
        ('copy_attempt', '尝试复制'),
        ('paste_attempt', '尝试粘贴'),
        ('print_attempt', '尝试打印'),
        ('face_missing', '人脸丢失'),
        ('multiple_faces', '多人脸检测'),
        ('unknown_face', '未知人脸'),
        ('other', '其他行为'),
    )
    
    exam_record = models.ForeignKey(ExamRecord, on_delete=models.CASCADE, related_name='snapshots', verbose_name='考试记录')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name='行为')
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='时间戳')
    details = models.TextField(blank=True, null=True, verbose_name='详细信息')
    screenshot = models.ImageField(upload_to='exam_snapshots/%Y/%m/%d/', null=True, blank=True, verbose_name='屏幕截图')
    is_violation = models.BooleanField(default=False, verbose_name='是否违规')
    
    class Meta:
        verbose_name = '考试快照'
        verbose_name_plural = verbose_name
        ordering = ['exam_record', '-timestamp']
    
    def __str__(self):
        return f"{self.exam_record.student.username} - {self.get_action_display()} - {self.timestamp}"


class ExamNotification(models.Model):
    """考试通知"""
    TYPE_CHOICES = (
        ('system', '系统通知'),
        ('invigilator', '监考员通知'),
        ('warning', '警告通知'),
        ('info', '信息通知'),
    )
    
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='notifications', verbose_name='考试')
    room = models.ForeignKey(ExamRoom, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications', verbose_name='考场')
    student = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='exam_notifications', verbose_name='考生')
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_notifications', verbose_name='发送人')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='system', verbose_name='通知类型')
    title = models.CharField(max_length=100, verbose_name='通知标题')
    content = models.TextField(verbose_name='通知内容')
    is_read = models.BooleanField(default=False, verbose_name='是否已读')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        verbose_name = '考试通知'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
