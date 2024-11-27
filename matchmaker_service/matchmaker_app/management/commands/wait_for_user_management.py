import ssl
import time

from django.core.management.base import BaseCommand
from http.client import HTTPSConnection


class Command(BaseCommand):
    """Django command to wait for user-management-service."""

    def handle(self, *args, **options):
        """Entrypoint for command."""
        self.stdout.write("Waiting for User management service...")
        user_up = False
        while user_up is False:
            try:
                context = ssl._create_unverified_context()
                check = HTTPSConnection(
                    'user-management',
                    8003,
                    context=context
                    )
                check.request('GET', '/health/')
                response = check.getresponse()
                if response.status == 200:
                    user_up = True
                    self.stdout.write(
                        self.style.SUCCESS('User management service is up!')
                    )
                else:
                    self.stdout.write(
                        'Waiting for User management service...'
                    )
                check.close()
            except Exception:
                self.stdout.write(
                    'Waiting for User management service...'
                )
            time.sleep(1)
