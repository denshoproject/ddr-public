from collections import OrderedDict

from django.conf import settings

from elasticsearch import Elasticsearch

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request as RestRequest
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView

from elastictools import docstore
from elastictools import search
from namesdb.definitions import SEARCH_FIELDS as NAMESDB_SEARCH_FIELDS
from . import models

DEFAULT_LIMIT = 25


# views ----------------------------------------------------------------

@api_view(['GET'])
def index(request, format=None):
    """Swagger UI: /api/swagger/
    """
    repo = 'ddr'
    data = {
        'search': reverse('names-api-search', request=request),
    }
    return Response(data)


@api_view(['GET'])
def object_nodes(request, object_id):
    return files(request._request, object_id)

def _list(request, data):
    host = request.META.get('HTTP_HOST')
    path = request.META['PATH_INFO']
    if data.get('prev'):
        data['prev'] = 'http://%s%s%s' % (host, path, data['prev'])
    if data.get('next'):
        data['next'] = 'http://%s%s%s' % (host, path, data['next'])
    return Response(data)

def _detail(request, data):
    """Common function for detail views.
    """
    if not data:
        return Response(status=status.HTTP_404_NOT_FOUND)
    return Response(data)

@api_view(['GET'])
def name(request, object_id, format=None):
    data = models.NameRecord.get(object_id, request)
    return _detail(request, data)


class Search(APIView):
    
    def get(self, request, format=None):
        """Search the Names Database; good for simpler searches.
        
        `fulltext`: Search string using Elasticsearch query_string syntax.
        `m_camp`: One or more camp IDs e.g. "9-rohwer".
        `page`: Selected results page (default: 0).

        Search API help: /api/search/help/
        """
        if request.GET.get('fulltext'):
            return self.grep(request)
        return Response({})
    
    def post(self, request, format=None):
        """Search the Names Database; good for more complicated custom searches.
        
        `fulltext`: Search string using Elasticsearch query_string syntax.
        `m_camp`: One or more camp IDs e.g. "9-rohwer".
        `page`: Selected results page (default: 0).
        
        Search API help: /api/search/help/
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
        
        searcher = search.Searcher()
        if isinstance(request, HttpRequest):
            params = request.GET.copy()
        elif isinstance(request, RestRequest):
            params = request.query_params.dict()
        searcher.prepare(
            params=params,
            params_whitelist=['fulltext', 'm_camp'],
            search_models=['names-record'],
            fields=NAMESDB_SEARCH_FIELDS,
            fields_nested=[],
            fields_agg={'m_camp':'m_camp'},
            wildcards=False,
        )
        results = searcher.execute(limit, offset)
        return Response(
            results.ordered_dict(request, format_functions=models.FORMATTERS)
        )
