import logging
logger = logging.getLogger(__name__)

from django.conf import settings

HOSTS = settings.DOCSTORE_HOSTS
INDEX = settings.DOCSTORE_INDEX

DEFAULT_SIZE = 10

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
