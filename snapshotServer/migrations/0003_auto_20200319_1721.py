# Generated by Django 2.2.10 on 2020-03-19 16:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('snapshotServer', '0002_auto_20200309_1545'),
    ]

    operations = [
        migrations.AddField(
            model_name='snapshot',
            name='compareOption',
            field=models.CharField(default='true', max_length=100),
        ),
        migrations.AddField(
            model_name='snapshot',
            name='name',
            field=models.CharField(default='', max_length=100),
        ),
    ]
