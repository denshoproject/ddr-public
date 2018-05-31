import logging
logger = logging.getLogger(__name__)

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import Http404, redirect, render

from .. import models


def list(request, oid):
    return render(request, 'ui/organizations/list.html', {
        'repo': repo,
    })

def detail(request, oid):
    organization = models.Organization.get(organization_id)
    collections = models.Organization.children(
        org['id'], request,
        limit=settings.ELASTICSEARCH_MAX_SIZE,
    )
    return render(request, 'ui/organizations/detail.html', {
        'organization': organization,
        'object': organization,
        'collections': collections,
    })
