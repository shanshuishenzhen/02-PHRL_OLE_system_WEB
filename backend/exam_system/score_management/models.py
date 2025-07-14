from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from exam_system.user_management.models import User
from exam_system.exam_monitoring.models import Exam, ExamRecord, ExamAnswer
from exam_system.paper_management.models import Paper, PaperQuestion


class ScoringCriteria(models.Model):
    """评分标准"""
    name = models.CharField(max_length=100, verbose_name='标准名称')
    description = models.TextField(blank=True, null=True, verbose_name='标准描述')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_criteria', verbose_name='创建人')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '评分标准'
        verbose_name_plural = verbose_name
        ordering = ['name']
    
    def __str__(self):
        return self.name


class ScoringRule(models.Model):
    """评分规则"""
    criteria = models.ForeignKey(ScoringCriteria, on_delete=models.CASCADE, related_name='rules', verbose_name='评分标准')
    question_type = models.CharField(max_length=50, verbose_name='题目类型')
    full_score = models.DecimalField(max_digits=5, decimal_places=1, verbose_name='满分')
    partial_score_allowed = models.BooleanField(default=True, verbose_name='允许部分得分')
    auto_score = models.BooleanField(default=True, verbose_name='自动评分')
    score_per_point = models.DecimalField(max_digits=5, decimal_places=1, default=1.0, verbose_name='每点得分')
    description = models.TextField(blank=True, null=True, verbose_name='规则描述')
    
    class Meta:
        verbose_name = '评分规则'
        verbose_name_plural = verbose_name
        ordering = ['criteria', 'question_type']
        unique_together = ['criteria', 'question_type']
    
    def __str__(self):
        return f"{self.criteria.name} - {self.question_type}"


class ScoreSheet(models.Model):
    """评分表"""
    STATUS_CHOICES = (
        ('pending', '待评分'),
        ('in_progress', '评分中'),
        ('completed', '已完成'),
        ('reviewed', '已复核'),
    )
    
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='score_sheets', verbose_name='考试')
    exam_record = models.OneToOneField(ExamRecord, on_delete=models.CASCADE, related_name='score_sheet', verbose_name='考试记录')
    criteria = models.ForeignKey(ScoringCriteria, on_delete=models.SET_NULL, null=True, related_name='score_sheets', verbose_name='评分标准')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    total_score = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, verbose_name='总分')
    passing_score = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, verbose_name='及格分数')
    is_passed = models.BooleanField(null=True, blank=True, verbose_name='是否及格')
    marker = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='marked_sheets', verbose_name='评分人')
    marked_at = models.DateTimeField(null=True, blank=True, verbose_name='评分时间')
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_sheets', verbose_name='复核人')
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name='复核时间')
    comments = models.TextField(blank=True, null=True, verbose_name='评语')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '评分表'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.exam_record.student.username} - {self.exam.name}"
    
    def calculate_total_score(self):
        """计算总分"""
        total = sum(item.score for item in self.score_items.all() if item.score is not None)
        self.total_score = total
        
        # 判断是否及格
        if self.passing_score is not None:
            self.is_passed = total >= self.passing_score
        
        self.save(update_fields=['total_score', 'is_passed'])
        
        # 同步到考试记录
        self.exam_record.score = total
        self.exam_record.is_passed = self.is_passed
        self.exam_record.save(update_fields=['score', 'is_passed'])
        
        return total


class ScoreItem(models.Model):
    """评分项"""
    score_sheet = models.ForeignKey(ScoreSheet, on_delete=models.CASCADE, related_name='score_items', verbose_name='评分表')
    question = models.ForeignKey(PaperQuestion, on_delete=models.CASCADE, related_name='score_items', verbose_name='试题')
    answer = models.ForeignKey(ExamAnswer, on_delete=models.CASCADE, related_name='score_items', verbose_name='答案')
    score = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, verbose_name='得分')
    max_score = models.DecimalField(max_digits=5, decimal_places=1, verbose_name='满分')
    auto_scored = models.BooleanField(default=False, verbose_name='是否自动评分')
    marker = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='marked_items', verbose_name='评分人')
    marked_at = models.DateTimeField(null=True, blank=True, verbose_name='评分时间')
    comments = models.TextField(blank=True, null=True, verbose_name='评语')
    
    class Meta:
        verbose_name = '评分项'
        verbose_name_plural = verbose_name
        ordering = ['score_sheet', 'question__order']
        unique_together = ['score_sheet', 'question']
    
    def __str__(self):
        return f"{self.score_sheet} - 题目{self.question.order}"


class ScoreDistribution(models.Model):
    """分数分布"""
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='score_distributions', verbose_name='考试')
    score_range_min = models.DecimalField(max_digits=5, decimal_places=1, verbose_name='分数范围最小值')
    score_range_max = models.DecimalField(max_digits=5, decimal_places=1, verbose_name='分数范围最大值')
    count = models.IntegerField(default=0, verbose_name='人数')
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='百分比')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '分数分布'
        verbose_name_plural = verbose_name
        ordering = ['exam', 'score_range_min']
        unique_together = ['exam', 'score_range_min', 'score_range_max']
    
    def __str__(self):
        return f"{self.exam.name} - {self.score_range_min}-{self.score_range_max}"


class ScoreStatistics(models.Model):
    """分数统计"""
    exam = models.OneToOneField(Exam, on_delete=models.CASCADE, related_name='score_statistics', verbose_name='考试')
    total_students = models.IntegerField(default=0, verbose_name='总人数')
    scored_students = models.IntegerField(default=0, verbose_name='已评分人数')
    passed_students = models.IntegerField(default=0, verbose_name='及格人数')
    pass_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='及格率')
    highest_score = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, verbose_name='最高分')
    lowest_score = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, verbose_name='最低分')
    average_score = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, verbose_name='平均分')
    median_score = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, verbose_name='中位数')
    standard_deviation = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='标准差')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '分数统计'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.exam.name} - 统计"
    
    def update_statistics(self):
        """更新统计数据"""
        from django.db.models import Avg, Max, Min, StdDev, Count, Q
        from statistics import median
        
        # 获取所有已评分的考试记录
        scored_records = ExamRecord.objects.filter(
            exam=self.exam, 
            status='submitted',
            score__isnull=False
        )
        
        # 总人数和已评分人数
        self.total_students = ExamRecord.objects.filter(exam=self.exam).count()
        self.scored_students = scored_records.count()
        
        if self.scored_students > 0:
            # 及格人数和及格率
            self.passed_students = scored_records.filter(is_passed=True).count()
            self.pass_rate = (self.passed_students / self.scored_students * 100) if self.scored_students > 0 else 0
            
            # 最高分、最低分、平均分
            stats = scored_records.aggregate(
                highest=Max('score'),
                lowest=Min('score'),
                average=Avg('score'),
                std_dev=StdDev('score')
            )
            
            self.highest_score = stats['highest']
            self.lowest_score = stats['lowest']
            self.average_score = stats['average']
            self.standard_deviation = stats['std_dev']
            
            # 中位数
            scores = list(scored_records.values_list('score', flat=True))
            if scores:
                self.median_score = median(scores)
        
        self.save()
        
        # 更新分数分布
        self.update_score_distribution()
        
        return self
    
    def update_score_distribution(self):
        """更新分数分布"""
        from django.db.models import Count, F
        
        # 清除旧的分布数据
        ScoreDistribution.objects.filter(exam=self.exam).delete()
        
        # 定义分数区间
        ranges = [
            (0, 60), (60, 70), (70, 80), (80, 90), (90, 100), (100, 100.1)
        ]
        
        # 获取所有已评分的考试记录
        scored_records = ExamRecord.objects.filter(
            exam=self.exam, 
            status='submitted',
            score__isnull=False
        )
        
        total_count = scored_records.count()
        
        # 创建新的分布数据
        for min_score, max_score in ranges:
            if min_score == 100 and max_score == 100.1:  # 处理满分情况
                count = scored_records.filter(score=100).count()
            else:
                count = scored_records.filter(score__gte=min_score, score__lt=max_score).count()
            
            percentage = (count / total_count * 100) if total_count > 0 else 0
            
            ScoreDistribution.objects.create(
                exam=self.exam,
                score_range_min=min_score,
                score_range_max=max_score,
                count=count,
                percentage=percentage
            )
        
        return True


class ScoreAppeal(models.Model):
    """分数申诉"""
    STATUS_CHOICES = (
        ('pending', '待处理'),
        ('processing', '处理中'),
        ('approved', '已通过'),
        ('rejected', '已拒绝'),
        ('cancelled', '已取消'),
    )
    
    score_item = models.ForeignKey(ScoreItem, on_delete=models.CASCADE, related_name='appeals', verbose_name='评分项')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='score_appeals', verbose_name='学生')
    reason = models.TextField(verbose_name='申诉理由')
    expected_score = models.DecimalField(max_digits=5, decimal_places=1, verbose_name='期望分数')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    handler = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='handled_appeals', verbose_name='处理人')
    handled_at = models.DateTimeField(null=True, blank=True, verbose_name='处理时间')
    response = models.TextField(blank=True, null=True, verbose_name='处理回复')
    original_score = models.DecimalField(max_digits=5, decimal_places=1, verbose_name='原始分数')
    adjusted_score = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, verbose_name='调整后分数')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '分数申诉'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.student.username} - {self.score_item}"
    
    def save(self, *args, **kwargs):
        # 保存原始分数
        if not self.pk and self.score_item and self.score_item.score is not None:
            self.original_score = self.score_item.score
        super().save(*args, **kwargs)
