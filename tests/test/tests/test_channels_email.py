import logging

from django.test import TestCase
from django.core import mail

from transmissions import message
from transmissions.models import Notification
from transmissions.channels import Channel
from transmissions.channels.email import DefaultEmailMessage
from . import factories


TRIGGER_SIMPLE = 'simple-email'
@message(TRIGGER_SIMPLE, subject='Hello World!')
class SimpleMessage(DefaultEmailMessage):
    template_name = 'test'

class EmailChannelTests(TestCase):
    def setUp(self):
        logging.disable(logging.WARNING)

    def test_email_channel(self):

        welcome_path = "{}.{}".format(SimpleMessage.__module__, SimpleMessage.__name__)
        trigger_settings = {TRIGGER_SIMPLE: welcome_path}
        with self.settings(TRANSMISSIONS_TRIGGERS=trigger_settings):
            user = factories.User()

            # Trigger notification
            notification = SimpleMessage.trigger(user)
            self.assertEqual(notification.trigger_name, TRIGGER_SIMPLE)
            self.assertEqual(notification.target_user, user)

            # Check channel and template are correct
            channel = Channel(notification)
            self.assertIsInstance(channel.message, SimpleMessage)


    def test_template_class(self):

        welcome_path = "{}.{}".format(SimpleMessage.__module__, SimpleMessage.__name__)
        trigger_settings = {TRIGGER_SIMPLE: welcome_path}
        with self.settings(TRANSMISSIONS_TRIGGERS=trigger_settings):

            user = factories.User()

            # Trigger notification
            notification = SimpleMessage.trigger(user)
            self.assertEqual(notification.trigger_name, TRIGGER_SIMPLE)
            self.assertEqual(notification.target_user, user)
            self.assertIsNone(notification.content)
            diff = notification.datetime_created - notification.datetime_scheduled
            self.assertLessEqual(abs(diff.seconds), 1)

            # Check channel and template are correct
            channel = Channel(notification)
            self.assertIsInstance(channel.message, DefaultEmailMessage)

    def test_send_plain_email(self):

        welcome_path = "{}.{}".format(SimpleMessage.__module__, SimpleMessage.__name__)
        trigger_settings = {TRIGGER_SIMPLE: welcome_path}
        with self.settings(TRANSMISSIONS_TRIGGERS=trigger_settings):

            user = factories.User()

            # Trigger notification
            notification = SimpleMessage.trigger(user)
            self.assertEqual(notification.trigger_name, TRIGGER_SIMPLE)
            self.assertEqual(notification.target_user, user)
            self.assertIsNone(notification.content)
            diff = notification.datetime_created - notification.datetime_scheduled
            self.assertLessEqual(abs(diff.seconds), 1)
            self.assertEqual(notification.status, Notification.Status.CREATED)

            # Send notification
            notification.send()

            # Check status
            self.assertEqual(notification.status, Notification.Status.SUCCESSFULLY_SENT)
            self.assertGreaterEqual(notification.datetime_processed, notification.datetime_scheduled)

            # Check email was sent
            self.assertEqual(len(mail.outbox), 1)
            self.assertEqual(mail.outbox[0].subject, 'Hello World!')
            self.assertEqual(mail.outbox[0].body, '')
            self.assertFalse(hasattr(mail.outbox[0], 'alternatives'))
