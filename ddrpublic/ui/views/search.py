from copy import deepcopy
from datetime import datetime
import json
import logging
logger = logging.getLogger(__name__)

from dateutil import parser
import requests

from django.conf import settings
from django.core.cache import cache
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import Http404, get_object_or_404, render_to_response
from django.template import RequestContext
from django.utils.http import urlquote  as django_urlquote

from DDR import docstore
from ui.identifier import Identifier, MODEL_CLASSES
from ui import domain_org
from ui import faceting
from ui import models
from ui import forms
from ui import api

# TODO We should have a whitelist of chars we *do* accept, not this.
SEARCH_INPUT_BLACKLIST = ('{', '}', '[', ']')


# helpers --------------------------------------------------------------

def kosher( query ):
    for char in SEARCH_INPUT_BLACKLIST:
        if char in query:
            return False
    return True

def force_list(terms):
    if isinstance(terms, list):
        return terms
    elif isinstance(terms, basestring):
        return [terms]
    raise Exception('Not a list or a string')


# views ----------------------------------------------------------------
    
def results(request, object_=None):
    """Results of a search query or a DDR ID query.
    """
    this_url = reverse('ui-search-results')
    
    form = forms.SearchForm(request.GET)
    form.is_valid()
    
    thispage = int(request.GET.get('page', 1))
    pagesize = settings.RESULTS_PER_PAGE
    
    # query dict
    MODELS = [
        'collection',
        'entity',
        'segment',
        'narrator',
    ]
    query = {
        'fulltext': form.cleaned_data.get('fulltext', ''),
        'must': [],
        'models': MODELS,
        'offset': thispage - 1,
        'limit': pagesize,
        'aggs': {
            'format':   {'terms': {'size': 50, 'field': 'format'}},
            'genre':    {'terms': {'size': 50, 'field': 'genre'}},
            'topics':   {'terms': {'size': 50, 'field': 'topics.id'}},
            'facility': {'terms': {'size': 50, 'field': 'facility.id'}},
            'rights':   {'terms': {'size': 50, 'field': 'rights'}},
        },
    }

    # search within collection
    if object_ and (object_['model'] == 'collection'):
        this_url = reverse('ui-object-search', args=[object_['id']])
        query['models'] = ['entity', 'segment']
        query['must'].append(
            {"wildcard": {"id": "%s-*" % object_['id']}}
        )
    
    def add_must(form, form_fieldname, es_fieldname, query, filters=False):
        """
        This form_fieldname/es_fieldname mess is because we have a field
        (e.g. format) whose name is a Python reserved word, and several
        fields (e.g. topics, facility) where the real value is a subfield.
        """
        if form.cleaned_data.get(form_fieldname):
            query['must'].append(
                {"terms": {es_fieldname: force_list(form.cleaned_data[form_fieldname])}}
            )
            filters = True
        return filters
    
    filters = False
    filters = add_must(form, 'filter_format',   'format',      query, filters)
    filters = add_must(form, 'filter_genre',    'genre',       query, filters)
    filters = add_must(form, 'filter_topics',   'topics.id',   query, filters)
    filters = add_must(form, 'filter_facility', 'facility.id', query, filters)
    filters = add_must(form, 'filter_rights',   'rights',      query, filters)
    
    # remove match _all from must, keeping fulltext arg
    for item in query['must']:
        if item.get('match') \
        and item['match'].get('_all') \
        and (item['match']['_all'] == query.get('fulltext')):
            query['must'].remove(item)
    
    # run query
    searching = False
    aggregations = None
    paginator = None
    page = None
    if query['fulltext'] or query['must']:
        searching = True
        results = api.api_search(
            text=query['fulltext'],
            must=query['must'],
            should=[],
            mustnot=[],
            models=query['models'],
            sort_fields=[],
            limit=query['limit'],
            offset=query['offset'],
            aggs=query['aggs'],
            request=request,
        )
        aggregations = results.get('aggregations')
        form.choice_aggs(aggregations)
        
        paginator = Paginator(
            api.pad_results(
                results,
                pagesize,
                thispage
            ),
            pagesize
        )
        page = paginator.page(thispage)
    
    # collection base template or default search results template
    if object_ and (object_['model'] == 'collection'):
        template_extends = "ui/collections/base.html"
    else:
        template_extends = "ui/search/base.html"
    
    return render_to_response(
        'ui/search/results.html',
        {
            'template_extends': template_extends,
            'hide_header_search': True,
            'searching': searching,
            'object': object_,
            'tab': request.GET.get('tab', 'list'),
            'filters': filters,
            'query': query,
            'query_json': json.dumps(query),
            'aggregations': aggregations,
            'search_form': form,
            'paginator': paginator,
            'page': page,
            'this_url': this_url,
            'api_url': reverse('ui-api-search'),
        },
        context_instance=RequestContext(request, processors=[])
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
    massaged = models.massage_query_results(results, thispage, settings.RESULTS_PER_PAGE)
    objects = models.instantiate_query_objects(massaged)
    paginator = Paginator(objects, settings.RESULTS_PER_PAGE)
    page = paginator.page(request.GET.get('page', 1))
    return render_to_response(
        'ui/search/results.html',
        {
            'hide_header_search': True,
            'paginator': paginator,
            'page': page,
            'terms': terms_display,
            'filters': filters,
            'sort': sort,
        },
        context_instance=RequestContext(request, processors=[])
    )
