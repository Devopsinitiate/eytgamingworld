"""Tests for the chat app"""
import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient
from unittest.mock import patch

from .models import Conversation, ConversationParticipant, Message
from .services import (
    create_conversation, create_group_conversation,
    send_message, mark_as_read, get_read_by,
)

User = get_user_model()


class ChatModelTests(TestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(
            email='a@test.com', password='pass', username='user_a'
        )
        self.user_b = User.objects.create_user(
            email='b@test.com', password='pass', username='user_b'
        )
        self.user_c = User.objects.create_user(
            email='c@test.com', password='pass', username='user_c'
        )

    def test_create_direct_conversation(self):
        conv = Conversation.objects.create(type='direct')
        ConversationParticipant.objects.create(conversation=conv, user=self.user_a)
        ConversationParticipant.objects.create(conversation=conv, user=self.user_b)
        self.assertEqual(conv.type, 'direct')
        self.assertEqual(conv.participants.count(), 2)

    def test_create_group_conversation(self):
        conv = Conversation.objects.create(type='group', title='Test Group')
        for u in [self.user_a, self.user_b, self.user_c]:
            ConversationParticipant.objects.create(conversation=conv, user=u)
        self.assertEqual(conv.type, 'group')
        self.assertEqual(conv.participants.count(), 3)
        self.assertEqual(conv.title, 'Test Group')

    def test_create_message(self):
        conv = Conversation.objects.create(type='direct')
        ConversationParticipant.objects.create(conversation=conv, user=self.user_a)
        ConversationParticipant.objects.create(conversation=conv, user=self.user_b)
        msg = Message.objects.create(conversation=conv, sender=self.user_a, content='Hello')
        self.assertEqual(msg.content, 'Hello')
        self.assertEqual(msg.sender, self.user_a)
        self.assertIsNotNone(msg.created_at)
        self.assertFalse(msg.is_edited)

    def test_message_ordering(self):
        conv = Conversation.objects.create(type='direct')
        ConversationParticipant.objects.create(conversation=conv, user=self.user_a)
        ConversationParticipant.objects.create(conversation=conv, user=self.user_b)
        m1 = Message.objects.create(conversation=conv, sender=self.user_a, content='First')
        m2 = Message.objects.create(conversation=conv, sender=self.user_b, content='Second')
        msgs = conv.messages.all()
        self.assertEqual(list(msgs), [m1, m2])

    def test_conversation_participant_unique(self):
        conv = Conversation.objects.create(type='direct')
        ConversationParticipant.objects.create(conversation=conv, user=self.user_a)
        with self.assertRaises(Exception):
            ConversationParticipant.objects.create(conversation=conv, user=self.user_a)

    def test_message_str(self):
        conv = Conversation.objects.create(type='direct')
        ConversationParticipant.objects.create(conversation=conv, user=self.user_a)
        ConversationParticipant.objects.create(conversation=conv, user=self.user_b)
        msg = Message.objects.create(conversation=conv, sender=self.user_a, content='Hello')
        self.assertIn('user_a', str(msg))


class ChatServiceTests(TestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(
            email='a@test.com', password='pass', username='user_a'
        )
        self.user_b = User.objects.create_user(
            email='b@test.com', password='pass', username='user_b'
        )
        self.user_c = User.objects.create_user(
            email='c@test.com', password='pass', username='user_c'
        )

    def test_create_conversation_new(self):
        conv, created = create_conversation(self.user_a, self.user_b)
        self.assertTrue(created)
        self.assertEqual(conv.type, 'direct')
        self.assertIn(self.user_a, conv.participants.all())
        self.assertIn(self.user_b, conv.participants.all())

    def test_create_conversation_existing(self):
        conv1, _ = create_conversation(self.user_a, self.user_b)
        conv2, created = create_conversation(self.user_a, self.user_b)
        self.assertFalse(created)
        self.assertEqual(conv1.id, conv2.id)

    def test_create_conversation_same_users_reversed(self):
        conv1, _ = create_conversation(self.user_a, self.user_b)
        conv2, created = create_conversation(self.user_b, self.user_a)
        self.assertFalse(created)
        self.assertEqual(conv1.id, conv2.id)

    def test_create_group_conversation(self):
        conv, created = create_group_conversation(
            self.user_a,
            [str(self.user_b.id), str(self.user_c.id)],
            title='Gaming Group'
        )
        self.assertTrue(created)
        self.assertEqual(conv.type, 'group')
        self.assertEqual(conv.title, 'Gaming Group')
        self.assertEqual(conv.participants.count(), 3)

    def test_create_group_auto_adds_creator(self):
        conv, created = create_group_conversation(
            self.user_a,
            [str(self.user_b.id)],
        )
        self.assertTrue(created)
        self.assertEqual(conv.participants.count(), 2)
        self.assertIn(self.user_a, conv.participants.all())

    def test_create_group_no_valid_users(self):
        fake_id = '00000000-0000-0000-0000-000000000000'
        conv, created = create_group_conversation(self.user_a, [fake_id])
        self.assertIsNone(conv)
        self.assertFalse(created)

    def test_send_message(self):
        conv, _ = create_conversation(self.user_a, self.user_b)
        msg = send_message(conv, self.user_a, 'Test message')
        self.assertEqual(msg.content, 'Test message')
        self.assertEqual(msg.sender, self.user_a)
        self.assertEqual(msg.conversation, conv)
        conv.refresh_from_db()
        self.assertIsNotNone(conv.updated_at)

    def test_mark_as_read(self):
        conv, _ = create_conversation(self.user_a, self.user_b)
        msg = send_message(conv, self.user_a, 'Hello')
        membership = conv.membership_set.get(user=self.user_b)
        self.assertIsNone(membership.last_read_at)
        mark_as_read(conv, self.user_b)
        membership.refresh_from_db()
        self.assertIsNotNone(membership.last_read_at)

    def test_get_read_by(self):
        import time
        conv, _ = create_conversation(self.user_a, self.user_b)
        msg = send_message(conv, self.user_a, 'Hello')
        # Initially no one has read it
        self.assertEqual(len(get_read_by(msg)), 0)
        time.sleep(0.01)
        # After marking as read, user_b should show up
        mark_as_read(conv, self.user_b)
        result = get_read_by(msg)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], self.user_b.id)

    def test_group_conversation_unique_participants(self):
        """Creating the same group twice should be allowed (no unique constraint on participant set)"""
        conv1, _ = create_group_conversation(
            self.user_a, [str(self.user_b.id), str(self.user_c.id)], 'Group'
        )
        conv2, _ = create_group_conversation(
            self.user_a, [str(self.user_b.id), str(self.user_c.id)], 'Group'
        )
        self.assertNotEqual(conv1.id, conv2.id)


class ChatAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_a = User.objects.create_user(
            email='a@test.com', password='pass', username='user_a'
        )
        self.user_b = User.objects.create_user(
            email='b@test.com', password='pass', username='user_b'
        )
        self.client.force_authenticate(user=self.user_a)

    def _get_csrf(self):
        from django.middleware.csrf import _get_new_csrf_string
        return _get_new_csrf_string()

    def test_list_conversations_empty(self):
        resp = self.client.get('/api/v1/chat/conversations')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        results = data.get('results', data)
        self.assertEqual(len(results), 0)

    def test_start_conversation(self):
        resp = self.client.post('/api/v1/chat/conversations/start', {
            'user_id': str(self.user_b.id)
        }, format='json')
        self.assertIn(resp.status_code, [200, 201])
        data = resp.json()
        self.assertEqual(data['type'], 'direct')

    def test_start_conversation_requires_user_id(self):
        resp = self.client.post('/api/v1/chat/conversations/start', {}, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_start_conversation_self(self):
        resp = self.client.post('/api/v1/chat/conversations/start', {
            'user_id': str(self.user_a.id)
        }, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_start_conversation_nonexistent(self):
        fake = '00000000-0000-0000-0000-000000000000'
        resp = self.client.post('/api/v1/chat/conversations/start', {
            'user_id': fake
        }, format='json')
        self.assertEqual(resp.status_code, 404)

    def test_start_conversation_idempotent(self):
        resp1 = self.client.post('/api/v1/chat/conversations/start', {
            'user_id': str(self.user_b.id)
        }, format='json')
        resp2 = self.client.post('/api/v1/chat/conversations/start', {
            'user_id': str(self.user_b.id)
        }, format='json')
        self.assertEqual(resp1.json()['id'], resp2.json()['id'])
        self.assertEqual(resp1.status_code, 201)
        self.assertEqual(resp2.status_code, 200)

    def test_create_group_conversation(self):
        resp = self.client.post('/api/v1/chat/conversations/create_group', {
            'user_ids': [str(self.user_b.id)],
            'title': 'Test Group',
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertEqual(data['type'], 'group')
        self.assertIn('Test Group', data.get('title', ''))

    def test_create_group_requires_user_ids(self):
        resp = self.client.post('/api/v1/chat/conversations/create_group', {
            'title': 'Empty'
        }, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_create_group_empty_list(self):
        resp = self.client.post('/api/v1/chat/conversations/create_group', {
            'user_ids': []
        }, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_send_and_list_messages(self):
        resp = self.client.post('/api/v1/chat/conversations/start', {
            'user_id': str(self.user_b.id)
        }, format='json')
        conv_id = resp.json()['id']

        resp = self.client.post(f'/api/v1/chat/conversations/{conv_id}/messages', {
            'content': 'Hello from test',
            'sender_id': str(self.user_a.id),
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        msg_data = resp.json()
        self.assertEqual(msg_data['content'], 'Hello from test')

        resp = self.client.get(f'/api/v1/chat/conversations/{conv_id}/messages')
        self.assertEqual(resp.status_code, 200)
        msgs = resp.json().get('results', resp.json())
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0]['content'], 'Hello from test')

    def test_message_polling_after_id(self):
        resp = self.client.post('/api/v1/chat/conversations/start', {
            'user_id': str(self.user_b.id)
        }, format='json')
        conv_id = resp.json()['id']

        m1 = self.client.post(f'/api/v1/chat/conversations/{conv_id}/messages', {
            'content': 'First', 'sender_id': str(self.user_a.id),
        }, format='json').json()

        self.client.post(f'/api/v1/chat/conversations/{conv_id}/messages', {
            'content': 'Second', 'sender_id': str(self.user_a.id),
        }, format='json').json()

        resp = self.client.get(f'/api/v1/chat/conversations/{conv_id}/messages?after={m1["id"]}')
        msgs = resp.json().get('results', resp.json())
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0]['content'], 'Second')

    def test_mark_read(self):
        resp = self.client.post('/api/v1/chat/conversations/start', {
            'user_id': str(self.user_b.id)
        }, format='json')
        conv_id = resp.json()['id']

        self.client.post(f'/api/v1/chat/conversations/{conv_id}/messages', {
            'content': 'Test', 'sender_id': str(self.user_a.id),
        }, format='json')

        resp = self.client.post(f'/api/v1/chat/conversations/{conv_id}/messages/mark-read', {}, format='json')
        self.assertEqual(resp.status_code, 200)

    def test_unread_count(self):
        resp = self.client.post('/api/v1/chat/conversations/start', {
            'user_id': str(self.user_b.id)
        }, format='json')
        conv_id = resp.json()['id']

        self.client.post(f'/api/v1/chat/conversations/{conv_id}/messages', {
            'content': 'Unread msg', 'sender_id': str(self.user_a.id),
        }, format='json')

        resp = self.client.get(f'/api/v1/chat/conversations/{conv_id}/messages/unread-count')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('count', data)

    def test_list_conversations_after_message(self):
        self.client.post('/api/v1/chat/conversations/start', {
            'user_id': str(self.user_b.id)
        }, format='json')
        resp = self.client.get('/api/v1/chat/conversations')
        self.assertEqual(resp.status_code, 200)

    def test_unauthenticated_access(self):
        self.client.force_authenticate(user=None)
        resp = self.client.get('/api/v1/chat/conversations')
        self.assertIn(resp.status_code, [401, 403])

    def test_send_message_to_nonexistent_conversation(self):
        fake = '00000000-0000-0000-0000-000000000000'
        resp = self.client.post(f'/api/v1/chat/conversations/{fake}/messages', {
            'content': 'Test', 'sender_id': str(self.user_a.id),
        }, format='json')
        self.assertEqual(resp.status_code, 404)


class ChatSignalTests(TestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(
            email='a@test.com', password='pass', username='user_a'
        )
        self.user_b = User.objects.create_user(
            email='b@test.com', password='pass', username='user_b'
        )
        from chat.services import create_conversation
        self.conv, _ = create_conversation(self.user_a, self.user_b)

    def test_notification_created_for_offline_recipient(self):
        from chat.services import send_message
        from notifications.models import Notification
        self.user_b.is_online = False
        self.user_b.save()
        with patch.object(Notification, 'create_notification') as mock_create:
            msg = send_message(self.conv, self.user_a, 'Hey there')
            mock_create.assert_called_once()
            args, kwargs = mock_create.call_args
            self.assertEqual(kwargs['user'], self.user_b)
            self.assertIn('user_a', kwargs['title'])
            self.assertEqual(kwargs['notification_type'], 'message')

    def test_no_notification_for_online_recipient(self):
        from chat.services import send_message
        from notifications.models import Notification
        self.user_b.is_online = True
        self.user_b.save()
        with patch.object(Notification, 'create_notification') as mock_create:
            send_message(self.conv, self.user_a, 'Hey there')
            mock_create.assert_not_called()

    def test_no_notification_for_sender(self):
        """Sender should not get a notification for their own message"""
        from chat.services import send_message
        from notifications.models import Notification
        self.user_a.is_online = False
        self.user_a.save()
        self.user_b.is_online = False
        self.user_b.save()
        with patch.object(Notification, 'create_notification') as mock_create:
            send_message(self.conv, self.user_a, 'Hey there')
            # Should only notify user_b, not user_a
            mock_create.assert_called_once()
            args, kwargs = mock_create.call_args
            self.assertEqual(kwargs['user'], self.user_b)

    def test_no_notification_for_created_false(self):
        """post_save with created=False should not trigger notification"""
        from chat.services import send_message
        from notifications.models import Notification
        with patch.object(Notification, 'create_notification') as mock_create:
            msg = send_message(self.conv, self.user_a, 'Test')
            msg.content = 'Updated'
            msg.save()
            # save() triggers post_save with created=False
            # mock_create should still have been called exactly once (from send_message)
            self.assertEqual(mock_create.call_count, 1)
