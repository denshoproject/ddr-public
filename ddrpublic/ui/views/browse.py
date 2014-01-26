import logging
logger = logging.getLogger(__name__)

from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import Http404, get_object_or_404, render_to_response
from django.template import RequestContext

from DDR import elasticsearch


# views ----------------------------------------------------------------

def index( request ):
    return render_to_response(
        'ui/browse/index.html',
        {},
        context_instance=RequestContext(request, processors=[])
    )

def facet( request, facet ):
    results = elasticsearch.facet_terms(settings.ELASTICSEARCH_HOST_PORT, 'ddr', facet, order='term')
    return render_to_response(
        'ui/browse/facet.html',
        {
            'facet': facet,
            'results': results,
        },
        context_instance=RequestContext(request, processors=[])
    )
