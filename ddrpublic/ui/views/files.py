import logging
logger = logging.getLogger(__name__)

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import Http404, render

from .. import models
from .. import misc


def detail(request, oid):
    try:
        ffile = models._object(request, oid)
    except models.NotFound:
        raise Http404
    misc.filter_if_branded(request, ffile['organization_id'])
    parent = models._object(request, ffile['parent_id'])
    organization = models._object(request, ffile['organization_id'])
    return render(request, 'ui/files/detail.html', {
        'object': ffile,
        'parent': parent,
        'organization': organization,
        'api_url': reverse('ui-api-object', args=[oid]),
    })
