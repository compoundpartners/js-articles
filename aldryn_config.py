# -*- coding: utf-8 -*-
from aldryn_client import forms

class Form(forms.BaseForm):

    hide_related_articles = forms.CheckboxField(
        "Hide Related Articles Selector",
        required=False,
        initial=True)

    hide_tags = forms.CheckboxField(
        "Hide Tags",
        required=False,
        initial=True)

    def to_settings(self, data, settings_dict):

        if data['hide_related_articles']:
            settings_dict['HIDE_RELATED_ARTICLES'] = int(data['hide_related_articles'])

        if data['hide_tags']:
            settings_dict['HIDE_TAGS'] = int(data['hide_tags'])

        settings_dict['INSTALLED_APPS'].extend([
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

        return settings_dict
