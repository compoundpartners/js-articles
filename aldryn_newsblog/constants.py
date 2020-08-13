# -*- coding: utf-8 -*-

from django.conf import settings
from django.utils.text import slugify

UPDATE_SEARCH_DATA_ON_SAVE = getattr(
    settings,
    'ALDRYN_NEWSBLOG_UPDATE_SEARCH_DATA_ON_SAVE',
    False,
)
SEARCH_SKIP_PLUGINS = getattr(
    settings,
    'SEARCH_SKIP_PLUGINS',
    [],
)

HIDE_RELATED_ARTICLES = getattr(
    settings,
    'ARTICLES_HIDE_RELATED',
    False,
)

HIDE_TAGS = getattr(
    settings,
    'ARTICLES_HIDE_TAGS',
    False,
)

HIDE_USER = getattr(
    settings,
    'ARTICLES_HIDE_USER',
    False,
)

ENABLE_LOCATIONS = getattr(
    settings,
    'ARTICLES_ENABLE_LOCATIONS',
    False,
)

ENABLE_READTIME = getattr(
    settings,
    'ARTICLES_ENABLE_READTIME',
    False,
)

SUMMARY_RICHTEXT = getattr(
    settings,
    'ARTICLES_SUMMARY_RICHTEXT',
    False,
)

SHOW_LOGO = getattr(
    settings,
    'ARTICLES_SHOW_LOGO',
    False,
)

SPECIFIC_ARTICLES_LAYOUTS = getattr(
    settings,
    'ARTICLES_SPECIFIC_LAYOUTS',
    (),
)
SPECIFIC_ARTICLES_LAYOUTS = zip(list(map(lambda s: slugify(s).replace('-', '_'), ('default',) + SPECIFIC_ARTICLES_LAYOUTS)), ('default',) + SPECIFIC_ARTICLES_LAYOUTS)

RELATED_ARTICLES_LAYOUTS = getattr(
    settings,
    'ARTICLES_RELATED_LAYOUTS',
    (),
)
RELATED_ARTICLES_LAYOUTS = zip(list(map(lambda s: slugify(s).replace('-', '_'), ('default',) + RELATED_ARTICLES_LAYOUTS)), ('default',) + RELATED_ARTICLES_LAYOUTS)

ADD_FILTERED_CATEGORIES = getattr(
    settings,
    'ARTICLES_ADD_FILTERED_CATEGORIES',
    [],
)
ADDITIONAL_EXCLUDE = getattr(
    settings,
    'ARTICLES_ADDITIONAL_EXCLUDE',
    {},
)
SITEMAP_CHANGEFREQ = getattr(
    settings,
    'ARTICLES_SITEMAP_CHANGEFREQ',
    'never',
)
SITEMAP_PRIORITY = getattr(
    settings,
    'ARTICLES_SITEMAP_PRIORITY',
    0.5,
)
SHOW_CONTER_FILTERS = getattr(
    settings,
    'ARTICLES_SHOW_CONTER_FILTERS',
    False,
)
ARTICLE_LAYOUTS = getattr(
    settings,
    'ARTICLES_ARTICLE_LAYOUTS',
    (),
)
ARTICLE_LAYOUT_CHOICES = list(ARTICLE_LAYOUTS)
if len(ARTICLE_LAYOUTS) == 0 or len(ARTICLE_LAYOUTS[0]) != 2:
    ARTICLE_LAYOUT_CHOICES = zip(list(map(lambda s: slugify(s).replace('-', '_'), ('',) + ARTICLE_LAYOUTS)), ('default',) + ARTICLE_LAYOUTS)
else:
    ARTICLE_LAYOUT_CHOICES.insert(0, ('', 'default'))

TRANSLATE_IS_PUBLISHED = getattr(
    settings,
    'ARTICLES_TRANSLATE_IS_PUBLISHED',
    False,
)
TRANSLATE_AUTHORS = getattr(
    settings,
    'ARTICLES_TRANSLATE_AUTHORS',
    False,
)
GET_NEXT_ARTICLE = getattr(
    settings,
    'ARTICLES_GET_NEXT_ARTICLE',
    False,
)
ADDITIONAL_CHILD_CLASSES = getattr(
    settings,
    'ARTICLES_ADDITIONAL_CHILD_CLASSES',
    {},
)
ENABLE_FEEDS = getattr(
    settings,
    'ARTICLES_ENABLE_FEEDS',
    False,
)
ARTICLE_CUSTOM_FIELDS = getattr(
    settings,
    'ARTICLES_ARTICLE_CUSTOM_FIELDS',
    {},
)
ARTICLE_SECTION_CUSTOM_FIELDS = getattr(
    settings,
    'ARTICLES_ARTICLE_SECTION_CUSTOM_FIELDS',
    {},
)

try:
    IS_THERE_COMPANIES = True
    from js_companies.models import Company
except:
    IS_THERE_COMPANIES = False
