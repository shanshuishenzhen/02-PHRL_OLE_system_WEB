from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PaperTemplateViewSet, PaperSectionViewSet, SectionRuleViewSet,
    PaperViewSet, PaperQuestionViewSet, PaperGenerationViewSet
)

router = DefaultRouter()
router.register(r'templates', PaperTemplateViewSet)
router.register(r'sections', PaperSectionViewSet)
router.register(r'rules', SectionRuleViewSet)
router.register(r'papers', PaperViewSet)
router.register(r'questions', PaperQuestionViewSet)
router.register(r'generations', PaperGenerationViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
