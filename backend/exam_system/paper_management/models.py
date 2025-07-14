from django.db import models
from django.utils import timezone
from exam_system.user_management.models import User
from exam_system.question_bank.models import Question, QuestionBank, QuestionType, DifficultyLevel


class PaperTemplate(models.Model):
    """试卷模板"""
    name = models.CharField(max_length=100, verbose_name='模板名称')
    description = models.TextField(blank=True, null=True, verbose_name='模板描述')
    subject = models.CharField(max_length=50, verbose_name='科目')
    total_score = models.DecimalField(max_digits=5, decimal_places=1, default=100.0, verbose_name='总分')
    passing_score = models.DecimalField(max_digits=5, decimal_places=1, default=60.0, verbose_name='及格分数')
    duration = models.IntegerField(default=120, verbose_name='考试时长(分钟)')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_templates', verbose_name='创建人')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '试卷模板'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class PaperSection(models.Model):
    """试卷模板的试题部分"""
    template = models.ForeignKey(PaperTemplate, on_delete=models.CASCADE, related_name='sections', verbose_name='试卷模板')
    name = models.CharField(max_length=100, verbose_name='部分名称')
    description = models.TextField(blank=True, null=True, verbose_name='部分描述')
    question_type = models.ForeignKey(QuestionType, on_delete=models.CASCADE, verbose_name='题目类型')
    question_count = models.IntegerField(verbose_name='题目数量')
    score_per_question = models.DecimalField(max_digits=5, decimal_places=1, verbose_name='每题分数')
    order = models.IntegerField(default=0, verbose_name='排序')
    
    class Meta:
        verbose_name = '试卷部分'
        verbose_name_plural = verbose_name
        ordering = ['template', 'order']
    
    def __str__(self):
        return f"{self.template.name} - {self.name}"
    
    @property
    def total_score(self):
        return self.question_count * self.score_per_question


class SectionRule(models.Model):
    """试卷部分的抽题规则"""
    RULE_TYPES = (
        ('random', '随机抽取'),
        ('fixed', '固定题目'),
        ('difficulty', '按难度抽取'),
        ('knowledge', '按知识点抽取'),
    )
    
    section = models.ForeignKey(PaperSection, on_delete=models.CASCADE, related_name='rules', verbose_name='试卷部分')
    rule_type = models.CharField(max_length=20, choices=RULE_TYPES, verbose_name='规则类型')
    question_bank = models.ForeignKey(QuestionBank, on_delete=models.CASCADE, verbose_name='题库')
    question_count = models.IntegerField(verbose_name='题目数量')
    difficulty = models.ForeignKey(DifficultyLevel, on_delete=models.CASCADE, null=True, blank=True, verbose_name='难度级别')
    knowledge_points = models.TextField(blank=True, null=True, verbose_name='知识点IDs(逗号分隔)')
    
    class Meta:
        verbose_name = '抽题规则'
        verbose_name_plural = verbose_name
    
    def __str__(self):
        return f"{self.section.name} - {self.get_rule_type_display()}"


class Paper(models.Model):
    """试卷"""
    STATUS_CHOICES = (
        ('draft', '草稿'),
        ('published', '已发布'),
        ('archived', '已归档'),
    )
    
    title = models.CharField(max_length=100, verbose_name='试卷标题')
    description = models.TextField(blank=True, null=True, verbose_name='试卷描述')
    subject = models.CharField(max_length=50, verbose_name='科目')
    template = models.ForeignKey(PaperTemplate, on_delete=models.SET_NULL, null=True, blank=True, related_name='papers', verbose_name='试卷模板')
    total_score = models.DecimalField(max_digits=5, decimal_places=1, default=100.0, verbose_name='总分')
    passing_score = models.DecimalField(max_digits=5, decimal_places=1, default=60.0, verbose_name='及格分数')
    duration = models.IntegerField(default=120, verbose_name='考试时长(分钟)')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name='状态')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_papers', verbose_name='创建人')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    published_at = models.DateTimeField(null=True, blank=True, verbose_name='发布时间')
    
    class Meta:
        verbose_name = '试卷'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def publish(self):
        """发布试卷"""
        self.status = 'published'
        self.published_at = timezone.now()
        self.save(update_fields=['status', 'published_at'])
    
    def archive(self):
        """归档试卷"""
        self.status = 'archived'
        self.save(update_fields=['status'])


class PaperQuestion(models.Model):
    """试卷中的题目"""
    paper = models.ForeignKey(Paper, on_delete=models.CASCADE, related_name='questions', verbose_name='试卷')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name='题目')
    section_name = models.CharField(max_length=100, verbose_name='所属部分名称')
    order = models.IntegerField(verbose_name='题目序号')
    score = models.DecimalField(max_digits=5, decimal_places=1, verbose_name='分数')
    
    class Meta:
        verbose_name = '试卷题目'
        verbose_name_plural = verbose_name
        ordering = ['paper', 'order']
        unique_together = ['paper', 'question']
    
    def __str__(self):
        return f"{self.paper.title} - 第{self.order}题"


class PaperGeneration(models.Model):
    """试卷生成记录"""
    STATUS_CHOICES = (
        ('pending', '待处理'),
        ('processing', '处理中'),
        ('completed', '已完成'),
        ('failed', '失败'),
    )
    
    paper = models.ForeignKey(Paper, on_delete=models.CASCADE, related_name='generations', verbose_name='试卷')
    template = models.ForeignKey(PaperTemplate, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='试卷模板')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='创建人')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')
    error_message = models.TextField(blank=True, null=True, verbose_name='错误信息')
    
    class Meta:
        verbose_name = '试卷生成记录'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.paper.title} - {self.get_status_display()}"
