# -*- coding: utf-8 -*-
# Generated by Django 1.10.dev20160107235441 on 2016-06-06 04:14
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('fileuploads', '0013_result_video'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='result',
            name='video',
        ),
    ]
