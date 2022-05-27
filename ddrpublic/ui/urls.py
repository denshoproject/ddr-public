from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.views.generic import TemplateView

from rest_framework import permissions
from rest_framework.schemas import get_schema_view
from rest_framework.urlpatterns import format_suffix_patterns
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from . import api
from . import sitemaps
from .views import browse, searching, collections, entities, objects, index
from .views import cite, ui_state, redirect, index

SITEMAPS = {
    'collections': sitemaps.CollectionSitemap,
}

API_BASE = '/api/0.2/'

urlpatterns = [
    
    path('robots.txt', include('robots.urls')),
    path('sitemap.xml', sitemap, {'sitemaps': SITEMAPS}, name='ui-sitemap'),
    
    path('redirect/archive.densho.org', redirect, name='ui-redirect'),
    path('names/', include('names.urls')),

    path('api/openapi', get_schema_view(
        title="Densho Digital Repository",
        description="Longer descriptive text",
        version="1.0.0",
    ), name='openapi-schema'),

    path('api/schema/', SpectacularAPIView.as_view(), name="schema"),
    path(
        'api/docs/',
        SpectacularSwaggerView.as_view(
            template_name="swagger-ui.html", url_name="schema"
        ),
        name="swagger-ui",
    ),
    
    path('api/0.2/ui-state/', ui_state, name='ui-api-state'),
    
    path('api/search/help/',
         TemplateView.as_view(template_name="ui/search/help.html"), name='ui-api-search-help'
    ),
    path('api/0.2/search/', api.Search.as_view(), name='ui-api-search'),
    
    path('api/0.2/narrator/<slug:object_id>/interviews/', api.narrator_interviews, name='ui-api-narrator-interviews'),
    path('api/0.2/narrator/<slug:object_id>/', api.narrator, name='ui-api-narrator'),
    path('api/0.2/narrator/', api.narrators, name='ui-api-narrators'),
    
    path('api/0.2/facet/<slug:facet_id>/children/', api.facetterms, name='ui-api-facetterms'),
    path('api/0.2/facet/<slug:facet_id>/<slug:term_id>/objects/', api.term_objects, name='ui-api-term-objects'),
    path('api/0.2/facet/<slug:facet_id>/<slug:term_id>/', api.facetterm, name='ui-api-term'),
    path('api/0.2/facet/<slug:facet_id>/', api.facet, name='ui-api-facet'),
    path('api/0.2/facet/', api.facet_index, name='ui-api-facets'),
    
    path('api/0.2/<slug:object_id>/children/', api.object_children, name='ui-api-object-children'),
    path('api/0.2/<slug:object_id>/files/', api.object_nodes, name='ui-api-object-nodes'),
    path('api/0.2/<slug:object_id>/', api.object_detail, name='ui-api-object'),
    
    path('api/0.2/', api.index, name='ui-api-index'),
    path('api/0.1/', api.index, name='ui-api-index'),
    path('api/', api.index, name='ui-api-index'),
    
    path('about/', TemplateView.as_view(template_name="ui/about.html"), name='ui-about'),
    path('contact/', TemplateView.as_view(template_name='ui/about.html'), name='ui-contact'),
    path('terms/', TemplateView.as_view(template_name='ui/terms.html'), name='ui-terms'),
    path('using/', TemplateView.as_view(template_name='ui/using.html'), name='ui-using'),
    path('ethicalediting/', TemplateView.as_view(template_name='ui/ethicalediting.html'), name='ui-ethicalediting'),
    
    path('narrators/<slug:oid>/search/', searching.narrator, name='ui-search-narrator'),
    path('narrators/<slug:oid>/', browse.narrator, name='ui-narrators-detail'),
    path('narrators/', browse.narrators, name='ui-narrators-list'),
    
    path('browse/<slug:facet_id>/<slug:term_id>/search/', searching.facetterm, name='ui-search-facetterm'),
    path('browse/<slug:facet_id>/<slug:term_id>/', browse.term, name='ui-browse-term'),
    path('browse/<slug:facet_id>/', browse.facet, name='ui-browse-facet'),
    path('browse/', browse.index, name='ui-browse-index'),
    
    path('search/results/', searching.search_ui, name='ui-search-results'),
    path('search/', searching.search_ui, name='ui-search-index'),
    
    path('cite/<slug:model>/<slug:object_id>/', cite, name='ui-cite'),
    
    path('collections/', collections.list, name='ui-collections-list'),
    
    path('interviews/<slug:oid>/', entities.interview, name='ui-interview'),
    
    # match legacy urls
    path('<slug:repo>/<slug:org>/<slug:cid>/<slug:eid>/<slug:role>/<slug:sha1>/', objects.legacy, name='ui-legacy'),
    path('<slug:repo>/<slug:org>/<slug:cid>/<slug:eid>/<slug:role>/', objects.legacy, name='ui-legacy'),
    path('<slug:repo>/<slug:org>/<slug:cid>/<slug:eid>', objects.legacy, name='ui-legacy'),
    path('<slug:repo>/<slug:org>/<slug:cid>/', objects.legacy, name='ui-legacy'),
    
    path('<slug:oid>/search/', searching.collection, name='ui-search-collection'),
    path('<slug:oid>/objects/', objects.children, name='ui-object-children'),
    path('<slug:oid>/files/', objects.nodes, name='ui-object-nodes'),
    path('<slug:oid>/', objects.detail, name='ui-object-detail'),
    
    path('', index, name='ui-index'),
]

handler400 = 'ui.views.handler400'
handler403 = 'ui.views.handler403'
handler404 = 'ui.views.handler404'
handler500 = 'ui.views.handler500'

urlpatterns = format_suffix_patterns(urlpatterns)
