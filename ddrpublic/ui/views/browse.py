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
from ui import api

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
    paginator = Paginator(
        api.pad_results(
            api.ApiNarrator.api_list(
                request,
                limit=pagesize,
                offset=pagesize*thispage
            ),
            pagesize,
            thispage
        ),
        pagesize
    )
    return render_to_response(
        'ui/browse/narrators.html',
        {
            'paginator': paginator,
            'page': paginator.page(thispage),
            'thispage': thispage,
            'tab': request.GET.get('tab', 'gallery'),
        },
        context_instance=RequestContext(request, processors=[])
    )

@cache_page(settings.CACHE_TIMEOUT)
def narrator(request, oid):
    return render_to_response(
        'ui/browse/narrator-detail.html',
        {
            'narrator': api.ApiNarrator.api_get(oid, request),
            'interviews': api.ApiNarrator.interviews(oid, request, limit=1000),
            'api_url': reverse('ui-api-narrator', args=[oid]),
        },
        context_instance=RequestContext(request, processors=[])
    )

@cache_page(settings.CACHE_TIMEOUT)
def facet(request, facet_id):
    if facet_id == 'topics':
        template_name = 'ui/browse/facet-topics.html'
        terms = api.ApiFacet.topics_terms(request)
        
    elif facet_id == 'facility':
        template_name = 'ui/browse/facet-facility.html'
        # for some reason ES does not sort
        terms = api.ApiFacet.facility_terms(request)
    
    return render_to_response(
        template_name,
        {
            'facet': api.ApiFacet.api_get(facet_id, request),
            'terms': terms,
        },
        context_instance=RequestContext(request, processors=[])
    )

@cache_page(settings.CACHE_TIMEOUT)
def term( request, facet_id, term_id ):
    oid = '-'.join([facet_id, term_id])
    template_name = 'ui/browse/term-%s.html' % facet_id
    facet = api.ApiFacet.api_get(facet_id, request)
    term = api.ApiTerm.api_get(oid, request)
    
    # terms tree (topics)
    if facet_id == 'topics':
        term['tree'] = [
            t for t in api.ApiFacet.topics_terms(request)
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
    paginator = Paginator(
        api.pad_results(
            api.ApiTerm.objects(
                facet_id, term_id,
                limit=pagesize,
                offset=thispage,
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
