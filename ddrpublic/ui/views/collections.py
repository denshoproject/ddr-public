import logging
logger = logging.getLogger(__name__)

from django.conf import settings
from django.core.paginator import Paginator
from django.shortcuts import Http404, render
from django.urls import reverse
from django.views.decorators.cache import cache_page

from elastictools import search
from .. import forms_search as forms
from .. import models
from .. import misc
from ..decorators import ui_state


@cache_page(settings.CACHE_TIMEOUT)
def list( request ):
    # TODO cache or restrict fields (truncate desc BEFORE caching)
    organizations = []
    repo,org = misc.domain_org(request)
    if repo and org:
        # partner site
        organization_id = '%s-%s' % (repo,org) # TODO relies on knowledge of ID structure!
        collections = models.Organization.children(
            org.id, request, limit=settings.ELASTICSEARCH_MAX_SIZE,
        )
        org_formatted = models.format_object_detail2(org.to_dict(), request)
        objects = collections.ordered_dict(
            request=request,
            format_functions=models.FORMATTERS,
            pad=True,
        )['objects']
        organizations.append( (org_formatted,objects) )
    else:
        # default site
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
            collections = models.Organization.children(
                org.id, request, limit=settings.ELASTICSEARCH_MAX_SIZE,
            )
            org_formatted = models.format_object_detail2(org.to_dict(), request)
            objects = collections.ordered_dict(
                request=request,
                format_functions=models.FORMATTERS,
                pad=True,
            )['objects']
            organizations.append( (org_formatted,objects) )
    return render(request, 'ui/collections.html', {
        'organizations': organizations,
    })

@cache_page(settings.CACHE_TIMEOUT)
def detail(request, oid):
    try:
        collection = models._object(request, oid)
    except models.NotFound:
        raise Http404
    misc.filter_if_branded(request, collection['organization_id'])
    # TODO fix this
    try:
        organization = models._object(request, collection['organization_id'])
    except:
        organization = None
    thispage = 1
    pagesize = 10
    results = models.Collection.children(
        oid=oid,
        request=request,
        limit=pagesize,
        offset=0,
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
    return render(request, 'ui/collections/detail.html', {
        'object': collection,
        'organization': organization,
        'paginator': paginator,
        'page': page,
        'api_url': reverse('ui-api-object', args=[oid]),
    })

@ui_state
def children(request, oid):
    """Lists all direct children of the collection.
    """
    try:
        collection = models._object(request, oid)
    except models.NotFound:
        raise Http404
    misc.filter_if_branded(request, collection['organization_id'])
    
    params = request.GET.copy()
    params['parent'] = oid
    if not params.get('fulltext'):
        params['match_all'] = 'true'
    searcher = search.Searcher(models.DOCSTORE)
    searcher.prepare(
        params=params,
        params_whitelist=models.SEARCH_PARAM_WHITELIST,
        search_models=['ddrentity'],
        sort=models.OBJECT_LIST_SORT,
        fields=models.SEARCH_INCLUDE_FIELDS,
        fields_nested=models.SEARCH_NESTED_FIELDS,
        fields_agg=models.SEARCH_AGG_FIELDS,
        wildcards=False,
    )
    limit,offset = search.limit_offset(request, settings.RESULTS_PER_PAGE)
    results = searcher.execute(limit, offset)
    paginator = Paginator(
        results.ordered_dict(
            request=request,
            format_functions=models.FORMATTERS,
            pad=True,
        )['objects'],
        results.page_size,
    )
    page = paginator.page(results.this_page)
    
    form = forms.SearchForm(
        data=request.GET.copy(),
        search_results=results,
    )

    return render(request, 'ui/collections/children.html', {
        'object': collection,
        'paginator': paginator,
        'page': page,
        'form': form,
        'api_url': reverse('ui-api-object-children', args=[oid]),
    })

@ui_state
def nodes(request, oid):
    """Lists all nodes of the collection.
    """
    raise Exception('no longer implemented')
