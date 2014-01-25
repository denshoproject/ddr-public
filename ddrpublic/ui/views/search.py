from datetime import datetime
import logging
logger = logging.getLogger(__name__)

from dateutil import parser

from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import Http404, get_object_or_404, render_to_response
from django.template import RequestContext

from DDR import elasticsearch


# helpers --------------------------------------------------------------


# views ----------------------------------------------------------------

def index( request ):
    return render_to_response(
        'ui/search/index.html',
        {},
        context_instance=RequestContext(request, processors=[])
    )

def results( request ):
    """Results of a search query.
    """
    # prep query for elasticsearch
    model = request.GET.get('model', None)
    q = request.GET.get('query', None)
    #filters = {'public': request.GET.get('public', ''),
    #           'status': request.GET.get('status', ''),}
    filters = {}
    sort = {'record_created': request.GET.get('record_created', ''),
            'record_lastmod': request.GET.get('record_lastmod', ''),}
    
    # do the query
    hits = elasticsearch.query(settings.ELASTICSEARCH_HOST_PORT, query=q, filters=filters, sort=sort)
    
    # massage the results
    def rename(hit, fieldname):
        # Django templates can't display fields/attribs that start with underscore
        under = '_%s' % fieldname
        hit[fieldname] = hit.pop(under)
    for hit in hits:
        rename(hit, 'index')
        rename(hit, 'type')
        rename(hit, 'id')
        rename(hit, 'score')
        rename(hit, 'source')
        # extract certain fields for easier display
        for field in hit['source']['d'][1:]:
            if field.keys():
                if field.keys()[0] == 'id': hit['id'] = field['id']
                if field.keys()[0] == 'title': hit['title'] = field['title']
                if field.keys()[0] == 'record_created': hit['record_created'] = parser.parse(field['record_created'])
                if field.keys()[0] == 'record_lastmod': hit['record_lastmod'] = parser.parse(field['record_lastmod'])
        # assemble urls for each record type
        if hit.get('id', None):
            if hit['type'] == 'collection':
                repo,org,cid = hit['id'].split('-')
                hit['url'] = reverse('ui-collection', args=[repo,org,cid])
            elif hit['type'] == 'entity':
                repo,org,cid,eid = hit['id'].split('-')
                hit['url'] = reverse('ui-entity', args=[repo,org,cid,eid])
            elif hit['type'] == 'file':
                repo,org,cid,eid,role,sha1 = hit['id'].split('-')
                hit['url'] = reverse('ui-file', args=[repo,org,cid,eid,role,sha1])
    return render_to_response(
        'ui/search/results.html',
        {'hits': hits,
         'query': q,
         'filters': filters,
         'sort': sort,},
        context_instance=RequestContext(request, processors=[])
    )
