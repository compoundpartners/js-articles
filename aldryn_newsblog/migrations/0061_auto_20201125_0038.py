# Generated by Django 2.2.10 on 2020-11-25 00:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0022_auto_20180620_1551'),
        ('aldryn_newsblog', '0060_newsblogjsrelatedplugin_related_service_sections'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='newsblogarticlesearchplugin',
            name='app_config',
        ),
        migrations.RemoveField(
            model_name='newsblogarticlesearchplugin',
            name='cmsplugin_ptr',
        ),
        migrations.RemoveField(
            model_name='newsblogauthorsplugin',
            name='app_config',
        ),
        migrations.RemoveField(
            model_name='newsblogauthorsplugin',
            name='cmsplugin_ptr',
        ),
        migrations.RemoveField(
            model_name='newsblogfeaturedarticlesplugin',
            name='app_config',
        ),
        migrations.RemoveField(
            model_name='newsblogfeaturedarticlesplugin',
            name='cmsplugin_ptr',
        ),
        migrations.RemoveField(
            model_name='newsbloglatestarticlesplugin',
            name='app_config',
        ),
        migrations.RemoveField(
            model_name='newsbloglatestarticlesplugin',
            name='cmsplugin_ptr',
        ),
        migrations.RemoveField(
            model_name='newsblogtagsplugin',
            name='app_config',
        ),
        migrations.RemoveField(
            model_name='newsblogtagsplugin',
            name='cmsplugin_ptr',
        ),
        migrations.RemoveField(
            model_name='article',
            name='tags',
        ),
        migrations.DeleteModel(
            name='NewsBlogArchivePlugin',
        ),
        migrations.DeleteModel(
            name='NewsBlogArticleSearchPlugin',
        ),
        migrations.DeleteModel(
            name='NewsBlogAuthorsPlugin',
        ),
        migrations.DeleteModel(
            name='NewsBlogFeaturedArticlesPlugin',
        ),
        migrations.DeleteModel(
            name='NewsBlogLatestArticlesPlugin',
        ),
        migrations.DeleteModel(
            name='NewsBlogTagsPlugin',
        ),
    ]