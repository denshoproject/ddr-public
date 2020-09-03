from datetime import datetime

from django.conf import settings
from django.contrib.sitemaps import Sitemap
from rest_framework.reverse import reverse

from . import models


class Item(object):
    location = ''
    timestamp = None
    
    def unicode(self):
        self.title
    
    def get_absolute_url(self):
        return self.location


class CollectionSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8
    
    def items(self):
        items = []
        orgs = models.Repository.children('ddr', request=None) # TODO HARDCODED
        SEARCH_INCLUDE_FIELDS = ['id', 'title', 'record_lastmod']
        for org in orgs.objects:
            collections = models.Organization.children(
                org.id, request=None,
                fields=SEARCH_INCLUDE_FIELDS,
                limit=settings.ELASTICSEARCH_MAX_SIZE,
            )
            for o in collections.objects:
                item = Item()
                item.title = o.title
                item.location = reverse('ui-object-detail', [o.id])
                item.timestamp = datetime.fromisoformat(o.record_lastmod)
                items.append(item)
        return items
    
    def lastmod(self, obj):
        return obj.timestamp
