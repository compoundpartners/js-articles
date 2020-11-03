# Generated by Django 2.2.12 on 2020-11-03 11:40

from django.db import migrations
import sortedm2m.fields


class Migration(migrations.Migration):

    dependencies = [
        ('js_services', '0020_auto_20200814_0944'),
        ('aldryn_newsblog', '0059_newsblogconfig_custom_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='newsblogjsrelatedplugin',
            name='related_service_sections',
            field=sortedm2m.fields.SortedManyToManyField(blank=True, help_text=None, to='js_services.ServicesConfig', verbose_name='related service section'),
        ),
    ]
