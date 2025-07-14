from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """自定义用户管理器"""
    
    def create_user(self, username, email, password=None, **extra_fields):
        """创建普通用户"""
        if not username:
            raise ValueError(_('用户名不能为空'))
        if not email:
            raise ValueError(_('邮箱不能为空'))
            
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, email, password=None, **extra_fields):
        """创建超级管理员"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'admin')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('超级用户必须设置is_staff=True'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('超级用户必须设置is_superuser=True'))
            
        return self.create_user(username, email, password, **extra_fields)


class User(AbstractUser):
    """用户模型"""
    ROLE_CHOICES = (
        ('admin', '管理员'),
        ('teacher', '教师'),
        ('student', '学生'),
        ('marker', '阅卷员'),
    )
    
    email = models.EmailField(_('邮箱'), unique=True)
    real_name = models.CharField(_('真实姓名'), max_length=50, blank=True)
    role = models.CharField(_('角色'), max_length=20, choices=ROLE_CHOICES, default='student')
    department = models.CharField(_('部门/班级'), max_length=100, blank=True)
    phone = models.CharField(_('手机号'), max_length=20, blank=True)
    avatar = models.ImageField(_('头像'), upload_to='avatars/', null=True, blank=True)
    last_login_ip = models.GenericIPAddressField(_('最后登录IP'), null=True, blank=True)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    objects = UserManager()
    
    class Meta:
        verbose_name = _('用户')
        verbose_name_plural = _('用户')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    @property
    def is_admin(self):
        return self.role == 'admin'
    
    @property
    def is_teacher(self):
        return self.role == 'teacher'
    
    @property
    def is_student(self):
        return self.role == 'student'
    
    @property
    def is_marker(self):
        return self.role == 'marker'


class LoginLog(models.Model):
    """登录日志"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_logs', verbose_name=_('用户'))
    ip_address = models.GenericIPAddressField(_('IP地址'))
    user_agent = models.TextField(_('用户代理'), blank=True)
    login_time = models.DateTimeField(_('登录时间'), auto_now_add=True)
    login_status = models.BooleanField(_('登录状态'), default=True)
    login_message = models.CharField(_('登录消息'), max_length=255, blank=True)
    
    class Meta:
        verbose_name = _('登录日志')
        verbose_name_plural = _('登录日志')
        ordering = ['-login_time']
    
    def __str__(self):
        return f"{self.user.username} - {self.login_time}"
