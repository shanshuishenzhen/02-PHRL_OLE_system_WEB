from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from .models import LoginLog, Department, Class
from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    PasswordChangeSerializer, LoginSerializer, LoginLogSerializer,
    DepartmentSerializer, ClassSerializer
)
from .authentication import JWTAuthentication
from .permissions import IsAdminUser, IsSelfOrAdmin

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """用户视图集"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['role', 'department', 'is_active']
    search_fields = ['username', 'email', 'real_name', 'department']
    ordering_fields = ['id', 'username', 'date_joined', 'last_login']
    ordering = ['-date_joined']
    
    def get_queryset(self):
        """过滤掉超级管理员用户，并根据角色过滤"""
        queryset = super().get_queryset()
        # 先过滤掉超级管理员用户
        queryset = queryset.filter(is_superuser=False)
        # 再过滤掉角色为超级管理员的用户
        queryset = queryset.exclude(role='超级管理员')
        # 最后过滤掉admin用户
        queryset = queryset.exclude(username='admin')
        # 根据请求参数中的角色进行过滤
        role = self.request.query_params.getlist('role')
        if role:
            queryset = queryset.filter(role__in=role)
        return queryset

class LauncherUserViewSet(UserViewSet):
    """启动器专用用户视图集"""
    def get_queryset(self):
        """不过滤admin用户"""
        queryset = super(UserViewSet, self).get_queryset()
        # 根据请求参数中的角色进行过滤
        role = self.request.query_params.getlist('role')
        if role:
            queryset = queryset.filter(role__in=role)
        return queryset
    
    def get_permissions(self):
        """根据不同的操作设置不同的权限"""
        if self.action in ['create', 'list', 'destroy']:
            permission_classes = [IsAdminUser]
        elif self.action in ['retrieve', 'update', 'partial_update', 'change_password']:
            permission_classes = [IsSelfOrAdmin]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        """根据不同的操作返回不同的序列化器"""
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        elif self.action == 'change_password':
            return PasswordChangeSerializer
        return UserSerializer
    
    @action(detail=True, methods=['post'])
    def change_password(self, request, pk=None):
        """修改密码"""
        user = self.get_object()
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'detail': _('密码修改成功')}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """获取当前用户信息"""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class AuthViewSet(viewsets.ViewSet):
    """认证视图集"""
    permission_classes = [permissions.AllowAny]
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        """用户登录"""
        serializer = LoginSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # 记录登录IP
            ip_address = self.get_client_ip(request)
            user.last_login_ip = ip_address
            user.save(update_fields=['last_login_ip'])
            
            # 记录登录日志
            LoginLog.objects.create(
                user=user,
                ip_address=ip_address,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                login_status=True,
                login_message='登录成功'
            )
            
            # 生成JWT令牌
            tokens = JWTAuthentication.generate_token(user)
            
            return Response({
                'user': UserSerializer(user).data,
                'tokens': tokens
            })
        
        # 记录登录失败日志
        try:
            username = request.data.get('username', '')
            user = User.objects.filter(username=username).first() or User.objects.filter(email=username).first()
            if user:
                LoginLog.objects.create(
                    user=user,
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    login_status=False,
                    login_message='密码错误'
                )
        except Exception:
            pass
            
        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)
    
    @action(detail=False, methods=['post'])
    def refresh(self, request):
        """刷新令牌"""
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'detail': _('刷新令牌不能为空')}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            tokens = JWTAuthentication.refresh_token(refresh_token)
            return Response(tokens)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
    
    @action(detail=False, methods=['post'])
    def logout(self, request):
        """用户登出"""
        # JWT无状态，客户端只需删除令牌
        return Response({'detail': _('登出成功')})
    
    def get_client_ip(self, request):
        """获取客户端IP地址"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class LoginLogViewSet(viewsets.ReadOnlyModelViewSet):
    """登录日志视图集"""
    queryset = LoginLog.objects.all()
    serializer_class = LoginLogSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['login_status', 'user']
    search_fields = ['user__username', 'user__real_name', 'ip_address']
    ordering_fields = ['login_time']
    ordering = ['-login_time']
    
    def get_queryset(self):
        """管理员可以查看所有日志，普通用户只能查看自己的日志"""
        queryset = super().get_queryset()
        user = self.request.user
        if not user.is_admin:
            queryset = queryset.filter(user=user)
        return queryset


class DepartmentViewSet(viewsets.ModelViewSet):
    """部门视图集"""
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    @action(detail=True, methods=['get'])
    def users(self, request, pk=None):
        """获取部门下的所有用户"""
        department = self.get_object()
        users = User.objects.filter(department=department, is_superuser=False)
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def classes(self, request, pk=None):
        """获取部门下的所有班级"""
        department = self.get_object()
        classes = Class.objects.filter(department=department)
        serializer = ClassSerializer(classes, many=True)
        return Response(serializer.data)


class ClassViewSet(viewsets.ModelViewSet):
    """班级视图集"""
    queryset = Class.objects.all()
    serializer_class = ClassSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['department']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    @action(detail=True, methods=['get'])
    def students(self, request, pk=None):
        """获取班级下的所有学生"""
        class_obj = self.get_object()
        students = User.objects.filter(class_info=class_obj, role='student')
        serializer = UserSerializer(students, many=True)
        return Response(serializer.data)
