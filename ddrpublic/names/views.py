import json

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404, redirect, render_to_response
from django.template import RequestContext
from django.views.decorators.http import require_http_methods

from names.forms import SearchForm
from names import models

HOSTS = settings.NAMESDB_DOCSTORE_HOSTS
INDEX = models.set_hosts_index(HOSTS, settings.NAMESDB_DOCSTORE_INDEX)


@require_http_methods(['GET',])
def index(request, template_name='names/index.html'):
    body = None
    records = []
    if 'query' in request.GET:
        form = SearchForm(request.GET, hosts=HOSTS, index=INDEX)
        if form.is_valid():
            filters = form.cleaned_data
            query = filters.pop('query')
            body,records = models.search(
                HOSTS, INDEX,
                query=query,
                filters=filters,
            )
            if body:
                body = json.dumps(body, indent=4, separators=(',', ': '), sort_keys=True)
    else:
        form = SearchForm(hosts=HOSTS, index=INDEX)
    return render_to_response(
        template_name,
        {
            'form': form,
            'body': body,
            'records': records,
        },
        context_instance=RequestContext(request)
    )

@require_http_methods(['GET',])
def detail(request, template_name='names/detail.html'):
    return render_to_response(
        template_name,
        {
        },
        context_instance=RequestContext(request)
    )
