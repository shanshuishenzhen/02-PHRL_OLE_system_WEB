import logging
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.utils import timezone
from datetime import timedelta
from data_analysis.models import AnalysisTask, ExamAnalysis, StudentAnalysis

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '优化分析任务数据库表，提高系统性能'

    def add_arguments(self, parser):
        parser.add_argument(
            '--vacuum',
            action='store_true',
            help='执行VACUUM操作（仅适用于PostgreSQL）'
        )
        parser.add_argument(
            '--reindex',
            action='store_true',
            help='重建索引（仅适用于PostgreSQL）'
        )
        parser.add_argument(
            '--analyze',
            action='store_true',
            help='更新统计信息（仅适用于PostgreSQL）'
        )
        parser.add_argument(
            '--optimize-tables',
            action='store_true',
            help='优化表（仅适用于MySQL）'
        )
        parser.add_argument(
            '--archive-old',
            action='store_true',
            help='归档旧的分析任务结果'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='归档多少天前的任务（默认90天）'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='仅显示将执行的操作，不实际执行'
        )

    def handle(self, *args, **options):
        vacuum = options['vacuum']
        reindex = options['reindex']
        analyze = options['analyze']
        optimize_tables = options['optimize_tables']
        archive_old = options['archive_old']
        days = options['days']
        dry_run = options['dry_run']

        # 获取数据库引擎
        db_engine = connection.vendor
        self.stdout.write(f'数据库引擎: {db_engine}')

        if dry_run:
            self.stdout.write(self.style.WARNING('干运行模式，不会实际执行操作'))

        # 执行优化操作
        if db_engine == 'postgresql':
            if vacuum:
                self._vacuum_tables(dry_run)
            if reindex:
                self._reindex_tables(dry_run)
            if analyze:
                self._analyze_tables(dry_run)
        elif db_engine == 'mysql':
            if optimize_tables:
                self._optimize_mysql_tables(dry_run)
        else:
            self.stdout.write(self.style.WARNING(f'不支持的数据库引擎: {db_engine}'))

        # 归档旧的分析任务
        if archive_old:
            self._archive_old_tasks(days, dry_run)

        self.stdout.write(self.style.SUCCESS('数据库优化操作完成'))

    def _vacuum_tables(self, dry_run):
        """对PostgreSQL表执行VACUUM操作"""
        tables = ['data_analysis_analysistask', 'data_analysis_examanalysis', 'data_analysis_studentanalysis']
        
        for table in tables:
            self.stdout.write(f'对表 {table} 执行VACUUM操作...')
            if not dry_run:
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(f'VACUUM FULL {table};')
                    self.stdout.write(self.style.SUCCESS(f'表 {table} VACUUM操作完成'))
                except Exception as e:
                    logger.exception(f'VACUUM表 {table} 时出错')
                    self.stdout.write(self.style.ERROR(f'VACUUM表 {table} 时出错: {str(e)}'))

    def _reindex_tables(self, dry_run):
        """重建PostgreSQL表的索引"""
        tables = ['data_analysis_analysistask', 'data_analysis_examanalysis', 'data_analysis_studentanalysis']
        
        for table in tables:
            self.stdout.write(f'对表 {table} 重建索引...')
            if not dry_run:
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(f'REINDEX TABLE {table};')
                    self.stdout.write(self.style.SUCCESS(f'表 {table} 索引重建完成'))
                except Exception as e:
                    logger.exception(f'重建表 {table} 索引时出错')
                    self.stdout.write(self.style.ERROR(f'重建表 {table} 索引时出错: {str(e)}'))

    def _analyze_tables(self, dry_run):
        """更新PostgreSQL表的统计信息"""
        tables = ['data_analysis_analysistask', 'data_analysis_examanalysis', 'data_analysis_studentanalysis']
        
        for table in tables:
            self.stdout.write(f'更新表 {table} 的统计信息...')
            if not dry_run:
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(f'ANALYZE {table};')
                    self.stdout.write(self.style.SUCCESS(f'表 {table} 统计信息更新完成'))
                except Exception as e:
                    logger.exception(f'更新表 {table} 统计信息时出错')
                    self.stdout.write(self.style.ERROR(f'更新表 {table} 统计信息时出错: {str(e)}'))

    def _optimize_mysql_tables(self, dry_run):
        """优化MySQL表"""
        tables = ['data_analysis_analysistask', 'data_analysis_examanalysis', 'data_analysis_studentanalysis']
        
        for table in tables:
            self.stdout.write(f'优化表 {table}...')
            if not dry_run:
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(f'OPTIMIZE TABLE {table};')
                    self.stdout.write(self.style.SUCCESS(f'表 {table} 优化完成'))
                except Exception as e:
                    logger.exception(f'优化表 {table} 时出错')
                    self.stdout.write(self.style.ERROR(f'优化表 {table} 时出错: {str(e)}'))

    def _archive_old_tasks(self, days, dry_run):
        """归档旧的分析任务结果"""
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # 查找旧的已完成任务
        old_tasks = AnalysisTask.objects.filter(
            status='completed',
            created_at__lt=cutoff_date
        )
        
        self.stdout.write(f'找到 {old_tasks.count()} 个超过 {days} 天的已完成任务')
        
        if not dry_run and old_tasks.exists():
            try:
                with transaction.atomic():
                    # 压缩结果数据（将详细结果移到摘要中，然后清空详细结果）
                    for task in old_tasks:
                        # 根据任务类型处理相应的分析结果
                        if task.task_type == 'exam':
                            try:
                                exam_analysis = ExamAnalysis.objects.get(task=task)
                                
                                # 将重要摘要信息保存到任务的result_summary
                                summary = {
                                    'average_score': exam_analysis.average_score,
                                    'highest_score': exam_analysis.highest_score,
                                    'lowest_score': exam_analysis.lowest_score,
                                    'median_score': exam_analysis.median_score,
                                    'pass_rate': exam_analysis.pass_rate,
                                    'archived_at': timezone.now().isoformat(),
                                    'archive_note': f'详细数据已归档（{days}天自动归档）'
                                }
                                
                                task.result_summary = summary
                                task.save(update_fields=['result_summary'])
                                
                                # 清空详细分析数据
                                exam_analysis.score_distribution = None
                                exam_analysis.question_analysis = None
                                exam_analysis.knowledge_point_analysis = None
                                exam_analysis.class_comparison = None
                                exam_analysis.department_comparison = None
                                exam_analysis.time_analysis = None
                                exam_analysis.save()
                                
                                self.stdout.write(f'已归档任务 #{task.id}: {task.name} 的考试分析结果')
                                
                            except ExamAnalysis.DoesNotExist:
                                pass
                                
                        elif task.task_type == 'student':
                            try:
                                student_analysis = StudentAnalysis.objects.get(task=task)
                                
                                # 将重要摘要信息保存到任务的result_summary
                                summary = {
                                    'archived_at': timezone.now().isoformat(),
                                    'archive_note': f'详细数据已归档（{days}天自动归档）'
                                }
                                
                                task.result_summary = summary
                                task.save(update_fields=['result_summary'])
                                
                                # 清空详细分析数据
                                student_analysis.exam_performance = None
                                student_analysis.knowledge_mastery = None
                                student_analysis.strength_weakness = None
                                student_analysis.progress_trend = None
                                student_analysis.comparison_with_class = None
                                student_analysis.comparison_with_department = None
                                student_analysis.learning_suggestions = None
                                student_analysis.save()
                                
                                self.stdout.write(f'已归档任务 #{task.id}: {task.name} 的学生分析结果')
                                
                            except StudentAnalysis.DoesNotExist:
                                pass
                    
                    self.stdout.write(self.style.SUCCESS(f'已归档 {old_tasks.count()} 个旧任务的详细结果'))
                    
            except Exception as e:
                logger.exception('归档旧任务时出错')
                self.stdout.write(self.style.ERROR(f'归档旧任务时出错: {str(e)}'))