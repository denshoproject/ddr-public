from datetime import datetime
import logging
logger = logging.getLogger(__name__)
import os

from django.conf import settings

from ui import git_commit, domain_org, choose_base_template
from ui.forms import SearchForm
from ui.models import Organization


def assets_base(request):
    """Return HTTP protocol (http,https), domain, and assets base URL
    The purpose of this is to deliver all assets in the same HTTP protocol
    so as to not generate mixed content messages when in HTTPS.
    Starting assets URLs with double slashes (e.g. "//assets/...") is supposed
    to do the same thing but doesn't work in local dev e.g. with an IP address
    and no domain name.
    """
    return '%s://%s/assets/%s' % (
        request.META.get('HTTP_X_FORWARDED_PROTO', 'http'),
        request.META.get('HTTP_HOST', 'ddr.densho.org'),
        settings.ASSETS_VERSION,
    )

def sitewide(request):
    """Variables that need to be inserted into all templates.
    """
    repo,org = domain_org(request)
    if repo and org:
        partner = Organization.get(repo, org)
    else:
        partner = None
    base_template = request.session.get('base_template', choose_base_template(org))
    return {
        'request': request,
        'ASSETS_BASE': assets_base(request),
        'hide_header_search': False,
        'search_form': SearchForm,
        'time': datetime.now().isoformat(),
        'pid': os.getpid(),
        'host': os.uname()[1],
        'commit': git_commit(),
        'partner': partner,
        'tab': request.session.get('tab', 'gallery'),
        'BASE_TEMPLATE': base_template,
        'ENCYC_BASE': settings.ENCYC_BASE,
        'MEDIA_URL': settings.MEDIA_URL,
        'ASSETS_VERSION': settings.ASSETS_VERSION,
        'MISSING_IMG': settings.MISSING_IMG,
        'DOWNLOAD_URL': settings.DOWNLOAD_URL,
        'STATIC_URL': settings.STATIC_URL,
        'DOCSTORE_HOSTS': settings.DOCSTORE_HOSTS,
        'DOCSTORE_INDEX': settings.DOCSTORE_INDEX,
    }
