# -*- coding: utf-8 -*-

from django.conf import settings

HIDE_RELATED_ARTICLES = getattr(
    settings,
    'HIDE_RELATED_ARTICLES',
    True,
)

HIDE_TAGS = getattr(
    settings,
    'HIDE_TAGS',
    True,
)
