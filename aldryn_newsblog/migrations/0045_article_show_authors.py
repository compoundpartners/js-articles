# -*- coding: utf-8 -*-
# Generated by Django 1.11.21 on 2019-06-11 16:10
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('aldryn_newsblog', '0044_auto_20190513_1205'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='show_authors',
            field=models.BooleanField(default=False, verbose_name='Show Authors'),
        ),
    ]
