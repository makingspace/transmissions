import logging

from django.utils import timezone

from transmissions.exceptions import DuplicateNotification
from transmissions.lock import lock

register = {}


def message(trigger_name, behavior=None, **kwargs):
    def wrapper(cls):
        from django.contrib.contenttypes.models import ContentType
        from transmissions.models import TriggerBehavior, Notification

        cls.trigger_name = trigger_name
        if behavior in TriggerBehavior.values.keys():
            cls.behavior = behavior
        else:
            cls.behavior = TriggerBehavior.DEFAULT
        cls.kwargs = kwargs

        if trigger_name in register:
            logging.getLogger('django-transmissions').warning(
                'Duplicate definition for trigger {} at {} and {}.{}',
                trigger_name, register[trigger_name],
                cls.__module__, cls.__name__)

        register[trigger_name] = "{}.{}".format(cls.__module__, cls.__name__)

        def trigger(cls, target_user, trigger_user=None,
                    datetime_scheduled=None, content=None, data=None, silent=True):
            """
            Trigger a notification
            """

            # No need for a lock
            if cls.behavior in (TriggerBehavior.DEFAULT, TriggerBehavior.DELETE_AFTER_PROCESSING):
                return _trigger_within_lock(cls,
                                            target_user,
                                            trigger_user,
                                            datetime_scheduled,
                                            content,
                                            data,
                                            silent)

            # Acquire lock before triggering
            else:
                key = '{}@{}'.format(cls.trigger_name, target_user.id)
                if cls.behavior in (TriggerBehavior.SEND_ONCE_PER_CONTENT,
                                    TriggerBehavior.TRIGGER_ONCE_PER_CONTENT):
                    key += '+{}.{}'.format(content.__class__.__name__, content.id)

                with lock(key):
                    return _trigger_within_lock(cls,
                                                target_user,
                                                trigger_user,
                                                datetime_scheduled,
                                                content,
                                                data,
                                                silent)

        def _trigger_within_lock(cls, target_user, trigger_user=None,
                                 datetime_scheduled=None, content=None, data=None, silent=True):

            try:
                if (cls.behavior == TriggerBehavior.SEND_ONCE and
                        Notification.objects.filter(
                            target_user=target_user,
                            trigger_name=cls.trigger_name).exists()):
                    raise DuplicateNotification()

                if (cls.behavior == TriggerBehavior.SEND_ONCE_PER_CONTENT and
                        Notification.objects.filter(
                            target_user=target_user,
                            trigger_name=cls.trigger_name,
                            content_type=ContentType.objects.get_for_model(content),
                            content_id=content.id).exists()):
                    raise DuplicateNotification()

                if (cls.behavior == TriggerBehavior.TRIGGER_ONCE and
                        Notification.objects.filter(target_user=target_user,
                                                    trigger_name=cls.trigger_name,
                                                    datetime_processed__isnull=True).exists()):
                    raise DuplicateNotification()

                if (cls.behavior == TriggerBehavior.TRIGGER_ONCE_PER_CONTENT and
                        Notification.objects.filter(
                            target_user=target_user,
                            trigger_name=cls.trigger_name,
                            datetime_processed__isnull=True,
                            content_type=ContentType.objects.get_for_model(content),
                            content_id=content.id).exists()):
                    raise DuplicateNotification()

                if cls.behavior == TriggerBehavior.LAST_ONLY:
                    waiting_notifications = Notification.objects.filter(
                        target_user=target_user,
                        trigger_name=cls.trigger_name,
                        datetime_processed__isnull=True)
                    for waiting_notification in waiting_notifications:
                        waiting_notification.cancel()

            except DuplicateNotification:
                if not silent:
                    raise
                else:
                    return None

            if datetime_scheduled is None:
                datetime_scheduled = timezone.now()

            extra = {}
            if content is not None:
                extra['content'] = content
            if data is not None:
                extra['data'] = data

            notification = Notification.objects.create(trigger_name=cls.trigger_name,
                                                       target_user=target_user,
                                                       trigger_user=trigger_user,
                                                       datetime_scheduled=datetime_scheduled,
                                                       status=Notification.Status.CREATED,
                                                       **extra)
            return notification

        cls.trigger = classmethod(trigger)

        return cls

    return wrapper
