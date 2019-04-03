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

    enable_locations = forms.CheckboxField(
        'Enable Locations', required=False, initial=False
    )

    summary_richtext = forms.CheckboxField(
        "Use rich text for Summary",
        required=False,
        initial=False)

    def to_settings(self, data, settings):

        if data['hide_related_articles']:
            settings['ARTICLES_HIDE_RELATED'] = int(data['hide_related_articles'])

        if data['hide_tags']:
            settings['ARTICLES_HIDE_TAGS'] = int(data['hide_tags'])

        if data['hide_user']:
            settings['ARTICLES_HIDE_USER'] = int(data['hide_user'])

        if data['enable_locations']:
            settings['ARTICLES_ENABLE_LOCATIONS'] = int(data['enable_locations'])

        if data['summary_richtext']:
            settings['ARTICLES_SUMMARY_RICHTEXT'] = int(data['summary_richtext'])


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
