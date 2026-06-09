from django.urls import path, include
from rest_framework_nested import routers
from . import views

router = routers.SimpleRouter(trailing_slash=False)
router.register(r'conversations', views.ConversationViewSet, basename='conversation')

conversations_router = routers.NestedSimpleRouter(router, r'conversations', lookup='conversation')
conversations_router.register(r'messages', views.MessageViewSet, basename='conversation-messages')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(conversations_router.urls)),
]
