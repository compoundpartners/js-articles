# Generated by Django 2.2.28 on 2024-02-27 11:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('aldryn_newsblog', '0068_article_bottom_article_sidebar'),
    ]

    operations = [
        migrations.AddField(
            model_name='articletranslation',
            name='summary',
            field=models.TextField(blank=True, default='', verbose_name='Long summary'),
        ),
    ]
