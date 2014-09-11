from datetime import datetime
import logging
logger = logging.getLogger(__name__)

from dateutil import parser

from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import Http404, get_object_or_404, render_to_response
from django.template import RequestContext
from django.utils.http import urlquote  as django_urlquote

from DDR import docstore, models
from ui import domain_org
from ui import faceting
from ui import models
from ui.forms import SearchForm

# TODO We should have a whitelist of chars we *do* accept, not this.
SEARCH_INPUT_BLACKLIST = ('{', '}', '[', ']')


# helpers --------------------------------------------------------------

def kosher( query ):
    for char in SEARCH_INPUT_BLACKLIST:
        if char in query:
            return False
    return True


# views ----------------------------------------------------------------

def index( request ):
    return render_to_response(
        'ui/search/index.html',
        {'hide_header_search': True,
         'search_form': SearchForm,},
        context_instance=RequestContext(request, processors=[])
    )

def results( request ):
    """Results of a search query or a DDR ID query.
    """
    template = 'ui/search/results.html'
    context = {
        'hide_header_search': True,
        'query': '',
        'error_message': '',
        'search_form': SearchForm(),
        'paginator': None,
        'page': None,
        'filters': None,
        'sort': None,
    }
    context['query'] = request.GET.get('query', '')
    # silently strip out bad chars
    query = context['query']
    for char in SEARCH_INPUT_BLACKLIST:
        query = query.replace(char, '')
    if query:
        context['search_form'] = SearchForm({'query': query})
        object_id_parts = models.split_object_id(query)
        if object_id_parts and (object_id_parts[0] in ['collection', 'entity', 'file']):
            # query is a DDR ID -- go straight to document page
            model = object_id_parts.pop(0)
            document = docstore.get(settings.DOCSTORE_HOSTS, settings.DOCSTORE_INDEX,
                                    model, query.strip())
            if document and (document['found'] or document['exists']):
                # OK -- redirect to document page
                object_url = models.make_object_url(object_id_parts)
                if object_url:
                    return HttpResponseRedirect(object_url)
            else:
                # FAIL -- try again
                context['error_message'] = '"%s" is not a valid DDR object ID.' % query
                return render_to_response(
                    template, context, context_instance=RequestContext(request, processors=[])
                )
            
        # prep query for elasticsearch
        model = request.GET.get('model', None)
        filters = {}
        fields = models.all_list_fields()
        sort = {'record_created': request.GET.get('record_created', ''),
                'record_lastmod': request.GET.get('record_lastmod', ''),}
        # filter by partner
        repo,org = domain_org(request)
        if repo and org:
            filters['repo'] = repo
            filters['org'] = org
        
        # do query and cache the results
        results = models.cached_query(settings.DOCSTORE_HOSTS, settings.DOCSTORE_INDEX,
                                      query=query, filters=filters,
                                      fields=fields, sort=sort)
        
        if results.get('hits',None) and not results.get('status',None):
            # OK -- prep results for display
            thispage = request.GET.get('page', 1)
            objects = models.process_query_results(results, thispage, settings.RESULTS_PER_PAGE)
            paginator = Paginator(objects, settings.RESULTS_PER_PAGE)
            page = paginator.page(thispage)
            context['paginator'] = paginator
            context['page'] = page
        else:
            # FAIL -- elasticsearch error
            context['error_message'] = 'Search query "%s" caused an error. Please try again.' % query
            return render_to_response(
                template, context, context_instance=RequestContext(request, processors=[])
            )
    
    return render_to_response(
        template, context, context_instance=RequestContext(request, processors=[])
    )

def term_query( request, field, term ):
    """Results of what ElasticSearch calls a 'term query'.
    """
    terms_display = {'field':field, 'term':term}
    filters = {}
    
    # silently strip out bad chars
    for char in SEARCH_INPUT_BLACKLIST:
        field = field.replace(char, '')
        term = term.replace(char, '')
    
    # prep query for elasticsearch
    terms = {field:term}
    facet = faceting.get_facet(field)
    for t in facet['terms']:
        if t['id'] == term:
            try:
                terms_display['term'] = t['title_display']
            except:
                terms_display['term'] = t['title']
            break
    
    # filter by partner
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
        'ui/search/results.html',
        {'hide_header_search': True,
         'paginator': paginator,
         'page': page,
         'terms': terms_display,
         'filters': filters,
         'sort': sort,},
        context_instance=RequestContext(request, processors=[])
    )
