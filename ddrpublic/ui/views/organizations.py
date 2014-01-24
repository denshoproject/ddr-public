import logging
logger = logging.getLogger(__name__)

from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import Http404, get_object_or_404, render_to_response
from django.template import RequestContext

import elasticsearch


# views ----------------------------------------------------------------

def list( request, repo ):
    return render_to_response(
        'ui/organizations/list.html',
        {
            'repo': repo,
        },
        context_instance=RequestContext(request, processors=[])
    )

def detail( request, repo, org ):
    #organization_id='%s-%s-%s' % (repo, org, cid)
    #organization = elasticsearch.get(
    #    index='ddr',
    #    model='organization',
    #    id=organization_id,
    #)
    hits = elasticsearch.query(
        model='collection',
        query='id:"%s-%s"' % (repo, org),
        #filters={'id':'ddr-testing-*'},
        #sort=sort
    )
    collections = elasticsearch.massage_hits( hits )
    return render_to_response(
        'ui/organizations/detail.html',
        {
            'repo': repo,
            'org': org,
            'collections': collections,
        },
        context_instance=RequestContext(request, processors=[])
    )
