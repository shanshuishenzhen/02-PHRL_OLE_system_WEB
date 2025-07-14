import os
import json
import csv
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from data_analysis.models import AnalysisTask, ExamAnalysis, StudentAnalysis

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '导出分析任务结果为CSV或JSON格式'

    def add_arguments(self, parser):
        parser.add_argument(
            '--task-id',
            type=int,
            help='要导出的分析任务ID'
        )
        parser.add_argument(
            '--type',
            type=str,
            choices=['exam', 'student', 'question', 'knowledge', 'class', 'department', 'custom', 'all'],
            default='all',
            help='要导出的分析任务类型（默认：all）'
        )
        parser.add_argument(
            '--status',
            type=str,
            choices=['completed', 'failed', 'all'],
            default='completed',
            help='要导出的任务状态（默认：completed）'
        )
        parser.add_argument(
            '--format',
            type=str,
            choices=['csv', 'json'],
            default='csv',
            help='导出格式（默认：csv）'
        )
        parser.add_argument(
            '--output-dir',
            type=str,
            default='./exports',
            help='导出文件保存目录（默认：./exports）'
        )
        parser.add_argument(
            '--days',
            type=int,
            help='仅导出最近几天的任务结果'
        )

    def handle(self, *args, **options):
        task_id = options['task_id']
        task_type = options['type']
        status = options['status']
        export_format = options['format']
        output_dir = options['output_dir']
        days = options['days']

        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)

        # 构建查询
        query = {}
        if task_id:
            query['id'] = task_id
        if task_type != 'all':
            query['task_type'] = task_type
        if status != 'all':
            query['status'] = status
        if days:
            cutoff_date = timezone.now() - timezone.timedelta(days=days)
            query['created_at__gte'] = cutoff_date

        # 获取任务
        tasks = AnalysisTask.objects.filter(**query).order_by('-created_at')

        if not tasks.exists():
            self.stdout.write(self.style.WARNING('没有找到符合条件的分析任务'))
            return

        self.stdout.write(self.style.SUCCESS(f'找到 {tasks.count()} 个符合条件的分析任务'))

        # 导出任务结果
        if task_id:
            # 导出单个任务
            task = tasks.first()
            self._export_task(task, export_format, output_dir)
        else:
            # 导出多个任务
            for task in tasks:
                self._export_task(task, export_format, output_dir)

        self.stdout.write(self.style.SUCCESS(f'导出完成，文件保存在 {os.path.abspath(output_dir)} 目录'))

    def _export_task(self, task, export_format, output_dir):
        """导出单个任务的结果"""
        if task.status != 'completed':
            self.stdout.write(self.style.WARNING(f'任务 #{task.id}: {task.name} 状态为 {task.status}，无法导出结果'))
            return

        # 获取任务结果
        result_data = self._get_task_result(task)
        if not result_data:
            self.stdout.write(self.style.WARNING(f'任务 #{task.id}: {task.name} 没有可导出的结果'))
            return

        # 生成文件名
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        filename = f"{task.task_type}_{task.id}_{timestamp}"

        # 导出为指定格式
        if export_format == 'json':
            self._export_json(result_data, filename, output_dir, task)
        else:  # csv
            self._export_csv(result_data, filename, output_dir, task)

    def _get_task_result(self, task):
        """获取任务的结果数据"""
        # 根据任务类型获取相应的分析结果
        if task.task_type == 'exam':
            try:
                exam_analysis = ExamAnalysis.objects.get(task=task)
                return {
                    'task_info': {
                        'id': task.id,
                        'name': task.name,
                        'type': task.task_type,
                        'created_at': task.created_at.isoformat(),
                        'created_by': f"{task.created_by.first_name} {task.created_by.last_name}".strip() or task.created_by.username,
                        'parameters': task.parameters
                    },
                    'exam_info': {
                        'exam_id': task.parameters.get('exam_id'),
                        'exam_name': task.parameters.get('exam_name'),
                    },
                    'analysis_results': {
                        'average_score': exam_analysis.average_score,
                        'highest_score': exam_analysis.highest_score,
                        'lowest_score': exam_analysis.lowest_score,
                        'median_score': exam_analysis.median_score,
                        'pass_rate': exam_analysis.pass_rate,
                        'score_distribution': exam_analysis.score_distribution,
                        'question_analysis': exam_analysis.question_analysis,
                        'knowledge_point_analysis': exam_analysis.knowledge_point_analysis,
                        'class_comparison': exam_analysis.class_comparison,
                        'department_comparison': exam_analysis.department_comparison,
                        'time_analysis': exam_analysis.time_analysis,
                    }
                }
            except ExamAnalysis.DoesNotExist:
                return None

        elif task.task_type == 'student':
            try:
                student_analysis = StudentAnalysis.objects.get(task=task)
                return {
                    'task_info': {
                        'id': task.id,
                        'name': task.name,
                        'type': task.task_type,
                        'created_at': task.created_at.isoformat(),
                        'created_by': f"{task.created_by.first_name} {task.created_by.last_name}".strip() or task.created_by.username,
                        'parameters': task.parameters
                    },
                    'student_info': {
                        'student_id': task.parameters.get('student_id'),
                        'student_name': task.parameters.get('student_name'),
                    },
                    'analysis_results': {
                        'exam_performance': student_analysis.exam_performance,
                        'knowledge_mastery': student_analysis.knowledge_mastery,
                        'strength_weakness': student_analysis.strength_weakness,
                        'progress_trend': student_analysis.progress_trend,
                        'comparison_with_class': student_analysis.comparison_with_class,
                        'comparison_with_department': student_analysis.comparison_with_department,
                        'learning_suggestions': student_analysis.learning_suggestions,
                    }
                }
            except StudentAnalysis.DoesNotExist:
                return None

        else:
            # 对于其他类型的任务，直接返回结果摘要
            return {
                'task_info': {
                    'id': task.id,
                    'name': task.name,
                    'type': task.task_type,
                    'created_at': task.created_at.isoformat(),
                    'created_by': f"{task.created_by.first_name} {task.created_by.last_name}".strip() or task.created_by.username,
                    'parameters': task.parameters
                },
                'analysis_results': task.result_summary
            }

    def _export_json(self, data, filename, output_dir, task):
        """导出为JSON格式"""
        filepath = os.path.join(output_dir, f"{filename}.json")
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.stdout.write(self.style.SUCCESS(f'任务 #{task.id}: {task.name} 已导出为 {filepath}'))
        except Exception as e:
            logger.exception(f'导出任务 #{task.id} 为JSON时出错')
            self.stdout.write(self.style.ERROR(f'导出任务 #{task.id} 为JSON时出错: {str(e)}'))

    def _export_csv(self, data, filename, output_dir, task):
        """导出为CSV格式（扁平化嵌套数据）"""
        filepath = os.path.join(output_dir, f"{filename}.csv")
        try:
            # 扁平化数据
            flat_data = self._flatten_data(data)
            
            # 写入CSV
            with open(filepath, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                # 写入表头
                writer.writerow(flat_data.keys())
                # 写入数据行
                writer.writerow(flat_data.values())
                
            self.stdout.write(self.style.SUCCESS(f'任务 #{task.id}: {task.name} 已导出为 {filepath}'))
        except Exception as e:
            logger.exception(f'导出任务 #{task.id} 为CSV时出错')
            self.stdout.write(self.style.ERROR(f'导出任务 #{task.id} 为CSV时出错: {str(e)}'))

    def _flatten_data(self, data, parent_key='', sep='_'):
        """将嵌套的字典扁平化为单层字典"""
        items = []
        for k, v in data.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            
            if isinstance(v, dict):
                items.extend(self._flatten_data(v, new_key, sep).items())
            elif isinstance(v, list) or isinstance(v, tuple):
                # 将列表转换为JSON字符串
                items.append((new_key, json.dumps(v, ensure_ascii=False)))
            else:
                items.append((new_key, v))
                
        return dict(items)