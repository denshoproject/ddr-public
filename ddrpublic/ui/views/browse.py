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



# views ----------------------------------------------------------------

def index( request ):
    return render_to_response(
        'ui/browse/index.html',
        {
            'facets': faceting.facets_list(),
        },
        context_instance=RequestContext(request, processors=[])
    )

def facet( request, facet ):
    facet_name = facet
    facets = faceting.facets_list()
    facet = faceting.get_facet(facets, facet_name)
    terms = faceting.facet_terms(facet)
    return render_to_response(
        'ui/browse/facet.html',
        {
            'facet': facet,
            'terms': terms,
            'facets': facets,
        },
        context_instance=RequestContext(request, processors=[])
    )
