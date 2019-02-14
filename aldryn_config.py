# -*- coding: utf-8 -*-
from aldryn_client import forms

class Form(forms.BaseForm):

    hide_related_articles = forms.CheckboxField(
        "Hide Specific Articles Selector",
        required=False,
        initial=True)

    hide_tags = forms.CheckboxField(
        "Hide Tags",
        required=False,
        initial=True)

    hide_user = forms.CheckboxField(
        'Hide owner', required=False, initial=False
    )

    summary_richtext = forms.CheckboxField(
        "Use rich text for Summary",
        required=False,
        initial=False)

    def to_settings(self, data, settings):

        if data['hide_related_articles']:
            settings['HIDE_RELATED_ARTICLES'] = int(data['hide_related_articles'])

        if data['hide_tags']:
            settings['HIDE_TAGS'] = int(data['hide_tags'])

        if data['hide_user']:
            settings['HIDE_USER'] = int(data['hide_user'])

        if data['summary_richtext']:
            settings['SUMMARY_RICHTEXT'] = int(data['summary_richtext'])


        settings['INSTALLED_APPS'].extend([
            'aldryn_apphooks_config',
            'aldryn_boilerplates',
            'aldryn_categories',
            'aldryn_common',
            'aldryn_newsblog',
            'aldryn_people',
            'aldryn_translation_tools',
            'easy_thumbnails',
            'filer',
            'sortedm2m',
            'taggit',
            'treebeard'
        ])

        return settings
