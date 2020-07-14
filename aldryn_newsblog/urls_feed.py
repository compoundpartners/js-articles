from django.conf.urls import url

from aldryn_newsblog.feeds import CustomFeed

urlpatterns = [
    url(r'^$', CustomFeed(), name='articles-feed'),
]
