import logging
logger = logging.getLogger(__name__)

from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import Http404, get_object_or_404, render_to_response
from django.template import RequestContext

from DDR import elasticsearch

from ui import faceting

SHOW_THESE = ['topic', 'facility', 'location', 'format', 'genre',]


# views ----------------------------------------------------------------

def index( request ):
    facets = [faceting.get_facet(name) for name in SHOW_THESE]
    return render_to_response(
        'ui/browse/index.html',
        {
            'facets': facets,
        },
        context_instance=RequestContext(request, processors=[])
    )

def facet( request, facet ):
    facet = faceting.get_facet(facet)
    terms = faceting.facet_terms(facet)
    return render_to_response(
        'ui/browse/facet.html',
        {
            'facet': facet,
            'facet_terms': terms,
        },
        context_instance=RequestContext(request, processors=[])
    )
