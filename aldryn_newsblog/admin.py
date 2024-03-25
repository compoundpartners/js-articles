# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from aldryn_apphooks_config.admin import BaseAppHookConfig, ModelAppHookConfig
from aldryn_translation_tools.admin import AllTranslationsMixin
from cms.admin.placeholderadmin import FrontendEditableAdminMixin
from cms.admin.placeholderadmin import PlaceholderAdminMixin
from cms.utils.i18n import get_current_language, get_language_list
from cms.utils import copy_plugins, get_current_site

from django.db import transaction
from django.db.models.query import EmptyQuerySet
from django.conf.urls import url
from django.contrib import admin
from django.contrib.admin.templatetags.admin_list import _boolean_icon
from django.contrib.sites.models import Site
from django.views.decorators.http import require_POST
from django.utils.translation import ugettext_lazy as _
from django.utils.decorators import method_decorator
from django.utils.encoding import force_text
from django.core.exceptions import PermissionDenied
from django.http import (
    HttpResponseRedirect,
    HttpResponse,
    Http404,
    HttpResponseBadRequest,
    HttpResponseForbidden,
)
from parler.admin import TranslatableAdmin
from sortedm2m_filter_horizontal_widget.forms import SortedFilteredSelectMultiple


from . import models, forms, default_medium

from .constants import (
    HIDE_RELATED_ARTICLES,
    HIDE_USER,
    ENABLE_LOCATIONS,
    ENABLE_READTIME,
    ENABLE_SUMMARY,
    IS_THERE_COMPANIES,
    SHOW_LOGO,
    SHOW_RELATED_IMAGE,
    TRANSLATE_IS_PUBLISHED,
    TRANSLATE_AUTHORS,
    ENABLE_FEEDS,
    ADMIN_LIST_FILTERS,
)
if IS_THERE_COMPANIES:
    from js_companies.models import Company

try:
    from custom.aldryn_newsblog.admin import CusomArticleAdminMixin
except ImportError:
    class CusomArticleAdminMixin(object):
        pass


require_POST = method_decorator(require_POST)


def make_published(modeladmin, request, queryset):
    if TRANSLATE_IS_PUBLISHED:
        for i in queryset.all():
            i.is_published_trans = True
            i.save()
        #language = get_current_language()
        #models.ArticleTranslation.objects.filter(language_code=language, master__in=queryset).update(is_published_trans=True)
    else:
        queryset.update(is_published=True)


make_published.short_description = _(
    "Mark selected articles as published")


def make_unpublished(modeladmin, request, queryset):
    if TRANSLATE_IS_PUBLISHED:
        for i in queryset.all():
            i.is_published_trans = False
            i.save()
        #language = get_current_language()
        #models.ArticleTranslation.objects.filter(language_code=language, master__in=queryset).update(is_published_trans=False)
    else:
        queryset.update(is_published=False)


make_unpublished.short_description = _(
    "Mark selected articles as not published")


def make_featured(modeladmin, request, queryset):
    if TRANSLATE_IS_PUBLISHED:
        for i in queryset.all():
            i.is_featured_trans = True
            i.save()
        #language = get_current_language()
        #models.ArticleTranslation.objects.filter(language_code=language, master__in=queryset).update(is_featured_trans=True)
    else:
        queryset.update(is_featured=True)


make_featured.short_description = _(
    "Mark selected articles as featured")


def make_not_featured(modeladmin, request, queryset):
    if TRANSLATE_IS_PUBLISHED:
        for i in queryset.all():
            i.is_featured_trans = False
            i.save()
        #language = get_current_language()
        #models.ArticleTranslation.objects.filter(language_code=language, master__in=queryset).update(is_featured_trans=False)
    else:
        queryset.update(is_featured=False)


make_not_featured.short_description = _(
    "Mark selected articles as not featured")


class ArticleAdmin(
    CusomArticleAdminMixin,
    PlaceholderAdminMixin,
    FrontendEditableAdminMixin,
    ModelAppHookConfig,
    TranslatableAdmin
):
    def get_queryset(self, request):
        return self.model.all_objects.distinct()

    form = forms.ArticleAdminForm
    list_display = ('title_view', 'app_config', 'is__published',
                    'is__featured', 'publishing_date')
    search_fields = ['translations__title', 'translations__slug', 'translations__lead_in']

    list_filter = []

    actions = (
        make_featured, make_not_featured,
        make_published, make_unpublished,
    )

    def title_view(self, obj):
         return obj.title
    title_view.short_description  = 'title'
    title_view.admin_order_field = 'translations__title'

    advanced_settings_fields = (
        'categories',
        'services',
    )
    if IS_THERE_COMPANIES:
        advanced_settings_fields += (
            'companies',
        )

    if HIDE_RELATED_ARTICLES == 0:
        advanced_settings_fields += (
            'related',
        )

    if HIDE_USER == 0:
        advanced_settings_fields += (
            'owner',
        )

    if ENABLE_FEEDS:
        advanced_settings_fields += (
            'feeds',
        )

    advanced_settings_fields += (
        'app_config',
    )

    main_fields = [
        'title',
        'author',
        'author_2',
        'author_3',
        'hide_authors',
        'publishing_date',
        'is_published',
        'is_featured',
        'featured_image',
        'related_image' if SHOW_RELATED_IMAGE else (),
        'lead_in',
    ]
    if ENABLE_SUMMARY:
        main_fields += [
            'summary',
        ]
    if ENABLE_READTIME:
        main_fields += [
            'read_time',
        ]
    main_fields += [
        'medium',
        'layout',
        'custom_fields',
    ]
    if ENABLE_LOCATIONS:
        main_fields += [
            'locations',
        ]


    fieldsets = (
        (None, {
            'fields': main_fields,
        }),
        (_('Meta Options'), {
            'classes': ('collapse',),
            'fields': (
                'slug',
                'meta_title',
                'meta_description',
                'meta_keywords',
                'share_image',
                'show_on_sitemap',
                'show_on_xml_sitemap',
                'noindex',
                'nofollow',
                'canonical_url',
            )
        }),
        (_('Advanced Settings'), {
            'classes': ('collapse',),
            'fields': advanced_settings_fields
        }),
    )



    filter_horizontal = [
        'categories',
    ]


    app_config_selection_title = ''
    app_config_selection_desc = ''

    def get_list_filter(self, request):
        filters = []
        for f in ADMIN_LIST_FILTERS + self.list_filter:
            if f == 'is_published' and TRANSLATE_IS_PUBLISHED:
                filters.append('translations__is_published_trans')
            else:
                filters.append(f)
        return filters

    # def get_list_display(self, request):
        # fields = []
        # list_display = super(ArticleAdmin, self).get_list_display(request)
        # for field in list_display:
            # if field  in ['is_published', 'is_featured'] and TRANSLATE_IS_PUBLISHED:
                # field += '_trans'
            # fields.append(field)
        # return fields
    def is__published(self, obj):
        if TRANSLATE_IS_PUBLISHED:
          return _boolean_icon(obj.is_published_trans)
        return _boolean_icon(obj.is_published)

    def is__featured(self, obj):
        if TRANSLATE_IS_PUBLISHED:
          return _boolean_icon(obj.is_featured_trans)
        return _boolean_icon(obj.is_featured)

    def get_fieldsets(self, request, obj=None):
        fieldsets = super(ArticleAdmin, self).get_fieldsets(request, obj)
        if SHOW_LOGO and obj and obj.app_config.show_logo:
            index = fieldsets[0][1]['fields'].index('featured_image')
            if 'svg_image' not in fieldsets[0][1]['fields']:
                fieldsets[0][1]['fields'].insert(
                    index + 1,
                    'svg_image',
                )
            if 'logo_image' not in fieldsets[0][1]['fields']:
                fieldsets[0][1]['fields'].insert(
                    index + 2,
                    'logo_image',
                )
        for fieldset in fieldsets:
            if len(fieldset) == 2 and 'fields' in fieldset[1]:
                fields = []
                for field in fieldset[1]['fields']:
                    if ((field  in ['is_published', 'is_featured'] and TRANSLATE_IS_PUBLISHED) or
                            (field  in ['author', 'author_2', 'author_3'] and TRANSLATE_AUTHORS)):
                        field += '_trans'
                    fields.append(field)
                fieldset[1]['fields'] = fields
        return fieldsets

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        if db_field.name in ['services', 'companies', 'locations', 'feeds']:
            kwargs['widget'] = SortedFilteredSelectMultiple()
        return super(ArticleAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name == 'app_config':
            kwargs["queryset"] = models.NewsBlogConfig.objects.exclude(namespace=models.NewsBlogConfig.default_namespace)
        if db_field.name == 'medium':
            default_medium_obj, created = models.ArticleMedium.objects.get_or_create(title=default_medium)
            kwargs["queryset"] = models.ArticleMedium.objects.exclude(pk=default_medium_obj.pk)
        return super(ArticleAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if IS_THERE_COMPANIES:
            obj.companies.set(Company.objects.filter(pk__in=form.cleaned_data.get('companies')))

    def get_site(self, request):
        site_id = request.session.get('cms_admin_site')

        if not site_id:
            return get_current_site()

        try:
            site = Site.objects._get_site_by_id(site_id)
        except Site.DoesNotExist:
            site = get_current_site()
        return site

    @require_POST
    @transaction.atomic
    def copy_language(self, request, article_id):
        article = self.get_object(request, object_id=article_id)
        source_language = request.POST.get('source_language')
        target_language = request.POST.get('target_language')

        if not self.has_change_permission(request, obj=article):
            raise PermissionDenied

        if article is None:
            raise Http404

        if not target_language or not target_language in get_language_list(site_id=self.get_site(request).pk):
            return HttpResponseBadRequest(force_text(_("Language must be set to a supported language!")))

        for placeholder in article.get_placeholders():
            plugins = list(
                placeholder.get_plugins(language=source_language).order_by('path'))
            if not placeholder.has_add_plugins_permission(request.user, plugins):
                return HttpResponseForbidden(force_text(_('You do not have permission to copy these plugins.')))
            copy_plugins.copy_plugins_to(plugins, placeholder, target_language)
        return HttpResponse("ok")

    def get_urls(self):
        urlpatterns = super().get_urls()
        opts = self.model._meta
        info = opts.app_label, opts.model_name
        return [url(
            r'^(.+)/copy_language/$',
            self.admin_site.admin_view(self.copy_language),
            name='{0}_{1}_copy_language'.format(*info)
        )] + urlpatterns


admin.site.register(models.Article, ArticleAdmin)


class NewsBlogConfigAdmin(
    PlaceholderAdminMixin,
    #BaseAppHookConfig,
    TranslatableAdmin
):
    form = forms.NewsBlogConfigAdminForm
    readonly_fields = ("type",)

    def get_fieldsets(self, request, obj):
        return [
            (None, {"fields": ("type", "namespace")}),
            ("Config", {"fields": self.fields}),
        ]

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.pk:
            return tuple(self.readonly_fields) + ("namespace",)
        else:
            return self.readonly_fields

    fields = (
            'app_title', 'show_landing_page', 'allow_post', 'permalink_type', 'non_permalink_handling',
            'template_prefix', 'paginate_by', 'pagination_pages_start',
            'pagination_pages_visible', 'exclude_featured',
            'create_authors', 'search_indexed', 'show_in_listing',
            'show_in_related', 'show_in_specific',
            'show_logo', 'auto_read_time',
            'custom_fields_settings', 'custom_fields'
        )


admin.site.register(models.NewsBlogConfig, NewsBlogConfigAdmin)


class NewsBlogFeedAdmin(
    BaseAppHookConfig,
    TranslatableAdmin
):
    form = forms.NewsBlogFeedAdminForm

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if 'articles' not in fieldsets[0][1]['fields']:
            fieldsets[0][1]['fields'] += (
                'articles',
            )
        return fieldsets

    def get_config_fields(self):
        return (
            'app_title', 'number',
        )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        obj.article_set.set(form.cleaned_data.get('articles'))

if ENABLE_FEEDS:
    admin.site.register(models.NewsBlogFeed, NewsBlogFeedAdmin)

admin.site.register(models.ArticleMedium)
