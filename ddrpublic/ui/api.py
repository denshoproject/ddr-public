from collections import defaultdict, OrderedDict
import json
import os
import urlparse

import requests

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponseRedirect

from elasticsearch import Elasticsearch
es = Elasticsearch(settings.DOCSTORE_HOSTS)

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.reverse import reverse

from ui import docstore
from ui.urls import API_BASE
from ui.views import filter_if_branded
from ui import encyc

DEFAULT_LIMIT = 25

CHILDREN = {
    'repository': ['organization'],
    'organization': ['collection'],
    'collection': ['entity'],
    'entity': ['entity', 'segment', 'file'],
    'segment': ['file'],
    'file': [],
}

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
    #topics_urls = [
    #    reverse('ui-api-term', args=(facet_id, tid), request=request)
    #    for tid in data.get(fieldname, [])
    #    if tid
    #]
    #data[fieldname] = topics_urls
    #topics_urls = [
    #
    for tid in data.get(fieldname, []):
        if isinstance(tid, dict) and tid.get('id'):
            url = reverse('ui-api-term', args=(facet_id, tid['id']), request=request)
            assert False
        elif tid:
            url = reverse('ui-api-term', args=(facet_id, tid), request=request)
    assert False

def access_filename(file_id):
    """
    TODO This is probably redundant. D-R-Y!
    """
    if file_id:
        return '%s-a.jpg' % file_id
    return file_id

def img_path(bucket, filename):
    """Constructs S3-style bucket-file URL
    
    file.path_rel now often contains a partial path not just filename.
    This chops that off.
    """
    return os.path.join(
        bucket,
        os.path.basename(filename)
    )


# TODO rm
def segment_img_url(denshouid):
    """Make a VH interview segment image URL given a denshouid
    
    >>> segment_img("denshovh-mkiyo_2-01")
    'http://ddr.densho.org/media/denshovh/denshovh-mkiyo_2-01.jpg'
    http://ddrstage.densho.org/media/ddr-densho-1000/denshovh-hgordon-01-a.jpg

    @param aid: str denshouid
    @returns: str URL
    """
    return os.path.join(settings.SEGMENT_URL, denshouid)







MODEL_CLASSES = {
    'repository': Repository,
    'organization': Organization,
    'collection': Collection,
    'entity': Entity,
    'segment': Entity,
    'file': File,
}

def id_object(oid=None, oi=None, request=None):
    """Get object from its Identifier or ID
    
    @param oid: str Object ID
    @param oi: identifier.Identifier
    @returns: object
    """
    assert oid or oi
    if oid and not oi:
        oi = Identifier(oid)
    return MODEL_CLASSES[oi.model].get(oid=oi.id, request=request, i=oi)


# views ----------------------------------------------------------------

@api_view(['GET'])
def index(request, format=None):
    """INDEX DOCS
    """
    repo = 'ddr'
    data = {
        'facets': reverse('ui-api-facets', request=request),
        'narrators': reverse('ui-api-narrators', request=request),
        'repository': reverse('ui-api-object', args=[repo,], request=request),
        'search': reverse('ui-api-search', request=request),
    }
    return Response(data)


@api_view(['GET', 'POST'])
def search(request, format=None):
    """
    <a href="/api/0.2/search/help/">Search API help</a>
    """
    query = OrderedDict()
    query['fulltext'] = request.data.get('fulltext')
    query['must'] = request.data.get('must', [])
    query['should'] = request.data.get('should', [])
    query['mustnot'] = request.data.get('mustnot', [])
    query['models'] = request.data.get('models', [])
    query['sort'] = request.data.get('sort', [])
    query['offset'] = request.data.get('offset', 0)
    query['limit'] = request.data.get('limit', DEFAULT_LIMIT)
    
    if query['fulltext'] or query['must'] or query['should'] or query['mustnot']:
        # do the query
        data = docstore_search(
            text = query['fulltext'],
            must = query['must'],
            should = query['should'],
            mustnot = query['mustnot'],
            models = query['models'],
            sort_fields = query['sort'],
            offset = query['offset'],
            limit = query['limit'],
            request = request,
        )
        # remove match _all from must, keeping fulltext arg
        for item in query['must']:
            if isinstance(item, dict) \
            and item.get('match') \
            and item['match'].get('_all') \
            and (item['match']['_all'] == query.get('fulltext')):
                query['must'].remove(item)
        # include query in response
        data['query'] = query
    
        return Response(data)
    return Response({})


@api_view(['GET'])
def object_nodes(request, oid):
    return files(request, oid)


@api_view(['GET'])
def object_children(request, oid):
    """OBJECT CHILDREN DOCS
    
    s - sort
    n - number of results AKA page size (limit)
    p - page (offset)
    """
    # TODO just get doc_type
    document = es.get(index=settings.DOCSTORE_INDEX, doc_type='_all', id=oid)
    model = document['_type']
    if   model == 'repository': return organizations(request, oid)
    elif model == 'organization': return collections(request, oid)
    elif model == 'collection': return entities(request, oid)
    elif model == 'entity': return segments(request, oid)
    elif model == 'segment': return files(request, oid)
    elif model == 'file': assert False
    raise Exception("Could not match ID,model,view.")

def _list(request, data):
    host = request.META['HTTP_HOST']
    path = request.META['PATH_INFO']
    if data.get('prev'):
        data['prev'] = 'http://%s%s%s' % (host, path, data['prev'])
    if data.get('next'):
        data['next'] = 'http://%s%s%s' % (host, path, data['next'])
    return Response(data)
    
@api_view(['GET'])
def organizations(request, oid, format=None):
    offset = int(request.GET.get('offset', 0))
    return _list(request, Repository.children(
        oid, request, limit=DEFAULT_LIMIT, offset=offset
    ))

@api_view(['GET'])
def collections(request, oid, format=None):
    offset = int(request.GET.get('offset', 0))
    return _list(request, Organization.children(
        oid, request, limit=DEFAULT_LIMIT, offset=offset
    ))

@api_view(['GET'])
def entities(request, oid, format=None):
    offset = int(request.GET.get('offset', 0))
    return _list(request, Collection.children(
        oid, request, limit=DEFAULT_LIMIT, offset=offset
    ))

@api_view(['GET'])
def segments(request, oid, format=None):
    offset = int(request.GET.get('offset', 0))
    return _list(request, Entity.children(
        oid, request, limit=DEFAULT_LIMIT, offset=offset
    ))

@api_view(['GET'])
def files(request, oid, format=None):
    offset = int(request.GET.get('offset', 0))
    return _list(request, Entity.files(
        oid, request, limit=DEFAULT_LIMIT, offset=offset
    ))

@api_view(['GET'])
def facets(request, oid, format=None):
    offset = int(request.GET.get('offset', 0))
    data = Facet.nodes(oid, request, offset=offset)
    return _list(request, data)

@api_view(['GET'])
def facetterms(request, facet_id, format=None):
    offset = int(request.GET.get('offset', 0))
    data = Facet.children(
        facet_id, request,
        sort=[('id','asc')],
        offset=offset,
        raw=True
    )
    assert False
    return Response(data)

@api_view(['GET'])
def object_detail(request, oid):
    """OBJECT DETAIL DOCS
    """
    # TODO just get doc_type
    document = es.get(index=settings.DOCSTORE_INDEX, doc_type='_all', id=oid)
    model = document['_type']
    if   model == 'repository': return repository(request, oid)
    elif model == 'organization': return organization(request, oid)
    elif model == 'collection': return collection(request, oid)
    elif model == 'entity': return entity(request, oid)
    elif model == 'segment': return entity(request, oid)
    elif model == 'file': return file(request, oid)
    raise Exception("Could not match ID,model,view.")

def _detail(request, data):
    """Common function for detail views.
    """
    if not data:
	return Response(status=status.HTTP_404_NOT_FOUND)
    return Response(data)

@api_view(['GET'])
def repository(request, oid, format=None):
    return _detail(request, Repository.get(oid, request))

@api_view(['GET'])
def organization(request, oid, format=None):
    return _detail(request, Organization.get(oid, request))

@api_view(['GET'])
def collection(request, oid, format=None):
    filter_if_branded(request, oid)
    return _detail(request, Collection.get(oid, request))

@api_view(['GET'])
def entity(request, oid, format=None):
    filter_if_branded(request, oid)
    return _detail(request, Entity.get(oid, request))

@api_view(['GET'])
def file(request, oid, format=None):
    filter_if_branded(request, oid)
    return _detail(request, File.get(oid, request))

@api_view(['GET'])
def narrators(request, format=None):
    offset = int(request.GET.get('offset', 0))
    data = Narrator.narrators(request, offset=offset)
    return _list(request, data)

@api_view(['GET'])
def narrator(request, oid, format=None):
    data = Narrator.get(oid, request)
    return _detail(request, data)

@api_view(['GET'])
def narrator_interviews(request, oid, format=None):
    offset = int(request.GET.get('offset', 0))
    data = Narrator.interviews(oid, request, limit=1000)
    return _list(request, data)

@api_view(['GET'])
def facet_index(request, format=None):
    data = Facet.facets(request)
    return Response(data)

@api_view(['GET'])
def facet(request, facet_id, format=None):
    data = es.get(index=settings.DOCSTORE_INDEX, doc_type='facet', id=facet_id)
    return _detail(request, format_facet(data, request))

@api_view(['GET'])
def term(request, facet_id, term_id, format=None):
    oid = '%s-%s' % (facet_id, term_id)
    data = Term.get(oid, request)
    return _detail(request, data)

@api_view(['GET'])
def term_objects(request, facet_id, term_id, limit=DEFAULT_LIMIT, offset=0):
    oid = '%s-%s' % (facet_id, term_id)
    data = Term.objects(
        facet_id=facet_id,
        term_id=term_id,
        offset=offset,
        request=request
    )
    return Response(data)
