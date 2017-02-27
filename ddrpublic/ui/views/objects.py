import logging
logger = logging.getLogger(__name__)

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import Http404, get_object_or_404, render_to_response
from django.template import RequestContext

from ui.identifier import Identifier
from ui.views import repo, organizations, collections, entities, files


def legacy(request, repo, org, cid, eid=None, role=None, sha1=None):
    # TODO this knows too much about structure of ID
    # but then, then old site was like that
    oid = '-'.join([
        part
        for part in [repo, org, cid, eid, role, sha1]
        if part
    ])
    return HttpResponseRedirect(reverse('ui-object-detail', args=[oid]))

def detail(request, oid):
    i = Identifier(id=oid)
    if i.model == 'repository': return repo.detail(request, oid)
    elif i.model == 'organization': return organizations.detail(request, oid)
    elif i.model == 'collection': return collections.detail(request, oid)
    elif i.model == 'entity': return entities.detail(request, oid)
    elif i.model == 'segment': return entities.detail(request, oid)
    elif i.model == 'file': return files.detail(request, oid)
    raise Exception("Could not match ID,model,view.")

def children(request, oid):
    i = Identifier(id=oid)
    if i.model == 'repository': return repo.children(request, oid)
    elif i.model == 'organization': return organizations.children(request, oid)
    elif i.model == 'collection': return collections.children(request, oid)
    elif i.model == 'entity': return entities.children(request, oid)
    elif i.model == 'segment': return entities.children(request, oid)
    elif i.model == 'file': return files.children(request, oid)
    raise Exception("Could not match ID,model,view.")

def nodes(request, oid):
    i = Identifier(id=oid)
    if i.model == 'repository': return repo.nodes(request, oid)
    elif i.model == 'organization': return organizations.nodes(request, oid)
    elif i.model == 'collection': return collections.nodes(request, oid)
    elif i.model == 'entity': return entities.nodes(request, oid)
    elif i.model == 'segment': return entities.nodes(request, oid)
    elif i.model == 'file': return files.nodes(request, oid)
    raise Exception("Could not match ID,model,view.")
