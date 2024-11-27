import io
import json
import urllib.error
import gzip

from django.test import TestCase
from unittest.mock import patch

from auth_app.utils.oauth import (
    exchange_code_for_token,
    get_user_data,
    unzip_response,
)


class OAuthUtilsTestCase(TestCase):
    """Tests for 42 OAuth 2.0 utilities."""

    @patch('urllib.request.urlopen')
    def test_exchange_code_for_token_http_error(self, mock_urlopen):
        """Test exchange_code_for_token with HTTP error."""
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url='',
            code=400,
            msg='',
            hdrs=None,
            fp=io.BytesIO(b'Error')
        )

        code = 'test_code'
        with self.assertRaises(Exception) as context:
            exchange_code_for_token(code)
        self.assertIn('HTTP Error: 400 - Error', str(context.exception))

    @patch('urllib.request.urlopen')
    def test_exchange_code_for_token_unexpected_error(self, mock_urlopen):
        """Test exchange_code_for_token with unexpected error."""
        mock_urlopen.side_effect = Exception('Unexpected error')

        code = 'test_code'
        with self.assertRaises(Exception) as context:
            exchange_code_for_token(code)
        self.assertIn('Unexpected Error: Unexpected error',
                      str(context.exception))

    @patch('urllib.request.urlopen')
    def test_get_user_data_success(self, mock_urlopen):
        """Test get_user_data with a successful response."""
        mock_response = io.BytesIO(gzip.compress(
            json.dumps({'name': 'John Doe'}).encode('utf-8')))
        mock_urlopen.return_value.__enter__.return_value = mock_response

        access_token = 'valid_access_token'
        result = get_user_data(access_token)
        self.assertEqual(result, {'name': 'John Doe'})

    @patch('urllib.request.urlopen')
    def test_get_user_data_http_error(self, mock_urlopen):
        """Test get_user_data with HTTP error."""
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url='',
            code=401,
            msg='',
            hdrs=None,
            fp=io.BytesIO(b'Unauthorized access')
        )

        access_token = 'invalid_access_token'
        with self.assertRaises(Exception) as context:
            get_user_data(access_token)
        self.assertIn('HTTP Error: 401 - Unauthorized access',
                      str(context.exception))

    @patch('urllib.request.urlopen')
    def test_get_user_data_unexpected_error(self, mock_urlopen):
        """Test get_user_data with unexpected error."""
        mock_urlopen.side_effect = Exception('Some unexpected error')

        access_token = 'any_access_token'
        with self.assertRaises(Exception) as context:
            get_user_data(access_token)
        self.assertEqual(str(context.exception),
                         'Unexpected Error: Some unexpected error')

    def test_unzip_response_success(self):
        """Test unzip_response with a successful response."""
        data = {'key': 'value'}
        json_data = json.dumps(data).encode('utf-8')
        compressed_data = gzip.compress(json_data)

        mock_response = io.BytesIO(compressed_data)

        # Call unzip_response with the mocked response
        result = unzip_response(mock_response)
        self.assertEqual(result, data)

    def test_unzip_response_invalid_gzip(self):
        """Test unzip_response with invalid gzip data."""
        mock_response = io.BytesIO(b'invalid gzip data')

        with self.assertRaises(OSError) as context:
            unzip_response(mock_response)
        self.assertIn('Not a gzipped file', str(context.exception))

    def test_unzip_response_empty(self):
        """Test unzip_response with an empty response body."""
        mock_response = io.BytesIO(b'')

        with self.assertRaises(ValueError) as context:
            unzip_response(mock_response)
        self.assertEqual(str(context.exception), 'Empty response body')
