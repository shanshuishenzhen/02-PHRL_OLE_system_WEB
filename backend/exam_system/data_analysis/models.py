from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from exam_system.user_management.models import User, Class, Department
from exam_system.exam_monitoring.models import Exam
from exam_system.paper_management.models import Paper, PaperQuestion
from exam_system.question_bank.models import Question, QuestionType, KnowledgePoint


class AnalysisTask(models.Model):
    """分析任务"""
    STATUS_CHOICES = (
        ('pending', '待处理'),
        ('processing', '处理中'),
        ('completed', '已完成'),
        ('failed', '失败'),
    )
    
    TYPE_CHOICES = (
        ('exam', '考试分析'),
        ('student', '学生分析'),
        ('question', '题目分析'),
        ('knowledge', '知识点分析'),
        ('class', '班级分析'),
        ('department', '院系分析'),
        ('custom', '自定义分析'),
    )
    
    name = models.CharField(max_length=100, verbose_name='任务名称')
    task_type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name='任务类型')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='analysis_tasks', verbose_name='创建人')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')
    parameters = models.JSONField(default=dict, verbose_name='参数')
    result_summary = models.TextField(blank=True, null=True, verbose_name='结果摘要')
    error_message = models.TextField(blank=True, null=True, verbose_name='错误信息')
    
    class Meta:
        verbose_name = '分析任务'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class ExamAnalysis(models.Model):
    """考试分析"""
    task = models.OneToOneField(AnalysisTask, on_delete=models.CASCADE, related_name='exam_analysis', verbose_name='分析任务')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='analyses', verbose_name='考试')
    total_students = models.IntegerField(default=0, verbose_name='总人数')
    attendance_count = models.IntegerField(default=0, verbose_name='出勤人数')
    attendance_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='出勤率')
    pass_count = models.IntegerField(default=0, verbose_name='及格人数')
    pass_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='及格率')
    average_score = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, verbose_name='平均分')
    highest_score = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, verbose_name='最高分')
    lowest_score = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, verbose_name='最低分')
    median_score = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, verbose_name='中位数')
    standard_deviation = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='标准差')
    difficulty_index = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='难度指数')
    discrimination_index = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='区分度指数')
    reliability_coefficient = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='信度系数')
    score_distribution = models.JSONField(default=dict, verbose_name='分数分布')
    question_analysis = models.JSONField(default=dict, verbose_name='题目分析')
    knowledge_point_analysis = models.JSONField(default=dict, verbose_name='知识点分析')
    class_comparison = models.JSONField(default=dict, verbose_name='班级对比')
    department_comparison = models.JSONField(default=dict, verbose_name='院系对比')
    time_spent_analysis = models.JSONField(default=dict, verbose_name='答题时间分析')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '考试分析'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.exam.name} - 分析"


class StudentAnalysis(models.Model):
    """学生分析"""
    task = models.OneToOneField(AnalysisTask, on_delete=models.CASCADE, related_name='student_analysis', verbose_name='分析任务')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='analyses', verbose_name='学生')
    exam_count = models.IntegerField(default=0, verbose_name='考试次数')
    attendance_count = models.IntegerField(default=0, verbose_name='出勤次数')
    attendance_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='出勤率')
    pass_count = models.IntegerField(default=0, verbose_name='及格次数')
    pass_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='及格率')
    average_score = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, verbose_name='平均分')
    highest_score = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, verbose_name='最高分')
    lowest_score = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, verbose_name='最低分')
    score_trend = models.JSONField(default=dict, verbose_name='分数趋势')
    knowledge_point_mastery = models.JSONField(default=dict, verbose_name='知识点掌握情况')
    question_type_performance = models.JSONField(default=dict, verbose_name='题型表现')
    time_spent_analysis = models.JSONField(default=dict, verbose_name='答题时间分析')
    error_pattern_analysis = models.JSONField(default=dict, verbose_name='错误模式分析')
    improvement_suggestions = models.TextField(blank=True, null=True, verbose_name='改进建议')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '学生分析'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.student.username} - 分析"


class QuestionAnalysis(models.Model):
    """题目分析"""
    task = models.OneToOneField(AnalysisTask, on_delete=models.CASCADE, related_name='question_analysis', verbose_name='分析任务')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='analyses', verbose_name='题目')
    usage_count = models.IntegerField(default=0, verbose_name='使用次数')
    correct_count = models.IntegerField(default=0, verbose_name='正确次数')
    correct_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='正确率')
    average_score = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, verbose_name='平均得分')
    difficulty_index = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='难度指数')
    discrimination_index = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='区分度指数')
    average_time_spent = models.IntegerField(null=True, blank=True, verbose_name='平均答题时间(秒)')
    option_distribution = models.JSONField(default=dict, verbose_name='选项分布')
    class_performance = models.JSONField(default=dict, verbose_name='班级表现')
    department_performance = models.JSONField(default=dict, verbose_name='院系表现')
    common_errors = models.TextField(blank=True, null=True, verbose_name='常见错误')
    improvement_suggestions = models.TextField(blank=True, null=True, verbose_name='改进建议')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '题目分析'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
    
    def __str__(self):
        return f"题目{self.question.id} - 分析"


class KnowledgePointAnalysis(models.Model):
    """知识点分析"""
    task = models.OneToOneField(AnalysisTask, on_delete=models.CASCADE, related_name='knowledge_point_analysis', verbose_name='分析任务')
    knowledge_point = models.ForeignKey(KnowledgePoint, on_delete=models.CASCADE, related_name='analyses', verbose_name='知识点')
    question_count = models.IntegerField(default=0, verbose_name='题目数量')
    usage_count = models.IntegerField(default=0, verbose_name='使用次数')
    correct_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='正确率')
    average_score = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, verbose_name='平均得分')
    difficulty_index = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='难度指数')
    mastery_distribution = models.JSONField(default=dict, verbose_name='掌握程度分布')
    class_performance = models.JSONField(default=dict, verbose_name='班级表现')
    department_performance = models.JSONField(default=dict, verbose_name='院系表现')
    related_knowledge_points = models.JSONField(default=dict, verbose_name='相关知识点表现')
    improvement_suggestions = models.TextField(blank=True, null=True, verbose_name='改进建议')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '知识点分析'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.knowledge_point.name} - 分析"


class ClassAnalysis(models.Model):
    """班级分析"""
    task = models.OneToOneField(AnalysisTask, on_delete=models.CASCADE, related_name='class_analysis', verbose_name='分析任务')
    class_obj = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='analyses', verbose_name='班级')
    student_count = models.IntegerField(default=0, verbose_name='学生数量')
    exam_count = models.IntegerField(default=0, verbose_name='考试次数')
    average_attendance_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='平均出勤率')
    average_pass_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='平均及格率')
    average_score = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, verbose_name='平均分')
    score_distribution = models.JSONField(default=dict, verbose_name='分数分布')
    knowledge_point_mastery = models.JSONField(default=dict, verbose_name='知识点掌握情况')
    question_type_performance = models.JSONField(default=dict, verbose_name='题型表现')
    student_ranking = models.JSONField(default=dict, verbose_name='学生排名')
    performance_trend = models.JSONField(default=dict, verbose_name='表现趋势')
    comparison_with_other_classes = models.JSONField(default=dict, verbose_name='与其他班级对比')
    improvement_suggestions = models.TextField(blank=True, null=True, verbose_name='改进建议')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '班级分析'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.class_obj.name} - 分析"


class DepartmentAnalysis(models.Model):
    """院系分析"""
    task = models.OneToOneField(AnalysisTask, on_delete=models.CASCADE, related_name='department_analysis', verbose_name='分析任务')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='analyses', verbose_name='院系')
    class_count = models.IntegerField(default=0, verbose_name='班级数量')
    student_count = models.IntegerField(default=0, verbose_name='学生数量')
    exam_count = models.IntegerField(default=0, verbose_name='考试次数')
    average_attendance_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='平均出勤率')
    average_pass_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='平均及格率')
    average_score = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, verbose_name='平均分')
    score_distribution = models.JSONField(default=dict, verbose_name='分数分布')
    knowledge_point_mastery = models.JSONField(default=dict, verbose_name='知识点掌握情况')
    question_type_performance = models.JSONField(default=dict, verbose_name='题型表现')
    class_ranking = models.JSONField(default=dict, verbose_name='班级排名')
    student_ranking = models.JSONField(default=dict, verbose_name='学生排名')
    performance_trend = models.JSONField(default=dict, verbose_name='表现趋势')
    comparison_with_other_departments = models.JSONField(default=dict, verbose_name='与其他院系对比')
    improvement_suggestions = models.TextField(blank=True, null=True, verbose_name='改进建议')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '院系分析'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.department.name} - 分析"


class AnalysisReport(models.Model):
    """分析报告"""
    task = models.OneToOneField(AnalysisTask, on_delete=models.CASCADE, related_name='report', verbose_name='分析任务')
    title = models.CharField(max_length=100, verbose_name='报告标题')
    summary = models.TextField(verbose_name='报告摘要')
    content = models.TextField(verbose_name='报告内容')
    charts = models.JSONField(default=dict, verbose_name='图表数据')
    tables = models.JSONField(default=dict, verbose_name='表格数据')
    recommendations = models.TextField(blank=True, null=True, verbose_name='建议')
    is_public = models.BooleanField(default=False, verbose_name='是否公开')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '分析报告'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title


class AnalysisTemplate(models.Model):
    """分析模板"""
    name = models.CharField(max_length=100, verbose_name='模板名称')
    description = models.TextField(blank=True, null=True, verbose_name='模板描述')
    task_type = models.CharField(max_length=20, choices=AnalysisTask.TYPE_CHOICES, verbose_name='任务类型')
    parameters = models.JSONField(default=dict, verbose_name='参数模板')
    report_template = models.TextField(blank=True, null=True, verbose_name='报告模板')
    is_system = models.BooleanField(default=False, verbose_name='是否系统模板')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='analysis_templates', verbose_name='创建人')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '分析模板'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
