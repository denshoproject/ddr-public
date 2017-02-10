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
    entity = api.ApiEntity.api_get(i.id, request)
    entity['identifier'] = i
    if not entity:
        raise Http404
    
    # if this is an interview, redirect to first segment
    if (entity['format'] == 'vh') and (entity['model'] == 'entity'):
        segments = api.ApiEntity.api_children(oid, request, limit=1)
        if segments['objects'][0]:
            sid = segments['objects'][0]['id']
            url = reverse('ui-interview', args=[sid])
            return HttpResponseRedirect(url)
    
    parent = api.ApiCollection.api_get(i.parent_id(), request)
    organization = api.ApiOrganization.api_get(i.organization().id, request)
    # facet terms
    facilities = [item for item in getattr(entity, 'facility', [])]
    creators = [item for item in getattr(entity, 'creators', [])]
    # children/nodes
    thispage = request.GET.get('page', 1)
    children_paginator = Paginator(
        api.ApiEntity.api_children(i.id, request)['objects'],
        DEFAULT_SIZE
    )
    nodes_paginator = Paginator(
        api.ApiEntity.api_nodes(i.id, request)['objects'],
        DEFAULT_SIZE
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
    segment = api.ApiEntity.api_get(si.id, request)
    segment['identifier'] = si
    if not segment:
        raise Http404
    ei = si.parent()
    entity = api.ApiEntity.api_get(ei.id, request)
    entity['identifier'] = si
    parent = api.ApiCollection.api_get(entity['identifier'].parent_id(), request)
    organization = api.ApiOrganization.api_get(entity['identifier'].organization().id, request)
    
    # TODO only id, title, extent
    segments = api.ApiEntity.api_children(ei.id, request, limit=1000)
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
    
    transcripts = api.ApiEntity.transcripts(si, request)
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
    entity = api.ApiEntity.api_get(i.id, request)
    entity['identifier'] = i
    if not entity:
        raise Http404
    # children
    thispage = request.GET.get('page', 1)
    children_paginator = Paginator(
        api.ApiEntity.api_children(i.id, request)['objects'],
        DEFAULT_SIZE
    )
    return render_to_response(
        'ui/entities/children.html',
        {
            'repo': i.parts['repo'],
            'org': i.parts['org'],
            'cid': i.parts['cid'],
            'eid': i.parts['eid'],
            'object': entity,
            'paginator': children_paginator,
            'page': children_paginator.page(thispage),
            'api_url': reverse('ui-api-object-children', args=[oid]),
        },
        context_instance=RequestContext(request, processors=[])
    )

def nodes( request, oid, role=None ):
    """Lists all nodes of the entity.
    """
    i = Identifier(id=oid)
    filter_if_branded(request, i)
    entity = api.ApiEntity.api_get(i.id, request)
    entity['identifier'] = i
    if not entity:
        raise Http404
    # nodes
    thispage = request.GET.get('page', 1)
    nodes_paginator = Paginator(
        api.ApiEntity.api_nodes(i.id, request)['objects'],
        DEFAULT_SIZE
    )
    return render_to_response(
        'ui/entities/nodes.html',
        {
            'repo': i.parts['repo'],
            'org': i.parts['org'],
            'cid': i.parts['cid'],
            'eid': i.parts['eid'],
            'object': entity,
            'paginator': nodes_paginator,
            'page': nodes_paginator.page(thispage),
            'api_url': reverse('ui-api-object-nodes', args=[oid]),
        },
        context_instance=RequestContext(request, processors=[])
    )
