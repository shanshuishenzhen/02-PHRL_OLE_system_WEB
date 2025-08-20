from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Log
from .serializers import LogSerializer
from exam_system.user_management.permissions import IsAdminUser
import pandas as pd
from django.http import HttpResponse
from rest_framework.decorators import action

class LogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    系统日志视图集
    """
    queryset = Log.objects.all()
    serializer_class = LogSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['user', 'action_type', 'target_model', 'status', 'ip_address']
    search_fields = ['description', 'user__username', 'user_agent']
    ordering_fields = ['action_time', 'user', 'action_type']
    ordering = ['-action_time']

    @action(detail=False, methods=['get'])
    def export_logs(self, request):
        """
        导出日志
        """
        logs = self.filter_queryset(self.get_queryset())

        data = []
        for log in logs:
            data.append({
                '操作时间': log.action_time,
                '操作用户': log.user.username if log.user else 'System',
                '操作类型': log.get_action_type_display(),
                '操作对象': f"{log.target_model} ({log.target_id})" if log.target_model else 'N/A',
                '操作内容': log.description,
                '操作结果': log.status,
                'IP地址': log.ip_address,
                '设备信息': log.user_agent
            })

        df = pd.DataFrame(data)
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="logs.xlsx"'
        df.to_excel(response, index=False, engine='openpyxl')
        return response