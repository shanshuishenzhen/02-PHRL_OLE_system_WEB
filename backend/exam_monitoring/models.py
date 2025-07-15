from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class ExamSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    exam_id = models.CharField(max_length=100)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    answers = models.JSONField(default=dict)
    is_completed = models.BooleanField(default=False)
    status = models.CharField(max_length=20, default='in_progress')
    remaining_time = models.IntegerField(default=3600)  # 默认1小时
    is_cheating = models.BooleanField(default=False)

    class Meta:
        app_label = 'exam_monitoring'
        verbose_name = '考试会话'
        verbose_name_plural = '考试会话'

    def __str__(self):
        return f"{self.user.username} - {self.exam_id}"