# Generated by Django 3.0.4 on 2020-05-19 15:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('snapshotServer', '0007_auto_20200420_1534'),
    ]

    operations = [
        migrations.AddField(
            model_name='testcaseinsession',
            name='name',
            field=models.CharField(max_length=100, null=True),
        ),
    ]
