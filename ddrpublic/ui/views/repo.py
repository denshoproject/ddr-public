import logging
logger = logging.getLogger(__name__)

from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.template import RequestContext
from django.urls import reverse

from .. import misc
from .. import models


def detail( request, oid ):
    return redirect('ui-object-children', 'ddr')

#@cache_page(settings.CACHE_TIMEOUT)
def children(request, oid='ddr'):
    repo,org = misc.domain_org(request)
    organizations = [
        models.format_object_detail2(org.to_dict(), request)
        for org in models.Repository.children(repo, request).objects
    ]
    return render(request, 'ui/repo/children.html', {
        'organizations': organizations,
    })
