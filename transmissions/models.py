# -*- coding: utf-8 -*-
"""
    django-transmissions.models
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This is the core of django-transmissions with the following key models:
       * `Notification`: single communication events to a user with a `Trigger` on a given `Channel`
       * `Trigger`: Rule-set to create a `Notification`


    Additionally, a Channel is a mechanism or platform to send a Notification.
    Most commonly email or mobile push for iOS or Android.
"""

import pickle
from base64 import b64decode, b64encode

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.db import models
from django.utils import timezone

from django_enumfield import enum
from django_extensions.db import fields
from transmissions.channels import Channel
from transmissions.exceptions import ChannelSendException

if hasattr(settings, 'TRANSMISSION_USER_MODEL'):
    USER_MODEL = settings.TRANSMISSION_USER_MODEL
else:
    USER_MODEL = settings.AUTH_USER_MODEL


class BaseModel(models.Model):

    class Meta:
        abstract = True

    def get_admin_url(self):
        def view_name_for_model(model):
            return "admin:%s_%s_change" % (model._meta.app_label, model._meta.model_name)

        return reverse(view_name_for_model(self), args=(self.id,))


class Notification(BaseModel):

    """
    The instance of a message triggered to a user

    Notifications are single communication events so that we can track:
      * when it was triggered (by whom)
      * when was it scheduled for
      * when was it processed

    `Notification` are submitting a `Trigger` through a `Channel`
    """
    class Status(enum.Enum):
        CREATED = 0
        FAILED = -1
        CANCELLED = -2
        BROKEN = -3
        SUCCESSFULLY_SENT = 1

    uuid = fields.ShortUUIDField(unique=True, editable=False)

    trigger_name = models.CharField(db_index=True, max_length=50)

    target_user = models.ForeignKey(USER_MODEL, related_name='notifications')
    trigger_user = models.ForeignKey(USER_MODEL, related_name='notifications_sent',
                                     null=True, default=None)

    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    content_id = models.PositiveIntegerField(null=True, blank=True)
    content = GenericForeignKey('content_type', 'content_id')
    data_pickled = models.TextField(blank=True, editable=False)

    datetime_created = models.DateTimeField(null=True, auto_now_add=True)
    datetime_scheduled = models.DateTimeField(db_index=True)
    datetime_processed = models.DateTimeField(db_index=True, null=True)
    datetime_seen = models.DateTimeField(null=True)
    datetime_consumed = models.DateTimeField(null=True)

    status = enum.EnumField(Status, default=Status.CREATED)

    @property
    def data(self):
        if not hasattr(self, '_data'):
            if len(self.data_pickled) <= 0:
                self._data = {}
            else:
                self._data = pickle.loads(b64decode(self.data_pickled.encode()))
        return self._data

    @data.setter
    def data(self, value):
        self._data = value

    class Meta:
        index_together = [['datetime_processed', 'datetime_scheduled'],
                          ['target_user', 'datetime_scheduled'],
                          ['target_user', 'trigger_name', 'datetime_processed']]
        app_label = 'transmissions'

    def send(self):
        """ Process notification and send via designated channel
        """

        try:
            channel = Channel(self)
            # Notification is not needed anymore
            if not channel.check_validity():
                self.status = self.Status.CANCELLED
            else:
                channel.send()
                self.status = self.Status.SUCCESSFULLY_SENT
            if channel.message.behavior == TriggerBehavior.DELETE_AFTER_PROCESSING:
                self.delete()
        except ChannelSendException:
            self.status = self.Status.FAILED
        except:
            self.status = self.Status.BROKEN
            raise
        finally:
            if self.pk:
                self.datetime_processed = timezone.now()
                self.save()

    def cancel(self):
        self.datetime_processed = timezone.now()
        self.status = self.Status.CANCELLED
        self.save()

    def save(self, *args, **kwargs):
        """
        Store pickled data before saving
        """

        try:
            self.data_pickled = b64encode(pickle.dumps(self.data)).decode()
        except:
            self.data_pickled = b64encode(pickle.dumps('{}')).decode()
            self.status = self.Status.BROKEN
        super(Notification, self).save(*args, **kwargs)

    def __unicode__(self):
        return u'Notification #{} to user #{}: {}'.format(
            self.pk, self.target_user_id, self.trigger_name)


class TriggerBehavior(enum.Enum):
    """
    Unless otherwise specified, Trigger Behaviors look for the existence of
    notifications with the same triger name and same addressee.
    """
    # Delete the Notification after it's processed.
    DELETE_AFTER_PROCESSING = 0
    DEFAULT = 10
    # There can be only one unprocessed notification at a time.
    TRIGGER_ONCE = 20
    # There can be only one unprocessed notification for this content at a
    # time.
    TRIGGER_ONCE_PER_CONTENT = 25
    # There can be only one notification ever sent.
    SEND_ONCE = 30
    # There can be only one notification for this content ever sent.
    SEND_ONCE_PER_CONTENT = 35
    # Cancel all pending notifications when a new one is scheduled.
    LAST_ONLY = 40
