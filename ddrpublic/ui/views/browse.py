import logging
logger = logging.getLogger(__name__)
import os
import urlparse

from django.conf import settings
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import Http404, get_object_or_404, render_to_response
from django.template import RequestContext
from django.views.decorators.cache import cache_page

from ui import domain_org
from ui import encyc
from ui import faceting
from ui import models

SHOW_THESE = ['topics', 'facility', 'location', 'format', 'genre',]


# views ----------------------------------------------------------------

@cache_page(settings.CACHE_TIMEOUT)
def index( request ):
    return render_to_response(
        'ui/browse/index.html',
        {
        },
        context_instance=RequestContext(request, processors=[])
    )

@cache_page(settings.CACHE_TIMEOUT)
def narrators(request):
    thispage = int(request.GET.get('page', 1))
    pagesize = settings.RESULTS_PER_PAGE
    offset = models.search_offset(thispage, pagesize)
    paginator = Paginator(
        models.pad_results(
            models.Narrator.narrators(
                request,
                limit=pagesize,
                offset=offset,
            ),
            pagesize,
            thispage
        ),
        pagesize
    )
    return render_to_response(
        'ui/narrators/list.html',
        {
            'paginator': paginator,
            'page': paginator.page(thispage),
            'thispage': thispage,
            'api_url': reverse('ui-api-narrators'),
        },
        context_instance=RequestContext(request, processors=[])
    )

@cache_page(settings.CACHE_TIMEOUT)
def narrator(request, oid):
    return render_to_response(
        'ui/narrators/detail.html',
        {
            'narrator': models.Narrator.get(oid, request),
            'interviews': models.Narrator.interviews(oid, request, limit=1000),
            'api_url': reverse('ui-api-narrator', args=[oid]),
        },
        context_instance=RequestContext(request, processors=[])
    )

@cache_page(settings.CACHE_TIMEOUT)
def facet(request, facet_id):
    if facet_id == 'topics':
        template_name = 'ui/facets/facet-topics.html'
        terms = models.Facet.topics_terms(request)
        
    elif facet_id == 'facility':
        template_name = 'ui/facets/facet-facility.html'
        # for some reason ES does not sort
        terms = models.Facet.facility_terms(request)
    
    return render_to_response(
        template_name,
        {
            'facet': models.Facet.get(facet_id, request),
            'terms': terms,
            'api_url': reverse('ui-api-facetterms', args=[facet_id]),
        },
        context_instance=RequestContext(request, processors=[])
    )

@cache_page(settings.CACHE_TIMEOUT)
def term( request, facet_id, term_id ):
    oid = '-'.join([facet_id, term_id])
    template_name = 'ui/facets/term-%s.html' % facet_id
    facet = models.Facet.get(facet_id, request)
    term = models.Term.get(oid, request)
    
    # terms tree (topics)
    if facet_id == 'topics':
        term['tree'] = [
            t for t in models.Facet.topics_terms(request)
            if (t['id'] in term['ancestors']) # ancestors of current term
            or (t['id'] == term['id'])        # current term
            or (term['id'] in t['ancestors']) # children of current term
        ]
    
    # API urls for elinks
    for item in term.get('elinks', []):
        try:
            url = urlparse.urlparse(item['url'])
            item['api_url'] = item['url'].replace(
                url.path,
                '/api/0.1%s' % url.path
            )
        except:
            pass
    # add titles to encyclopedia urls on topics
    # facilities elinks already have titles
    if term.get('encyc_urls'):
        # topics
        term['encyc_urls'] = [
            encyc.article_url_title(url)
            for url in term['encyc_urls']
        ]
    
    # term objects
    thispage = int(request.GET.get('page', 1))
    pagesize = settings.RESULTS_PER_PAGE
    offset = models.search_offset(thispage, pagesize)
    
    paginator = Paginator(
        models.pad_results(
            models.Term.objects(
                facet_id, term_id,
                limit=pagesize,
                offset=offset,
                request=request,
            ),
            pagesize,
            thispage
        ),
        pagesize
    )
    return render_to_response(
        template_name,
        {
            'facet': facet,
            'term': term,
            'paginator': paginator,
            'page': paginator.page(thispage),
            'api_url': reverse('ui-api-term', args=[facet['id'], term['id']]),
        },
        context_instance=RequestContext(request, processors=[])
    )
