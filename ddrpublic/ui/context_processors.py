from datetime import datetime
import logging
logger = logging.getLogger(__name__)
import os

from django.conf import settings
from django.core.cache import cache

from ui import assets_base, domain_org, choose_base_template
from ui import dvcs
from ui.docstore import aliases_indices
from ui.forms import SearchForm

# Latest commits so visible in error pages and in page footers.
COMMITS_DDRPUBLIC = dvcs.latest_commit(os.path.dirname(__file__))
COMMITS_TEXT = '\n'.join([
    'pub: %s' % COMMITS_DDRPUBLIC,
])


def docstore_info():
    """
    {
    'hosts': [{'host': '192.168.56.1', 'port': '9200'}],
    'aliases': [{'index': u'ddrpub-20170321', 'alias': u'ddrpublic-dev'}]
    }
    """
    key = 'hosts-aliases-indices'
    cached = cache.get(key)
    if not cached:

        text = '\n'.join([
            '%s -> %s' % (x['alias'], x['index'])
            for x in aliases_indices()
        ])
        
        cached = text
        cache.set(key, cached, settings.CACHE_TIMEOUT)
    return cached

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
        'docstore_hosts': settings.DOCSTORE_HOSTS[0]['host'],
        'docstore_index': settings.DOCSTORE_INDEX,
        'namesdb_hosts': settings.NAMESDB_DOCSTORE_HOSTS[0]['host'],
        'namesdb_index': settings.NAMESDB_DOCSTORE_INDEX,
        'ASSETS_BASE': assets_base(request),
        'hide_header_search': False,
        'search_form': SearchForm,
        'partner': partner,
        'tab': request.session.get('tab', 'gallery'),
        'BASE_TEMPLATE': base_template,
        'ENCYC_BASE': settings.ENCYC_BASE,
        'MEDIA_URL': settings.MEDIA_URL,
        'ASSETS_VERSION': settings.ASSETS_VERSION,
        'MISSING_IMG': settings.MISSING_IMG,
        'DOWNLOAD_URL': settings.DOWNLOAD_URL,
        'STATIC_URL': settings.STATIC_URL,
    }
