from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404, redirect, render_to_response
from django.template import RequestContext
from django.views.decorators.http import require_http_methods


@require_http_methods(['GET',])
def index(request, template_name='names/index.html'):
    return render_to_response(
        template_name,
        {
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
