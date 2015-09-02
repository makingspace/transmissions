# -*- coding: utf-8 -*-
"""
    django-transmissions.factories
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Factories used by unit tests and sample code

"""
from factory import DjangoModelFactory, Sequence
from django.conf import settings


class User(DjangoModelFactory):

    class Meta:
        model = settings.AUTH_USER_MODEL

    username = Sequence(lambda n: 'factory_user_{}'.format(n))
    email = Sequence(lambda n: 'factory-user-{}@example.com'.format(n))
