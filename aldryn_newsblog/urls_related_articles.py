from django.conf.urls import url

from aldryn_newsblog.views import RelatedArticles

urlpatterns = [
    url(r'^$',
        RelatedArticles.as_view(), name='related_articles'),
    url(r'^(?P<type>\w[-\w]*)/$',
        RelatedArticles.as_view(), name='related_articles'),
    url(r'^(?P<type>\w[-\w]*)/(?P<category>\w[-\w]*)/$',
        RelatedArticles.as_view(), name='related_articles'),
    url(r'^(?P<type>\w[-\w]*)/(?P<category>\w[-\w]*)/(?P<author>\w[-\w]*)/$',
        RelatedArticles.as_view(), name='related_articles'),

]
