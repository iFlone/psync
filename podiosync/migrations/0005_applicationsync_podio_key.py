# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-04-27 07:24
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('podiosync', '0004_applicationsync_last_synced'),
    ]

    operations = [
        migrations.AddField(
            model_name='applicationsync',
            name='podio_key',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='podiosync.PodioKey'),
            preserve_default=False,
        ),
    ]
