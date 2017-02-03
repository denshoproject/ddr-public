# stub

import logging
logger = logging.getLogger(__name__)

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import Http404, get_object_or_404, redirect, render_to_response
from django.template import RequestContext

from ui.identifier import Identifier
from ui.models import Repository, Organization, Collection, Entity, File


# views ----------------------------------------------------------------

def list(request, oid):
    return render_to_response(
        'ui/narrators/list.html',
        {
#            'repo': repo,
        },
        context_instance=RequestContext(request, processors=[])
    )

def detail(request, oid):
#    i = Identifier(id=oid)
#    organization = Organization.get(i)
#    collections = organization.children()
    return render_to_response(
        'ui/narrators/detail.html',
        {
#            'repo': i.parts['repo'],
#            'org': i.parts['org'],
#            'organization': organization,
#            'object': organization,
#            'collections': collections,
        },
        context_instance=RequestContext(request, processors=[])
    )
