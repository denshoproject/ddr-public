import logging
logger = logging.getLogger(__name__)

from django.conf import settings
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import Http404, get_object_or_404, render_to_response
from django.template import RequestContext

from ui import api
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
        },
        context_instance=RequestContext(request, processors=[])
    )
