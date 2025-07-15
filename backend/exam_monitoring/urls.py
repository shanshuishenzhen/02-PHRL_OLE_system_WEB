from django.urls import path
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from . import views

urlpatterns = [
    path('current/', permission_classes([IsAuthenticated])(views.current_exam), name='current-exam'),
    path('submit/', permission_classes([IsAuthenticated])(views.submit_exam), name='submit-exam'),
    path('monitor/', permission_classes([IsAuthenticated])(views.monitor_exam), name='monitor-exam'),
]