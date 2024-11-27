import json
import time
from urllib.parse import parse_qs, urlparse

from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from unittest.mock import patch

from auth_app.utils.jwt import jwt_encode


class ViewTests(TestCase):
    """Tests for views."""

    def setUp(self):
        settings_manager = override_settings(SECURE_SSL_REDIRECT=False)
        settings_manager.enable()
        self.addCleanup(settings_manager.disable)
        self.secret_key = 'test_secret'
        self.email = 'test@test'
        self.exp = 3600
        self.payload = {
            'email': self.email,
            'exp': int(time.time()) + self.exp,
        }
        self.token = jwt_encode(self.payload, self.secret_key)
        self.client = Client()
        self.otp = '123456'
        self.jwt_secret_key = settings.JWT_SECRET_KEY
        session = self.client.session
        session['otp'] = self.otp
        session['email'] = self.email
        session['oauth_token'] = 'dummy_oauth_token'
        session.save()

    @patch('auth_app.views.get_user_data')
    @patch('auth_app.views.exchange_code_for_token')
    def test_oauth_callback_success(
            self,
            mock_exchange_code_for_token,
            mock_get_user_data
            ):
        """Test OAuth callback view with successful
            token exchange and user data retrieval."""
        mock_exchange_code_for_token.return_value = 'mock_token'
        mock_get_user_data.return_value = {
            'email': 'test@example.com',
            'login': 'testuser',
            'displayname': 'Test'
        }

        response = self.client.get(
                        '/oauth-callback/', {'code': 'test_code'}
                    )

        redirect_url = response['Location']
        parsed_url = urlparse(redirect_url)
        actual_params = parse_qs(parsed_url.query)

        expected_params = {
            'email': ['test@example.com'],
            'username': ['testuser'],
            'displayname': ['Test']
        }

        self.assertEqual(actual_params, expected_params)

    def test_oauth_callback_missing_code(self):
        """Test OAuth callback view with missing authorization code."""
        response = self.client.get('/oauth-callback/')
        self.assertEqual(response.status_code, 500)
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertEqual(
            response_data['error'], 'An internal server error occurred'
        )

    @patch('auth_service.utils.decorators.logger')
    @patch('auth_app.views.exchange_code_for_token')
    def test_oauth_callback_token_exchange_error(
        self,
        mock_exchange_code_for_token,
        mock_logger
    ):
        """Test OAuth callback view with token exchange error."""
        mock_exchange_code_for_token.side_effect = Exception(
            'Failed to exchange code for token'
        )

        response = \
            self.client.get('/oauth-callback/', {'code': 'test_code'})
        self.assertEqual(response.status_code, 500)
        self.assertIn('error', response.json())
        mock_logger.error.assert_called_with(
            'GET /oauth-callback/ - Error: Failed to exchange code for token'
        )
        self.assertEqual(
            response.json()['error'], 'An internal server error occurred'
        )

    @patch('auth_service.utils.decorators.logger')
    @patch('auth_app.views.get_user_data')
    @patch('auth_app.views.exchange_code_for_token')
    def test_oauth_callback_user_data_error(
        self,
        mock_exchange_code_for_token, mock_get_user_data, mock_logger
    ):
        """Test OAuth callback view with user data retrieval error."""
        mock_exchange_code_for_token.return_value = 'mock_token'
        mock_get_user_data.side_effect = Exception(
            'User data retrieval error'
        )
        response = \
            self.client.get('/oauth-callback/', {'code': 'test_code'})
        self.assertEqual(response.status_code, 500)
        self.assertIn('error', response.json())
        mock_logger.error.assert_called_with(
            'GET /oauth-callback/ - Error: User data retrieval error'
        )
        self.assertEqual(
            response.json()['error'], 'An internal server error occurred'
        )

    def test_verify_otp_failure(self):
        """Test if the OTP is incorrect and no JWT cookie is set."""
        response = self.client.post(
            reverse('verify-otp'),
            data=json.dumps({'otp': 'wrong_otp'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)
        self.assertIn('Invalid OTP', response.json()['error'])
        self.assertNotIn('jwt', response.cookies)

    @patch('django.conf.settings.JWT_SECRET_KEY', new='test_secret')
    def test_validate_jwt_view(self):
        """Test that the validate JWT view works."""
        url = reverse('validate-jwt')
        response = self.client.post(url, json.dumps({
            'jwt': self.token
        }), content_type='application/json')

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertNotIn('error', response_data)
        self.assertEqual(response_data['email'], self.email)

    @patch('django.conf.settings.JWT_SECRET_KEY', new='test_secret')
    def test_validate_jwt_view_expired_token(self):
        """Test validate JWT view with an expired token."""
        expired_payload = {
            'exp': time.time() - 3600,
            'iat': time.time() - 7200,
            'email': 'test@example.com'
        }
        expired_token = jwt_encode(expired_payload, 'test_secret')

        url = reverse('validate-jwt')
        response = self.client.post(url, json.dumps({
            'jwt': expired_token
        }), content_type='application/json')

        self.assertEqual(response.status_code, 401)
        response_data = json.loads(response.content)
        self.assertEqual(
            response_data['error'], 'Invalid token: Token has expired'
        )

    @patch('django.conf.settings.JWT_SECRET_KEY', new='test_secret')
    def test_validate_jwt_view_invalid_token(self):
        """Test validate JWT view with an invalid token."""
        invalid_token = 'invalid_token_string'

        url = reverse('validate-jwt')
        response = self.client.post(url, json.dumps({
            'jwt': invalid_token
        }), content_type='application/json')

        self.assertEqual(response.status_code, 401)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['error'].startswith('Invalid token'))

    @patch('django.conf.settings.JWT_SECRET_KEY', new='test_secret')
    def test_validate_jwt_view_invalid_json(self):
        """Test validate JWT view with invalid JSON."""
        url = reverse('validate-jwt')
        response = self.client.post(
            url,
            '{"invalid_json"',
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['error'], 'Invalid JSON')

    @patch('django.conf.settings.JWT_SECRET_KEY', new='test_secret')
    def test_validate_jwt_view_invalid_request_method(self):
        """Test validate JWT view with an invalid request method."""
        url = reverse('validate-jwt')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 405)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['error'], 'Method not allowed')

    @patch('django.conf.settings.JWT_SECRET_KEY', new='test_secret')
    def test_validate_jwt_view_missing_token(self):
        """Test validate JWT view with missing token."""
        url = reverse('validate-jwt')
        response = self.client.post(
            url,
            json.dumps({}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 401)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['error'], 'jwt is required')
