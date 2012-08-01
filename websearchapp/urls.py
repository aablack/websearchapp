from django.conf.urls import patterns, include, url

from django.contrib.staticfiles.urls import staticfiles_urlpatterns

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
        url(r'^search/', include('search.urls')),
        )

# where to serve static files (for development)
urlpatterns += staticfiles_urlpatterns()

