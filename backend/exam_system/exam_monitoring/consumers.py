import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import Exam, ExamRoom, ExamRecord, ExamSnapshot, ExamNotification
from exam_system.user_management.models import User


class ExamMonitoringConsumer(AsyncWebsocketConsumer):
    """
    考试监控WebSocket消费者
    处理考试监控过程中的实时通信
    """
    
    async def connect(self):
        """
        连接建立时调用
        """
        self.user = self.scope['user']
        
        # 检查用户是否已认证
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # 从URL路由中获取考试ID
        self.exam_id = self.scope['url_route']['kwargs']['exam_id']
        
        # 创建考试房间组名
        self.exam_room_group_name = f'exam_{self.exam_id}'
        
        # 将通道加入考试房间组
        await self.channel_layer.group_add(
            self.exam_room_group_name,
            self.channel_name
        )
        
        # 接受WebSocket连接
        await self.accept()
        
        # 发送连接成功消息
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': '考试监控连接已建立',
            'user_id': self.user.id,
            'username': self.user.username,
            'role': self.user.role,
            'timestamp': timezone.now().isoformat()
        }))
        
        # 如果是监考员或管理员，发送当前考试状态
        if self.user.role in ['teacher', 'admin']:
            exam_status = await self.get_exam_status()
            await self.send(text_data=json.dumps({
                'type': 'exam_status',
                'data': exam_status
            }))
    
    async def disconnect(self, close_code):
        """
        连接关闭时调用
        """
        # 如果是学生，记录离开考试的行为
        if self.user.role == 'student':
            await self.record_student_action('leave', '学生离开考试页面')
        
        # 将通道从考试房间组中移除
        await self.channel_layer.group_discard(
            self.exam_room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """
        接收WebSocket消息时调用
        """
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            # 根据消息类型处理不同的消息
            if message_type == 'student_action':
                await self.handle_student_action(text_data_json)
            elif message_type == 'invigilator_command':
                await self.handle_invigilator_command(text_data_json)
            elif message_type == 'notification':
                await self.handle_notification(text_data_json)
            elif message_type == 'heartbeat':
                await self.handle_heartbeat(text_data_json)
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'未知的消息类型: {message_type}'
                }))
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': '无效的JSON格式'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'处理消息时出错: {str(e)}'
            }))
    
    async def handle_student_action(self, data):
        """
        处理学生行为消息
        """
        if self.user.role != 'student':
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': '只有学生可以发送行为消息'
            }))
            return
        
        action = data.get('action')
        details = data.get('details', '')
        
        # 记录学生行为
        await self.record_student_action(action, details)
        
        # 将学生行为广播给监考员
        await self.channel_layer.group_send(
            self.exam_room_group_name,
            {
                'type': 'broadcast_student_action',
                'student_id': self.user.id,
                'student_name': self.user.username,
                'action': action,
                'details': details,
                'timestamp': timezone.now().isoformat()
            }
        )
    
    async def handle_invigilator_command(self, data):
        """
        处理监考员命令消息
        """
        if self.user.role not in ['teacher', 'admin']:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': '只有监考员或管理员可以发送命令'
            }))
            return
        
        command = data.get('command')
        target_student_id = data.get('student_id')
        message = data.get('message', '')
        
        # 处理不同类型的命令
        if command == 'send_warning':
            await self.send_warning_to_student(target_student_id, message)
        elif command == 'force_submit':
            await self.force_student_submit(target_student_id)
        elif command == 'broadcast_message':
            await self.broadcast_message_to_all(message)
        else:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'未知的命令: {command}'
            }))
    
    async def handle_notification(self, data):
        """
        处理通知消息
        """
        if self.user.role not in ['teacher', 'admin']:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': '只有监考员或管理员可以发送通知'
            }))
            return
        
        notification_type = data.get('notification_type', 'info')
        title = data.get('title', '考试通知')
        content = data.get('content', '')
        target_student_id = data.get('student_id')
        
        # 创建通知记录
        await self.create_notification(notification_type, title, content, target_student_id)
        
        # 广播通知
        if target_student_id:
            # 发送给特定学生
            await self.send_notification_to_student(target_student_id, notification_type, title, content)
        else:
            # 广播给所有人
            await self.broadcast_notification(notification_type, title, content)
    
    async def handle_heartbeat(self, data):
        """
        处理心跳消息，用于保持连接活跃
        """
        await self.send(text_data=json.dumps({
            'type': 'heartbeat_response',
            'timestamp': timezone.now().isoformat()
        }))
    
    async def broadcast_student_action(self, event):
        """
        广播学生行为给监考员
        """
        # 只有监考员或管理员才能接收学生行为广播
        if self.user.role in ['teacher', 'admin']:
            await self.send(text_data=json.dumps({
                'type': 'student_action',
                'student_id': event['student_id'],
                'student_name': event['student_name'],
                'action': event['action'],
                'details': event['details'],
                'timestamp': event['timestamp']
            }))
    
    async def send_warning_to_student(self, student_id, message):
        """
        向特定学生发送警告
        """
        await self.channel_layer.group_send(
            self.exam_room_group_name,
            {
                'type': 'student_warning',
                'student_id': student_id,
                'message': message,
                'sender_id': self.user.id,
                'sender_name': self.user.username,
                'timestamp': timezone.now().isoformat()
            }
        )
    
    async def student_warning(self, event):
        """
        接收学生警告消息
        """
        # 只有目标学生才能接收警告
        if self.user.role == 'student' and str(self.user.id) == str(event['student_id']):
            await self.send(text_data=json.dumps({
                'type': 'warning',
                'message': event['message'],
                'sender_id': event['sender_id'],
                'sender_name': event['sender_name'],
                'timestamp': event['timestamp']
            }))
    
    async def force_student_submit(self, student_id):
        """
        强制学生提交考试
        """
        await self.channel_layer.group_send(
            self.exam_room_group_name,
            {
                'type': 'force_submit',
                'student_id': student_id,
                'sender_id': self.user.id,
                'sender_name': self.user.username,
                'timestamp': timezone.now().isoformat()
            }
        )
    
    async def force_submit(self, event):
        """
        接收强制提交消息
        """
        # 只有目标学生才能接收强制提交命令
        if self.user.role == 'student' and str(self.user.id) == str(event['student_id']):
            await self.send(text_data=json.dumps({
                'type': 'force_submit',
                'message': '监考员已强制提交您的考试',
                'sender_id': event['sender_id'],
                'sender_name': event['sender_name'],
                'timestamp': event['timestamp']
            }))
    
    async def broadcast_message_to_all(self, message):
        """
        向所有人广播消息
        """
        await self.channel_layer.group_send(
            self.exam_room_group_name,
            {
                'type': 'broadcast_message',
                'message': message,
                'sender_id': self.user.id,
                'sender_name': self.user.username,
                'timestamp': timezone.now().isoformat()
            }
        )
    
    async def broadcast_message(self, event):
        """
        接收广播消息
        """
        await self.send(text_data=json.dumps({
            'type': 'broadcast',
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'timestamp': event['timestamp']
        }))
    
    async def send_notification_to_student(self, student_id, notification_type, title, content):
        """
        向特定学生发送通知
        """
        await self.channel_layer.group_send(
            self.exam_room_group_name,
            {
                'type': 'student_notification',
                'student_id': student_id,
                'notification_type': notification_type,
                'title': title,
                'content': content,
                'sender_id': self.user.id,
                'sender_name': self.user.username,
                'timestamp': timezone.now().isoformat()
            }
        )
    
    async def student_notification(self, event):
        """
        接收学生通知消息
        """
        # 只有目标学生才能接收通知
        if self.user.role == 'student' and str(self.user.id) == str(event['student_id']):
            await self.send(text_data=json.dumps({
                'type': 'notification',
                'notification_type': event['notification_type'],
                'title': event['title'],
                'content': event['content'],
                'sender_id': event['sender_id'],
                'sender_name': event['sender_name'],
                'timestamp': event['timestamp']
            }))
    
    async def broadcast_notification(self, notification_type, title, content):
        """
        广播通知给所有人
        """
        await self.channel_layer.group_send(
            self.exam_room_group_name,
            {
                'type': 'notification_broadcast',
                'notification_type': notification_type,
                'title': title,
                'content': content,
                'sender_id': self.user.id,
                'sender_name': self.user.username,
                'timestamp': timezone.now().isoformat()
            }
        )
    
    async def notification_broadcast(self, event):
        """
        接收广播通知
        """
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification_type': event['notification_type'],
            'title': event['title'],
            'content': event['content'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'timestamp': event['timestamp']
        }))
    
    @database_sync_to_async
    def record_student_action(self, action, details):
        """
        记录学生行为到数据库
        """
        try:
            # 获取考试记录
            exam = Exam.objects.get(id=self.exam_id)
            exam_record, created = ExamRecord.objects.get_or_create(
                exam=exam,
                student=self.user,
                defaults={'status': 'in_progress'}
            )
            
            # 判断行为是否违规
            is_violation = action in [
                'switch_tab', 'full_screen_exit', 'copy_attempt', 
                'paste_attempt', 'print_attempt', 'face_missing',
                'multiple_faces', 'unknown_face'
            ]
            
            # 创建快照记录
            ExamSnapshot.objects.create(
                exam_record=exam_record,
                action=action,
                details=details,
                is_violation=is_violation
            )
            
            # 如果是违规行为，创建通知
            if is_violation:
                ExamNotification.objects.create(
                    exam=exam,
                    student=self.user,
                    type='warning',
                    title=f'考试违规警告: {dict(ExamSnapshot.ACTION_CHOICES).get(action, action)}',
                    content=f'系统检测到可能的违规行为: {details}'
                )
            
            return True
        except Exception as e:
            print(f"记录学生行为出错: {str(e)}")
            return False
    
    @database_sync_to_async
    def create_notification(self, notification_type, title, content, student_id=None):
        """
        创建通知记录
        """
        try:
            exam = Exam.objects.get(id=self.exam_id)
            student = None
            if student_id:
                student = User.objects.get(id=student_id)
            
            ExamNotification.objects.create(
                exam=exam,
                student=student,
                sender=self.user,
                type=notification_type,
                title=title,
                content=content
            )
            return True
        except Exception as e:
            print(f"创建通知出错: {str(e)}")
            return False
    
    @database_sync_to_async
    def get_exam_status(self):
        """
        获取当前考试状态
        """
        try:
            exam = Exam.objects.get(id=self.exam_id)
            
            # 更新考试状态
            exam.update_status()
            
            # 获取考场信息
            rooms = ExamRoom.objects.filter(exam=exam).values('id', 'name', 'location')
            
            # 获取考生信息
            records = ExamRecord.objects.filter(exam=exam).select_related('student')
            students_data = []
            for record in records:
                # 获取最近的违规行为
                recent_violations = ExamSnapshot.objects.filter(
                    exam_record=record,
                    is_violation=True
                ).order_by('-timestamp')[:5].values('action', 'details', 'timestamp')
                
                students_data.append({
                    'id': record.student.id,
                    'username': record.student.username,
                    'name': f"{record.student.first_name} {record.student.last_name}".strip(),
                    'status': record.status,
                    'start_time': record.start_time.isoformat() if record.start_time else None,
                    'submit_time': record.submit_time.isoformat() if record.submit_time else None,
                    'duration': record.calculate_duration(),
                    'ip_address': record.ip_address,
                    'recent_violations': list(recent_violations)
                })
            
            return {
                'exam_id': exam.id,
                'name': exam.name,
                'status': exam.status,
                'start_time': exam.start_time.isoformat(),
                'end_time': exam.end_time.isoformat(),
                'duration': exam.duration,
                'rooms': list(rooms),
                'students': students_data,
                'total_students': len(students_data),
                'in_progress_count': sum(1 for s in students_data if s['status'] == 'in_progress'),
                'submitted_count': sum(1 for s in students_data if s['status'] == 'submitted'),
                'not_started_count': sum(1 for s in students_data if s['status'] == 'not_started')
            }
        except Exception as e:
            print(f"获取考试状态出错: {str(e)}")
            return {'error': str(e)}