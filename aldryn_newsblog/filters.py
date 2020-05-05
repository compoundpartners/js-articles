# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.utils.timezone import now
from django import forms
from django.core.cache import cache
from aldryn_categories.models import Category
from js_services.models import Service
from js_locations.models import Location
import django_filters
import datetime
from . import models, default_medium
from .cms_appconfig import NewsBlogConfig

class NoneMixin(object):
    pass

try:
    from custom.aldryn_newsblog.filters import CustomFilterMixin
except:
    CustomFilterMixin = NoneMixin

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


class ArticleFilters(CustomFilterMixin, django_filters.FilterSet):
    q = django_filters.CharFilter('translations__title', 'icontains', label='Search the directory')
    medium = django_filters.ModelChoiceFilter('medium', label='medium', queryset=models.ArticleMedium.objects.exclude(title=default_medium, **ADDITIONAL_EXCLUDE.get('medium', {})))
    location = django_filters.ModelChoiceFilter('locations', label='location', queryset=Location.objects.published().exclude(**ADDITIONAL_EXCLUDE.get('location', {})))
    category = django_filters.ModelChoiceFilter('categories', label='category', queryset=Category.objects.exclude(**ADDITIONAL_EXCLUDE.get('category', {})))
    service = django_filters.ModelChoiceFilter('services', label='service', queryset=Service.objects.published().exclude(**ADDITIONAL_EXCLUDE.get('service', {})))
    section = django_filters.ModelChoiceFilter('app_config', label='section', queryset=NewsBlogConfig.objects.filter(show_in_listing=True).exclude(namespace=NewsBlogConfig.default_namespace, **ADDITIONAL_EXCLUDE.get('section', {})))


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

        self.sort_choices(self.filters['section'])
        self.sort_choices(self.filters['service'])
        self.sort_choices(self.filters['category'])
        self.sort_choices(self.filters['location'])
        self.sort_choices(self.filters['medium'])

        if IS_THERE_COMPANIES:
            self.filters['company'] = django_filters.ModelChoiceFilter('companies', label='company', queryset=Company.objects.exclude(**ADDITIONAL_EXCLUDE.get('company', {})).order_by('name'))
            self.filters['company'].extra.update({'empty_label': 'by company'})
        if ADD_FILTERED_CATEGORIES:
            for category in ADD_FILTERED_CATEGORIES:
                qs = Category.objects.filter(translations__slug=category[0])[0].get_children().exclude(**ADDITIONAL_EXCLUDE.get(category[0], {})).order_by('translations__name') if Category.objects.filter(translations__slug=category[0]).exists() else Category.objects.none()
                name = category[0].replace('-', '_')
                self.filters[name] = django_filters.ModelChoiceFilter('categories', label=category[1], queryset=qs)
                self.filters[name].extra.update({'empty_label': 'by %s' % category[1]})

    def sort_choices(self, field):
        field = field.field
        if isinstance(field.choices, django_filters.fields.ModelChoiceIterator):
            choices = [(obj.pk, str(obj)) for obj in field.choices.queryset]
            field.iterator = django_filters.fields.ChoiceIterator
            field._set_choices(sorted(choices, key=lambda item: item[1]))


def hash_dict(obj):
    ret = ''
    for key, value in obj.items():
        ret +='-%s-%s' % (key, value)
    return ret

def get_services(namespace, **filters):
    key = 'services-for-artlces-by-namespace-%s' % namespace
    if filters:
        key += hash_dict(filters)
    output = cache.get(key)
    if not output:
        output = []
        for service in Service.objects.published().filter(**filters):
            count = models.Article.objects.published().namespace(namespace).filter(services=service).count()
            if count:
                output.append({
                    'item': service,
                    'count': count,
                    'url_name': '%s:article-list-by-service' % namespace,
                })

        output.sort(key=lambda k: k['count'])
        output.reverse()
        cache.set(key, output, 3600)
    return output

def get_authors(namespace, **filters):
    key = 'authors-for-artlces-by-namespace-%s' % namespace
    if filters:
        key += hash_dict(filters)
    output = cache.get(key)
    if not output:
        qs = models.Article.objects.published().namespace(namespace).filter(**filters)
        done = []
        output = []
        for item in qs.select_related('author'):
            if item.author and not item.author.id in done:
                done.append(item.author.id)

                out = {
                    'item': item.author,
                    'count': qs.filter(author=item.author).count(),
                    'url_name': '%s:article-list-by-author' % namespace,
                }

                output.append(out)
        output.sort(key=lambda k: k['count'])
        output.reverse()
        cache.set(key, output, 3600)
    return output


def get_archive(namespace, **filters):
    key = 'archive-for-artlces-by-namespace-%s' % namespace
    if filters:
        key += hash_dict(filters)
    output = cache.get(key)
    if not output:
        qs = models.Article.objects.published().namespace(namespace).filter(**filters)
        done = []
        output = []

        for item in qs.all().order_by('-publishing_date'):
            date = item.publishing_date
            uiq_date = '%d%d' % (date.month, date.year)

            if not uiq_date in done:
                done.append(uiq_date)

                out = {
                    'item': datetime.datetime.strftime(date, '%B %Y'),
                    'count': qs.filter(publishing_date__month=date.month, publishing_date__year=date.year).count(),
                    'url_name': '%s:article-list-by-month' % namespace,
                    'year': date.year,
                    'month': datetime.datetime.strftime(date, '%m'),
                }

                output.append(out)
        cache.set(key, output, 3600)
    return output
