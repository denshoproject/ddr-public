from collections import OrderedDict

from django.conf import settings

from elasticsearch import Elasticsearch
ddr_es = Elasticsearch(settings.DOCSTORE_HOSTS)
names_es = Elasticsearch(settings.NAMESDB_DOCSTORE_HOSTS)

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from .misc import filter_if_branded
from .models import Repository, Organization, Collection, Entity, File
from .models import Narrator, Facet, Term
from .models import NameRecord
from .models import FORMATTERS
from . import search
from namesdb.definitions import SEARCH_FIELDS as NAMESDB_SEARCH_FIELDS

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
    """Swagger UI: /api/swagger/
    """
    repo = 'ddr'
    data = {
        'facets': reverse('ui-api-facets', request=request),
        'narrators': reverse('ui-api-narrators', request=request),
        'repository': reverse('ui-api-object', args=[repo,], request=request),
        'search': reverse('ui-api-search', request=request),
    }
    return Response(data)


class Search(APIView):
    
    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter(
            'fulltext',
            description='Search string using Elasticsearch query_string syntax.',
            required=True,
            in_=openapi.IN_QUERY, type=openapi.TYPE_STRING
        ),
        openapi.Parameter(
            'topics',
            description='Topic term ID(s) from http://partner.densho.org/vocab/api/0.2/topics.json.',
            in_=openapi.IN_QUERY,
            type=openapi.TYPE_ARRAY, items={'type':'integer'}
        ),
        openapi.Parameter(
            'facility',
            description='Facility ID(s) from http://partner.densho.org/vocab/api/0.2/facility.json.',
            in_=openapi.IN_QUERY,
            type=openapi.TYPE_ARRAY, items={'type':'integer'}
        ),
        openapi.Parameter(
            'format',
            description='Format term ID(s) from http://partner.densho.org/vocab/api/0.2/format.json.',
            in_=openapi.IN_QUERY,
            type=openapi.TYPE_ARRAY, items={'type':'string'}
        ),
        openapi.Parameter(
            'genre',
            description='Genre term ID(s) from http://partner.densho.org/vocab/api/0.2/genre.json',
            in_=openapi.IN_QUERY,
            type=openapi.TYPE_ARRAY, items={'type':'string'}
        ),
        openapi.Parameter(
            'rights',
            description='Rights term ID(s) from http://partner.densho.org/vocab/api/0.2/rights.json',
            in_=openapi.IN_QUERY,
            type=openapi.TYPE_ARRAY, items={'type':'string'}
        ),
        openapi.Parameter(
            'page',
            description='Selected results page (default: 0).',
            in_=openapi.IN_QUERY, type=openapi.TYPE_STRING
        ),
    ])
    def get(self, request, format=None):
        """Search the Repository; good for simpler searches.
        
        Search API help: /api/0.2/search/help/
        """
        if request.GET.get('fulltext'):
            return self.grep(request)
        return Response({})
    
    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter(
            'body',
            description='DESCRIPTION HERE',
            required=True,
            in_=openapi.IN_FORM, type=openapi.TYPE_STRING),
    ])
    def post(self, request, format=None):
        """Search the Repository; good for more complicated custom searches.
        
        Search API help: /api/0.2/search/help/
        
        Sample search body JSON:
        
        {
            "fulltext": "seattle",
            "must": [
                {"topics": "239"}
            ]
        }

        """
        if request.data.get('fulltext'):
            return self.grep(request)
        return Response({})
    
    def grep(self, request):
        """DR search
        """
        def reget(request, field):
            if request.GET.get(field):
                return request.GET[field]
            elif request.data.get(field):
                return request.data[field]
            return None
        
        fulltext = reget(request, 'fulltext')
        offset = reget(request, 'offset')
        limit = reget(request, 'limit')
        page = reget(request, 'page')
        
        if offset:
            # limit and offset args take precedence over page
            if not limit:
                limit = settings.RESULTS_PER_PAGE
            offset = int(offset)
        elif page:
            limit = settings.RESULTS_PER_PAGE
            thispage = int(page)
            offset = search.es_offset(limit, thispage)
        else:
            limit = settings.RESULTS_PER_PAGE
            offset = 0
        
        searcher = search.Searcher(
            conn=ddr_es,
            index=settings.DOCSTORE_INDEX,
            #mappings=identifier.ELASTICSEARCH_CLASSES_BY_MODEL,
            #fields=identifier.ELASTICSEARCH_LIST_FIELDS,
        )
        searcher.prepare(
            params=request,
            params_whitelist=search.SEARCH_PARAM_WHITELIST,
            search_models=search.SEARCH_MODELS,
            fields=search.SEARCH_INCLUDE_FIELDS,
            fields_nested=search.SEARCH_NESTED_FIELDS,
            fields_agg=search.SEARCH_AGG_FIELDS,
        )
        results = searcher.execute(limit, offset)
        return Response(
            results.ordered_dict(request, format_functions=FORMATTERS)
        )


@api_view(['GET'])
def object_nodes(request, object_id):
    return files(request._request, object_id)


@api_view(['GET'])
def object_children(request, object_id):
    """OBJECT CHILDREN DOCS
    
    s - sort
    n - number of results AKA page size (limit)
    p - page (offset)
    """
    # TODO just get doc_type
    document = ddr_es.get(index=settings.DOCSTORE_INDEX, doc_type='_all', id=object_id)
    model = document['_type']
    if   model == 'repository': return organizations(request._request, object_id)
    elif model == 'organization': return collections(request._request, object_id)
    elif model == 'collection': return entities(request._request, object_id)
    elif model == 'entity': return segments(request._request, object_id)
    elif model == 'segment': return files(request._request, object_id)
    elif model == 'file': assert False
    raise Exception("Could not match ID,model,view.")

def _list(request, data):
    host = request.META.get('HTTP_HOST')
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
    document = ddr_es.get(index=settings.DOCSTORE_INDEX, doc_type='_all', id=object_id)
    model = document['_type']
    if   model == 'repository': return repository(request._request, object_id)
    elif model == 'organization': return organization(request._request, object_id)
    elif model == 'collection': return collection(request._request, object_id)
    elif model == 'entity': return entity(request._request, object_id)
    elif model == 'segment': return entity(request._request, object_id)
    elif model == 'file': return file(request._request, object_id)
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
def name(request, object_id, format=None):
    data = NameRecord.get(object_id, request)
    return _detail(request, data)

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


class NamesSearch(APIView):
    
    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter(
            'fulltext',
            description='Search string using Elasticsearch query_string syntax.',
            required=True,
            in_=openapi.IN_QUERY, type=openapi.TYPE_STRING
        ),
        openapi.Parameter(
            'm_camp',
            description='One or more camp IDs e.g. "9-rohwer".',
            in_=openapi.IN_QUERY, type=openapi.TYPE_STRING
        ),
        openapi.Parameter(
            'page',
            description='Selected results page (default: 0).',
            in_=openapi.IN_QUERY, type=openapi.TYPE_STRING
        ),
    ])
    def get(self, request, format=None):
        """Search the Names Database; good for simpler searches.
        
        Search API help: /api/0.2/search/help/
        """
        if request.GET.get('fulltext'):
            return self.grep(request)
        return Response({})
    
    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter(
            'body',
            description='DESCRIPTION HERE',
            required=True,
            in_=openapi.IN_FORM, type=openapi.TYPE_STRING),
    ])
    def post(self, request, format=None):
        """Search the Names Database; good for more complicated custom searches.
        
        Search API help: /api/0.2/search/help/
        """
        if request.data.get('fulltext'):
            return self.grep(request)
        return Response({})
    
    def grep(self, request):
        """NamesDB search
        """
        def reget(request, field):
            if request.GET.get(field):
                return request.GET[field]
            elif request.data.get(field):
                return request.data[field]
            return None
        
        fulltext = reget(request, 'fulltext')
        offset = reget(request, 'offset')
        limit = reget(request, 'limit')
        page = reget(request, 'page')
        
        if offset:
            # limit and offset args take precedence over page
            if not limit:
                limit = settings.RESULTS_PER_PAGE
            offset = int(offset)
        elif page:
            limit = settings.RESULTS_PER_PAGE
            thispage = int(page)
            offset = search.es_offset(limit, thispage)
        else:
            limit = settings.RESULTS_PER_PAGE
            offset = 0
        
        searcher = search.Searcher(
            conn=names_es,
            index=settings.NAMESDB_DOCSTORE_INDEX,
        )
        searcher.prepare(
            params=request,
            params_whitelist=['fulltext', 'm_camp'],
            search_models=['names-record'],
            fields=NAMESDB_SEARCH_FIELDS,
            fields_nested=[],
            fields_agg={'m_camp':'m_camp'},
        )
        results = searcher.execute(limit, offset)
        return Response(
            results.ordered_dict(request, format_functions=FORMATTERS)
        )
