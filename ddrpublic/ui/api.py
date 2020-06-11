from collections import OrderedDict

from django.conf import settings

from elasticsearch import Elasticsearch
ddr_es = Elasticsearch(settings.DOCSTORE_HOSTS)

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request as RestRequest
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from . import docstore
from . import identifier
from .misc import filter_if_branded
from .models import Repository, Organization, Collection, Entity, File
from .models import Narrator, Facet, Term
from .models import FORMATTERS
from . import search

# set default hosts and index
DOCSTORE = docstore.Docstore()

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
    
    def get(self, request, format=None):
        """Search the Repository; good for simpler searches.
        
        `fulltext`: Search string using Elasticsearch query_string syntax.
        `topics`: Topic term ID(s) from http://partner.densho.org/vocab/api/0.2/topics.json.
        `facility`: Facility ID(s) from http://partner.densho.org/vocab/api/0.2/facility.json.
        `format`: Format term ID(s) from http://partner.densho.org/vocab/api/0.2/format.json.
        `genre`: Genre term ID(s) from http://partner.densho.org/vocab/api/0.2/genre.json
        `rights`: Rights term ID(s) from http://partner.densho.org/vocab/api/0.2/rights.json
        `page`: Selected results page (default: 0).
        
        Search API help: /api/search/help/
        """
        if request.GET.get('fulltext'):
            return self.grep(request)
        return Response({})
    
    def post(self, request, format=None):
        """Search the Repository; good for more complicated custom searches.
        
        Search API help: /api/search/help/
        
        Sample search body JSON:
        
        {"fulltext": "seattle", "must": [{"topics": "239"}]}
        
        `fulltext`: Search string using Elasticsearch query_string syntax.
        `topics`: Topic term ID(s) from http://partner.densho.org/vocab/api/0.2/topics.json.
        `facility`: Facility ID(s) from http://partner.densho.org/vocab/api/0.2/facility.json.
        `format`: Format term ID(s) from http://partner.densho.org/vocab/api/0.2/format.json.
        `genre`: Genre term ID(s) from http://partner.densho.org/vocab/api/0.2/genre.json
        `rights`: Rights term ID(s) from http://partner.densho.org/vocab/api/0.2/rights.json
        `page`: Selected results page (default: 0).
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
        
        searcher = search.Searcher()
        searcher.prepare(
            params=request.query_params.dict(),
            params_whitelist=search.SEARCH_PARAM_WHITELIST,
            search_models=search.SEARCH_MODELS,
            fields=search.SEARCH_INCLUDE_FIELDS,
            fields_nested=search.SEARCH_NESTED_FIELDS,
            fields_agg=search.SEARCH_AGG_FIELDS,
        )
        results = searcher.execute(limit, offset)
        results_dict = results.ordered_dict(request, format_functions=FORMATTERS)
        results_dict.pop('aggregations')
        return Response(results_dict)


@api_view(['GET'])
def object_nodes(request, object_id):
    return files(request._request, object_id)


@api_view(['GET'])
def object_children(request, object_id):
    """List children for a collection or collection object
    """
    # TODO just get doc_type
    document = DOCSTORE.es.get(
        index=DOCSTORE.index_name(identifier.Identifier(object_id).model),
        id=object_id
    )
    model = document['_index'].replace(docstore.INDEX_PREFIX, '')
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
    if isinstance(data, dict):
        return Response(data)
    return Response(data.ordered_dict(request, FORMATTERS))
    
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
    """List of facets
    """
    offset = int(request.GET.get('offset', 0))
    data = Facet.nodes(object_id, request, offset=offset)
    return _list(request, data)

@api_view(['GET'])
def facetterms(request, facet_id, format=None):
    """Terms for specified facet
    
    `facet_id`: "topics", "facility", "format", "genre", or "rights". 
    """
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
    """DDR objects for specified facet term
    
    `facet_id`: "topics", "facility", "format", "genre", or "rights". 
    `term_id`: A term ID from one of the following lists:
    
    - http://partner.densho.org/vocab/api/0.2/topics.json
    - http://partner.densho.org/vocab/api/0.2/facility.json
    - http://partner.densho.org/vocab/api/0.2/format.json
    - http://partner.densho.org/vocab/api/0.2/genre.json
    - http://partner.densho.org/vocab/api/0.2/rights.json
    """
    object_id = '%s-%s' % (facet_id, term_id)
    offset = int(request.GET.get('offset', 0))
    data = Term.objects(facet_id, term_id, request, limit=limit, offset=offset)
    return _list(request, data)

@api_view(['GET'])
def object_detail(request, object_id):
    """Information for a specific object.
    """
    # TODO just get doc_type
    document = DOCSTORE.es.get(
        index=DOCSTORE.index_name(identifier.Identifier(object_id).model),
        id=object_id
    )
    model = document['_index'].replace(docstore.INDEX_PREFIX, '')
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
    """Detail for specified facet
    
    `facet_id`: "topics", "facility", "format", "genre", or "rights". 
    """
    data = Facet.get(facet_id, request)
    return _detail(request, data)

@api_view(['GET'])
def facetterm(request, facet_id, term_id, format=None):
    """Detail for specified facet term
    
    `facet_id`: "topics", "facility", "format", "genre", or "rights". 
    `term_id`: A term ID from one of the following lists:
    
    - http://partner.densho.org/vocab/api/0.2/topics.json
    - http://partner.densho.org/vocab/api/0.2/facility.json
    - http://partner.densho.org/vocab/api/0.2/format.json
    - http://partner.densho.org/vocab/api/0.2/genre.json
    - http://partner.densho.org/vocab/api/0.2/rights.json
    """
    object_id = '%s-%s' % (facet_id, term_id)
    data = Term.get(object_id, request)
    return _detail(request, data)
