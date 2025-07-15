import json
from channels.testing import WebsocketCommunicator
from django.test import TestCase
from exam_system.exam_monitoring.consumers import ExamMonitoringConsumer
from exam_system.user_management.authentication import JWTAuthentication
from exam_system.user_management.models import User

class WebSocketTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        cls.token = JWTAuthentication.generate_token(cls.user)['access']

    async def test_connect_and_authenticate(self):
        communicator = WebsocketCommunicator(
            ExamMonitoringConsumer.as_asgi(),
            f"/ws/exam/1/?token={self.token}"
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.disconnect()

    async def test_invalid_token_rejection(self):
        communicator = WebsocketCommunicator(
            ExamMonitoringConsumer.as_asgi(),
            "/ws/exam/1/?token=invalid"
        )
        connected, _ = await communicator.connect()
        self.assertFalse(connected)

    async def test_screenshot_message_handling(self):
        communicator = WebsocketCommunicator(
            ExamMonitoringConsumer.as_asgi(),
            f"/ws/exam/1/?token={self.token}"
        )
        await communicator.connect()
        
        # 发送截图消息
        await communicator.send_json_to({
            "type": "screenshot",
            "image": "base64encodedimage",
            "timestamp": "2023-01-01T00:00:00Z"
        })
        
        # 验证响应
        response = await communicator.receive_json_from()
        self.assertEqual(response["type"], "screenshot")
        await communicator.disconnect()

    async def test_activity_message_handling(self):
        communicator = WebsocketCommunicator(
            ExamMonitoringConsumer.as_asgi(),
            f"/ws/exam/1/?token={self.token}"
        )
        await communicator.connect()
        
        # 发送活动消息
        await communicator.send_json_to({
            "type": "activity",
            "activity": "tab_switch",
            "timestamp": "2023-01-01T00:00:00Z"
        })
        
        # 验证响应
        response = await communicator.receive_json_from()
        self.assertEqual(response["type"], "activity")
        await communicator.disconnect()