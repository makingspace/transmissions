import logging

from django.test import TestCase

from transmissions import message
from transmissions.channels import Channel
from transmissions.channels.email import DefaultEmailMessage
from . import factories


@message('welcome', behavior=None, subject='Hello World!')
class HelloWorld(DefaultEmailMessage):
    template_name = 'test'

class DecoratorTests(TestCase):

    def setUp(self):
        logging.disable(logging.WARNING)


    def test_simple(self):

        trigger_name = 'welcome'
        user = factories.User()

        welcome_path = "{}.{}".format(HelloWorld.__module__, HelloWorld.__name__)
        trigger_settings = {trigger_name: welcome_path}

        with self.settings(TRANSMISSIONS_TRIGGERS=trigger_settings):


            # Trigger notification
            notification = HelloWorld.trigger(user, datetime_scheduled=None)
            self.assertEqual(notification.trigger_name, trigger_name)
            self.assertEqual(notification.target_user, user)

            # Check channel and template are correct
            channel = Channel(notification)
            self.assertIsInstance(channel.message, HelloWorld)