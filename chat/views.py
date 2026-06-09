from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.db.models import Q
from .models import Conversation, Message
from .serializers import (
    ConversationListSerializer, ConversationDetailSerializer,
    MessageSerializer
)
from .services import create_conversation, create_group_conversation, send_message, mark_as_read

User = get_user_model()


class ConversationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ConversationListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ConversationDetailSerializer
        return ConversationListSerializer

    def get_queryset(self):
        return Conversation.objects.filter(
            membership_set__user=self.request.user
        ).prefetch_related(
            'participants', 'messages'
        ).distinct()

    @action(detail=False, methods=['post'])
    def start(self, request):
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'error': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            other_user = User.objects.get(id=user_id, is_active=True)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        if other_user == request.user:
            return Response({'error': 'Cannot start conversation with yourself'}, status=status.HTTP_400_BAD_REQUEST)
        conv, created = create_conversation(request.user, other_user)
        serializer = ConversationListSerializer(conv, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def create_group(self, request):
        user_ids = request.data.get('user_ids', [])
        title = request.data.get('title', '').strip()
        if not isinstance(user_ids, list) or len(user_ids) < 1:
            return Response({'error': 'user_ids must be a list with at least 1 user'}, status=status.HTTP_400_BAD_REQUEST)
        all_ids = list(set(user_ids + [str(request.user.id)]))
        conv, created = create_group_conversation(request.user, all_ids, title)
        if not conv:
            return Response({'error': 'No valid users found'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = ConversationListSerializer(conv, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MessageViewSet(viewsets.GenericViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        conv_id = self.kwargs.get('conversation_pk')
        return Message.objects.filter(
            conversation_id=conv_id,
            conversation__membership_set__user=self.request.user
        ).select_related('sender').order_by('created_at')

    def list(self, request, conversation_pk=None):
        after = request.query_params.get('after')
        qs = self.get_queryset()
        if after:
            qs = qs.filter(id__gt=after)
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    def create(self, request, conversation_pk=None):
        try:
            conv = Conversation.objects.get(
                id=conversation_pk,
                membership_set__user=request.user
            )
        except Conversation.DoesNotExist:
            return Response({'error': 'Conversation not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        msg = send_message(conv, request.user, serializer.validated_data['content'])
        out = MessageSerializer(msg, context={'request': request})
        return Response(out.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='mark-read')
    def mark_read(self, request, conversation_pk=None):
        try:
            conv = Conversation.objects.get(
                id=conversation_pk,
                membership_set__user=request.user
            )
        except Conversation.DoesNotExist:
            return Response({'error': 'Conversation not found'}, status=status.HTTP_404_NOT_FOUND)
        mark_as_read(conv, request.user)
        return Response({'status': 'ok'})

    @action(detail=False, methods=['get'], url_path='unread-count')
    def unread_count(self, request, conversation_pk=None):
        try:
            conv = Conversation.objects.get(
                id=conversation_pk,
                membership_set__user=request.user
            )
        except Conversation.DoesNotExist:
            return Response({'error': 'Conversation not found'}, status=status.HTTP_404_NOT_FOUND)
        membership = conv.membership_set.get(user=request.user)
        count = conv.messages.filter(
            created_at__gt=membership.last_read_at
        ).count() if membership.last_read_at else conv.messages.count()
        return Response({'count': count})
