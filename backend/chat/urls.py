from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChatSessionViewSet

router = DefaultRouter()
router.register(r'sessions', ChatSessionViewSet, basename='chatsession')
# The router automatically creates:
# GET /sessions/
# POST /sessions/
# GET /sessions/<pk>/messages/
# POST /sessions/<pk>/ask/

urlpatterns = [
    path('', include(router.urls)),
]
