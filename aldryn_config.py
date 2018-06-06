# -*- coding: utf-8 -*-
from aldryn_client import forms

class Form(forms.BaseForm):

    show_related_articles = forms.CheckboxField(
        "Show Related Articles Selector",
        required=False,
        initial=True)

    def to_settings(self, data, settings_dict):

        if data['show_related_articles']:
            settings_dict['SHOW_RELATED_ARTICLES'] = int(data['show_related_articles'])

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
