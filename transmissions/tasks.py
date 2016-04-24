# -*- coding: utf-8 -*-
"""
    django-transmissions.tasks
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tasks to run asynchronously via Celery
"""

from transmissions.lock import lock
from django.utils import timezone
from celery.task import task

@task(ignore_result=True)
def process_notification(notification_id):
    from transmissions.models import Notification
    with lock('{0}'.format(notification_id)):
        # Load notification
        notification = Notification.objects.get(pk=notification_id)

        # Process if not processed already
        if notification.status == Notification.Status.CREATED:
            notification.send()


@task(ignore_result=True, time_limit=55)
def process_all_notifications():
    from transmissions.models import Notification
    notification_ids = Notification.objects.filter(datetime_scheduled__lte=timezone.now(),
                                                   datetime_processed__isnull=True).order_by('datetime_scheduled')\
        .values_list('id', flat=True)

    for notification_id in notification_ids:
        process_notification.delay(notification_id)

    return len(notification_ids)
