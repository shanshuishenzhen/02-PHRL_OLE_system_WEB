import logging
import json
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from data_analysis.models import AnalysisTask
from exam_system.user_management.models import User
from exam_system.exam_monitoring.models import Exam

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '创建新的分析任务'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            choices=['exam', 'student', 'question', 'knowledge', 'class', 'department', 'custom'],
            required=True,
            help='分析任务类型'
        )
        parser.add_argument(
            '--name',
            type=str,
            required=True,
            help='分析任务名称'
        )
        parser.add_argument(
            '--admin-username',
            type=str,
            required=True,
            help='管理员用户名（作为任务创建者）'
        )
        parser.add_argument(
            '--params',
            type=str,
            help='任务参数，JSON格式字符串'
        )
        parser.add_argument(
            '--exam-id',
            type=int,
            help='考试ID（用于考试分析）'
        )
        parser.add_argument(
            '--student-id',
            type=int,
            help='学生ID（用于学生分析）'
        )
        parser.add_argument(
            '--class-id',
            type=int,
            help='班级ID（用于班级分析）'
        )
        parser.add_argument(
            '--department-id',
            type=int,
            help='院系ID（用于院系分析）'
        )
        parser.add_argument(
            '--question-id',
            type=int,
            help='题目ID（用于题目分析）'
        )
        parser.add_argument(
            '--knowledge-id',
            type=int,
            help='知识点ID（用于知识点分析）'
        )

    def handle(self, *args, **options):
        task_type = options['type']
        name = options['name']
        admin_username = options['admin_username']
        params_str = options['params']
        exam_id = options['exam_id']
        student_id = options['student_id']
        class_id = options['class_id']
        department_id = options['department_id']
        question_id = options['question_id']
        knowledge_id = options['knowledge_id']

        # 验证管理员用户
        try:
            admin_user = User.objects.get(username=admin_username)
            if admin_user.role not in ['admin', 'teacher']:
                self.stdout.write(self.style.ERROR(f'用户 {admin_username} 不是管理员或教师'))
                return
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'用户 {admin_username} 不存在'))
            return

        # 准备任务参数
        parameters = {}
        
        # 解析JSON参数
        if params_str:
            try:
                parameters = json.loads(params_str)
            except json.JSONDecodeError:
                self.stdout.write(self.style.ERROR('参数JSON格式无效'))
                return
        
        # 根据任务类型添加特定参数
        if task_type == 'exam':
            if not exam_id:
                self.stdout.write(self.style.ERROR('考试分析需要指定exam-id参数'))
                return
            try:
                exam = Exam.objects.get(id=exam_id)
                parameters['exam_id'] = exam_id
                parameters['exam_name'] = exam.name
            except Exam.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'考试ID {exam_id} 不存在'))
                return
        
        elif task_type == 'student':
            if not student_id:
                self.stdout.write(self.style.ERROR('学生分析需要指定student-id参数'))
                return
            try:
                student = User.objects.get(id=student_id, role='student')
                parameters['student_id'] = student_id
                parameters['student_name'] = f"{student.first_name} {student.last_name}".strip() or student.username
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'学生ID {student_id} 不存在'))
                return
        
        elif task_type == 'class':
            if not class_id:
                self.stdout.write(self.style.ERROR('班级分析需要指定class-id参数'))
                return
            parameters['class_id'] = class_id
        
        elif task_type == 'department':
            if not department_id:
                self.stdout.write(self.style.ERROR('院系分析需要指定department-id参数'))
                return
            parameters['department_id'] = department_id
        
        elif task_type == 'question':
            if not question_id:
                self.stdout.write(self.style.ERROR('题目分析需要指定question-id参数'))
                return
            parameters['question_id'] = question_id
        
        elif task_type == 'knowledge':
            if not knowledge_id:
                self.stdout.write(self.style.ERROR('知识点分析需要指定knowledge-id参数'))
                return
            parameters['knowledge_id'] = knowledge_id

        # 创建分析任务
        try:
            with transaction.atomic():
                task = AnalysisTask.objects.create(
                    name=name,
                    task_type=task_type,
                    status='pending',
                    created_by=admin_user,
                    parameters=parameters
                )
                
                self.stdout.write(self.style.SUCCESS(f'成功创建分析任务 #{task.id}: {task.name} ({task.task_type})'))
                self.stdout.write(self.style.SUCCESS(f'任务参数: {json.dumps(parameters, ensure_ascii=False)}')
                )
                self.stdout.write(self.style.SUCCESS('请运行 process_analysis_tasks 命令来处理该任务'))
        except Exception as e:
            logger.exception('创建分析任务时出错')
            self.stdout.write(self.style.ERROR(f'创建分析任务时出错: {str(e)}'))