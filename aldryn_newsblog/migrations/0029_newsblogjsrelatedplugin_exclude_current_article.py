# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-10-29 09:35
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('aldryn_newsblog', '0028_auto_20181015_0632'),
    ]

    operations = [
        migrations.AddField(
            model_name='newsblogjsrelatedplugin',
            name='exclude_current_article',
            field=models.BooleanField(default=False),
        ),
    ]