import logging

from django.test import TestCase

from transmissions import message
from transmissions.channels.sms import DefaultSMSMessage
from transmissions.channels import Channel
from . import factories


TRIGGER_SIMPLE = 'simple-sms'
@message(TRIGGER_SIMPLE, subject='Hello World!')
class SimpleMessage(DefaultSMSMessage):
    template_name = 'test'

class SmsChannelTests(TestCase):
    def setUp(self):
        logging.disable(logging.WARNING)

    def test_sms_channel(self):

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
            self.assertIsInstance(channel.message, DefaultSMSMessage)

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
            self.assertIsInstance(channel.message, DefaultSMSMessage)
