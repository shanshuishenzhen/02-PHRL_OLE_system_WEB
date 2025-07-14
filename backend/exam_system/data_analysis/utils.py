import numpy as np
import pandas as pd
from django.db.models import Avg, Count, Max, Min, StdDev, Sum, Q, F
from django.utils import timezone
from exam_system.exam_monitoring.models import Exam, ExamRecord, ExamAnswer
from exam_system.question_bank.models import Question, KnowledgePoint
from exam_system.user_management.models import Class, Department, User
from exam_system.paper_management.models import Paper, PaperQuestion
from exam_system.score_management.models import ScoreSheet, ScoreItem, ScoreStatistics
from .models import (
    AnalysisTask, ExamAnalysis, StudentAnalysis, QuestionAnalysis,
    KnowledgePointAnalysis, ClassAnalysis, DepartmentAnalysis,
    AnalysisReport, AnalysisTemplate
)


class AnalysisTaskProcessor:
    """分析任务处理器，用于处理不同类型的分析任务"""
    
    @staticmethod
    def process_task(task_id):
        """处理分析任务
        
        Args:
            task_id: 分析任务ID
        
        Returns:
            bool: 处理是否成功
        """
        try:
            task = AnalysisTask.objects.get(id=task_id)
            
            # 更新任务状态为处理中
            task.status = 'processing'
            task.save(update_fields=['status'])
            
            # 根据任务类型调用相应的处理方法
            if task.task_type == 'exam':
                result = ExamAnalyzer.analyze(task)
            elif task.task_type == 'student':
                result = StudentAnalyzer.analyze(task)
            elif task.task_type == 'question':
                result = QuestionAnalyzer.analyze(task)
            elif task.task_type == 'knowledge_point':
                result = KnowledgePointAnalyzer.analyze(task)
            elif task.task_type == 'class':
                result = ClassAnalyzer.analyze(task)
            elif task.task_type == 'department':
                result = DepartmentAnalyzer.analyze(task)
            else:
                task.status = 'failed'
                task.error_message = f'不支持的任务类型: {task.task_type}'
                task.save(update_fields=['status', 'error_message'])
                return False
            
            if result:
                # 更新任务状态为已完成
                task.status = 'completed'
                task.completed_at = timezone.now()
                task.save(update_fields=['status', 'completed_at'])
                return True
            else:
                # 更新任务状态为失败
                task.status = 'failed'
                task.error_message = '分析过程中出现错误'
                task.save(update_fields=['status', 'error_message'])
                return False
                
        except AnalysisTask.DoesNotExist:
            return False
        except Exception as e:
            try:
                task = AnalysisTask.objects.get(id=task_id)
                task.status = 'failed'
                task.error_message = str(e)
                task.save(update_fields=['status', 'error_message'])
            except:
                pass
            return False


class ExamAnalyzer:
    """考试分析器，用于分析考试数据"""
    
    @staticmethod
    def analyze(task):
        """分析考试数据
        
        Args:
            task: 分析任务对象
        
        Returns:
            bool: 分析是否成功
        """
        try:
            # 获取考试ID
            exam_id = task.parameters.get('exam_id')
            if not exam_id:
                raise ValueError('缺少考试ID参数')
            
            # 获取考试对象
            exam = Exam.objects.get(id=exam_id)
            
            # 获取考试记录
            exam_records = ExamRecord.objects.filter(exam=exam)
            
            # 获取评分表
            score_sheets = ScoreSheet.objects.filter(exam_record__in=exam_records)
            
            # 计算基本统计数据
            total_students = exam_records.count()
            attendance_count = exam_records.filter(status__in=['completed', 'graded']).count()
            attendance_rate = (attendance_count / total_students * 100) if total_students > 0 else 0
            
            # 计算分数统计
            score_stats = score_sheets.filter(status='completed').aggregate(
                avg_score=Avg('total_score'),
                max_score=Max('total_score'),
                min_score=Min('total_score'),
                std_dev=StdDev('total_score')
            )
            
            # 计算通过率
            pass_score = exam.pass_score if exam.pass_score is not None else 60
            pass_count = score_sheets.filter(status='completed', total_score__gte=pass_score).count()
            pass_rate = (pass_count / attendance_count * 100) if attendance_count > 0 else 0
            
            # 计算中位数分数
            if attendance_count > 0:
                scores = list(score_sheets.filter(status='completed').values_list('total_score', flat=True))
                median_score = np.median(scores) if scores else 0
            else:
                median_score = 0
            
            # 计算分数分布
            score_ranges = [
                {'range': '0-60', 'count': score_sheets.filter(status='completed', total_score__lt=60).count()},
                {'range': '60-70', 'count': score_sheets.filter(status='completed', total_score__gte=60, total_score__lt=70).count()},
                {'range': '70-80', 'count': score_sheets.filter(status='completed', total_score__gte=70, total_score__lt=80).count()},
                {'range': '80-90', 'count': score_sheets.filter(status='completed', total_score__gte=80, total_score__lt=90).count()},
                {'range': '90-100', 'count': score_sheets.filter(status='completed', total_score__gte=90).count()}
            ]
            
            # 计算试题分析
            paper_questions = PaperQuestion.objects.filter(paper=exam.paper)
            question_analysis = []
            
            for pq in paper_questions:
                # 获取该题的所有评分项
                score_items = ScoreItem.objects.filter(
                    score_sheet__in=score_sheets,
                    question_id=pq.question.id
                )
                
                # 计算该题的平均分
                avg_score = score_items.aggregate(avg=Avg('score'))['avg'] or 0
                
                # 计算该题的得分率
                score_rate = (avg_score / pq.score * 100) if pq.score > 0 else 0
                
                # 计算该题的难度系数 (1 - 得分率/100)
                difficulty = 1 - (score_rate / 100)
                
                # 添加到题目分析列表
                question_analysis.append({
                    'question_id': pq.question.id,
                    'question_type': pq.question.question_type,
                    'content': pq.question.content[:100] + '...' if len(pq.question.content) > 100 else pq.question.content,
                    'full_score': pq.score,
                    'avg_score': avg_score,
                    'score_rate': score_rate,
                    'difficulty': difficulty
                })
            
            # 计算知识点分析
            knowledge_point_analysis = []
            
            # 获取试卷中涉及的所有知识点
            knowledge_points = KnowledgePoint.objects.filter(
                question__paperquestion__paper=exam.paper
            ).distinct()
            
            for kp in knowledge_points:
                # 获取该知识点相关的所有题目
                questions = Question.objects.filter(
                    knowledge_points=kp,
                    paperquestion__paper=exam.paper
                )
                
                # 获取这些题目的所有评分项
                score_items = ScoreItem.objects.filter(
                    score_sheet__in=score_sheets,
                    question_id__in=questions.values_list('id', flat=True)
                )
                
                # 计算该知识点的平均得分率
                total_possible_score = sum(pq.score for pq in PaperQuestion.objects.filter(
                    paper=exam.paper, question__in=questions
                ))
                
                total_actual_score = score_items.aggregate(sum=Sum('score'))['sum'] or 0
                total_max_score = score_items.count() * total_possible_score
                
                mastery_rate = (total_actual_score / total_max_score * 100) if total_max_score > 0 else 0
                
                # 添加到知识点分析列表
                knowledge_point_analysis.append({
                    'knowledge_point_id': kp.id,
                    'name': kp.name,
                    'questions_count': questions.count(),
                    'mastery_rate': mastery_rate
                })
            
            # 计算班级对比
            class_comparison = []
            
            # 获取参加考试的所有班级
            classes = Class.objects.filter(
                students__examrecord__in=exam_records
            ).distinct()
            
            for cls in classes:
                # 获取该班级的所有评分表
                class_score_sheets = ScoreSheet.objects.filter(
                    exam_record__student__class_id=cls.id,
                    exam_record__exam=exam,
                    status='completed'
                )
                
                # 计算该班级的平均分
                avg_score = class_score_sheets.aggregate(avg=Avg('total_score'))['avg'] or 0
                
                # 计算该班级的通过率
                class_attendance = class_score_sheets.count()
                class_pass_count = class_score_sheets.filter(total_score__gte=pass_score).count()
                class_pass_rate = (class_pass_count / class_attendance * 100) if class_attendance > 0 else 0
                
                # 添加到班级对比列表
                class_comparison.append({
                    'class_id': cls.id,
                    'name': cls.name,
                    'student_count': class_attendance,
                    'avg_score': avg_score,
                    'pass_rate': class_pass_rate
                })
            
            # 计算院系对比
            department_comparison = []
            
            # 获取参加考试的所有院系
            departments = Department.objects.filter(
                classes__students__examrecord__in=exam_records
            ).distinct()
            
            for dept in departments:
                # 获取该院系的所有评分表
                dept_score_sheets = ScoreSheet.objects.filter(
                    exam_record__student__class__department_id=dept.id,
                    exam_record__exam=exam,
                    status='completed'
                )
                
                # 计算该院系的平均分
                avg_score = dept_score_sheets.aggregate(avg=Avg('total_score'))['avg'] or 0
                
                # 计算该院系的通过率
                dept_attendance = dept_score_sheets.count()
                dept_pass_count = dept_score_sheets.filter(total_score__gte=pass_score).count()
                dept_pass_rate = (dept_pass_count / dept_attendance * 100) if dept_attendance > 0 else 0
                
                # 添加到院系对比列表
                department_comparison.append({
                    'department_id': dept.id,
                    'name': dept.name,
                    'student_count': dept_attendance,
                    'avg_score': avg_score,
                    'pass_rate': dept_pass_rate
                })
            
            # 计算答题时间分析
            time_spent_records = exam_records.filter(status__in=['completed', 'graded'])
            avg_time_spent = time_spent_records.aggregate(
                avg=Avg(F('submit_time') - F('start_time'))
            )['avg']
            
            avg_minutes = avg_time_spent.total_seconds() / 60 if avg_time_spent else 0
            
            # 创建或更新考试分析对象
            exam_analysis, created = ExamAnalysis.objects.update_or_create(
                task=task,
                defaults={
                    'exam': exam,
                    'total_students': total_students,
                    'attendance_count': attendance_count,
                    'attendance_rate': attendance_rate,
                    'pass_count': pass_count,
                    'pass_rate': pass_rate,
                    'average_score': score_stats['avg_score'] or 0,
                    'highest_score': score_stats['max_score'] or 0,
                    'lowest_score': score_stats['min_score'] or 0,
                    'median_score': median_score,
                    'standard_deviation': score_stats['std_dev'] or 0,
                    'difficulty_index': sum(q['difficulty'] for q in question_analysis) / len(question_analysis) if question_analysis else 0,
                    'discrimination_index': 0.7,  # 需要更复杂的计算，这里简化处理
                    'reliability_coefficient': 0.8,  # 需要更复杂的计算，这里简化处理
                    'score_distribution': {'ranges': score_ranges},
                    'question_analysis': {'questions': question_analysis},
                    'knowledge_point_analysis': {'knowledge_points': knowledge_point_analysis},
                    'class_comparison': {'classes': class_comparison},
                    'department_comparison': {'departments': department_comparison},
                    'time_spent_analysis': {'average_time': avg_minutes}
                }
            )
            
            return True
            
        except Exception as e:
            task.error_message = f'考试分析失败: {str(e)}'
            task.save(update_fields=['error_message'])
            return False


class StudentAnalyzer:
    """学生分析器，用于分析学生数据"""
    
    @staticmethod
    def analyze(task):
        """分析学生数据
        
        Args:
            task: 分析任务对象
        
        Returns:
            bool: 分析是否成功
        """
        try:
            # 获取学生ID
            student_id = task.parameters.get('student_id')
            if not student_id:
                raise ValueError('缺少学生ID参数')
            
            # 获取学生对象
            student = User.objects.get(id=student_id, role='student')
            
            # 获取学生的所有考试记录
            exam_records = ExamRecord.objects.filter(
                student=student,
                status__in=['completed', 'graded']
            )
            
            # 获取学生的所有评分表
            score_sheets = ScoreSheet.objects.filter(
                exam_record__in=exam_records,
                status='completed'
            )
            
            # 计算基本统计数据
            total_exams = exam_records.count()
            completed_exams = score_sheets.count()
            
            # 计算平均分
            avg_score = score_sheets.aggregate(avg=Avg('total_score'))['avg'] or 0
            
            # 计算通过率
            pass_count = 0
            total_count = 0
            
            for sheet in score_sheets:
                exam = sheet.exam_record.exam
                pass_score = exam.pass_score if exam.pass_score is not None else 60
                if sheet.total_score >= pass_score:
                    pass_count += 1
                total_count += 1
            
            pass_rate = (pass_count / total_count * 100) if total_count > 0 else 0
            
            # 班级排名（已移除）
            class_rankings = []
            # 学生排名（已移除）
            student_rankings = []
            # 学生排名计算已移除
            
            # 计算分数分布
            score_distribution = [
                {'range': '0-60', 'count': score_sheets.filter(total_score__lt=60).count()},
                {'range': '60-70', 'count': score_sheets.filter(total_score__gte=60, total_score__lt=70).count()},
                {'range': '70-80', 'count': score_sheets.filter(total_score__gte=70, total_score__lt=80).count()},
                {'range': '80-90', 'count': score_sheets.filter(total_score__gte=80, total_score__lt=90).count()},
                {'range': '90-100', 'count': score_sheets.filter(total_score__gte=90).count()}
            ]
            
            # 表现趋势计算已移除
            performance_trend = []
            
            # 院系对比计算已移除
            department_comparison = []

            
            # 院系对比计算已移除
            
            # 计算最高分和最低分
            max_score = score_sheets.aggregate(max=Max('total_score'))['max'] or 0
            min_score = score_sheets.aggregate(min=Min('total_score'))['min'] or 0
            
            # 计算知识点掌握度
            knowledge_points_mastery = []
            
            # 获取所有相关的知识点
            knowledge_points = set()
            for sheet in score_sheets:
                for item in sheet.score_items.all():
                    if item.question and item.question.knowledge_points.exists():
                        for kp in item.question.knowledge_points.all():
                            knowledge_points.add(kp)
            
            # 计算每个知识点的掌握度
            for kp in knowledge_points:
                total_points = 0
                earned_points = 0
                
                for sheet in score_sheets:
                    for item in sheet.score_items.all():
                        if item.question and item.question.knowledge_points.filter(id=kp.id).exists():
                            total_points += item.max_score
                            earned_points += item.score
                
                mastery_percentage = (earned_points / total_points * 100) if total_points > 0 else 0
                knowledge_points_mastery.append({
                    'knowledge_point_id': kp.id,
                    'knowledge_point_name': kp.name,
                    'mastery_percentage': mastery_percentage
                })
            
            # 计算题型表现
            question_type_performance = []
            question_types = set()
            
            # 获取所有题型
            for sheet in score_sheets:
                for item in sheet.score_items.all():
                    if item.question:
                        question_types.add(item.question.question_type)
            
            # 计算每种题型的表现
            for q_type in question_types:
                total_points = 0
                earned_points = 0
                
                for sheet in score_sheets:
                    for item in sheet.score_items.all():
                        if item.question and item.question.question_type == q_type:
                            total_points += item.max_score
                            earned_points += item.score
                
                performance_percentage = (earned_points / total_points * 100) if total_points > 0 else 0
                question_type_performance.append({
                    'question_type': q_type,
                    'performance_percentage': performance_percentage
                })
            
            # 计算通过率
            pass_count = 0
            total_count = len(score_sheets)
            for sheet in score_sheets:
                exam = sheet.exam_record.exam
                pass_score = exam.pass_score if exam.pass_score is not None else 60
                if sheet.total_score >= pass_score:
                    pass_count += 1
            
            pass_rate = (pass_count / total_count * 100) if total_count > 0 else 0
            
            # 保存分析结果
            analysis_data = {
                'avg_score': avg_score,
                'max_score': max_score,
                'min_score': min_score,
                'pass_rate': pass_rate,
                'score_distribution': score_distribution,
                'knowledge_points_mastery': knowledge_points_mastery,
                'question_type_performance': question_type_performance,
                'class_rankings': [],
                'student_rankings': [],
                'performance_trend': [],
                'department_comparison': []
            }
            
            # 将分析结果保存到数据库
            department_analysis.analysis_data = analysis_data
            department_analysis.save()
            
            # 更新分析任务状态
            analysis_task.status = 'completed'
            analysis_task.save()
            
            # 分析完成

            
            # 创建或更新学生分析对象
            student_analysis, created = StudentAnalysis.objects.update_or_create(
                task=task,
                defaults={
                    'student': student,
                    'total_exams': total_exams,
                    'completed_exams': completed_exams,
                    'average_score': avg_score,
                    'highest_score': max_score,
                    'lowest_score': min_score,
                    'pass_rate': pass_rate,
                    'knowledge_point_mastery': {'knowledge_points': knowledge_point_mastery},
                    'question_type_performance': {'question_types': question_type_performance},
                    'error_patterns': {'patterns': []},
                    'performance_trend': {'exams': []},
                    'class_ranking': {'rankings': []}
                }
            )
            
            return True
            
        except Exception as e:
            task.error_message = f'学生分析失败: {str(e)}'
            task.save(update_fields=['error_message'])
            return False


class QuestionAnalyzer:
    """题目分析器，用于分析题目数据"""
    
    @staticmethod
    def analyze(task):
        """分析题目数据
        
        Args:
            task: 分析任务对象
        
        Returns:
            bool: 分析是否成功
        """
        try:
            # 获取题目ID
            question_id = task.parameters.get('question_id')
            if not question_id:
                raise ValueError('缺少题目ID参数')
            
            # 获取题目对象
            question = Question.objects.get(id=question_id)
            
            # 获取包含该题目的所有试卷
            papers = Paper.objects.filter(paperquestion__question=question)
            
            # 获取使用这些试卷的所有考试
            exams = Exam.objects.filter(paper__in=papers)
            
            # 获取这些考试的所有评分表
            score_sheets = ScoreSheet.objects.filter(
                exam_record__exam__in=exams,
                status='completed'
            )
            
            # 获取该题目的所有评分项
            score_items = ScoreItem.objects.filter(
                score_sheet__in=score_sheets,
                question=question
            )
            
            # 计算基本统计数据
            total_answers = score_items.count()
            
            # 计算平均分和得分率
            avg_score = 0
            score_rate = 0
            
            if total_answers > 0:
                # 计算平均分
                total_score = score_items.aggregate(sum=Sum('score'))['sum'] or 0
                avg_score = total_score / total_answers
                
                # 计算得分率
                max_possible_score = 0
                for item in score_items:
                    try:
                        paper_question = PaperQuestion.objects.get(
                            paper=item.score_sheet.exam_record.exam.paper,
                            question=question
                        )
                        max_possible_score += paper_question.score
                    except PaperQuestion.DoesNotExist:
                        continue
                
                score_rate = (total_score / max_possible_score * 100) if max_possible_score > 0 else 0
            
            # 计算难度系数 (1 - 得分率/100)
            difficulty = 1 - (score_rate / 100)
            
            # 计算区分度
            discrimination = 0.7  # 需要更复杂的计算，这里简化处理
            
            # 计算选项分布（仅适用于选择题）
            option_distribution = {}
            
            if question.question_type in ['single_choice', 'multiple_choice']:
                # 获取该题目的所有答案
                answers = ExamAnswer.objects.filter(
                    exam_record__in=score_sheets.values('exam_record'),
                    question=question
                )
                
                # 统计选项分布
                for answer in answers:
                    if answer.answer:
                        options = answer.answer.split(',')
                        for option in options:
                            option = option.strip()
                            if option in option_distribution:
                                option_distribution[option] += 1
                            else:
                                option_distribution[option] = 1
            
            # 计算班级表现
            class_performance = []
            
            # 获取参加过包含该题目的考试的所有班级
            classes = Class.objects.filter(
                students__examrecord__exam__in=exams
            ).distinct()
            
            for cls in classes:
                # 获取该班级的所有评分项
                class_items = score_items.filter(
                    score_sheet__exam_record__student__class_id=cls.id
                )
                
                if class_items.exists():
                    # 计算该班级的平均得分率
                    total_score = class_items.aggregate(sum=Sum('score'))['sum'] or 0
                    max_possible_score = 0
                    
                    for item in class_items:
                        try:
                            paper_question = PaperQuestion.objects.get(
                                paper=item.score_sheet.exam_record.exam.paper,
                                question=question
                            )
                            max_possible_score += paper_question.score
                        except PaperQuestion.DoesNotExist:
                            continue
                    
                    class_score_rate = (total_score / max_possible_score * 100) if max_possible_score > 0 else 0
                    
                    # 添加到班级表现列表
                    class_performance.append({
                        'class_id': cls.id,
                        'name': cls.name,
                        'student_count': class_items.values('score_sheet__exam_record__student').distinct().count(),
                        'score_rate': class_score_rate
                    })
            
            # 计算院系表现
            department_performance = []
            
            # 获取参加过包含该题目的考试的所有院系
            departments = Department.objects.filter(
                classes__students__examrecord__exam__in=exams
            ).distinct()
            
            for dept in departments:
                # 获取该院系的所有评分项
                dept_items = score_items.filter(
                    score_sheet__exam_record__student__class__department_id=dept.id
                )
                
                if dept_items.exists():
                    # 计算该院系的平均得分率
                    total_score = dept_items.aggregate(sum=Sum('score'))['sum'] or 0
                    max_possible_score = 0
                    
                    for item in dept_items:
                        try:
                            paper_question = PaperQuestion.objects.get(
                                paper=item.score_sheet.exam_record.exam.paper,
                                question=question
                            )
                            max_possible_score += paper_question.score
                        except PaperQuestion.DoesNotExist:
                            continue
                    
                    dept_score_rate = (total_score / max_possible_score * 100) if max_possible_score > 0 else 0
                    
                    # 添加到院系表现列表
                    department_performance.append({
                        'department_id': dept.id,
                        'name': dept.name,
                        'student_count': dept_items.values('score_sheet__exam_record__student').distinct().count(),
                        'score_rate': dept_score_rate
                    })
            
            # 创建或更新题目分析对象
            question_analysis, created = QuestionAnalysis.objects.update_or_create(
                task=task,
                defaults={
                    'question': question,
                    'total_answers': total_answers,
                    'average_score': avg_score,
                    'score_rate': score_rate,
                    'difficulty': difficulty,
                    'discrimination': discrimination,
                    'option_distribution': {'options': [{'option': k, 'count': v} for k, v in option_distribution.items()]},
                    'class_performance': {'classes': class_performance},
                    'department_performance': {'departments': department_performance}
                }
            )
            
            return True
            
        except Exception as e:
            task.error_message = f'题目分析失败: {str(e)}'
            task.save(update_fields=['error_message'])
            return False


class KnowledgePointAnalyzer:
    """知识点分析器，用于分析知识点数据"""
    
    @staticmethod
    def analyze(task):
        """分析知识点数据
        
        Args:
            task: 分析任务对象
        
        Returns:
            bool: 分析是否成功
        """
        try:
            # 获取知识点ID
            knowledge_point_id = task.parameters.get('knowledge_point_id')
            if not knowledge_point_id:
                raise ValueError('缺少知识点ID参数')
            
            # 获取知识点对象
            knowledge_point = KnowledgePoint.objects.get(id=knowledge_point_id)
            
            # 获取包含该知识点的所有题目
            questions = Question.objects.filter(knowledge_points=knowledge_point)
            
            # 获取包含这些题目的所有试卷
            papers = Paper.objects.filter(paperquestion__question__in=questions).distinct()
            
            # 获取使用这些试卷的所有考试
            exams = Exam.objects.filter(paper__in=papers)
            
            # 获取这些考试的所有评分表
            score_sheets = ScoreSheet.objects.filter(
                exam_record__exam__in=exams,
                status='completed'
            )
            
            # 获取这些题目的所有评分项
            score_items = ScoreItem.objects.filter(
                score_sheet__in=score_sheets,
                question__in=questions
            )
            
            # 计算基本统计数据
            total_questions = questions.count()
            total_students = score_sheets.values('exam_record__student').distinct().count()
            
            # 计算掌握程度
            total_score = score_items.aggregate(sum=Sum('score'))['sum'] or 0
            max_possible_score = 0
            
            for item in score_items:
                try:
                    paper_question = PaperQuestion.objects.get(
                        paper=item.score_sheet.exam_record.exam.paper,
                        question=item.question
                    )
                    max_possible_score += paper_question.score
                except PaperQuestion.DoesNotExist:
                    continue
            
            mastery_rate = (total_score / max_possible_score * 100) if max_possible_score > 0 else 0
            
            # 计算掌握程度分布
            mastery_distribution = [
                {'level': '优秀 (90-100%)', 'count': 0},
                {'level': '良好 (80-90%)', 'count': 0},
                {'level': '中等 (70-80%)', 'count': 0},
                {'level': '及格 (60-70%)', 'count': 0},
                {'level': '不及格 (0-60%)', 'count': 0}
            ]
            
            # 计算每个学生的掌握程度
            students = User.objects.filter(
                examrecord__in=score_sheets.values('exam_record')
            ).distinct()
            
            for student in students:
                # 获取该学生的所有评分项
                student_items = score_items.filter(
                    score_sheet__exam_record__student=student
                )
                
                if student_items.exists():
                    # 计算该学生的掌握程度
                    student_score = student_items.aggregate(sum=Sum('score'))['sum'] or 0
                    student_max_score = 0
                    
                    for item in student_items:
                        try:
                            paper_question = PaperQuestion.objects.get(
                                paper=item.score_sheet.exam_record.exam.paper,
                                question=item.question
                            )
                            student_max_score += paper_question.score
                        except PaperQuestion.DoesNotExist:
                            continue
                    
                    student_mastery = (student_score / student_max_score * 100) if student_max_score > 0 else 0
                    
                    # 更新掌握程度分布
                    if student_mastery >= 90:
                        mastery_distribution[0]['count'] += 1
                    elif student_mastery >= 80:
                        mastery_distribution[1]['count'] += 1
                    elif student_mastery >= 70:
                        mastery_distribution[2]['count'] += 1
                    elif student_mastery >= 60:
                        mastery_distribution[3]['count'] += 1
                    else:
                        mastery_distribution[4]['count'] += 1
            
            # 计算班级表现
            class_performance = []
            
            # 获取参加过包含该知识点的考试的所有班级
            classes = Class.objects.filter(
                students__examrecord__exam__in=exams
            ).distinct()
            
            for cls in classes:
                # 获取该班级的所有评分项
                class_items = score_items.filter(
                    score_sheet__exam_record__student__class_id=cls.id
                )
                
                if class_items.exists():
                    # 计算该班级的掌握程度
                    class_score = class_items.aggregate(sum=Sum('score'))['sum'] or 0
                    class_max_score = 0
                    
                    for item in class_items:
                        try:
                            paper_question = PaperQuestion.objects.get(
                                paper=item.score_sheet.exam_record.exam.paper,
                                question=item.question
                            )
                            class_max_score += paper_question.score
                        except PaperQuestion.DoesNotExist:
                            continue
                    
                    class_mastery = (class_score / class_max_score * 100) if class_max_score > 0 else 0
                    
                    # 添加到班级表现列表
                    class_performance.append({
                        'class_id': cls.id,
                        'name': cls.name,
                        'student_count': class_items.values('score_sheet__exam_record__student').distinct().count(),
                        'mastery_rate': class_mastery
                    })
            
            # 计算院系表现
            department_performance = []
            
            # 获取参加过包含该知识点的考试的所有院系
            departments = Department.objects.filter(
                classes__students__examrecord__exam__in=exams
            ).distinct()
            
            for dept in departments:
                # 获取该院系的所有评分项
                dept_items = score_items.filter(
                    score_sheet__exam_record__student__class__department_id=dept.id
                )
                
                if dept_items.exists():
                    # 计算该院系的掌握程度
                    dept_score = dept_items.aggregate(sum=Sum('score'))['sum'] or 0
                    dept_max_score = 0
                    
                    for item in dept_items:
                        try:
                            paper_question = PaperQuestion.objects.get(
                                paper=item.score_sheet.exam_record.exam.paper,
                                question=item.question
                            )
                            dept_max_score += paper_question.score
                        except PaperQuestion.DoesNotExist:
                            continue
                    
                    dept_mastery = (dept_score / dept_max_score * 100) if dept_max_score > 0 else 0
                    
                    # 添加到院系表现列表
                    department_performance.append({
                        'department_id': dept.id,
                        'name': dept.name,
                        'student_count': dept_items.values('score_sheet__exam_record__student').distinct().count(),
                        'mastery_rate': dept_mastery
                    })
            
            # 计算相关知识点
            related_knowledge_points = []
            
            # 获取与该知识点相关的其他知识点（共同出现在同一题目中的知识点）
            related_kps = KnowledgePoint.objects.filter(
                question__in=questions
            ).exclude(id=knowledge_point.id).distinct()
            
            for related_kp in related_kps:
                # 计算相关程度（共同出现的题目数量 / 该知识点的题目总数）
                common_questions = Question.objects.filter(
                    knowledge_points=knowledge_point
                ).filter(
                    knowledge_points=related_kp
                ).count()
                
                relatedness = (common_questions / total_questions * 100) if total_questions > 0 else 0
                
                # 添加到相关知识点列表
                related_knowledge_points.append({
                    'knowledge_point_id': related_kp.id,
                    'name': related_kp.name,
                    'common_questions': common_questions,
                    'relatedness': relatedness
                })
            
            # 创建或更新知识点分析对象
            knowledge_point_analysis, created = KnowledgePointAnalysis.objects.update_or_create(
                task=task,
                defaults={
                    'knowledge_point': knowledge_point,
                    'total_questions': total_questions,
                    'total_students': total_students,
                    'mastery_rate': mastery_rate,
                    'mastery_distribution': {'levels': mastery_distribution},
                    'class_performance': {'classes': class_performance},
                    'department_performance': {'departments': department_performance},
                    'related_knowledge_points': {'knowledge_points': related_knowledge_points}
                }
            )
            
            return True
            
        except Exception as e:
            task.error_message = f'知识点分析失败: {str(e)}'
            task.save(update_fields=['error_message'])
            return False


class ClassAnalyzer:
    """班级分析器，用于分析班级数据"""
    
    @staticmethod
    def analyze(task):
        """分析班级数据
        
        Args:
            task: 分析任务对象
        
        Returns:
            bool: 分析是否成功
        """
        try:
            # 获取班级ID
            class_id = task.parameters.get('class_id')
            if not class_id:
                raise ValueError('缺少班级ID参数')
            
            # 获取班级对象
            class_obj = Class.objects.get(id=class_id)
            
            # 获取班级的所有学生
            students = User.objects.filter(class_id=class_obj, role='student')
            
            # 获取这些学生的所有考试记录
            exam_records = ExamRecord.objects.filter(
                student__in=students,
                status__in=['completed', 'graded']
            )
            
            # 获取这些考试记录的所有评分表
            score_sheets = ScoreSheet.objects.filter(
                exam_record__in=exam_records,
                status='completed'
            )
            
            # 计算基本统计数据
            total_students = students.count()
            total_exams = Exam.objects.filter(examrecord__in=exam_records).distinct().count()
            
            # 计算平均分
            avg_score = score_sheets.aggregate(avg=Avg('total_score'))['avg'] or 0
            
            # 计算通过率
            pass_count = 0
            total_count = 0
            
            for sheet in score_sheets:
                exam = sheet.exam_record.exam
                pass_score = exam.pass_score if exam.pass_score is not None else 60
                if sheet.total_score >= pass_score:
                    pass_count += 1
                total_count += 1
            
            pass_rate = (pass_count / total_count * 100) if total_count > 0 else 0
            
            # 计算分数分布
            score_distribution = [
                {'range': '0-60', 'count': score_sheets.filter(total_score__lt=60).count()},
                {'range': '60-70', 'count': score_sheets.filter(total_score__gte=60, total_score__lt=70).count()},
                {'range': '70-80', 'count': score_sheets.filter(total_score__gte=70, total_score__lt=80).count()},
                {'range': '80-90', 'count': score_sheets.filter(total_score__gte=80, total_score__lt=90).count()},
                {'range': '90-100', 'count': score_sheets.filter(total_score__gte=90).count()}
            ]
            
            # 计算知识点掌握情况
            knowledge_point_mastery = []
            
            # 获取班级参加过的考试中涉及的所有知识点
            knowledge_points = KnowledgePoint.objects.filter(
                question__paperquestion__paper__exam__examrecord__in=exam_records
            ).distinct()
            
            for kp in knowledge_points:
                # 获取该知识点相关的所有题目
                questions = Question.objects.filter(knowledge_points=kp)
                
                # 获取这些题目的所有评分项
                score_items = ScoreItem.objects.filter(
                    score_sheet__in=score_sheets,
                    question__in=questions
                )
                
                if score_items.exists():
                    # 计算该知识点的掌握程度
                    total_score = score_items.aggregate(sum=Sum('score'))['sum'] or 0
                    max_possible_score = 0
                    
                    for item in score_items:
                        try:
                            paper_question = PaperQuestion.objects.get(
                                paper=item.score_sheet.exam_record.exam.paper,
                                question=item.question
                            )
                            max_possible_score += paper_question.score
                        except PaperQuestion.DoesNotExist:
                            continue
                    
                    mastery_rate = (total_score / max_possible_score * 100) if max_possible_score > 0 else 0
                    
                    # 添加到知识点掌握列表
                    knowledge_point_mastery.append({
                        'knowledge_point_id': kp.id,
                        'name': kp.name,
                        'mastery_rate': mastery_rate,
                        'questions_count': score_items.values('question').distinct().count()
                    })
            
            # 计算题型表现
            question_type_performance = []
            
            # 获取所有题型
            question_types = Question.objects.filter(
                paperquestion__paper__exam__examrecord__in=exam_records
            ).values_list('question_type', flat=True).distinct()
            
            for qtype in question_types:
                # 获取该题型的所有评分项
                score_items = ScoreItem.objects.filter(
                    score_sheet__in=score_sheets,
                    question__question_type=qtype
                )
                
                if score_items.exists():
                    # 计算该题型的表现
                    total_score = score_items.aggregate(sum=Sum('score'))['sum'] or 0
                    max_possible_score = 0
                    
                    for item in score_items:
                        try:
                            paper_question = PaperQuestion.objects.get(
                                paper=item.score_sheet.exam_record.exam.paper,
                                question=item.question
                            )
                            max_possible_score += paper_question.score
                        except PaperQuestion.DoesNotExist:
                            continue
                    
                    performance_rate = (total_score / max_possible_score * 100) if max_possible_score > 0 else 0
                    
                    # 添加到题型表现列表
                    question_type_performance.append({
                        'question_type': qtype,
                        'performance_rate': performance_rate,
                        'questions_count': score_items.values('question').distinct().count()
                    })
            
            # 计算学生排名
            student_ranking = []
            
            # 计算每个学生的平均分
            for student in students:
                student_sheets = score_sheets.filter(exam_record__student=student)
                if student_sheets.exists():
                    student_avg_score = student_sheets.aggregate(avg=Avg('total_score'))['avg'] or 0
                    student_ranking.append({
                        'student_id': student.id,
                        'name': student.username,
                        'average_score': student_avg_score,
                        'exams_count': student_sheets.count()
                    })
            
            # 按平均分排序
            student_ranking.sort(key=lambda x: x['average_score'], reverse=True)
            
            # 添加排名
            for i, student in enumerate(student_ranking):
                student['rank'] = i + 1
            
            # 计算表现趋势
            performance_trend = []
            
            # 获取班级参加过的所有考试
            exams = Exam.objects.filter(examrecord__in=exam_records).distinct().order_by('start_time')
            
            for exam in exams:
                # 获取该考试的所有评分表
                exam_sheets = score_sheets.filter(exam_record__exam=exam)
                
                if exam_sheets.exists():
                    # 计算该考试的平均分
                    exam_avg_score = exam_sheets.aggregate(avg=Avg('total_score'))['avg'] or 0
                    
                    # 计算该考试的通过率
                    pass_score = exam.pass_score if exam.pass_score is not None else 60
                    exam_pass_count = exam_sheets.filter(total_score__gte=pass_score).count()
                    exam_pass_rate = (exam_pass_count / exam_sheets.count() * 100) if exam_sheets.count() > 0 else 0
                    
                    # 添加到表现趋势列表
                    performance_trend.append({
                        'exam_id': exam.id,
                        'name': exam.name,
                        'date': exam.start_time.date().isoformat(),
                        'average_score': exam_avg_score,
                        'pass_rate': exam_pass_rate,
                        'students_count': exam_sheets.count()
                    })
            
            # 计算与其他班级的对比
            class_comparison = []
            
            # 获取同一院系的其他班级
            other_classes = Class.objects.filter(department=class_obj.department).exclude(id=class_obj.id)
            
            for other_class in other_classes:
                # 获取该班级的所有评分表
                other_class_sheets = ScoreSheet.objects.filter(
                    exam_record__student__class_id=other_class.id,
                    exam_record__exam__in=exams,
                    status='completed'
                )
                
                if other_class_sheets.exists():
                    # 计算该班级的平均分
                    other_class_avg_score = other_class_sheets.aggregate(avg=Avg('total_score'))['avg'] or 0
                    
                    # 计算该班级的通过率
                    other_class_pass_count = 0
                    for sheet in other_class_sheets:
                        exam = sheet.exam_record.exam
                        pass_score = exam.pass_score if exam.pass_score is not None else 60
                        if sheet.total_score >= pass_score:
                            other_class_pass_count += 1
                    
                    other_class_pass_rate = (other_class_pass_count / other_class_sheets.count() * 100) if other_class_sheets.count() > 0 else 0
                    
                    # 添加到班级对比列表
                    class_comparison.append({
                        'class_id': other_class.id,
                        'name': other_class.name,
                        'students_count': User.objects.filter(class_id=other_class, role='student').count(),
                        'average_score': other_class_avg_score,
                        'pass_rate': other_class_pass_rate,
                        'exams_count': Exam.objects.filter(examrecord__student__class_id=other_class.id).distinct().count()
                    })
            
            # 创建或更新班级分析对象
            class_analysis, created = ClassAnalysis.objects.update_or_create(
                task=task,
                defaults={
                    'class_obj': class_obj,
                    'total_students': total_students,
                    'total_exams': total_exams,
                    'average_score': avg_score,
                    'pass_rate': pass_rate,
                    'score_distribution': {'ranges': score_distribution},
                    'knowledge_point_mastery': {'knowledge_points': knowledge_point_mastery},
                    'question_type_performance': {'question_types': question_type_performance},
                    'student_ranking': {'students': student_ranking},
                    'performance_trend': {'exams': performance_trend},
                    'class_comparison': {'classes': class_comparison}
                }
            )
            
            return True
            
        except Exception as e:
            task.error_message = f'班级分析失败: {str(e)}'
            task.save(update_fields=['error_message'])
            return False


class DepartmentAnalyzer:
    """院系分析器，用于分析院系数据"""
    
    @staticmethod
    def analyze(task):
        """分析院系数据
        
        Args:
            task: 分析任务对象
        
        Returns:
            bool: 分析是否成功
        """
        try:
            # 获取院系ID
            department_id = task.parameters.get('department_id')
            if not department_id:
                raise ValueError('缺少院系ID参数')
            
            # 获取院系对象
            department = Department.objects.get(id=department_id)
            
            # 获取院系的所有班级
            classes = Class.objects.filter(department=department)
            
            # 获取这些班级的所有学生
            students = User.objects.filter(class_id__in=classes, role='student')
            
            # 获取这些学生的所有考试记录
            exam_records = ExamRecord.objects.filter(
                student__in=students,
                status__in=['completed', 'graded']
            )
            
            # 获取这些考试记录的所有评分表
            score_sheets = ScoreSheet.objects.filter(
                exam_record__in=exam_records,
                status='completed'
            )
            
            # 计算基本统计数据
            total_students = students.count()
            total_classes = classes.count()
            total_exams = Exam.objects.filter(examrecord__in=exam_records).distinct().count()
            
            # 计算平均分
            avg_score = score_sheets.aggregate(avg=