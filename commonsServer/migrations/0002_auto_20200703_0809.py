# Generated by Django 3.0.4 on 2020-07-03 06:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('commonsServer', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='testcase',
            name='name',
            field=models.CharField(max_length=150),
        ),
    ]
