# Generated by Django 2.2.10 on 2020-03-20 09:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('snapshotServer', '0003_auto_20200319_1721'),
    ]

    operations = [
        migrations.AddField(
            model_name='testsession',
            name='name',
            field=models.CharField(default='', max_length=100),
        ),
        migrations.AddField(
            model_name='testsession',
            name='ttl',
            field=models.IntegerField(default=30),
        ),
    ]