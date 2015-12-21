# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transmissions', '0002_auto_20150105_1523'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='datetime_processed',
            field=models.DateTimeField(null=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='notification',
            name='datetime_scheduled',
            field=models.DateTimeField(db_index=True),
        ),
    ]
