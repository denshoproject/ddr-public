import logging
logger = logging.getLogger(__name__)

from django.conf import settings
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import Http404, get_object_or_404, render_to_response
from django.template import RequestContext

from ui import domain_org
from ui.identifier import Identifier
from ui.models import Repository, Organization, Collection, Entity, File
from ui.models import DEFAULT_SIZE
from ui.views import filter_if_branded
    

# views ----------------------------------------------------------------

def list( request ):
    organizations = []
    repo,org = domain_org(request)
    if repo and org:
        # partner site
        idparts = {'model':'organization', 'repo':repo, 'org':org}
        identifier = Identifier(parts=idparts)
        organization = Organization.get(identifier)
        collections = organization.children(1, 1000000)
        organizations.append( (organization,collections) )
    else:
        # default site
        idparts = {'model':'repository', 'repo':repo}
        identifier = Identifier(parts=idparts)
        repository = Repository.get(identifier)
        organizations = []
        for org in repository.children():
            collections = org.children(1, 1000000)
            organizations.append( (org,collections) )
    return render_to_response(
        'ui/collections.html',
        {
            'organizations': organizations,
        },
        context_instance=RequestContext(request, processors=[])
    )

def detail( request, repo, org, cid ):
    filter_if_branded(request, repo, org)
    identifier = Identifier(url=request.META['PATH_INFO'])
    collection = Collection.get(identifier)
    if not collection:
        raise Http404
    organization = collection.parent()
    thispage = 1
    objects = collection.children(thispage, DEFAULT_SIZE)
    paginator = Paginator(objects, DEFAULT_SIZE)
    page = paginator.page(thispage)
    return render_to_response(
        'ui/collections/detail.html',
        {
            'repo': repo,
            'org': org,
            'cid': cid,
            'object': collection,
            'organization': organization,
            'paginator': paginator,
            'page': page,
        },
        context_instance=RequestContext(request, processors=[])
    )

def entities( request, repo, org, cid ):
    filter_if_branded(request, repo, org)
    idparts = {'model':'collection', 'repo':repo, 'org':org, 'cid':cid}
    identifier = Identifier(parts=idparts)
    collection = Collection.get(identifier)
    if not collection:
        raise Http404
    thispage = request.GET.get('page', 1)
    objects = collection.children(thispage, settings.RESULTS_PER_PAGE)
    paginator = Paginator(objects, settings.RESULTS_PER_PAGE)
    page = paginator.page(thispage)
    return render_to_response(
        'ui/collections/entities.html',
        {
            'repo': repo,
            'org': org,
            'cid': cid,
            'object': collection,
            'paginator': paginator,
            'page': page,
        },
        context_instance=RequestContext(request, processors=[])
    )

def files( request, repo, org, cid ):
    filter_if_branded(request, repo, org)
    idparts = {'model':'collection', 'repo':repo, 'org':org, 'cid':cid}
    identifier = Identifier(parts=idparts)
    collection = Collection.get(identifier)
    if not collection:
        raise Http404
    thispage = request.GET.get('page', 1)
    files = collection.files(thispage, settings.RESULTS_PER_PAGE)
    paginator = Paginator(files, settings.RESULTS_PER_PAGE)
    page = paginator.page(thispage)
    return render_to_response(
        'ui/collections/files.html',
        {
            'repo': repo,
            'org': org,
            'cid': cid,
            'object': collection,
            'paginator': paginator,
            'page': page,
        },
        context_instance=RequestContext(request, processors=[])
    )
