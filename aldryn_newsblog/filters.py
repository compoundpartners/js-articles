# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.utils.timezone import now
from django import forms
from aldryn_categories.models import Category
from js_services.models import Service
from js_locations.models import Location
import django_filters
from . import models
from .cms_appconfig import NewsBlogConfig

from .constants import (
    UPDATE_SEARCH_DATA_ON_SAVE,
    IS_THERE_COMPANIES,
    ADD_FILTERED_CATEGORIES,
    ADDITIONAL_EXCLUDE,
)
if IS_THERE_COMPANIES:
    from js_companies.models import Company


class SearchFilter(django_filters.Filter):
    def filter(self, qs, values):
        values = values or ''
        if len(values) > 0:
            for value in values.strip().split():
                value = value.strip()
                if value:
                    qs = qs.filter(translations__search_data__icontains=value)
        return qs


class ArticleFilters(django_filters.FilterSet):
    q = django_filters.CharFilter('translations__title', 'icontains', label='Search the directory')
    medium = django_filters.ModelChoiceFilter('medium', label='medium', queryset=models.ArticleMedium.objects.exclude(**ADDITIONAL_EXCLUDE.get('medium', {})).order_by('position'))
    location = django_filters.ModelChoiceFilter('locations', label='location', queryset=Location.objects.exclude(**ADDITIONAL_EXCLUDE.get('location', {})).order_by('translations__name'))
    category = django_filters.ModelChoiceFilter('categories', label='category', queryset=Category.objects.exclude(**ADDITIONAL_EXCLUDE.get('category', {})).order_by('translations__name'))
    service = django_filters.ModelChoiceFilter('services', label='service', queryset=Service.objects.published().exclude(**ADDITIONAL_EXCLUDE.get('service', {})).order_by('translations__title'))
    section = django_filters.ModelChoiceFilter('app_config', label='section', queryset=NewsBlogConfig.objects.exclude(**ADDITIONAL_EXCLUDE.get('section', {})).order_by('translations__app_title'))

    class Meta:
        model = models.Article
        fields = ['q', 'medium', 'location', 'category', 'service', 'section']

    def __init__(self, values, *args, **kwargs):
        super(ArticleFilters, self).__init__(values, *args, **kwargs)
        self.filters['medium'].extra.update({'empty_label': 'by medium'})
        self.filters['location'].extra.update({'empty_label': 'by location'})
        self.filters['category'].extra.update({'empty_label': 'by category'})
        self.filters['service'].extra.update({'empty_label': 'by service'})
        self.filters['section'].extra.update({'empty_label': 'by section'})

        if UPDATE_SEARCH_DATA_ON_SAVE:
            self.filters['q'] = SearchFilter(label='Search the directory')

        if IS_THERE_COMPANIES:
            self.filters['company'] = django_filters.ModelChoiceFilter('companies', label='company', queryset=Company.objects.exclude(**ADDITIONAL_EXCLUDE.get('company', {})).order_by('name'))
            self.filters['company'].extra.update({'empty_label': 'by company'})
        if ADD_FILTERED_CATEGORIES:
            for category in ADD_FILTERED_CATEGORIES:
                qs = Category.objects.filter(translations__slug=category[0])[0].get_children().exclude(**ADDITIONAL_EXCLUDE.get(category[0], {})).order_by('translations__name') if Category.objects.filter(translations__slug=category[0]).exists() else Category.objects.none()
                name = category[0].replace('-', '_')
                self.filters[name] = django_filters.ModelChoiceFilter('categories', label=category[1], queryset=qs)
                self.filters[name].extra.update({'empty_label': 'by %s' % category[1]})

