# -*- coding: utf-8 -*-
"""
    django-transmissions.exceptions
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module contains all exceptions used by the Django Transmissions module
"""


class DuplicateNotification(Exception):
    """ Notification could not be triggered again because of trigger limitation """

class ChannelSendException(Exception):
    """ Notification could not be sent through this channel """

class UnknownTriggerException(Exception):
    """ Notification's trigger is not defined """