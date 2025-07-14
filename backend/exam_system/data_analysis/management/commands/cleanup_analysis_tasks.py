import logging
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from data_analysis.models import AnalysisTask

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '清理过期的分析任务数据'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='清理多少天前的已完成任务'
        )
        parser.add_argument(
            '--failed-days',
            type=int,
            default=7,
            help='清理多少天前的失败任务'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅显示将被删除的任务，不实际删除'
        )

    def handle(self, *args, **options):
        days = options['days']
        failed_days = options['failed_days']
        dry_run = options['dry_run']

        self.stdout.write(self.style.SUCCESS(
            f'开始清理分析任务，已完成任务保留{days}天，失败任务保留{failed_days}天'
        ))

        if dry_run:
            self.stdout.write(self.style.WARNING('干运行模式，不会实际删除任务'))

        # 计算截止日期
        completed_cutoff = timezone.now() - timedelta(days=days)
        failed_cutoff = timezone.now() - timedelta(days=failed_days)

        # 查找要删除的已完成任务
        completed_tasks = AnalysisTask.objects.filter(
            status='completed',
            completed_at__lt=completed_cutoff
        )

        # 查找要删除的失败任务
        failed_tasks = AnalysisTask.objects.filter(
            status='failed',
            updated_at__lt=failed_cutoff
        )

        self.stdout.write(f'找到 {completed_tasks.count()} 个过期已完成任务')
        self.stdout.write(f'找到 {failed_tasks.count()} 个过期失败任务')

        if dry_run:
            # 显示将被删除的任务
            for task in completed_tasks:
                self.stdout.write(f'将删除已完成任务 #{task.id}: {task.name} ({task.completed_at})')
            
            for task in failed_tasks:
                self.stdout.write(f'将删除失败任务 #{task.id}: {task.name} ({task.updated_at})')
        else:
            # 实际删除任务
            with transaction.atomic():
                completed_count, _ = completed_tasks.delete()
                failed_count, _ = failed_tasks.delete()
                
                self.stdout.write(self.style.SUCCESS(f'已删除 {completed_count} 个过期已完成任务'))
                self.stdout.write(self.style.SUCCESS(f'已删除 {failed_count} 个过期失败任务'))

        self.stdout.write(self.style.SUCCESS('清理任务完成'))