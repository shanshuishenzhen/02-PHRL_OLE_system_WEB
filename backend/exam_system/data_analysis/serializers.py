from rest_framework import serializers
from django.utils import timezone
from .models import (
    AnalysisTask, ExamAnalysis, StudentAnalysis, QuestionAnalysis,
    KnowledgePointAnalysis, ClassAnalysis, DepartmentAnalysis,
    AnalysisReport, AnalysisTemplate
)
from exam_system.user_management.serializers import UserSerializer, ClassSerializer, DepartmentSerializer
from exam_system.exam_monitoring.serializers import ExamSerializer
from exam_system.question_bank.serializers import QuestionSerializer, KnowledgePointSerializer


class AnalysisTaskSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    
    class Meta:
        model = AnalysisTask
        fields = '__all__'
        read_only_fields = ['status', 'created_at', 'updated_at', 'completed_at', 'result_summary', 'error_message']


class AnalysisTaskCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalysisTask
        fields = ['name', 'task_type', 'parameters']
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        validated_data['status'] = 'pending'
        return super().create(validated_data)


class AnalysisTaskUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalysisTask
        fields = ['name', 'parameters']


class ExamAnalysisSerializer(serializers.ModelSerializer):
    task = AnalysisTaskSerializer(read_only=True)
    exam = ExamSerializer(read_only=True)
    
    class Meta:
        model = ExamAnalysis
        fields = '__all__'
        read_only_fields = [
            'total_students', 'attendance_count', 'attendance_rate', 'pass_count', 'pass_rate',
            'average_score', 'highest_score', 'lowest_score', 'median_score', 'standard_deviation',
            'difficulty_index', 'discrimination_index', 'reliability_coefficient', 'score_distribution',
            'question_analysis', 'knowledge_point_analysis', 'class_comparison', 'department_comparison',
            'time_spent_analysis', 'created_at', 'updated_at'
        ]


class ExamAnalysisCreateSerializer(serializers.ModelSerializer):
    exam_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = ExamAnalysis
        fields = ['exam_id']
    
    def validate_exam_id(self, value):
        from exam_system.exam_monitoring.models import Exam
        try:
            exam = Exam.objects.get(pk=value)
            # 检查考试是否已结束
            if exam.status not in ['completed', 'archived']:
                raise serializers.ValidationError("只能分析已完成或已归档的考试")
            return value
        except Exam.DoesNotExist:
            raise serializers.ValidationError("考试不存在")
    
    def create(self, validated_data):
        from exam_system.exam_monitoring.models import Exam
        
        # 创建分析任务
        task_data = {
            'name': f"考试分析 - {Exam.objects.get(pk=validated_data['exam_id']).name}",
            'task_type': 'exam',
            'status': 'pending',
            'created_by': self.context['request'].user,
            'parameters': {'exam_id': validated_data['exam_id']}
        }
        task = AnalysisTask.objects.create(**task_data)
        
        # 创建考试分析
        exam = Exam.objects.get(pk=validated_data['exam_id'])
        exam_analysis = ExamAnalysis.objects.create(
            task=task,
            exam=exam
        )
        
        return exam_analysis


class StudentAnalysisSerializer(serializers.ModelSerializer):
    task = AnalysisTaskSerializer(read_only=True)
    student = UserSerializer(read_only=True)
    
    class Meta:
        model = StudentAnalysis
        fields = '__all__'
        read_only_fields = [
            'exam_count', 'attendance_count', 'attendance_rate', 'pass_count', 'pass_rate',
            'average_score', 'highest_score', 'lowest_score', 'score_trend',
            'knowledge_point_mastery', 'question_type_performance', 'time_spent_analysis',
            'error_pattern_analysis', 'improvement_suggestions', 'created_at', 'updated_at'
        ]


class StudentAnalysisCreateSerializer(serializers.ModelSerializer):
    student_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = StudentAnalysis
        fields = ['student_id']
    
    def validate_student_id(self, value):
        from exam_system.user_management.models import User
        try:
            student = User.objects.get(pk=value)
            if student.role != 'student':
                raise serializers.ValidationError("只能分析学生用户")
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("学生不存在")
    
    def create(self, validated_data):
        from exam_system.user_management.models import User
        
        # 创建分析任务
        student = User.objects.get(pk=validated_data['student_id'])
        task_data = {
            'name': f"学生分析 - {student.username}",
            'task_type': 'student',
            'status': 'pending',
            'created_by': self.context['request'].user,
            'parameters': {'student_id': validated_data['student_id']}
        }
        task = AnalysisTask.objects.create(**task_data)
        
        # 创建学生分析
        student_analysis = StudentAnalysis.objects.create(
            task=task,
            student=student
        )
        
        return student_analysis


class QuestionAnalysisSerializer(serializers.ModelSerializer):
    task = AnalysisTaskSerializer(read_only=True)
    question = QuestionSerializer(read_only=True)
    
    class Meta:
        model = QuestionAnalysis
        fields = '__all__'
        read_only_fields = [
            'usage_count', 'correct_count', 'correct_rate', 'average_score',
            'difficulty_index', 'discrimination_index', 'average_time_spent',
            'option_distribution', 'class_performance', 'department_performance',
            'common_errors', 'improvement_suggestions', 'created_at', 'updated_at'
        ]


class QuestionAnalysisCreateSerializer(serializers.ModelSerializer):
    question_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = QuestionAnalysis
        fields = ['question_id']
    
    def validate_question_id(self, value):
        from exam_system.question_bank.models import Question
        try:
            Question.objects.get(pk=value)
            return value
        except Question.DoesNotExist:
            raise serializers.ValidationError("题目不存在")
    
    def create(self, validated_data):
        from exam_system.question_bank.models import Question
        
        # 创建分析任务
        question = Question.objects.get(pk=validated_data['question_id'])
        task_data = {
            'name': f"题目分析 - 题目{question.id}",
            'task_type': 'question',
            'status': 'pending',
            'created_by': self.context['request'].user,
            'parameters': {'question_id': validated_data['question_id']}
        }
        task = AnalysisTask.objects.create(**task_data)
        
        # 创建题目分析
        question_analysis = QuestionAnalysis.objects.create(
            task=task,
            question=question
        )
        
        return question_analysis


class KnowledgePointAnalysisSerializer(serializers.ModelSerializer):
    task = AnalysisTaskSerializer(read_only=True)
    knowledge_point = KnowledgePointSerializer(read_only=True)
    
    class Meta:
        model = KnowledgePointAnalysis
        fields = '__all__'
        read_only_fields = [
            'question_count', 'usage_count', 'correct_rate', 'average_score',
            'difficulty_index', 'mastery_distribution', 'class_performance',
            'department_performance', 'related_knowledge_points',
            'improvement_suggestions', 'created_at', 'updated_at'
        ]


class KnowledgePointAnalysisCreateSerializer(serializers.ModelSerializer):
    knowledge_point_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = KnowledgePointAnalysis
        fields = ['knowledge_point_id']
    
    def validate_knowledge_point_id(self, value):
        from exam_system.question_bank.models import KnowledgePoint
        try:
            KnowledgePoint.objects.get(pk=value)
            return value
        except KnowledgePoint.DoesNotExist:
            raise serializers.ValidationError("知识点不存在")
    
    def create(self, validated_data):
        from exam_system.question_bank.models import KnowledgePoint
        
        # 创建分析任务
        knowledge_point = KnowledgePoint.objects.get(pk=validated_data['knowledge_point_id'])
        task_data = {
            'name': f"知识点分析 - {knowledge_point.name}",
            'task_type': 'knowledge',
            'status': 'pending',
            'created_by': self.context['request'].user,
            'parameters': {'knowledge_point_id': validated_data['knowledge_point_id']}
        }
        task = AnalysisTask.objects.create(**task_data)
        
        # 创建知识点分析
        knowledge_point_analysis = KnowledgePointAnalysis.objects.create(
            task=task,
            knowledge_point=knowledge_point
        )
        
        return knowledge_point_analysis


class ClassAnalysisSerializer(serializers.ModelSerializer):
    task = AnalysisTaskSerializer(read_only=True)
    class_obj = ClassSerializer(read_only=True)
    
    class Meta:
        model = ClassAnalysis
        fields = '__all__'
        read_only_fields = [
            'student_count', 'exam_count', 'average_attendance_rate', 'average_pass_rate',
            'average_score', 'score_distribution', 'knowledge_point_mastery',
            'question_type_performance', 'student_ranking', 'performance_trend',
            'comparison_with_other_classes', 'improvement_suggestions', 'created_at', 'updated_at'
        ]


class ClassAnalysisCreateSerializer(serializers.ModelSerializer):
    class_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = ClassAnalysis
        fields = ['class_id']
    
    def validate_class_id(self, value):
        from exam_system.user_management.models import Class
        try:
            Class.objects.get(pk=value)
            return value
        except Class.DoesNotExist:
            raise serializers.ValidationError("班级不存在")
    
    def create(self, validated_data):
        from exam_system.user_management.models import Class
        
        # 创建分析任务
        class_obj = Class.objects.get(pk=validated_data['class_id'])
        task_data = {
            'name': f"班级分析 - {class_obj.name}",
            'task_type': 'class',
            'status': 'pending',
            'created_by': self.context['request'].user,
            'parameters': {'class_id': validated_data['class_id']}
        }
        task = AnalysisTask.objects.create(**task_data)
        
        # 创建班级分析
        class_analysis = ClassAnalysis.objects.create(
            task=task,
            class_obj=class_obj
        )
        
        return class_analysis


class DepartmentAnalysisSerializer(serializers.ModelSerializer):
    task = AnalysisTaskSerializer(read_only=True)
    department = DepartmentSerializer(read_only=True)
    
    class Meta:
        model = DepartmentAnalysis
        fields = '__all__'
        read_only_fields = [
            'class_count', 'student_count', 'exam_count', 'average_attendance_rate',
            'average_pass_rate', 'average_score', 'score_distribution',
            'knowledge_point_mastery', 'question_type_performance', 'class_ranking',
            'student_ranking', 'performance_trend', 'comparison_with_other_departments',
            'improvement_suggestions', 'created_at', 'updated_at'
        ]


class DepartmentAnalysisCreateSerializer(serializers.ModelSerializer):
    department_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = DepartmentAnalysis
        fields = ['department_id']
    
    def validate_department_id(self, value):
        from exam_system.user_management.models import Department
        try:
            Department.objects.get(pk=value)
            return value
        except Department.DoesNotExist:
            raise serializers.ValidationError("院系不存在")
    
    def create(self, validated_data):
        from exam_system.user_management.models import Department
        
        # 创建分析任务
        department = Department.objects.get(pk=validated_data['department_id'])
        task_data = {
            'name': f"院系分析 - {department.name}",
            'task_type': 'department',
            'status': 'pending',
            'created_by': self.context['request'].user,
            'parameters': {'department_id': validated_data['department_id']}
        }
        task = AnalysisTask.objects.create(**task_data)
        
        # 创建院系分析
        department_analysis = DepartmentAnalysis.objects.create(
            task=task,
            department=department
        )
        
        return department_analysis


class AnalysisReportSerializer(serializers.ModelSerializer):
    task = AnalysisTaskSerializer(read_only=True)
    
    class Meta:
        model = AnalysisReport
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class AnalysisReportCreateSerializer(serializers.ModelSerializer):
    task_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = AnalysisReport
        fields = ['task_id', 'title', 'summary', 'content', 'charts', 'tables', 'recommendations', 'is_public']
    
    def validate_task_id(self, value):
        try:
            task = AnalysisTask.objects.get(pk=value)
            if task.status != 'completed':
                raise serializers.ValidationError("只能为已完成的分析任务创建报告")
            if hasattr(task, 'report'):
                raise serializers.ValidationError("该分析任务已有报告")
            return value
        except AnalysisTask.DoesNotExist:
            raise serializers.ValidationError("分析任务不存在")
    
    def create(self, validated_data):
        task_id = validated_data.pop('task_id')
        task = AnalysisTask.objects.get(pk=task_id)
        
        report = AnalysisReport.objects.create(
            task=task,
            **validated_data
        )
        
        return report


class AnalysisTemplateSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    
    class Meta:
        model = AnalysisTemplate
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'is_system']


class AnalysisTemplateCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalysisTemplate
        fields = ['name', 'description', 'task_type', 'parameters', 'report_template']
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        validated_data['is_system'] = False
        return super().create(validated_data)
