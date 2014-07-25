from datetime import datetime
import logging
logger = logging.getLogger(__name__)
import os

from ui import git_commit, domain_org, choose_base_template
from ui.forms import SearchForm


def sitewide(request):
    """Variables that need to be inserted into all templates.
    """
    domain,org = domain_org(request)
    base_template = choose_base_template(org)
    return {
        'request': request,
        'hide_header_search': False,
        'search_form': SearchForm,
        'time': datetime.now().isoformat(),
        'pid': os.getpid(),
        'host': os.uname()[1],
        'commit': git_commit()[:7],
        'domain': domain,
        'org': org,
        'BASE_TEMPLATE': base_template,
    }
