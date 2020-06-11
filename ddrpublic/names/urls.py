from django.urls import include, path

from names import views

urlpatterns = [
    path('search/', views.search_ui, name='names-search'),
    path('<slug:id>/', views.detail, name='names-detail'),
    path('', views.search_ui, name='names-index'),
]
