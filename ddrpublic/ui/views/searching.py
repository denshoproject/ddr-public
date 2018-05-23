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
from ui import forms_search as forms
from ui import models
from ui import search


def _mkurl(request, path, query=None):
    return urlparse.urlunparse((
        request.META['wsgi.url_scheme'],
        request.META['HTTP_HOST'],
        path, None, query, None
    ))
    
def search_ui(request):
    api_url = '%s?%s' % (
        _mkurl(request, reverse('ui-api-search')),
        request.META['QUERY_STRING']
    )
    context = {
        'template_extends': 'ui/search/base.html',
        'searching': False,
        'filters': True,
        'api_url': api_url,
    }
    
    if request.GET.get('fulltext'):
        context['searching'] = True
        
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
            #mappings=identifier.ELASTICSEARCH_CLASSES_BY_MODEL,
            #fields=identifier.ELASTICSEARCH_LIST_FIELDS,
        )
        searcher.prepare(request)
        results = searcher.execute(limit, offset)
        form = forms.SearchForm(
            data=request.GET.copy(),
            search_results=results,
        )
        context['results'] = results
        context['search_form'] = form
        
        if results.objects:
            paginator = Paginator(
                results.ordered_dict(
                    request=request,
                    list_function=models.format_object_detail2,
                    pad=True,
                )['objects'],
                results.page_size,
            )
            page = paginator.page(results.this_page)
            context['paginator'] = paginator
            context['page'] = page

    else:
        context['search_form'] = forms.SearchForm()

    return render(request, 'ui/search/results.html', context)
