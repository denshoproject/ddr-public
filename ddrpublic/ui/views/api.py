from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ui.models import Repository, Organization, Collection, Entity, File
from ui.views import filter_if_branded


def add_url_host(request, data):
    host = 'http://%s' % request.META['HTTP_HOST']
    for key,val in data.iteritems():
        if key and val and ('url' in key) and ('http://' not in val):
            data[key] = '%s%s' % (host, val)
    return data


@api_view(['GET'])
def repository_detail(request, repo, format=None):
    data = Repository.api_get(repo)
    if not data:
	return Response(status=status.HTTP_404_NOT_FOUND)
    add_url_host(request, data)
    return Response(data)

@api_view(['GET'])
def organization_detail(request, repo, org, format=None):
    data = Organization.api_get(repo, org)
    if not data:
	return Response(status=status.HTTP_404_NOT_FOUND)
    add_url_host(request, data)
    return Response(data)

@api_view(['GET'])
def collection_detail(request, repo, org, cid, format=None):
    filter_if_branded(request, repo, org)
    data = Collection.api_get(repo, org, cid)
    if not data:
	return Response(status=status.HTTP_404_NOT_FOUND)
    add_url_host(request, data)
    for e in data['entities']:
        add_url_host(request, e)
    return Response(data)

@api_view(['GET'])
def entity_detail(request, repo, org, cid, eid, format=None):
    data = Entity.api_get(repo, org, cid, eid)
    if not data:
	return Response(status=status.HTTP_404_NOT_FOUND)
    add_url_host(request, data)
    for f in data['files']:
        add_url_host(request, f)
    return Response(data)

@api_view(['GET'])
def file_detail(request, repo, org, cid, eid, role, sha1, format=None):
    data = File.api_get(repo, org, cid, eid, role, sha1)
    if not data:
	return Response(status=status.HTTP_404_NOT_FOUND)
    add_url_host(request, data)
    return Response(data)
