# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0001_initial'),
    ]

    if hasattr(settings, 'TRANSMISSION_USER_MODEL'):
        USER_MODEL = settings.TRANSMISSION_USER_MODEL
    else:
        USER_MODEL = settings.AUTH_USER_MODEL

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('uuid', django_extensions.db.fields.ShortUUIDField(unique=True, editable=False, blank=True)),
                ('trigger_name', models.CharField(max_length=50, db_index=True)),
                ('content_id', models.PositiveIntegerField(null=True, blank=True)),
                ('data_pickled', models.TextField(editable=False, blank=True)),
                ('datetime_created', models.DateTimeField(auto_now_add=True, null=True)),
                ('datetime_scheduled', models.DateTimeField()),
                ('datetime_processed', models.DateTimeField(null=True)),
                ('datetime_seen', models.DateTimeField(null=True)),
                ('datetime_consumed', models.DateTimeField(null=True)),
                ('status', models.IntegerField(default=-2, db_index=True)),
                ('content_type', models.ForeignKey(blank=True, to='contenttypes.ContentType', null=True)),
                ('target_user', models.ForeignKey(related_name='notifications', to=USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Trigger',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=50)),
                ('message', models.TextField()),
                ('channel', models.IntegerField(default=1, db_index=True)),
                ('behavior', models.IntegerField(default=10, db_index=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='notification',
            name='trigger',
            field=models.ForeignKey(blank=True, to='transmissions.Trigger', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='notification',
            name='trigger_user',
            field=models.ForeignKey(related_name='notifications_sent', default=None, to=USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AlterIndexTogether(
            name='notification',
            index_together=set([('datetime_processed', 'datetime_scheduled'), ('target_user', 'datetime_scheduled'), ('target_user', 'trigger', 'datetime_processed')]),
        ),
    ]
