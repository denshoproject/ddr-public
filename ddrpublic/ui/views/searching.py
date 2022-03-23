import logging
logger = logging.getLogger(__name__)
import re
from urllib.parse import urlparse, urlunparse

from django.conf import settings
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from elastictools import search
from .. import api
from .. import forms_search as forms
from .. import models
from ..decorators import ui_state


def _mkurl(request, path, query=None):
    return urlunparse((
        request.META['wsgi.url_scheme'],
        request.META.get('HTTP_HOST'),
        path, None, query, None
    ))

ID_PATTERNS = [
    '^(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)-(?P<role>[a-zA-Z]+)-(?P<sha1>[\w]+)$',
    '^(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)-(?P<sid>[\d]+)-(?P<role>[a-zA-Z]+)-(?P<sha1>[\w]+)$',
    '^(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)-(?P<role>[a-zA-Z]+)$',
    '^(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)-(?P<sid>[\d]+)-(?P<role>[a-zA-Z]+)$',
    '^(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)-(?P<sid>[\d]+)$',
    '^(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)$',
    '^(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)$',
    #'^(?P<repo>[\w]+)-(?P<org>[\w]+)$',
    #'^(?P<repo>[\w]+)$',
]

def is_ddr_id(text, patterns=ID_PATTERNS):
    """True if text matches one of ID_PATTERNS
    
    See ddr-cmdln:DDR.identifier._is_id
    
    @param text: str
    @returns: dict of idparts including model
    """
    try:
        ddr_index = text.index('ddr')
    except:
        ddr_index = -1
    if ddr_index == 0:
        for pattern in patterns:
            m = re.match(pattern, text)
            if m:
                idparts = {k:v for k,v in m.groupdict().items()}
                return idparts
    return {}


# views ----------------------------------------------------

@ui_state
def search_ui(request):
    api_url = '%s?%s' % (
        _mkurl(request, reverse('ui-api-search')),
        request.META['QUERY_STRING']
    )
    context = {
        'template_extends': 'ui/search/base.html',
        'hide_header_search': True,
        'searching': False,
        'filters': True,
        'api_url': api_url,
    }
    
    searcher = search.Searcher(models.DOCSTORE)
    if request.GET.get('fulltext'):
        # Redirect if fulltext is a DDR ID
        if is_ddr_id(request.GET.get('fulltext')):
            return HttpResponseRedirect(
                reverse('ui-object-detail', args=[
                    request.GET.get('fulltext')
            ]))
        params = request.GET.copy()
        searcher.prepare(
            params=params,
            params_whitelist=models.SEARCH_PARAM_WHITELIST,
            search_models=models.SEARCH_MODELS,
            sort=[],
            fields=models.SEARCH_INCLUDE_FIELDS,
            fields_nested=models.SEARCH_NESTED_FIELDS,
            fields_agg=models.SEARCH_AGG_FIELDS,
        )
        context['searching'] = True
    
    if searcher.params.get('fulltext'):
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
        
        context['results'] = results
        context['paginator'] = paginator
        context['page'] = page
        context['search_form'] = form

    else:
        form = forms.SearchForm(
            data=request.GET.copy(),
        )
        context['search_form'] = forms.SearchForm()

    return render(request, 'ui/search/results.html', context)

def collection(request, oid):
    #filter_if_branded(request, i)
    collection = models.Collection.get(oid, request)
    if not collection:
        raise Http404
    return parent_search(request, collection)

def facetterm(request, facet_id, term_id):
    oid = '-'.join([facet_id, term_id])
    term = models.Term.get(oid, request)
    if not term:
        raise Http404
    return parent_search(request, term)

def narrator(request, oid):
    narrator = models.Narrator.get(oid, request)
    if not narrator:
        raise Http404
    return parent_search(request, narrator)

@ui_state
def parent_search(request, obj):
    """search within collection/facetterm/narrator
    """
    api_url = '%s?%s' % (
        _mkurl(request, reverse('ui-api-search')),
        request.META['QUERY_STRING']
    )
    this_url = reverse('ui-search-results')
    template = 'ui/search/results.html'
    template_extends = "ui/search/base.html"
    context = {
        'hide_header_search': True,
        'searching': False,
        'filters': True,
        'api_url': api_url,
    }

    params = request.GET.copy()
    limit,offset = search.limit_offset(request, settings.RESULTS_PER_PAGE)
    params['parent'] = obj['id']
    
    # search collection
    if obj['model'] == 'collection':
        search_models = ['ddrentity', 'ddrsegment']
        this_url = reverse('ui-search-collection', args=[obj['id']])
        template_extends = "ui/collections/base.html"
    # search topic
    elif (obj['model'] == 'ddrfacetterm') and (obj['facet'] == 'topics'):
        this_url = reverse('ui-search-facetterm', args=[obj['facet'], obj['term_id']])
        template_extends = "ui/facets/base-topics.html"
        obj['model'] = 'topics'
    # search facility
    elif (obj['model'] == 'ddrfacetterm') and (obj['facet'] == 'facility'):
        this_url = reverse('ui-search-facetterm', args=[obj['facet'], obj['term_id']])
        template_extends = "ui/facets/base-facility.html"
        obj['model'] = 'facilities'
    # search narrator
    elif obj['model'] == 'narrator':
        search_models = ['ddrentity', 'ddrsegment']
        this_url = reverse('ui-search-narrator', args=[obj['id']])
        template_extends = "ui/narrators/base.html"
        obj['title'] = obj['display_name']
    context['template_extends'] = template_extends
    context['object'] = obj

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
        data=params,
        search_results=results,
    )
    context['results'] = results
    context['search_form'] = form
    context['paginator'] = paginator
    context['page'] = page

    return render(request, 'ui/search/results.html', context)
