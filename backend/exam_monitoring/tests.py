from rest_framework.test import APITestCase
from exam_system.user_management.models import User
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from exam_monitoring.models import ExamSession
from rest_framework.response import Response
from typing import Any, Dict, Literal, Optional, cast

class ExamAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.exam = ExamSession.objects.create(
            user=self.user,
            exam_id=1,
            status='in_progress',
            start_time=timezone.now(),
            registration_id=1
        )
        self.client.force_authenticate(user=self.user)

    def test_get_current_exam(self) -> None:
        response = self.client.get('/api/exam/current/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = cast(Response, response)
        data = cast(Dict[str, Any], response.data)
        self.assertIsNotNone(data)
        exam: ExamSession = cast(ExamSession, self.exam)
        self.assertEqual(str(data['exam']), str(exam.exam_id))  # type: ignore

    def test_submit_exam(self) -> None:
        data: Dict[str, Any] = {'answers': {1: 'A'}}
        response = self.client.post('/api/exam/submit/', data, format='json')
        response = cast(Response, response)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        exam: ExamSession = cast(ExamSession, self.exam)
        exam.refresh_from_db()
        self.assertEqual(exam.status, 'submitted')  # type: ignore

    def test_monitor_exam(self) -> None:
        response = self.client.get('/api/exam/monitor/')
        response = cast(Response, response)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = cast(Dict[str, Any], response.data)
        self.assertIsNotNone(data)
        self.assertIn('status', data)
        self.assertIn('exam_id', data)
        self.assertEqual(data['status'], 'in_progress')
        exam: ExamSession = cast(ExamSession, self.exam)
        self.assertEqual(str(data['exam_id']), str(exam.exam_id))  # type: ignore[attr-defined]

    def test_websocket_connection(self) -> None:
        # 测试WebSocket连接
        response = self.client.get('/ws/exam/')
        response = cast(Response, response)
        self.assertEqual(response.status_code, status.HTTP_101_SWITCHING_PROTOCOLS)

    def test_anti_cheating_detection(self) -> None:
        # 测试防作弊功能
        data: Dict[str, Any] = {'suspicious_activity': True}
        response = self.client.post('/api/exam/report/', data, format='json')
        response = cast(Response, response)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        exam: ExamSession = cast(ExamSession, self.exam)
        exam.refresh_from_db()
        self.assertEqual(exam.status, 'violation')  # type: ignore