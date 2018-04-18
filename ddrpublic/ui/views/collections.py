import logging
logger = logging.getLogger(__name__)

from django.conf import settings
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import Http404, get_object_or_404, render_to_response
from django.template import RequestContext
from django.views.decorators.cache import cache_page

from ui import domain_org
from ui import models
from ui.views import filter_if_branded

# views ----------------------------------------------------------------

@cache_page(settings.CACHE_TIMEOUT)
def list( request ):
    # TODO cache or restrict fields (truncate desc BEFORE caching)
    organizations = []
    repo,org = domain_org(request)
    if repo and org:
        # partner site
        organization_id = '%s-%s' % (repo,org) # TODO relies on knowledge of ID structure!
        organization = models.Organization.get(organization_id)
        collections = models.Organization.children(
            org['id'], request,
            limit=settings.ELASTICSEARCH_MAX_SIZE,
        )
        organizations.append( (org, collections['objects']) )
    else:
        # default site
        orgs = models.Repository.children(repo, request)
        for org in orgs['objects']:
            collections = models.Organization.children(
                org['id'], request,
                limit=settings.ELASTICSEARCH_MAX_SIZE,
            )
            organizations.append( (org, collections['objects']) )
    return render_to_response(
        'ui/collections.html',
        {
            'organizations': organizations,
        },
        context_instance=RequestContext(request, processors=[])
    )

@cache_page(settings.CACHE_TIMEOUT)
def detail(request, oid):
    try:
        collection = models._object(request, oid)
    except models.NotFound:
        raise Http404
    filter_if_branded(request, collection['organization_id'])
    # TODO fix this
    try:
        organization = models._object(request, collection['organization_id'])
    except:
        organization = None
    thispage = 1
    pagesize = 10
    paginator = Paginator(
        models.pad_results(
            models._object_children(
                document=collection,
                request=request,
                limit=pagesize,
                offset=0,
            ),
            pagesize,
            thispage
        ),
        pagesize
    )
    return render_to_response(
        'ui/collections/detail.html',
        {
            'object': collection,
            'organization': organization,
            'paginator': paginator,
            'page': paginator.page(thispage),
            'api_url': reverse('ui-api-object', args=[oid]),
        },
        context_instance=RequestContext(request, processors=[])
    )

def children(request, oid):
    """Lists all direct children of the collection.
    """
    try:
        collection = models._object(request, oid)
    except models.NotFound:
        raise Http404
    filter_if_branded(request, collection['organization_id'])
    thispage = int(request.GET.get('page', 1))
    pagesize = settings.RESULTS_PER_PAGE
    offset = models.search_offset(thispage, pagesize)
    paginator = Paginator(
        models.pad_results(
            models._object_children(
                document=collection,
                request=request,
                limit=pagesize,
                offset=0,
            ),
            pagesize,
            thispage
        ),
        pagesize
    )
    return render_to_response(
        'ui/collections/children.html',
        {
            'object': collection,
            'paginator': paginator,
            'page': paginator.page(thispage),
            'api_url': reverse('ui-api-object-children', args=[oid]),
        },
        context_instance=RequestContext(request, processors=[])
    )

def nodes(request, oid):
    """Lists all nodes of the collection.
    """
    raise Exception('no longer implemented')
