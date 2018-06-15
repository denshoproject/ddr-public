from collections import OrderedDict

from django.conf import settings

from elasticsearch import Elasticsearch
es = Elasticsearch(settings.DOCSTORE_HOSTS)

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse

from misc import filter_if_branded
from models import Repository, Organization, Collection, Entity, File
from models import Narrator, Facet, Term
from models import FORMATTERS, format_object_detail2
from search import es_offset, Searcher

DEFAULT_LIMIT = 25

CHILDREN = {
    'repository': ['organization'],
    'organization': ['collection'],
    'collection': ['entity'],
    'entity': ['entity', 'segment', 'file'],
    'segment': ['file'],
    'file': [],
}


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


@api_view(['GET'])
def search(request, format=None):
    """
    <a href="/api/0.2/search/help/">Search API help</a>
    """
    if request.GET.get('offset'):
        # limit and offset args take precedence over page
        limit = request.GET.get(
            'limit',
            int(request.GET.get('limit', settings.RESULTS_PER_PAGE))
        )
        offset = request.GET.get(
            'offset',
            int(request.GET.get('offset', 0))
        )
    elif request.GET.get('page'):
        limit = settings.RESULTS_PER_PAGE
        thispage = int(request.GET['page'])
        offset = es_offset(limit, thispage)
    else:
        limit = settings.RESULTS_PER_PAGE
        offset = 0

    searcher = Searcher(
        #mappings=identifier.ELASTICSEARCH_CLASSES_BY_MODEL,
        #fields=identifier.ELASTICSEARCH_LIST_FIELDS,
    )
    searcher.prepare(request)
    results = searcher.execute(limit, offset)
    return Response(
        results.ordered_dict(request, format_functions=FORMATTERS)
    )


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
    return _list(request, data)

@api_view(['GET'])
def term_objects(request, facet_id, term_id, limit=DEFAULT_LIMIT, offset=0):
    oid = '%s-%s' % (facet_id, term_id)
    data = Term.objects(facet_id, term_id, request, offset=offset)
    return _list(request, data)

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
    data = Facet.get(facet_id, request)
    return _detail(request, data)

@api_view(['GET'])
def facetterm(request, facet_id, term_id, format=None):
    oid = '%s-%s' % (facet_id, term_id)
    data = Term.get(oid, request)
    return _detail(request, data)
