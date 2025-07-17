from django.views.generic import TemplateView
from rest_framework.views import APIView
from rest_framework.response import Response

class SystemStatusView(APIView):
    def get(self, request):
        return Response({
            'backend_status': True,
            'database_status': True
        })
from django.http import Http404
from pathlib import Path

class DebugDashboardView(TemplateView):
    """调试面板视图"""
    
    def get_template_names(self):
        """获取模板文件路径"""
        from django.template import engines
        template_path = Path(self.kwargs.get('path', ''))
        
        # 获取默认模板引擎
        engine = engines['django']
        
        # 检查前端目录
        frontend_path = Path(engine.dirs[0]) / template_path
        if frontend_path.is_file():
            return [str(template_path)]
            
        # 检查前端构建目录
        dist_path = Path(engine.dirs[1]) / template_path
        if dist_path.is_file():
            return [str(template_path)]
            
        # 检查后端模板目录
        template_dir_path = Path(engine.dirs[2]) / template_path
        if template_dir_path.is_file():
            return [str(template_path)]
            
        raise Http404(f'Template {template_path} not found')