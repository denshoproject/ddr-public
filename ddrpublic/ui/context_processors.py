from datetime import datetime
import logging
logger = logging.getLogger(__name__)
import os

import envoy

from django.conf import settings
from django.contrib.sites.models import RequestSite
from django.template.loader import get_template
from django.template import TemplateDoesNotExist

from ui.forms import SearchForm


def git_commit():
    """Returns the ddr-local repo's most recent Git commit.
    """
    try:
        commit = envoy.run('git log --pretty=format:"%H" -1').std_out
    except:
        commit = 'unknown'
    return commit

def domain_org(request):
    """Match request domain with org
    
    Uses settings.PARTNER_DOMAINS
    TODO cache this in session!
    """
    domain = RequestSite(request).domain
    org = None
    for o,ds in settings.ORG_DOMAINS.iteritems():
        for d in ds:
            if domain == d:
                org = o
    return domain,org

def choose_base_template(org, default='ui/base.html'):
    """Choose base template given the selected org
    
    Looks for an existing base template file for the org;
    Uses default if template for org does not exist.
    
    TODO cache this in session!
    """
    template_name = 'ui/base-%s.html' % org
    try:
        get_template(template_name)
        template = template_name
    except TemplateDoesNotExist:
        template = default
    return template

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
