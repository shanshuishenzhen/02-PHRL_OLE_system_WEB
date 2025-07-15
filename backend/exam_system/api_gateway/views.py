from django.http import JsonResponse, HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny
import requests
import logging

logger = logging.getLogger('api_gateway')

@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@permission_classes([AllowAny])
def route_view(request, path=''):
    """API网关路由视图"""
    try:
        method = request.method
        headers = {
            'Authorization': request.headers.get('Authorization', ''),
            'Content-Type': 'application/json'
        }
        
        # 转发请求到对应服务
        service_url = f"http://127.0.0.1:8000/api/{path}"
        
        # 如果用户已认证但无Authorization头，添加session认证
        if request.user.is_authenticated and not headers['Authorization']:
            headers['Cookie'] = request.META.get('HTTP_COOKIE', '')
        response = requests.request(
            method,
            service_url,
            headers=headers,
            json=request.data if method in ['POST', 'PUT'] else None,
            params=request.query_params
        )
        
        logger.info(f"API Gateway routed: {method} {path}")
        return Response(response.json(), status=response.status_code)
        
    except AuthenticationFailed as e:
        logger.warning(f"API Gateway auth failed: {str(e)}")
        return Response(
            {'error': str(e)},
            status=401
        )
    except Exception as e:
        logger.error(f"API Gateway error: {str(e)}")
        return Response(
            {'error': 'Internal server error'},
            status=500
        )