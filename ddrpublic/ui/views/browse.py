import logging
logger = logging.getLogger(__name__)

from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import Http404, get_object_or_404, render_to_response
from django.template import RequestContext

from ui import domain_org
from ui import faceting
from ui import models

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

def term( request, facet_id, term_id ):
    term = faceting.Term(facet_id=facet_id, term_id=term_id)
    # prep query for elasticsearch
    terms = {facet_id:term_id}
    facet = faceting.get_facet(facet_id)
    for t in facet['terms']:
        if t['id'] == term:
            try:
                terms_display['term'] = t['title_display']
            except:
                terms_display['term'] = t['title']
            break
    # filter by partner
    filters = {}
    repo,org = domain_org(request)
    if repo and org:
        filters['repo'] = repo
        filters['org'] = org
    fields = models.all_list_fields()
    sort = {'record_created': request.GET.get('record_created', ''),
            'record_lastmod': request.GET.get('record_lastmod', ''),}
    # do the query
    results = models.cached_query(settings.DOCSTORE_HOSTS, settings.DOCSTORE_INDEX,
                                  terms=terms, filters=filters,
                                  fields=fields, sort=sort)
    thispage = request.GET.get('page', 1)
    objects = models.process_query_results(results, thispage, settings.RESULTS_PER_PAGE)
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
