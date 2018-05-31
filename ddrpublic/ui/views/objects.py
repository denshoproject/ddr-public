import logging
logger = logging.getLogger(__name__)

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import Http404, render

from .. import models
from . import repo as repository
from . import organizations, collections, entities, files


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
    o = models._object(request, oid)
    if   o['model'] == 'repository': return repository.detail(request, oid)
    elif o['model'] == 'organization': return organizations.detail(request, oid)
    elif o['model'] == 'collection': return collections.detail(request, oid)
    elif o['model'] == 'entity': return entities.detail(request, oid)
    elif o['model'] == 'segment': return entities.detail(request, oid)
    elif o['model'] == 'file': return files.detail(request, oid)
    raise Exception("Could not match ID,model,view.")

def children(request, oid):
    o = models._object(request, oid)
    if   o['model'] == 'repository': return repository.children(request, oid)
    elif o['model'] == 'organization': return organizations.children(request, oid)
    elif o['model'] == 'collection': return collections.children(request, oid)
    elif o['model'] == 'entity': return entities.children(request, oid)
    elif o['model'] == 'segment': return entities.children(request, oid)
    elif o['model'] == 'file': return files.children(request, oid)
    raise Exception("Could not match ID,model,view.")

def nodes(request, oid):
    o = models._object(request, oid)
    if   o['model'] == 'repository': return repository.nodes(request, oid)
    elif o['model'] == 'organization': return organizations.nodes(request, oid)
    elif o['model'] == 'collection': return collections.nodes(request, oid)
    elif o['model'] == 'entity': return entities.nodes(request, oid)
    elif o['model'] == 'segment': return entities.nodes(request, oid)
    elif o['model'] == 'file': return files.nodes(request, oid)
    raise Exception("Could not match ID,model,view.")
