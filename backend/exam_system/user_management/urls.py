from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, AuthViewSet, LoginLogViewSet

router = DefaultRouter()
router.register(r'', UserViewSet)
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'login-logs', LoginLogViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
