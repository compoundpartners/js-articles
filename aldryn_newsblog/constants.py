# -*- coding: utf-8 -*-

from django.conf import settings
from django.utils.text import slugify

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

SUMMARY_RICHTEXT = getattr(
    settings,
    'ARTICLES_SUMMARY_RICHTEXT',
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

try:
    IS_THERE_COMPANIES = True
    from js_companies.models import Company
except:
    IS_THERE_COMPANIES = False
