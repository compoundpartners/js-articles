# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.utils.timezone import now
from django import forms
from aldryn_categories.models import Category
from js_services.models import Service
from js_locations.models import Location
import django_filters
from . import models

from .constants import (
    IS_THERE_COMPANIES,
    ADD_FILTERED_CATEGORIES,
)
if IS_THERE_COMPANIES:
    from js_companies.models import Company


class ArticleFilters(django_filters.FilterSet):
    q = django_filters.CharFilter('translations__title', 'icontains', label='Search the directory')
    medium = django_filters.ModelChoiceFilter('medium', label='medium', queryset=models.ArticleMedium.objects.all().order_by('position'))
    location = django_filters.ModelChoiceFilter('locations', label='location', queryset=Location.objects.all().order_by('translations__name'))
    category = django_filters.ModelChoiceFilter('categories', label='category', queryset=Category.objects.all().order_by('translations__name'))
    service = django_filters.ModelChoiceFilter('services', label='service', queryset=Service.objects.published().all().order_by('translations__title'))

    class Meta:
        model = models.Article
        fields = ['q', 'medium', 'location', 'category', 'service']

    def __init__(self, values, *args, **kwargs):
        super(ArticleFilters, self).__init__(values, *args, **kwargs)
        self.filters['medium'].extra.update({'empty_label': 'by medium'})
        self.filters['location'].extra.update({'empty_label': 'by location'})
        self.filters['category'].extra.update({'empty_label': 'by category'})
        self.filters['service'].extra.update({'empty_label': 'by service'})
        if IS_THERE_COMPANIES:
            self.filters['company'] = django_filters.ModelChoiceFilter('companies', label='company', queryset=Company.objects.all().order_by('name'))
            self.filters['company'].extra.update({'empty_label': 'by company'})
        if ADD_FILTERED_CATEGORIES:
            for category in ADD_FILTERED_CATEGORIES:
                qs = Category.objects.filter(translations__slug=category[0])[0].get_children().order_by('translations__name') if Category.objects.filter(translations__slug=category[0]).exists() else Category.objects.none()
                name = category[0].replace('-', '_')
                self.filters[name] = django_filters.ModelChoiceFilter('categories', label=category[1], queryset=qs)
                self.filters[name].extra.update({'empty_label': 'by %s' % category[1]})

