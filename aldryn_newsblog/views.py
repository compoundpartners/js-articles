# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import base64
import hashlib

from datetime import datetime, date
from dateutil.relativedelta import relativedelta

from django.contrib.sitemaps import Sitemap
from django.db.models import Q
from django.db.models.functions import Lower
from django.http import (
    Http404,
    HttpResponse,
    HttpResponseRedirect,
    HttpResponsePermanentRedirect,
)
from django.shortcuts import get_object_or_404
from django.utils import translation
from django.utils.cache import patch_cache_control
from django.utils.timezone import now
from django.views.generic import ListView
from django.views.generic.detail import DetailView, SingleObjectMixin

from easy_thumbnails.options import ThumbnailOptions
from easy_thumbnails.alias import aliases

from cms.cache.page import set_page_cache, get_page_cache
from cms.utils.compat import DJANGO_2_2, DJANGO_3_0
from menus.utils import set_language_changer
from parler.views import TranslatableSlugMixin, ViewUrlMixin

from aldryn_apphooks_config.mixins import AppConfigMixin
from aldryn_apphooks_config.utils import get_app_instance
from aldryn_categories.models import Category
from aldryn_people.models import Person
from js_services.models import Service

from aldryn_newsblog.utils.utilities import get_valid_languages_from_request
from .cms_appconfig import NewsBlogConfig
from .models import Article
from .utils import add_prefix_to_path
from .filters import ArticleFilters, RelatedArticlesFilters
from .constants import (
    IS_THERE_COMPANIES, 
    SHOW_CONTER_FILTERS, 
    GET_NEXT_ARTICLE,
    USE_CACHE,
)

class NoneMixin(object):
    pass

try:
    from custom.aldryn_newsblog.views import CustomListMixin
except:
    CustomListMixin = NoneMixin
try:
    from custom.aldryn_newsblog.views import CustomDetailMixin
except:
    CustomDetailMixin = NoneMixin


class CachedMixin():
    def use_cache(self, request):
        is_authenticated = request.user.is_authenticated
        model_name = str(self.model.__name__ if self.model else self.queryset.model.__name__)
        return request.method.lower() == 'get' and model_name in USE_CACHE and USE_CACHE[model_name] and (
            not hasattr(request, 'toolbar') or (
                not request.toolbar.edit_mode_active and not request.toolbar.show_toolbar and not is_authenticated
            )
        )

    def dispatch(self, request, *args, **kwargs):
        # Try to dispatch to the right method; if a method doesn't exist,
        # defer to the error handler. Also defer to the error handler if the
        # request method isn't on the approved list.
        response_timestamp = now()
        if self.use_cache(request):
            cache_content = get_page_cache(request)
            if cache_content is not None:
                content, headers, expires_datetime = cache_content
                response = HttpResponse(content)
                response.xframe_options_exempt = True
                if DJANGO_2_2 or DJANGO_3_0:
                    response._headers = headers
                else:
                    #  for django3.2 and above. response.headers replaces response._headers in earlier versions of django
                    response.headers = headers
                # Recalculate the max-age header for this cached response
                max_age = int(
                    (expires_datetime - response_timestamp).total_seconds() + 0.5)
                patch_cache_control(response, max_age=max_age)
                return response
        return super().dispatch(request, *args, **kwargs)

    def render_to_response(self, context, **response_kwargs):
        response = super().render_to_response(context, **response_kwargs)
        if self.use_cache(self.request):
            response.add_post_render_callback(set_page_cache)
        return response


class TemplatePrefixMixin(object):

    def prefix_template_names(self, template_names):
        if (hasattr(self.config, 'template_prefix') and
                self.config.template_prefix):
            prefix = self.config.template_prefix
            return [
                add_prefix_to_path(template, prefix)
                for template in template_names]
        return template_names

    def get_template_names(self):
        template_names = super(TemplatePrefixMixin, self).get_template_names()
        return self.prefix_template_names(template_names)


class EditModeMixin(object):
    """
    A mixin which sets the property 'edit_mode' with the truth value for
    whether a user is logged-into the CMS and is in edit-mode.
    """
    edit_mode = False

    def dispatch(self, request, *args, **kwargs):
        self.edit_mode = (
            self.request.toolbar and self.request.toolbar.edit_mode_active)
        return super(EditModeMixin, self).dispatch(request, *args, **kwargs)


class PreviewModeMixin(EditModeMixin):
    """
    If content editor is logged-in, show all articles. Otherwise, only the
    published articles should be returned.
    """
    def get_queryset(self):
        if self.namespace == NewsBlogConfig.default_namespace:
            qs = self.model.objects
        else:
            qs = self.model.all_objects.namespace(self.namespace)
        # check if user can see unpublished items. this will allow to switch
        # to edit mode instead of 404 on article detail page. CMS handles the
        # permissions.
        user = self.request.user
        user_can_edit = user.is_staff or user.is_superuser
        if not (self.edit_mode or user_can_edit):
            qs = qs.published()
        #language = translation.get_language()
        #qs = qs.active_translations(language)
        return qs


class AppHookCheckMixin(object):

    def dispatch(self, request, *args, **kwargs):
        self.valid_languages = get_valid_languages_from_request(
            self.namespace, request)
        return super(AppHookCheckMixin, self).dispatch(
            request, *args, **kwargs)

    def get_queryset(self):
        # filter available objects to contain only resolvable for current
        # language. IMPORTANT: after .translated - we cannot use .filter
        # on translated fields (parler/django limitation).
        # if your mixin contains filtering after super call - please place it
        # after this mixin.
        qs = super(AppHookCheckMixin, self).get_queryset()
        return qs#.translated(*self.valid_languages)


class ArticleDetail(CustomDetailMixin, CachedMixin, AppConfigMixin, AppHookCheckMixin, EditModeMixin,
                    TranslatableSlugMixin, TemplatePrefixMixin, DetailView):
    queryset = Article.all_objects
    slug_field = 'slug'
    year_url_kwarg = 'year'
    month_url_kwarg = 'month'
    day_url_kwarg = 'day'
    slug_url_kwarg = 'slug'
    pk_url_kwarg = 'pk'

    @property
    def template_name_suffix(self):
        return '_%s' %  (self.object.layout or 'detail')

    def get(self, request, *args, **kwargs):
        """
        This handles non-permalinked URLs according to preferences as set in
        NewsBlogConfig.
        """
        if not hasattr(self, 'object'):
            self.object = self.get_object()
        user = self.request.user
        user_can_edit = user.is_staff or user.is_superuser
        if not (self.edit_mode or user_can_edit):
            if not self.object.published_for_language(self.get_language()):
                raise Http404('Object not found.')
        set_language_changer(request, self.object.get_public_url)
        url = self.object.get_absolute_url()
        if (self.config.non_permalink_handling == 200 or request.path == url):
            # Continue as normal
            #return super(ArticleDetail, self).get(request, *args, **kwargs)
            context = self.get_context_data(object=self.object)
            return self.render_to_response(context)

        # Check to see if the URL path matches the correct absolute_url of
        # the found object
        if self.config.non_permalink_handling == 302:
            return HttpResponseRedirect(url)
        elif self.config.non_permalink_handling == 301:
            return HttpResponsePermanentRedirect(url)
        else:
            raise Http404('This is not the canonical uri of this object.')

    def post(self, request, *args, **kwargs):
        if self.config.allow_post:
            return super(ArticleDetail, self).get(request, *args, **kwargs)
        else:
            return super(ArticleDetail, self).http_method_not_allowed(request, *args, **kwargs)

    def get_object(self, queryset=None):
        """
        Supports ALL of the types of permalinks that we've defined in urls.py.
        However, it does require that either the id and the slug is available
        and unique.
        """
        if queryset is None:
            queryset = self.get_queryset()

        slug = self.kwargs.get(self.slug_url_kwarg, None)
        pk = self.kwargs.get(self.pk_url_kwarg, None)

        if pk is not None:
            # Let the DetailView itself handle this one
            return DetailView.get_object(self, queryset=queryset)
        elif slug is not None:
            # Let the TranslatedSlugMixin take over
            return super(ArticleDetail, self).get_object(queryset=queryset)

        raise AttributeError('ArticleDetail view must be called with either '
                             'an object pk or a slug')

    def get_context_data(self, **kwargs):
        context = super(ArticleDetail, self).get_context_data(**kwargs)
        if GET_NEXT_ARTICLE:
            context['prev_article'] = self.get_prev_object(
                self.queryset, self.object)
            context['next_article'] = self.get_next_object(
                self.queryset, self.object)

        if False:
            article = context['article']
            articles = Article.objects.published().exclude(id=article.id).distinct()
            categories = article.categories.all()
            context['related_articles'] = articles.filter(categories__in=categories)[:3]
            services = article.services.all()
            context['related_articles_by_services'] = articles.filter(services__in=services)[:3]
            if IS_THERE_COMPANIES and article.companies.count():
                context['related_articles_by_company'] = articles.filter(companies__in=article.companies.all())[:3]

            related_types_first = article.app_config
            if related_types_first is not None:
                context['related_types_first'] = related_types_first.namespace
            else:
                context['related_types_first'] = 'all'
            related_categories_first = article.categories.all().first()
            if related_categories_first is not None:
                context['related_categories_first'] = related_categories_first.slug
            else:
                context['related_categories_first'] = 'all'

        return context

    def get_prev_object(self, queryset=None, object=None):
        if queryset is None:
            queryset = self.get_queryset()
        if object is None:
            object = self.get_object(self)
        prev_objs = queryset.filter(
            publishing_date__lt=object.publishing_date
        ).order_by(
            '-publishing_date'
        )[:1]
        if prev_objs:
            return prev_objs[0]
        else:
            return None

    def get_next_object(self, queryset=None, object=None):
        if queryset is None:
            queryset = self.get_queryset()
        if object is None:
            object = self.get_object(self)
        next_objs = queryset.filter(
            publishing_date__gt=object.publishing_date
        ).order_by(
            'publishing_date'
        )[:1]
        if next_objs:
            return next_objs[0]
        else:
            return None


class ArticleListBase(CustomListMixin, AppConfigMixin, AppHookCheckMixin, TemplatePrefixMixin,
                      PreviewModeMixin, ViewUrlMixin, ListView):
    model = Article
    show_header = False
    strict = False

    def get(self, request, *args, **kwargs):
        if self.config.show_landing_page:
            from cms.page_rendering import render_page
            return render_page(request, request.current_page, translation.get_language(), None)
        self.edit_mode = (request.toolbar and request.toolbar.edit_mode_active)
        self.filterset = ArticleFilters(self.request.GET, queryset=self.get_queryset())
        if not self.filterset.is_bound or self.filterset.is_valid() or not self.get_strict():
            self.object_list = self.filterset.qs.distinct()
        else:
            self.object_list = self.filterset.queryset.none()
        context = self.get_context_data(filter=self.filterset,
                                        object_list=self.object_list)
        return self.render_to_response(context)

    def get_paginate_by(self, queryset):
        if self.paginate_by is not None:
            return self.paginate_by
        else:
            try:
                return self.config.paginate_by
            except AttributeError:
                return 10  # sensible failsafe

    def get_pagination_options(self):
        # Django does not handle negative numbers well
        # when using variables.
        # So we perform the conversion here.
        if self.config:
            options = {
                'pages_start': self.config.pagination_pages_start,
                'pages_visible': self.config.pagination_pages_visible,
            }
        else:
            options = {
                'pages_start': 10,
                'pages_visible': 4,
            }

        pages_visible_negative = -options['pages_visible']
        options['pages_visible_negative'] = pages_visible_negative
        options['pages_visible_total'] = options['pages_visible'] + 1
        options['pages_visible_total_negative'] = pages_visible_negative - 1
        return options

    def get_context_data(self, **kwargs):
        context = super(ArticleListBase, self).get_context_data(**kwargs)
        context['pagination'] = self.get_pagination_options()
        if SHOW_CONTER_FILTERS:
            from .filters import get_services, get_authors, get_archive
            context['filter_services'] = get_services(self.namespace)
            context['filter_authors'] = get_authors(self.namespace)
            context['filter_archive'] = get_archive(self.namespace)
        return context

    def get_strict(self):
        return self.strict


class ArticleList(ArticleListBase):
    """A complete list of articles."""
    show_header = True

    def get_queryset(self):
        qs = super(ArticleList, self).get_queryset()
        # exclude featured articles from queryset, to allow featured article
        # plugin on the list view page without duplicate entries in page qs.
        exclude_count = self.config.exclude_featured
        if exclude_count:
            featured_qs = Article.objects.all().filter(is_featured=True)
            if not self.edit_mode:
                featured_qs = featured_qs.published()
            exclude_featured = featured_qs[:exclude_count].values_list('pk')
            qs = qs.exclude(pk__in=exclude_featured)
        return qs


class ArticleSearchResultsList(ArticleListBase):
    model = Article
    http_method_names = ['get', 'post', ]
    partial_name = 'aldryn_newsblog/includes/search_results.html'
    template_name = 'aldryn_newsblog/article_list.html'

    def get(self, request, *args, **kwargs):
        self.query = request.GET.get('q')
        self.max_articles = request.GET.get('max_articles', 0)
        return super(ArticleSearchResultsList, self).get(request)

    def get_paginate_by(self, queryset):
        """
        If a max_articles was set (by a plugin), use that figure, else,
        paginate by the app_config's settings.
        """
        return self.max_articles or super(
            ArticleSearchResultsList, self).get_paginate_by(self.get_queryset())

    def get_queryset(self):
        qs = super(ArticleSearchResultsList, self).get_queryset()
        if self.query:
            return qs.filter(
                Q(translations__title__icontains=self.query) |
                Q(translations__lead_in__icontains=self.query) |
                Q(translations__search_data__icontains=self.query)
            ).distinct()
        else:
            return qs.none()

    def get_context_data(self, **kwargs):
        cxt = super(ArticleSearchResultsList, self).get_context_data(**kwargs)
        cxt['query'] = self.query
        return cxt

    def get_template_names(self):
        if self.request.is_ajax:
            template_names = [self.partial_name]
        else:
            template_names = [self.template_name]
        return self.prefix_template_names(template_names)


class AuthorArticleList(ArticleListBase):
    """A list of articles written by a specific author."""
    def get_queryset(self):
        # Note: each Article.author is Person instance with guaranteed
        # presence of unique slug field, which allows to use it in URLs
        qs =  super(AuthorArticleList, self).get_queryset()
        return qs.filter(
            Q(author=self.author) |
            Q(author_2=self.author) |
            Q(author_3=self.author)
        ).distinct()

    def get(self, request, author):
        language = translation.get_language_from_request(
            request, check_path=True)
        self.author = Person.objects.language(language).active_translations(
            language, slug=author).first()
        if not self.author:
            raise Http404('Author not found')
        return super(AuthorArticleList, self).get(request)

    def get_context_data(self, **kwargs):
        kwargs['newsblog_author'] = self.author
        return super(AuthorArticleList, self).get_context_data(**kwargs)


class CategoryArticleList(ArticleListBase):
    """A list of articles filtered by categories."""
    def get_queryset(self):
        return super(CategoryArticleList, self).get_queryset().filter(
            categories=self.category
        )

    def get(self, request, category):
        self.category = get_object_or_404(
            Category, translations__slug=category)
        return super(CategoryArticleList, self).get(request)

    def get_context_data(self, **kwargs):
        kwargs['newsblog_category'] = self.category
        ctx = super(CategoryArticleList, self).get_context_data(**kwargs)
        ctx['newsblog_category'] = self.category
        return ctx


class ServiceArticleList(ArticleListBase):
    """A list of articles filtered by services."""
    def get_queryset(self):
        return super(ServiceArticleList, self).get_queryset().filter(
            services=self.service
        )

    def get(self, request, service):
        self.service = get_object_or_404(
            Service, translations__slug=service)
        return super(ServiceArticleList, self).get(request)

    def get_context_data(self, **kwargs):
        kwargs['newsblog_service'] = self.service
        ctx = super(ServiceArticleList, self).get_context_data(**kwargs)
        ctx['newsblog_service'] = self.service
        return ctx


class DateRangeArticleList(ArticleListBase):
    """A list of articles for a specific date range"""
    def get_queryset(self):
        return super(DateRangeArticleList, self).get_queryset().filter(
            publishing_date__gte=self.date_from,
            publishing_date__lt=self.date_to
        )

    def _daterange_from_kwargs(self, kwargs):
        raise NotImplemented('Subclasses of DateRangeArticleList need to'
                             'implement `_daterange_from_kwargs`.')

    def get(self, request, **kwargs):
        self.date_from, self.date_to = self._daterange_from_kwargs(kwargs)
        return super(DateRangeArticleList, self).get(request)

    def get_context_data(self, **kwargs):
        kwargs['newsblog_day'] = (
            int(self.kwargs.get('day')) if 'day' in self.kwargs else None)
        kwargs['newsblog_month'] = (
            int(self.kwargs.get('month')) if 'month' in self.kwargs else None)
        kwargs['newsblog_year'] = (
            int(self.kwargs.get('year')) if 'year' in self.kwargs else None)
        if kwargs['newsblog_year']:
            kwargs['newsblog_archive_date'] = date(
                kwargs['newsblog_year'],
                kwargs['newsblog_month'] or 1,
                kwargs['newsblog_day'] or 1)
        return super(DateRangeArticleList, self).get_context_data(**kwargs)


class YearArticleList(DateRangeArticleList):
    def _daterange_from_kwargs(self, kwargs):
        date_from = datetime(int(kwargs['year']), 1, 1)
        date_to = date_from + relativedelta(years=1)
        return date_from, date_to


class MonthArticleList(DateRangeArticleList):
    def _daterange_from_kwargs(self, kwargs):
        date_from = datetime(int(kwargs['year']), int(kwargs['month']), 1)
        date_to = date_from + relativedelta(months=1)
        return date_from, date_to


class DayArticleList(DateRangeArticleList):
    def _daterange_from_kwargs(self, kwargs):
        date_from = datetime(
            int(kwargs['year']), int(kwargs['month']), int(kwargs['day']))
        date_to = date_from + relativedelta(days=1)
        return date_from, date_to


class RelatedArticles(ListView):
    model = Article
    template_name = 'aldryn_newsblog/article_list.html'
    paginate_by = 8
    type_url_kwarg = 'type'
    category_url_kwarg = 'category'
    pagination_pages_start = 5
    pagination_pages_visible = 2

    def get_pagination_options(self):
        options = dict()
        options['pages_start'] = self.pagination_pages_start
        options['pages_visible'] = self.pagination_pages_visible
        pages_visible_negative = -self.pagination_pages_visible
        options['pages_visible_negative'] = pages_visible_negative
        options['pages_visible_total'] = self.pagination_pages_visible + 1
        options['pages_visible_total_negative'] = pages_visible_negative - 1
        return options

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        type_url = self.kwargs.get(self.type_url_kwarg, 'all')
        category_url = self.kwargs.get(self.category_url_kwarg, 'all')

        # context['type_filter_list'] = NewsBlogConfig.objects.all().exclude(translations__app_title__icontains='DISABLED')
            # Allows adding 'DISABLED' anywhere in title of a Section to exclude it from the related articles listing filters
        context['type_filter_list'] = NewsBlogConfig.objects.all().exclude(enabled=False).order_by(Lower('namespace'))
        context['category_filter_list'] = Category.objects.all().exclude(translations__slug__iexact='hr-hub').order_by(Lower('translations__name'))
        context['split_path'] = self.request.path_info.split('/')[1:-1]  # Drop leading & trailing slash
        if type_url != 'all':
            context['type_filter_active'] = NewsBlogConfig.objects.all().filter(namespace__iexact=type_url)
        else:
            context['type_filter_active'] = ['all']
        if category_url != 'all':
            context['category_filter_active'] = Category.objects.all().filter(translations__slug__iexact=category_url)
        else:
            context['category_filter_active'] = ['all']

        context['pagination'] = self.get_pagination_options()

        # GAT01-170; reorder types manually  >  Move Quick Reads to top of filter list
        type_filter_list_custom_sort = list()
        for item in context['type_filter_list']:
            if item.namespace == 'quick-reads':
                type_filter_list_custom_sort.append(item)
        for item in context['type_filter_list']:
            if item.namespace != 'quick-reads':
                type_filter_list_custom_sort.append(item)
        context['type_filter_list'] = type_filter_list_custom_sort

        return context

    def get_queryset(self):
        type_url = self.kwargs.get(self.type_url_kwarg, 'all')
        category_url = self.kwargs.get(self.category_url_kwarg, 'all')

        qs = Article.objects.all().filter(is_published=True).filter(
            publishing_date__lte=datetime.now()).distinct()
        if type_url != 'all':
            qs_type = NewsBlogConfig.objects.all().filter(namespace__iexact=type_url)
            qs = qs.filter(app_config__in=qs_type)
        if category_url != 'all':
            qs_category = Category.objects.all().filter(translations__slug__iexact=category_url)
            qs = qs.filter(categories__in=qs_category.all())
        return qs


class ArticlesSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.7

    def items(self):
        return Article.objects.published()

    def lastmod(self, obj):
        return obj.publishing_date  # MOD date exists?  (e.g. when plugins are updated)


class ArticleRelatedView(TranslatableSlugMixin, ListView):
    model = Article
    strict = True

    def get(self, request, *args, **kwargs):
        import json
        data = request.GET
        if 'json' in request.GET:
            try:
                data = json.loads(request.GET['json'])
                if not 'mode' in data:
                    data['mode'] = 'json'
            except:
                pass
        self.filterset = RelatedArticlesFilters(data, queryset=self.get_queryset().published())
        if not self.filterset.is_bound or self.filterset.is_valid() or not self.get_strict():
            self.object_list = self.filterset.qs
        else:
            self.object_list = self.filterset.queryset.none()
        try:
            exclude_current = bool(self.filterset.form['count'].value())
            if self.object and exclude_current:
                self.object_list = self.exclude(pk=self.object.pk)
        except:
            pass

        try:
            exclude_current = int(self.filterset.form['exclude_current'].value())
            self.object_list = self.object_list.exclude(pk=exclude_current)
        except:
            pass

        try:
            count = int(self.filterset.form['count'].value())
            self.object_list = self.object_list.distinct()[:count]
        except:
            pass

        try:
            thumb_opts = self.filterset.form['image'].value() or {}
            width = thumb_opts.pop('width', 200)
            height = thumb_opts.pop('height', 150)
            subject_location = thumb_opts.pop('subject_location', False)
            thumb_opts['size'] = [width, height]
            thumb_opts = ThumbnailOptions(thumb_opts)

            parts = list(thumb_opts.items())
            parts.sort()
            parts = '.'.join('%s:%s' % (k,v) for k,v in parts)
            short_sha = hashlib.sha1(parts.encode('utf-8')).digest()
            thumb_opts_name = base64.urlsafe_b64encode(short_sha[:9]).decode('utf-8')


            if not aliases.get(thumb_opts_name):
                aliases.set(thumb_opts_name, thumb_opts)
        except:
            thumb_opts_name = None
            width = 200
            height = 150
            subject_location = False

        context = super().get_context_data(
            filter=self.filterset,
            object_list=self.object_list,
            thumb_opts=thumb_opts_name,
            image_size=f"{width}x{height}",
            image_subject_location=subject_location,
        )
        return self.render_to_response(context)

    def get_strict(self):
        return self.strict

    @property
    def template_name_suffix(self):
        mode = self.filterset.form['mode'].data
        return '_%s' %  ('related_%s' % mode if mode else 'related' )


