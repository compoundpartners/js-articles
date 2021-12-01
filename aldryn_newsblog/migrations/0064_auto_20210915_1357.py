# Generated by Django 2.2.24 on 2021-09-15 13:57

from django.db import migrations, models
import django.db.models.deletion
import filer.fields.file


class Migration(migrations.Migration):

    dependencies = [
        ('aldryn_newsblog', '0063_auto_20210716_0704'),
    ]

    operations = [
        migrations.AddField(
            model_name='newsblogconfig',
            name='show_in_related',
            field=models.BooleanField(default=True, help_text='Show articles in Related Articles plugin', verbose_name='Show in Related Articles'),
        ),
        migrations.AddField(
            model_name='newsblogconfig',
            name='show_in_specific',
            field=models.BooleanField(default=True, help_text='Show articles in Specific Articles plugin', verbose_name='Show in Specific Articles'),
        ),
        migrations.AlterField(
            model_name='article',
            name='svg_image',
            field=filer.fields.file.FilerFileField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='filer.File', verbose_name='logo SVG'),
        ),
    ]
