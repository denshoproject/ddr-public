import logging
logger = logging.getLogger(__name__)

from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import Http404, get_object_or_404, render_to_response
from django.template import RequestContext

from ui.models import Repository, Organization, Collection, Entity, File
from ui.models import DEFAULT_SIZE


# views ----------------------------------------------------------------

def list( request ):
    organizations = []
    for org in Repository.get('ddr').organizations():
        collections = org.collections(1, 1000000)
        organizations.append( (org,collections) )
    return render_to_response(
        'ui/collections.html',
        {
            'organizations': organizations,
        },
        context_instance=RequestContext(request, processors=[])
    )

def detail( request, repo, org, cid ):
    collection = Collection.get(repo, org, cid)
    if not collection:
        raise Http404
    organization = Organization.get(collection.repo, collection.org)
    thispage = 1
    objects = collection.entities(thispage, DEFAULT_SIZE)
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
    collection = Collection.get(repo, org, cid)
    if not collection:
        raise Http404
    thispage = request.GET.get('page', 1)
    objects = collection.entities(thispage, settings.RESULTS_PER_PAGE)
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
    collection = Collection.get(repo, org, cid)
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
