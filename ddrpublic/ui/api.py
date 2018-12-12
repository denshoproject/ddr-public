from collections import OrderedDict

from django.conf import settings

from elasticsearch import Elasticsearch
es = Elasticsearch(settings.DOCSTORE_HOSTS)

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse

from .misc import filter_if_branded
from .models import Repository, Organization, Collection, Entity, File
from .models import Narrator, Facet, Term
from .models import FORMATTERS
from .search import es_offset, Searcher

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


@api_view(['GET', 'POST'])
def search(request, format=None):
    """
    Search API help: /api/0.2/search/help/
    """
    if request.data.get('fulltext'):
        if request.data.get('offset'):
            # limit and offset args take precedence over page
            limit = request.data.get(
                'limit',
                int(request.data.get('limit', settings.RESULTS_PER_PAGE))
            )
            offset = request.data.get(
                'offset',
                int(request.data.get('offset', 0))
            )
        elif request.data.get('page'):
            limit = settings.RESULTS_PER_PAGE
            thispage = int(request.data['page'])
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
    return Response({})


@api_view(['GET'])
def object_nodes(request, object_id):
    return files(request, object_id)


@api_view(['GET'])
def object_children(request, object_id):
    """OBJECT CHILDREN DOCS
    
    s - sort
    n - number of results AKA page size (limit)
    p - page (offset)
    """
    # TODO just get doc_type
    document = es.get(index=settings.DOCSTORE_INDEX, doc_type='_all', id=object_id)
    model = document['_type']
    if   model == 'repository': return organizations(request, object_id)
    elif model == 'organization': return collections(request, object_id)
    elif model == 'collection': return entities(request, object_id)
    elif model == 'entity': return segments(request, object_id)
    elif model == 'segment': return files(request, object_id)
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
def organizations(request, object_id, format=None):
    offset = int(request.GET.get('offset', 0))
    return _list(request, Repository.children(
        object_id, request, limit=DEFAULT_LIMIT, offset=offset
    ))

@api_view(['GET'])
def collections(request, object_id, format=None):
    offset = int(request.GET.get('offset', 0))
    return _list(request, Organization.children(
        object_id, request, limit=DEFAULT_LIMIT, offset=offset
    ))

@api_view(['GET'])
def entities(request, object_id, format=None):
    offset = int(request.GET.get('offset', 0))
    return _list(request, Collection.children(
        object_id, request, limit=DEFAULT_LIMIT, offset=offset
    ))

@api_view(['GET'])
def segments(request, object_id, format=None):
    offset = int(request.GET.get('offset', 0))
    return _list(request, Entity.children(
        object_id, request, limit=DEFAULT_LIMIT, offset=offset
    ))

@api_view(['GET'])
def files(request, object_id, format=None):
    offset = int(request.GET.get('offset', 0))
    return _list(request, Entity.files(
        object_id, request, limit=DEFAULT_LIMIT, offset=offset
    ))

@api_view(['GET'])
def facets(request, object_id, format=None):
    offset = int(request.GET.get('offset', 0))
    data = Facet.nodes(object_id, request, offset=offset)
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
    object_id = '%s-%s' % (facet_id, term_id)
    data = Term.objects(facet_id, term_id, request, offset=offset)
    return _list(request, data)

@api_view(['GET'])
def object_detail(request, object_id):
    """OBJECT DETAIL DOCS
    """
    # TODO just get doc_type
    document = es.get(index=settings.DOCSTORE_INDEX, doc_type='_all', id=object_id)
    model = document['_type']
    if   model == 'repository': return repository(request, object_id)
    elif model == 'organization': return organization(request, object_id)
    elif model == 'collection': return collection(request, object_id)
    elif model == 'entity': return entity(request, object_id)
    elif model == 'segment': return entity(request, object_id)
    elif model == 'file': return file(request, object_id)
    raise Exception("Could not match ID,model,view.")

def _detail(request, data):
    """Common function for detail views.
    """
    if not data:
        return Response(status=status.HTTP_404_NOT_FOUND)
    return Response(data)

@api_view(['GET'])
def repository(request, object_id, format=None):
    return _detail(request, Repository.get(object_id, request))

@api_view(['GET'])
def organization(request, object_id, format=None):
    return _detail(request, Organization.get(object_id, request))

@api_view(['GET'])
def collection(request, object_id, format=None):
    filter_if_branded(request, object_id)
    return _detail(request, Collection.get(object_id, request))

@api_view(['GET'])
def entity(request, object_id, format=None):
    filter_if_branded(request, object_id)
    return _detail(request, Entity.get(object_id, request))

@api_view(['GET'])
def file(request, object_id, format=None):
    filter_if_branded(request, object_id)
    return _detail(request, File.get(object_id, request))

@api_view(['GET'])
def narrators(request, format=None):
    offset = int(request.GET.get('offset', 0))
    data = Narrator.narrators(request, offset=offset)
    return _list(request, data)

@api_view(['GET'])
def narrator(request, object_id, format=None):
    data = Narrator.get(object_id, request)
    return _detail(request, data)

@api_view(['GET'])
def narrator_interviews(request, object_id, format=None):
    offset = int(request.GET.get('offset', 0))
    data = Narrator.interviews(object_id, request, limit=1000)
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
    object_id = '%s-%s' % (facet_id, term_id)
    data = Term.get(oid, request)
    return _detail(request, data)
