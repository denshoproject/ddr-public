from datetime import datetime
import logging
logger = logging.getLogger(__name__)
import os

from django.conf import settings

from ui import git_commit, domain_org, choose_base_template
from ui.forms import SearchForm
from ui.models import Organization


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
        'hide_header_search': False,
        'search_form': SearchForm,
        'time': datetime.now().isoformat(),
        'pid': os.getpid(),
        'host': os.uname()[1],
        'commit': git_commit()[:7],
        'partner': partner,
        'BASE_TEMPLATE': base_template,
    }
