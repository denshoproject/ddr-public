from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView

from rest_framework.urlpatterns import format_suffix_patterns

urlpatterns = patterns(
    '',
    url(r'^names', include('names.urls')),
    
    url(r'^api/0.2/facet/(?P<facet_id>[\w]+)/(?P<term_id>[\d]+)/objects/$', 'ui.api.term_objects', name='ui-api-term-objects'),
    url(r'^api/0.2/facet/(?P<facet_id>[\w]+)/(?P<term_id>[\d]+)/$', 'ui.api.term', name='ui-api-term'),
    url(r'^api/0.2/facet/(?P<facet>[\w]+)/$', 'ui.api.facet', name='ui-api-facet'),
    url(r'^api/0.2/facet/$', 'ui.api.facet_index', name='ui-api-facets'),
    
    # lists
    url(r'^api/0.2/e/(?P<oid>[\w\d-]+)/children/$', 'ui.api.files', name='ui-api-files'),
    url(r'^api/0.2/c/(?P<oid>[\w\d-]+)/children/$', 'ui.api.entities', name='ui-api-entities'),
    url(r'^api/0.2/o/(?P<oid>[\w\d-]+)/children/$', 'ui.api.collections', name='ui-api-collections'),
    url(r'^api/0.2/r/(?P<oid>[\w\d-]+)/children/$', 'ui.api.organizations', name='ui-api-organizations'),
    
    # nodes
    url(r'^api/0.2/f/(?P<oid>[\w\d-]+)/$', 'ui.api.file', name='ui-api-file'),
    url(r'^api/0.2/s/(?P<oid>[\w\d-]+)/$', 'ui.api.entity', name='ui-api-segment'),
    url(r'^api/0.2/e/(?P<oid>[\w\d-]+)/$', 'ui.api.entity', name='ui-api-entity'),
    url(r'^api/0.2/c/(?P<oid>[\w\d-]+)/$', 'ui.api.collection', name='ui-api-collection'),
    url(r'^api/0.2/o/(?P<oid>[\w\d-]+)/$', 'ui.api.organization', name='ui-api-organization'),
    url(r'^api/0.2/r/(?P<oid>[\w\d-]+)/$', 'ui.api.repository', name='ui-api-repository'),
    
    url(r'^api/0.2/$', 'ui.api.index', name='ui-api-index'),
    url(r'^api/0.1/$', 'ui.api.index', name='ui-api-index'),
    
    url(r'^about/', TemplateView.as_view(template_name="ui/about.html"), name='ui-about'),
    url(r'^contact/$', TemplateView.as_view(template_name='ui/about.html'), name='ui-contact'),
    url(r'^faq/$', TemplateView.as_view(template_name='ui/faq.html'), name='ui-faq'),
    url(r'^terms/$', TemplateView.as_view(template_name='ui/terms.html'), name='ui-terms'),
    url(r'^using/$', TemplateView.as_view(template_name='ui/using.html'), name='ui-using'),

    url(r'^browse/(?P<facet_id>[\w]+)/(?P<term_id>[\d]+)/$', 'ui.views.browse.term', name='ui-browse-term'),
    url(r'^browse/(?P<facet>[\w]+)/$', 'ui.views.browse.facet', name='ui-browse-facet'),
    url(r'^browse/$', 'ui.views.browse.index', name='ui-browse-index'),
    
    url(r'^search/(?P<field>[\w]+):(?P<term>[\w ,]+)/$', 'ui.views.search.term_query', name='ui-search-term-query'),
    url(r'^search/results/$', 'ui.views.search.results', name='ui-search-results'),
    url(r'^search/$', 'ui.views.search.index', name='ui-search-index'),
    
    url(r'^cite/(?P<model>[\w]+)/(?P<object_id>[\w\d-]+)/$', 'ui.views.cite', name='ui-cite'),
    
    url(r'^collections/$', 'ui.views.collections.list', name='ui-collections-list'),
    
    url(r'^f/(?P<oid>[\w\d-]+)/$', 'ui.views.files.detail', name='ui-file'),
    url(r'^r/(?P<oid>[\w\d-]+)/$', 'ui.views.entities.nodes', name='ui-file-role'),
    
    url(r'^s/(?P<oid>[\w\d-]+)/files/$', 'ui.views.entities.nodes', name='ui-segment-nodes'),
    url(r'^s/(?P<oid>[\w\d-]+)/objects/$', 'ui.views.entities.children', name='ui-segment-children'),
    url(r'^s/(?P<oid>[\w\d-]+)/$', 'ui.views.entities.detail', name='ui-segment'),
    
    url(r'^e/(?P<oid>[\w\d-]+)/files/$', 'ui.views.entities.nodes', name='ui-entity-nodes'),
    url(r'^e/(?P<oid>[\w\d-]+)/objects/$', 'ui.views.entities.children', name='ui-entity-children'),
    url(r'^e/(?P<oid>[\w\d-]+)/$', 'ui.views.entities.detail', name='ui-entity'),
    
    url(r'^c/(?P<oid>[\w\d-]+)/files/$', 'ui.views.collections.nodes', name='ui-collection-nodes'),
    url(r'^c/(?P<oid>[\w\d-]+)/objects/$', 'ui.views.collections.children', name='ui-collection-children'),
    url(r'^c/(?P<oid>[\w\d-]+)/$', 'ui.views.collections.detail', name='ui-collection'),
    
    url(r'^o/(?P<oid>[\w\d-]+)/$', 'ui.views.organizations.detail', name='ui-organization'),
    
    url(r'^r/(?P<oid>[\w\d-]+)/$', 'ui.views.repo.detail', name='ui-repo'),
    
    url(r'^$', 'ui.views.index', name='ui-index'),
)

urlpatterns = format_suffix_patterns(urlpatterns)
