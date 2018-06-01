from django.conf.urls import include, url
from django.views.generic import TemplateView

from rest_framework.urlpatterns import format_suffix_patterns

from . import api
from views import browse, search, searching, collections, entities, objects, index
from views import cite, choose_tab, redirect, index

API_BASE = '/api/0.2/'

urlpatterns = [
    url(r'^redirect/archive.densho.org$', redirect, name='ui-redirect'),
    url(r'^names', include('names.urls')),
    
    url(r'^api/0.2/choose-tab/$', choose_tab, name='ui-api-choose-tab'),
    
    url(r'^api/0.2/search/help/', TemplateView.as_view(template_name="ui/search/help.html"), name='ui-about'),
    url(r'^api/0.2/search/$', api.search, name='ui-api-search'),
    
    url(r'^api/0.2/narrator/(?P<oid>[\w]+)/interviews/$', api.narrator_interviews, name='ui-api-narrator-interviews'),
    url(r'^api/0.2/narrator/(?P<oid>[\w]+)/$', api.narrator, name='ui-api-narrator'),
    url(r'^api/0.2/narrator/$', api.narrators, name='ui-api-narrators'),
    
    url(r'^api/0.2/facet/(?P<facet_id>[\w]+)/children/$', api.facetterms, name='ui-api-facetterms'),
    url(r'^api/0.2/facet/(?P<facet_id>[\w]+)/(?P<term_id>[\w]+)/objects/$', api.term_objects, name='ui-api-term-objects'),
    url(r'^api/0.2/facet/(?P<facet_id>[\w]+)/(?P<term_id>[\w]+)/$', api.facetterm, name='ui-api-term'),
    url(r'^api/0.2/facet/(?P<facet_id>[\w]+)/$', api.facet, name='ui-api-facet'),
    url(r'^api/0.2/facet/$', api.facet_index, name='ui-api-facets'),
    
    url(r'^api/0.2/(?P<oid>[\w\d-]+)/children/$', api.object_children, name='ui-api-object-children'),
    url(r'^api/0.2/(?P<oid>[\w\d-]+)/files/$', api.object_nodes, name='ui-api-object-nodes'),
    url(r'^api/0.2/(?P<oid>[\w\d-]+)/$', api.object_detail, name='ui-api-object'),
    
    url(r'^api/0.2/$', api.index, name='ui-api-index'),
    url(r'^api/0.1/$', api.index, name='ui-api-index'),
    
    url(r'^about/', TemplateView.as_view(template_name="ui/about.html"), name='ui-about'),
    url(r'^contact/$', TemplateView.as_view(template_name='ui/about.html'), name='ui-contact'),
    url(r'^terms/$', TemplateView.as_view(template_name='ui/terms.html'), name='ui-terms'),
    url(r'^using/$', TemplateView.as_view(template_name='ui/using.html'), name='ui-using'),
    url(r'^ethicalediting/$', TemplateView.as_view(template_name='ui/ethicalediting.html'), name='ui-ethicalediting'),
    
    url(r'^narrators/(?P<oid>[\w]+)/search/$', search.narrator, name='ui-search-narrator'),
    url(r'^narrators/(?P<oid>[\w]+)/$', browse.narrator, name='ui-narrators-detail'),
    url(r'^narrators/$', browse.narrators, name='ui-narrators-list'),
    
    url(r'^browse/(?P<facet_id>[\w]+)/(?P<term_id>[\w]+)/search/$', search.facetterm, name='ui-search-facetterm'),
    url(r'^browse/(?P<facet_id>[\w]+)/(?P<term_id>[\w]+)/$', browse.term, name='ui-browse-term'),
    url(r'^browse/(?P<facet_id>[\w]+)/$', browse.facet, name='ui-browse-facet'),
    url(r'^browse/$', browse.index, name='ui-browse-index'),
    
    url(r'^search/(?P<field>[\w]+):(?P<term>[\w ,]+)/$', search.term_query, name='ui-search-term-query'),
    url(r'^search/results/$', searching.search_ui, name='ui-search-results'),
    url(r'^search/$', searching.search_ui, name='ui-search-index'),
    
    url(r'^cite/(?P<model>[\w]+)/(?P<object_id>[\w\d-]+)/$', cite, name='ui-cite'),
    
    url(r'^collections/$', collections.list, name='ui-collections-list'),
    
    url(r'^interviews/(?P<oid>[\w\d-]+)/', entities.interview, name='ui-interview'),
    
    url(r'^r/(?P<oid>[\w\d-]+)/$', entities.nodes, name='ui-file-role'),
    
    # match legacy urls
    url(r'^(?P<repo>[\w]+)/(?P<org>[\w]+)/(?P<cid>[\d]+)/(?P<eid>[\d]+)/(?P<role>[\w]+)/(?P<sha1>[\w\d]+)/', objects.legacy, name='ui-legacy'),
    url(r'^(?P<repo>[\w]+)/(?P<org>[\w]+)/(?P<cid>[\d]+)/(?P<eid>[\d]+)/(?P<role>[\w]+)/', objects.legacy, name='ui-legacy'),
    url(r'^(?P<repo>[\w]+)/(?P<org>[\w]+)/(?P<cid>[\d]+)/(?P<eid>[\d]+)/', objects.legacy, name='ui-legacy'),
    url(r'^(?P<repo>[\w]+)/(?P<org>[\w]+)/(?P<cid>[\d]+)/', objects.legacy, name='ui-legacy'),
    
    url(r'^(?P<oid>[\w\d-]+)/search/$', search.collection, name='ui-search-collection'),
    url(r'^(?P<oid>[\w\d-]+)/objects/$', objects.children, name='ui-object-children'),
    url(r'^(?P<oid>[\w\d-]+)/files/$', objects.nodes, name='ui-object-nodes'),
    url(r'^(?P<oid>[\w\d-]+)/', objects.detail, name='ui-object-detail'),
    
    url(r'^$', index, name='ui-index'),
]

handler400 = 'ui.views.error400'
handler403 = 'ui.views.error403'
handler404 = 'ui.views.error404'
handler500 = 'ui.views.error500'

urlpatterns = format_suffix_patterns(urlpatterns)
