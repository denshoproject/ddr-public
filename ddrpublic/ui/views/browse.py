import logging
logger = logging.getLogger(__name__)

from django.conf import settings
from django.core.cache import cache
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
    return render_to_response(
        'ui/browse/index.html',
        {
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
            'thispage': thispage,
            'tab': request.GET.get('tab', 'gallery'),
        },
        context_instance=RequestContext(request, processors=[])
    )

def narrator(request, oid):
    return render_to_response(
        'ui/browse/narrator-detail.html',
        {
            'narrator': api.ApiNarrator.api_get(oid, request),
            'interviews': api.ApiNarrator.interviews(oid, request, limit=1000),
        },
        context_instance=RequestContext(request, processors=[])
    )

def facet(request, facet_id):
    
    if facet_id == 'topics':
        template_name = 'ui/browse/facet-topics.html'
        key = '%s:terms:tree' % facet_id
        terms = cache.get(key)
        if not terms:
            terms = api.ApiFacet.make_tree(
                api.ApiFacet.api_children(
                    facet_id, request,
                    sort=[('sort','asc')],
                    limit=10000, raw=True
                )
            )
            for term in terms:
                term['links'] = {}
                term['links']['html'] = reverse('ui-browse-term', args=[facet_id, term['id']])
            cache.set(key, terms, settings.ELASTICSEARCH_QUERY_TIMEOUT)

    elif facet_id == 'facility':
        
        template_name = 'ui/browse/facet-facility.html'
        terms = api.ApiFacet.api_children(
            facet_id, request,
            sort=[('title','asc')],
            limit=10000, raw=True
        )
        # for some reason ES does not sort
        terms = sorted(terms, key=lambda term: term['title']) 
        for term in terms:
            term['links'] = {}
            term['links']['html'] = reverse(
                'ui-browse-term', args=[facet_id, term['id']]
            )
                
    return render_to_response(
        template_name,
        {
            'facet': api.ApiFacet.api_get(facet_id, request),
            'terms': terms,
        },
        context_instance=RequestContext(request, processors=[])
    )

def term( request, facet_id, term_id ):
    oid = '-'.join([facet_id, term_id])
    term = api.ApiTerm.api_get(oid, request)
    thispage = int(request.GET.get('page', 1))
    pagesize = settings.RESULTS_PER_PAGE
    results = api.ApiTerm.objects(
        facet_id, term_id,
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
            'facet': api.ApiFacet.api_get(facet_id, request),
            'term': term,
            'paginator': paginator,
            'page': page,
        },
        context_instance=RequestContext(request, processors=[])
    )
