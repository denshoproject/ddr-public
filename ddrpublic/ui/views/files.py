import logging
logger = logging.getLogger(__name__)

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import Http404, get_object_or_404, render_to_response
from django.template import RequestContext

from ui import api
from ui.identifier import Identifier
from ui.views import filter_if_branded


# views ----------------------------------------------------------------

def detail(request, oid):
    i = Identifier(id=oid)
    filter_if_branded(request, i)
    try:
        ffile = api.File.get(i.id, request)
    except api.NotFound:
        raise Http404
    ffile['identifier'] = i
    parent = api.Entity.get(i.parent_id(), request)
    organization = api.Organization.get(i.organization().id, request)
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
            'api_url': reverse('ui-api-object', args=[oid]),
        },
        context_instance=RequestContext(request, processors=[])
    )
