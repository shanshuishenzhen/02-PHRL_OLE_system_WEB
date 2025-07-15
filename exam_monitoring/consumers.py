import json
from datetime import datetime
from django.db import models
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import ExamSession

class ExamMonitorConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.exam_id = self.scope['url_route']['kwargs']['exam_id']
        self.user_id = self.scope['user'].id
        self.room_group_name = f'exam_monitor_{self.exam_id}'

        # 验证考试会话
        if await self.verify_exam_session():
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()
            await self.send_welcome_message()
        else:
            await self.close(code=4001)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            message_data = data.get('data')

            # 处理不同类型消息
            handlers = {
                'heartbeat': self.handle_heartbeat,
                'screenshot': self.handle_screenshot,
                'warning': self.handle_warning,
                'command_response': self.handle_command_response
            }
            if handler := handlers.get(message_type):
                await handler(message_data)

        except json.JSONDecodeError:
            await self.send_error('Invalid JSON format')
        except Exception as e:
            await self.send_error(str(e))

    async def send_welcome_message(self):
        await self.send(text_data=json.dumps({
            'type': 'system',
            'data': {
                'message': 'WebSocket连接已建立',
                'timestamp': datetime.now().isoformat()
            }
        }))

    async def send_error(self, error_msg):
        await self.send(text_data=json.dumps({
            'type': 'error',
            'data': {
                'message': error_msg,
                'timestamp': datetime.now().isoformat()
            }
        }))

    async def handle_heartbeat(self, data):
        await self.update_last_active()
        await self.send(text_data=json.dumps({
            'type': 'heartbeat_ack',
            'data': {
                'status': 'ok',
                'timestamp': datetime.now().isoformat()
            }
        }))

    async def handle_screenshot(self, data):
        # 保存截图记录并更新计数
        await self.save_screenshot(data)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'monitor_message',
                'message': {
                    'type': 'screenshot',
                    'data': data,
                    'timestamp': datetime.now().isoformat()
                }
            }
        )

    async def handle_warning(self, data):
        await self.increment_warning_count()
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'monitor_message',
                'message': {
                    'type': 'warning',
                    'data': data,
                    'timestamp': datetime.now().isoformat()
                }
            }
        )

    async def handle_command_response(self, data):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'monitor_message',
                'message': {
                    'type': 'command_response',
                    'data': data,
                    'timestamp': datetime.now().isoformat()
                }
            }
        )

    @database_sync_to_async
    def verify_exam_session(self):
        return ExamSession.objects.filter(
            id=self.exam_id,
            user_id=self.user_id,
            is_active=True
        ).exists()

    @database_sync_to_async
    def update_last_active(self):
        ExamSession.objects.filter(
            id=self.exam_id
        ).update(last_active=timezone.now())

    @database_sync_to_async
    def save_screenshot(self, data):
        ExamSession.objects.filter(
            id=self.exam_id
        ).update(
            last_screenshot=timezone.now(),
            screenshot_count=models.F('screenshot_count') + 1
        )

    @database_sync_to_async
    def increment_warning_count(self):
        ExamSession.objects.filter(
            id=self.exam_id
        ).update(
            warning_count=models.F('warning_count') + 1
        )