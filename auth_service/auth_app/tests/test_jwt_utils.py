import base64
import hashlib
import hmac
import json
import time

from django.test import TestCase
from auth_app.utils.jwt import (
    base64url_encode,
    base64url_decode,
    jwt_encode,
    jwt_decode,
    make_jwt,
)


class JWTUtilsTests(TestCase):
    """Tests for JWT utilities."""

    def setUp(self) -> None:
        self.secret_key = 'test_secret'
        self.email = 'testuser'
        self.exp = 3600
        self.payload = {
            'username': 'testuser',
            'displayname': 'Test User',
            'email': self.email,
            'exp': int(time.time()) + self.exp
        }
        self.raw_user_info = json.dumps(self.payload)

    def test_base64url_encode(self):
        """Test base64url encoding."""
        data = b'Hello, world!'
        encoded = base64url_encode(data)
        self.assertEqual(encoded, 'SGVsbG8sIHdvcmxkIQ')

    def test_base64url_decode(self):
        """Test base64url decoding."""
        encoded = 'SGVsbG8sIHdvcmxkIQ'
        decoded = base64url_decode(encoded)
        self.assertEqual(decoded, b'Hello, world!')

    def test_jwt_encode(self):
        """Test JWT encoding."""
        token = jwt_encode(self.payload, self.secret_key)
        self.assertIsNotNone(token)

        encoded_header, encoded_payload, encoded_signature = token.split('.')

        # Compare encoded header without padding
        expected_header = base64.urlsafe_b64encode(
            json.dumps({'alg': 'HS256', 'typ': 'JWT'})
            .encode()).decode().rstrip("=")
        self.assertEqual(encoded_header, expected_header)

        # Compare encoded payload without padding
        expected_payload = base64.urlsafe_b64encode(
            json.dumps(self.payload)
            .encode()).decode().rstrip("=")
        self.assertEqual(encoded_payload, expected_payload)

        # Decode and verify header
        decoded_header = json.loads(base64.urlsafe_b64decode(
            encoded_header + '==').decode('utf-8'))
        self.assertEqual(decoded_header,
                         {'alg': 'HS256', 'typ': 'JWT'})

        # Decode and verify payload
        decoded_payload = json.loads(base64.urlsafe_b64decode(
            encoded_payload + '==').decode('utf-8'))
        self.assertEqual(decoded_payload, self.payload)

        # Verify signature
        expected_signature = hmac.new(
            self.secret_key.encode(),
            f'{encoded_header}.{encoded_payload}'.encode(),
            hashlib.sha256
        ).digest()
        expected_encoded_signature = base64.urlsafe_b64encode(
            expected_signature).decode().rstrip("=")

        self.assertEqual(encoded_signature,
                         expected_encoded_signature)

    def test_jwt_decode(self):
        """Test JWT decoding."""
        # First, encode the token
        token = jwt_encode(self.payload, self.secret_key)
        self.assertIsNotNone(token)

        # Now, decode the token
        decoded_payload = jwt_decode(token, self.secret_key)
        self.assertEqual(decoded_payload, self.payload)

        # Split the token to verify components
        encoded_header, encoded_payload, encoded_signature = token.split('.')

        # Verify header
        decoded_header = json.loads(base64.urlsafe_b64decode(
            encoded_header + '==').decode('utf-8'))
        self.assertEqual(decoded_header,
                         {'alg': 'HS256', 'typ': 'JWT'})

        # Verify payload
        decoded_payload = json.loads(base64.urlsafe_b64decode(
            encoded_payload + '==').decode('utf-8'))
        self.assertEqual(decoded_payload, self.payload)

        # Verify signature
        expected_signature = hmac.new(
            self.secret_key.encode(),
            f'{encoded_header}.{encoded_payload}'.encode(),
            hashlib.sha256
        ).digest()
        expected_encoded_signature = base64.urlsafe_b64encode(
            expected_signature).rstrip(b'=').decode()

        self.assertEqual(encoded_signature,
                         expected_encoded_signature)

    def test_make_jwt_creates_valid_token(self):
        """Test that make_jwt creates a valid JWT token."""
        token = make_jwt(self.secret_key, self.raw_user_info, self.exp)
        decoded_payload = jwt_decode(token, self.secret_key)
        self.assertEqual(decoded_payload['email'], self.payload['email'])
        self.assertAlmostEqual(
            decoded_payload['exp'], self.payload['exp'], delta=1
            )

    def test_make_jwt_expiration(self):
        """Test that the expiration time in the JWT is correctly set."""
        exp = 120
        expected_exp_time = int(time.time()) + exp
        token = make_jwt(self.secret_key, self.raw_user_info, exp)
        decoded_payload = jwt_decode(token, self.secret_key)
        self.assertAlmostEqual(
            decoded_payload['exp'], expected_exp_time, delta=1
            )

    def test_make_jwt_invalid_secret(self):
        """Test that a token cannot be decoded with another secret."""
        token = make_jwt(self.secret_key, self.raw_user_info, self.exp)
        with self.assertRaises(ValueError) as cm:
            jwt_decode(token, 'wrong_secret')
        self.assertIn('Invalid token signature', str(cm.exception))

    def test_make_jwt_expired_token(self):
        """Test that a JWT token expires correctly."""
        exp = -10
        token = make_jwt(self.secret_key, self.raw_user_info, exp)
        with self.assertRaises(ValueError) as cm:
            jwt_decode(token, self.secret_key)
        self.assertIn('Token has expired', str(cm.exception))
