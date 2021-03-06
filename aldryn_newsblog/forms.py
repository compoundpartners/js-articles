# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from sortedm2m_filter_horizontal_widget.forms import SortedFilteredSelectMultiple, SortedMultipleChoiceField

from . import models
from .constants import (
    IS_THERE_COMPANIES,
    SPECIFIC_ARTICLES_LAYOUTS,
    RELATED_ARTICLES_LAYOUTS,
)
if IS_THERE_COMPANIES:
    from js_companies.models import Company


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
