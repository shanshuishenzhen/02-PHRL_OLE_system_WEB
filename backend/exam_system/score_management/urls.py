from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'scoring-criteria', views.ScoringCriteriaViewSet)
router.register(r'scoring-rules', views.ScoringRuleViewSet)
router.register(r'score-sheets', views.ScoreSheetViewSet)
router.register(r'score-items', views.ScoreItemViewSet)
router.register(r'score-statistics', views.ScoreStatisticsViewSet)
router.register(r'score-appeals', views.ScoreAppealViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
