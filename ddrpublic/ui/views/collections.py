import logging
logger = logging.getLogger(__name__)

from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import Http404, get_object_or_404, render_to_response
from django.template import RequestContext

from DDR import elasticsearch
from ui.models import Repository, Organization, Collection, Entity, File


# views ----------------------------------------------------------------

def list( request ):
    organizations = Repository.get('ddr').organizations()
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
    return render_to_response(
        'ui/collections/detail.html',
        {
            'repo': repo,
            'org': org,
            'cid': cid,
            'object': collection,
            'entities': collection.entities(),
        },
        context_instance=RequestContext(request, processors=[])
    )

def entities( request, repo, org, cid ):
    collection = Collection.get(repo, org, cid)
    if not collection:
        raise Http404
    paginator = Paginator(collection.entities(), settings.RESULTS_PER_PAGE)
    page = paginator.page(request.GET.get('page', 1))
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
    paginator = Paginator(collection.files(), settings.RESULTS_PER_PAGE)
    page = paginator.page(request.GET.get('page', 1))
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
