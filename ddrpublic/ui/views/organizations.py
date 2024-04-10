import logging
logger = logging.getLogger(__name__)

from django.conf import settings
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.shortcuts import Http404, redirect, render
from django.urls import reverse

from elastictools import search
from .. import misc
from .. import models


def list(request):
    """List organizations 
    """
    organizations = []
    repo,org = misc.domain_org(request)
    try:
        orgs = models.Repository.children(repo, request)
    except:  # NotFoundError:
        raise Exception(
            'No repository record. ' \
            'Run "ddrindex repo /PATH/TO/REPO/repository.json".'
        )
    if not orgs.objects:
        raise Exception(
            'No organization records. ' \
            'Run "ddrindex org /PATH/TO/ORG/organization.json".'
        )
    for org in orgs.objects:
        oid = org['id']
        org_formatted = models.format_object_detail2(org.to_dict(), request)
        num_collections = models.Organization.children(
            oid, request, limit=settings.ELASTICSEARCH_MAX_SIZE,
            just_count=True
        )['count']
        organizations.append( (org_formatted,num_collections) )
    return render(request, 'ui/organizations/list.html', {
        'num_organizations': len(organizations),
        'organizations': organizations,
        'api_url': reverse('ui-api-object-children', args=[repo]),
    })

def detail(request, oid):
    repo,org = misc.domain_org(request)
    organization = models.Organization.get(oid, request)
    # collections
    limit,offset = search.limit_offset(request, settings.RESULTS_PER_PAGE)
    results = models.Organization.children(
        oid, request, limit=limit, offset=offset,
    )
    paginator = Paginator(
        results.ordered_dict(
            request=request,
            format_functions=models.FORMATTERS,
            pad=True,
        )['objects'],
        results.page_size,
    )
    page = paginator.page(results.this_page)
    return render(request, 'ui/organizations/detail.html', {
        'repo': repo,
        'organization': organization,
        'object': organization,
        'num_collections': results.total,
        'paginator': paginator,
        'page': page,
        'api_url': reverse('ui-api-object', args=[oid]),
    })
