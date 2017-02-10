import logging
logger = logging.getLogger(__name__)

from django.conf import settings
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import Http404, get_object_or_404, render_to_response
from django.template import RequestContext

from ui import api
from ui import domain_org
from ui.identifier import Identifier
from ui.models import DEFAULT_SIZE
from ui.views import filter_if_branded


# views ----------------------------------------------------------------

def list( request ):
    # TODO cache or restrict fields (truncate desc BEFORE caching)
    organizations = []
    repo,org = domain_org(request)
    if repo and org:
        # partner site
        idparts = {'model':'organization', 'repo':repo, 'org':org}
        identifier = Identifier(parts=idparts)
        organization = api.ApiOrganization.api_get(identifier.id)
        collections = api.ApiOrganization.api_children(
            org['id'], request,
            limit=settings.ELASTICSEARCH_MAX_SIZE,
        )
        organizations.append( (org, collections['objects']) )
    else:
        # default site
        orgs = api.ApiRepository.api_children(repo, request)
        for org in orgs['objects']:
            collections = api.ApiOrganization.api_children(
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

def detail(request, oid):
    i = Identifier(id=oid)
    filter_if_branded(request, i)
    collection = api.ApiCollection.api_get(i.id, request)
    collection['identifier'] = i
    if not collection:
        raise Http404
    organization = api.ApiOrganization.api_get(i.parent_id(stubs=1), request)
    thispage = 1
    paginator = Paginator(
        api.ApiCollection.api_children(i.id, request)['objects'],
        settings.RESULTS_PER_PAGE
    )
    page = paginator.page(thispage)
    return render_to_response(
        'ui/collections/detail.html',
        {
            'repo': i.parts['repo'],
            'org': i.parts['org'],
            'cid': i.parts['cid'],
            'object': collection,
            'organization': organization,
            'paginator': paginator,
            'page': page,
            'api_url': reverse('ui-api-object', args=[oid]),
        },
        context_instance=RequestContext(request, processors=[])
    )

def children(request, oid):
    """Lists all direct children of the collection.
    """
    i = Identifier(id=oid)
    filter_if_branded(request, i)
    collection = api.ApiCollection.api_get(i.id, request)
    collection['identifier'] = i
    if not collection:
        raise Http404
    thispage = request.GET.get('page', 1)
    paginator = Paginator(
        api.ApiCollection.api_children(i.id, request)['objects'],
        settings.RESULTS_PER_PAGE
    )
    page = paginator.page(thispage)
    return render_to_response(
        'ui/collections/children.html',
        {
            'repo': i.parts['repo'],
            'org': i.parts['org'],
            'cid': i.parts['cid'],
            'object': collection,
            'paginator': paginator,
            'page': page,
            'api_url': reverse('ui-api-object-children', args=[oid]),
        },
        context_instance=RequestContext(request, processors=[])
    )

def nodes(request, oid):
    """Lists all nodes of the collection.
    """
    i = Identifier(id=oid)
    filter_if_branded(request, i)
    collection = Collection.get(i)
    if not collection:
        raise Http404
    thispage = request.GET.get('page', 1)
    files = collection.files(thispage, settings.RESULTS_PER_PAGE)
    paginator = Paginator(files, settings.RESULTS_PER_PAGE)
    page = paginator.page(thispage)
    return render_to_response(
        'ui/collections/nodes.html',
        {
            'repo': i.parts['repo'],
            'org': i.parts['org'],
            'cid': i.parts['cid'],
            'object': collection,
            'paginator': paginator,
            'page': page,
            'api_url': reverse('ui-api-object-nodes', args=[oid]),
        },
        context_instance=RequestContext(request, processors=[])
    )
