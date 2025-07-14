from django.apps import AppConfig


class LogAuditConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'exam_system.log_audit'
    verbose_name = '日志审计'