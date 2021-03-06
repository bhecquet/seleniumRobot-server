# Generated by Django 3.0.4 on 2021-02-25 06:53

import commonsServer.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('snapshotServer', '0008_testcaseinsession_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='snapshot',
            name='computingError',
            field=commonsServer.models.TruncatingCharField(default='', max_length=250),
        ),
        migrations.AlterField(
            model_name='snapshot',
            name='image',
            field=models.ImageField(upload_to='documents/%Y/%m/%d'),
        ),
        migrations.AlterField(
            model_name='snapshot',
            name='name',
            field=models.CharField(default='', max_length=150),
        ),
    ]
