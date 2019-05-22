# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-04-23 15:16
from __future__ import unicode_literals

from django.db import migrations
import sortedm2m.fields


def forwards(apps, schema_editor):
    Article = apps.get_model('aldryn_newsblog', 'Article')
    for a in Article.objects.all():
        if a.location:
            a.locations.add(a.location)

def backward(apps, schema_editor):
    Article = apps.get_model('aldryn_newsblog', 'Article')
    for a in Service.objects.all():
        if a.locations.all().count():
            a.location = a.locations.all()[0]
            a.save()

class Migration(migrations.Migration):

    dependencies = [
        ('js_locations', '0002_location_dx'),
        ('aldryn_newsblog', '0039_article_location'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='locations',
            field=sortedm2m.fields.SortedManyToManyField(blank=True, help_text=None, to='js_locations.Location', verbose_name='locations'),
        ),
        migrations.RunPython(forwards, backward),
        migrations.RemoveField(
            model_name='article',
            name='location',
        ),
    ]