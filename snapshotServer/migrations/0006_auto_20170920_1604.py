# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-09-20 14:04
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('variableServer', '0002_auto_20170920_1604'),
        ('commonsServer', '0001_initial'),
        ('snapshotServer', '0005_stepresult_duration'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='testcase',
            name='application',
        ),
        migrations.RemoveField(
            model_name='testenvironment',
            name='genericEnvironment',
        ),
        migrations.RemoveField(
            model_name='version',
            name='application',
        ),
        migrations.DeleteModel(
            name='Application',
        ),
        migrations.DeleteModel(
            name='TestCase',
        ),
        migrations.DeleteModel(
            name='TestEnvironment',
        ),
        migrations.DeleteModel(
            name='Version',
        ),
        migrations.CreateModel(
            name='Application',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
            },
            bases=('commonsServer.application',),
        ),
        migrations.CreateModel(
            name='TestCase',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
            },
            bases=('commonsServer.testcase',),
        ),
        migrations.CreateModel(
            name='TestEnvironment',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
            },
            bases=('commonsServer.testenvironment',),
        ),
        migrations.CreateModel(
            name='Version',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
            },
            bases=('commonsServer.version',),
        ),
    ]
