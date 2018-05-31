import json
import logging
logger = logging.getLogger(__name__)

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.http import HttpResponsePermanentRedirect
from django.shortcuts import Http404, render

from .. import misc


def index( request ):
    return render(request, 'ui/index.html', {})

def redirect(request):
    """Catch redirects from old archive.densho.org site
    """
    url = '/?archive.densho.org=1'
    return HttpResponsePermanentRedirect(url)

def cite( request ):
    return render(request, 'ui/cite.html', {})

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
    return render(request, 'ui/400.html', {
        'ASSETS_BASE': misc.assets_base(request),
    })

def error403(request):
    return render(request, 'ui/403.html', {
        'ASSETS_BASE': misc.assets_base(request),
    })

def error404(request):
    return render(request, 'ui/404.html', {
        'ASSETS_BASE': misc.assets_base(request),
    })

def error500(request):
    return render(request, 'ui/500.html', {
        'ASSETS_BASE': misc.assets_base(request),
    })
