from optparse import make_option
from django.utils import timezone
from django.core.management.base import BaseCommand
from transmissions.models import Notification
from transmissions.lock import lock


class Command(BaseCommand):
    help = 'Retry to process failed notifications'

    option_list = BaseCommand.option_list + (
        make_option('--days', action='store', dest='days', type='int', default=7,
            help='Number of days since last failure'),
    )

    def handle(self, days, db_dry_run=False, *args, **options):

        since_datetime = timezone.now() - timezone.timedelta(days=days)

        notifications = Notification.objects.filter(datetime_scheduled__lte=timezone.now(),
                                                    datetime_scheduled__gte=since_datetime,
                                                    status=Notification.Status.FAILED).order_by('datetime_scheduled')

        for notification in notifications:
            self.stdout.write("Sending {}".format(notification))
            with lock('{0}'.format(notification.id)):
                notification.send()
