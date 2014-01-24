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

def list( request, repo, org, cid ):
    return render_to_response(
        'ui/entities/list.html',
        {
            'repo': repo,
            'org': org,
            'cid': cid,
        },
        context_instance=RequestContext(request, processors=[])
    )

def detail( request, repo, org, cid, eid ):
    entity_id='%s-%s-%s-%s' % (repo, org, cid, eid)
    get = elasticsearch.get(
        index='ddr',
        model='entity',
        id=entity_id,
    )
    obj = []
    for field in get:
        for k,v in field.iteritems():
            obj.append((k,v))
    hits = elasticsearch.query(
        model='file',
        query='id:"%s-%s-%s-%s"' % (repo, org, cid, eid),
    )
    files = elasticsearch.massage_hits( hits )
    return render_to_response(
        'ui/entities/detail.html',
        {
            'repo': repo,
            'org': org,
            'cid': cid,
            'eid': eid,
            'entity': obj,
            'files': files,
        },
        context_instance=RequestContext(request, processors=[])
    )
