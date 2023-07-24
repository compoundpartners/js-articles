# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django import forms
from django.core.cache import cache
from django.utils.translation import ugettext_lazy as _
from django.utils.timezone import now
from aldryn_categories.models import Category
from aldryn_people.models import Person
from js_services.models import Service, ServicesConfig
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
    FILTER_EMPTY_LABELS,
    TRANSLATE_AUTHORS,
    TRANSLATE_IS_PUBLISHED,
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
    medium = django_filters.ModelChoiceFilter('medium', label='medium', empty_label='by medium', queryset=models.ArticleMedium.objects.exclude(title=default_medium).exclude(**ADDITIONAL_EXCLUDE.get('medium', {})))
    location = django_filters.ModelChoiceFilter('locations', label='location', empty_label='by location', queryset=Location.objects.published().exclude(**ADDITIONAL_EXCLUDE.get('location', {})))
    category = django_filters.ModelChoiceFilter('categories', label='category', empty_label='by category', queryset=Category.objects.exclude(**ADDITIONAL_EXCLUDE.get('category', {})))
    service = django_filters.ModelChoiceFilter('services', label='service', empty_label='by service', queryset=Service.objects.published().exclude(**ADDITIONAL_EXCLUDE.get('service', {})))
    section = django_filters.ModelChoiceFilter('app_config', label='section', empty_label='by section', queryset=NewsBlogConfig.objects.filter(show_in_listing=True).exclude(namespace=NewsBlogConfig.default_namespace).exclude(**ADDITIONAL_EXCLUDE.get('section', {})))


    class Meta:
        model = models.Article
        fields = ['q', 'medium', 'location', 'category', 'service', 'section']

    def __init__(self, values, *args, **kwargs):
        super(ArticleFilters, self).__init__(values, *args, **kwargs)
        if UPDATE_SEARCH_DATA_ON_SAVE:
            self.filters['q'] = SearchFilter(label='Search the directory')

        selects = ['medium', 'location', 'category', 'service', 'section']
        if IS_THERE_COMPANIES:
            self.filters['company'] = django_filters.ModelChoiceFilter('companies', label='company', empty_label='by company', queryset=Company.objects.exclude(**ADDITIONAL_EXCLUDE.get('company', {})).order_by('name'))
            selects.append('company')
        if ADD_FILTERED_CATEGORIES:
            for category in ADD_FILTERED_CATEGORIES:
                qs = Category.objects.filter(translations__slug=category[0])[0].get_children().exclude(**ADDITIONAL_EXCLUDE.get(category[0], {})).order_by('translations__name') if Category.objects.filter(translations__slug=category[0]).exists() else Category.objects.none()
                name = category[0].replace('-', '_')
                self.filters[name] = django_filters.ModelChoiceFilter('categories', label=category[1], queryset=qs)
                self.filters[name].extra.update({'empty_label': 'by %s' % category[1]})
                selects.append(name)

        self.set_empty_labels(**FILTER_EMPTY_LABELS)

        for field in selects:
            self.sort_choices(self.filters[field])

    def set_empty_labels(self, **kwargs):
        for key, value in kwargs.items():
            if key in self.filters:
                self.filters[key].extra['empty_label'] = value

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


class ModeFilter(django_filters.Filter):
    field_class = django_filters.fields.ChoiceField

    def filter(self, qs, values):
        return qs


class NoneFilter(django_filters.Filter):

    def filter(self, qs, values):
        return qs


class RelatedArticlesFilters(django_filters.FilterSet):
    mode = ModeFilter(label='mode', choices=[['json', 'json']])
    count = NoneFilter(label='count', required=True)
    is_featured = django_filters.BooleanFilter('is_featured', label='is featured')
    exclude_current = NoneFilter(label='exclude current article')
    mediums = django_filters.ModelMultipleChoiceFilter('medium', label='medium', queryset=models.ArticleMedium.objects.all())
    locations = django_filters.ModelMultipleChoiceFilter('locations', label='location', queryset=Location.objects.all())
    categories = django_filters.ModelMultipleChoiceFilter('categories', label='category', queryset=Category.objects.all())
    services = django_filters.ModelMultipleChoiceFilter('services', label='service', queryset=Service.objects.all())
    service_sections = django_filters.ModelMultipleChoiceFilter('services__sections', label='service section', queryset=ServicesConfig.objects.all())
    sections = django_filters.ModelMultipleChoiceFilter('app_config', label='section', queryset=NewsBlogConfig.objects.all())
    authors = django_filters.ModelMultipleChoiceFilter('author', label='author', queryset=Person.objects.all())
    image = NoneFilter(label='image')

    class Meta:
        model = models.Article
        fields = ['count', 'is_featured', 'exclude_current', 'mediums',
                  'locations', 'categories', 'services',
                  'service_sections', 'sections', 'authors', 'mode']

    def __init__(self, values, *args, **kwargs):
        super().__init__(values, *args, **kwargs)
        if TRANSLATE_AUTHORS:
            self.filters['authors'].field_name = 'author_trans'
