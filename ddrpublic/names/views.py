import json
from urllib.parse import urlparse, urlunparse

from django.conf import settings
from django.core.paginator import Paginator
from django.http.request import HttpRequest
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from namesdb import definitions
from . import forms
from . import models
from ui import api
from ui import search

PAGE_SIZE = 20
CONTEXT = 3
DEFAULT_FILTERS = [
    'm_dataset',
    'm_camp',
    'm_originalstate',
]
NON_FILTER_FIELDS = [
    'query'
]


def _mkurl(request, path, query=None):
    return urlunparse((
        request.META['wsgi.url_scheme'],
        request.META.get('HTTP_HOST'),
        path, None, query, None
    ))

def index(request, template_name='names/index.html'):
    """Simplified index page with just query and camp fields.
    """
    kwargs = [(key,val) for key,val in request.GET.items()]
    kwargs_values = [val for val in request.GET.values() if val]
    thispage = int(request.GET.get('page', 1))
    pagesize = int(request.GET.get('pagesize', PAGE_SIZE))
    
    # All the filter fields are MultipleChoiceFields, which does not
    # support an "empty_label" choice.  Unfortunately, the UI design
    # makes use of a <select> with a blank "All camps" default.
    # So... make a copy of request.GET and forcibly remove 'm_camp'
    # if the "All camps" choice was selected.
    local_GET = request.GET.copy()
    if ('m_camp' in local_GET.keys()) and not local_GET.get('m_camp'):
        local_GET.pop('m_camp')
    
    search = None
    body = {}
    m_camp_selected = None
    paginator = None
    if kwargs_values:
        form = forms.SearchForm(
            local_GET,
            hosts=settings.NAMESDB_DOCSTORE_HOST,
        )
        if form.is_valid():
            filters = form.cleaned_data
            query = filters.pop('query')
            start,end = models.Paginator.start_end(thispage, pagesize)
            search = models.search(
                settings.NAMESDB_DOCSTORE_HOST,
                query=query,
                filters=filters,
                start=start,
                pagesize=pagesize,
            )
            body = search.to_dict()
            response = search.execute()
            m_camp_selected = filters['m_camp']
            #form.update_doc_counts(response)
            paginator = models.Paginator(
                response, thispage, pagesize, CONTEXT, request.META['QUERY_STRING']
            )
    else:
        form = forms.SearchForm(
            hosts=settings.NAMESDB_DOCSTORE_HOST,
        )
    m_camp_choices = form.fields['m_camp'].choices
    return render(request, template_name, {
        'kwargs': kwargs,
        'form': form,
        'm_camp_choices': m_camp_choices,
        'm_camp_selected': m_camp_selected,
        'body': json.dumps(body, indent=4, separators=(',', ': '), sort_keys=True),
        'paginator': paginator,
    })

def _limit_offset(request):
    if request.GET.get('offset'):
        # limit and offset args take precedence over page
        limit = request.GET.get(
            'limit', int(request.GET.get('limit', settings.RESULTS_PER_PAGE))
        )
        offset = request.GET.get('offset', int(request.GET.get('offset', 0)))
    elif request.GET.get('page'):
        limit = settings.RESULTS_PER_PAGE
        thispage = int(request.GET['page'])
        offset = search.es_offset(limit, thispage)
    else:
        limit = settings.RESULTS_PER_PAGE
        offset = 0
    return limit,offset

def search_ui(request):
    api_url = '%s?%s' % (
        _mkurl(request, reverse('names-api-search')),
        request.META['QUERY_STRING']
    )
    context = {
        'searching': False,
        'filters': True,
        'api_url': api_url,
    }
    
    if request.GET.get('fulltext'):
        context['searching'] = True
        
        searcher = search.Searcher()
        searcher.prepare(
            params=request.GET.copy(),
            params_whitelist=models.SEARCH_PARAM_WHITELIST,
            search_models=models.SEARCH_MODELS,
            fields=models.SEARCH_INCLUDE_FIELDS,
            fields_nested=models.SEARCH_NESTED_FIELDS,
            fields_agg=models.SEARCH_AGG_FIELDS,
        )
        limit,offset = _limit_offset(request)
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
        context['form'] = form

    else:
        context['form'] = forms.SearchForm()

    return render(request, 'names/index.html', context)

def detail(request, object_id, template_name='names/detail.html'):
    try:
        record = models.NameRecord.get(object_id, request)
    except models.NotFound:
        raise Http404
    # Format field data, add labels
    record_type = type(record)
    record.fields = models.NameRecord.fields_enriched(record, True, True).values()
    # TODO Doesn't seem to work on current production site
    #record.other_datasets = models.NameRecord.other_datasets(record)
    record.other_datasets = []
    record.family_members = models.NameRecord.same_familyno(record, request)
    return render(request, template_name, {
        'record': record,
    })
