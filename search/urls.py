from django.conf.urls import patterns, include, url

urlpatterns = patterns('search.views',
    url(r'^$', 'search', name='search'),
)
