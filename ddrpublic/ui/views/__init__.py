import json
import logging
logger = logging.getLogger(__name__)

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import Http404, get_object_or_404, render_to_response
from django.template import RequestContext

from ui import assets_base, domain_org


# helpers --------------------------------------------------------------

def filter_if_branded(request, oidentifier):
    pass
    #partner_repo,partner_org = domain_org(request)
    #if partner_repo and partner_org and (org != partner_org):
    #    raise Http404

# views ----------------------------------------------------------------

def index( request ):
    return render_to_response(
        'ui/index.html',
        {},
        context_instance=RequestContext(request, processors=[])
    )

def cite( request ):
    return render_to_response(
        'ui/cite.html',
        {},
        context_instance=RequestContext(request, processors=[])
    )

def choose_tab(request):
    """Remember which results view type between pages.
    """
    TAB_CHOICES = [
        'gallery',
        'list',
    ]
    if request.GET.get('tab') in TAB_CHOICES:
        request.session['tab'] = request.GET['tab']
        return HttpResponse(
            json.dumps({
                'selected': request.GET['tab'],
            }),
            content_type="application/json"
        )
    else:
        raise Http404

def error400(request):
    return render_to_response(
        'ui/400.html',
        {
            'ASSETS_BASE': assets_base(request),
        },
        context_instance=RequestContext(request, processors=[])
    )

def error403(request):
    return render_to_response(
        'ui/403.html',
        {
            'ASSETS_BASE': assets_base(request),
        },
        context_instance=RequestContext(request, processors=[])
    )

def error404(request):
    return render_to_response(
        'ui/404.html',
        {
            'ASSETS_BASE': assets_base(request),
        },
        context_instance=RequestContext(request, processors=[])
    )

def error500(request):
    return render_to_response(
        'ui/500.html',
        {
            'ASSETS_BASE': assets_base(request),
        },
        context_instance=RequestContext(request, processors=[])
    )
