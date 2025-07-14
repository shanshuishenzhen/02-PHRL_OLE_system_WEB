from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # 考试监控WebSocket路由
    # URL格式: ws://domain/ws/exam/<exam_id>/
    re_path(r'ws/exam/(?P<exam_id>\w+)/$', consumers.ExamMonitoringConsumer.as_asgi()),
]