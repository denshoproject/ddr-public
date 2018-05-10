import logging
logger = logging.getLogger(__name__)
import urlparse

from django.conf import settings
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.shortcuts import render, render_to_response
from django.template import RequestContext

from elasticsearch.exceptions import ConnectionError, ConnectionTimeout

from ui import api
from ui import docstore
from ui import search
from ui import forms_search as forms


def _mkurl(request, path, query=None):
    return urlparse.urlunparse((
        request.META['wsgi.url_scheme'],
        request.META['HTTP_HOST'],
        path, None, query, None
    ))
    
def search_ui(request):
    api_url = '%s?%s' % (
        _mkurl(request, reverse('api-search')),
        request.META['QUERY_STRING']
    )
    context = {
        'api_url': api_url,
    }

    if request.GET.get('fulltext'):

        if request.GET.get('offset'):
            # limit and offset args take precedence over page
            limit = request.GET.get('limit', int(request.GET.get('limit', settings.RESULTS_PER_PAGE)))
            offset = request.GET.get('offset', int(request.GET.get('offset', 0)))
        elif request.GET.get('page'):
            limit = settings.RESULTS_PER_PAGE
            thispage = int(request.GET['page'])
            offset = search.es_offset(limit, thispage)
        else:
            limit = settings.RESULTS_PER_PAGE
            offset = 0
        
        searcher = search.Searcher(
            mappings=identifier.ELASTICSEARCH_CLASSES_BY_MODEL,
            fields=identifier.ELASTICSEARCH_LIST_FIELDS,
        )
        searcher.prepare(request)
        results = searcher.execute(limit, offset)
        context['results'] = results
        context['search_form'] = forms.SearchForm(
            search_results=results,
            data=request.GET
        )
        
        if results.objects:
            paginator = Paginator(
                results.ordered_dict(
                    request=request, list_function=api._prep_detail, pad=True
                )['objects'],
                results.page_size,
            )
            context['paginator'] = paginator
            context['page'] = paginator.page(results.this_page)

    else:
        context['search_form'] = forms.SearchForm()
    
    return render(request, 'webui/search/search.html', context)
