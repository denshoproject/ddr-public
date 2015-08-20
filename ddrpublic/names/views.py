from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404, redirect, render_to_response
from django.template import RequestContext
from django.views.decorators.http import require_http_methods

from names.forms import SearchForm
from names import models


@require_http_methods(['GET',])
def index(request, template_name='names/index.html'):
    if request.method == 'POST':
        form = SearchForm(request.POST)
        if form.is_valid():
            assert False
    else:
        form = SearchForm()
    return render_to_response(
        template_name,
        {
            'form': form,
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
