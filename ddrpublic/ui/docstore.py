import json
import logging
logger = logging.getLogger(__name__)

from django.conf import settings

from elasticsearch import Elasticsearch

MAX_SIZE = 1000


class Docstore():

    def __init__(self, hosts=settings.DOCSTORE_HOSTS, index=settings.DOCSTORE_INDEX, connection=None):
        self.hosts = hosts
        self.indexname = index
        if connection:
            self.es = connection
        else:
            self.es = Elasticsearch(hosts)
     
    def exists(self, model, document_id):
        """
        @param model:
        @param document_id:
        """
        return self.es.exists(index=self.indexname, doc_type=model, id=document_id)
     
    def get(self, model, document_id, fields=None):
        """
        @param model:
        @param document_id:
        @param fields: boolean Only return these fields
        """
        if self.exists(model, document_id):
            ES_Class = ELASTICSEARCH_CLASSES_BY_MODEL[model]
            return ES_Class.get(document_id, using=self.es, index=self.indexname)
        return None

    def count(self, doctypes=[], query={}):
        """Executes a query and returns number of hits.
        
        The "query" arg must be a dict that conforms to the Elasticsearch query DSL.
        See docstore.search_query for more info.
        
        @param doctypes: list Type of object ('collection', 'entity', 'file')
        @param query: dict The search definition using Elasticsearch Query DSL
        @returns raw ElasticSearch query output
        """
        logger.debug('count(index=%s, doctypes=%s, query=%s' % (
            self.indexname, doctypes, query
        ))
        if not query:
            raise Exception("Can't do an empty search. Give me something to work with here.")
        
        doctypes = ','.join(doctypes)
        logger.debug(json.dumps(query))
        
        return self.es.count(
            index=self.indexname,
            doc_type=doctypes,
            body=query,
        )
    
    def search(self, doctypes=[], query={}, sort=[], fields=[], from_=0, size=MAX_SIZE):
        """Executes a query, get a list of zero or more hits.
        
        The "query" arg must be a dict that conforms to the Elasticsearch query DSL.
        See docstore.search_query for more info.
        
        @param doctypes: list Type of object ('collection', 'entity', 'file')
        @param query: dict The search definition using Elasticsearch Query DSL
        @param sort: list of (fieldname,direction) tuples
        @param fields: str
        @param from_: int Index of document from which to start results
        @param size: int Number of results to return
        @returns raw ElasticSearch query output
        """
        logger.debug('search(index=%s, doctypes=%s, query=%s, sort=%s, fields=%s, from_=%s, size=%s' % (
            self.indexname, doctypes, query, sort, fields, from_, size
        ))
        if not query:
            raise Exception("Can't do an empty search. Give me something to work with here.")
        
        doctypes = ','.join(doctypes)
        logger.debug(json.dumps(query))
        _clean_dict(sort)
        sort_cleaned = _clean_sort(sort)
        fields = ','.join(fields)
        
        results = self.es.search(
            index=self.indexname,
            doc_type=doctypes,
            body=query,
            sort=sort_cleaned,
            from_=from_,
            size=size,
            _source_include=fields,
        )
        return results


def aggs_dict(aggregations):
    """Simplify aggregations data in search results
    
    input
    {
    u'format': {u'buckets': [{u'doc_count': 2, u'key': u'ds'}], u'doc_count_error_upper_bound': 0, u'sum_other_doc_count': 0},
    u'rights': {u'buckets': [{u'doc_count': 3, u'key': u'cc'}], u'doc_count_error_upper_bound': 0, u'sum_other_doc_count': 0},
    }
    output
    {
    u'format': {u'ds': 2},
    u'rights': {u'cc': 3},
    }
    """
    return {
        fieldname: {
            bucket['key']: bucket['doc_count']
            for bucket in data['buckets']
        }
        for fieldname,data in aggregations.iteritems()
    }

def aliases_indices():
    """Lists host and alias(es) with target index(es).
    
    @returns: dict {'host', 'aliases': []}
    """
    return [
        {'index':a[0], 'alias':a[1]}
        for a in docstore.Docstore().aliases()
        if a[1] in [
            settings.DOCSTORE_INDEX,
            settings.NAMESDB_DOCSTORE_INDEX
        ]
    ]

def search_query(text='', must=[], should=[], mustnot=[], aggs={}):
    """Assembles a dict conforming to the Elasticsearch query DSL.
    
    Elasticsearch query dicts
    See https://www.elastic.co/guide/en/elasticsearch/guide/current/_most_important_queries.html
    - {"match": {"fieldname": "value"}}
    - {"multi_match": {
        "query": "full text search",
        "fields": ["fieldname1", "fieldname2"]
      }}
    - {"terms": {"fieldname": ["value1","value2"]}},
    - {"range": {"fieldname.subfield": {"gt":20, "lte":31}}},
    - {"exists": {"fieldname": "title"}}
    - {"missing": {"fieldname": "title"}}
    
    Elasticsearch aggregations
    See https://www.elastic.co/guide/en/elasticsearch/guide/current/aggregations.html
    aggs = {
        'formats': {'terms': {'field': 'format'}},
        'topics': {'terms': {'field': 'topics'}},
    }
    
    >>> from ui import docstore,format_json
    >>> t = 'posthuman'
    >>> a = [{'terms':{'language':['eng','chi']}}, {'terms':{'creators.role':['distraction']}}]
    >>> q = docstore.search_query(text=t, must=a)
    >>> print(format_json(q))
    >>> d = ['entity','segment']
    >>> f = ['id','title']
    >>> results = docstore.Docstore().search(doctypes=d, query=q, fields=f)
    >>> for x in results['hits']['hits']:
    ...     print x['_source']
    
    @param text: str Free-text search.
    @param must: list of Elasticsearch query dicts (see above)
    @param should:  list of Elasticsearch query dicts (see above)
    @param mustnot: list of Elasticsearch query dicts (see above)
    @param aggs: dict Elasticsearch aggregations subquery (see above)
    @returns: dict
    """
    body = {
        "query": {
            "bool": {
                "must": must,
                "should": should,
                "must_not": mustnot,
            }
        }
    }
    if text:
        body['query']['bool']['must'].append(
            {
                "match": {
                    "_all": text
                }
            }
        )
    if aggs:
        body['aggregations'] = aggs
    return body


class InvalidPage(Exception):
    pass
class PageNotAnInteger(InvalidPage):
    pass
class EmptyPage(InvalidPage):
    pass

def _validate_number(number, num_pages):
        """Validates the given 1-based page number.
        see django.core.pagination.Paginator.validate_number
        """
        try:
            number = int(number)
        except (TypeError, ValueError):
            raise PageNotAnInteger('That page number is not an integer')
        if number < 1:
            raise EmptyPage('That page number is less than 1')
        if number > num_pages:
            if number == 1:
                pass
            else:
                raise EmptyPage('That page contains no results')
        return number

def _page_bottom_top(total, index, page_size):
        """
        Returns a Page object for the given 1-based page number.
        """
        num_pages = total / page_size
        if total % page_size:
            num_pages = num_pages + 1
        number = _validate_number(index, num_pages)
        bottom = (number - 1) * page_size
        top = bottom + page_size
        return bottom,top,num_pages

def massage_query_results(results, thispage, page_size):
    """Takes ES query, makes facsimile of original object; pads results for paginator.
    
    Problem: Django Paginator only displays current page but needs entire result set.
    Actually, it just needs a list that is the same size as the actual result set.
    
    GOOD:
    Do an ElasticSearch search, without ES paging.
    Loop through ES results, building new list, process only the current page's hits
    hits outside current page added as placeholders
    
    BETTER:
    Do an ElasticSearch search, *with* ES paging.
    Loop through ES results, building new list, processing all the hits
    Pad list with empty objects fore and aft.
    
    @param results: ElasticSearch result set (non-empty, no errors)
    @param thispage: Value of GET['page'] or 1
    @param page_size: Number of objects per page
    @returns: list of hit dicts, with empty "hits" fore and aft of current page
    """
    def unlistify(o, fieldname):
        if o.get(fieldname, None):
            if isinstance(o[fieldname], list):
                o[fieldname] = o[fieldname][0]
    
    objects = []
    if results and results['hits']:
        total = results['hits']['total']
        bottom,top,num_pages = _page_bottom_top(total, thispage, page_size)
        # only process this page
        for n,hit in enumerate(results['hits']['hits']):
            o = {'n':n,
                 'id': hit['_id'],
                 'placeholder': True}
            if (n >= bottom) and (n < top):
                # if we tell ES only return certain fields, object is in 'fields'
                if hit.get('fields', None):
                    o = hit['fields']
                elif hit.get('_source', None):
                    o = hit['_source']
                # copy ES results info to individual object source
                o['index'] = hit['_index']
                o['type'] = hit['_type']
                o['model'] = hit['_type']
                o['id'] = hit['_id']
                # ElasticSearch wraps field values in lists
                # when you use a 'fields' array in a query
                for fieldname in all_list_fields():
                    unlistify(o, fieldname)
            objects.append(o)
    return objects

def _clean_dict(data):
    """Remove null or empty fields; ElasticSearch chokes on them.
    
    >>> d = {'a': 'abc', 'b': 'bcd', 'x':'' }
    >>> _clean_dict(d)
    >>> d
    {'a': 'abc', 'b': 'bcd'}
    
    @param data: Standard DDR list-of-dicts data structure.
    """
    if data and isinstance(data, dict):
        for key in data.keys():
            if not data[key]:
                del(data[key])

def _clean_sort( sort ):
    """Take list of [a,b] lists, return comma-separated list of a:b pairs
    
    >>> _clean_sort( 'whatever' )
    >>> _clean_sort( [['a', 'asc'], ['b', 'asc'], 'whatever'] )
    >>> _clean_sort( [['a', 'asc'], ['b', 'asc']] )
    'a:asc,b:asc'
    """
    cleaned = ''
    if sort and isinstance(sort,list):
        all_lists = [1 if isinstance(x, list) else 0 for x in sort]
        if not 0 in all_lists:
            cleaned = ','.join([':'.join(x) for x in sort])
    return cleaned
