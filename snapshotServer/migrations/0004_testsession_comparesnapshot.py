# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-08-02 11:28
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('snapshotServer', '0003_auto_20170801_1805'),
    ]

    operations = [
        migrations.AddField(
            model_name='testsession',
            name='compareSnapshot',
            field=models.BooleanField(default=False),
        ),
    ]