import logging
logger = logging.getLogger(__name__)

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import Http404, get_object_or_404, redirect, render_to_response
from django.template import RequestContext

from ui.identifier import Identifier
from ui.models import Repository, Organization, Collection, Entity, File


# views ----------------------------------------------------------------

def detail( request, oid ):
    #i = Identifier(id=oid)
    #repository = Repository.get(i)
    #organizations = repository.children()
    #return render_to_response(
    #    'ui/repo/detail.html',
    #    {
    #        'repo': i.parts['repo'],
    #        'repository': repository,
    #        'organizations': organizations,
    #    },
    #    context_instance=RequestContext(request, processors=[])
    #)
    return redirect('ui-collections-list')
