# -*- coding: utf-8 -*-
# Generated by Django 1.10.dev20160107235441 on 2016-12-03 06:40
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('groups', '0003_auto_20161003_1844'),
    ]

    operations = [
        migrations.CreateModel(
            name='Process',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('group_name', models.CharField(max_length=400)),
                ('group_id', models.IntegerField(default=0)),
                ('policy_name', models.CharField(max_length=100)),
                ('policy_id', models.IntegerField(default=0)),
                ('processed_time', models.DateTimeField()),
                ('user_name', models.CharField(default=None, max_length=400, null=True)),
                ('shared', models.BooleanField(default=True)),
                ('status', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Result',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('filename', models.CharField(max_length=400)),
                ('task_id', models.CharField(max_length=200)),
                ('status', models.BooleanField(default=False)),
                ('process', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='groups.Process')),
            ],
        ),
        migrations.CreateModel(
            name='Row',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('signal_name', models.CharField(max_length=200)),
                ('op_name', models.CharField(max_length=200)),
                ('cut_off_number', models.FloatField(default=0)),
                ('display_order', models.IntegerField(default=0)),
                ('result_number', models.FloatField(default=0)),
                ('frame_number', models.FloatField(default=0)),
                ('result', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='groups.Result')),
            ],
        ),
    ]
