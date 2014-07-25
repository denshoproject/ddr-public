import envoy

from django.conf import settings
from django.contrib.sites.models import RequestSite
from django.template.loader import get_template
from django.template import TemplateDoesNotExist


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
    
    Uses settings.ORG_DOMAINS
    NOTE: "org" is referred to as "partner" in views to avoid
    confusion with the 'org' argument.
    
    @param request
    @returns: organization keyword or None
    """
    domain = RequestSite(request).domain
    org = None
    for o,ds in settings.ORG_DOMAINS.iteritems():
        for d in ds:
            if domain == d:
                org = o
    return org

def choose_base_template(org, default='ui/base.html'):
    """Choose base template given the selected org
    
    Looks for an existing base template file for the org;
    Uses default if template for org does not exist.
    
    TODO cache this in session!
    
    @param org
    @param default
    @returns: template name (e.g. 'ui/base.html')
    """
    template_name = 'ui/base-%s.html' % org
    try:
        get_template(template_name)
        template = template_name
    except TemplateDoesNotExist:
        template = default
    return template
