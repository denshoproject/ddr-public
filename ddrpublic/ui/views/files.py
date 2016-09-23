import logging
logger = logging.getLogger(__name__)

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import Http404, get_object_or_404, render_to_response
from django.template import RequestContext

from ui.identifier import Identifier
from ui.models import Repository, Organization, Collection, Entity, File
from ui.views import filter_if_branded


# views ----------------------------------------------------------------

def detail(request, oid):
    i = Identifier(id=oid)
    filter_if_branded(request, i)
    ffile = File.get(i)
    if not ffile:
        raise Http404
    parent = ffile.parent()
    organization = Organization.get(ffile.identifier.organization())
    return render_to_response(
        'ui/files/detail.html',
        {
            'repo': i.parts['repo'],
            'org': i.parts['org'],
            'cid': i.parts['cid'],
            'eid': i.parts['eid'],
            'role': i.parts['role'],
            'sha1': i.parts['sha1'],
            'object': ffile,
            'parent': parent,
            'organization': organization,
        },
        context_instance=RequestContext(request, processors=[])
    )
