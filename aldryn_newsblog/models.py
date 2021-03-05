# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import django.core.validators
from aldryn_apphooks_config.fields import AppHookConfigField
from aldryn_categories.fields import CategoryManyToManyField
from aldryn_categories.models import Category
from aldryn_newsblog.utils.utilities import get_valid_languages_from_request
from aldryn_people.models import Person
from aldryn_translation_tools.models import TranslatedAutoSlugifyMixin, TranslationHelperMixin
from cms.models.fields import PlaceholderField
from cms.models.pluginmodel import CMSPlugin
from cms.utils.i18n import get_current_language, get_redirect_on_fallback
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
try:
    from django.core.urlresolvers import reverse
except ImportError:
    # Django 2.0
    from django.urls import reverse
from django.contrib.postgres.fields import JSONField
from django.db import connection, models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.encoding import python_2_unicode_compatible
from django.utils.functional import cached_property
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import override, ugettext
from djangocms_icon.fields import Icon
from djangocms_text_ckeditor.fields import HTMLField
from filer.fields.image import FilerImageField
from parler.models import TranslatableModel, TranslatedFields
from sortedm2m.fields import SortedManyToManyField

from .cms_appconfig import NewsBlogConfig, NewsBlogFeed
from .managers import RelatedManager, AllManager, SearchManager
from .utils import get_plugin_index_data, get_request, strip_tags

try:
    from django.utils.encoding import force_unicode
except ImportError:
    try:
        from django.utils.encoding import force_text as force_unicode
    except ImportError:
        def force_unicode(value):
            return value.decode()

from .constants import (
    IS_THERE_COMPANIES,
    TRANSLATE_IS_PUBLISHED,
    TRANSLATE_AUTHORS,
)


if settings.LANGUAGES:
    LANGUAGE_CODES = [language[0] for language in settings.LANGUAGES]
elif settings.LANGUAGE:
    LANGUAGE_CODES = [settings.LANGUAGE]
else:
    raise ImproperlyConfigured(
        'Neither LANGUAGES nor LANGUAGE was found in settings.')


# At startup time, SQL_NOW_FUNC will contain the database-appropriate SQL to
# obtain the CURRENT_TIMESTAMP.
SQL_NOW_FUNC = {
    'mssql': 'GetDate()', 'mysql': 'NOW()', 'postgresql': 'now()',
    'sqlite': 'CURRENT_TIMESTAMP', 'oracle': 'CURRENT_TIMESTAMP'
}[connection.vendor]

SQL_IS_TRUE = {
    'mssql': '== TRUE', 'mysql': '= 1', 'postgresql': 'IS TRUE',
    'sqlite': '== 1', 'oracle': 'IS TRUE'
}[connection.vendor]


try:
    from custom.aldryn_newsblog.models import CustomArticleMixin
except:
    class CustomArticleMixin(object):
        pass


@python_2_unicode_compatible
class ArticleMedium(models.Model):
    title = models.CharField(_('title'), max_length=255)
    position = models.PositiveSmallIntegerField(
        default=0,
        blank=False,
    )

    class Meta:
        ordering = ['position']
        verbose_name = _('Medium')
        verbose_name_plural = _('Medium')

    def __str__(self):
        return self.title



@python_2_unicode_compatible
class Article(CustomArticleMixin,
              TranslatedAutoSlugifyMixin,
              TranslationHelperMixin,
              TranslatableModel):

    # TranslatedAutoSlugifyMixin options
    slug_source_field_name = 'title'
    slug_default = _('untitled-article')
    # when True, updates the article's search_data field
    # whenever the article is saved or a plugin is saved
    # on the article's content placeholder.
    update_search_on_save = getattr(
        settings,
        'ALDRYN_NEWSBLOG_UPDATE_SEARCH_DATA_ON_SAVE',
        False
    ) or getattr(
        settings,
        'ALDRYN_NEWSBLOG_AUTO_CALCULATE_READ_TIME',
        False
    )

    translations = TranslatedFields(
        title=models.CharField(_('title'), max_length=234),
        slug=models.SlugField(
            verbose_name=_('slug'),
            max_length=255,
            db_index=True,
            blank=True,
            help_text=_(
                'Used in the URL. If changed, the URL will change. '
                'Clear it to have it re-created automatically.'),
        ),
        lead_in=HTMLField(
            verbose_name=_('Summary'), default='',
            help_text=_(
                'The Summary gives the reader the main idea of the story, this '
                'is useful in overviews, lists or as an introduction to your '
                'article.'
            ),
            blank=True,
        ),
        read_time=models.CharField(
            max_length=255, verbose_name=_('Read time'),
            blank=True, default=''),
        meta_title=models.CharField(
            max_length=255, verbose_name=_('meta title'),
            blank=True, default=''),
        meta_description=models.TextField(
            verbose_name=_('meta description'), blank=True, default=''),
        meta_keywords=models.TextField(
            verbose_name=_('meta keywords'), blank=True, default=''),
        meta={'unique_together': (('language_code', 'slug', ), )},

        search_data=models.TextField(blank=True, editable=False),

        author_trans = models.ForeignKey(Person, on_delete=models.SET_NULL,
            related_name='articles_trans', null=True, blank=True,
            verbose_name=_('author')),
        author_2_trans = models.ForeignKey(Person, on_delete=models.SET_NULL,
            related_name='articles_trans_2', null=True, blank=True,
            verbose_name=_('second author')),
        author_3_trans = models.ForeignKey(Person, on_delete=models.SET_NULL,
            related_name='articles_trans_3', null=True, blank=True,
            verbose_name=_('third author')),
        is_published_trans = models.BooleanField(_('is published'),
            default=False, db_index=True),
        is_featured_trans = models.BooleanField(_('is featured'),
            default=False, db_index=True),
    )

    content = PlaceholderField('newsblog_article_content',
                               related_name='newsblog_article_content')
    related_articles = PlaceholderField('newsblog_related_articles',
                                related_name='newsblog_related_articles')
    article_carousel = PlaceholderField('newsblog_article_carousel',
                                related_name='newsblog_article_carousel')
    article_sidebar = PlaceholderField('newsblog_article_sidebar',
                                related_name='newsblog_article_sidebar')
    hide_authors = models.BooleanField(_('Hide Authors'),
                                default=False,)
    author = models.ForeignKey(Person, on_delete=models.SET_NULL, null=True, blank=True,
                               verbose_name=_('author'))
    author_2 = models.ForeignKey(Person, on_delete=models.SET_NULL, related_name='author_2', null=True, blank=True,
                               verbose_name=_('second author'))
    author_3 = models.ForeignKey(Person, on_delete=models.SET_NULL, related_name='author_3', null=True, blank=True,
                               verbose_name=_('third author'))
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, verbose_name=_('owner'),
                              null=True, blank=True)
    app_config = AppHookConfigField(
        NewsBlogConfig,
        on_delete=models.CASCADE,
        verbose_name=_('Section'),
        help_text='',
    )
    locations = SortedManyToManyField('js_locations.location',
                                       verbose_name=_('locations'),
                                       blank=True)
    categories = CategoryManyToManyField('aldryn_categories.Category',
                                         verbose_name=_('categories'),
                                         blank=True)
    services = SortedManyToManyField('js_services.Service',
                                     verbose_name=_('services'),
                                     blank=True)
    feeds = models.ManyToManyField(NewsBlogFeed,
                                   verbose_name=_('feeds'),
                                   blank=True)
    publishing_date = models.DateTimeField(_('publishing date'),
                                           default=now)
    is_published = models.BooleanField(_('is published'), default=False,
                                       db_index=True)
    is_featured = models.BooleanField(_('is featured'), default=False,
                                      db_index=True)
    featured_image = FilerImageField(
        verbose_name=_('featured image'),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    share_image = FilerImageField(
        verbose_name=_('social share image'),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text='This image will only be shown on social channels. Minimum size: 1200x630px',
        related_name='+'
    )
    logo_image = FilerImageField(
        verbose_name=_('logo image'),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    medium = models.ForeignKey(ArticleMedium, on_delete=models.SET_NULL, verbose_name=_('medium'),
                              null=True, blank=True)

    show_on_sitemap = models.BooleanField(_('Show on sitemap'), null=False, default=True)
    show_on_xml_sitemap = models.BooleanField(_('Show on xml sitemap'), null=False, default=True)
    noindex = models.BooleanField(_('noindex'), null=False, default=False)
    nofollow = models.BooleanField(_('nofollow'), null=False, default=False)
    canonical_url = models.CharField(
        blank=True,
        null=True,
        max_length=255,
        verbose_name=_('Canonical URL')
    )

    layout = models.CharField(
        blank=True,
        default='',
        max_length=60,
        verbose_name=_('layout')
    )
    custom_fields = JSONField(blank=True, null=True)
    # Setting "symmetrical" to False since it's a bit unexpected that if you
    # set "B relates to A" you immediately have also "A relates to B". It have
    # to be forced to False because by default it's True if rel.to is "self":
    #
    # https://github.com/django/django/blob/1.8.4/django/db/models/fields/related.py#L2144
    #
    # which in the end causes to add reversed releted-to entry as well:
    #
    # https://github.com/django/django/blob/1.8.4/django/db/models/fields/related.py#L977
    related = SortedManyToManyField('self', verbose_name=_('specific articles'),
                                    blank=True, symmetrical=False)

    objects = RelatedManager()
    all_objects = AllManager()
    search_objects = SearchManager()

    class Meta:
        ordering = ['-publishing_date']

    def get_class(self):
        '''Return class name'''
        return self.__class__.__name__

    @property
    def type(self):
        '''Article Type / Section.'''
        return self.app_config

    @cached_property
    def cached_type(self):
        '''Article Type / Section.'''
        return self.app_config

    @property
    def type_slug(self):
        '''Article Type / Section Machine Name'''
        return self.app_config.namespace

    @property
    def published(self):
        """
        Returns True only if the article (is_published == True) AND has a
        published_date that has passed.
        """
        language = get_current_language()
        return self.published_for_language(language)

    def published_for_language(self, language):
        if TRANSLATE_IS_PUBLISHED:
            return (
                (self.safe_translation_getter('is_published_trans', language_code=language, any_language=False) or False
            ) and self.publishing_date <= now())
        return (self.is_published and self.publishing_date <= now())

    @property
    def authors(self):
        authors = []
        if TRANSLATE_AUTHORS:
            if self.author_trans and self.author_trans.published:
                authors.append(self.author_trans)
            if self.author_2_trans and self.author_2_trans.published:
                authors.append(self.author_2_trans)
            if self.author_3_trans and self.author_3_trans.published:
                authors.append(self.author_3_trans)
        else:
            if self.author and self.author.published:
                authors.append(self.author)
            if self.author_2 and self.author_2.published:
                authors.append(self.author_2)
            if self.author_3 and self.author_3.published:
                authors.append(self.author_3)
        return authors

    @property
    def future(self):
        """
        Returns True if the article is published but is scheduled for a
        future date/time.
        """
        return (self.is_published and self.publishing_date > now())

    def get_absolute_url(self, language=None):
        """Returns the url for this Article in the selected permalink format."""
        if not language:
            language = get_current_language()
        kwargs = {}
        permalink_type = self.cached_type.permalink_type
        if 'y' in permalink_type:
            kwargs.update(year=self.publishing_date.year)
        if 'm' in permalink_type:
            kwargs.update(month="%02d" % self.publishing_date.month)
        if 'd' in permalink_type:
            kwargs.update(day="%02d" % self.publishing_date.day)
        if 'i' in permalink_type:
            kwargs.update(pk=self.pk)
        if 's' in permalink_type:
            slug, lang = self.known_translation_getter(
                'slug', default=None, language_code=language)
            if slug and lang:
                site_id = getattr(settings, 'SITE_ID', None)
                if get_redirect_on_fallback(language, site_id):
                    language = lang
                kwargs.update(slug=slug)

        if self.cached_type.namespace:
            namespace = self.cached_type.namespace
            try:
                reverse('{0}:article-list'.format(namespace))
            except:
                namespace = NewsBlogConfig.default_namespace
        else:
            namespace = NewsBlogConfig.default_namespace

        with override(language):
            return reverse('{0}:article-detail'.format(namespace), kwargs=kwargs)

    def get_public_url(self, language=None):
        if not language:
            language = get_current_language()
        if not TRANSLATE_IS_PUBLISHED and self.published:
            return self.get_absolute_url(language)
        if (TRANSLATE_IS_PUBLISHED and \
                (self.safe_translation_getter('is_published_trans', language_code=language, any_language=False) or False) and \
                self.publishing_date <= now()):
            return self.get_absolute_url(language)
        return ''

    def get_search_data(self, language=None, request=None):
        """
        Provides an index for use with Haystack, or, for populating
        Article.translations.search_data.
        """
        if not self.pk:
            return ''
        if language is None:
            language = get_current_language()
        if request is None:
            request = get_request(language=language)
        title = self.safe_translation_getter('title', '')
        description = self.safe_translation_getter('lead_in', '')
        text_bits = [title, strip_tags(description)]
        for category in self.categories.all():
            text_bits.append(
                force_unicode(category.safe_translation_getter('name')))
        for service in self.services.all():
            text_bits.append(
                force_unicode(service.safe_translation_getter('title')))
        text_bits.append('=c=o=n=t=e=n=t=')
        if self.content:
            plugins = self.content.cmsplugin_set.filter(language=language)
            for base_plugin in plugins:
                plugin_text_content = ' '.join(
                    get_plugin_index_data(base_plugin, request))
                text_bits.append(plugin_text_content)
        return ' '.join(text_bits)

    def save(self, *args, **kwargs):
        # Update the search index
        if self.update_search_on_save:
            self.search_data = self.get_search_data()
            auto_read_time = getattr(
                settings,
                'ALDRYN_NEWSBLOG_AUTO_CALCULATE_READ_TIME',
                False
            )
            if callable(auto_read_time):
                auto_read_time = auto_read_time(self)
            if auto_read_time and self.app_config.auto_read_time:
                read_time = self.get_read_time()
                if read_time:
                    self.read_time = read_time
        # Ensure there is an owner.
        if self.app_config.create_authors and self.owner and self.author is None:
            if hasattr(Person, 'first_name') and hasattr(Person, 'last_name'):
                defaults={
                    'first_name': self.owner.first_name,
                    'last_name': self.owner.last_name,
                }
            else:
                defaults={'name': ' '.join((
                        self.owner.first_name,
                        self.owner.last_name,
                    )),
                }
            self.author = Person.objects.get_or_create(
                user=self.owner, defaults=defaults
                )[0]
        # slug would be generated by TranslatedAutoSlugifyMixin
        #if not self.medium:
            #self.medium = ArticleMedium.objects.first()
        super(Article, self).save(*args, **kwargs)

    def get_read_time(self):
        if '=c=o=n=t=e=n=t=' in self.search_data:
           read_time_function = getattr(settings,
                'ALDRYN_NEWSBLOG_READ_TIME_FUNCTION',
                lambda x : x // 200 + (0 if x % 200 == 0 else 1) )
           return read_time_function(len(self.search_data.split('=c=o=n=t=e=n=t=')[1].split()))

    def get_placeholders(self):
        return [
            self.content,
            self.related_articles,
            self.article_carousel,
            self.article_sidebar
        ]

    def __str__(self):
        return self.safe_translation_getter('title', any_language=True)

    def get_related_articles_by_services(self, article_category=None):
        articles = self.__class__.objects.published().filter(services__in=self.services.all()).distinct().exclude(id=self.id)
        if article_category:
            return articles.namespace(article_category)
        return articles

    def get_related_articles_by_categories(self, article_category=None):
        articles = self.__class__.objects.published().filter(categories__in=self.categories.all()).distinct().exclude(id=self.id)
        if article_category:
            return articles.namespace(article_category)
        return articles

    def related_articles_by_services(self):
        return self.get_related_articles_by_services()

    def related_articles_by_categories(self):
        return self.get_related_articles_by_categories()

    def related_articles_same_type_by_services(self):
        return self.get_related_articles_by_services(self.app_config.namespace)

    def related_articles_same_type_by_categories(self):
        return self.get_related_articles_by_categories(self.app_config.namespace)


class PluginEditModeMixin(object):
    def get_edit_mode(self, request):
        """
        Returns True only if an operator is logged-into the CMS and is in
        edit mode.
        """
        return (
            hasattr(request, 'toolbar') and request.toolbar and
            request.toolbar.edit_mode_active)


class AdjustableCacheModelMixin(models.Model):
    # NOTE: This field shouldn't even be displayed in the plugin's change form
    # if using django CMS < 3.3.0
    cache_duration = models.PositiveSmallIntegerField(
        default=0,  # not the most sensible, but consistent with older versions
        blank=False,
        help_text=_(
            "The maximum duration (in seconds) that this plugin's content "
            "should be cached.")
    )

    class Meta:
        abstract = True


class NewsBlogCMSPlugin(CMSPlugin):
    """AppHookConfig aware abstract CMSPlugin class for Aldryn Newsblog"""
    # avoid reverse relation name clashes by not adding a related_name
    # to the parent plugin
    cmsplugin_ptr = models.OneToOneField(
        CMSPlugin, on_delete=models.CASCADE, related_name='+', parent_link=True)

    app_config = models.ForeignKey(NewsBlogConfig, on_delete=models.CASCADE, verbose_name=_('Apphook configuration'))

    class Meta:
        abstract = True

    def copy_relations(self, old_instance):
        self.app_config = old_instance.app_config


@python_2_unicode_compatible
class NewsBlogCategoriesPlugin(PluginEditModeMixin, NewsBlogCMSPlugin):
    def __str__(self):
        return ugettext('%s categories') % (self.app_config.get_app_title(), )

    def get_categories(self, request):
        """
        Returns a list of categories, annotated by the number of articles
        (article_count) that are visible to the current user. If this user is
        anonymous, then this will be all articles that are published and whose
        publishing_date has passed. If the user is a logged-in cms operator,
        then it will be all articles.
        """

        subquery = """
            SELECT COUNT(*)
            FROM aldryn_newsblog_article, aldryn_newsblog_article_categories
            WHERE
                aldryn_newsblog_article_categories.category_id =
                    aldryn_categories_category.id AND
                aldryn_newsblog_article_categories.article_id =
                    aldryn_newsblog_article.id AND
                aldryn_newsblog_article.app_config_id = %d
        """ % (self.app_config.pk, )

        if not self.get_edit_mode(request):
            subquery += """ AND
                aldryn_newsblog_article.is_published %s AND
                aldryn_newsblog_article.publishing_date <= %s
            """ % (SQL_IS_TRUE, SQL_NOW_FUNC, )

        query = """
            SELECT (%s) as article_count, aldryn_categories_category.*
            FROM aldryn_categories_category
        """ % (subquery, )

        raw_categories = list(Category.objects.raw(query))
        categories = [
            category for category in raw_categories if category.article_count]
        return sorted(categories, key=lambda x: x.article_count, reverse=True)



@python_2_unicode_compatible
class NewsBlogRelatedPlugin(PluginEditModeMixin, AdjustableCacheModelMixin,
                            CMSPlugin):
    # NOTE: This one does NOT subclass NewsBlogCMSPlugin. This is because this
    # plugin can really only be placed on the article detail view in an apphook.
    cmsplugin_ptr = models.OneToOneField(
        CMSPlugin, on_delete=models.CASCADE, related_name='+', parent_link=True)
    title = models.CharField(max_length=255, blank=True, verbose_name=_('Title'))
    layout = models.CharField(max_length=30, verbose_name=_('layout'), blank=True, null=True)
    related_articles = SortedManyToManyField(Article, verbose_name=_('related articles'), blank=True, symmetrical=False)
    more_button_is_shown = models.BooleanField(blank=True, default=False, verbose_name=_('Show “See More Button”'))
    more_button_text = models.CharField(max_length=255, blank=True, verbose_name=_('See More Button Text'))
    more_button_link = models.CharField(max_length=255, blank=True, verbose_name=_('See More Button Link'))

    def copy_relations(self, oldinstance):
        self.related_articles.set(oldinstance.related_articles.all())

    def get_articles(self, article, request):
        """
        Returns a queryset of articles that are related to the given article.
        """
        languages = get_valid_languages_from_request(
            article.app_config.namespace, request)
        if self.language not in languages:
            return Article.objects.none()
        qs = article.related.translated(*languages)
        if not self.get_edit_mode(request):
            qs = qs.published()
        return qs

    def __str__(self):
        return ugettext('Specific articles')



@python_2_unicode_compatible
class NewsBlogJSRelatedPlugin(PluginEditModeMixin, AdjustableCacheModelMixin,
                            CMSPlugin):
    # NOTE: This one does NOT subclass NewsBlogCMSPlugin. This is because this
    # plugin can really only be placed on the article detail view in an apphook.
    cmsplugin_ptr = models.OneToOneField(
        CMSPlugin, on_delete=models.CASCADE, related_name='+', parent_link=True)

    title = models.CharField(max_length=255, blank=True, verbose_name=_('Title'))
    icon = Icon(blank=False, default='')
    image = FilerImageField(on_delete=models.SET_NULL, null=True, blank=True, related_name="title_image")
    number_of_articles = models.PositiveSmallIntegerField(verbose_name=_('Number of articles'), validators=[django.core.validators.MaxValueValidator(120)])
    layout = models.CharField(max_length=30, verbose_name=_('layout'))
    featured = models.BooleanField(blank=True, default=False)
    exclude_current_article = models.BooleanField(blank=True, default=False)
    related_types = SortedManyToManyField(NewsBlogConfig, verbose_name=_('related sections'), blank=True, symmetrical=False)
    related_mediums = SortedManyToManyField(ArticleMedium, verbose_name=_('medium'), blank=True, symmetrical=False)
    related_categories = SortedManyToManyField(Category, verbose_name=_('related categories'), blank=True, symmetrical=False)
    related_service_sections = SortedManyToManyField('js_services.ServicesConfig', verbose_name=_('related service section'), blank=True, symmetrical=False)
    related_services = SortedManyToManyField('js_services.Service', verbose_name=_('related services'), blank=True, symmetrical=False)
    related_authors = SortedManyToManyField(Person, verbose_name=_('related authors'), blank=True, symmetrical=False)
    more_button_is_shown = models.BooleanField(blank=True, default=False, verbose_name=_('Show “See More Button”'))
    more_button_text = models.CharField(max_length=255, blank=True, verbose_name=_('See More Button Text'))
    more_button_link = models.CharField(max_length=255, blank=True, verbose_name=_('See More Button Link'))

    def copy_relations(self, oldinstance):
        self.related_types.set(oldinstance.related_types.all())
        self.related_mediums.set(oldinstance.related_mediums.all())
        self.related_categories.set(oldinstance.related_categories.all())
        self.related_service_sections.set(oldinstance.related_service_sections.all())
        self.related_services.set(oldinstance.related_services.all())
        self.related_authors.set(oldinstance.related_authors.all())
        if IS_THERE_COMPANIES:
            self.related_companies.set(oldinstance.related_companies.all())

    # def get_articles(self, article, request):
    #     """
    #     Returns a queryset of articles that are related to the given article.
    #     """
    #     languages = get_valid_languages_from_request(
    #         article.app_config.namespace, request)
    #     if self.language not in languages:
    #         return Article.objects.none()
    #     qs = article.related.translated(*languages)
    #     if not self.get_edit_mode(request):
    #         qs = qs.published()
    #     return qs

    def __str__(self):
        return ugettext('Related articles')


@receiver(post_save, dispatch_uid='article_update_search_data')
def update_search_data(sender, instance, **kwargs):
    """
    Upon detecting changes in a plugin used in an Article's content
    (PlaceholderField), update the article's search_index so that we can
    perform simple searches even without Haystack, etc.
    """
    is_cms_plugin = issubclass(instance.__class__, CMSPlugin)

    if Article.update_search_on_save and is_cms_plugin:
        placeholder = (getattr(instance, '_placeholder_cache', None) or
                       instance.placeholder)
        if hasattr(placeholder, '_attached_model_cache'):
            if placeholder._attached_model_cache == Article and placeholder.slot == 'newsblog_article_content':
                article = placeholder._attached_model_cache.objects.language(
                    instance.language).get(content=placeholder.pk)
                #article.search_data = article.get_search_data(instance.language)
                article.save()
