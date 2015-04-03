from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ui.models import Repository, Organization, Collection, Entity, File
from ui.views import filter_if_branded


# helpers

def add_url_host(request, data):
    host = 'http://%s' % request.META['HTTP_HOST']
    for key,val in data.iteritems():
        if key and val \
        and (('url' in key) or (key == 'children')) \
        and ('http://' not in val):
            data[key] = '%s%s' % (host, val)
    return data


# views

@api_view(['GET'])
def index(request, format=None):
    repo = 'ddr'
    url = 'http://%s%s' % (request.META['HTTP_HOST'], reverse('ui-api-repository', args=[repo,]))
    data = {
        'repository': url
    }
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
