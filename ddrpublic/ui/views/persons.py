import logging
logger = logging.getLogger(__name__)

from django.conf import settings
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.shortcuts import Http404, redirect, render
from django.urls import reverse

from elastictools.search import limit_offset
from .. import models


#@cache_page(settings.CACHE_TIMEOUT)
def detail(request, naan, noid):
    nr_id = f"{naan}/{noid}"
    try:
        person_url,person_status_code,person = models.person(request, nr_id)
    except models.NotFound:
        raise Http404
    if not person_status_code == 200:
        assert False
    limit,offset = limit_offset(request, settings.RESULTS_PER_PAGE)
    results = models.person_objects(
        request,
        nr_id,
        limit,
        offset,
    )
    paginator = Paginator(
        results.ordered_dict(
            request=request,
            format_functions=models.FORMATTERS,
            pad=True,
        )['objects'],
        results.page_size,
    )
    page = paginator.page(results.this_page)
    return render(request, 'ui/persons/detail.html', {
        'naan': naan,
        'noid': noid,
        'person': person,
        'person_url': person_url,
        'person_status_code': person_status_code,
        'paginator': paginator,
        'page': page,
        'api_url': reverse('ui-api-nrid-detail', args=[naan,noid]),
    })
