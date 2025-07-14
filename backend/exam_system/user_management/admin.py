from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, LoginLog


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """用户管理"""
    list_display = ('username', 'email', 'real_name', 'role', 'department', 'is_active', 'date_joined', 'last_login')
    list_filter = ('role', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'email', 'real_name', 'department')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('个人信息'), {'fields': ('email', 'real_name', 'role', 'department', 'phone', 'avatar')}),
        (_('权限'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('重要日期'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'real_name', 'role', 'department'),
        }),
    )


@admin.register(LoginLog)
class LoginLogAdmin(admin.ModelAdmin):
    """登录日志管理"""
    list_display = ('user', 'ip_address', 'login_time', 'login_status', 'login_message')
    list_filter = ('login_status', 'login_time')
    search_fields = ('user__username', 'user__real_name', 'ip_address')
    ordering = ('-login_time',)
    readonly_fields = ('user', 'ip_address', 'user_agent', 'login_time', 'login_status', 'login_message')
