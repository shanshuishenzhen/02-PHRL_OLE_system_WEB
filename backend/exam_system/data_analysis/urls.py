from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'tasks', views.AnalysisTaskViewSet)
router.register(r'exam-analyses', views.ExamAnalysisViewSet)
router.register(r'student-analyses', views.StudentAnalysisViewSet)
router.register(r'question-analyses', views.QuestionAnalysisViewSet)
router.register(r'knowledge-point-analyses', views.KnowledgePointAnalysisViewSet)
router.register(r'class-analyses', views.ClassAnalysisViewSet)
router.register(r'department-analyses', views.DepartmentAnalysisViewSet)
router.register(r'reports', views.AnalysisReportViewSet)
router.register(r'templates', views.AnalysisTemplateViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
