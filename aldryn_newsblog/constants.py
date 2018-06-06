# -*- coding: utf-8 -*-

from django.conf import settings

SHOW_RELATED_ARTICLES = getattr(
    settings,
    'SHOW_RELATED_ARTICLES',
    True,
)
