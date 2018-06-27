import logging
logger = logging.getLogger(__name__)

from django.conf import settings
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import Http404, render

from .. import archivedotorg
from .. import models
from .. import misc


def detail(request, oid):
    try:
        entity = models._object(request, oid)
    except models.NotFound:
        raise Http404
    misc.filter_if_branded(request, entity['organization_id'])

    model = entity['model']
    
    # if this is an interview, redirect to first segment
    format_ = None
    if entity.get('format') and isinstance(entity['format'], str):
        format_ = entity['format']
    elif entity.get('format') and isinstance(entity['format'], dict):
        format_ = entity['format']['id']  # format is wrapped in Entity.get
    format_ = entity['format']  # format is wrapped in Entity.get
    if format_ == 'vh':
        if model == 'segment':
            return HttpResponseRedirect(reverse('ui-interview', args=[oid]))
        elif (model == 'entity'):
            segments = models.Entity.children(oid, request, limit=1)
            if segments['objects']:
                # make sure this is actually a segment before redirecting
                s = models._object(request, segments['objects'][0]['id'])
                if s['model'] == 'segment':
                    return HttpResponseRedirect(reverse('ui-interview', args=[s['id']]))
    
    parent = models._object(request, entity['parent_id'])
    organization = models._object(request, entity['organization_id'])
    # signature
    signature = None
    if entity.get('signature_id'):
        signature = models._object(request, entity['signature_id'])
    if signature:
        signature['access_size'] = models.file_size(signature['links']['img'])
    # facet terms
    facilities = [item for item in getattr(entity, 'facility', [])]
    creators = [item for item in getattr(entity, 'creators', [])]
    # children/nodes
    thispage = request.GET.get('page', 1)
    pagesize = 5
    children_paginator = Paginator(
        models.pad_results(
            models.Entity.children(
                oid, request, limit=pagesize, offset=0,
            ),
            pagesize,
            thispage
        ),
        pagesize
    )
    nodes_paginator = Paginator(
        models.pad_results(
            models.Entity.files(
                oid, request, limit=pagesize, offset=0,
            ),
            pagesize,
            thispage
        ),
        pagesize
    )
    return render(request, 'ui/entities/detail.html', {
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
    })

def interview(request, oid):
    try:
        segment = models._object(request, oid)
    except models.NotFound:
        raise Http404
    misc.filter_if_branded(request, segment['organization_id'])
    # die if not a segment
    if segment['model'] != 'segment':
        raise Http404

    entity = models._object(request, segment['parent_id'])
    parent = models._object(request, entity['parent_id'])
    collection = models._object(request, entity['collection_id'])
    organization = models._object(request, entity['organization_id'])
    
    # TODO only id, title, extent
    segments = models._object_children(
        document=entity,
        models=['entity','segment'],
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
    
    transcripts = models.Entity.transcripts(
        segment['id'], segment['parent_id'], segment['collection_id'],
        request
    )
    download_meta = archivedotorg.segment_download_meta(segment['id'])
    
    return render(request, 'ui/entities/segment.html', {
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
    })
    
def children( request, oid, role=None ):
    """Lists all direct children of the entity.
    """
    try:
        entity = models._object(request, oid)
    except models.NotFound:
        raise Http404
    misc.filter_if_branded(request, entity['organization_id'])
    # children
    thispage = int(request.GET.get('page', 1))
    pagesize = settings.RESULTS_PER_PAGE
    offset = models.search_offset(thispage, pagesize)
    paginator = Paginator(
        models.pad_results(
            models._object_children(
                document=entity,
                request=request,
                limit=pagesize,
                offset=offset,
            ),
            pagesize,
            thispage
        ),
        pagesize
    )
    return render(request, 'ui/entities/children.html', {
        'object': entity,
        'paginator': paginator,
        'page': paginator.page(thispage),
        'api_url': reverse('ui-api-object-children', args=[oid]),
    })

def nodes( request, oid, role=None ):
    """Lists all nodes of the entity.
    """
    try:
        entity = models.Entity.get(oid, request)
    except models.NotFound:
        raise Http404
    misc.filter_if_branded(request, entity['organization_id'])
    # nodes
    thispage = int(request.GET.get('page', 1))
    pagesize = settings.RESULTS_PER_PAGE
    offset = models.search_offset(thispage, pagesize)
    paginator = Paginator(
        models.pad_results(
            models.Entity.files(
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
    return render(request, 'ui/entities/nodes.html', {
        'object': entity,
        'paginator': paginator,
        'page': paginator.page(thispage),
        'api_url': reverse('ui-api-object-nodes', args=[oid]),
    })
