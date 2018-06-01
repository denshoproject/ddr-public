from collections import defaultdict, OrderedDict
import logging
logger = logging.getLogger(__name__)
import os
import urlparse

import requests
from elasticsearch import Elasticsearch
import elasticsearch_dsl

from django.conf import settings
from django.core.cache import cache

from rest_framework.exceptions import NotFound
from rest_framework.reverse import reverse

from . import docstore
from . import search

es = Elasticsearch(settings.DOCSTORE_HOSTS)

DEFAULT_SIZE = 10
DEFAULT_LIMIT = 25

CHILDREN = {
    'repository': ['organization'],
    'organization': ['collection'],
    'collection': ['entity'],
    'entity': ['entity', 'segment', 'file'],
    'segment': ['file'],
    'file': [],
}

# TODO Hard-coded! Get this data from Elasticsearch or something
MODEL_PLURALS = {
    'file':         'files',
    'segment':      'entities',
    'entity':       'entities',
    'collection':   'collections',
    'organization': 'organizations',
    'repository':   'Repositories',
    'narrator':     'narrators',
    'facet':        'facet',
    'facetterm':    'facetterm',
}

# TODO move to ddr-defs
REPOSITORY_LIST_FIELDS = ['id', 'model', 'title', 'description', 'url',]
ORGANIZATION_LIST_FIELDS = ['id', 'model', 'title', 'description', 'url',]
COLLECTION_LIST_FIELDS = ['id', 'model', 'title', 'description', 'signature_id',]
ENTITY_LIST_FIELDS = ['id', 'model', 'title', 'description', 'signature_id',]
FILE_LIST_FIELDS = ['id', 'model', 'title', 'description', 'access_rel','sort',]

# TODO mode to ddr-defs: knows too much about structure of ID
#      Does Elasticsearch have lambda functions for sorting?
REPOSITORY_LIST_SORT = [
    ['repo','asc'],
]
ORGANIZATION_LIST_SORT = [
    ['repo','asc'],
    ['org','asc'],
]
COLLECTION_LIST_SORT = [
    ['repo','asc'],
    ['org','asc'],
    ['cid','asc'],
    ['id','asc'],
]
ENTITY_LIST_SORT = [
    ['repo','asc'],
    ['org','asc'],
    ['cid','asc'],
    ['eid','asc'],
    ['id','asc'],
]
FILE_LIST_SORT = [
    ['repo','asc'],
    ['org','asc'],
    ['cid','asc'],
    ['eid','asc'],
    ['sort','asc'],
    ['role','desc'],
    ['id','asc'],
]

MODEL_LIST_SETTINGS = {
    'repository': {'fields': REPOSITORY_LIST_FIELDS, 'sort': REPOSITORY_LIST_SORT},
    'organization': {'fields': ORGANIZATION_LIST_FIELDS, 'sort': ORGANIZATION_LIST_SORT},
    'collection': {'fields': COLLECTION_LIST_FIELDS, 'sort': COLLECTION_LIST_SORT},
    'entity': {'fields': ENTITY_LIST_FIELDS, 'sort': ENTITY_LIST_SORT},
    'segment': {'fields': ENTITY_LIST_FIELDS, 'sort': ENTITY_LIST_SORT},
    'file': {'fields': FILE_LIST_FIELDS, 'sort': FILE_LIST_SORT},
}

def all_list_fields():
    LIST_FIELDS = []
    for mf in [REPOSITORY_LIST_FIELDS, ORGANIZATION_LIST_FIELDS,
               COLLECTION_LIST_FIELDS, ENTITY_LIST_FIELDS, FILE_LIST_FIELDS]:
        for f in mf:
            if f not in LIST_FIELDS:
                LIST_FIELDS.append(f)
    return LIST_FIELDS

SEARCH_RETURN_FIELDS = [
    'id',
    'model',
    'links_html',
    'links_json',
    'links_img',
    'links_thumb',
    'title',
    'description',
    'access_rel',
    'alternate_id',
    'bio',
    'collection_id',
    'display_name',
    'extent',
    'facet',
    'format',
    'image_url',
    'mimetype',
    'role',
    'signature_id',
    'sort',
    'url',
]

MEDIA_LOCAL_SCHEME = urlparse.urlparse(settings.MEDIA_URL_LOCAL).scheme
MEDIA_LOCAL_HOSTNAME = urlparse.urlparse(settings.MEDIA_URL_LOCAL).hostname


class AttributeDict():
    """Wraps OrderedDict, makes it appear to be an object.
    Lets user access data as attributes (using .) rather than dict keys (['']).
    """
    data = OrderedDict()
    def __repr__(self):
        return str(self.data)
    def __getattr__(self, attr):
        return self.data[attr]
    def __setattr__(self, attr, value):
        self.data[attr] = value


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

def narrator_img_url(image_url):
    return os.path.join(settings.NARRATORS_URL, image_url)

def local_thumb_url(url, request=None):
    """Replaces thumbnail domain with local IP addr (or domain?)
    This is necessary because CloudFlare
    """
    if not request:
        return ''
    # hide thumb links in the REST API unless DEBUG is on
    show_thumb_links = False
    if request and (request.META['PATH_INFO'][:len(settings.API_BASE)] != settings.API_BASE):
        show_thumb_links = True
    elif settings.DEBUG:
        show_thumb_links = True
    
    if url and settings.MEDIA_URL_LOCAL and show_thumb_links:
        u = urlparse.urlparse(url)
        return urlparse.urlunsplit(
            (MEDIA_LOCAL_SCHEME, MEDIA_LOCAL_HOSTNAME, u.path, u.params, u.query)
        )
    return url

def file_size(url):
    """Get the size of a file from HTTP headers (without downloading)
    
    @param url: str
    @returns: int
    """
    r = requests.head(url)
    if r.status_code == 200:
        return r.headers['Content-Length']
    return 0


def pop_field(obj, fieldname):
    """Safely remove fields from objects.
    
    @param obj: dict
    @param fieldname: str
    """
    try:
        obj.pop(fieldname)
    except KeyError:
        pass


def search_offset(thispage, pagesize):
    """Calculate index for start of current page
    
    @param thispage: int The current pagep (1-indexed)
    @param pagesize: int Number of items per page
    @returns: int offset
    """
    return pagesize * (thispage - 1)

def docstore_search(text='', must=[], should=[], mustnot=[], models=[], fields=[], sort_fields=[], limit=DEFAULT_LIMIT, offset=0, aggs={}, request=None):
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

    if not fields:
        fields = SEARCH_RETURN_FIELDS
    
    q = docstore.search_query(
        text=text,
        must=must,
        should=should,
        mustnot=mustnot,
        aggs=aggs,
    )
    return format_list_objects(
        paginate_results(
            docstore.Docstore().search(
                doctypes=models,
                query=q,
                sort=sort_fields,
                fields=fields,
                from_=offset,
                size=limit,
            ),
            offset, limit, request
        ),
        request
    )

def _object(request, oid, format=None):
    data = es.get(index=settings.DOCSTORE_INDEX, doc_type='_all', id=oid)
    return format_object_detail2(data, request)

def _object_children(document, request, models=[], sort_fields=[], limit=DEFAULT_LIMIT, offset=0):
    if not models:
        models = CHILDREN[document['model']]
    if not sort_fields:
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
    data = children(
        request=request,
        model=models,
        parent_id=document['id'],
        sort_fields=sort_fields,
        limit=limit, offset=offset
    )
    for d in data['objects']:
        d['links']['thumb'] = local_thumb_url(d['links'].get('img',''), request)
    return data

def children(request, model, parent_id, sort_fields, limit=DEFAULT_LIMIT, offset=0, just_count=False):
    """Return object children list in Django REST Framework format.
    
    Returns a paged list with count/prev/next metadata
    
    @param request: Django request object.
    @param model: str
    @param parent_id: str
    @param sort_fields: list
    @param limit: int
    @param offset: int
    @param just_count: boolean
    @returns: dict
    """
    if not isinstance(model, basestring):
        models = model
    elif isinstance(model, list):
        models = ','.join(model)
    else:
        raise Exception('model must be a string or a list')
    q = docstore.search_query(
        must=[
            {"term": {"parent_id": parent_id}},
        ],
    )
    if just_count:
        return docstore.Docstore().count(
            doctypes=model,
            query=q,
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

def count_children(model, parent_id):
    """Return count of object's children
    
    @param model: str
    @param parent_id: str
    @returns: dict
    """
    if not isinstance(model, basestring):
        models = model
    elif isinstance(model, list):
        models = ','.join(model)
    else:
        raise Exception('model must be a string or a list')
    q = docstore.search_query(
        must=[
            {"term": {"parent_id": parent_id}},
        ],
    )
    r = docstore.Docstore().count(
        doctypes=model,
        query=q,
    )
    return r['count']

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
    data['aggregations'] = results.get('aggregations', {})
    return data

def format_object_detail2(document, request, listitem=False):
    """Formats repository objects, adds list URLs,
    """
    if document.get('_source'):
        oid = document['_id']
        model = document['_type']
        document = document['_source']
    else:
        oid = document.pop('id')
        model = document.pop('model')

    d = OrderedDict()
    d['id'] = oid
    d['model'] = model
    
    if not listitem:
        d['collection_id'] = document.get('collection_id')
    # links
    d['links'] = OrderedDict()
    d['links']['html'] = reverse(
        'ui-object-detail', args=[document.pop('links_html')], request=request
    )
    d['links']['json'] = reverse(
        'ui-api-object', args=[document.pop('links_json')], request=request
    )
    if document.get('mimetype') and ('text' in document['mimetype']):
        d['links']['download'] = '%s%s' % (settings.MEDIA_URL, document.pop('links_img'))
    else:
        d['links']['img'] = '%s%s' % (settings.MEDIA_URL, document.pop('links_img'))
        d['links']['thumb'] = '%s%s' % (settings.MEDIA_URL_LOCAL, document.pop('links_thumb'))
        if document.get('links_download'):
            d['links']['download'] = '%s%s' % (settings.MEDIA_URL_LOCAL, document.pop('links_download'))
    
    if not listitem:
        if document.get('parent_id'):
            d['links']['parent'] = reverse(
                'ui-api-object',
                args=[document.pop('links_parent')],
                request=request
            )
        if CHILDREN[model]:
            if model in ['entity', 'segment']:
                d['links']['children-objects'] = reverse(
                    'ui-api-object-children',
                    args=[document['links_children']],
                    request=request
                )
                d['links']['children-files'] = reverse(
                    'ui-api-object-nodes',
                    args=[document['links_children']],
                    request=request
                )
                document.pop('links_children')
            else:
                d['links']['children'] = reverse(
                    'ui-api-object-children',
                    args=[document['links_children']],
                    request=request
                )
                document.pop('links_children')
        d['parent_id'] = document.get('parent_id', '')
        d['organization_id'] = document.get('organization_id', '')
        # gfroh: every object must have signature_id
        # gjost: except objects that don't have them
        d['signature_id'] = document.get('signature_id', '')
    # title, description
    d['title'] = document['title']
    d['description'] = document['description']
    if not listitem:
        if document.get('lineage'):
            crumbs = [c for c in document.pop('lineage')[::-1]]
            for c in crumbs:
                c['api_url'] = reverse(
                    'ui-api-object', args=[c['id']], request=request
                )
                c['url'] = reverse(
                    'ui-object-detail', args=[c['id']], request=request
                )
            d['breadcrumbs'] = crumbs
    # everything else
    HIDDEN_FIELDS = [
        'repo','org','cid','eid','sid','sha1'
         # don't hide role, used in file list-object
    ]
    for key in document.iterkeys():
        if key not in HIDDEN_FIELDS:
            d[key] = document[key]
    return d

def format_narrator(document, request, listitem=False):
    if document and document.get('_source'):
        oid = document['_source'].pop('id')
        
        d = OrderedDict()
        d['id'] = oid
        d['model'] = 'narrator'
        # links
        d['links'] = OrderedDict()
        d['links']['html'] = reverse('ui-narrators-detail', args=[oid], request=request)
        d['links']['json'] = reverse('ui-api-narrator', args=[oid], request=request)
        d['links']['img'] = narrator_img_url(document['_source'].pop('image_url'))
        d['links']['thumb'] = local_thumb_url(d['links'].get('img',''), request)
        d['links']['interviews'] = reverse('ui-api-narrator-interviews', args=[oid], request=request)
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

def format_facet(document, request, listitem=False):
    if document.get('_source'):
        oid = document['_id']
        model = document['_type']
        document = document['_source']
    else:
        oid = document.pop('id')
        model = document.pop('model')

    d = OrderedDict()
    d['id'] = oid
    d['model'] = model
    # links
    d['links'] = OrderedDict()
    d['links']['html'] = reverse(
        'ui-object-detail', args=[oid], request=request
    )
    d['links']['json'] = reverse(
        'ui-api-facet', args=[oid], request=request
    )
    d['links']['children'] = reverse(
        'ui-api-facetterms',
        args=[oid],
        request=request
    )
    d['title'] = document['title']
    if document.get('description'):
        d['description'] = document['description']
    return d

def format_term(document, request, listitem=False):
    if document.get('_source'):
        oid = document['_id']
        model = document['_type']
        document = document['_source']
    else:
        oid = document.pop('id')
        model = document.pop('model')

    facet_id = document['facet']
    term_id = document.pop('term_id')
    
    d = OrderedDict()
    d['id'] = oid
    d['model'] = model
    d['facet'] = document.pop('facet')
    d['term_id'] = term_id
    # links
    d['links'] = OrderedDict()
    d['links']['json'] = reverse('ui-api-term', args=[facet_id,term_id], request=request)
    d['links']['html'] = reverse('ui-browse-term', args=[facet_id,term_id], request=request)
    if document.get('parent_id'):
        d['links']['parent'] = reverse('ui-api-term', args=[facet_id,document['parent_id']], request=request)
    if document.get('ancestors'):
        d['links']['ancestors'] = [
            reverse('ui-api-term', args=[facet_id,tid], request=request)
            for tid in document['ancestors']
        ]
    if document.get('siblings'):
        d['links']['siblings'] = [
            reverse('ui-api-term', args=[facet_id,tid], request=request)
            for tid in document['siblings']
        ]
    if document.get('children'):
        d['links']['children'] = [
            reverse('ui-api-term', args=[facet_id,tid], request=request)
            for tid in document['children']
        ]
    d['links']['objects'] = reverse('ui-api-term-objects', args=[facet_id,term_id], request=request)
    # title, description
    if document.get('_title'): d['_title'] = document.pop('_title')
    if document.get('title'): d['title'] = document.pop('title')
    if document.get('description'): d['description'] = document.pop('description')
    # cleanup
    if document.get('links_json'): document.pop('links_json')
    if document.get('links_html'): document.pop('links_html')
    # everything else
    HIDDEN_FIELDS = [
        'created',
        'modified',
        'parent_id',
        #'ancestors',
        #'siblings',
        #'children',
    ]
    for key in document.iterkeys():
        if key not in HIDDEN_FIELDS:
            d[key] = document[key]
    return d

FORMATTERS = {
    'narrator': format_narrator,
    'facet': format_facet,
    'facetterm': format_term,
}

def format_list_objects(results, request, function=format_object_detail2):
    """Iterate through results objects apply format_object_detail function
    """
    results['objects'] = []
    while(results['hits']):
        hit = results['hits'].pop(0)
        doctype = hit['_type']
        function = FORMATTERS.get(doctype, format_object_detail2)
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

def facet_labels():
    """Labels for the various facet types.
    
    @returns: dict of facet ids mapped to labels
    """
    key = 'facet:ids-labels'
    cached = cache.get(key)
    if not cached:
        
        SORT_FIELDS = ['id', 'title',]
        LIST_FIELDS = ['id', 'facet', 'title',]
        q = docstore.search_query(
            should=[
                {"terms": {"facet": [
                    'format', 'genre', 'language', 'rights',
                ]}}
            ]
        )
        results = docstore.Docstore().search(
            doctypes=['facetterm'],
            query=q,
            sort=SORT_FIELDS,
            fields=LIST_FIELDS,
            from_=0,
            size=10000,
        )
        ids_labels = {}
        for hit in results['hits']['hits']:
            d = hit['_source']
            if not ids_labels.get(d['facet']):
                ids_labels[d['facet']] = {}
            ids_labels[d['facet']][d['id']] = d['title']
        
        cached = ids_labels
        cache.set(key, cached, settings.CACHE_TIMEOUT)
    return cached

FACET_LABELS = facet_labels()


# classes --------------------------------------------------------------


class Repository(object):
    
    @staticmethod
    def get(oid, request):
        return _object(request, oid)

    @staticmethod
    def children(oid, request, limit=DEFAULT_LIMIT, offset=0):
        return _object_children(
            document=_object(request, oid),
            request=request,
            limit=limit,
            offset=offset
        )


class Organization(object):

    @staticmethod
    def get(oid, request):
        return _object(request, oid)

    @staticmethod
    def children(oid, request, limit=DEFAULT_LIMIT, offset=0):
        return _object_children(
            document=_object(request, oid),
            request=request,
            limit=limit,
            offset=offset
        )


class Collection(object):
    
    @staticmethod
    def get(oid, request):
        return _object(request, oid)

    @staticmethod
    def children(oid, request, limit=DEFAULT_LIMIT, offset=0):
        return _object_children(
            document=_object(request, oid),
            request=request,
            limit=limit,
            offset=offset
        )


class Entity(object):

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
    def _labelify(document, fields=[]):
        """
        TODO i've been coding for 14 hours pls rewrite this
        
        @param document: dict/OrderedDict
        @param facetlabels: dict Output of facet_labels()
        @returns: dict document
        """
        def _wrap(fname,fdata):
            return {
                'id': fdata,
                'query': '?filter_%s=%s' % (fname,fdata),
                'label': FACET_LABELS[fname][fdata],
            }
        
        for fieldname in FACET_LABELS.keys():
            if not fieldname in fields:
                continue
            field_data = document.get(fieldname)
            if isinstance(field_data, basestring):
                document[fieldname] = _wrap(fieldname,field_data)
            elif isinstance(field_data, list):
                document[fieldname] = [
                    _wrap(fieldname,fd)
                    for fd in field_data
                ]
        return document
    
    @staticmethod
    def get(oid, request):
        return _object(request, oid)

    @staticmethod
    def children(oid, request, limit=DEFAULT_LIMIT, offset=0):
        models = ['entity','segment']
        return _object_children(
            document=_object(request, oid),
            request=request,
            models=models,
            limit=limit,
            offset=offset
        )

    @staticmethod
    def files(oid, request, limit=DEFAULT_LIMIT, offset=0):
        models = ['file']
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
        return _object_children(
            document=_object(request, oid),
            request=request,
            models=models,
            sort_fields=sort_fields,
            limit=limit,
            offset=offset
        )


    @staticmethod
    def transcripts(segment_id, parent_id, collection_id, request):
        """Extra stuff require by interview segment page.
        segment transcript
        full transcript
        """
        data = {
            'segment': None,
            'interview': None,
            'glossary': None,
        }
        # segment transcript
        results = docstore_search(
            should=[
                {"wildcard": {"id": "%s-transcript-*" % segment_id}},
                {"wildcard": {"id": "%s-transcript-*" % parent_id}},
            ],
            models=[
                'file',
            ],
            #limit=1, # should only be one transcript per File
            request=request
        )
        # assign to role
        for n,d in enumerate(results['objects']):
            if 'glossary' in d['title'].lower():
                data['glossary'] = results['objects'][n]
            elif 'segment' in d['title'].lower():
                data['segment'] = results['objects'][n]
            else:
                data['interview'] = results['objects'][n]
        return data

class Role(object):

    @staticmethod
    def children(oid, request, limit=DEFAULT_LIMIT, offset=0):
        return _object_children(
            document=_object(request, oid),
            request=request,
            limit=limit,
            offset=offset
        )


class File(object):
    
    @staticmethod
    def get(oid, request):
        return _object(request, oid)

    @staticmethod
    def children(oid, request, limit=DEFAULT_LIMIT, offset=0):
        return {
            "count": 0,
            "prev": None,
            "next": None,
            "results": [],
        }


INTERVIEW_LIST_FIELDS = SEARCH_RETURN_FIELDS + ['creation', 'location']

class Narrator(object):
    
    @staticmethod
    def get(oid, request):
        document = es.get(index=settings.DOCSTORE_INDEX, doc_type='narrator', id=oid)
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
    def narrators(request, limit=DEFAULT_LIMIT, offset=0):
        SORT_FIELDS = [
            ['last_name','asc'],
            ['first_name','asc'],
            ['middle_name','asc'],
        ]
        LIST_FIELDS = [
            'id',
            'display_name',
            'image_url',
            'generation',
            'birth_location',
            'b_date',
            'd_date',
            'bio',
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

    @staticmethod
    def interviews(narrator_id, request, limit=DEFAULT_LIMIT, offset=0):
        """Interview (Entity) objects for specified narrator.
        
        TODO cache this - counts segments for each entity
        """
        SORT_FIELDS = []
        q = docstore.search_query(
            must=[
                # TODO narrator->interview link using creators.id
                #{"term": {"creators.id": narrator_id}},
                {"term": {"narrator_id": narrator_id}},
                {"term": {"format": "vh"}},
                {"term": {"model": "entity"}},
            ]
        )
        results = format_list_objects(
            paginate_results(
                docstore.Docstore().search(
                    doctypes=['entity'],
                    query=q,
                    sort=SORT_FIELDS,
                    fields=INTERVIEW_LIST_FIELDS,
                    from_=offset,
                    size=limit,
                ),
                offset, limit, request
            ),
            request
        )
        # add segment count per interview
        for d in results['objects']:
            d['num_segments'] = count_children(CHILDREN[d['model']], d['id'])
        return results


class Facet(object):
    
    @staticmethod
    def get(oid, request):
        document = es.get(index=settings.DOCSTORE_INDEX, doc_type='facet', id=oid)
        if not document:
            raise NotFound()
        data = format_facet(document, request)
        HIDDEN_FIELDS = []
        for field in HIDDEN_FIELDS:
            pop_field(data, field)
        return data
    
    @staticmethod
    def facets(request, limit=DEFAULT_LIMIT, offset=0):
        SORT_FIELDS = [
        ]
        LIST_FIELDS = [
            'id',
            'title',
        ]
        q = docstore.search_query(
            must=[
                { "match_all": {}}
            ]
        )
        results = docstore.Docstore().search(
            doctypes=['facet'],
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
            format_facet
        )
    
    @staticmethod
    def children(oid, request, sort=[], limit=DEFAULT_LIMIT, offset=0, raw=False):
        #LIST_FIELDS = [
        #    'id',
        #    'sort',
        #    'title',
        #    'facet',
        #    'ancestors',
        #    'path',
        #    'type',
        #]
        q = docstore.search_query(
            must=[
                {'term': {'facet': oid}}
            ]
        )
        results = docstore.Docstore().search(
            doctypes=['facetterm'],
            query=q,
            sort=sort,
            #fields=LIST_FIELDS,
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
            format_term
        )
    
    @staticmethod
    def make_tree(terms_list):
        """Rearranges terms list into hierarchical list.
        
        Uses term['ancestors'] to generate a tree structure
        then "prints out" the tree to a list with indent (depth) indicators.
        More specifically, it adds term['depth'] attribs and reorders
        terms so they appear in the correct places in the hierarchy.
        source: https://gist.github.com/hrldcpr/2012250
        
        @param terms_list: list
        @returns: list
        """
        def tree():
            """Define a tree data structure
            """
            return defaultdict(tree)
        
        def add(tree_, path):
            """
            @param tree_: defaultdict
            @param path: list of ancestor term IDs
            """
            for node in path:
                tree_ = tree_[node]
        
        def populate(terms_list):
            """Create and populate tree structure
            by iterating through list of terms and referencing ancestor/path keys
            
            @param terms_list: list of dicts
            @returns: defaultdict
            """
            tree_ = tree()
            for term in terms_list:
                path = [
                    tid for tid in term.get('ancestors', [])
                ]
                path.append(term['term_id'])
                add(tree_, path)
            return tree_
        
        def flatten(tree_, depth=0):
            """Takes tree dict and returns list of terms with depth values
            
            Variation on ptr() from the gist
            Recursively gets term objects from terms_dict, adds depth,
            and appends to list of terms.
            
            @param tree_: defaultdict Tree
            @param depth: int Depth of indents
            """
            for key in sorted(tree_.keys()):
                term = terms_dict[key]
                term['depth'] = depth
                terms.append(term)
                depth += 1
                flatten(tree_[key], depth)
                depth -= 1
        
        terms_dict = {t['term_id']: t for t in terms_list}
        terms_tree = populate(terms_list)
        terms = []
        flatten(terms_tree)
        return terms

    @staticmethod
    def topics_terms(request):
        """List of topics facet terms, with tree indents and doc counts
        
        TODO ES does query and aggregations caching.
        Does caching this mean the query/aggs won't be cached in ES?
        
        @param request: Django request object.
        @returns: list of Terms
        """
        facet_id = 'topics'
        key = 'facet:%s:terms' % facet_id
        cached = cache.get(key)
        if not cached:
            terms = Facet.children(
                facet_id, request,
                sort=[('title','asc')],
                limit=10000, raw=True
            )['objects']
            for term in terms:
                term['links'] = {}
                term['links']['html'] = reverse(
                    'ui-browse-term', args=[facet_id, term['term_id']]
                )
            terms = Facet.make_tree(terms)
            Term.term_aggs_nested(
                terms,
                doctypes=['entity','segment'],
                fieldname='topics',
            )
            cached = terms
            cache.set(key, cached, settings.CACHE_TIMEOUT)
        return cached

    @staticmethod
    def facility_terms(request):
        """List of facility facet terms, sorted and with doc counts
        
        TODO ES does query and aggregations caching.
        Does caching this mean the query/aggs won't be cached in ES?
        
        @param request: Django request object.
        @returns: list of Terms
        """
        facet_id = 'facility'
        key = 'facet:%s:terms' % facet_id
        cached = cache.get(key)
        if not cached:
            terms = Facet.children(
                facet_id, request,
                sort=[('title','asc')],
                limit=10000, raw=True
            )['objects']
            for term in terms:
                term_id = term['term_id']
                term['links'] = {}
                term['links']['html'] = reverse(
                    'ui-browse-term', args=[facet_id, term_id]
                )
            terms = sorted(terms, key=lambda term: term['title'])
            Term.term_aggs_nested(
                terms,
                doctypes=['entity','segment'],
                fieldname='facility',
            )
            cached = terms
            cache.set(key, cached, settings.CACHE_TIMEOUT)
        return cached


class Term(object):
    
    @staticmethod
    def get(oid, request):
        document = es.get(index=settings.DOCSTORE_INDEX, doc_type='facetterm', id=oid)
        if not document:
            raise NotFound()
        # save data for breadcrumbs
        # (we assume ancestors and path in same order)
        facet = document['_source']['facet']
        path = document['_source'].get('path')
        ancestors = document['_source'].get('ancestors')
        
        data = format_term(document, request)
        HIDDEN_FIELDS = []
        for field in HIDDEN_FIELDS:
            pop_field(data, field)
        # breadcrumbs
        # join path (titles) and ancestors (IDs)
        if path and ancestors:
            data['breadcrumbs'] = []
            path = path.split(':')
            path.pop() # last path item is not an ancestor
            if len(path) == len(ancestors):
                for n,tid in enumerate(ancestors):
                    data['breadcrumbs'].append({
                        'url':reverse('ui-browse-term', args=[facet, tid]),
                        'title':path[n]
                    })
        return data
    
    @staticmethod
    def terms(request, limit=DEFAULT_LIMIT, offset=0):
        SORT_FIELDS = [
        ]
        LIST_FIELDS = [
            'id',
            'title',
        ]
        q = docstore.search_query(
            must=[
                { "match_all": {}}
            ]
        )
        results = docstore.Docstore().search(
            doctypes=['facetterm'],
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
            format_facet
        )
    
    @staticmethod
    def term_aggregations(field, fieldname, terms, request):
        """Add number of documents for each facet term
        
        @param field: str Field name in ES (e.g. 'topics.id')
        @param fieldname: str Fieldname in ddrpublic (e.g. 'topics')
        @param terms list
        """
        # aggregations
        query = {
            'models': [
                'entity',
                'segment',
            ],
            'aggs': {
                fieldname: {
                    'terms': {
                        'field': field,
                        'size': len(terms), # doc counts for all terms
                    }
                },
            }
        }
        results = docstore_search(
            models=query['models'],
            aggs=query['aggs'],
            request=request,
        )
        aggs = docstore.aggs_dict(results.get('aggregations'))[fieldname]
        # assign num docs per term
        for term in terms:
            num = aggs.get(str(term['term_id']), 0) # aggs keys are str(int)s
            term['doc_count'] = num            # could be used for sorting terms!
    
    @staticmethod
    def term_aggs_nested(terms, doctypes=[], fieldname=''):
        """Add number of documents for each facet term (nested fields)
        
        NOTE: assumes values are in the form FIELDNAME.id
        Example:
            ...
            'topics': [
                {'id': 123, 'title': 'Topic Title'},
            ],
            ...
        
        models.gather_nested_aggregations(
            terms,
            doctypes=['entity','segment'],
            fieldname='topics'
        )
        
        @param doctypes: list
        @param fieldnames: list
        @returns: None
        """
        ds = docstore.Docstore()
        s = elasticsearch_dsl.Search(using=ds.es, index=ds.indexname)
        s = s.query("match_all")
        for dt in doctypes:
            s = s.doc_type(dt)
        # aggregations buckets for each nested field
        #s.aggs.bucket(
        #    'topics', 'nested', path='topics'
        #).bucket(
        #    'topic_ids', 'terms', field='topics.id', size=1000
        #)
        s.aggs.bucket(
            fieldname, 'nested', path=fieldname
        ).bucket(
            '%s_ids' % fieldname,
            'terms',
            field='%s.id' % fieldname,
            size=1000
        )
        results = search.Searcher(search=s).execute(limit=1000, offset=0)
        # fieldname:term:id dict
        aggs = {}
        for fieldname,data in results.aggregations.iteritems():
            aggs[fieldname] = {}
            for item in data:
                aggs[fieldname][item['key']] = item['doc_count']
        # assign doc_count per term
        for term in terms:
            fid = term['facet']
            tid = str(term['term_id'])
            term['doc_count'] = ''
            if aggs.get(fid) and aggs[fid].get(tid):
                term['doc_count'] = aggs[fid].get(tid)
    
    @staticmethod
    def objects(facet_id, term_id, request=None, limit=DEFAULT_LIMIT, offset=0):
        """Returns list of repository objects matching the term ID.
        
        NOTE: only works if the nested value is "id", e.g. "topics.id"
        
        @param facet_id: str
        @param term_id: str
        @param request: Django request object.
        @param limit: int
        @param offset: int
        @returns: SearchResults
        """
        models = CHILDREN.keys()
        q = docstore.search_query(
            must=[
                {"nested": {
                    "path": facet_id,
                    "query": {"term": {
                        "%s.id" % facet_id: term_id
                    }}
                }}
            ],
        )
        return format_list_objects(
            paginate_results(
                docstore.Docstore().search(
                    doctypes=models,
                    query=q,
                    sort=[
                        'sort',
                        'id',
                        'record_created',
                        'record_lastmod',
                    ],
                    fields=SEARCH_RETURN_FIELDS,
                    from_=offset,
                    size=limit,
                ),
                offset, limit, request
            ),
            request
        )


# TODO REPLACE THESE HARDCODED VALUES!!!

MODELS_CHOICES = [
    ('collection', 'Collection'),
    ('entity', 'Entity'),
    ('segment', 'Segment'),
    ('file', 'File'),
    ('narrator', 'Narrator'),
    ('term', 'Topic Term'),
]

LANGUAGE_CHOICES = [
    ('eng', 'English'),
    ('jpn', 'Japanese'),
    ('chi', 'Chinese'),
]

FORMAT_CHOICES = [
    ['av','Audio/Visual'],
    ['ds','Dataset'],
    ['doc','Document'],
    ['img','Still Image'],
    ['vh','Oral History'],
]

RIGHTS_CHOICES = [
    ["cc", "DDR Creative Commons"],
    ["pcc", "Copyright, with special 3rd-party grant permitted"],
    ["nocc", "Copyright restricted"],
    ["pdm", "Public domain" ],
]

GENRE_CHOICES = [
    ['advertisement','Advertisements'],
    ['album','Albums'],
    ['architecture','Architecture'],
    ['baseball_card','Baseball Cards'],
    ['blank_form','Blank Forms'],
    ['book','Books'],
    ['broadside','Broadsides'],
    ['cartoon','Cartoons (Commentary)'],
    ['catalog','Catalogs'],
    ['cityscape','Cityscapes'],
    ['clipping','Clippings'],
    ['correspondence','Correspondence'],
    ['diary','Diaries'],
    ['drawing','Drawings'],
    ['ephemera','Ephemera'],
    ['essay','Essays'],
    ['ethnography','Ethnography'],
    ['fieldnotes','Fieldnotes'],
    ['illustration','Illustrations'],
    ['interview','Interviews'],
    ['landscape','Landscapes'],
    ['leaflet','Leaflets'],
    ['manuscript','Manuscripts'],
    ['map','Maps'],
    ['misc_document','Miscellaneous Documents'],
    ['motion_picture','Motion Pictures'],
    ['music','Music'],
    ['narrative','Narratives'],
    ['painting','Paintings'],
    ['pamphlet','Pamphlets'],
    ['periodical','Periodicals'],
    ['petition','Petitions'],
    ['photograph','Photographs'],
    ['physical_object','Physical Objects'],
    ['poetry','Poetry'],
    ['portrait','Portraits'],
    ['postcard','Postcards'],
    ['poster','Posters'],
    ['print','Prints'],
    ['program','Programs'],
    ['rec_log','Recording Logs'],
    ['score','Scores'],
    ['sheet_music','Sheet Music'],
    ['timetable','Timetables'],
    ['transcription','Transcriptions'],
]


def flatten(path, indent='--'):
    paths = [x for x in path.split(':')]
    # TODO replace instead of make new list
    flat = []
    for x in paths[:-1]:
        flat.append(indent)
    flat.append(paths[-1])
    return ''.join(flat)

def topics_flattened():
    oid = 'topics'
    request = None
    key = 'search:filters:%s' % oid
    cached = cache.get(key)
    if not cached:
        terms = Facet.make_tree(
            Facet.children(
                oid, request,
                sort=[('sort','asc')],
                limit=10000, raw=True
            )['objects']
        )
        choices = [
            (term['id'], term['path'])
            for term in terms
        ]
        cached = choices
        cache.set(key, cached, 15) # settings.ELASTICSEARCH_QUERY_TIMEOUT)
    return cached

def facilities():
    oid = 'facility'
    request = None
    key = 'search:filters:%s' % oid
    cached = cache.get(key)
    if not cached:
        terms = Facet.children(
            oid, request,
            sort=[('title','asc')],
            limit=10000, raw=True
        )['objects']
        # for some reason ES does not sort
        terms = sorted(terms, key=lambda term: term['title'])
        cached = [
            (term['id'], term['title'])
            for term in terms
        ]
        cache.set(key, cached, 15) # settings.ELASTICSEARCH_QUERY_TIMEOUT)
    return cached

