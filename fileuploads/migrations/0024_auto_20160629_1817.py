# -*- coding: utf-8 -*-
# Generated by Django 1.10.dev20160107235441 on 2016-06-29 18:17
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('fileuploads', '0023_member_file_id'),
    ]

    operations = [
        migrations.RenameField(
            model_name='member',
            old_name='filename',
            new_name='file_name',
        ),
    ]
