import logging
logger = logging.getLogger(__name__)

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import Http404, get_object_or_404, redirect, render_to_response
from django.template import RequestContext

from ui import api


# views ----------------------------------------------------------------

def list(request, oid):
    return render_to_response(
        'ui/organizations/list.html',
        {
            'repo': repo,
        },
        context_instance=RequestContext(request, processors=[])
    )

def detail(request, oid):
    organization = api.Organization.get(organization_id)
    collections = api.Organization.children(
        org['id'], request,
        limit=settings.ELASTICSEARCH_MAX_SIZE,
    )
    return render_to_response(
        'ui/organizations/detail.html',
        {
            'organization': organization,
            'object': organization,
            'collections': collections,
        },
        context_instance=RequestContext(request, processors=[])
    )
