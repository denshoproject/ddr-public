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

def detail( request, repo, org, cid, eid, role, sha1 ):
    filter_if_branded(request, repo, org)
    identifier = Identifier(url=request.META['PATH_INFO'])
    ffile = File.get(identifier)
    if not ffile:
        raise Http404
    organization = Organization.get(ffile.identifier.organization())
    return render_to_response(
        'ui/files/detail.html',
        {
            'repo': repo,
            'org': org,
            'cid': cid,
            'eid': eid,
            'role': role,
            'sha1': sha1,
            'object': ffile,
            'organization': organization,
        },
        context_instance=RequestContext(request, processors=[])
    )
