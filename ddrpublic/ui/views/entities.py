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
    i = Identifier(id=oid)
    filter_if_branded(request, i)
    try:
        entity = api.Entity.get(i.id, request)
    except api.NotFound:
        raise Http404
    entity['identifier'] = i
    
    # if this is an interview, redirect to first segment
    format_ = None
    if entity.get('format') and isinstance(entity['format'], basestring):
        format_ = entity['format']
    elif entity.get('format') and isinstance(entity['format'], dict):
        format_ = entity['format']['id']  # format is wrapped in Entity.get
    format_ = entity['format']['id']  # format is wrapped in Entity.get
    if format_ == 'vh':
        if i.model == 'segment':
            return HttpResponseRedirect(reverse('ui-interview', args=[i.id]))
        elif (i.model == 'entity'):
            segments = api.Entity.children(oid, request, limit=1)
            if segments['objects']:
                # make sure this is actually a segment before redirecting
                si = Identifier(id=segments['objects'][0]['id'])
                if si.model == 'segment':
                    return HttpResponseRedirect(reverse('ui-interview', args=[si.id]))
    
    parent = api.Collection.get(i.parent_id(), request)
    organization = api.Organization.get(i.organization().id, request)
    # signature
    signature = None
    if entity.get('signature_id'):
        signature = api.File.get(entity['signature_id'], request)
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
            api.Entity.children(
                i.id, request, limit=pagesize, offset=0,
            ),
            pagesize,
            thispage
        ),
        pagesize
    )
    nodes_paginator = Paginator(
        api.pad_results(
            api.Entity.nodes(
                i.id, request, limit=pagesize, offset=0,
            ),
            pagesize,
            thispage
        ),
        pagesize
    )
    return render_to_response(
        'ui/entities/detail.html',
        {
            'repo': i.parts['repo'],
            'org': i.parts['org'],
            'cid': i.parts['cid'],
            'eid': i.parts['eid'],
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
    si = Identifier(id=oid)
    filter_if_branded(request, si)
    try:
        segment = api.Entity.get(si.id, request)
    except api.NotFound:
        raise Http404
    segment['identifier'] = si
    # die if not a segment
    if segment['model'] != 'segment':
        raise Http404
    
    ei = si.parent()
    entity = api.Entity.get(ei.id, request)
    entity['identifier'] = si
    parent = api.Collection.get(entity['identifier'].parent_id(), request)
    collection = api.Collection.get(si.collection_id(), request)
    organization = api.Organization.get(entity['identifier'].organization().id, request)
    
    # TODO only id, title, extent
    segments = api.Entity.children(ei.id, request, limit=1000)
    # get next,prev segments
    segment['index'] = 0
    num_segments = len(segments['objects'])
    for n,s in enumerate(segments['objects']):
        if s['id'] == si.id:
            segment['index'] = n
    segment['prev'] = None; segment['next'] = None
    pr = segment['index'] - 1; nx = segment['index'] + 1
    if pr >= 0:
        segment['prev'] = segments['objects'][pr]['id']
    if nx < num_segments:
        segment['next'] = segments['objects'][nx]['id']
    # segment index for humans
    segment['this'] = segment['index'] + 1
    
    transcripts = api.Entity.transcripts(si, request)
    download_meta = archivedotorg.segment_download_meta(si.id)
    
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
    i = Identifier(id=oid)
    filter_if_branded(request, i)
    try:
        entity = api.Entity.get(i.id, request)
    except api.NotFound:
        raise Http404
    entity['identifier'] = i
    # children
    thispage = int(request.GET.get('page', 1))
    pagesize = settings.RESULTS_PER_PAGE
    offset = api.search_offset(thispage, pagesize)
    paginator = Paginator(
        api.pad_results(
            api.Entity.children(
                i.id,
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
        'ui/entities/children.html',
        {
            'repo': i.parts['repo'],
            'org': i.parts['org'],
            'cid': i.parts['cid'],
            'eid': i.parts['eid'],
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
    i = Identifier(id=oid)
    filter_if_branded(request, i)
    try:
        entity = api.Entity.get(i.id, request)
    except api.NotFound:
        raise Http404
    entity['identifier'] = i
    # nodes
    thispage = int(request.GET.get('page', 1))
    pagesize = settings.RESULTS_PER_PAGE
    offset = api.search_offset(thispage, pagesize)
    paginator = Paginator(
        api.pad_results(
            api.Entity.nodes(
                i.id,
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
            'repo': i.parts['repo'],
            'org': i.parts['org'],
            'cid': i.parts['cid'],
            'eid': i.parts['eid'],
            'object': entity,
            'paginator': paginator,
            'page': paginator.page(thispage),
            'api_url': reverse('ui-api-object-nodes', args=[oid]),
        },
        context_instance=RequestContext(request, processors=[])
    )
