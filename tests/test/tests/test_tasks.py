import logging

from django.core import mail
from django.test import TestCase
from django.utils import timezone

from transmissions import tasks, message
from transmissions.channels import Channel
from transmissions.channels.email import DefaultEmailMessage
from transmissions.models import Notification
from . import factories

try:
    xrange
except NameError:
    xrange = range

TRIGGER_NAME = 'task_test'
TRIGGER_SUBJECT = 'This is a task test'

@message(TRIGGER_NAME, behavior=None, subject=TRIGGER_SUBJECT)
class TaskTestMessage(DefaultEmailMessage):
    template_name = 'test'


@message('broken', behavior=None, subject=TRIGGER_SUBJECT)
class BrokenMessage(DefaultEmailMessage):
    template_name = 'broken'

    def __init__(self, notification):
        super(BrokenMessage, self).__init__(notification)
        raise Exception('This message is broken at init')

class TasksTests(TestCase):

    def setUp(self):
        logging.disable(logging.WARNING)

        welcome_path = "{}.{}".format(TaskTestMessage.__module__, TaskTestMessage.__name__)
        self.trigger_settings = {TRIGGER_NAME: welcome_path}

    def test_process_task(self):

        with self.settings(TRANSMISSIONS_TRIGGERS=self.trigger_settings):
            user = factories.User()

            # Create trigger
            trigger_name = TRIGGER_NAME

            # Trigger notification
            notification = TaskTestMessage.trigger(user)
            self.assertEqual(notification.trigger_name, trigger_name)
            self.assertEqual(notification.target_user, user)
            self.assertEqual(notification.status, Notification.Status.CREATED)

            # Check channel and template are correct
            channel = Channel(notification)
            self.assertIsInstance(channel.message, TaskTestMessage)

            # Trigger single task
            tasks.process_notification(notification.id)
            notification = Notification.objects.get(pk=notification.id)

            # Check status
            self.assertEqual(notification.status, Notification.Status.SUCCESSFULLY_SENT)
            self.assertGreaterEqual(notification.datetime_processed, notification.datetime_scheduled)

            # Check email was sent
            self.assertEqual(len(mail.outbox), 1)
            self.assertEqual(mail.outbox[0].subject, TRIGGER_SUBJECT)


    def test_process_task_multiple_times(self):

        with self.settings(TRANSMISSIONS_TRIGGERS=self.trigger_settings):
            user = factories.User()

            # Create trigger
            trigger_name = TRIGGER_NAME

            # Trigger notification
            notification = TaskTestMessage.trigger(user)
            self.assertEqual(notification.trigger_name, trigger_name)
            self.assertEqual(notification.target_user, user)
            self.assertEqual(notification.status, Notification.Status.CREATED)

            # Check channel and template are correct
            channel = Channel(notification)
            self.assertIsInstance(channel.message, TaskTestMessage)

            # Trigger single task
            tasks.process_notification(notification.id)
            tasks.process_notification(notification.id)
            tasks.process_notification(notification.id)
            tasks.process_notification(notification.id)
            tasks.process_notification(notification.id)
            notification = Notification.objects.get(pk=notification.id)

            # Check status
            self.assertEqual(notification.status, Notification.Status.SUCCESSFULLY_SENT)
            self.assertGreaterEqual(notification.datetime_processed, notification.datetime_scheduled)

            # Check email was sent
            self.assertEqual(len(mail.outbox), 1)
            self.assertEqual(mail.outbox[0].subject, TRIGGER_SUBJECT)


    def test_process_all_notifications_task(self):

        with self.settings(TRANSMISSIONS_TRIGGERS=self.trigger_settings):
            users = [factories.User() for i in xrange(7)]
            notifications = []

            # Create trigger
            trigger_name = TRIGGER_NAME

            # Trigger notification
            for user in users:
                notification = TaskTestMessage.trigger(user)
                notifications.append(notification)
                self.assertEqual(notification.trigger_name, trigger_name)
                self.assertEqual(notification.target_user, user)
                self.assertEqual(notification.status, Notification.Status.CREATED)

                # Check channel and template are correct
                channel = Channel(notification)
                self.assertIsInstance(channel.message, TaskTestMessage)

            self.assertEqual(len(users), len(notifications))

            # Trigger task to process all remaining notifications
            processed_count = tasks.process_all_notifications()
            self.assertEqual(processed_count, len(notifications))

            # Check status
            for notification in notifications:
                notification = Notification.objects.get(pk=notification.id)
                self.assertEqual(notification.status, Notification.Status.SUCCESSFULLY_SENT)
                self.assertGreaterEqual(notification.datetime_processed, notification.datetime_scheduled)

            # Check email was sent
            self.assertEqual(len(mail.outbox), len(notifications))
            self.assertEqual(mail.outbox[0].subject, TRIGGER_SUBJECT)


            # Trigger task ... again
            processed_count = tasks.process_all_notifications()
            self.assertEqual(processed_count, 0)
            self.assertEqual(len(mail.outbox), len(notifications))


    def test_process_all_notifications_task_future_one(self):

        with self.settings(TRANSMISSIONS_TRIGGERS=self.trigger_settings):
            # Create trigger
            trigger_name = TRIGGER_NAME

            # Schedule notification for later
            user = factories.User()
            later_notification = TaskTestMessage.trigger(user, datetime_scheduled=timezone.now()+timezone.timedelta(days=2))
            self.assertEqual(later_notification.trigger_name, trigger_name)
            self.assertEqual(later_notification.target_user, user)
            self.assertEqual(later_notification.status, Notification.Status.CREATED)

            # Trigger task to process all remaining notifications
            processed_count = tasks.process_all_notifications()
            self.assertEqual(processed_count, 0)

            # Check status for later notification
            self.assertEqual(later_notification.status, Notification.Status.CREATED)
            self.assertIsNone(later_notification.datetime_processed)

            # Check no email was sent
            self.assertEqual(len(mail.outbox), 0)



    def test_process_all_notifications_task_except_future_one(self):

        with self.settings(TRANSMISSIONS_TRIGGERS=self.trigger_settings):
            users = [factories.User() for i in xrange(3)]
            notifications = []

            # Create trigger
            trigger_name = TRIGGER_NAME

            # Trigger notification
            for user in users:
                notification = TaskTestMessage.trigger(user)
                notifications.append(notification)
                self.assertEqual(notification.trigger_name, trigger_name)
                self.assertEqual(notification.target_user, user)
                self.assertEqual(notification.status, Notification.Status.CREATED)

                # Check channel and template are correct
                channel = Channel(notification)
                self.assertIsInstance(channel.message, TaskTestMessage)

            self.assertEqual(len(users), len(notifications))

            # Schedule notification for later
            user = factories.User()
            later_notification = TaskTestMessage.trigger(user, datetime_scheduled=timezone.now()+timezone.timedelta(days=2))
            self.assertEqual(later_notification.trigger_name, trigger_name)
            self.assertEqual(later_notification.target_user, user)
            self.assertEqual(later_notification.status, Notification.Status.CREATED)

            # Trigger task to process all remaining notifications
            processed_count = tasks.process_all_notifications()
            self.assertEqual(processed_count, len(notifications))

            # Check status
            for notification in notifications:
                notification = Notification.objects.get(pk=notification.id)
                self.assertEqual(notification.status, Notification.Status.SUCCESSFULLY_SENT)
                self.assertGreaterEqual(notification.datetime_processed, notification.datetime_scheduled)

            # Check email was sent
            self.assertEqual(len(mail.outbox), len(notifications))
            self.assertEqual(mail.outbox[0].subject, TRIGGER_SUBJECT)

            # Check status for later notification
            self.assertEqual(later_notification.status, Notification.Status.CREATED)
            self.assertIsNone(later_notification.datetime_processed)

            # Trigger task to process all remaining notifications
            processed_count = tasks.process_all_notifications()
            self.assertEqual(processed_count, 0)

    def test_process_broken(self):

        user = factories.User()

        # Trigger notification
        notification = BrokenMessage.trigger(user)
        self.assertEqual(notification.trigger_name, 'broken')
        self.assertEqual(notification.target_user, user)
        self.assertEqual(notification.status, Notification.Status.CREATED)

        # Trigger single task
        with self.assertRaisesMessage(Exception, 'This message is broken at init'):
            tasks.process_all_notifications()
        notification = Notification.objects.get(pk=notification.id)

        # Check that the notification is not retried
        num = tasks.process_all_notifications()
        self.assertEqual(num, 0)

        # Check status
        self.assertEqual(notification.status, Notification.Status.BROKEN)
        self.assertGreaterEqual(notification.datetime_processed, notification.datetime_scheduled)

        # Check email was sent
        self.assertEqual(len(mail.outbox), 0)