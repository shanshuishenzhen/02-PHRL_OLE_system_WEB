import logging
import time
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from data_analysis.models import AnalysisTask
from data_analysis.utils import AnalysisTaskProcessor

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '处理待处理的分析任务'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='一次处理的最大任务数量'
        )
        parser.add_argument(
            '--timeout',
            type=int,
            default=300,
            help='任务处理超时时间（秒）'
        )
        parser.add_argument(
            '--continuous',
            action='store_true',
            help='是否持续运行，定期检查新任务'
        )
        parser.add_argument(
            '--interval',
            type=int,
            default=60,
            help='持续运行模式下的检查间隔（秒）'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        timeout = options['timeout']
        continuous = options['continuous']
        interval = options['interval']

        self.stdout.write(self.style.SUCCESS(f'开始处理分析任务，限制: {limit}, 超时: {timeout}秒'))

        if continuous:
            self.stdout.write(self.style.SUCCESS(f'持续运行模式，检查间隔: {interval}秒'))
            while True:
                try:
                    self.process_tasks(limit, timeout)
                    time.sleep(interval)
                except KeyboardInterrupt:
                    self.stdout.write(self.style.WARNING('收到中断信号，停止处理'))
                    break
                except Exception as e:
                    logger.error(f'处理任务时出错: {str(e)}')
                    self.stdout.write(self.style.ERROR(f'处理任务时出错: {str(e)}'))
                    time.sleep(interval)
        else:
            self.process_tasks(limit, timeout)

    def process_tasks(self, limit, timeout):
        # 获取待处理的任务
        pending_tasks = AnalysisTask.objects.filter(status='pending').order_by('created_at')[:limit]
        
        if not pending_tasks:
            self.stdout.write('没有待处理的任务')
            return
        
        self.stdout.write(f'找到 {pending_tasks.count()} 个待处理任务')
        
        for task in pending_tasks:
            try:
                self.stdout.write(f'处理任务 #{task.id}: {task.name} ({task.task_type})')
                
                # 设置开始处理时间
                start_time = time.time()
                
                # 处理任务
                success = AnalysisTaskProcessor.process_task(task.id)
                
                # 计算处理时间
                elapsed_time = time.time() - start_time
                
                if success:
                    self.stdout.write(self.style.SUCCESS(
                        f'任务 #{task.id} 处理成功，耗时: {elapsed_time:.2f}秒'
                    ))
                else:
                    self.stdout.write(self.style.ERROR(
                        f'任务 #{task.id} 处理失败，耗时: {elapsed_time:.2f}秒'
                    ))
                
                # 检查是否超时
                if elapsed_time > timeout:
                    self.stdout.write(self.style.WARNING(
                        f'任务 #{task.id} 处理超时 ({elapsed_time:.2f}秒 > {timeout}秒)'
                    ))
            except Exception as e:
                logger.exception(f'处理任务 #{task.id} 时出错')
                self.stdout.write(self.style.ERROR(f'处理任务 #{task.id} 时出错: {str(e)}'))
                
                # 更新任务状态为失败
                with transaction.atomic():
                    task.refresh_from_db()
                    if task.status == 'processing':  # 只有在处理中状态才更新为失败
                        task.status = 'failed'
                        task.error_message = f'命令执行出错: {str(e)}'
                        task.save(update_fields=['status', 'error_message', 'updated_at'])