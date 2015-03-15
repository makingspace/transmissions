# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('transmissions', '0001_initial'),
    ]

    operations = [
        migrations.AlterIndexTogether(
            name='notification',
            index_together=set([('datetime_processed', 'datetime_scheduled'), ('target_user', 'datetime_scheduled'), ('target_user', 'trigger_name', 'datetime_processed')]),
        ),
        migrations.RemoveField(
            model_name='notification',
            name='trigger',
        ),
        migrations.DeleteModel(
            name='Trigger',
        ),
    ]
