from django.conf.urls import include, url

from names import views

urlpatterns = [
    url(r"^search/$", views.search_ui, name='names-search'),
    url(r"^(?P<id>[\w\W]+)/$", views.detail, name='names-detail'),
    url(r"^$", views.search_ui, name='names-index'),
]
