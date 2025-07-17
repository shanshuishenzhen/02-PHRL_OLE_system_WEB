from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.translation import gettext_lazy as _


class Department(models.Model):
    """部门/班级模型"""
    name = models.CharField(_('名称'), max_length=100)
    description = models.TextField(_('描述'), blank=True)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('部门/班级')
        verbose_name_plural = _('部门/班级')
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Class(models.Model):
    """班级模型"""
    name = models.CharField(_('班级名称'), max_length=100)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='classes', verbose_name=_('所属部门'))
    teacher = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, blank=True, related_name='teaching_classes', verbose_name=_('班主任'))
    description = models.TextField(_('描述'), blank=True)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('班级')
        verbose_name_plural = _('班级')
        ordering = ['name']
    
    def __str__(self):
        return self.name


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
        # 强制设置超级管理员用户名为 phrladmin
        username = 'phrladmin'
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', '超级管理员')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('超级用户必须设置is_staff=True'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('超级用户必须设置is_superuser=True'))
            
        return self.create_user(username, email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """用户模型"""
    ROLE_CHOICES = (
        ('超级管理员', '超级管理员'),  # 系统内置隐含
        ('管理员', '管理员'),      # 系统配置
        ('teacher', '考评员'),     # 考场管理
        ('student', '考生'),      # 参加考试
    )
    
    username = models.CharField(_('用户名'), max_length=150, unique=True)
    email = models.EmailField(_('邮箱'), unique=True)
    real_name = models.CharField(_('真实姓名'), max_length=50, blank=True)
    role = models.CharField(_('角色'), max_length=20, choices=ROLE_CHOICES, default='student')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='users', verbose_name=_('部门'))
    class_info = models.ForeignKey(Class, on_delete=models.SET_NULL, null=True, blank=True, related_name='students', verbose_name=_('班级'))
    phone = models.CharField(_('手机号'), max_length=20, blank=True)
    avatar = models.ImageField(_('头像'), upload_to='avatars/', null=True, blank=True)
    last_login_ip = models.GenericIPAddressField(_('最后登录IP'), null=True, blank=True)
    is_active = models.BooleanField(_('是否激活'), default=True)
    is_staff = models.BooleanField(_('是否员工'), default=False)
    date_joined = models.DateTimeField(_('加入时间'), auto_now_add=True)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']
    
    objects = UserManager()
    
    class Meta:
        verbose_name = _('用户')
        verbose_name_plural = _('用户')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    @property
    def is_admin(self):
        return self.role in ['超级管理员', '管理员']
    
    @property
    def is_teacher(self):
        return self.role == 'teacher'
    
    @property
    def is_student(self):
        return self.role == 'student'


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
