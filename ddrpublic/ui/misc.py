import os

import envoy

from django.conf import settings
from django.contrib.sites.requests import RequestSite
from django.core.cache import cache
from django.template.loader import get_template
from django.template import TemplateDoesNotExist


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

def filter_if_branded(request, organization_id):
    pass
    #partner_repo,partner_org = domain_org(request)
    #if partner_repo and partner_org and (org != partner_org):
    #    raise Http404

def git_commits():
    """Returns various repos' most recent Git commit.
    """
    commits = {}
    pub_path = os.getcwd()
    cmd_path = settings.CMDLN_INSTALL_PATH
    def_path = settings.REPO_MODELS_PATH
    cmd = 'git log --pretty=format:"%h %ci%d" -1'
    os.chdir(pub_path); commits['pub'] = envoy.run(cmd).std_out
    os.chdir(cmd_path); commits['cmd'] = envoy.run(cmd).std_out
    os.chdir(def_path); commits['def'] = envoy.run(cmd).std_out
    return commits

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
    for o,ds in settings.PARTNER_DOMAINS.items():
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
