"""
URL Configuration for exam_system project.
"""

from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from exam_system.common.views import DebugDashboardView, SystemStatusView
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# API文档配置
schema_view = get_schema_view(
    openapi.Info(
        title="职业技能等级认证考试系统 API",
        default_version='v1',
        description="职业技能等级认证考试系统Web版API文档",
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="contact@example.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    # API文档
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # 各模块API路由
    path('api/users/', include('exam_system.user_management.urls')),
    path('api/questions/', include('exam_system.question_bank.urls')),
    path('api/papers/', include('exam_system.paper_management.urls')),
    path('api/exams/', include('exam_system.exam_monitoring.urls')),
    path('api/scores/', include('exam_system.score_management.urls')),
    path('api/marking/', include('exam_system.marking_center.urls')),
    path('api/logs/', include('exam_system.log_audit.urls')),
    path('api/gateway/', include('exam_system.api_gateway.urls')),
    path('api/analysis/', include('exam_system.data_analysis.urls')),
    
    # 调试相关API
    # path('api/debug/check-venv/', include('exam_system.common.debug_urls')),
    # path('api/debug/check-dependencies/', include('exam_system.common.debug_urls')),
    # path('api/debug/install-dependencies/', include('exam_system.common.debug_urls')),
    path('api/debug/system-status/', SystemStatusView.as_view(), name='system-status'),
    
    # 静态HTML文件路由
    re_path(r'^(?P<path>.+\.html)$', DebugDashboardView.as_view(
        content_type='text/html'
    ), name='html-files'),
    
    # 默认路由 - 使用TemplateView直接渲染index.html
    re_path(r'^$', TemplateView.as_view(template_name='index.html'), name='index'),
]

# 开发环境下提供媒体文件访问
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
