import logging
import threading

from django.conf import settings
from django.core.mail import send_mail
from django.utils.crypto import get_random_string


logger = logging.getLogger('auth-service')


def get_otp():
    return get_random_string(length=6, allowed_chars='0123456789')


def email_otp(email, otp):
    def send_email():
        try:
            send_mail(
                    'Your OTP Code',
                    f'Your OTP code is {otp}',
                    settings.EMAIL_HOST_USER,
                    [email],
                    fail_silently=False,
                )
        except Exception as e:
            logger.error(f'Something went wrong with sending the email: {e}')

    threading.Thread(target=send_email).start()
