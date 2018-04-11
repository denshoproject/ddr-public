import logging
logger = logging.getLogger(__name__)

from django.conf import settings
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import Http404, get_object_or_404, render_to_response
from django.template import RequestContext

from ui import api
from ui import archivedotorg
from ui.identifier import Identifier
from ui.models import DEFAULT_SIZE
from ui.views import filter_if_branded


# views ----------------------------------------------------------------

def detail(request, oid):
    try:
        entity = api._object(request, oid)
    except api.NotFound:
        raise Http404
    filter_if_branded(request, entity['organization_id'])

    model = entity['model']
    
    # if this is an interview, redirect to first segment
    format_ = None
    if entity.get('format') and isinstance(entity['format'], basestring):
        format_ = entity['format']
    elif entity.get('format') and isinstance(entity['format'], dict):
        format_ = entity['format']['id']  # format is wrapped in Entity.get
    format_ = entity['format']  # format is wrapped in Entity.get
    if format_ == 'vh':
        if model == 'segment':
            return HttpResponseRedirect(reverse('ui-interview', args=[oid]))
        elif (model == 'entity'):
            segments = api.Entity.children(oid, request, limit=1)
            if segments['objects']:
                # make sure this is actually a segment before redirecting
                si = Identifier(id=segments['objects'][0]['id'])
                if si.model == 'segment':
                    return HttpResponseRedirect(reverse('ui-interview', args=[si.id]))
    
    parent = api._object(request, entity['parent_id'])
    organization = api._object(request, entity['organization_id'])
    # signature
    signature = None
    if entity.get('signature_id'):
        signature = api._object(request, entity['signature_id'])
    if signature:
        signature['access_size'] = api.file_size(signature['links']['img'])
    # facet terms
    facilities = [item for item in getattr(entity, 'facility', [])]
    creators = [item for item in getattr(entity, 'creators', [])]
    # children/nodes
    thispage = request.GET.get('page', 1)
    pagesize = 5
    children_paginator = Paginator(
        api.pad_results(
            api._object_children(
                document=entity,
                request=request,
                limit=pagesize,
                offset=0,
            ),
            pagesize,
            thispage
        ),
        pagesize
    )
    nodes_paginator = Paginator(
        api.pad_results(
            api.Entity.files(
                oid, request, limit=pagesize, offset=0,
            ),
            pagesize,
            thispage
        ),
        pagesize
    )
    return render_to_response(
        'ui/entities/detail.html',
        {
            'object': entity,
            'facilities': facilities,
            'creators': creators,
            'parent': parent,
            'organization': organization,
            'signature': signature,
            'children_paginator': children_paginator,
            'children_page': children_paginator.page(thispage),
            'nodes_paginator': nodes_paginator,
            'nodes_page': nodes_paginator.page(thispage),
            'api_url': reverse('ui-api-object', args=[oid]),
        },
        context_instance=RequestContext(request, processors=[])
    )

def interview(request, oid):
    try:
        segment = api._object(request, oid)
    except api.NotFound:
        raise Http404
    filter_if_branded(request, segment['organization_id'])
    # die if not a segment
    if segment['model'] != 'segment':
        raise Http404

    entity = api._object(request, segment['parent_id'])
    parent = api._object(request, entity['parent_id'])
    collection = api._object(request, entity['collection_id'])
    organization = api._object(request, entity['organization_id'])
    
    # TODO only id, title, extent
    segments = api._object_children(
        document=entity,
        request=request,
        limit=1000,
        offset=0,
    )
    # get next,prev segments
    segment['index'] = 0
    num_segments = len(segments['objects'])
    for n,s in enumerate(segments['objects']):
        if s['id'] == segment['id']:
            segment['index'] = n
    segment['prev'] = None; segment['next'] = None
    pr = segment['index'] - 1; nx = segment['index'] + 1
    if pr >= 0:
        segment['prev'] = segments['objects'][pr]['id']
    if nx < num_segments:
        segment['next'] = segments['objects'][nx]['id']
    # segment index for humans
    segment['this'] = segment['index'] + 1
    
    transcripts = api.Entity.transcripts(segment['id'], request)
    download_meta = archivedotorg.segment_download_meta(segment['id'])
    
    return render_to_response(
        'ui/entities/segment.html',
        {
            'segment': segment,
            'segments': segments,
            'transcripts': transcripts,
            'downloads': download_meta,
            'entity': entity,
            'parent': parent,
            'collection': collection,
            'organization': organization,
            'tableft': request.GET.get('tableft', 'downloads'),
            'api_url': reverse('ui-api-object', args=[entity['id']]),
        },
        context_instance=RequestContext(request, processors=[])
    )
    
def children( request, oid, role=None ):
    """Lists all direct children of the entity.
    """
    try:
        entity = api._object(request, oid)
    except api.NotFound:
        raise Http404
    filter_if_branded(request, entity['organization_id'])
    # children
    thispage = int(request.GET.get('page', 1))
    pagesize = settings.RESULTS_PER_PAGE
    offset = api.search_offset(thispage, pagesize)
    paginator = Paginator(
        api.pad_results(
            api._object_children(
                document=entity,
                request=request,
                limit=pagesize,
                offset=0,
            ),
            pagesize,
            thispage
        ),
        pagesize
    )
    return render_to_response(
        'ui/entities/children.html',
        {
            'object': entity,
            'paginator': paginator,
            'page': paginator.page(thispage),
            'api_url': reverse('ui-api-object-children', args=[oid]),
        },
        context_instance=RequestContext(request, processors=[])
    )

def nodes( request, oid, role=None ):
    """Lists all nodes of the entity.
    """
    try:
        entity = api.Entity.get(oid, request)
    except api.NotFound:
        raise Http404
    filter_if_branded(request, entity['organization_id'])
    # nodes
    thispage = int(request.GET.get('page', 1))
    pagesize = settings.RESULTS_PER_PAGE
    offset = api.search_offset(thispage, pagesize)
    paginator = Paginator(
        api.pad_results(
            api.Entity.files(
                oid,
                request,
                limit=pagesize,
                offset=offset,
            ),
            pagesize,
            thispage
        ),
        pagesize
    )
    return render_to_response(
        'ui/entities/nodes.html',
        {
            'object': entity,
            'paginator': paginator,
            'page': paginator.page(thispage),
            'api_url': reverse('ui-api-object-nodes', args=[oid]),
        },
        context_instance=RequestContext(request, processors=[])
    )
