import logging

from django.test import TestCase

from transmissions import message
from transmissions.models import Notification
from transmissions.channels.email import DefaultEmailMessage
from . import factories


TRIGGER_NAME = 'package_test'

@message(TRIGGER_NAME, behavior=None)
class PackageTestMessage(DefaultEmailMessage):
    template_name = 'test'


class PackageTests(TestCase):
    def setUp(self):
        logging.disable(logging.WARNING)

    def test_trigger(self):

        welcome_path = "{}.{}".format(PackageTestMessage.__module__, PackageTestMessage.__name__)
        trigger_settings = {TRIGGER_NAME: welcome_path}

        with self.settings(TRANSMISSIONS_TRIGGERS=trigger_settings):

            # Create user + trigger
            u = factories.User()

            # Trigger notification
            notification = PackageTestMessage.trigger(u)

            # Check notification
            self.assertEqual(notification.trigger_name, TRIGGER_NAME)
            self.assertEqual(notification.target_user, u)
            self.assertEqual(notification.status, Notification.Status.CREATED)