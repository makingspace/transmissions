import logging

from django.test import TestCase
from django.utils import timezone

from transmissions.models import Notification, TriggerBehavior
from transmissions.channels.email import DefaultEmailMessage
from transmissions import exceptions, message
from . import factories


TRIGGER_SIMPLE = 'simple-model'
@message(TRIGGER_SIMPLE)
class SimpleMessage(DefaultEmailMessage):
    template_name = 'test'

TRIGGER_SEND_ONCE = 'send_once'
@message(TRIGGER_SEND_ONCE, behavior=TriggerBehavior.SEND_ONCE)
class SendOnceMessage(DefaultEmailMessage):
    template_name = 'test'

TRIGGER_SEND_ONCE_PER_CONTENT = 'send_once_per_content'
@message(TRIGGER_SEND_ONCE_PER_CONTENT, behavior=TriggerBehavior.SEND_ONCE_PER_CONTENT)
class SendOncePerContentMessage(DefaultEmailMessage):
    template_name = 'test'

TRIGGER_ONCE = 'trigger_once'
@message(TRIGGER_ONCE, behavior=TriggerBehavior.TRIGGER_ONCE)
class TriggerOnceMessage(DefaultEmailMessage):
    template_name = 'test'

TRIGGER_ONCE_PER_CONTENT = 'trigger_once_per_content'
@message(TRIGGER_ONCE_PER_CONTENT, behavior=TriggerBehavior.TRIGGER_ONCE_PER_CONTENT)
class TriggerOncePerContentMessage(DefaultEmailMessage):
    template_name = 'test'

TRIGGER_DELETE_AFTER_PROCESSING = 'trigger_delete_after'
@message(TRIGGER_DELETE_AFTER_PROCESSING, behavior=TriggerBehavior.DELETE_AFTER_PROCESSING)
class TriggerDeleteAfterMessage(DefaultEmailMessage):
    template_name = 'test'

class ModelTests(TestCase):

    def setUp(self):
        logging.disable(logging.WARNING)


    def test_trigger_notification(self):

        welcome_path = "{}.{}".format(SimpleMessage.__module__, SimpleMessage.__name__)
        trigger_settings = {TRIGGER_SIMPLE: welcome_path}
        with self.settings(TRANSMISSIONS_TRIGGERS=trigger_settings):

            user = factories.User()

            notification = SimpleMessage.trigger(user)

            self.assertEqual(notification.trigger_name, TRIGGER_SIMPLE)
            self.assertEqual(notification.target_user, user)
            self.assertIsNone(notification.content)

            diff = notification.datetime_created - notification.datetime_scheduled
            self.assertLessEqual(abs(diff.seconds), 1)

    def test_trigger_notification_with_data(self):

        welcome_path = "{}.{}".format(SimpleMessage.__module__, SimpleMessage.__name__)
        trigger_settings = {TRIGGER_SIMPLE: welcome_path}
        with self.settings(TRANSMISSIONS_TRIGGERS=trigger_settings):

            user = factories.User()

            data = {'hello': 'World', 'count': 5, 'date': timezone.now().date()}
            notification = SimpleMessage.trigger(user, data=data)

            self.assertEqual(notification.trigger_name, TRIGGER_SIMPLE)
            self.assertEqual(notification.target_user, user)
            self.assertIsNone(notification.content)

            diff = notification.datetime_created - notification.datetime_scheduled
            self.assertLessEqual(abs(diff.seconds), 1)

            notification = Notification.objects.get(pk=notification.id)
            self.assertEqual(notification.data, data)

    def test_trigger_notification_send_once(self):

        welcome_path = "{}.{}".format(SendOnceMessage.__module__, SendOnceMessage.__name__)
        trigger_settings = {TRIGGER_SEND_ONCE: welcome_path}
        with self.settings(TRANSMISSIONS_TRIGGERS=trigger_settings):

            user = factories.User()

            # First notification
            notification = SendOnceMessage.trigger(user)
            self.assertEqual(notification.trigger_name, TRIGGER_SEND_ONCE)
            self.assertEqual(notification.target_user, user)

            # Second notification
            with self.assertRaises(exceptions.DuplicateNotification):
                SendOnceMessage.trigger(user, silent=False)

    def test_trigger_notification_send_once_per_content(self):

        welcome_path = "{}.{}".format(SendOncePerContentMessage.__module__, SendOncePerContentMessage.__name__)
        trigger_settings = {TRIGGER_SEND_ONCE_PER_CONTENT: welcome_path}
        with self.settings(TRANSMISSIONS_TRIGGERS=trigger_settings):

            user = factories.User()
            other_user = factories.User()

            # First notification
            notification = SendOncePerContentMessage.trigger(user, content=user)
            self.assertEqual(notification.trigger_name, TRIGGER_SEND_ONCE_PER_CONTENT)
            self.assertEqual(notification.target_user, user)
            self.assertEqual(notification.content, user)

            # Second notification with different content
            notification = SendOncePerContentMessage.trigger(user, content=other_user)
            self.assertEqual(notification.trigger_name, TRIGGER_SEND_ONCE_PER_CONTENT)
            self.assertEqual(notification.target_user, user)
            self.assertEqual(notification.content, other_user)

            # Second notification with the same content
            with self.assertRaises(exceptions.DuplicateNotification):
                SendOncePerContentMessage.trigger(user, content=user, silent=False)

    def test_trigger_notification_trigger_once(self):

        welcome_path = "{}.{}".format(TriggerOnceMessage.__module__, TriggerOnceMessage.__name__)
        trigger_settings = {TRIGGER_ONCE: welcome_path}
        with self.settings(TRANSMISSIONS_TRIGGERS=trigger_settings):

            user = factories.User()

            # First notification
            notification = TriggerOnceMessage.trigger(user)
            self.assertEqual(notification.trigger_name, TRIGGER_ONCE)
            self.assertEqual(notification.target_user, user)

            # Second notification while 1st is not processed yet
            with self.assertRaises(exceptions.DuplicateNotification):
                TriggerOnceMessage.trigger(user, silent=False)

            # Mark 1st notification as processed
            notification.datetime_processed = timezone.now()
            notification.save()

            # Second notification while 1st IS NOW processed
            new_notification = TriggerOnceMessage.trigger(user)
            self.assertNotEqual(new_notification, notification)
            self.assertEqual(new_notification.trigger_name, TRIGGER_ONCE)
            self.assertEqual(new_notification.target_user, user)

    def test_trigger_notification_trigger_once_per_content(self):

        welcome_path = "{}.{}".format(TriggerOncePerContentMessage.__module__, TriggerOncePerContentMessage.__name__)
        trigger_settings = {TRIGGER_ONCE_PER_CONTENT: welcome_path}
        with self.settings(TRANSMISSIONS_TRIGGERS=trigger_settings):

            user = factories.User()
            other_user = factories.User()

            # First notification
            notification = TriggerOncePerContentMessage.trigger(user, content=user)
            self.assertEqual(notification.trigger_name, TRIGGER_ONCE_PER_CONTENT)
            self.assertEqual(notification.target_user, user)
            self.assertEqual(notification.content, user)

            # Second notification while 1st is not processed yet with different content
            other_notification = TriggerOncePerContentMessage.trigger(user, content=other_user)
            self.assertEqual(other_notification.trigger_name, TRIGGER_ONCE_PER_CONTENT)
            self.assertEqual(other_notification.target_user, user)
            self.assertEqual(other_notification.content, other_user)

            # Second notification while 1st is not processed yet
            with self.assertRaises(exceptions.DuplicateNotification):
                TriggerOncePerContentMessage.trigger(user, content=user, silent=False)

            # Mark 1st notification as processed
            notification.datetime_processed = timezone.now()
            notification.save()

            # Second notification while 1st IS NOW processed
            new_notification = TriggerOncePerContentMessage.trigger(user, content=user)
            self.assertNotEqual(new_notification, notification)
            self.assertEqual(new_notification.trigger_name, TRIGGER_ONCE_PER_CONTENT)
            self.assertEqual(new_notification.target_user, user)
            self.assertEqual(new_notification.content, user)

    def test_trigger_notification_delete_after_processing(self):

        welcome_path = "{}.{}".format(TriggerDeleteAfterMessage.__module__, TriggerDeleteAfterMessage.__name__)
        trigger_settings = {TRIGGER_DELETE_AFTER_PROCESSING: welcome_path}
        with self.settings(TRANSMISSIONS_TRIGGERS=trigger_settings):

            user = factories.User()

            # First notification
            notification = TriggerDeleteAfterMessage.trigger(user)
            self.assertEqual(notification.trigger_name, TRIGGER_DELETE_AFTER_PROCESSING)
            self.assertEqual(notification.target_user, user)

            # Second notification while 1st is not processed yet
            second_notification = TriggerDeleteAfterMessage.trigger(user)
            self.assertEqual(second_notification.trigger_name, TRIGGER_DELETE_AFTER_PROCESSING)
            self.assertEqual(second_notification.target_user, user)

            # Mark 1st notification as processed
            notification.send()

            with self.assertRaises(Notification.DoesNotExist):
                Notification.objects.get(pk=notification.id)

            second_notification = Notification.objects.get(pk=second_notification.id)
            self.assertEqual(second_notification.status, Notification.Status.CREATED)

    def test_invalid_data(self):

        welcome_path = "{}.{}".format(SimpleMessage.__module__, SimpleMessage.__name__)
        trigger_settings = {TRIGGER_SIMPLE: welcome_path}
        with self.settings(TRANSMISSIONS_TRIGGERS=trigger_settings):

            user = factories.User()

            notification = SimpleMessage.trigger(user)

            self.assertEqual(notification.trigger_name, TRIGGER_SIMPLE)
            self.assertEqual(notification.target_user, user)
            self.assertIsNone(notification.content)

            notification.data_pickled = "(dp0\n."
            delattr(notification, '_data')
            notification.save()

            self.assertEqual(notification.status, Notification.Status.BROKEN)
            self.assertEqual(notification.data, '{}')

