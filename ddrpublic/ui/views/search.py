from datetime import datetime
import logging
logger = logging.getLogger(__name__)

from dateutil import parser

from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import Http404, get_object_or_404, render_to_response
from django.template import RequestContext
from django.utils.http import urlquote  as django_urlquote

from DDR import elasticsearch
from ui import models


# helpers --------------------------------------------------------------


# views ----------------------------------------------------------------

def index( request ):
    return render_to_response(
        'ui/search/index.html',
        {},
        context_instance=RequestContext(request, processors=[])
    )

def results( request ):
    """Results of a search query.
    """
    # prep query for elasticsearch
    model = request.GET.get('model', None)
    q = django_urlquote(request.GET.get('query', ''))
    #filters = {'public': request.GET.get('public', ''),
    #           'status': request.GET.get('status', ''),}
    filters = {}
    sort = {'record_created': request.GET.get('record_created', ''),
            'record_lastmod': request.GET.get('record_lastmod', ''),}
    # do the query
    results = elasticsearch.query(settings.ELASTICSEARCH_HOST_PORT, settings.DOCUMENT_INDEX, query=q, filters=filters, sort=sort)
    hits = models.massage_query_results(results)
    return render_to_response(
        'ui/search/results.html',
        {'hits': hits,
         'query': q,
         'filters': filters,
         'sort': sort,},
        context_instance=RequestContext(request, processors=[])
    )

def term_query( request, field, term ):
    """Results of a search query.
    """
    # prep query for elasticsearch
    terms = {field:term}
    filters = {}
    sort = {'record_created': request.GET.get('record_created', ''),
            'record_lastmod': request.GET.get('record_lastmod', ''),}
    # do the query
    results = elasticsearch.query(settings.ELASTICSEARCH_HOST_PORT, settings.DOCUMENT_INDEX, term=terms, filters=filters, sort=sort)
    hits = models.massage_query_results(results)
    return render_to_response(
        'ui/search/results.html',
        {'hits': hits,
         'filters': filters,
         'sort': sort,},
        context_instance=RequestContext(request, processors=[])
    )
