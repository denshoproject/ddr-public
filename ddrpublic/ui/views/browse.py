import logging
logger = logging.getLogger(__name__)

from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import Http404, get_object_or_404, render_to_response
from django.template import RequestContext

from DDR import elasticsearch


def facets_list():
    """Returns a list of facets in alphabetical order, with URLs
    """
    facets_list = []
    facets = elasticsearch.load_facets('/usr/local/src/ddr-cmdln/ddr/DDR/models/facets.json')
    names = facets.keys()
    names.sort()
    for name in names:
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


# views ----------------------------------------------------------------

def index( request ):
    return render_to_response(
        'ui/browse/index.html',
        {
            'facets': facets_list(),
        },
        context_instance=RequestContext(request, processors=[])
    )

def facet( request, facet ):
    facet_name = facet
    facets = facets_list()
    facet = get_facet(facets, facet_name)
    terms = facet_terms(facet)
    return render_to_response(
        'ui/browse/facet.html',
        {
            'facet': facet,
            'terms': terms,
            'facets': facets,
        },
        context_instance=RequestContext(request, processors=[])
    )
