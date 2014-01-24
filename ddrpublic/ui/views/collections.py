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

def list( request, repo, org ):
    return render_to_response(
        'ui/collections/list.html',
        {
            'repo': repo,
            'org': org,
        },
        context_instance=RequestContext(request, processors=[])
    )

def detail( request, repo, org, cid ):
    collection_id='%s-%s-%s' % (repo, org, cid)
    get = elasticsearch.get(
        index='ddr',
        model='collection',
        id=collection_id,
    )
    obj = []
    for field in get:
        for k,v in field.iteritems():
            obj.append((k,v))
    entities = elasticsearch.massage_hits(
        elasticsearch.query(
            model='entity',
            query='id:"%s-%s-%s"' % (repo, org, cid),
        )
    )
    return render_to_response(
        'ui/collections/detail.html',
        {
            'repo': repo,
            'org': org,
            'cid': cid,
            'collection': obj,
            'entities': entities,
        },
        context_instance=RequestContext(request, processors=[])
    )
