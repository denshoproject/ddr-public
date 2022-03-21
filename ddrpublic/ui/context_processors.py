from datetime import datetime
import logging
logger = logging.getLogger(__name__)
import os

from django.conf import settings
from django.core.cache import cache

from ui import dvcs
from ui.forms import SearchForm
from ui.misc import assets_base, domain_org, choose_base_template

# Latest commits so visible in error pages and in page footers.
COMMITS_DDRPUBLIC = dvcs.latest_commit(os.path.dirname(__file__))
COMMITS_TEXT = '\n'.join([
    'pub: %s' % COMMITS_DDRPUBLIC,
])


def sitewide(request):
    """Variables that need to be inserted into all templates.
    """
    from_oldsite = False
    if request.GET.get('archive.densho.org'):
        from_oldsite = True
    repo,org = domain_org(request)
    if repo and org:
        #partner = Organization.get(repo, org)
        pass
    else:
        partner = None
    base_template = request.session.get('base_template', choose_base_template(org))
    return {
        'request': request,
        'time': datetime.now().isoformat(),
        'pid': os.getpid(),
        'host': os.uname()[1],
        'commits': COMMITS_TEXT,
        'version': settings.VERSION,
        'packages': settings.PACKAGES,
        'docstore_hosts': settings.DOCSTORE_HOST,
        'namesdb_hosts': settings.NAMESDB_DOCSTORE_HOST,
        'ddrpublic_cluster': settings.DOCSTORE_CLUSTER,
        'namesdb_cluster': settings.NAMESDB_CLUSTER,
        'ASSETS_BASE': assets_base(request),
        'hide_header_search': False,
        'search_form': SearchForm,
        'partner': partner,
        'liststyle': request.session.get('liststyle', 'gallery'),
        'tab': request.session.get('liststyle', 'gallery'),
        'site_msg_text': settings.SITE_MSG_TEXT,
        'BASE_TEMPLATE': base_template,
        'ENCYC_BASE': settings.ENCYC_BASE,
        'MEDIA_URL': settings.MEDIA_URL,
        'ASSETS_VERSION': settings.ASSETS_VERSION,
        'MISSING_IMG': settings.MISSING_IMG,
        'DOWNLOAD_URL': settings.DOWNLOAD_URL,
        'STATIC_URL': settings.STATIC_URL,
    }
