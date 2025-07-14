from django.http import JsonResponse
from rest_framework.decorators import api_view

# 这里将实现日志审计的视图函数
# @api_view(['GET'])
# def login_logs(request):
#     return JsonResponse({'message': '获取登录日志成功'})

# @api_view(['GET'])
# def operation_logs(request):
#     return JsonResponse({'message': '获取操作日志成功'})