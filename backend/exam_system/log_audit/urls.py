from django.urls import path
from . import views

urlpatterns = [
    # 这里将添加日志审计的路由
    # path('login', views.login_logs, name='login_logs'),
    # path('operation', views.operation_logs, name='operation_logs'),
]