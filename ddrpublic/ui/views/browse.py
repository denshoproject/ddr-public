import logging
logger = logging.getLogger(__name__)
from urllib.parse import urlparse

from django.conf import settings
from django.core.paginator import Paginator
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.cache import cache_page

from elastictools import search
from .. import encyc
from .. import forms_search as forms
from .. import models
from ..decorators import ui_state

SHOW_THESE = ['topics', 'facility', 'location', 'format', 'genre',]


@cache_page(settings.CACHE_TIMEOUT)
def index( request ):
    return render(request, 'ui/browse/index.html', {})

@ui_state
def narrators(request):
    thispage = int(request.GET.get('page', 1))
    pagesize = settings.RESULTS_PER_PAGE
    offset = models.search_offset(thispage, pagesize)
    results = models.Narrator.narrators(
        request,
        limit=pagesize,
        offset=offset,
    )
    paginator = Paginator(
        results.ordered_dict(
            request=request,
            format_functions=models.FORMATTERS,
            pad=True,
        )['objects'],
        results.page_size,
    )
    page = paginator.page(results.this_page)
    return render(request, 'ui/narrators/list.html', {
        'paginator': paginator,
        'page': paginator.page(thispage),
        'thispage': thispage,
        'api_url': reverse('ui-api-narrators'),
    })

@cache_page(settings.CACHE_TIMEOUT)
def narrator(request, oid):
    return render(request, 'ui/narrators/detail.html', {
        'narrator': models.Narrator.get(oid, request),
        'interviews': models.Narrator.interviews(oid, request, limit=1000),
        'api_url': reverse('ui-api-narrator', args=[oid]),
    })

@ui_state
def facet(request, facet_id):
    if facet_id == 'topics':
        template_name = 'ui/facets/facet-topics.html'
        terms = models.Facet.topics_terms(request)
        
    elif facet_id == 'facility':
        template_name = 'ui/facets/facet-facility.html'
        # for some reason ES does not sort
        terms = models.Facet.facility_terms(request)
    
    return render(request, template_name, {
        'facet': models.Facet.get(facet_id, request),
        'terms': terms,
        'api_url': reverse('ui-api-facetterms', args=[facet_id]),
    })

@ui_state
def term( request, facet_id, term_id ):
    oid = '-'.join([facet_id, term_id])
    template_name = 'ui/facets/term-%s.html' % facet_id
    facet = models.Facet.get(facet_id, request)
    term = models.Term.get(oid, request)
    
    # terms tree (topics)
    if facet_id == 'topics':
        term['tree'] = models.Term.topics_tree(term, request)
    
    # API urls for elinks
    for item in term.get('elinks', []):
        try:
            url = urlparse(item['url'])
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

    params = request.GET.copy()
    params['match_all'] = 'true'
    params[facet_id] = term_id
    searcher = search.Searcher(models.DOCSTORE)
    searcher.prepare(
        params=params,
        params_whitelist=models.SEARCH_PARAM_WHITELIST,
        search_models=models.SEARCH_MODELS,
        sort=[],
        fields=models.SEARCH_INCLUDE_FIELDS,
        fields_nested=models.SEARCH_NESTED_FIELDS,
        fields_agg=models.SEARCH_AGG_FIELDS,
    )
    
    limit,offset = search.limit_offset(request, settings.RESULTS_PER_PAGE)
    results = searcher.execute(limit, offset)
    paginator = Paginator(
        results.ordered_dict(
            request=request,
            format_functions=models.FORMATTERS,
            pad=True,
        )['objects'],
        results.page_size,
    )
    page = paginator.page(results.this_page)
    
    form = forms.SearchForm(
        data=request.GET.copy(),
        search_results=results,
    )

    return render(request, template_name, {
        'facet': facet,
        'term': term,
        'results': results,
        'paginator': paginator,
        'page': page,
        'form': form,
        'api_url': reverse('ui-api-term', args=[facet['id'], term['term_id']]),
    })
