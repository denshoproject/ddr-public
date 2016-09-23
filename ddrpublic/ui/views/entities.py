import logging
logger = logging.getLogger(__name__)

from django.conf import settings
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import Http404, get_object_or_404, render_to_response
from django.template import RequestContext

from ui.identifier import Identifier
from ui.models import Repository, Organization, Collection, Entity, File
from ui.models import DEFAULT_SIZE
from ui.views import filter_if_branded


# views ----------------------------------------------------------------

def detail(request, oid):
    i = Identifier(id=oid)
    filter_if_branded(request, i)
    entity = Entity.get(i)
    if not entity:
        raise Http404
    parent = entity.collection()
    organization = Organization.get(entity.identifier.organization())
    # facet terms
    facilities = [item for item in getattr(entity, 'facility', [])]
    creators = [item for item in getattr(entity, 'creators', [])]
    # child objects
    thispage = 1
    objects = entity.children(thispage, DEFAULT_SIZE)
    paginator = Paginator(objects, DEFAULT_SIZE)
    page = paginator.page(thispage)
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
            'paginator': paginator,
            'page': page,
        },
        context_instance=RequestContext(request, processors=[])
    )

def files( request, oid, role=None ):
    """Lists all the files in an entity.
    """
    i = Identifier(id=oid)
    filter_if_branded(request, i)
    entity = Entity.get(i)
    if not entity:
        raise Http404
    thispage = request.GET.get('page', 1)
    objects = entity.children(thispage, settings.RESULTS_PER_PAGE)
    paginator = Paginator(objects, settings.RESULTS_PER_PAGE)
    page = paginator.page(thispage)
    return render_to_response(
        'ui/entities/files.html',
        {
            'repo': i.parts['repo'],
            'org': i.parts['org'],
            'cid': i.parts['cid'],
            'eid': i.parts['eid'],
            'object': entity,
            'paginator': paginator,
            'page': page,
        },
        context_instance=RequestContext(request, processors=[])
    )
