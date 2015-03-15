# -*- coding: utf-8 -*-
"""
    django-transmissions.factories
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Factories used by unit tests and sample code

"""
from factory import DjangoModelFactory, Sequence, RelatedFactory, SubFactory, SelfAttribute
from transmissions.channels import Channel
from django.conf import settings

from transmissions import models


class User(DjangoModelFactory):
    FACTORY_FOR = settings.AUTH_USER_MODEL

    username = Sequence(lambda n: 'factory_user_{}'.format(n))
    email = Sequence(lambda n: 'factory-user-{}@example.com'.format(n))
