from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from DDR.models import Identity
from ui.models import Repository, Organization, Collection, Entity, File
from ui.views import filter_if_branded
from ui import faceting
from ui import models


# helpers --------------------------------------------------------------

URL_FIELDS = ['ancestors', 'siblings', 'children']

def http_host(request):
    return 'http://%s' % request.META['HTTP_HOST']

def add_url_host(request, data):
    host = http_host(request)
    for key,val in data.iteritems():
        if key and val \
        and isinstance(val, basestring) \
        and (('url' in key) or (key in URL_FIELDS)) \
        and ('http://' not in val):
            data[key] = '%s%s' % (host, val)

def add_host_list(request, data):
    host = http_host(request)
    new = []
    for val in data:
        if val \
        and isinstance(val, basestring) \
        and ('http://' not in val):
            val = '%s%s' % (host, val)
        new.append(val)
    return new

def term_urls(request, data, facet_id, fieldname):
    """Convert facet term IDs to links to term API nodes.
    """
    host = http_host(request)
    topics_urls = []
    for tid in data[fieldname]:
        if tid:
            url = '%s%s' % (host, reverse('ui-api-term', args=(facet_id, tid)))
            topics_urls.append(url)
    data[fieldname] = topics_urls

def encyc_urls(data):
    encyc_urls = [
        '%s%s' % (settings.ENCYC_BASE, url)
        for url in data['encyclopedia']
    ]
    data['encyclopedia'] = encyc_urls


# views ----------------------------------------------------------------

@api_view(['GET'])
def index(request, format=None):
    repo = 'ddr'
    data = {
        'repository': reverse('ui-api-repository', args=[repo,]),
        'facets': reverse('ui-api-facets'),
    }
    host = http_host(request)
    for key,val in data.iteritems():
        data[key] = '%s%s' % (host, val)
    return Response(data)


def _list(request, results):
    data = {
        "count": len(results),
        "next": None,
        "previous": None,
        "results": results
    }
    for d in data['results']:
        add_url_host(request, d)
    return Response(data)
    
@api_view(['GET'])
def organizations(request, repo, format=None):
    results = Repository.api_children(repo, page=1)
    return _list(request, results)

@api_view(['GET'])
def collections(request, repo, org, format=None):
    results = Organization.api_children(repo, org, page=1)
    return _list(request, results)

@api_view(['GET'])
def entities(request, repo, org, cid, format=None):
    results = Collection.api_children(repo, org, cid, page=1)
    return _list(request, results)

@api_view(['GET'])
def files(request, repo, org, cid, eid, format=None):
    results = Entity.api_children(repo, org, cid, eid, page=1)
    return _list(request, results)

@api_view(['GET'])
def term_objects(request, facet_id, term_id, format=None):
    terms = {facet_id:term_id}
    fields = models.all_list_fields()
    sort = {'record_created': request.GET.get('record_created', ''),
            'record_lastmod': request.GET.get('record_lastmod', ''),}
    # filter by partner
    filters = {}
    repo,org = None,None
    if repo and org:
        filters['repo'] = repo
        filters['org'] = org
    # do the query
    results = models.cached_query(
        settings.DOCSTORE_HOSTS, settings.DOCSTORE_INDEX,
        terms=terms, filters=filters,
        fields=fields,
        sort=sort
    )
    # post-processing. See *.api_children methods in .models.py
    documents = [hit['_source'] for hit in results['hits']['hits']]
    for d in documents:
        idparts = Identity.split_object_id(d['id'])
        model = idparts.pop(0)
        d['url'] = reverse('ui-api-%s' % model, args=(idparts))
        d['absolute_url'] = reverse('ui-%s' % model, args=(idparts))
        if d['signature_file']:
            d['img_url'] = models.signature_url(d['signature_file'])
    return _list(request, documents)


def _detail(request, data):
    """Common function for detail views.
    """
    if not data:
	return Response(status=status.HTTP_404_NOT_FOUND)
    add_url_host(request, data)
    return Response(data)

@api_view(['GET'])
def repository(request, repo, format=None):
    return _detail(request, Repository.api_get(repo))

@api_view(['GET'])
def organization(request, repo, org, format=None):
    return _detail(request, Organization.api_get(repo, org))

@api_view(['GET'])
def collection(request, repo, org, cid, format=None):
    filter_if_branded(request, repo, org)
    return _detail(request, Collection.api_get(repo, org, cid))

@api_view(['GET'])
def entity(request, repo, org, cid, eid, format=None):
    data = Entity.api_get(repo, org, cid, eid)
    term_urls(request, data, 'topics', 'topics')
    term_urls(request, data, 'facility', 'facility')
    return _detail(request, data)

@api_view(['GET'])
def file(request, repo, org, cid, eid, role, sha1, format=None):
    return _detail(request, File.api_get(repo, org, cid, eid, role, sha1))


@api_view(['GET'])
def facet_index(request, format=None):
    host = http_host(request)
    data = {
        'topics': '%s%s' % (host, reverse('ui-api-facet', args=['topics',])),
        'facility': '%s%s' % (host, reverse('ui-api-facet', args=['facility',])),
    }
    return Response(data)

@api_view(['GET'])
def facet(request, facet, format=None):
    facet = faceting.Facet(facet)
    data = facet.api_data()
    add_url_host(request, data)
    for d in data['terms']:
        add_url_host(request, d)
    return Response(data)

@api_view(['GET'])
def term(request, facet_id, term_id, format=None):
    term = faceting.Term(facet_id=facet_id, term_id=term_id)
    data = term.api_data()
    add_url_host(request, data)
    data['ancestors'] = add_host_list(request, data['ancestors'])
    data['siblings'] = add_host_list(request, data['siblings'])
    data['children'] = add_host_list(request, data['children'])
    encyc_urls(data)
    return Response(data)
