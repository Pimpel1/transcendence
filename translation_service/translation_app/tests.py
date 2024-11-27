import json
import os

from django.conf import settings
from django.test import TestCase, Client, override_settings
from django.urls import reverse


class GetTranslationTests(TestCase):
    def setUp(self):
        settings_manager = override_settings(SECURE_SSL_REDIRECT=False)
        settings_manager.enable()
        self.addCleanup(settings_manager.disable)
        self.client = Client()

    def test_get_french_translation(self):
        url = reverse('get-translation', args=['fr'])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        try:
            translation_data = json.loads(response.content)
            self.assertIsInstance(translation_data, dict)
        except json.JSONDecodeError:
            self.fail("Response content is not valid JSON")

    def test_get_english_translation(self):
        url = reverse('get-translation', args=['en'])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        try:
            translation_data = json.loads(response.content)
            self.assertIsInstance(translation_data, dict)
        except json.JSONDecodeError:
            self.fail("Response content is not valid JSON")

    def test_default_to_english(self):
        translations_dir = os.path.join(
            settings.BASE_DIR, 'translation_files'
        )
        default_file = os.path.join(translations_dir, 'en.json')

        with open(default_file, 'r') as file:
            expected_data = json.load(file)

        url = reverse('get-translation', args=['notexisting'])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        try:
            response_data = json.loads(response.content)
            self.assertIsInstance(response_data, dict)
            self.assertEqual(response_data, expected_data)
        except json.JSONDecodeError:
            self.fail("Response content is not valid JSON")
