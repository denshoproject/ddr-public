from collections import OrderedDict
import json
import os

from django.conf import settings
from django.http import HttpResponseRedirect

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.reverse import reverse

from DDR import docstore
from ui.identifier import Identifier, CHILDREN, CHILDREN_ALL
from ui.views import filter_if_branded
from ui import faceting
from ui import models

DEFAULT_LIMIT = 25

CHILDREN = {
    'repository': ['organization'],
    'organization': ['collection'],
    'collection': ['entity'],
    'entity': ['segment', 'file'],
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

def img_url(bucket, filename, request=None):
    """Constructs URL; sorl.thumbnail-friendly if request contains flag.

    sorl.thumbnail can make thumbnails from images on external systems,
    but fails when the source URL is behind a proxy e.g. CloudFlare.
    
    URLs are constructed from MEDIA_URL by default for the convenience
    of external users of the API.  MEDIA_URL_LOCAL is used if the request
    contains settings.MEDIA_URL_LOCAL_MARKER.
    
    @param bucket: str S3-style bucket, usually the collection ID.
    @param filename: str File name within the bucket.
    @param request: Django request object.
    @returns: URL or None
    """
    internal = 0
    if request:
        internal = request.GET.get(settings.MEDIA_URL_LOCAL_MARKER, 0)
    if internal and isinstance(internal, basestring) and internal.isdigit():
        internal = int(internal)
    if bucket and filename and internal:
        return '%s%s/%s' % (settings.MEDIA_URL_LOCAL, bucket, filename)
    elif bucket and filename:
        return '%s%s/%s' % (settings.MEDIA_URL, bucket, filename)
    return None

def pop_field(obj, fieldname):
    """Safely remove fields from objects.
    
    @param obj: dict
    @param fieldname: str
    """
    try:
        obj.pop(fieldname)
    except KeyError:
        pass


SEARCH_RETURN_FIELDS = [
    'id',
    'signature_id',
    'collection_id',
    'title',
    'description',
    'url',
    'access_rel',
    'sort',
]

def api_search(text='', must=[], should=[], mustnot=[], models=[], sort_fields=[], limit=DEFAULT_LIMIT, offset=0, request=None):
    """Return object children list in Django REST Framework format.
    
    Returns a paged list with count/prev/next metadata
    
    @returns: dict
    """
    if not isinstance(models, basestring):
        models = models
    elif isinstance(models, list):
        models = ','.join(models)
    else:
        raise Exception('model must be a string or a list')
    
    q = docstore.search_query(
        text=text,
        must=must,
        should=should,
        mustnot=mustnot
    )
    
    return format_list_objects(
        paginate_results(
            docstore.Docstore().search(
                doctypes=models,
                query=q,
                sort=sort_fields,
                fields=SEARCH_RETURN_FIELDS,
                from_=offset,
                size=limit,
            ),
            offset, limit, request
        ),
        request
    )

def api_children(request, model, object_id, sort_fields, limit=DEFAULT_LIMIT, offset=0):
    """Return object children list in Django REST Framework format.
    
    Returns a paged list with count/prev/next metadata
    
    @returns: dict
    """
    if not isinstance(model, basestring):
        models = model
    elif isinstance(model, list):
        models = ','.join(model)
    else:
        raise Exception('model must be a string or a list')
    
    q = docstore.search_query(
        must=[{"wildcard": {"id": "%s-*" % object_id}}],
    )
    return format_list_objects(
        paginate_results(
            docstore.Docstore().search(
                doctypes=model,
                query=q,
                sort=sort_fields,
                fields=SEARCH_RETURN_FIELDS,
                from_=offset,
                size=limit,
            ),
            offset, limit, request
        ),
        request
    )

def paginate_results(results, offset, limit, request=None):
    """Makes Elasticsearch results nicer to work with (doesn't actually paginate)
    
    Strips much of the raw ES stuff, adds total, page_size, prev/next links
    TODO format data to work with Django paginator?
    
    @param results: dict Output of docstore.Docstore().search
    @returns: list of dicts
    """
    offset = int(offset)
    limit = int(limit)
    data = OrderedDict()
    data['total'] = int(results['hits']['total'])
    data['page_size'] = limit
    
    data['prev'] = None
    data['next'] = None
    p = offset - limit
    n = offset + limit
    if p < 0:
        p = None
    if n >= data['total']:
        n = None
    if p is not None:
        data['prev'] = '?limit=%s&offset=%s' % (limit, p)
    if n:
        data['next'] = '?limit=%s&offset=%s' % (limit, n)
    
    data['hits'] = [hit for hit in results['hits']['hits']]
    return data

def format_object_detail(document, request, listitem=False):
    """Formats repository objects, adds list URLs,
    """
    if document and document.get('_source'):
        oid = document['_source'].pop('id')
        i = Identifier(oid)
        
        d = OrderedDict()
        d['id'] = oid
        d['model'] = document['_type']
        if not listitem:
            try:
                d['collection_id'] = i.collection_id()
            except:
                pass
        # links
        d['links'] = OrderedDict()
        if not listitem:
            if document.get('parent_id'):
                d['links']['parent'] = reverse(
                    'ui-api-object',
                    args=[document['parent_id']],
                    request=request
                )
            elif i.parent_id():
                d['links']['parent'] = reverse(
                    'ui-api-object',
                    args=[i.parent_id()],
                    request=request
                )
        d['links']['html'] = reverse(
            'ui-object-detail', args=[oid], request=request
        )
        d['links']['json'] = reverse(
            'ui-api-object', args=[oid], request=request
        )
        #if not listitem:
        #    d['links']['children'] = reverse(
        #        'ui-api-object-children',
        #        args=[i.id],
        #        request=request
        #    )
        # links-img
        if document['_source'].get('signature_id'):
            d['links']['img'] = img_url(
                i.collection_id(),
                access_filename(document['_source'].pop('signature_id')),
                request
            )
        elif i.model == 'file':
            d['links']['img'] = img_url(
                i.collection_id(),
                os.path.basename(document['_source'].pop('access_rel')),
                request
            )
        # title, description
        if document['_source'].get('title'):
            d['title'] = document['_source'].pop('title')
        if document['_source'].get('description'):
            d['description'] = document['_source'].pop('description')
        # everything else
        HIDDEN_FIELDS = [
            'repo','org','cid','eid','sid','role','sha1'
        ]
        for key in document['_source'].iterkeys():
            if key not in HIDDEN_FIELDS:
                d[key] = document['_source'][key]
        return d
    return None

def format_list_objects(results, request, function=format_object_detail):
    """Iterate through results objects apply format_object_detail function
    """
    results['objects'] = []
    while(results['hits']):
        hit = results['hits'].pop(0)
        results['objects'].append(
            function(hit, request, listitem=True)
        )
    return results

def pad_results(results, pagesize, thispage):
    """Returns result set objects with dummy objects before/after specified page
    
    This is necessary for displaying API results using the
    Django paginator.
    
    @param objects: dict Raw output of search API
    @param pagesize: int
    @param thispage: int
    @param total: int Total number of results
    @returns: list of objects
    """
    page_start = (thispage-1) * pagesize
    page_next = (thispage) * pagesize
    # pad before
    for n in range(0, page_start):
        results['objects'].insert(n, {'n':n})
    # pad after
    for n in range(page_next, results['total']):
        results['objects'].append({'n':n})
    return results['objects']


# classes --------------------------------------------------------------

class ApiRepository(object):
    
    @staticmethod
    def api_get(oid, request):
        i = Identifier(id=oid)
        document = docstore.Docstore().get(model=i.model, document_id=i.id)
        if not document:
            raise NotFound()
        data = format_object_detail(document, request)
        data['links']['children'] = reverse(
            'ui-api-object-children',
            args=[i.id],
            request=request
        )
        data['repository_url'] = data['url']
        return data

    @staticmethod
    def api_children(oid, request, limit=DEFAULT_LIMIT, offset=0):
        i = Identifier(id=oid)
        sort_fields = [
            ['repo','asc'],
            ['org','asc'],
            ['id','asc'],
        ]
        return api_children(
            request, CHILDREN[i.model], i.id, sort_fields, limit=limit, offset=offset
        )


class ApiOrganization(object):
    
    @staticmethod
    def api_get(oid, request):
        i = Identifier(id=oid)
        document = docstore.Docstore().get(model=i.model, document_id=i.id)
        if not document:
            raise NotFound()
        data = format_object_detail(document, request)
        data['links']['parent'] = reverse(
            'ui-api-object',
            args=[i.parent_id(stubs=1)],
            request=request
        )
        data['links']['children'] = reverse(
            'ui-api-object-children',
            args=[i.id],
            request=request
        )
        return data

    @staticmethod
    def api_children(oid, request, limit=DEFAULT_LIMIT, offset=0):
        i = Identifier(id=oid)
        sort_fields = [
            ['repo','asc'],
            ['org','asc'],
            ['cid','asc'],
            ['id','asc'],
        ]
        return api_children(
            request, CHILDREN[i.model], i.id, sort_fields, limit=limit, offset=offset
        )


class ApiCollection(object):
    
    @staticmethod
    def api_get(oid, request):
        i = Identifier(id=oid)
        idparts = [x for x in i.parts.itervalues()]
        document = docstore.Docstore().get(model=i.model, document_id=i.id)
        if not document:
            raise NotFound()
        data = format_object_detail(document, request)
        data['links']['parent'] = reverse(
            'ui-api-object',
            args=[i.parent_id(stubs=1)],
            request=request
        )
        data['links']['children'] = reverse(
            'ui-api-object-children',
            args=[i.id],
            request=request
        )
        HIDDEN_FIELDS = [
            'notes',
        ]
        for field in HIDDEN_FIELDS:
            pop_field(data, field)
        return data

    @staticmethod
    def api_children(oid, request, limit=DEFAULT_LIMIT, offset=0):
        i = Identifier(id=oid)
        sort_fields = [
            ['repo','asc'],
            ['org','asc'],
            ['cid','asc'],
            ['eid','asc'],
            ['id','asc'],
        ]
        return api_children(
            request, CHILDREN[i.model], i.id, sort_fields, limit=limit, offset=offset
        )


class ApiEntity(object):

    @staticmethod
    def term_url(request, data, facet_id, fieldname):
        """Convert facet term IDs to links to term API nodes.
        """
        for tid in data.get(fieldname, []):
            if isinstance(tid, dict) and tid.get('id'):
                url = reverse('ui-api-term', args=(facet_id, tid['id']), request=request)
                assert False
            elif tid:
                url = reverse('ui-api-term', args=(facet_id, tid), request=request)
        assert False
    
    @staticmethod
    def api_get(oid, request):
        i = Identifier(id=oid)
        document = docstore.Docstore().get(model=i.model, document_id=i.id)
        if not document:
            raise NotFound()
        data = format_object_detail(document, request)
        pop_field(data['links'], 'children')
        data['links']['children-objects'] = reverse(
            'ui-api-object-children', args=[oid], request=request
        )
        data['links']['children-files'] = reverse(
            'ui-api-object-nodes', args=[oid], request=request
        )
        for facet in ['facility', 'topics']:
            for x in data.get(facet, []):
                x['json'] = reverse(
                    'ui-api-term', args=[facet, x['id']], request=request
                )
                x['html'] = reverse(
                    'ui-browse-term', args=[facet, x['id']], request=request
                )
        HIDDEN_FIELDS = [
            'files',
            'notes',
            'parent',
            'status',
            'public',
        ]
        for field in HIDDEN_FIELDS:
            pop_field(data, field)
        return data

    @staticmethod
    def api_children(oid, request, limit=DEFAULT_LIMIT, offset=0):
        i = Identifier(id=oid)
        sort_fields = [
            ['repo','asc'],
            ['org','asc'],
            ['cid','asc'],
            ['eid','asc'],
            ['role','desc'],
            ['sort','asc'],
            ['sha1','asc'],
            ['id','asc'],
        ]
        models = CHILDREN[i.model]
        if 'file' in models:
            models.remove('file')
        return api_children(
            request, models, i.id, sort_fields, limit=limit, offset=offset
        )

    @staticmethod
    def api_nodes(oid, request, limit=DEFAULT_LIMIT, offset=0):
        i = Identifier(id=oid)
        sort_fields = [
            ['repo','asc'],
            ['org','asc'],
            ['cid','asc'],
            ['eid','asc'],
            ['role','desc'],
            ['sort','asc'],
            ['sha1','asc'],
            ['id','asc'],
        ]
        models = ['file']
        return api_children(
            request, models, i.id, sort_fields, limit=limit, offset=offset
        )


class ApiRole(object):

    @staticmethod
    def api_children(oid, request, limit=DEFAULT_LIMIT, offset=0):
        i = Identifier(id=oid)
        sort_fields = [
            ['repo','asc'],
            ['org','asc'],
            ['cid','asc'],
            ['eid','asc'],
            ['role','desc'],
            ['sort','asc'],
            ['sha1','asc'],
            ['id','asc'],
        ]
        return api_children(
            request, CHILDREN[i.model], i.id, sort_fields, limit=limit, offset=offset
        )


class ApiFile(object):
    
    @staticmethod
    def api_get(oid, request):
        i = Identifier(id=oid)
        idparts = [x for x in i.parts.itervalues()]
        collection_id = i.collection_id()
        document = docstore.Docstore().get(
            model=i.model, document_id=i.id
        )
        if not document:
            raise NotFound()
        data = format_object_detail(document, request)
        HIDDEN_FIELDS = [
            'public',
        ]
        for field in HIDDEN_FIELDS:
            pop_field(data, field)
        data['links']['download'] = img_url(
            data['collection_id'],
            data['path_rel'],
            request
        )
        return data

    @staticmethod
    def api_children(oid, request, limit=DEFAULT_LIMIT, offset=0):
        return {
            "count": 0,
            "prev": None,
            "next": None,
            "results": [],
        }

    
def format_narrator(document, request, listitem=False):
    if document and document.get('_source'):
        oid = document['_source'].pop('id')
        
        d = OrderedDict()
        d['id'] = oid
        d['model'] = 'narrator'
        # links
        d['links'] = OrderedDict()
        d['links']['html'] = reverse('ui-browse-narrator', args=[oid], request=request)
        d['links']['json'] = reverse('ui-api-narrator', args=[oid], request=request)
        d['links']['img'] = document['_source'].pop('image_url')
        d['links']['documents'] = ''
        # title, description
        if document['_source'].get('title'):
            d['title'] = document['_source'].pop('title')
        if document['_source'].get('description'):
            d['description'] = document['_source'].pop('description')
        # everything else
        HIDDEN_FIELDS = [
            'repo','org','cid','eid','sid','role','sha1'
        ]
        for key in document['_source'].iterkeys():
            if key not in HIDDEN_FIELDS:
                d[key] = document['_source'][key]
        return d
    return None

class ApiNarrator(object):
    
    @staticmethod
    def api_get(oid, request):
        document = docstore.Docstore().get(
            model='narrator', document_id=oid
        )
        if not document:
            raise NotFound()
        data = format_narrator(document, request)
        HIDDEN_FIELDS = [
            'notes',
        ]
        for field in HIDDEN_FIELDS:
            pop_field(data, field)
        return data
    
    @staticmethod
    def api_list(request, limit=DEFAULT_LIMIT, offset=0):
        SORT_FIELDS = [
            ['last_name','asc'],
            ['first_name','asc'],
            ['middle_name','asc'],
        ]
        LIST_FIELDS = [
            'id',
            'title',
            'image_url',
        ]
        q = docstore.search_query(
            must=[
                { "match_all": {}}
            ]
        )
        results = docstore.Docstore().search(
            doctypes=['narrator'],
            query=q,
            sort=SORT_FIELDS,
            fields=LIST_FIELDS,
            from_=offset,
            size=limit,
        )
        return format_list_objects(
            paginate_results(
                results,
                offset,
                limit,
                request
            ),
            request,
            format_narrator
        )


class ApiFacet(faceting.Facet):

    def api_data(self, request):
        data = {
            'id': self.id,
            'name': self.name,
            'title': self.title,
            'description': self.description,
            'json': reverse('ui-api-facet', args=[self.id,], request=request),
            'html': reverse('ui-browse-facet', args=[self.id,], request=request),
        }
        data['terms'] = [
            {
                'id': term.id,
                'title': term.title,
                'json': reverse('ui-api-term', args=(term.facet_id, term.id), request=request),
                'html': reverse('ui-browse-term', args=(term.facet_id, term.id), request=request),
            }
            for term in self.terms()
        ]
        return data
    
    def terms(self):
        if not self._terms:
            self._terms = []
            for t in self._terms_raw:
                term = ApiTerm(facet_id=self.id, term_id=t['id'])
                self._terms.append(term)
            self._terms_raw = None
        return self._terms


class ApiTerm(faceting.Term):
        
    def api_data(self, request):
        data = {
            'id': self.id,
            'parent_id': self.parent_id,
            'facet_id': self.facet_id,
            'title': self.title,
            'description': self.description,
            'weight': self.weight,
            'created': self.created,
            'modified': self.modified,
            'encyclopedia': self.encyc_urls,
            'links': {
                'json': reverse('ui-api-term', args=(self.facet_id, self.id), request=request),
                'html': self.url(),
                'parent': '',
            },
        }
        if self.parent_id:
            data['links']['parent'] = reverse(
                'ui-api-term',
                args=[self.facet_id, self.parent_id],
                request=request)
        data['links']['ancestors'] = [
            reverse('ui-api-term', args=[self.facet_id, tid], request=request)
            for tid in self._ancestors
        ]
        data['links']['siblings'] = [
            reverse('ui-api-term', args=[self.facet_id, tid], request=request)
            for tid in self._siblings
        ]
        data['links']['children'] = [
            reverse('ui-api-term', args=[self.facet_id, tid], request=request)
            for tid in self._children
        ]
        data['links']['objects'] = reverse(
            'ui-api-term-objects',
            args=[self.facet_id, self.id],
            request=request
        )
        return data
    
    def objects(self, limit=DEFAULT_LIMIT, offset=0, request=None):
        """
        http://DOMAIN/api/0.1/facet/{facet_id}/{term_id}/objects/?{internal=1}&{limit=5}
        """
        field = '%s.id' % self.facet_id
        return api_search(
            must=[
                {'terms': {field: [self.id]}},
            ],
            models=[],
            sort_fields=[
                'record_created',
                'record_lastmod',
            ],
            limit=limit,
            offset=offset,
            request=request
        )


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
        data = api_search(
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
    i = Identifier(id=oid)
    if i.model == 'repository': return organizations(request, oid)
    elif i.model == 'organization': return collections(request, oid)
    elif i.model == 'collection': return entities(request, oid)
    elif i.model == 'entity': return segments(request, oid)
    elif i.model == 'segment': return files(request, oid)
    elif i.model == 'file': assert False
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
    data = ApiRepository.api_children(oid, request, offset=offset)
    return _list(request, data)

@api_view(['GET'])
def collections(request, oid, format=None):
    offset = int(request.GET.get('offset', 0))
    data = ApiOrganization.api_children(oid, request, offset=offset)
    return _list(request, data)

@api_view(['GET'])
def entities(request, oid, format=None):
    offset = int(request.GET.get('offset', 0))
    data = ApiCollection.api_children(oid, request, offset=offset)
    return _list(request, data)

@api_view(['GET'])
def segments(request, oid, format=None):
    offset = int(request.GET.get('offset', 0))
    data = ApiEntity.api_children(oid, request, offset=offset)
    return _list(request, data)

@api_view(['GET'])
def files(request, oid, format=None):
    offset = int(request.GET.get('offset', 0))
    data = ApiEntity.api_nodes(oid, request, offset=offset)
    return _list(request, data)


@api_view(['GET'])
def object_detail(request, oid):
    """OBJECT DETAIL DOCS
    """
    i = Identifier(id=oid)
    if i.model == 'repository': return repository(request, oid)
    elif i.model == 'organization': return organization(request, oid)
    elif i.model == 'collection': return collection(request, oid)
    elif i.model == 'entity': return entity(request, oid)
    elif i.model == 'segment': return entity(request, oid)
    elif i.model == 'file': return file(request, oid)
    raise Exception("Could not match ID,model,view.")

def _detail(request, data):
    """Common function for detail views.
    """
    if not data:
	return Response(status=status.HTTP_404_NOT_FOUND)
    return Response(data)

@api_view(['GET'])
def repository(request, oid, format=None):
    data = ApiRepository.api_get(oid, request)
    return _detail(request, data)

@api_view(['GET'])
def organization(request, oid, format=None):
    data = ApiOrganization.api_get(oid, request)
    return _detail(request, data)

@api_view(['GET'])
def collection(request, oid, format=None):
    filter_if_branded(request, oid)
    data = ApiCollection.api_get(oid, request)
    return _detail(request, data)

@api_view(['GET'])
def entity(request, oid, format=None):
    filter_if_branded(request, oid)
    data = ApiEntity.api_get(oid, request)
    return _detail(request, data)

@api_view(['GET'])
def file(request, oid, format=None):
    filter_if_branded(request, oid)
    data = ApiFile.api_get(oid, request)
    return _detail(request, data)

@api_view(['GET'])
def narrator_index(request, format=None):
    offset = int(request.GET.get('offset', 0))
    data = ApiNarrator.api_list(request, offset=offset)
    return _list(request, data)

@api_view(['GET'])
def narrator(request, oid, format=None):
    data = ApiNarrator.api_get(oid, request)
    return _detail(request, data)

@api_view(['GET'])
def facet_index(request, format=None):
    data = {
        'topics': reverse('ui-api-facet', args=['topics',], request=request),
        'facility': reverse('ui-api-facet', args=['facility',], request=request),
    }
    return Response(data)

@api_view(['GET'])
def facet(request, facet, format=None):
    facet = ApiFacet(facet)
    data = facet.api_data(request)
    return Response(data)

@api_view(['GET'])
def term(request, facet_id, term_id, format=None):
    term = ApiTerm(facet_id=facet_id, term_id=term_id)
    data = term.api_data(request)
    return Response(data)

@api_view(['GET'])
def term_objects(request, facet_id, term_id, format=None):
    """
    http://DOMAIN/api/0.1/facet/{facet_id}/{term_id}/objects/?{internal=1}&{limit=5}
    """
    term = ApiTerm(facet_id=facet_id, term_id=term_id)
    data = term.objects(request)
    return Response(data)
