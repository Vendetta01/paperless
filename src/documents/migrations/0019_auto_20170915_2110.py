# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2017-09-15 19:10
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0018_auto_20170715_1712'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='filenumber',
            field=models.IntegerField(db_index=True, default=1),
        ),
        migrations.AddField(
            model_name='document',
            name='foldernumber',
            field=models.IntegerField(db_index=True, default=1),
        ),
        migrations.AlterUniqueTogether(
            name='document',
            unique_together=set([('foldernumber', 'filenumber')]),
        ),
    ]