from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, LauncherUserViewSet, AuthViewSet, LoginLogViewSet, DepartmentViewSet, ClassViewSet

router = DefaultRouter()
router.register(r'', UserViewSet)
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'login-logs', LoginLogViewSet)
router.register(r'departments', DepartmentViewSet)
router.register(r'classes', ClassViewSet)

launcher_router = DefaultRouter()
launcher_router.register(r'', LauncherUserViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('launcher/', include(launcher_router.urls)),
]
