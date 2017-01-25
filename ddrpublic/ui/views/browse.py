import logging
logger = logging.getLogger(__name__)

from django.conf import settings
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import Http404, get_object_or_404, render_to_response
from django.template import RequestContext

from ui import domain_org
from ui import faceting
from ui import models
from ui import api

SHOW_THESE = ['topics', 'facility', 'location', 'format', 'genre',]


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

def narrators(request):
    thispage = int(request.GET.get('page', 1))
    pagesize = settings.RESULTS_PER_PAGE

    results = api.ApiNarrator.api_list(
        request,
        limit=pagesize,
        offset=pagesize*thispage
    )
    objects = api.pad_results(results, pagesize, thispage)
    paginator = Paginator(objects, pagesize)
    page = paginator.page(thispage)
    return render_to_response(
        'ui/browse/narrators.html',
        {
            'paginator': paginator,
            'page': page,
        },
        context_instance=RequestContext(request, processors=[])
    )

def narrator(request, oid):
    return render_to_response(
        'ui/browse/narrator-detail.html',
        {
            'narrator': api.ApiNarrator.api_get(oid, request),
        },
        context_instance=RequestContext(request, processors=[])
    )

def facet( request, facet ):
    facet = faceting.Facet(facet)
    terms = facet.tree()
    return render_to_response(
        'ui/browse/facet.html',
        {
            'facet': facet,
            'terms': terms,
        },
        context_instance=RequestContext(request, processors=[])
    )

def term( request, facet_id, term_id ):
    thispage = int(request.GET.get('page', 1))
    pagesize = settings.RESULTS_PER_PAGE
    
    term = api.ApiTerm(facet_id=facet_id, term_id=term_id)
    results = term.objects(
        limit=pagesize,
        offset=thispage,
        request=request,
    )
    objects = api.pad_results(results, pagesize, thispage)
    paginator = Paginator(objects, settings.RESULTS_PER_PAGE)
    page = paginator.page(request.GET.get('page', 1))
    return render_to_response(
        'ui/browse/term.html',
        {
            'term': term,
            'paginator': paginator,
            'page': page,
        },
        context_instance=RequestContext(request, processors=[])
    )
