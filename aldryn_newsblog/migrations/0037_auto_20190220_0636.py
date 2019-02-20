# -*- coding: utf-8 -*-
# Generated by Django 1.11.18 on 2019-02-20 06:36
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('aldryn_newsblog', '0036_auto_20190214_0556'),
    ]

    operations = [
        migrations.CreateModel(
            name='ArticleMedium',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('position', models.PositiveSmallIntegerField(default=0)),
            ],
            options={
                'verbose_name': 'Medium',
                'verbose_name_plural': 'Mediums',
                'ordering': ['position'],
            },
        ),
        migrations.AddField(
            model_name='article',
            name='medium',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='aldryn_newsblog.ArticleMedium', verbose_name='medium'),
        ),
    ]
