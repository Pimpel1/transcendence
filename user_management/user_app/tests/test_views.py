import json
import logging

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.test.utils import override_settings
from django.urls import reverse
from unittest.mock import patch
from user_app.models import UserProfile


User = get_user_model()


class UserViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password')
        self.user_profile = UserProfile.objects.create(user=self.user)
        self.user_profile.avatar.save(
            'avatar.png',
            SimpleUploadedFile(
                'avatar.png',
                b'file_content',
                content_type='image/png'))
        self.user_profile.save()

    @override_settings(SECURE_SSL_REDIRECT=False)
    @patch('user_app.views.get_wins_losses_status')
    @patch('user_app.views.get_user_info')
    def test_get_user_details(self,
                              mock_get_user_info,
                              mock_get_wins_losses_status):

        mock_get_user_info.return_value = {'email': 'test@example.com'}
        mock_get_wins_losses_status.return_value = {
            'wins': 1, 'losses': 1,
            'status': False
            }
        self.client.cookies['jwt'] = 'fake_jwt_token'

        self.client.login(username='testuser', password='password')
        response = self.client.get(reverse('user-details'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('email', response.json())
        self.assertIn('username', response.json())
        self.assertIn('displayname', response.json())
        self.assertIn('avatar', response.json())

    @override_settings(SECURE_SSL_REDIRECT=False)
    def test_get_user_details_no_jwt(self):
        response = self.client.get(reverse('user-details'))
        self.assertEqual(response.status_code, 401)
        self.assertIn('error', response.json())


class FriendViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password',
            displayname='Test Friend User'
            )
        self.user_profile = UserProfile.objects.create(user=self.user)
        self.user_profile.save()

    @override_settings(SECURE_SSL_REDIRECT=False)
    def test_get_friends(self):
        self.client.login(username='testuser', password='password')
        response = self.client.get(reverse('my-friends'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('friends', response.json())

    @override_settings(SECURE_SSL_REDIRECT=False)
    @patch('user_app.views.get_user_info')
    def test_send_friend_request(self, mock_get_user_info):
        mock_get_user_info.return_value = {'email': 'test@example.com'}

        self.client.cookies['jwt'] = 'fake_jwt_token'

        self.client.login(username='testuser', password='password')
        friend_user = User.objects.create_user(
            username='frienduser',
            email='friend@example.com',
            password='password',
            displayname='FriendRequest User'
            )
        friend_profile = UserProfile.objects.create(user=friend_user)
        friend_profile.save()

        response = self.client.post(
            reverse('send-friend-request'),
            json.dumps({'username': 'frienduser'}),
            content_type='application/json'
            )
        self.assertEqual(response.status_code, 200)
        self.assertIn('success', response.json())

    @override_settings(SECURE_SSL_REDIRECT=False)
    @patch('user_app.views.get_user_info')
    def test_delete_friend(self, mock_get_user_info):
        mock_get_user_info.return_value = {'email': 'test@example.com'}

        self.client.cookies['jwt'] = 'fake_jwt_token'

        self.client.login(username='testuser', password='password')
        friend_user = User.objects.create_user(
            username='frienduser',
            email='friend@example.com',
            password='password',
            displayname='FriendDeletion User'
            )
        friend_profile = UserProfile.objects.create(user=friend_user)
        friend_profile.save()
        self.user_profile.friends.add(friend_profile)
        self.user_profile.save()

        response = self.client.delete(
            reverse('delete-friend'),
            json.dumps({'username': 'frienduser'}),
            content_type='application/json'
            )
        self.assertEqual(response.status_code, 200)
        self.assertIn('success', response.json())


class HealthCheckTests(TestCase):
    @override_settings(SECURE_SSL_REDIRECT=False)
    def test_health_check(self):
        response = self.client.get(reverse('health-check'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok'})


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GetAllUsersTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password'
            )
        self.user_profile = UserProfile.objects.create(user=self.user)
        self.user_profile.save()

    @override_settings(SECURE_SSL_REDIRECT=False)
    @patch('user_app.services.get_non_friends_list')
    @patch('user_app.services.get_friend_requests_list')
    @patch('user_app.services.get_friends_list')
    @patch('user_app.views.get_user_info')
    def test_get_all_users_success(self, mock_get_user_info,
                                   mock_get_friends_list,
                                   mock_get_friend_requests_list,
                                   mock_get_non_friends_list):
        mock_get_user_info.return_value = {
            'username': 'testuser',
            'display_name': 'Test User'
            }
        mock_get_non_friends_list.return_value = [
            {'username': 'friend1'},
            {'username': 'friend2'}
            ]
        mock_get_friend_requests_list.return_value = [{'username': 'request1'}]
        mock_get_friends_list.return_value = [
            {'username': 'friend1'},
            {'username': 'friend2'}
            ]

        self.client.cookies['jwt'] = 'fake_jwt_token'

        response = self.client.get(reverse('all-users'))

        logger.info(f"Status Code: {response.status_code}")
        logger.info(f"Response Content: {response.content}")
        logger.info(f"Response Headers: {response.headers}")

        try:
            json_response = response.json()
            logger.info(f"JSON Response: {json_response}")
        except ValueError as e:
            logger.error(f"Failed to parse JSON: {str(e)}")

        self.assertEqual(response.status_code, 200)
        self.assertIn('users', response.json())
        self.assertIn('friend_requests', response.json())
        self.assertIn('friends', response.json())

    @override_settings(SECURE_SSL_REDIRECT=False)
    def test_get_all_users_no_jwt(self):
        response = self.client.get(reverse('all-users'))

        logger.info(f"Status Code (No JWT): {response.status_code}")
        logger.info(f"Response Content (No JWT): {response.content}")

        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())
