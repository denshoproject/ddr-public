import logging
logger = logging.getLogger(__name__)

from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import Http404, get_object_or_404, render_to_response
from django.template import RequestContext


# views ----------------------------------------------------------------

def list( request, repo ):
    return render_to_response(
        'ui/organizations/list.html',
        {
            'repo': repo,
        },
        context_instance=RequestContext(request, processors=[])
    )

def detail( request, repo, org ):
    return render_to_response(
        'ui/organizations/detail.html',
        {
            'repo': repo,
            'org': org,
        },
        context_instance=RequestContext(request, processors=[])
    )