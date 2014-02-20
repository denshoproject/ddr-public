from django.conf import settings
from django.core.urlresolvers import reverse

from DDR import elasticsearch

SHOW_THESE = ['topics', 'facility', 'location', 'format', 'genre',]


def facets_list():
    """Returns a list of facets in alphabetical order, with URLs
    """
    facets_list = []
    facets = elasticsearch.load_facets('/usr/local/src/ddr-cmdln/ddr/DDR/models/facets.json')
    names = facets.keys()
    #names.sort()
    #for name in names:
    for name in SHOW_THESE:
        f = facets[name]
        f['name'] = name
        f['url'] = reverse('ui-browse-facet', args=[name])
        facets_list.append(f)
    return facets_list

def get_facet(facets, name):
    for f in facets:
        if f['name'] == name:
            return f
    return None

def facet_terms(facet):
    """
    If term is precoordinate all the terms are listed, with count of number of occurances (if any).
    If term is postcoordinate, all the terms come from the index, but there is not title/description.
    """
    facet_terms = []
    results = elasticsearch.facet_terms(settings.ELASTICSEARCH_HOST_PORT, settings.DOCUMENT_INDEX, facet['name'], order='term')
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
