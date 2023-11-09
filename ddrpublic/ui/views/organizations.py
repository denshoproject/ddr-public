import logging
logger = logging.getLogger(__name__)

from django.conf import settings
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.shortcuts import Http404, redirect, render
from django.urls import reverse

from .. import identifier
from .. import misc
from .. import models
from ..decorators import ui_state


#@cache_page(settings.CACHE_TIMEOUT)
def list( request ):
    repo,org = misc.domain_org(request)
    organizations = [
        models.format_object_detail2(org.to_dict(), request)
        for org in models.Repository.children(repo, request).objects
    ]
    return render(request, 'ui/organizations/list.html', {
        'organizations': organizations,
    })

def detail(request, oid):
    repo,org = misc.domain_org(request)
    organization = models.Organization.get(oid, request)
    ## children
    #collections = models.Organization.children(
    #    organization['id'], request, limit=settings.ELASTICSEARCH_MAX_SIZE,
    #).ordered_dict(
    #    request=request,
    #    format_functions=models.FORMATTERS,
    #    pad=True,
    #)['objects']

    # children/nodes
    thispage = request.GET.get('page', 1)
    pagesize = 5
    offset = models.search_offset(thispage, pagesize)
    children_results = models.Organization.children(
        oid=oid,
        request=request,
        limit=pagesize,
        offset=offset,
    )
    children_paginator = Paginator(
        children_results.ordered_dict(
            request=request,
            format_functions=models.FORMATTERS,
            pad=True,
        )['objects'],
        children_results.page_size,
    )
    children_page = children_paginator.page(children_results.this_page)

    children_page_object_list = children_page.object_list
    #assert 0
    return render(request, 'ui/organizations/detail.html', {
        'repo': repo,
        'organization': organization,
        'children_paginator': children_paginator,
        'children_page': children_page,
        'pagesize': pagesize,
    })

@ui_state
def children( request, oid, role=None ):
    """Lists all direct children of the entity.
    """
    try:
        organization = models._object(request, oid)
    except models.NotFound:
        raise Http404
    # children
    thispage = int(request.GET.get('page', 1))
    pagesize = settings.RESULTS_PER_PAGE
    offset = models.search_offset(thispage, pagesize)
    results = models.Organization.children(
        oid=oid,
        request=request,
        limit=pagesize,
        offset=offset,
    )
    paginator = Paginator(
        results.ordered_dict(
            request=request,
            format_functions=models.FORMATTERS,
            pad=True,
        )['objects'],
        results.page_size,
    )
    page = paginator.page(results.this_page)
    return render(request, 'ui/organizations/children.html', {
        'organization': organization,
        'object': organization,
        'paginator': paginator,
        'page': page,
        'api_url': reverse('ui-api-object-children', args=[oid]),
    })
