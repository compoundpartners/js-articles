# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-10-02 15:50
from __future__ import unicode_literals

from django.db import migrations
import sortedm2m.fields


class Migration(migrations.Migration):

    dependencies = [
        ('aldryn_newsblog', '0022_auto_20181001_0736'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='newsblogjsrelatedplugin',
            name='related_types',
        ),
        migrations.AddField(
            model_name='newsblogjsrelatedplugin',
            name='related_types',
            field=sortedm2m.fields.SortedManyToManyField(blank=True, help_text=None, to='aldryn_newsblog.NewsBlogConfig', verbose_name='related articles'),
        ),
    ]
