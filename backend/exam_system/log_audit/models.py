from django.db import models
from django.conf import settings

class Log(models.Model):
    """系统日志模型"""
    ACTION_TYPES = [
        ('login', '用户登录'),
        ('logout', '用户登出'),
        ('create', '创建操作'),
        ('update', '更新操作'),
        ('delete', '删除操作'),
        ('export', '导出操作'),
        ('import', '导入操作'),
        ('system', '系统事件'),
        ('error', '错误日志'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="操作用户"
    )
    action_time = models.DateTimeField(auto_now_add=True, verbose_name="操作时间")
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES, verbose_name="操作类型")
    target_model = models.CharField(max_length=100, blank=True, null=True, verbose_name="操作对象模型")
    target_id = models.PositiveIntegerField(blank=True, null=True, verbose_name="操作对象ID")
    description = models.TextField(verbose_name="操作内容")
    status = models.CharField(max_length=20, default='success', verbose_name="操作结果")
    ip_address = models.GenericIPAddressField(blank=True, null=True, verbose_name="IP地址")
    user_agent = models.CharField(max_length=255, blank=True, null=True, verbose_name="设备信息")

    class Meta:
        verbose_name = "系统日志"
        verbose_name_plural = verbose_name
        ordering = ['-action_time']

    def __str__(self):
        return f"{self.action_time} - {self.user} - {self.get_action_type_display()}"
