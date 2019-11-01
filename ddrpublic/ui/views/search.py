import json
import logging
logger = logging.getLogger(__name__)

from django.conf import settings
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.shortcuts import Http404, render

from .. import faceting
from .. import forms
from .. import misc
from .. import models

# TODO We should have a whitelist of chars we *do* accept, not this.
SEARCH_INPUT_BLACKLIST = ('{', '}', '[', ']')


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
    repo,org = misc.domain_org(request)
    if repo and org:
        filters['repo'] = repo
        filters['org'] = org
    
    fields = models.all_list_fields()
    sort = {'record_created': request.GET.get('record_created', ''),
            'record_lastmod': request.GET.get('record_lastmod', ''),}
    
    # do the query
    results = models.cached_query(settings.DOCSTORE_HOSTS,
                                  terms=terms, filters=filters,
                                  fields=fields, sort=sort)
    thispage = request.GET.get('page', 1)
    massaged = models.massage_query_results(results, thispage, settings.RESULTS_PER_PAGE)
    objects = models.instantiate_query_objects(massaged)
    paginator = Paginator(objects, settings.RESULTS_PER_PAGE)
    page = paginator.page(request.GET.get('page', 1))
    return render(request, 'ui/search/results.html', {
        'hide_header_search': True,
        'paginator': paginator,
        'page': page,
        'terms': terms_display,
        'filters': filters,
        'sort': sort,
    })
