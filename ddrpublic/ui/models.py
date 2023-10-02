from collections import defaultdict, OrderedDict
import logging
logger = logging.getLogger(__name__)
import os
from urllib.parse import urlparse, urlunsplit

import requests

from django.conf import settings
from django.core.cache import cache
from django.shortcuts import Http404

from rest_framework.exceptions import NotFound
from rest_framework.reverse import reverse

from elastictools import docstore
from elastictools import search
from . import identifier

INDEX_PREFIX = 'ddr'

# see if cluster is available, quit with nice message if not
docstore.Docstore(INDEX_PREFIX, settings.DOCSTORE_HOST, settings).start_test()

# set default hosts and index
DOCSTORE = docstore.Docstore('ddr', settings.DOCSTORE_HOST, settings)

DEFAULT_SIZE = 10
DEFAULT_LIMIT = 25

# whitelist of params recognized in URL query
# TODO move to ddr-defs/repo_models/elastic.py?
SEARCH_PARAM_WHITELIST = [
    'fulltext',
    'sort',
    'topics',
    'facility',
    'model',
    'models',
    'parent',
    'status',
    'public',
    'topics',
    'facility',
    'contributor',
    'creators',
    'creators.id',
    'creators.oh_id',
    'creators.role',
    'creators.namepart',
    'narrator',
    'format',
    'genre',
    'geography',
    'language',
    'location',
    'mimetype',
    'persons',
    'rights',
    'search_hidden',
]

# fields where the relevant value is nested e.g. topics.id
# TODO move to ddr-defs/repo_models/elastic.py?
SEARCH_NESTED_FIELDS = [
    'creators',
    'facility',
    'topics',
]

# TODO move to ddr-defs/repo_models/elastic.py?
SEARCH_AGG_FIELDS = {
    #'model': 'model',
    #'status': 'status',
    #'public': 'public',
    #'contributor': 'contributor',
    #'creators': 'creators.namepart',
    'facility': 'facility.id',
    'format': 'format',
    'genre': 'genre',
    #'geography': 'geography.term',
    #'language': 'language',
    #'location': 'location',
    #'mimetype': 'mimetype',
    #'persons': 'persons',
    'rights': 'rights',
    'topics': 'topics.id',
}

# TODO move to ddr-defs/repo_models/elastic.py?
SEARCH_MODELS = [
    'ddrcollection',
    'ddrentity',
    'ddrsegment',
    'ddrnarrator'
]

NAMESDB_SEARCH_MODELS = ['names-record']

# fields searched by query e.g. query will find search terms in these fields
# IMPORTANT: These are used for fulltext search so they must ALL be TEXT fields
# TODO move to ddr-defs/repo_models/elastic.py?
SEARCH_INCLUDE_FIELDS = [
    # ddr object fields
    'id',
    'model',
    'links_html',
    'links_json',
    'links_img',
    'links_thumb',
    'links_children',
    'status',
    'public',
    'title',
    'description',
    'contributor',
    'creators',
    'creators.namepart',
    'facility',
    'format',
    'genre',
    'geography',
    'label',
    'language',
    'creation',
    'location',
    'persons',
    'rights',
    'topics',
    # narrator fields
    'image_url',
    'display_name',
    'bio',
    'extent',
    'search_hidden',
]

# TODO move to ddr-defs/repo_models/elastic.py?
SEARCH_FORM_LABELS = {
    'model': 'Model',
    'status': 'Status',
    'public': 'Public',
    'contributor': 'Contributor',
    'creators.namepart': 'Creators',
    'facility': 'Facility',
    'format': 'Format',
    'genre': 'Genre',
    'geography.term': 'Geography',
    'language': 'Language',
    'location': 'Location',
    'mimetype': 'Mimetype',
    'persons': 'Persons',
    'rights': 'Rights',
    'topics': 'Topics',
}

NAMESDB_SEARCH_FORM_LABELS = {
    'm_camp': 'Camp',
}

## TODO should this live in models?
#def _vocab_choice_labels(field):
#    return {
#        str(term['id']): term['title']
#        for term in vocab.get_vocab(
#            os.path.join(settings.VOCAB_TERMS_URL % field)
#        )['terms']
#    }
#VOCAB_TOPICS_IDS_TITLES = {
#    'facility': _vocab_choice_labels('facility'),
#    'format': _vocab_choice_labels('format'),
#    'genre': _vocab_choice_labels('genre'),
#    'language': _vocab_choice_labels('language'),
#    'public': _vocab_choice_labels('public'),
#    'rights': _vocab_choice_labels('rights'),
#    'status': _vocab_choice_labels('status'),
#    'topics': _vocab_choice_labels('topics'),
#}

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
    'repo',
]
ORGANIZATION_LIST_SORT = [
    'repo',
    'org',
]
COLLECTION_LIST_SORT = [
    'repo',
    'org',
    'cid',
    'id',
]
ENTITY_LIST_SORT = [
    'repo',
    'org',
    'cid',
    'eid',
    'id',
]
FILE_LIST_SORT = [
    'repo',
    'org',
    'cid',
    'eid',
    'sort',
    '-role',
    'id',
]
OBJECT_LIST_SORT = [
    'repo',
    'org',
    'cid',
    'eid',
    '-role',
    'sort',
    'sha1',
    'id',
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
    'links_download',
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

MEDIA_LOCAL_SCHEME = urlparse(settings.MEDIA_URL_LOCAL).scheme
MEDIA_LOCAL_HOSTNAME = urlparse(settings.MEDIA_URL_LOCAL).hostname


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
    if internal and isinstance(internal, str) and internal.isdigit():
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
        u = urlparse(url)
        return urlunsplit(
            (MEDIA_LOCAL_SCHEME, MEDIA_LOCAL_HOSTNAME, u.path, u.params, u.query)
        )
    return url

def file_size(url):
    """Get the size of a file from HTTP headers (without downloading)
    
    @param url: str
    @returns: int
    """
    # Disable verification of SSL certs to enable thumbnails in dev
    # e.g. URLs like https://ddrpublic.local
    # TODO maybe have a setting that disables only in dev?
    r = requests.head(url, verify=False)
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
    if not isinstance(models, str):
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
            DOCSTORE.search(
                doctypes=models,
                query=q,
                sort=sort_fields,
                fields=fields,
                from_=offset,
                size=limit,
            ),
            offset, limit, request
        ),
        request,
        format_object_detail2
    )

def _object(request, oid, format=None):
    try:
        data = DOCSTORE.es.get(
            index=DOCSTORE.index_name(identifier.Identifier(oid).model),
            id=oid
        )
    except docstore.NotFoundError:
        raise Http404
    return format_object_detail2(data, request)

def _object_children(document, request, models=[], sort_fields=[], fields=SEARCH_INCLUDE_FIELDS, limit=DEFAULT_LIMIT, offset=0):
    """
    TODO this function is probably superfluous
    """
    if not models:
        models = CHILDREN[document['model']]
    if not sort_fields:
        sort_fields = OBJECT_LIST_SORT
    return children(
        request=request,
        model=models,
        parent_id=document['id'],
        sort_fields=sort_fields,
        fields=fields,
        limit=limit, offset=offset
    )

def children(request, model, parent_id, sort_fields, fields=SEARCH_INCLUDE_FIELDS, limit=DEFAULT_LIMIT, offset=0, just_count=False):
    """Return object children list in Django REST Framework format.
    
    Returns a paged list with count/prev/next metadata
    
    @param request: Django request object.
    @param model: str
    @param parent_id: str
    @param fields: list
    @param sort_fields: list
    @param limit: int
    @param offset: int
    @param just_count: boolean
    @returns: dict
    """
    if not isinstance(model, str):
        models = model
    elif isinstance(model, list):
        models = ','.join(model)
    else:
        raise Exception('model must be a string or a list')
    if just_count:
        q = docstore.search_query(
            must=[
                {"term": {"parent_id": parent_id}},
            ],
        )
        return DOCSTORE.count(
            doctypes=model,
            query=q,
        )
    indices = ','.join([DOCSTORE.index_name(model) for model in models])
    params={
        'parent': parent_id,
    }
    searcher = search.Searcher(DOCSTORE)
    searcher.prepare(
        params=params,
        params_whitelist=SEARCH_PARAM_WHITELIST,
        search_models=indices,
        sort=sort_fields,
        fields=fields,
        fields_nested=[],
        fields_agg={},
        wildcards=False,
    )
    return searcher.execute(limit, offset)
    
def count_children(model, parent_id):
    """Return count of object's children
    
    @param model: str
    @param parent_id: str
    @returns: dict
    """
    if not isinstance(model, str):
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
    r = DOCSTORE.count(
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
    data['total'] = len(results['hits'])
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
        model = document['_index']
        document = document['_source']
    else:
        oid = document.pop('id')
        model = document.pop('model')
    model = model.replace(INDEX_PREFIX, '')
    
    d = OrderedDict()
    d['id'] = oid
    d['model'] = model
    if document.get('index'): d['index'] = document.pop('index')
    
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
        if document.get('backblaze'):
            d['links']['img'] = '{}{}'.format(
                settings.BACKBLAZE_BUCKET_URL, document.pop('links_img')
            )
        else:
            d['links']['img'] = '{}{}'.format(
                settings.MEDIA_URL, document.pop('links_img')
            )
        d['links']['thumb'] = '%s%s' % (settings.MEDIA_URL_LOCAL, document.pop('links_thumb'))
        if document.get('links_download'):
            if document.get('backblaze'):
                d['links']['download'] = '{}{}'.format(
                    settings.BACKBLAZE_BUCKET_URL, document.pop('links_download')
                )
            else:
                d['links']['download'] = '{}{}'.format(
                    settings.MEDIA_URL, document.pop('links_download')
                )
    
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
    for key in document.keys():
        if key not in HIDDEN_FIELDS:
            d[key] = document[key]
    # download filename
    if d['links'].get('img'):
        d['download_large'] = os.path.basename(d['links']['img'])
    if d['links'].get('download'):
        d['download_fullsize'] = os.path.basename(d['links']['download'])
    return d

def format_narrator(document, request, listitem=False):
    
    if document.get('_source'):
        oid = document['_id']
        model = document['_index']
        document = document['_source']
        
    oid = document.pop('id')
    if hasattr(document, 'model'):
        model = document.pop('model')
    else:
        model = 'narrator'
        
    d = OrderedDict()
    d['id'] = oid
    d['model'] = model
    if document.get('index'): d['index'] = document.pop('index')
    # links
    d['links'] = OrderedDict()
    d['links']['html'] = reverse('ui-narrators-detail', args=[oid], request=request)
    d['links']['json'] = reverse('ui-api-narrator', args=[oid], request=request)
    d['links']['img'] = narrator_img_url(document.pop('image_url'))
    d['links']['thumb'] = local_thumb_url(d['links'].get('img',''), request)
    d['links']['interviews'] = reverse('ui-api-narrator-interviews', args=[oid], request=request)
    # title, description
    for fieldname in ['title', 'display_name']:
        if document.get(fieldname):
            d['display_name'] = document.pop(fieldname)
    for fieldname in ['description', 'bio']:
        if document.get(fieldname):
            d['bio'] = document.pop(fieldname)
    # everything else
    HIDDEN_FIELDS = [
        'repo','org','cid','eid','sid','role','sha1'
    ]
    for key in document.keys():
        if key not in HIDDEN_FIELDS:
            d[key] = document[key]
    return d

def format_facet(document, request, listitem=False):
    if document.get('_source'):
        oid = document['_id']
        model = document['_index']
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
        model = document['_index']
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
    for key in document.keys():
        if key not in HIDDEN_FIELDS:
            d[key] = document[key]
    return d

FORMATTERS = {
    'ddrnarrator': format_narrator,
    'ddrfacet': format_facet,
    'ddrfacetterm': format_term,
    'ddrrepository': format_object_detail2,
    'ddrorganization': format_object_detail2,
    'ddrcollection': format_object_detail2,
    'ddrentity': format_object_detail2,
    'ddrsegment': format_object_detail2,
    'ddrfile': format_object_detail2,
}

def format_list_objects(results, request, function):
    """Iterate through results objects apply format_object_detail function
    
    @param results: Output of models.paginate_results
    @param request: Django request object.
    @param function: Item formatting function
    """
    results['objects'] = []
    while(results['hits']):
        hit = results['hits'].pop(0)
        doctype = hit['_index']
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
    SORT_FIELDS = ['id', 'title',]
    LIST_FIELDS = ['id', 'facet', 'title',]
    q = docstore.search_query(
        should=[
            {"terms": {"facet": [
                'format', 'genre', 'language', 'rights',
            ]}}
        ]
    )
    results = DOCSTORE.search(
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
    return ids_labels

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
            sort_fields=ORGANIZATION_LIST_SORT,
            limit=limit,
            offset=offset
        )


class Organization(object):

    @staticmethod
    def get(oid, request):
        return _object(request, oid)

    @staticmethod
    def children(oid, request, fields=SEARCH_INCLUDE_FIELDS, limit=DEFAULT_LIMIT, offset=0):
        return _object_children(
            document=_object(request, oid),
            request=request,
            fields=fields,
            sort_fields=COLLECTION_LIST_SORT,
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
            if isinstance(field_data, str):
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
        return _object_children(
            document=_object(request, oid),
            request=request,
            models=models,
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
    model = 'narrator'
    
    @staticmethod
    def get(oid, request):
        document = DOCSTORE.es.get(
            index=DOCSTORE.index_name(Narrator.model),
            id=oid
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
    def narrators(request, limit=DEFAULT_LIMIT, offset=0):
        key = 'narrators:{}:{}'.format(limit, offset)
        results = cache.get(key)
        if not results:
            sort_fields = [
                'last_name',
                'first_name',
                'middle_name',
            ]
            list_fields = [
                'id',
                'display_name',
                'image_url',
                'generation',
                'birth_location',
                'b_date',
                'd_date',
                'bio',
            ]
            params={
                'match_all': '1',
            }
            searcher = search.Searcher(DOCSTORE)
            searcher.prepare(
                params=params,
                params_whitelist=SEARCH_PARAM_WHITELIST,
                search_models=['ddrnarrator'],
                sort=sort_fields,
                fields=list_fields,
                fields_nested=[],
                fields_agg={},
                wildcards=False,
            )
            results = searcher.execute(limit, offset)
            cache.set(key, results, settings.CACHE_TIMEOUT)
        return results

    @staticmethod
    def interviews(narrator_id, request, limit=DEFAULT_LIMIT, offset=0):
        """Interview (Entity) objects for specified narrator.
        
        TODO cache this - counts segments for each entity
        """
        params={
            'creators.oh_id': str(narrator_id),
        }
        searcher = search.Searcher(DOCSTORE)
        searcher.prepare(
            params=params,
            params_whitelist=SEARCH_PARAM_WHITELIST,
            search_models=['ddrentity'],
            sort=[],
            fields=SEARCH_INCLUDE_FIELDS,
            fields_nested=[],
            fields_agg={},
            wildcards=False,
        )
        results = searcher.execute(limit, offset)
        # add segment count per interview
        for o in results.objects:
            o['num_segments'] = count_children(CHILDREN[o.model], o.id)
        # TODO restore when data is migrated
        #return results.ordered_dict(
        #    request, format_functions=FORMATTERS
        #)
        
        ohid_interviews = results.ordered_dict(
            request, format_functions=FORMATTERS
        )['objects']
        # TODO rm backwards-compatibility when creators.id converted to .oh_id
        params={
            'narrator': str(narrator_id),
        }
        searcher = search.Searcher(DOCSTORE)
        searcher.prepare(
            params=params,
            params_whitelist=SEARCH_PARAM_WHITELIST,
            search_models=['ddrentity'],
            sort=[],
            fields=SEARCH_INCLUDE_FIELDS,
            fields_nested=[],
            fields_agg={},
            wildcards=False,
        )
        results = searcher.execute(limit, offset)
        # add segment count per interview
        for o in results.objects:
            o['num_segments'] = count_children(CHILDREN[o.model], o.id)
        id_interviews = results.ordered_dict(
            request, format_functions=FORMATTERS
        )['objects']
        # NOTE simulate normal formatted ordereddict
        interviews = ohid_interviews + id_interviews
        data = {
            "NOTE": "> > > Temporary API modification while we migrate narrator data < < <",
            "total": len(interviews),
            "limit": 1000,
            "offset": 0,
            "prev_offset": None,
            "next_offset": None,
            "page_size": 1000,
            "this_page": 1,
            "num_this_page": len(interviews),
            "prev_api": "",
            "next_api": "",
            "objects": interviews,
            "query": {},
            "aggregations": {},
        }
        return data

class Facet(object):
    
    @staticmethod
    def get(oid, request):
        document = DOCSTORE.es.get(
            index=DOCSTORE.index_name('facet'),
            id=oid
        )
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
        results = DOCSTORE.search(
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
        results = DOCSTORE.search(
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
            # add doc_count per term
            for term in terms:
                term['doc_count'] = Term.objects(
                    'topics', str(term['term_id']),
                    limit=settings.RESULTS_PER_PAGE, offset=0,
                    request=None,
                ).total
            
            cached = terms
            cache.set(key, cached, settings.CACHE_TIMEOUT_LONG)
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
            # add doc_count per term
            for term in terms:
                term['doc_count'] = Term.objects(
                    'facility', str(term['term_id']),
                    limit=settings.RESULTS_PER_PAGE, offset=0,
                    request=None,
                ).total
            
            cached = terms
            cache.set(key, cached, settings.CACHE_TIMEOUT_LONG)
        return cached


class Term(object):
    
    @staticmethod
    def get(oid, request):
        document = DOCSTORE.es.get(
            index=DOCSTORE.index_name('facetterm'),
            id=oid
        )
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
        results = DOCSTORE.search(
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
    def topics_tree(term, request):
        """Terms tree for a particular term, with URLs
        
        @param term: dict or OrderedDict
        @param request
        @returns: list
        """
        ancestors_oids = [
            'topics-{}'.format(id)
            for id in term.get('ancestors', [])
        ]
        #children_oids = [
        #    'topics-{}'.format(id)
        #    for id in term.get('children', [])
        #]
        tree = [
            t for t in Facet.topics_terms(request)
            if (
                    (t['id'] in ancestors_oids)
                    or (t['id'] == term['id'])
                    #or (t['id'] in children_oids)
            )
        ]
        return tree
    
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
        key = 'term:{}:{}:{}:{}:objects'.format(facet_id, term_id, limit, offset)
        results = cache.get(key)
        if not results:
            params = {
                'match_all': 'true',
            }
            params[facet_id] = term_id
            searcher = search.Searcher(DOCSTORE)
            searcher.prepare(
                params=params,
                params_whitelist=SEARCH_PARAM_WHITELIST,
                search_models=SEARCH_MODELS,
                sort=[],
                fields=SEARCH_INCLUDE_FIELDS,
                fields_nested=[],
                fields_agg={},
                wildcards=False,
            )
            results = searcher.execute(limit, offset)
            cache.set(key, results, settings.CACHE_TIMEOUT)
        return results


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
