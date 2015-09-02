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

from django.conf import settings
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from base64 import b64encode, b64decode
from django_extensions.db import fields
from django_enumfield import enum
from transmissions.exceptions import DuplicateNotification, ChannelSendException
from transmissions.channels import Channel
from django.utils import timezone
from django.core.urlresolvers import reverse, NoReverseMatch

import pickle


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

    target_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='notifications')
    trigger_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='notifications_sent',
                                     null=True, default=None)

    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    content_id = models.PositiveIntegerField(null=True, blank=True)
    content = generic.GenericForeignKey('content_type', 'content_id')
    data_pickled = models.TextField(blank=True, editable=False)

    datetime_created = models.DateTimeField(null=True, auto_now_add=True)
    datetime_scheduled = models.DateTimeField()
    datetime_processed = models.DateTimeField(null=True)
    datetime_seen = models.DateTimeField(null=True)
    datetime_consumed = models.DateTimeField(null=True)

    status = enum.EnumField(Status, default=Status.CREATED)

    @property
    def data(self):
        if not hasattr(self, '_data'):
            self._data = {} if len(self.data_pickled) <= 0 else pickle.loads(b64decode(self.data_pickled.encode()))
        return self._data

    @data.setter
    def data(self, value):
        self._data = value

    class Meta:
        index_together = [['datetime_processed', 'datetime_scheduled'],
                          ['target_user', 'datetime_scheduled'],
                          ['target_user', 'trigger_name', 'datetime_processed']]

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
        self.status = self.Status.CANCELLED
        self.save()

    def save(self, *args, **kwargs):
        """
        Store pickled data before saving
        """

        self.data_pickled = b64encode(pickle.dumps(self.data)).decode()
        super(Notification, self).save(*args, **kwargs)

    def __unicode__(self):
        return u'Notification #{} to user #{}: {}'.format(self.pk, self.target_user_id, self.trigger_name)


class TriggerBehavior(enum.Enum):
    DELETE_AFTER_PROCESSING = 0
    DEFAULT = 10
    TRIGGER_ONCE = 20
    TRIGGER_ONCE_PER_CONTENT = 25
    SEND_ONCE = 30
    SEND_ONCE_PER_CONTENT = 35
