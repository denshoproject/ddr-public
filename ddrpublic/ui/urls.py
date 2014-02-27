from django.conf.urls import patterns, include, url

# /
# /search/
# /browse/
# /browse/creators/
# /browse/facilities/
# /browse/formats/
# /browse/genres/
# /browse/languages/
# /browse/locations/
# /browse/persons/
# /browse/topics/
# /ddr/
# /ddr/testing/
# /ddr/testing/123/
# /ddr/testing/123/1/
# /ddr/testing/123/1/master/a1b2c3d4e5/

urlpatterns = patterns(
    '',
    
    url(r'^browse/(?P<facet>[\w]+)/$', 'ui.views.browse.facet', name='ui-browse-facet'),
    url(r'^browse/$', 'ui.views.browse.index', name='ui-browse-index'),
    
    url(r'^search/(?P<field>[\w]+):(?P<term>[\w ,]+)/$', 'ui.views.search.term_query', name='ui-search-term-query'),
    url(r'^search/results/$', 'ui.views.search.results', name='ui-search-results'),
    url(r'^search/$', 'ui.views.search.index', name='ui-search-index'),
    
    url(r'^cite/(?P<model>[\w]+)/(?P<object_id>[\w\d-]+)/$', 'ui.views.cite', name='ui-cite'),
    
    url(r'^collections/$', 'ui.views.collections.list', name='ui-collections-list'),
    
    url(r'^(?P<repo>[\w]+)/(?P<org>[\w]+)/(?P<cid>[\d]+)/(?P<eid>[\d]+)/(?P<role>[\w]+)/(?P<sha1>[\w]+)/$', 'ui.views.files.detail', name='ui-file'),

    url(r'^(?P<repo>[\w]+)/(?P<org>[\w]+)/(?P<cid>[\d]+)/(?P<eid>[\d]+)/files/$', 'ui.views.entities.files', name='ui-entity-files'),
    url(r'^(?P<repo>[\w]+)/(?P<org>[\w]+)/(?P<cid>[\d]+)/(?P<eid>[\d]+)/$', 'ui.views.entities.detail', name='ui-entity'),
    
    url(r'^(?P<repo>[\w]+)/(?P<org>[\w]+)/(?P<cid>[\d]+)/files/$', 'ui.views.collections.files', name='ui-collection-files'),
    url(r'^(?P<repo>[\w]+)/(?P<org>[\w]+)/(?P<cid>[\d]+)/objects/$', 'ui.views.collections.entities', name='ui-collection-entities'),
    url(r'^(?P<repo>[\w]+)/(?P<org>[\w]+)/(?P<cid>[\d]+)/$', 'ui.views.collections.detail', name='ui-collection'),
    
    url(r'^(?P<repo>[\w]+)/(?P<org>[\w]+)/$', 'ui.views.organizations.detail', name='ui-organization'),
    
    url(r'^(?P<repo>[\w]+)/$', 'ui.views.repo.detail', name='ui-repo'),
    
    url(r'^$', 'ui.views.index', name='ui-index'),
)
