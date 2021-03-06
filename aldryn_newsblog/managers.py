# -*- coding: utf-8 -*-

from __future__ import unicode_literals

try:
    from collections import Counter
except ImportError:
    from backport_collections import Counter

import datetime
from operator import attrgetter

from django.db import models
from django.utils.timezone import now

from aldryn_apphooks_config.managers.base import ManagerMixin, QuerySetMixin
from aldryn_people.models import Person
from parler.managers import TranslatableManager, TranslatableQuerySet

from .constants import (
    TRANSLATE_IS_PUBLISHED,
)

class ArticleQuerySet(QuerySetMixin, TranslatableQuerySet):
    def published(self):
        """
        Returns articles that are published AND have a publishing_date that
        has actually passed.
        """
        qs = self.filter(publishing_date__lte=now())
        if TRANSLATE_IS_PUBLISHED:
            return qs.translated(is_published_trans=True)
        return qs.filter(is_published=True)

    def published_one_of_trans(self):
        if TRANSLATE_IS_PUBLISHED:
            return self.filter(publishing_date__lte=now(), translations__is_published_trans=True)
        return self.published()


class AllManager(ManagerMixin, TranslatableManager):
    def get_queryset(self):
        qs = ArticleQuerySet(self.model, using=self.db)
        return qs#.select_related('featured_image')

    def published(self):
        return self.get_queryset().published()

    def published_one_of_trans(self):
        return self.get_queryset().published_one_of_trans()

    def get_months(self, request, namespace):
        """
        Get months and years with articles count for given request and namespace
        string. This means how many articles there are in each month.

        The request is required, because logged-in content managers may get
        different counts.

        Return list of dictionaries ordered by article publishing date of the
        following format:
        [
            {
                'date': date(YEAR, MONTH, ARBITRARY_DAY),
                'num_articles': NUM_ARTICLES
            },
            ...
        ]
        """

        # TODO: check if this limitation still exists in Django 1.6+
        # This is done in a naive way as Django is having tough time while
        # aggregating on date fields
        if (request and hasattr(request, 'toolbar') and
                request.toolbar and request.toolbar.edit_mode_active):
            articles = self.namespace(namespace)
        else:
            articles = self.published().namespace(namespace)
        dates = articles.values_list('publishing_date', flat=True)
        dates = [(x.year, x.month) for x in dates]
        date_counter = Counter(dates)
        dates = set(dates)
        dates = sorted(dates, reverse=True)
        months = [
            # Use day=3 to make sure timezone won't affect this hacks'
            # month value. There are UTC+14 and UTC-12 timezones!
            {'date': datetime.date(year=year, month=month, day=3),
             'num_articles': date_counter[(year, month)]}
            for year, month in dates]
        return months

    def get_authors(self, namespace):
        """
        Get authors with articles count for given namespace string.

        Return Person queryset annotated with and ordered by 'num_articles'.
        """

        # This methods relies on the fact that Article.app_config.namespace
        # is effectively unique for Article models
        return Person.objects.filter(
            article__app_config__namespace=namespace,
            article__is_published=True).annotate(
                num_articles=models.Count('article')).order_by('-num_articles')


class RelatedManager(AllManager):
    def get_queryset(self):
        qs = ArticleQuerySet(self.model, using=self.db)
        qs = qs.filter(app_config__show_in_listing=True)
        return qs#.select_related('featured_image')


class SearchManager(AllManager):
    def get_queryset(self):
        qs = ArticleQuerySet(self.model, using=self.db)
        qs = qs.filter(app_config__search_indexed=True)
        return qs#.select_related('featured_image')
