from datetime import datetime
import logging
logger = logging.getLogger(__name__)

from dateutil import parser

from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import Http404, get_object_or_404, render_to_response
from django.template import RequestContext
from django.utils.http import urlquote  as django_urlquote

from DDR import elasticsearch, models
from ui import faceting, models
from ui.forms import SearchForm


# helpers --------------------------------------------------------------


# views ----------------------------------------------------------------

def index( request ):
    return render_to_response(
        'ui/search/index.html',
        {'search_form': SearchForm,},
        context_instance=RequestContext(request, processors=[])
    )

def results( request ):
    """Results of a search query or a DDR ID query.
    """
    query = ''
    if 'query' in request.GET and request.GET['query']:
        query = request.GET['query']
        # if query is a DDR ID go straight to document page
        object_id_parts = models.split_object_id(query)
        if object_id_parts and (object_id_parts[0] in ['collection', 'entity', 'file']):
            model = object_id_parts.pop(0)
            document = elasticsearch.get(settings.ELASTICSEARCH_HOST_PORT, settings.DOCUMENT_INDEX,
                                         model, q.strip())
            if document['status'] == 200:
                object_url = models.make_object_url(object_id_parts)
                if object_url:
                    return HttpResponseRedirect(object_url)
            else:
                # print error message and go to blank search page
                return render_to_response(
                    'ui/search/results.html',
                    {'hide_header_search': True,
                     'error_message': '"%s" is not a valid DDR object ID.' % q,},
                    context_instance=RequestContext(request, processors=[])
                )
        # prep query for elasticsearch
        model = request.GET.get('model', None)
        filters = {}
        fields = models.all_list_fields()
        sort = {'record_created': request.GET.get('record_created', ''),
                'record_lastmod': request.GET.get('record_lastmod', ''),}
        # do the query
        results = elasticsearch.query(settings.ELASTICSEARCH_HOST_PORT, settings.DOCUMENT_INDEX,
                                      query=query, filters=filters,
                                      fields=fields, sort=sort)
        if results.get('status',None) and results['status'] != 200:
            return render_to_response(
                'ui/search/results.html',
                {'hide_header_search': True,
                 'error_message': 'Search query "%s" caused an error. Please try again.' % q,
                 'search_form': form,},
                context_instance=RequestContext(request, processors=[])
            )
        thispage = request.GET.get('page', 1)
        objects = models.process_query_results(results, thispage, settings.RESULTS_PER_PAGE)
        paginator = Paginator(objects, settings.RESULTS_PER_PAGE)
        page = paginator.page(thispage)
        # search form
        search_form = SearchForm({'query': query})
        return render_to_response(
            'ui/search/results.html',
            {'hide_header_search': True,
             'paginator': paginator,
             'page': page,
             'query': query,
             'filters': filters,
             'sort': sort,
             'search_form': search_form,},
            context_instance=RequestContext(request, processors=[])
        )
    return render_to_response(
        'ui/search/results.html',
        {'hide_header_search': True,},
        context_instance=RequestContext(request, processors=[])
    )

def term_query( request, field, term ):
    """Results of what ElasticSearch calls a 'term query'.
    """
    # prep query for elasticsearch
    terms_display = {'field':field, 'term':term}
    terms = {field:term}
    facet = faceting.get_facet(field)
    for t in facet['terms']:
        if t['id'] == term:
            try:
                terms_display['term'] = t['title_display']
            except:
                terms_display['term'] = t['title']
            break
    filters = {}
    fields = models.all_list_fields()
    sort = {'record_created': request.GET.get('record_created', ''),
            'record_lastmod': request.GET.get('record_lastmod', ''),}
    # do the query
    results = elasticsearch.query(settings.ELASTICSEARCH_HOST_PORT, settings.DOCUMENT_INDEX,
                                  term=terms, filters=filters,
                                  fields=fields, sort=sort)
    thispage = request.GET.get('page', 1)
    objects = models.process_query_results(results, thispage, settings.RESULTS_PER_PAGE)
    paginator = Paginator(objects, settings.RESULTS_PER_PAGE)
    page = paginator.page(request.GET.get('page', 1))
    return render_to_response(
        'ui/search/results.html',
        {'hide_header_search': True,
         'paginator': paginator,
         'page': page,
         'terms': terms_display,
         'filters': filters,
         'sort': sort,},
        context_instance=RequestContext(request, processors=[])
    )
