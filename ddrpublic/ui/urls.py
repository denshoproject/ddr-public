from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView

from rest_framework.urlpatterns import format_suffix_patterns

API_BASE = '/api/0.2/'

urlpatterns = patterns(
    '',
    url(r'^redirect/archive.densho.org$', 'ui.views.redirect', name='ui-redirect'),
    url(r'^names', include('names.urls')),
    
    url(r'^api/0.2/choose-tab/$', 'ui.views.choose_tab', name='ui-api-choose-tab'),
    
    url(r'^api/0.2/search/help/', TemplateView.as_view(template_name="ui/search/help.html"), name='ui-about'),
    url(r'^api/0.2/search/$', 'ui.api.search', name='ui-api-search'),
    
    url(r'^api/0.2/narrator/(?P<oid>[\w]+)/interviews/$', 'ui.api.narrator_interviews', name='ui-api-narrator-interviews'),
    url(r'^api/0.2/narrator/(?P<oid>[\w]+)/$', 'ui.api.narrator', name='ui-api-narrator'),
    url(r'^api/0.2/narrator/$', 'ui.api.narrators', name='ui-api-narrators'),
    
    url(r'^api/0.2/facet/(?P<facet_id>[\w]+)/children/$', 'ui.api.facetterms', name='ui-api-facetterms'),
    url(r'^api/0.2/facet/(?P<facet_id>[\w]+)/(?P<term_id>[\w]+)/objects/$', 'ui.api.term_objects', name='ui-api-term-objects'),
    url(r'^api/0.2/facet/(?P<facet_id>[\w]+)/(?P<term_id>[\w]+)/$', 'ui.api.facetterm', name='ui-api-term'),
    url(r'^api/0.2/facet/(?P<facet_id>[\w]+)/$', 'ui.api.facet', name='ui-api-facet'),
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
    
    url(r'^narrators/(?P<oid>[\w]+)/search/$', 'ui.views.search.narrator', name='ui-search-narrator'),
    url(r'^narrators/(?P<oid>[\w]+)/$', 'ui.views.browse.narrator', name='ui-narrators-detail'),
    url(r'^narrators/$', 'ui.views.browse.narrators', name='ui-narrators-list'),
    
    url(r'^browse/(?P<facet_id>[\w]+)/(?P<term_id>[\d]+)/search/$', 'ui.views.search.facetterm', name='ui-search-facetterm'),
    url(r'^browse/(?P<facet_id>[\w]+)/(?P<term_id>[\d]+)/$', 'ui.views.browse.term', name='ui-browse-term'),
    url(r'^browse/(?P<facet_id>[\w]+)/$', 'ui.views.browse.facet', name='ui-browse-facet'),
    url(r'^browse/$', 'ui.views.browse.index', name='ui-browse-index'),
    
    url(r'^search/(?P<field>[\w]+):(?P<term>[\w ,]+)/$', 'ui.views.search.term_query', name='ui-search-term-query'),
    url(r'^search/results/$', 'ui.views.search.results', name='ui-search-results'),
    url(r'^search/$', 'ui.views.search.results', name='ui-search-index'),
    
    url(r'^cite/(?P<model>[\w]+)/(?P<object_id>[\w\d-]+)/$', 'ui.views.cite', name='ui-cite'),
    
    url(r'^collections/$', 'ui.views.collections.list', name='ui-collections-list'),
    
    url(r'^interviews/(?P<oid>[\w\d-]+)/', 'ui.views.entities.interview', name='ui-interview'),
    
    url(r'^r/(?P<oid>[\w\d-]+)/$', 'ui.views.entities.nodes', name='ui-file-role'),
    
    # match legacy urls
    url(r'^(?P<repo>[\w]+)/(?P<org>[\w]+)/(?P<cid>[\d]+)/(?P<eid>[\d]+)/(?P<role>[\w]+)/(?P<sha1>[\w\d]+)/', 'ui.views.objects.legacy', name='ui-legacy'),
    url(r'^(?P<repo>[\w]+)/(?P<org>[\w]+)/(?P<cid>[\d]+)/(?P<eid>[\d]+)/(?P<role>[\w]+)/', 'ui.views.objects.legacy', name='ui-legacy'),
    url(r'^(?P<repo>[\w]+)/(?P<org>[\w]+)/(?P<cid>[\d]+)/(?P<eid>[\d]+)/', 'ui.views.objects.legacy', name='ui-legacy'),
    url(r'^(?P<repo>[\w]+)/(?P<org>[\w]+)/(?P<cid>[\d]+)/', 'ui.views.objects.legacy', name='ui-legacy'),
    
    url(r'^(?P<oid>[\w\d-]+)/search/$', 'ui.views.search.collection', name='ui-search-collection'),
    url(r'^(?P<oid>[\w\d-]+)/objects/$', 'ui.views.objects.children', name='ui-object-children'),
    url(r'^(?P<oid>[\w\d-]+)/files/$', 'ui.views.objects.nodes', name='ui-object-nodes'),
    url(r'^(?P<oid>[\w\d-]+)/', 'ui.views.objects.detail', name='ui-object-detail'),
    
    url(r'^$', 'ui.views.index', name='ui-index'),
)

handler400 = 'ui.views.error400'
handler403 = 'ui.views.error403'
handler404 = 'ui.views.error404'
handler500 = 'ui.views.error500'

urlpatterns = format_suffix_patterns(urlpatterns)
