from django.db import models
from exams.models import Exam
from django.contrib.auth import get_user_model

User = get_user_model()

class ExamSession(models.Model):
    id = models.CharField(max_length=36, primary_key=True)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    last_active = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    screenshot_interval = models.PositiveIntegerField(default=30)
    screenshot_count = models.PositiveIntegerField(default=0)
    last_screenshot = models.DateTimeField(null=True, blank=True)
    warning_count = models.PositiveIntegerField(default=0)
    is_terminated = models.BooleanField(default=False)
    termination_reason = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'exam_sessions'
        unique_together = ('exam', 'user')
        indexes = [
            models.Index(fields=['user', 'exam']),
        ]
        ordering = ['-start_time']

    def __str__(self):
        return f"{self.user.username} - {self.exam.title}"