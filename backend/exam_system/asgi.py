"""
ASGI config for exam_system project.

It exposes the ASGI callable as a module-level variable named ``application``.
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'exam_system.settings')

# 获取Django ASGI应用
django_asgi_app = get_asgi_application()

# 导入WebSocket路由
from exam_monitoring.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    # HTTP请求由Django处理
    'http': django_asgi_app,
    # WebSocket请求
    'websocket': AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})
