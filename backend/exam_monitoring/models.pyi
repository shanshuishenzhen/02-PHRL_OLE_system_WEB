from typing import Literal, Dict, Any, Optional
from django.db import models
from django.contrib.auth import get_user_model
from datetime import datetime

User = get_user_model()

class ExamSession(models.Model):
    id: int
    exam_id: str
    exam: Any  # ForeignKey to Exam
    user: Any  # ForeignKey to User
    status: Literal['pending', 'in_progress', 'submitted', 'violation']
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    answers: Dict[str, Any]
    is_completed: bool
    remaining_time: int
    is_cheating: bool
    created_at: datetime
    updated_at: datetime

    def __str__(self) -> str: ...
    def refresh_from_db(self, using=None, fields=None) -> None: ...