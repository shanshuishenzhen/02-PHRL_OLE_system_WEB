import logging
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from data_analysis.models import AnalysisTask

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '检查并重置卡在处理中状态的分析任务'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=1,
            help='处理时间超过多少小时视为卡住（默认1小时）'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅显示将被重置的任务，不实际重置'
        )
        parser.add_argument(
            '--auto-retry',
            action='store_true',
            help='自动将卡住的任务重置为待处理状态（否则标记为失败）'
        )

    def handle(self, *args, **options):
        hours = options['hours']
        dry_run = options['dry_run']
        auto_retry = options['auto_retry']

        self.stdout.write(self.style.SUCCESS(
            f'开始检查处理时间超过 {hours} 小时的任务'
        ))

        if dry_run:
            self.stdout.write(self.style.WARNING('干运行模式，不会实际重置任务'))

        # 计算截止时间
        cutoff_time = timezone.now() - timedelta(hours=hours)

        # 查找卡住的任务
        stalled_tasks = AnalysisTask.objects.filter(
            status='processing',
            updated_at__lt=cutoff_time
        )

        self.stdout.write(f'找到 {stalled_tasks.count()} 个可能卡住的任务')

        if dry_run:
            # 显示将被重置的任务
            for task in stalled_tasks:
                processing_time = timezone.now() - task.updated_at
                hours, remainder = divmod(processing_time.total_seconds(), 3600)
                minutes, seconds = divmod(remainder, 60)
                
                self.stdout.write(
                    f'任务 #{task.id}: {task.name} ({task.task_type}) ' +
                    f'已处理 {int(hours)}小时{int(minutes)}分钟，将被重置'
                )
        else:
            # 实际重置任务
            reset_count = 0
            for task in stalled_tasks:
                try:
                    with transaction.atomic():
                        processing_time = timezone.now() - task.updated_at
                        hours, remainder = divmod(processing_time.total_seconds(), 3600)
                        minutes, seconds = divmod(remainder, 60)
                        
                        time_str = f'{int(hours)}小时{int(minutes)}分钟'
                        
                        if auto_retry:
                            # 重置为待处理状态
                            task.status = 'pending'
                            task.error_message = f'任务处理时间过长（{time_str}），已自动重置为待处理状态'
                            self.stdout.write(self.style.WARNING(
                                f'任务 #{task.id}: {task.name} 已重置为待处理状态'
                            ))
                        else:
                            # 标记为失败
                            task.status = 'failed'
                            task.error_message = f'任务处理时间过长（{time_str}），已自动标记为失败'
                            self.stdout.write(self.style.WARNING(
                                f'任务 #{task.id}: {task.name} 已标记为失败'
                            ))
                        
                        task.save(update_fields=['status', 'error_message', 'updated_at'])
                        reset_count += 1
                except Exception as e:
                    logger.exception(f'重置任务 #{task.id} 时出错')
                    self.stdout.write(self.style.ERROR(f'重置任务 #{task.id} 时出错: {str(e)}'))

            self.stdout.write(self.style.SUCCESS(f'已重置 {reset_count} 个卡住的任务'))

        self.stdout.write(self.style.SUCCESS('检查完成'))