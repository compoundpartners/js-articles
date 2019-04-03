# -*- coding: utf-8 -*-

from django.conf import settings

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
