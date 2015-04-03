from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ui.models import Repository, Organization, Collection, Entity, File
from ui.views import filter_if_branded
from ui import faceting


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
    repository = Repository.get(repo)
    results = repository.api_children(page=1)
    return _list(request, results)

@api_view(['GET'])
def collections(request, repo, org, format=None):
    organization = Organization.get(repo, org)
    results = organization.api_children(page=1)
    return _list(request, results)

@api_view(['GET'])
def entities(request, repo, org, cid, format=None):
    collection = Collection.get(repo, org, cid)
    results = collection.api_children(page=1)
    return _list(request, results)

@api_view(['GET'])
def files(request, repo, org, cid, eid, format=None):
    entity = Entity.get(repo, org, cid, eid)
    results = entity.api_children(page=1)
    return _list(request, results)


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
    return _detail(request, Entity.api_get(repo, org, cid, eid))

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
    return Response(data)
