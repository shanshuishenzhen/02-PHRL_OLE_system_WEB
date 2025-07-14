from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    QuestionBankViewSet, QuestionTypeViewSet, DifficultyLevelViewSet,
    KnowledgePointViewSet, QuestionViewSet, QuestionImportViewSet
)

router = DefaultRouter()
router.register(r'banks', QuestionBankViewSet)
router.register(r'types', QuestionTypeViewSet)
router.register(r'difficulties', DifficultyLevelViewSet)
router.register(r'knowledge-points', KnowledgePointViewSet)
router.register(r'', QuestionViewSet)
router.register(r'imports', QuestionImportViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
