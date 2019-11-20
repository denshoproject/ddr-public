import logging
logger = logging.getLogger(__name__)

from django.conf import settings
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.shortcuts import Http404, render
from django.views.decorators.cache import cache_page

from .. import models
from .. import misc
from ..decorators import ui_state


@cache_page(settings.CACHE_TIMEOUT)
def list( request ):
    # TODO cache or restrict fields (truncate desc BEFORE caching)
    organizations = []
    repo,org = misc.domain_org(request)
    if repo and org:
        # partner site
        organization_id = '%s-%s' % (repo,org) # TODO relies on knowledge of ID structure!
        collections = models.Organization.children(
            org.id, request, limit=settings.ELASTICSEARCH_MAX_SIZE,
        )
        org_formatted = models.format_object_detail2(org.to_dict(), request)
        objects = collections.ordered_dict(
            request=request,
            format_functions=models.FORMATTERS,
            pad=True,
        )['objects']
        organizations.append( (org_formatted,objects) )
    else:
        # default site
        orgs = models.Repository.children(repo, request)
        for org in orgs.objects:
            collections = models.Organization.children(
                org.id, request, limit=settings.ELASTICSEARCH_MAX_SIZE,
            )
            org_formatted = models.format_object_detail2(org.to_dict(), request)
            objects = collections.ordered_dict(
                request=request,
                format_functions=models.FORMATTERS,
                pad=True,
            )['objects']
            organizations.append( (org_formatted,objects) )
    return render(request, 'ui/collections.html', {
        'organizations': organizations,
    })

@cache_page(settings.CACHE_TIMEOUT)
def detail(request, oid):
    try:
        collection = models._object(request, oid)
    except models.NotFound:
        raise Http404
    misc.filter_if_branded(request, collection['organization_id'])
    # TODO fix this
    try:
        organization = models._object(request, collection['organization_id'])
    except:
        organization = None
    thispage = 1
    pagesize = 10
    results = models.Collection.children(
        oid=oid,
        request=request,
        limit=pagesize,
        offset=0,
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
    return render(request, 'ui/collections/detail.html', {
        'object': collection,
        'organization': organization,
        'paginator': paginator,
        'page': page,
        'api_url': reverse('ui-api-object', args=[oid]),
    })

@ui_state
def children(request, oid):
    """Lists all direct children of the collection.
    """
    try:
        collection = models._object(request, oid)
    except models.NotFound:
        raise Http404
    misc.filter_if_branded(request, collection['organization_id'])
    thispage = int(request.GET.get('page', 1))
    pagesize = settings.RESULTS_PER_PAGE
    offset = models.search_offset(thispage, pagesize)
    results = models.Collection.children(
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
    return render(request, 'ui/collections/children.html', {
        'object': collection,
        'paginator': paginator,
        'page': page,
        'api_url': reverse('ui-api-object-children', args=[oid]),
    })

@ui_state
def nodes(request, oid):
    """Lists all nodes of the collection.
    """
    raise Exception('no longer implemented')
