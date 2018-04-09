import logging
logger = logging.getLogger(__name__)

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import Http404, get_object_or_404, render_to_response
from django.template import RequestContext

from ui import api
from ui.views import filter_if_branded


# views ----------------------------------------------------------------

def detail(request, oid):
    try:
        ffile = api._object(request, oid)
    except api.NotFound:
        raise Http404
    filter_if_branded(request, ffile['organization_id'])
    parent = api._object(request, ffile['parent_id'])
    organization = api._object(request, ffile['organization_id'])
    return render_to_response(
        'ui/files/detail.html',
        {
            'object': ffile,
            'parent': parent,
            'organization': organization,
            'api_url': reverse('ui-api-object', args=[oid]),
        },
        context_instance=RequestContext(request, processors=[])
    )
