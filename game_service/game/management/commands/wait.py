import time
import ssl

from http.client import HTTPSConnection

from django.core.management.base import BaseCommand
from django.db.utils import OperationalError
from psycopg import OperationalError as Psycopg0pError


class Command(BaseCommand):
    """Django command to wait for database."""

    def handle(self, *args, **options):
        """Entrypoint for command."""
        self.stdout.write("Waiting for database...")
        db_up = False
        while db_up is False:
            try:
                self.check(databases=['default'])
                db_up = True
            except (Psycopg0pError, OperationalError):
                self.stdout.write('Database unavailable, waiting 1 second...')
                time.sleep(1)
        self.stdout.write(self.style.SUCCESS('Database available!'))

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
                    self.stdout.write(
                        self.style.SUCCESS('Auth service is up!')
                    )
                else:
                    self.stdout.write(
                        'Waiting for Auth service...'
                    )
                check.close()
            except Exception:
                self.stdout.write(
                    'Waiting for Auth service...'
                )
            time.sleep(1)

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
