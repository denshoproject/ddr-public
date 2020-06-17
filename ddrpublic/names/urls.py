from django.urls import include, path, re_path

from . import api
from . import views


urlpatterns = [
    re_path(r'^api/0.2/names/(?P<object_id>[0-9a-zA-Z_:-]+)',
            api.name, name='names-api-name'
    ),
    path('api/0.2/names', api.Search.as_view(), name='names-api-search'),
    
    path('search/', views.search_ui, name='names-search'),
    re_path(r'^(?P<object_id>[0-9a-zA-Z_:-]+)',
            views.detail, name='names-detail'
    ),
    path('', views.search_ui, name='names-index'),
]
