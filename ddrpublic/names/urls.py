from django.conf.urls import patterns, include, url

urlpatterns = patterns(
    '',
    url(r"^(?P<page>[\w\W]+)/$", 'names.views.detail', name='names-detail'),
    url(r"^/$", 'names.views.index', name='names-index'),
)
