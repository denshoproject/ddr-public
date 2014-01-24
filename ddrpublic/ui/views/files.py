import logging
logger = logging.getLogger(__name__)

from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import Http404, get_object_or_404, render_to_response
from django.template import RequestContext


# views ----------------------------------------------------------------

def list( request, repo, org, cid, eid ):
    return render_to_response(
        'ui/files/list.html',
        {
            'repo': repo,
            'org': org,
            'cid': cid,
            'eid': eid,
        },
        context_instance=RequestContext(request, processors=[])
    )

def detail( request, repo, org, cid, eid, role, sha1 ):
    return render_to_response(
        'ui/files/detail.html',
        {
            'repo': repo,
            'org': org,
            'cid': cid,
            'eid': eid,
            'role': role,
            'sha1': sha1,
        },
        context_instance=RequestContext(request, processors=[])
    )
