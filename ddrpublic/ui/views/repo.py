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

def detail( request, repo ):
    hits = elasticsearch.query(
        model='organization',
        query='id:"%s"' % (repo),
        #filters={'id':'ddr-testing-*'},
        #sort=sort
    )
    organizations = elasticsearch.massage_hits( hits )
    return render_to_response(
        'ui/repo/detail.html',
        {
            'repo': repo,
            'organizations': organizations,
        },
        context_instance=RequestContext(request, processors=[])
    )
