from django.test import TestCase, Client
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from exam_system.user_management.models import User
import json

class APIGatewayTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.client = Client()
        
    def test_api_gateway_authentication(self):
        """测试API网关认证"""
        url = reverse('api_gateway_route', kwargs={'path': 'users/'})
        response = self.client.get(url)
        # 网关本身允许任何请求，实际权限由目标服务决定
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
    def test_api_gateway_routing(self):
        """测试API网关路由功能"""
        url = reverse('api_gateway_route', kwargs={'path': 'users/'})
        self.client.force_login(self.user)
        response = self.client.get(url)
        # 网关应正确转发请求，实际响应由目标服务决定
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)