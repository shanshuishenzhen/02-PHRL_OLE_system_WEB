from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.utils.translation import gettext_lazy as _
from .models import LoginLog, Department, Class

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """用户序列化器"""
    password = serializers.CharField(write_only=True, required=False)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    class_name = serializers.CharField(source='class_info.name', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'real_name', 'role', 'role_display',
                 'department', 'department_name', 'class_info', 'class_name', 'phone', 'avatar', 
                 'is_active', 'date_joined', 'last_login', 'last_login_ip', 'created_at', 'updated_at']
        read_only_fields = ['id', 'date_joined', 'last_login', 'last_login_ip', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user


class UserCreateSerializer(serializers.ModelSerializer):
    """用户创建序列化器"""
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'real_name', 'role',
                 'department', 'class_info', 'phone', 'avatar']
    
    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password_confirm'):
            raise serializers.ValidationError({'password_confirm': _('两次密码输入不一致')})
        return attrs
    
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            real_name=validated_data.get('real_name', ''),
            role=validated_data.get('role', 'student'),
            department=validated_data.get('department', None),
            class_info=validated_data.get('class_info', None),
            phone=validated_data.get('phone', ''),
            avatar=validated_data.get('avatar', None)
        )
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """用户更新序列化器"""
    class Meta:
        model = User
        fields = ['email', 'real_name', 'department', 'class_info', 'phone', 'avatar']


class PasswordChangeSerializer(serializers.Serializer):
    """密码修改序列化器"""
    old_password = serializers.CharField(required=True, style={'input_type': 'password'})
    new_password = serializers.CharField(required=True, style={'input_type': 'password'})
    new_password_confirm = serializers.CharField(required=True, style={'input_type': 'password'})
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(_('原密码不正确'))
        return value
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({'new_password_confirm': _('两次密码输入不一致')})
        return attrs
    
    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    """登录序列化器"""
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, style={'input_type': 'password'}, write_only=True)
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            # 尝试使用用户名登录
            user = authenticate(request=self.context.get('request'), username=username, password=password)
            
            # 如果用户名登录失败，尝试使用邮箱登录
            if not user:
                try:
                    user_obj = User.objects.get(email=username)
                    user = authenticate(request=self.context.get('request'), username=user_obj.username, password=password)
                except User.DoesNotExist:
                    user = None
            
            if not user:
                msg = _('无法使用提供的凭据登录')
                raise serializers.ValidationError(msg, code='authorization')
            
            if not user.is_active:
                raise serializers.ValidationError(_('用户账号已被禁用'), code='authorization')
        else:
            msg = _('必须包含用户名和密码')
            raise serializers.ValidationError(msg, code='authorization')
        
        attrs['user'] = user
        return attrs


class LoginLogSerializer(serializers.ModelSerializer):
    """登录日志序列化器"""
    username = serializers.CharField(source='user.username', read_only=True)
    real_name = serializers.CharField(source='user.real_name', read_only=True)
    
    class Meta:
        model = LoginLog
        fields = ['id', 'username', 'real_name', 'ip_address', 'user_agent',
                 'login_time', 'login_status', 'login_message']
        read_only_fields = fields


class DepartmentSerializer(serializers.ModelSerializer):
    """部门序列化器"""
    
    class Meta:
        model = Department
        fields = ['id', 'name', 'description', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ClassSerializer(serializers.ModelSerializer):
    """班级序列化器"""
    department_name = serializers.CharField(source='department.name', read_only=True)
    teacher_name = serializers.CharField(source='teacher.real_name', read_only=True)
    
    class Meta:
        model = Class
        fields = ['id', 'name', 'department', 'department_name', 'teacher', 'teacher_name', 
                 'description', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
