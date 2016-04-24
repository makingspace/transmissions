# -*- coding: utf-8 -*-
"""
    django-transmissions.channels
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Base class for channels

"""
import logging

from django.utils.module_loading import import_string
from django_enumfield import enum
from transmissions.exceptions import UnknownTriggerException, ChannelSendException


class Channel(object):

    def __init__(self, notification):
        self.notification = notification

        template_class = self.get_template()
        self.message = template_class(self.notification)

    class Types(enum.Enum):
        EMAIL = 1
        SMS = 2

    def get_template(self):

        # Dynamically load template class
        from transmissions.trigger import register
        if self.notification.trigger_name in register:
            return import_string(register[self.notification.trigger_name])

        raise UnknownTriggerException()

    def check_validity(self):
        """ Method called just before send() to determine if notification should still be sent

        :return: True if still valid, False if notification should be cancelled
        """
        return not hasattr(self.message, 'check_validity') or self.message.check_validity()

    def send(self):
        """ Send notification

        :param notification:
        :return:
        """

        try:
            return self.message.send()
        except Exception as e:
            logging.getLogger('django-transmissions').exception(e)
            raise ChannelSendException()
