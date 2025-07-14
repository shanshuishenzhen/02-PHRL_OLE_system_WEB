from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ExamViewSet, ExamRoomViewSet, ExamRegistrationViewSet, 
    ExamRecordViewSet, ExamAnswerViewSet, ExamSnapshotViewSet,
    ExamNotificationViewSet
)

router = DefaultRouter()
router.register(r'exams', ExamViewSet, basename='exam')
router.register(r'exam-rooms', ExamRoomViewSet, basename='exam-room')
router.register(r'exam-registrations', ExamRegistrationViewSet, basename='exam-registration')
router.register(r'exam-records', ExamRecordViewSet, basename='exam-record')
router.register(r'exam-answers', ExamAnswerViewSet, basename='exam-answer')
router.register(r'exam-snapshots', ExamSnapshotViewSet, basename='exam-snapshot')
router.register(r'exam-notifications', ExamNotificationViewSet, basename='exam-notification')

urlpatterns = [
    path('', include(router.urls)),
]
