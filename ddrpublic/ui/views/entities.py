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

def detail( request, repo, org, cid, eid ):
    filter_if_branded(request, repo, org)
    identifier = Identifier(url=request.META['PATH_INFO'])
    entity = Entity.get(identifier)
    if not entity:
        raise Http404
    organization = Organization.get(entity.identifier.organization())
    thispage = 1
    objects = entity.children(thispage, DEFAULT_SIZE)
    paginator = Paginator(objects, DEFAULT_SIZE)
    page = paginator.page(thispage)
    return render_to_response(
        'ui/entities/detail.html',
        {
            'repo': repo,
            'org': org,
            'cid': cid,
            'eid': eid,
            'object': entity,
            'organization': organization,
            'paginator': paginator,
            'page': page,
        },
        context_instance=RequestContext(request, processors=[])
    )

def files( request, repo, org, cid, eid, role=None ):
    """Lists all the files in an entity.
    """
    filter_if_branded(request, repo, org)
    idparts = {'model':'entity', 'repo':repo, 'org':org, 'cid':cid, 'eid':eid}
    identifier = Identifier(parts=idparts)
    entity = Entity.get(identifier)
    crumbs = entity.identifier.breadcrumbs()
    assert False
    if not entity:
        raise Http404
    thispage = request.GET.get('page', 1)
    objects = entity.children(thispage, settings.RESULTS_PER_PAGE)
    paginator = Paginator(objects, settings.RESULTS_PER_PAGE)
    page = paginator.page(thispage)
    return render_to_response(
        'ui/entities/files.html',
        {
            'repo': repo,
            'org': org,
            'cid': cid,
            'eid': eid,
            'object': entity,
            'paginator': paginator,
            'page': page,
        },
        context_instance=RequestContext(request, processors=[])
    )
