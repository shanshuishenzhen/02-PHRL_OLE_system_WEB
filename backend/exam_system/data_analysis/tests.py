from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from exam_system.user_management.models import Department, Class
from exam_system.question_bank.models import Subject, KnowledgePoint, Question, QuestionType
from exam_system.paper_management.models import Paper
from exam_system.exam_monitoring.models import Exam
from .models import (
    AnalysisTask, ExamAnalysis, StudentAnalysis, QuestionAnalysis,
    KnowledgePointAnalysis, ClassAnalysis, DepartmentAnalysis,
    AnalysisReport, AnalysisTemplate
)

User = get_user_model()


class AnalysisTaskModelTests(TestCase):
    def setUp(self):
        # 创建用户
        self.admin_user = User.objects.create_user(
            username='admin',
            password='password',
            email='admin@example.com',
            role='admin'
        )
        
        # 创建分析任务
        self.task = AnalysisTask.objects.create(
            name='测试分析任务',
            task_type='exam',
            status='pending',
            created_by=self.admin_user,
            parameters={'exam_id': 1}
        )
    
    def test_analysis_task_creation(self):
        """测试分析任务创建"""
        self.assertEqual(self.task.name, '测试分析任务')
        self.assertEqual(self.task.task_type, 'exam')
        self.assertEqual(self.task.status, 'pending')
        self.assertEqual(self.task.created_by, self.admin_user)
        self.assertEqual(self.task.parameters, {'exam_id': 1})
        self.assertIsNone(self.task.completed_at)


class AnalysisTaskAPITests(APITestCase):
    def setUp(self):
        # 创建用户
        self.admin_user = User.objects.create_user(
            username='admin',
            password='password',
            email='admin@example.com',
            role='admin'
        )
        self.teacher_user = User.objects.create_user(
            username='teacher',
            password='password',
            email='teacher@example.com',
            role='teacher'
        )
        self.student_user = User.objects.create_user(
            username='student',
            password='password',
            email='student@example.com',
            role='student'
        )
        
        # 创建分析任务
        self.task = AnalysisTask.objects.create(
            name='测试分析任务',
            task_type='exam',
            status='pending',
            created_by=self.admin_user,
            parameters={'exam_id': 1}
        )
    
    def test_list_tasks(self):
        """测试获取分析任务列表"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('analysistask-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_create_task(self):
        """测试创建分析任务"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('analysistask-list')
        data = {
            'name': '新分析任务',
            'task_type': 'student',
            'parameters': {'student_id': 1}
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AnalysisTask.objects.count(), 2)
        self.assertEqual(AnalysisTask.objects.get(id=2).name, '新分析任务')
    
    def test_cancel_task(self):
        """测试取消分析任务"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('analysistask-cancel', args=[self.task.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, 'failed')
        self.assertEqual(self.task.error_message, '用户取消')


class ExamAnalysisModelTests(TestCase):
    def setUp(self):
        # 创建用户
        self.admin_user = User.objects.create_user(
            username='admin',
            password='password',
            email='admin@example.com',
            role='admin'
        )
        
        # 创建科目
        self.subject = Subject.objects.create(
            name='测试科目',
            code='TEST',
            created_by=self.admin_user
        )
        
        # 创建试卷
        self.paper = Paper.objects.create(
            title='测试试卷',
            subject=self.subject,
            total_score=100,
            status='published',
            created_by=self.admin_user
        )
        
        # 创建考试
        self.exam = Exam.objects.create(
            name='测试考试',
            paper=self.paper,
            start_time='2023-01-01T09:00:00Z',
            end_time='2023-01-01T11:00:00Z',
            duration=120,
            status='completed',
            created_by=self.admin_user
        )
        
        # 创建分析任务
        self.task = AnalysisTask.objects.create(
            name='测试考试分析',
            task_type='exam',
            status='completed',
            created_by=self.admin_user,
            parameters={'exam_id': self.exam.id},
            completed_at='2023-01-02T09:00:00Z'
        )
        
        # 创建考试分析
        self.exam_analysis = ExamAnalysis.objects.create(
            task=self.task,
            exam=self.exam,
            total_students=100,
            attendance_count=90,
            attendance_rate=90.00,
            pass_count=80,
            pass_rate=88.89,
            average_score=75.5,
            highest_score=98.0,
            lowest_score=45.0,
            median_score=76.0,
            standard_deviation=10.5,
            difficulty_index=0.65,
            discrimination_index=0.75,
            reliability_coefficient=0.85,
            score_distribution={'ranges': [{'range': '0-60', 'count': 10}, {'range': '60-70', 'count': 20}, {'range': '70-80', 'count': 30}, {'range': '80-90', 'count': 20}, {'range': '90-100', 'count': 10}]},
            question_analysis={'questions': []},
            knowledge_point_analysis={'knowledge_points': []},
            class_comparison={'classes': []},
            department_comparison={'departments': []},
            time_spent_analysis={'average_time': 100}
        )
    
    def test_exam_analysis_creation(self):
        """测试考试分析创建"""
        self.assertEqual(self.exam_analysis.task, self.task)
        self.assertEqual(self.exam_analysis.exam, self.exam)
        self.assertEqual(self.exam_analysis.total_students, 100)
        self.assertEqual(self.exam_analysis.attendance_count, 90)
        self.assertEqual(float(self.exam_analysis.attendance_rate), 90.00)
        self.assertEqual(self.exam_analysis.pass_count, 80)
        self.assertEqual(float(self.exam_analysis.pass_rate), 88.89)
        self.assertEqual(float(self.exam_analysis.average_score), 75.5)
        self.assertEqual(float(self.exam_analysis.highest_score), 98.0)
        self.assertEqual(float(self.exam_analysis.lowest_score), 45.0)
        self.assertEqual(float(self.exam_analysis.median_score), 76.0)
        self.assertEqual(float(self.exam_analysis.standard_deviation), 10.5)
        self.assertEqual(float(self.exam_analysis.difficulty_index), 0.65)
        self.assertEqual(float(self.exam_analysis.discrimination_index), 0.75)
        self.assertEqual(float(self.exam_analysis.reliability_coefficient), 0.85)
        self.assertEqual(self.exam_analysis.score_distribution['ranges'][0]['range'], '0-60')
        self.assertEqual(self.exam_analysis.score_distribution['ranges'][0]['count'], 10)


class AnalysisReportModelTests(TestCase):
    def setUp(self):
        # 创建用户
        self.admin_user = User.objects.create_user(
            username='admin',
            password='password',
            email='admin@example.com',
            role='admin'
        )
        
        # 创建分析任务
        self.task = AnalysisTask.objects.create(
            name='测试分析任务',
            task_type='exam',
            status='completed',
            created_by=self.admin_user,
            parameters={'exam_id': 1},
            completed_at='2023-01-02T09:00:00Z'
        )
        
        # 创建分析报告
        self.report = AnalysisReport.objects.create(
            task=self.task,
            title='测试分析报告',
            summary='这是一份测试分析报告的摘要',
            content='这是一份测试分析报告的内容',
            charts={'chart1': {'type': 'bar', 'data': {}}},
            tables={'table1': {'headers': [], 'rows': []}},
            recommendations='这是一些建议',
            is_public=True
        )
    
    def test_analysis_report_creation(self):
        """测试分析报告创建"""
        self.assertEqual(self.report.task, self.task)
        self.assertEqual(self.report.title, '测试分析报告')
        self.assertEqual(self.report.summary, '这是一份测试分析报告的摘要')
        self.assertEqual(self.report.content, '这是一份测试分析报告的内容')
        self.assertEqual(self.report.charts['chart1']['type'], 'bar')
        self.assertEqual(self.report.recommendations, '这是一些建议')
        self.assertTrue(self.report.is_public)


class AnalysisTemplateModelTests(TestCase):
    def setUp(self):
        # 创建用户
        self.admin_user = User.objects.create_user(
            username='admin',
            password='password',
            email='admin@example.com',
            role='admin'
        )
        
        # 创建分析模板
        self.template = AnalysisTemplate.objects.create(
            name='测试分析模板',
            description='这是一个测试分析模板',
            task_type='exam',
            parameters={'include_question_analysis': True, 'include_knowledge_point_analysis': True},
            report_template='# {title}\n\n## 摘要\n\n{summary}\n\n## 详细分析\n\n{content}',
            is_system=True,
            created_by=self.admin_user
        )
    
    def test_analysis_template_creation(self):
        """测试分析模板创建"""
        self.assertEqual(self.template.name, '测试分析模板')
        self.assertEqual(self.template.description, '这是一个测试分析模板')
        self.assertEqual(self.template.task_type, 'exam')
        self.assertTrue(self.template.parameters['include_question_analysis'])
        self.assertTrue(self.template.parameters['include_knowledge_point_analysis'])
        self.assertIn('# {title}', self.template.report_template)
        self.assertTrue(self.template.is_system)
        self.assertEqual(self.template.created_by, self.admin_user)
