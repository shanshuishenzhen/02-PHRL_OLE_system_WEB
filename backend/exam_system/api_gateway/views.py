from django.http import JsonResponse
from rest_framework.decorators import api_view

# 这里将实现API网关的视图函数
# @api_view(['GET', 'POST'])
# def route_view(request):
#     return JsonResponse({'message': 'API网关路由成功'})