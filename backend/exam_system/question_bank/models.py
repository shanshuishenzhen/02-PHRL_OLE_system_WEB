from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

User = get_user_model()


class QuestionBank(models.Model):
    """题库"""
    name = models.CharField(_('题库名称'), max_length=100)
    subject = models.CharField(_('科目'), max_length=100)
    description = models.TextField(_('描述'), blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_question_banks',
                                  verbose_name=_('创建人'))
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    is_active = models.BooleanField(_('是否启用'), default=True)
    
    class Meta:
        verbose_name = _('题库')
        verbose_name_plural = _('题库')
        ordering = ['-created_at']
        unique_together = ['name', 'subject']
    
    def __str__(self):
        return f"{self.name} ({self.subject})"


class QuestionType(models.Model):
    """题目类型"""
    TYPE_CHOICES = (
        ('single_choice', '单选题'),
        ('multiple_choice', '多选题'),
        ('true_false', '判断题'),
        ('fill_blank', '填空题'),
        ('short_answer', '简答题'),
        ('programming', '编程题'),
    )
    
    name = models.CharField(_('类型名称'), max_length=50, choices=TYPE_CHOICES, unique=True)
    description = models.TextField(_('描述'), blank=True)
    
    class Meta:
        verbose_name = _('题目类型')
        verbose_name_plural = _('题目类型')
    
    def __str__(self):
        return self.get_name_display()


class DifficultyLevel(models.Model):
    """难度级别"""
    LEVEL_CHOICES = (
        (1, '简单'),
        (2, '较简单'),
        (3, '中等'),
        (4, '较难'),
        (5, '困难'),
    )
    
    level = models.PositiveSmallIntegerField(_('难度级别'), choices=LEVEL_CHOICES, unique=True)
    description = models.CharField(_('描述'), max_length=100, blank=True)
    
    class Meta:
        verbose_name = _('难度级别')
        verbose_name_plural = _('难度级别')
        ordering = ['level']
    
    def __str__(self):
        return self.get_level_display()


class KnowledgePoint(models.Model):
    """知识点"""
    name = models.CharField(_('知识点名称'), max_length=100)
    subject = models.CharField(_('所属科目'), max_length=100)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                              related_name='children', verbose_name=_('父级知识点'))
    description = models.TextField(_('描述'), blank=True)
    
    class Meta:
        verbose_name = _('知识点')
        verbose_name_plural = _('知识点')
        unique_together = ['name', 'subject', 'parent']
    
    def __str__(self):
        if self.parent:
            return f"{self.parent} > {self.name}"
        return self.name


class Question(models.Model):
    """题目"""
    question_bank = models.ForeignKey(QuestionBank, on_delete=models.CASCADE, related_name='questions',
                                     verbose_name=_('所属题库'))
    question_type = models.ForeignKey(QuestionType, on_delete=models.PROTECT, related_name='questions',
                                     verbose_name=_('题目类型'))
    difficulty = models.ForeignKey(DifficultyLevel, on_delete=models.PROTECT, related_name='questions',
                                  verbose_name=_('难度级别'))
    knowledge_points = models.ManyToManyField(KnowledgePoint, related_name='questions',
                                            verbose_name=_('知识点'))
    content = models.TextField(_('题目内容'))
    answer = models.TextField(_('参考答案'))
    analysis = models.TextField(_('解析'), blank=True)
    score = models.PositiveSmallIntegerField(_('分值'), default=1)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_questions',
                                  verbose_name=_('创建人'))
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    is_active = models.BooleanField(_('是否启用'), default=True)
    
    class Meta:
        verbose_name = _('题目')
        verbose_name_plural = _('题目')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.question_type} - {self.content[:30]}..."


class QuestionOption(models.Model):
    """题目选项"""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options',
                                verbose_name=_('所属题目'))
    option_key = models.CharField(_('选项键'), max_length=10)  # A, B, C, D...
    option_content = models.TextField(_('选项内容'))
    is_correct = models.BooleanField(_('是否正确答案'), default=False)
    
    class Meta:
        verbose_name = _('题目选项')
        verbose_name_plural = _('题目选项')
        ordering = ['option_key']
        unique_together = ['question', 'option_key']
    
    def __str__(self):
        return f"{self.question} - {self.option_key}"


class QuestionImage(models.Model):
    """题目图片"""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='images',
                                verbose_name=_('所属题目'))
    image = models.ImageField(_('图片'), upload_to='question_images/')
    description = models.CharField(_('描述'), max_length=255, blank=True)
    
    class Meta:
        verbose_name = _('题目图片')
        verbose_name_plural = _('题目图片')
    
    def __str__(self):
        return f"{self.question} - {self.description or '图片'}"


class QuestionImport(models.Model):
    """题目导入记录"""
    STATUS_CHOICES = (
        ('pending', '待处理'),
        ('processing', '处理中'),
        ('completed', '已完成'),
        ('failed', '失败'),
    )
    
    question_bank = models.ForeignKey(QuestionBank, on_delete=models.CASCADE, related_name='imports',
                                     verbose_name=_('目标题库'))
    file = models.FileField(_('导入文件'), upload_to='question_imports/')
    status = models.CharField(_('状态'), max_length=20, choices=STATUS_CHOICES, default='pending')
    total_count = models.PositiveIntegerField(_('总题目数'), default=0)
    success_count = models.PositiveIntegerField(_('成功导入数'), default=0)
    error_message = models.TextField(_('错误信息'), blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='question_imports',
                                  verbose_name=_('创建人'))
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    completed_at = models.DateTimeField(_('完成时间'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('题目导入')
        verbose_name_plural = _('题目导入')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.question_bank} - {self.created_at}"
