# Generated by Django 3.2.18 on 2023-10-16 13:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('snapshotServer', '0018_testcaseinsession_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='testsession',
            name='compareSnapshotBehaviour',
            field=models.CharField(default='DISPLAY_ONLY', max_length=20),
        ),
    ]
