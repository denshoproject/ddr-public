import json

from django.conf import settings
from django.core.cache import cache
from django.core.urlresolvers import reverse

from DDR import elasticsearch

CACHE_TIMEOUT = 30

def facets_list():
    """Returns a list of facets in alphabetical order, with URLs
    """
    key = 'facets:list'
    cached = cache.get(key)
    if not cached:
        facets_list = []
        for name in elasticsearch.list_facets():
            raw = elasticsearch.get(settings.ELASTICSEARCH_HOST_PORT,
                                    index=settings.METADATA_INDEX, model='facet', id=name)
            f = json.loads(raw['response'])['_source']
            f['name'] = name
            f['url'] = reverse('ui-browse-facet', args=[name])
            facets_list.append(f)
        cached = facets_list
        cache.set(key, cached, CACHE_TIMEOUT)
    return cached

def get_facet(name):
    key = 'facets:%s' % name
    print(key)
    cached = cache.get(key)
    print('cached: %s' % cached)
    if not cached:
        for f in facets_list():
            if f['name'] == name:
                cached = f
                cache.set(key, cached, CACHE_TIMEOUT)
    return cached

def facet_terms(facet):
    """
    If term is precoordinate all the terms are listed, with count of number of occurances (if any).
    If term is postcoordinate, all the terms come from the index, but there is not title/description.
    """
    facet_terms = []
    results = elasticsearch.facet_terms(settings.ELASTICSEARCH_HOST_PORT,
                                        settings.DOCUMENT_INDEX, facet['name'], order='term')
    if facet.get('terms', []):
        # precoordinate
        term_counts = {}
        for t in results['terms']:
            term_counts[t['term']] = t['count']
        # add counts to terms
        for term in facet['terms']:
            t = {'term':term[0], 'title':term[1], 'description':term[2]}
            t['count'] = term_counts.get(t['term'], None)
            facet_terms.append(t)
    else:
        # postcoordinate
        for t in results['terms']:
            t['title'] = t['term']
            t['description'] = ''
            facet_terms.append(t)
    return facet_terms
