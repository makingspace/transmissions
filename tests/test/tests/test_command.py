import logging
from datetime import date, time

import pytz
from django.test import TestCase
from django.utils import timezone
from django.core.management import call_command

import mock
from transmissions import message
from transmissions.models import Notification
from transmissions.channels.email import DefaultEmailMessage
from . import factories


@message('command_test', behavior=None, subject='Hello World!')
class FailedAttemptMessage(DefaultEmailMessage):
    template_name = 'test'

class CommandTests(TestCase):

    def setUp(self):
        logging.disable(logging.WARNING)

    def test_simple(self):

        trigger_name = 'command_test'
        user = factories.User()

        # Trigger notification
        notification = FailedAttemptMessage.trigger(user, datetime_scheduled=None)
        self.assertEqual(notification.trigger_name, trigger_name)
        self.assertEqual(notification.target_user, user)
        self.assertEqual(notification.status, Notification.Status.CREATED)

        # Test
        call_command('retry_failed_notifications', days=8)
        notification = Notification.objects.get(pk=notification.id)
        self.assertEqual(notification.status, Notification.Status.CREATED)

        # Update to failed
        notification.status = Notification.Status.FAILED
        notification.save()

        # Test
        call_command('retry_failed_notifications', days=8)
        notification = Notification.objects.get(pk=notification.id)
        self.assertEqual(notification.status, Notification.Status.SUCCESSFULLY_SENT)


    @mock.patch.object(timezone, 'now')
    def test_older(self, mock_timezone_now):

        # Mock time to now
        mock_time = time(8, 0, tzinfo=pytz.utc)
        today = date.today()
        mock_timezone_now.return_value = timezone.datetime.combine(today, mock_time)

        trigger_name = 'command_test'
        user = factories.User()

        # Trigger notification
        notification = FailedAttemptMessage.trigger(user, datetime_scheduled=None)
        self.assertEqual(notification.trigger_name, trigger_name)
        self.assertEqual(notification.target_user, user)
        self.assertEqual(notification.status, Notification.Status.CREATED)

        # Test
        call_command('retry_failed_notifications', days=8)
        notification = Notification.objects.get(pk=notification.id)
        self.assertEqual(notification.status, Notification.Status.CREATED)

        # Update to failed
        notification.status = Notification.Status.FAILED
        notification.save()

        # Move 10 days in the future
        mock_timezone_now.return_value += timezone.timedelta(days=10)

        # Test
        call_command('retry_failed_notifications', days=8)
        notification = Notification.objects.get(pk=notification.id)
        self.assertEqual(notification.status, Notification.Status.FAILED)