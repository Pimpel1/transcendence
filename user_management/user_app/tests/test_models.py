from django.contrib.auth import get_user_model
from django.test import TestCase


class ModelTests(TestCase):
    """Test creating a new user."""

    def test_create_user_with_email_successful(self):
        """Test creating a new user with an email is successful."""
        email = 'test@example.com'
        password = 'Testpass123'
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test the email for a new user is normalized."""
        sample_emails = [
            ['test1@EXAMPLE.COM', 'test1@example.com', 'user1'],
            ['Test2@Example.Com', 'Test2@example.com', 'user2'],
            ['TEST3@EXAMPLE.COM', 'TEST3@example.com', 'user3'],
            ['test4@example.com', 'test4@example.com', 'user4'],
        ]

        for email, expected, username in sample_emails:
            user = get_user_model().objects.create_user(
                email=email,
                username=username,
                displayname=username,
                password='password123'
            )
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_raises_error(self):
        """Test creating user without email raises error."""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('', 'sample123')

    def test_create_superuser(self):
        """Test creating a new superuser."""
        user = get_user_model().objects.create_superuser(
            'test@example.com',
            'test123'
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
