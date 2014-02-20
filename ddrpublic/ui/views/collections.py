import logging
logger = logging.getLogger(__name__)

from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import Http404, get_object_or_404, render_to_response
from django.template import RequestContext

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
    entities = collection.entities()
    return render_to_response(
        'ui/collections/detail.html',
        {
            'repo': repo,
            'org': org,
            'cid': cid,
            'object': collection,
            'entities': entities,
        },
        context_instance=RequestContext(request, processors=[])
    )
