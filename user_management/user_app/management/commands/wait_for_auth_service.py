import time
import ssl
from http.client import HTTPSConnection
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Django command to wait for auth-service."""

    def handle(self, *args, **options):
        """Entrypoint for command."""
        self.stdout.write("Waiting for auth_service...")
        auth_up = False
        while auth_up is False:
            try:
                context = ssl._create_unverified_context()
                check = HTTPSConnection('auth-service', 8001, context=context)
                check.request('GET', '/health/')
                response = check.getresponse()
                if response.status == 200:
                    auth_up = True
                    self.stdout.write(self.style.SUCCESS(
                        'Auth service is up!'))
                else:
                    self.stdout.write(f'Auth service returned\
                                      status code {response.status}.\
                                        Waiting 1 second...')
                check.close()
            except Exception as e:
                self.stdout.write(f'Auth service\
                                  not reachable: {e}. Waiting 1 second...')
            time.sleep(1)
