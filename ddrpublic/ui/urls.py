from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView

from rest_framework.urlpatterns import format_suffix_patterns

urlpatterns = patterns(
    '',
    url(r'^names', include('names.urls')),
    
    url(r'^api/0.2/search/help/', TemplateView.as_view(template_name="ui/search/help.html"), name='ui-about'),
    url(r'^api/0.2/search/$', 'ui.api.search', name='ui-api-search'),
    
    url(r'^api/0.2/narrator/(?P<oid>[\w]+)/$', 'ui.api.narrator', name='ui-api-narrator'),
    url(r'^api/0.2/narrator/$', 'ui.api.narrator_index', name='ui-api-narrators'),
    
    url(r'^api/0.2/facet/(?P<facet_id>[\w]+)/(?P<term_id>[\d]+)/objects/$', 'ui.api.term_objects', name='ui-api-term-objects'),
    url(r'^api/0.2/facet/(?P<facet_id>[\w]+)/(?P<term_id>[\d]+)/$', 'ui.api.term', name='ui-api-term'),
    url(r'^api/0.2/facet/(?P<facet>[\w]+)/$', 'ui.api.facet', name='ui-api-facet'),
    url(r'^api/0.2/facet/$', 'ui.api.facet_index', name='ui-api-facets'),
    
    url(r'^api/0.2/(?P<oid>[\w\d-]+)/children/$', 'ui.api.object_children', name='ui-api-object-children'),
    url(r'^api/0.2/(?P<oid>[\w\d-]+)/files/$', 'ui.api.object_nodes', name='ui-api-object-nodes'),
    url(r'^api/0.2/(?P<oid>[\w\d-]+)/$', 'ui.api.object_detail', name='ui-api-object'),
    
    url(r'^api/0.2/$', 'ui.api.index', name='ui-api-index'),
    url(r'^api/0.1/$', 'ui.api.index', name='ui-api-index'),
    
    url(r'^about/', TemplateView.as_view(template_name="ui/about.html"), name='ui-about'),
    url(r'^contact/$', TemplateView.as_view(template_name='ui/about.html'), name='ui-contact'),
    url(r'^terms/$', TemplateView.as_view(template_name='ui/terms.html'), name='ui-terms'),
    url(r'^using/$', TemplateView.as_view(template_name='ui/using.html'), name='ui-using'),
    url(r'^ethicalediting/$', TemplateView.as_view(template_name='ui/ethicalediting.html'), name='ui-ethicalediting'),
    
    url(r'^narrators/(?P<oid>[\w]+)/$', 'ui.views.browse.narrator', name='ui-browse-narrator'),
    url(r'^narrators/$', 'ui.views.browse.narrators', name='ui-browse-narrators'),

    url(r'^browse/(?P<facet_id>[\w]+)/(?P<term_id>[\d]+)/$', 'ui.views.browse.term', name='ui-browse-term'),
    url(r'^browse/(?P<facet>[\w]+)/$', 'ui.views.browse.facet', name='ui-browse-facet'),
    url(r'^browse/$', 'ui.views.browse.index', name='ui-browse-index'),
    
    url(r'^search/(?P<field>[\w]+):(?P<term>[\w ,]+)/$', 'ui.views.search.term_query', name='ui-search-term-query'),
    url(r'^search/results/$', 'ui.views.search.results', name='ui-search-results'),
    url(r'^search/$', 'ui.views.search.index', name='ui-search-index'),
    
    url(r'^cite/(?P<model>[\w]+)/(?P<object_id>[\w\d-]+)/$', 'ui.views.cite', name='ui-cite'),
    
    url(r'^collections/$', 'ui.views.collections.list', name='ui-collections-list'),
    
    url(r'^r/(?P<oid>[\w\d-]+)/$', 'ui.views.entities.nodes', name='ui-file-role'),
    
    url(r'^(?P<oid>[\w\d-]+)/objects/$', 'ui.views.objects.children', name='ui-object-children'),
    url(r'^(?P<oid>[\w\d-]+)/files/$', 'ui.views.objects.nodes', name='ui-object-nodes'),
    url(r'^(?P<oid>[\w\d-]+)/', 'ui.views.objects.detail', name='ui-object-detail'),
    
    url(r'^$', 'ui.views.index', name='ui-index'),
)

urlpatterns = format_suffix_patterns(urlpatterns)
