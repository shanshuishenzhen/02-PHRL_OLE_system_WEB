import logging
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count, Avg, Min, Max, F, ExpressionWrapper, fields
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth
from data_analysis.models import AnalysisTask

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '生成分析任务的统计报告'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='统计最近多少天的数据'
        )
        parser.add_argument(
            '--group-by',
            choices=['day', 'week', 'month'],
            default='day',
            help='统计数据的分组方式'
        )
        parser.add_argument(
            '--output',
            type=str,
            help='输出文件路径，不指定则输出到控制台'
        )

    def handle(self, *args, **options):
        days = options['days']
        group_by = options['group_by']
        output_file = options['output']

        self.stdout.write(self.style.SUCCESS(f'生成最近 {days} 天的分析任务统计报告，按{group_by}分组'))

        # 计算起始日期
        start_date = timezone.now() - timedelta(days=days)

        # 基础查询集
        base_queryset = AnalysisTask.objects.filter(created_at__gte=start_date)

        # 生成报告内容
        report = []
        report.append('=' * 80)
        report.append(f'分析任务统计报告 - 生成时间: {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}')
        report.append(f'统计范围: {start_date.strftime("%Y-%m-%d")} 至 {timezone.now().strftime("%Y-%m-%d")}')
        report.append('=' * 80)
        report.append('')

        # 总体统计
        total_tasks = base_queryset.count()
        pending_tasks = base_queryset.filter(status='pending').count()
        processing_tasks = base_queryset.filter(status='processing').count()
        completed_tasks = base_queryset.filter(status='completed').count()
        failed_tasks = base_queryset.filter(status='failed').count()

        report.append('总体统计:')
        report.append(f'总任务数: {total_tasks}')
        report.append(f'待处理任务: {pending_tasks} ({pending_tasks/total_tasks*100:.1f}% 如果总任务数不为0)' if total_tasks else '待处理任务: 0 (0.0%)')
        report.append(f'处理中任务: {processing_tasks} ({processing_tasks/total_tasks*100:.1f}% 如果总任务数不为0)' if total_tasks else '处理中任务: 0 (0.0%)')
        report.append(f'已完成任务: {completed_tasks} ({completed_tasks/total_tasks*100:.1f}% 如果总任务数不为0)' if total_tasks else '已完成任务: 0 (0.0%)')
        report.append(f'失败任务: {failed_tasks} ({failed_tasks/total_tasks*100:.1f}% 如果总任务数不为0)' if total_tasks else '失败任务: 0 (0.0%)')
        report.append('')

        # 按任务类型统计
        type_stats = base_queryset.values('task_type').annotate(
            count=Count('id'),
            completed=Count('id', filter=F('status')=='completed'),
            failed=Count('id', filter=F('status')=='failed'),
            completion_rate=ExpressionWrapper(
                Count('id', filter=F('status')=='completed') * 100.0 / Count('id'),
                output_field=fields.FloatField()
            )
        ).order_by('-count')

        report.append('按任务类型统计:')
        for stat in type_stats:
            report.append(f"类型: {stat['task_type']}, 总数: {stat['count']}, 完成: {stat['completed']}, " +
                         f"失败: {stat['failed']}, 完成率: {stat['completion_rate']:.1f}%")
        report.append('')

        # 按时间分组统计
        if group_by == 'day':
            trunc_func = TruncDay
            date_format = '%Y-%m-%d'
            group_name = '日期'
        elif group_by == 'week':
            trunc_func = TruncWeek
            date_format = '%Y-%m-%d'
            group_name = '周'
        else:  # month
            trunc_func = TruncMonth
            date_format = '%Y-%m'
            group_name = '月份'

        time_stats = base_queryset.annotate(
            period=trunc_func('created_at')
        ).values('period').annotate(
            count=Count('id'),
            completed=Count('id', filter=F('status')=='completed'),
            failed=Count('id', filter=F('status')=='failed'),
            completion_rate=ExpressionWrapper(
                Count('id', filter=F('status')=='completed') * 100.0 / Count('id'),
                output_field=fields.FloatField()
            )
        ).order_by('period')

        report.append(f'按{group_name}统计:')
        for stat in time_stats:
            report.append(f"{group_name}: {stat['period'].strftime(date_format)}, 总数: {stat['count']}, " +
                         f"完成: {stat['completed']}, 失败: {stat['failed']}, 完成率: {stat['completion_rate']:.1f}%")
        report.append('')

        # 处理时间统计（仅针对已完成任务）
        completed_queryset = base_queryset.filter(status='completed', completed_at__isnull=False)
        
        if completed_queryset.exists():
            # 添加处理时间字段
            completed_with_duration = completed_queryset.annotate(
                processing_time=ExpressionWrapper(
                    F('completed_at') - F('created_at'),
                    output_field=fields.DurationField()
                )
            )
            
            # 计算平均处理时间
            avg_processing_seconds = completed_with_duration.aggregate(
                avg_seconds=Avg(ExpressionWrapper(
                    F('processing_time').total_seconds(),
                    output_field=fields.FloatField()
                ))
            )['avg_seconds'] or 0
            
            # 计算最长和最短处理时间
            max_processing_seconds = completed_with_duration.aggregate(
                max_seconds=Max(ExpressionWrapper(
                    F('processing_time').total_seconds(),
                    output_field=fields.FloatField()
                ))
            )['max_seconds'] or 0
            
            min_processing_seconds = completed_with_duration.aggregate(
                min_seconds=Min(ExpressionWrapper(
                    F('processing_time').total_seconds(),
                    output_field=fields.FloatField()
                ))
            )['min_seconds'] or 0
            
            report.append('处理时间统计:')
            report.append(f'平均处理时间: {timedelta(seconds=avg_processing_seconds)}')
            report.append(f'最长处理时间: {timedelta(seconds=max_processing_seconds)}')
            report.append(f'最短处理时间: {timedelta(seconds=min_processing_seconds)}')
        else:
            report.append('处理时间统计: 没有已完成的任务')
        
        report.append('')
        report.append('=' * 80)

        # 输出报告
        report_text = '\n'.join(report)
        
        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(report_text)
                self.stdout.write(self.style.SUCCESS(f'报告已保存到: {output_file}'))
            except Exception as e:
                logger.exception(f'保存报告到文件时出错')
                self.stdout.write(self.style.ERROR(f'保存报告到文件时出错: {str(e)}'))
                self.stdout.write(report_text)
        else:
            self.stdout.write(report_text)