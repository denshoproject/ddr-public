from django.urls import include, path
from django.views.generic import TemplateView

from drf_yasg import views as yasg_views
from drf_yasg import openapi
from rest_framework import permissions
from rest_framework.urlpatterns import format_suffix_patterns

from names import api as names_api
from . import api
from .views import browse, searching, collections, entities, objects, index
from .views import cite, ui_state, redirect, index

API_BASE = '/api/0.2/'

schema_view = yasg_views.get_schema_view(
   openapi.Info(
      title="Densho Digital Repository API",
      default_version='0.2',
      #description="DESCRIPTION TEXT HERE",
      terms_of_service="http://ddr.densho.org/terms/",
      contact=openapi.Contact(email="info@densho.org"),
      #license=openapi.License(name="TBD"),
   ),
   #validators=['flex', 'ssv'],
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('redirect/archive.densho.org', redirect, name='ui-redirect'),
    path('names/', include('names.urls')),
    
    path('api/swagger.json',
         schema_view.without_ui(cache_timeout=0), name='schema-json'
    ),
    path('api/swagger.yaml',
         schema_view.without_ui(cache_timeout=0), name='schema-yaml'
    ),
    path('api/swagger/',
         schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'
    ),
    path('api/redoc/',
         schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'
    ),
    
    path('api/0.2/ui-state/', ui_state, name='ui-api-state'),
    
    path('api/search/help/',
         TemplateView.as_view(template_name="ui/search/help.html"), name='ui-api-search-help'
    ),
    path('api/0.2/search/', api.Search.as_view(), name='ui-api-search'),
    
    path('api/0.2/names/<slug:object_id>/', names_api.name, name='names-api-name'),
    path('api/0.2/names', names_api.Search.as_view(), name='names-api-search'),
    
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
    
    path('<slug:oid>/', entities.nodes, name='ui-file-role'),
    
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
