import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from data_analysis.models import AnalysisTask

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '重试失败的分析任务'

    def add_arguments(self, parser):
        parser.add_argument(
            '--task-ids',
            nargs='+',
            type=int,
            help='要重试的特定任务ID列表'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='重试所有失败的任务'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='重试的最大任务数量'
        )

    def handle(self, *args, **options):
        task_ids = options['task_ids']
        retry_all = options['all']
        limit = options['limit']

        if not task_ids and not retry_all:
            self.stdout.write(self.style.ERROR('请指定要重试的任务ID或使用--all参数重试所有失败任务'))
            return

        # 查找要重试的任务
        if task_ids:
            tasks = AnalysisTask.objects.filter(id__in=task_ids)
            self.stdout.write(f'找到 {tasks.count()} 个指定的任务')
        else:
            tasks = AnalysisTask.objects.filter(status='failed').order_by('-updated_at')[:limit]
            self.stdout.write(f'找到 {tasks.count()} 个失败任务')

        if not tasks:
            self.stdout.write('没有找到要重试的任务')
            return

        # 重置任务状态为待处理
        retry_count = 0
        for task in tasks:
            try:
                with transaction.atomic():
                    self.stdout.write(f'重置任务 #{task.id}: {task.name} ({task.task_type})')
                    
                    # 记录原始状态和错误信息
                    original_status = task.status
                    original_error = task.error_message
                    
                    # 重置任务状态
                    task.status = 'pending'
                    task.error_message = f'重试前状态: {original_status}, 错误: {original_error}'
                    task.save(update_fields=['status', 'error_message', 'updated_at'])
                    
                    retry_count += 1
                    self.stdout.write(self.style.SUCCESS(f'任务 #{task.id} 已重置为待处理状态'))
            except Exception as e:
                logger.exception(f'重置任务 #{task.id} 时出错')
                self.stdout.write(self.style.ERROR(f'重置任务 #{task.id} 时出错: {str(e)}'))

        self.stdout.write(self.style.SUCCESS(f'成功重置 {retry_count} 个任务为待处理状态'))
        self.stdout.write(self.style.SUCCESS('请运行 process_analysis_tasks 命令来处理这些任务'))