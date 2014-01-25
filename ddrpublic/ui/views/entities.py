import logging
logger = logging.getLogger(__name__)

from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import Http404, get_object_or_404, render_to_response
from django.template import RequestContext

from ui.models import Repository, Organization, Collection, Entity, File


# views ----------------------------------------------------------------

def list( request, repo, org, cid ):
    return render_to_response(
        'ui/entities/list.html',
        {
            'repo': repo,
            'org': org,
            'cid': cid,
        },
        context_instance=RequestContext(request, processors=[])
    )

def detail( request, repo, org, cid, eid ):
    entity = Entity.get(repo, org, cid, eid)
    if not entity:
        raise Http404
    files = entity.files()
    return render_to_response(
        'ui/entities/detail.html',
        {
            'repo': repo,
            'org': org,
            'cid': cid,
            'eid': eid,
            'object': entity,
            'files': files,
        },
        context_instance=RequestContext(request, processors=[])
    )
