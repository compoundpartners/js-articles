# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-10-11 15:33
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('aldryn_newsblog', '0026_newsblogjsrelatedplugin_number_of_articles'),
    ]

    operations = [
        migrations.AddField(
            model_name='newsblogjsrelatedplugin',
            name='featured',
            field=models.BooleanField(default=False),
        ),
    ]