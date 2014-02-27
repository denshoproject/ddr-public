import json
import re

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
    cached = cache.get(key)
    if not cached:
        for f in facets_list():
            if f['name'] == name:
                cached = f
                cache.set(key, cached, CACHE_TIMEOUT)
    return cached

INT_IN_STRING = re.compile(r'^\d+$')

def extract_term_id( text ):
    """
    >>> extract_term_id('Manzanar [7]')
    '7'
    >>> extract_term_id('[7]')
    '7'
    >>> extract_term_id('7')
    '7'
    >>> extract_term_id(7)
    '7'
    """
    if ('[' in text) and (']' in text):
        term_id = text.split('[')[1].split(']')[0]
    elif re.match(INT_IN_STRING, text):
        term_id = text
    else:
        term_id = text
    return term_id

def facet_terms(facet):
    """
    If term is precoordinate all the terms are listed, with count of number of occurances (if any).
    If term is postcoordinate, all the terms come from the index, but there is not title/description.
    """
    facetterms = []
    results = elasticsearch.facet_terms(settings.ELASTICSEARCH_HOST_PORT,
                                        settings.DOCUMENT_INDEX, facet['name'], order='term')
    if facet.get('terms', []):
        # precoordinate
        # IMPORTANT: topics and facility term IDs are int. All others are str.
        term_counts = {}
        for t in results['terms']:
            term_id = extract_term_id(t['term'])
            term_count = t['count']
            if term_id and term_count:
                term_counts[term_id] = term_count
        # make URLs for terms
        for term in facet['terms']:
            term['url'] = reverse('ui-search-term-query', args=(facet['id'], term['id']))
        # add counts to terms
        for term in facet['terms']:
            term_id = term['id']
            if isinstance(term_id, int):
                term_id = str(term_id)
            term['count'] = term_counts.get(term_id, 0)
            facetterms.append(term)
    else:
        # postcoordinate
        for t in results['terms']:
            t['title'] = t['term']
            t['description'] = ''
            t['url'] = '/search/%s:%s/' % (facet['id'], t['term'])
            facetterms.append(t)
    return facetterms
