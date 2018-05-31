from django.conf.urls import patterns, include, url

urlpatterns = patterns(
    '',
    url(r"^search/$", 'names.views.search', name='names-search'),
    url(r"^(?P<id>[\w\W]+)/$", 'names.views.detail', name='names-detail'),
    url(r"^$", 'names.views.index', name='names-index'),
)
