import os
import json
import csv
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from data_analysis.models import AnalysisTask
from exam_system.user_management.models import User
from exam_system.exam_monitoring.models import Exam

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '从CSV或JSON文件批量导入分析任务'

    def add_arguments(self, parser):
        parser.add_argument(
            'file_path',
            type=str,
            help='CSV或JSON文件路径'
        )
        parser.add_argument(
            '--format',
            type=str,
            choices=['csv', 'json'],
            help='文件格式（如果未指定，将根据文件扩展名自动判断）'
        )
        parser.add_argument(
            '--admin-username',
            type=str,
            help='管理员用户名（作为任务创建者，如果文件中未指定）'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅验证导入数据，不实际创建任务'
        )
        parser.add_argument(
            '--skip-errors',
            action='store_true',
            help='遇到错误时跳过并继续处理其他任务'
        )

    def handle(self, *args, **options):
        file_path = options['file_path']
        file_format = options['format']
        admin_username = options['admin_username']
        dry_run = options['dry_run']
        skip_errors = options['skip_errors']

        # 检查文件是否存在
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'文件不存在: {file_path}'))
            return

        # 如果未指定格式，根据文件扩展名判断
        if not file_format:
            _, ext = os.path.splitext(file_path)
            if ext.lower() == '.csv':
                file_format = 'csv'
            elif ext.lower() == '.json':
                file_format = 'json'
            else:
                self.stdout.write(self.style.ERROR(f'无法确定文件格式: {file_path}'))
                return

        # 验证管理员用户
        admin_user = None
        if admin_username:
            try:
                admin_user = User.objects.get(username=admin_username)
                if admin_user.role not in ['admin', 'teacher']:
                    self.stdout.write(self.style.ERROR(f'用户 {admin_username} 不是管理员或教师'))
                    return
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'用户 {admin_username} 不存在'))
                return

        # 读取文件内容
        try:
            if file_format == 'csv':
                tasks_data = self._read_csv(file_path)
            else:  # json
                tasks_data = self._read_json(file_path)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'读取文件时出错: {str(e)}'))
            return

        if not tasks_data:
            self.stdout.write(self.style.WARNING('文件中没有有效的任务数据'))
            return

        self.stdout.write(f'从文件中读取了 {len(tasks_data)} 个任务')

        # 验证任务数据
        valid_tasks = []
        for i, task_data in enumerate(tasks_data):
            try:
                # 验证必填字段
                if 'name' not in task_data:
                    raise ValueError('缺少必填字段: name')
                if 'task_type' not in task_data:
                    raise ValueError('缺少必填字段: task_type')

                # 验证任务类型
                task_type = task_data['task_type']
                valid_types = ['exam', 'student', 'question', 'knowledge', 'class', 'department', 'custom']
                if task_type not in valid_types:
                    raise ValueError(f'无效的任务类型: {task_type}，有效类型: {", ".join(valid_types)}')

                # 验证创建者
                creator_username = task_data.get('created_by')
                creator = None
                if creator_username:
                    try:
                        creator = User.objects.get(username=creator_username)
                        if creator.role not in ['admin', 'teacher']:
                            raise ValueError(f'用户 {creator_username} 不是管理员或教师')
                    except User.DoesNotExist:
                        raise ValueError(f'用户 {creator_username} 不存在')
                elif admin_user:
                    creator = admin_user
                else:
                    raise ValueError('未指定任务创建者')

                # 验证参数
                parameters = task_data.get('parameters', {})
                if isinstance(parameters, str):
                    try:
                        parameters = json.loads(parameters)
                    except json.JSONDecodeError:
                        raise ValueError('参数JSON格式无效')

                # 根据任务类型验证特定参数
                if task_type == 'exam':
                    exam_id = parameters.get('exam_id')
                    if not exam_id:
                        raise ValueError('考试分析需要指定exam_id参数')
                    try:
                        exam = Exam.objects.get(id=exam_id)
                        parameters['exam_name'] = exam.name
                    except Exam.DoesNotExist:
                        raise ValueError(f'考试ID {exam_id} 不存在')

                elif task_type == 'student':
                    student_id = parameters.get('student_id')
                    if not student_id:
                        raise ValueError('学生分析需要指定student_id参数')
                    try:
                        student = User.objects.get(id=student_id, role='student')
                        parameters['student_name'] = f"{student.first_name} {student.last_name}".strip() or student.username
                    except User.DoesNotExist:
                        raise ValueError(f'学生ID {student_id} 不存在')

                # 构建有效的任务数据
                valid_task = {
                    'name': task_data['name'],
                    'task_type': task_type,
                    'created_by': creator,
                    'parameters': parameters,
                    'status': 'pending'
                }

                valid_tasks.append(valid_task)
                self.stdout.write(f'任务 #{i+1}: {valid_task["name"]} 验证通过')

            except ValueError as e:
                error_msg = f'任务 #{i+1} 验证失败: {str(e)}'
                if skip_errors:
                    self.stdout.write(self.style.WARNING(error_msg))
                else:
                    self.stdout.write(self.style.ERROR(error_msg))
                    return

        self.stdout.write(f'验证通过 {len(valid_tasks)} 个任务')

        # 如果是干运行模式，不实际创建任务
        if dry_run:
            self.stdout.write(self.style.WARNING('干运行模式，不会实际创建任务'))
            return

        # 创建任务
        created_count = 0
        try:
            with transaction.atomic():
                for task_data in valid_tasks:
                    task = AnalysisTask.objects.create(
                        name=task_data['name'],
                        task_type=task_data['task_type'],
                        status=task_data['status'],
                        created_by=task_data['created_by'],
                        parameters=task_data['parameters']
                    )
                    created_count += 1
                    self.stdout.write(f'已创建任务 #{task.id}: {task.name}')

            self.stdout.write(self.style.SUCCESS(f'成功创建 {created_count} 个分析任务'))
            self.stdout.write(self.style.SUCCESS('请运行 process_analysis_tasks 命令来处理这些任务'))

        except Exception as e:
            logger.exception('创建分析任务时出错')
            self.stdout.write(self.style.ERROR(f'创建分析任务时出错: {str(e)}'))

    def _read_csv(self, file_path):
        """从CSV文件读取任务数据"""
        tasks = []
        with open(file_path, 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 处理参数字段
                if 'parameters' in row and row['parameters']:
                    try:
                        row['parameters'] = json.loads(row['parameters'])
                    except json.JSONDecodeError:
                        # 如果不是有效的JSON，保留原始字符串
                        pass
                tasks.append(row)
        return tasks

    def _read_json(self, file_path):
        """从JSON文件读取任务数据"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # 处理单个任务或任务列表
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                if 'tasks' in data and isinstance(data['tasks'], list):
                    return data['tasks']
                else:
                    # 假设是单个任务
                    return [data]
            else:
                raise ValueError('无效的JSON格式')