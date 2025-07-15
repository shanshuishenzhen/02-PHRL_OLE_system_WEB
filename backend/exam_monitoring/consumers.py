import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

class ExamMonitoringConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # 测试环境下处理
        if 'test_user' in self.scope:
            self.scope['user'] = self.scope['test_user']
            await self.accept()
            return
            
        # 开发环境下直接从scope获取用户
        if hasattr(self.scope, 'user') and self.scope['user']:
            await self.accept()
            return
            
        # 获取JWT Token
        try:
            token = self.scope.get('query_string').decode().split('token=')[1]
        except (AttributeError, IndexError):
            await self.close(code=4001)
            return
        
        if not token:
            await self.close(code=4001)
            return

        # 验证Token
        try:
            jwt_auth = JWTAuthentication()
            validated_token = jwt_auth.get_validated_token(token)
            user = await database_sync_to_async(jwt_auth.get_user)(validated_token)
            
            if user.is_anonymous:
                await self.close(code=4003)
                return
                
            self.scope['user'] = user
            await self.accept()
            
            # 加入考试房间
            exam_id = self.scope['url_route']['kwargs']['exam_id']
            await self.channel_layer.group_add(
                f"exam_{exam_id}",
                self.channel_name
            )
            
        except (InvalidToken, TokenError, IndexError):
            await self.close(code=4003)

    async def disconnect(self, close_code):
        exam_id = self.scope['url_route']['kwargs']['exam_id']
        await self.channel_layer.group_discard(
            f"exam_{exam_id}",
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            exam_id = self.scope['url_route']['kwargs']['exam_id']
            
            # 处理不同类型的消息
            if data['type'] == 'screenshot':
                await self.handle_screenshot(data, exam_id)
            elif data['type'] == 'activity':
                await self.handle_activity(data, exam_id)
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'error': 'Invalid JSON format'
            }))

    async def handle_screenshot(self, data, exam_id):
        # 处理截图数据
        await self.channel_layer.group_send(
            f"exam_{exam_id}",
            {
                'type': 'monitoring.screenshot',
                'user_id': self.scope['user'].id,
                'image_data': data['image'],
                'timestamp': data['timestamp']
            }
        )

    async def handle_activity(self, data, exam_id):
        # 处理活动数据
        await self.channel_layer.group_send(
            f"exam_{exam_id}",
            {
                'type': 'monitoring.activity',
                'user_id': self.scope['user'].id,
                'activity_type': data['activity'],
                'timestamp': data['timestamp']
            }
        )

    async def monitoring_screenshot(self, event):
        # 发送截图数据给监控端
        await self.send(text_data=json.dumps({
            'type': 'screenshot',
            'user_id': event['user_id'],
            'image_data': event['image_data'],
            'timestamp': event['timestamp']
        }))

    async def monitoring_activity(self, event):
        # 发送活动数据给监控端
        await self.send(text_data=json.dumps({
            'type': 'activity',
            'user_id': event['user_id'],
            'activity_type': event['activity_type'],
            'timestamp': event['timestamp']
        }))