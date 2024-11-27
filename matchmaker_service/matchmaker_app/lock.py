import logging
import time

from django.db import transaction
from django.utils import timezone

from .models import Lock


logger = logging.getLogger('matchmaker-service')


def acquire(*lock_names, timeout=5):
    if len(lock_names) == 1 and isinstance(lock_names[0], (list, tuple)):
        lock_names = lock_names[0]
    else:
        lock_names = list(lock_names)

    lock_order = {'player': 1, 'game': 2, 'tournament': 3}
    ordered_locks = \
        sorted(lock_names, key=lambda name: lock_order.get(name, 0))

    for name in ordered_locks:
        acquire_lock(name, timeout)


def acquire_lock(name, timeout=5):
    while True:
        try:
            now = timezone.now()
            lock_expiry = now - timezone.timedelta(seconds=timeout)
            with transaction.atomic():
                Lock.objects.filter(acquired_at__lte=lock_expiry).delete()
                _, created = Lock.objects.get_or_create(
                    name=name, defaults={'acquired_at': now}
                )
                if created:
                    break
                else:
                    logger.debug(f'Waiting for database lock \'{name}\'...')
                    time.sleep(0.1)

        except Exception:
            logger.debug(f'Waiting for database lock \'{name}\'...')
            time.sleep(0.1)


def release(*lock_names):
    if len(lock_names) == 1 and isinstance(lock_names[0], (list, tuple)):
        lock_names = lock_names[0]
    else:
        lock_names = list(lock_names)

    lock_order = {'player': 1, 'game': 2, 'tournament': 3}
    ordered_locks = \
        sorted(lock_names, key=lambda name: lock_order.get(name, 0))

    for name in ordered_locks:
        release_lock(name)


def release_lock(name):
    try:
        with transaction.atomic():
            Lock.objects.filter(name=name).delete()
    except Exception as e:
        logger.error(f'Failed to release database lock \'{name}\': {e}')
