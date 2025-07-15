from django.urls import path
from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny
from . import views

urlpatterns = [
    path('', permission_classes([AllowAny])(views.route_view), name='api_gateway_root'),
    path('<path:path>', permission_classes([AllowAny])(views.route_view), name='api_gateway_route'),
]