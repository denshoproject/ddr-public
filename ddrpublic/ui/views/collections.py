import logging
logger = logging.getLogger(__name__)

from django.conf import settings
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import Http404, get_object_or_404, render_to_response
from django.template import RequestContext
from django.views.decorators.cache import cache_page

from ui import api
from ui import domain_org
from ui.identifier import Identifier
from ui.models import DEFAULT_SIZE
from ui.views import filter_if_branded
from ui.views import search

# views ----------------------------------------------------------------

@cache_page(settings.CACHE_TIMEOUT)
def list( request ):
    # TODO cache or restrict fields (truncate desc BEFORE caching)
    organizations = []
    repo,org = domain_org(request)
    if repo and org:
        # partner site
        idparts = {'model':'organization', 'repo':repo, 'org':org}
        identifier = Identifier(parts=idparts)
        organization = api.Organization.get(identifier.id)
        collections = api.Organization.children(
            org['id'], request,
            limit=settings.ELASTICSEARCH_MAX_SIZE,
        )
        organizations.append( (org, collections['objects']) )
    else:
        # default site
        orgs = api.Repository.children(repo, request)
        for org in orgs['objects']:
            collections = api.Organization.children(
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
    i = Identifier(id=oid)
    filter_if_branded(request, i)
    collection = api.Collection.get(i.id, request)
    collection['identifier'] = i
    if not collection:
        raise Http404
    organization = api.Organization.get(i.parent_id(stubs=1), request)
    thispage = 1
    pagesize = 10
    paginator = Paginator(
        api.pad_results(
            api.Collection.children(
                i.id,
                request,
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
            'repo': i.parts['repo'],
            'org': i.parts['org'],
            'cid': i.parts['cid'],
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
    i = Identifier(id=oid)
    filter_if_branded(request, i)
    collection = api.Collection.get(i.id, request)
    collection['identifier'] = i
    if not collection:
        raise Http404
    thispage = int(request.GET.get('page', 1))
    pagesize = settings.RESULTS_PER_PAGE
    paginator = Paginator(
        api.pad_results(
            api.Collection.children(
                i.id,
                request,
                limit=pagesize,
                offset=pagesize*(thispage-1),
            ),
            pagesize,
            thispage
        ),
        pagesize
    )
    return render_to_response(
        'ui/collections/children.html',
        {
            'repo': i.parts['repo'],
            'org': i.parts['org'],
            'cid': i.parts['cid'],
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
