# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from aldryn_translation_tools.sitemaps import I18NSitemap

from ..models import Article, NewsBlogConfig
from ..constants import SITEMAP_CHANGEFREQ, SITEMAP_PRIORITY, TRANSLATE_IS_PUBLISHED


class NewsBlogSitemap(I18NSitemap):

    changefreq = SITEMAP_CHANGEFREQ
    priority = SITEMAP_PRIORITY

    def __init__(self, *args, **kwargs):
        self.namespace = kwargs.pop('namespace', None)
        if self.namespace == NewsBlogConfig.default_namespace:
            self.namespace = None
        self.sitemap_type = kwargs.pop('type', 'xml')
        super(NewsBlogSitemap, self).__init__(*args, **kwargs)

    def items(self):
        qs = Article.objects.published()
        if self.language is not None:
            qs = qs.language(self.language)
        if self.namespace is not None:
            qs = qs.filter(app_config__namespace=self.namespace)
        if self.sitemap_type == 'html':
            qs = qs.exclude(show_on_sitemap=False)
        elif self.sitemap_type == 'xml':
            qs = qs.exclude(show_on_xml_sitemap=False)
        return qs

    def lastmod(self, obj):
        return obj.publishing_date

try:
    from js_sitemap.alt_sitemap import SitemapAlt
    class NewsBlogSitemapAlt(SitemapAlt, NewsBlogSitemap):
        def get_queryset(self):
            if TRANSLATE_IS_PUBLISHED:
                return Article.objects.published_one_of_trans().prefetch_related('translations').distinct()
            return super(NewsBlogSitemapAlt, self).get_queryset()

        def languages(self, obj):
            if TRANSLATE_IS_PUBLISHED:
                return obj.translations.filter(is_published_trans=True).values_list('language_code', flat=True)
            return super(NewsBlogSitemapAlt, self).languages(obj)
except:
    pass
