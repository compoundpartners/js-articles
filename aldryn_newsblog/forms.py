# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from sortedm2m_filter_horizontal_widget.forms import SortedFilteredSelectMultiple, SortedMultipleChoiceField
from parler.forms import TranslatableModelForm

from aldryn_people.models import Person

from . import models
from .constants import (
    IS_THERE_COMPANIES,
    SPECIFIC_ARTICLES_LAYOUTS,
    RELATED_ARTICLES_LAYOUTS,
    ARTICLE_LAYOUT_CHOICES,
    ARTICLE_CUSTOM_FIELDS,
    ARTICLE_SECTION_CUSTOM_FIELDS,
    SUMMARY_RICHTEXT,
)
if IS_THERE_COMPANIES:
    from js_companies.models import Company

try:
    from js_custom_fields.forms import CustomFieldsFormMixin, CustomFieldsSettingsFormMixin
except:
    class CustomFieldsFormMixin(object):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            if 'custom_fields' in self.fields:
                self.fields['custom_fields'].widget = forms.HiddenInput()

    class CustomFieldsSettingsFormMixin(object):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            if 'custom_fields_settings' in self.fields:
                self.fields['custom_fields_settings'].widget = forms.HiddenInput()


class ArticleAdminForm(CustomFieldsFormMixin, TranslatableModelForm):
    companies = forms.CharField()
    layout = forms.ChoiceField(choices=ARTICLE_LAYOUT_CHOICES, required=False)

    custom_fields = 'get_custom_fields'

    class Meta:
        model = models.Article
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        #if 'initial' in kwargs:
            #kwargs['initial']['medium'] = models.ArticleMedium.objects.first().pk if models.ArticleMedium.objects.first() else None
        super().__init__(*args, **kwargs)

        qs = models.Article.objects
        if self.instance.app_config_id:
            qs = models.Article.objects.filter(
                app_config=self.instance.app_config)
        elif 'initial' in kwargs and 'app_config' in kwargs['initial']:
            qs = models.Article.objects.filter(
                app_config=kwargs['initial']['app_config'])

        author_fileds = ['author', 'author_trans', 'author_2', 'author_2_trans', 'author_3', 'author_3_trans', ]
        for field in author_fileds:
            if field in self.fields:
                self.fields[field].queryset = Person.objects.all().order_by('last_name')

        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if 'related' in self.fields:
            self.fields['related'].queryset = qs

        # Don't allow app_configs to be added here. The correct way to add an
        # apphook-config is to create an apphook on a cms Page.
        self.fields['app_config'].widget.can_add_related = False
        # Don't allow related articles to be added here.
        # doesn't makes much sense to add articles from another article other
        # than save and add another.
        if ('related' in self.fields and
                hasattr(self.fields['related'], 'widget')):
            self.fields['related'].widget.can_add_related = False
        if not SUMMARY_RICHTEXT:
            self.fields['lead_in'].widget = forms.widgets.Textarea()
        if IS_THERE_COMPANIES:
            self.fields['companies'] = forms.ModelMultipleChoiceField(queryset=Company.objects.all(), required=False)# self.instance.companies
            self.fields['companies'].widget = SortedFilteredSelectMultiple()
            self.fields['companies'].queryset = Company.objects.all()
            if self.instance.pk and self.instance.companies.count():
                self.fields['companies'].initial = self.instance.companies.all()
        else:
            del self.fields['companies']

    def get_custom_fields(self):
        fields = ARTICLE_CUSTOM_FIELDS
        if self.instance and hasattr(self.instance, 'app_config') and self.instance.app_config.custom_fields_settings:
            fields.update(self.instance.app_config.custom_fields_settings)
        return fields


class NewsBlogConfigAdminForm(CustomFieldsFormMixin, CustomFieldsSettingsFormMixin, TranslatableModelForm):
    custom_fields = ARTICLE_SECTION_CUSTOM_FIELDS


class NewsBlogFeedAdminForm(TranslatableModelForm):
    articles = forms.ModelMultipleChoiceField(queryset=models.Article.objects.all(), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['articles'].widget = SortedFilteredSelectMultiple()
        self.fields['articles'].queryset = models.Article.objects.all()
        if self.instance.pk and self.instance.article_set.count():
            self.fields['articles'].initial = self.instance.article_set.all()


class AutoAppConfigFormMixin(object):
    """
    If there is only a single AppConfig to choose, automatically select it.
    """
    def __init__(self, *args, **kwargs):
        super(AutoAppConfigFormMixin, self).__init__(*args, **kwargs)
        if 'app_config' in self.fields:
            # if has only one choice, select it by default
            if self.fields['app_config'].queryset.count() == 1:
                self.fields['app_config'].empty_label = None


class NewsBlogCategoriesPluginForm(AutoAppConfigFormMixin, forms.ModelForm):
    class Meta:
        model = models.NewsBlogCategoriesPlugin
        fields = ['app_config']


class NewsBlogRelatedPluginForm(forms.ModelForm):
    layout = forms.ChoiceField(choices=SPECIFIC_ARTICLES_LAYOUTS)
    related_articles = SortedMultipleChoiceField(
        label='ralated articles',
        queryset=models.Article.objects.all(),
        required=False,
        widget=SortedFilteredSelectMultiple(attrs={'verbose_name':'article', 'verbose_name_plural':'articles'})
    )

    class Meta:
        fields = '__all__'


class NewsBlogJSRelatedPluginForm(forms.ModelForm):

    layout = forms.ChoiceField(choices=RELATED_ARTICLES_LAYOUTS)

    featured = forms.BooleanField(label='Show "Is Featured"', required=False)

    exclude_current_article = forms.BooleanField(label='Exclude current article', required=False)

    from aldryn_newsblog.models import NewsBlogConfig
    related_types = forms.ModelMultipleChoiceField(
        label='Related sections',
        queryset=NewsBlogConfig.objects.exclude(namespace=NewsBlogConfig.default_namespace),
        required=False,
        widget=FilteredSelectMultiple("Related sections", is_stacked=False))

    related_mediums = forms.ModelMultipleChoiceField(queryset=models.ArticleMedium.objects.all(), required=False, widget=FilteredSelectMultiple("Medium", is_stacked=False))

    from aldryn_people.models import Person
    related_authors = forms.ModelMultipleChoiceField(queryset=Person.objects.all(), required=False, widget=FilteredSelectMultiple("Related authors", is_stacked=False))

    from aldryn_categories.models import Category
    related_categories = forms.ModelMultipleChoiceField(queryset=Category.objects.all(), required=False, widget=FilteredSelectMultiple("Related categories", is_stacked=False))

    from js_services.models import Service, ServicesConfig
    related_services = forms.ModelMultipleChoiceField(
        queryset=Service.objects.all(),
        required=False,
        widget=FilteredSelectMultiple('Related services', False)
    )
    related_service_sections = forms.ModelMultipleChoiceField(
        queryset=ServicesConfig.objects.all(),
        required=False,
        widget=FilteredSelectMultiple('Related service sections', False)
    )

    related_companies = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(NewsBlogJSRelatedPluginForm, self).__init__(*args, **kwargs)
        if IS_THERE_COMPANIES:
            self.fields['related_companies'] = forms.ModelMultipleChoiceField(queryset=Company.objects.all(), required=False)
            self.fields['related_companies'].widget = FilteredSelectMultiple("Related companies", is_stacked=False)
            self.fields['related_companies'].queryset = Company.objects.all()
            if self.instance.pk and self.instance.related_companies.count():
                self.fields['related_companies'].initial = self.instance.related_companies.all()
