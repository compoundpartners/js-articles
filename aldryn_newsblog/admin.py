# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from aldryn_apphooks_config.admin import BaseAppHookConfig, ModelAppHookConfig
from aldryn_people.models import Person
from aldryn_translation_tools.admin import AllTranslationsMixin
from cms.admin.placeholderadmin import FrontendEditableAdminMixin
from cms.utils.i18n import get_current_language, get_language_list
from cms.utils import copy_plugins, get_current_site

from django.db import transaction
from django.db.models.query import EmptyQuerySet
from django import forms
from django.conf.urls import url
from django.contrib import admin
from django.contrib.sites.models import Site
from django.forms import widgets
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
from parler.forms import TranslatableModelForm
from sortedm2m_filter_horizontal_widget.forms import SortedFilteredSelectMultiple

try:
    from js_custom_fields.forms import CustomFieldsFormMixin, CustomFieldsSettingsFormMixin
except:
    class CustomFieldsFormMixin(object):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields['custom_fields'].widget = forms.HiddenInput()

    class CustomFieldsSettingsFormMixin(object):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields['custom_fields_settings'].widget = forms.HiddenInput()

from . import models, default_medium

from .constants import (
    HIDE_RELATED_ARTICLES,
    HIDE_TAGS,
    HIDE_USER,
    ENABLE_LOCATIONS,
    ENABLE_READTIME,
    SUMMARY_RICHTEXT,
    IS_THERE_COMPANIES,
    ARTICLE_LAYOUT_CHOICES,
    SHOW_LOGO,
    TRANSLATE_IS_PUBLISHED,
    TRANSLATE_AUTHORS,
    ENABLE_FEEDS,
)
if IS_THERE_COMPANIES:
    from js_companies.models import Company


from cms.admin.placeholderadmin import PlaceholderAdminMixin

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
        super(ArticleAdminForm, self).__init__(*args, **kwargs)

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
            self.fields['lead_in'].widget = widgets.Textarea()
        if IS_THERE_COMPANIES:
            self.fields['companies'] = forms.ModelMultipleChoiceField(queryset=Company.objects.all(), required=False)# self.instance.companies
            self.fields['companies'].widget = SortedFilteredSelectMultiple()
            self.fields['companies'].queryset = Company.objects.all()
            if self.instance.pk and self.instance.companies.count():
                self.fields['companies'].initial = self.instance.companies.all()
        else:
            del self.fields['companies']

    def get_custom_fields(self):
        if self.instance and hasattr(self.instance, 'app_config'):
            return self.instance.app_config.custom_fields_settings


class ArticleAdmin(
    PlaceholderAdminMixin,
    FrontendEditableAdminMixin,
    ModelAppHookConfig,
    TranslatableAdmin
):
    def get_queryset(self, request):
        return self.model.all_objects

    form = ArticleAdminForm
    list_display = ('title_view', 'app_config', 'is_featured',
                    'is_published', 'publishing_date')
    list_filter = [
        'app_config',
        'categories',
        'services',
    ]
    if ENABLE_LOCATIONS:
        list_filter += [
            'locations',
        ]

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

    if HIDE_TAGS == 0:
        advanced_settings_fields += (
            'tags',
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
        'lead_in',
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
    app_config_values = {
        'default_published': 'is_published'
    }
    app_config_selection_title = ''
    app_config_selection_desc = ''

    def get_list_display(self, request):
        fields = []
        list_display = super(ArticleAdmin, self).get_list_display(request)
        for field in list_display:
            if field  in ['is_published', 'is_featured'] and TRANSLATE_IS_PUBLISHED:
                field += '_trans'
            fields.append(field)
        return fields

    def get_fieldsets(self, request, obj=None):
        fieldsets = super(ArticleAdmin, self).get_fieldsets(request, obj)
        if SHOW_LOGO and obj and obj.app_config.show_logo and 'logo_image' not in fieldsets[0][1]['fields']:
            fieldsets[0][1]['fields'] += [
                'logo_image',
            ]
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


class NewsBlogConfigAdminForm(CustomFieldsSettingsFormMixin, TranslatableModelForm):
    pass


class NewsBlogConfigAdmin(
    PlaceholderAdminMixin,
    BaseAppHookConfig,
    TranslatableAdmin
):
    form = NewsBlogConfigAdminForm

    def get_config_fields(self):
        return (
            'app_title', 'allow_post', 'permalink_type', 'non_permalink_handling',
            'template_prefix', 'paginate_by', 'pagination_pages_start',
            'pagination_pages_visible', 'exclude_featured',
            'create_authors', 'search_indexed', 'show_in_listing',
            'show_logo',
            'config.default_published', 'custom_fields_settings',
        )


admin.site.register(models.NewsBlogConfig, NewsBlogConfigAdmin)


class NewsBlogFeedAdminForm(TranslatableModelForm):
    articles = forms.ModelMultipleChoiceField(queryset=models.Article.objects.all(), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['articles'].widget = SortedFilteredSelectMultiple()
        self.fields['articles'].queryset = models.Article.objects.all()
        if self.instance.pk and self.instance.article_set.count():
            self.fields['articles'].initial = self.instance.article_set.all()


class NewsBlogFeedAdmin(
    BaseAppHookConfig,
    TranslatableAdmin
):
    form = NewsBlogFeedAdminForm

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
