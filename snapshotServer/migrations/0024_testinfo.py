# Generated by Django 3.2.18 on 2024-02-08 10:04

import commonsServer.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('snapshotServer', '0023_auto_20240205_1548'),
    ]

    operations = [
        migrations.CreateModel(
            name='TestInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', commonsServer.models.TruncatingCharField(default='', max_length=100)),
                ('info', models.TextField(null=True)),
                ('testCase', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='testInfos', to='snapshotServer.testcaseinsession')),
            ],
        ),
    ]