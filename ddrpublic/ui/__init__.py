import envoy

from django.conf import settings
from django.contrib.sites.models import RequestSite
from django.core.cache import cache
from django.template.loader import get_template
from django.template import TemplateDoesNotExist


def git_commit():
    """Returns the ddr-local repo's most recent Git commit.
    
    Cached for 15min.
    """
    key = 'ddrpub:git_commit'
    timeout = 60 * 15
    cached = cache.get(key)
    if not cached:
        try:
            cached = envoy.run('git log --pretty=format:"%H" -1').std_out
        except:
            cached = 'unknown'
        cache.set(key, cached, timeout)
    return cached

def domain_org(request):
    """Match request domain with repo,org
    
    Uses settings.ORG_DOMAINS
    NOTE: "org" is referred to as "partner" in views to avoid
    confusion with the 'org' argument.
    
    @param request
    @returns: repo,org (str,str) or None,None
    """
    repo,org = None,None
    domain = RequestSite(request).domain
    for o,ds in settings.PARTNER_DOMAINS.iteritems():
        repo = 'ddr'
        for d in ds:
            if domain == d:
                org = o
    return repo,org

def choose_base_template(org, default='ui/base.html'):
    """Choose base template given the selected org
    
    Looks for an existing base template file for the org;
    Uses default if template for org does not exist.
    
    TODO cache this in session!
    
    @param org: str
    @param default: str
    @returns: template name (e.g. 'ui/base.html')
    """
    if org:
        template_name = 'ui/base-%s.html' % org
        try:
            get_template(template_name)
            template = template_name
        except TemplateDoesNotExist:
            template = 'ui/base-partner.html'
    else:
        template = default
    return template
