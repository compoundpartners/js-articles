# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-04-01 09:14
from __future__ import unicode_literals

from django.db import migrations
import sortedm2m.fields


class Migration(migrations.Migration):

    dependencies = [
        #('js_companies', '0001_initial'),
        ('aldryn_newsblog', '0037_auto_20190220_0636'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='articlemedium',
            options={'ordering': ['position'], 'verbose_name': 'Medium', 'verbose_name_plural': 'Medium'},
        ),
        #migrations.AddField(
            #model_name='article',
            #name='companies',
            #field=sortedm2m.fields.SortedManyToManyField(blank=True, help_text=None, to='js_companies.Company', verbose_name='companies'),
        #),
    ]
