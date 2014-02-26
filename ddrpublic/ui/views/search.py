from datetime import datetime
import logging
logger = logging.getLogger(__name__)

from dateutil import parser

from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
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
    filters = {}
    fields = models.all_list_fields()
    sort = {'record_created': request.GET.get('record_created', ''),
            'record_lastmod': request.GET.get('record_lastmod', ''),}
    # do the query
    results = elasticsearch.query(settings.ELASTICSEARCH_HOST_PORT, settings.DOCUMENT_INDEX,
                                  query=q, filters=filters,
                                  fields=fields, sort=sort)
    hits = models.massage_query_results(results)
    paginator = Paginator(hits, settings.RESULTS_PER_PAGE)
    page = paginator.page(request.GET.get('page', 1))
    return render_to_response(
        'ui/search/results.html',
        {'paginator': paginator,
         'page': page,
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
    fields = models.all_list_fields()
    sort = {'record_created': request.GET.get('record_created', ''),
            'record_lastmod': request.GET.get('record_lastmod', ''),}
    # do the query
    results = elasticsearch.query(settings.ELASTICSEARCH_HOST_PORT, settings.DOCUMENT_INDEX,
                                  term=terms, filters=filters,
                                  fields=fields, sort=sort)
    hits = models.massage_query_results(results)
    paginator = Paginator(hits, settings.RESULTS_PER_PAGE)
    page = paginator.page(request.GET.get('page', 1))
    return render_to_response(
        'ui/search/results.html',
        {'paginator': paginator,
         'page': page,
         'terms': terms,
         'filters': filters,
         'sort': sort,},
        context_instance=RequestContext(request, processors=[])
    )
