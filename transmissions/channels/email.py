# -*- coding: utf-8 -*-
"""
    django-transmissions.channels.email_mandrill
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Mandrill email channel

"""
from django.core.mail import EmailMessage


class DefaultEmailMessage(object):

    def __init__(self, notification):
        self.to = notification.target_user
        self.subject = self.kwargs.get('subject')
        self.body = ''

    def create_message(self):
        """ Create EmailMessage object from message data

        :return: EmailMessage
        """
        msg = EmailMessage(self.subject, body=self.body, to=[self.to.email])
        return msg

    def send(self):
        self.create_message().send()

    def check_validity(self):
        """ Email is valid and can be sent """
        return True
