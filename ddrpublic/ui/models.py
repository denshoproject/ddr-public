import hashlib
import json
import logging
logger = logging.getLogger(__name__)
import os

from dateutil import parser

from django.conf import settings
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.template import Context, Template
from django.template.loader import get_template
from django.utils.http import urlquote  as django_urlquote

from DDR import docstore

from ui import faceting
from ui.identifier import Identifier, MODEL_CLASSES


DEFAULT_SIZE = 10

# TODO move to DDR.identifier?
REPOSITORY_LIST_FIELDS = ['id', 'title', 'description', 'url',]
ORGANIZATION_LIST_FIELDS = ['id', 'title', 'description', 'url',]
COLLECTION_LIST_FIELDS = ['id', 'title', 'description', 'signature_id',]
ENTITY_LIST_FIELDS = ['id', 'title', 'description', 'signature_id',]
FILE_LIST_FIELDS = ['id', 'basename_orig', 'label', 'access_rel','sort',]

# TODO refactor: knows too much about structure of ID
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

HOSTS = settings.DOCSTORE_HOSTS
INDEX = settings.DOCSTORE_INDEX


# TODO reindex using parents/children (http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/docs-index_.html#parent-children)


# functions for GETing object data from ElasticSearch

def absolute_url(identifier):
    """Takes a list of object ID parts and returns URL for that object.
    """
    return reverse(
        'ui-%s' % identifier.model,
        args=identifier.parts.values()
    )

def backend_url(identifier):
    """Debug link to ElasticSearch page for the object.
    """
    if settings.DEBUG:
        return 'http://%s/%s/%s/%s' % (HOSTS, INDEX, identifier.model, identifier.id)
    return ''

def cite_url(identifier):
    """Link to object's citation page
    """
    return reverse('ui-cite', args=(identifier.model, identifier.id))

def org_logo_url(identifier):
    """Link to organization logo image
    """
    return os.path.join(settings.MEDIA_URL, identifier.organization_id(), 'logo.png')

def signature_url(identifier, signature_id):
    """
    @param identifier: Identifier
    @param signature_id: str File ID
    """
    return '%s%s/%s-a.jpg' % (settings.MEDIA_URL, identifier.collection_id(), signature_id)

def media_url_local( url ):
    """Replace media_url with one that points to "local" media server
    
    MEDIA_URLs contain a domain name and thus have to go through DNS
    and possibly a trying-to-be-helpful CDN that blocks urllib2 requests
    with no User-agent headers.  Replaces the MEDIA_URL portion with
    MEDIA_URL_LOCAL, which should contain the IP address of the local
    media server.
    """
    if url:
        return url.replace(settings.MEDIA_URL, settings.MEDIA_URL_LOCAL)
    return None

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

# ----------------------------------------------------------------------
# functions for displaying various types of content

#>>> t = Template("My name is {{ my_name }}.")
#>>> c = Context({"my_name": "Adrian"})

DATETIME_TEMPLATE = """{{ dt|date:"Y F j (D) G:i:s" }}"""

FACET_TEMPLATE = """<ul class="list-unstyled">
{% for facet in facets %}
  <li><a href="{{ facet.url }}">{{ facet.title }}</a></li>
{% endfor %}
</ul>"""

FILESIZE_TEMPLATE = """{{ text|filesizeformat }}"""

STRING_TEMPLATE = """{{ text }}"""

STRING_COLLAPSED_TEMPLATE = """{{ text|truncatechars:512 }}"""

def display_datetime(fieldname, text):
    dt = parser.parse(text)
    t = Template(DATETIME_TEMPLATE)
    c = Context({'dt':dt})
    return t.render(c)

def display_facet(fieldname, text, facet):
    # make everything a list
    if isinstance(text, basestring):
        text = text.strip().split(';')
    lines = []
    for txt in text:
        term_id = faceting.extract_term_id(txt)
        url = '/search/%s:%s/' % (fieldname, django_urlquote(term_id))
        termdata = {'url':url, 'term':txt.strip(), 'title':txt.strip()}
        if facet and facet['terms']:
            for term in facet['terms']:
                if term['id'] == term_id:
                    termdata['title'] = term['title']
        lines.append(termdata)
    t = Template(FACET_TEMPLATE)
    c = Context({'facets': lines})
    return t.render(c)

def display_filesize(fieldname, text):
    t = Template(FILESIZE_TEMPLATE)
    c = Context({'text':text})
    return t.render(c)

def display_rights(fieldname, text):
    t = get_template('ui/license-%s.html' % text)
    return t.render(Context({}))

def display_string(fieldname, text):
    t = Template(STRING_TEMPLATE)
    c = Context({'text':text})
    return t.render(c)

def display_string_collapsed(fieldname, text):
    t = Template(STRING_COLLAPSED_TEMPLATE)
    c = Context({'text':text})
    return t.render(c)

field_display_handler = {
    'datetime': display_datetime,
    'facet': display_facet,
    'filesize': display_filesize,
    'rights': display_rights,
    'string': display_string,
    'string_collapsed': display_string_collapsed,
}

def field_display_style( o, field ):
    for modelfield in model_fields(o.identifier):
        if modelfield['name'] == field:
            return modelfield['elasticsearch']['display']
    return None

# ----------------------------------------------------------------------
# functions for performing searches and processing results

def cached_query(host, index, model='', query='', terms={}, filters={}, fields=[], sort=[], size=10000):
    """Perform an ElasticSearch query and cache it.
    
    Cache key consists of a hash of all the query arguments.
    """
    query_args = {'host':host, 'index':index, 'model':model,
                  'query':query, 'terms':terms, 'filters':filters,
                  'fields':fields, 'sort':sort,}
    key = hashlib.sha1(json.dumps(query_args)).hexdigest()
    cached = cache.get(key)
    if not cached:
        cached = docstore.search(hosts=HOSTS, index=index, model=model,
                                 query=query, term=terms, filters=filters,
                                 fields=fields, sort=sort, size=size)
        cache.set(key, cached, settings.ELASTICSEARCH_QUERY_TIMEOUT)
    return cached

def massage_query_results( results, thispage, page_size ):
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
    objects = docstore.massage_query_results(results, thispage, page_size)
    results = None
    for o in objects:
        if not o.get('placeholder',False):
            # assemble urls for each record type
            if o.get('id', None):
                identifier = Identifier(o['id'])
                o['identifier'] = identifier
                o['url'] = reverse(
                    'ui-%s' % identifier.model,
                    args=identifier.parts.values()
                )
    return objects

def instantiate_query_objects( massaged ):
    """Instantiate Collection/Entity/File objects in massaged list of results
    
    @param massaged: list Output of massage_query_results().
    @returns: list of Collection/Entity/File objects and Hit dicts
    """
    objects = []
    for hit in massaged:
        if hit.get('placeholder', None):
            objects.append(hit)
        else:
            o = build_object(Identifier(hit['id']), hit)
            if o:
                objects.append(o)
            else:
                objects.append(hit)
    return objects

def model_fields(identifier):
    """Get list of fields from ES
    
    @param identifier: Identifier
    @returns: list of field names
    """
    key = 'ddrpublic:%s:fields' % identifier.model
    cached = cache.get(key)
    if not cached:
        cached = identifier.fields_module().FIELDS
        cache.set(key, cached, 60*1)
    return cached

def build_object(identifier, source, rename={} ):
    """Build object from ES GET data.
    
    NOTE: This only works on object types listed in DDR.models.MODULES.
    
    'rename' contains fields in 'source' that are to be given alternate names.
    Entity.files() and .topics() methods override the original fields.
    
    @param identifier: Identifier
    @param source: dict Contents of Elasticsearch document (document['_source']).
    @param rename: dict of {'fieldnames': 'alternate_names'}.
    """
    object_class = identifier.object_class(mappings=MODEL_CLASSES)
    o = object_class()
    o.identifier = identifier  # required or o.__repr__ will crash
    o.id = o.identifier.id
    o.fields = []
    fields = model_fields(o.identifier)
    for field in fields:
        fieldname = field['name']
        label = field.get('label', field['name'])
        if source.get(fieldname,None):
            # use a different attribute name if requested
            if fieldname in rename.keys():
                fname = rename[fieldname]
            else:
                fname = fieldname
            # direct attribute
            setattr(o, fname, source[fieldname])
            # fieldname,label,value tuple for use in template
            contents = source[fieldname]
            style = field_display_style(o, fieldname)
            if style:
                if style == 'facet':
                    facet = faceting.get_facet(fieldname)
                    contents_display = field_display_handler[style](fieldname, contents, facet)
                else:
                    contents_display = field_display_handler[style](fieldname, contents)
                o.fields.append( (fieldname, label, contents_display) )
    # signature file
    if source.get('signature_id', None):
        o.signature_id = source['signature_id']
    return o


# ----------------------------------------------------------------------

def get_stub_object(identifier):
    document = docstore.get(
        HOSTS, index=INDEX,
        model=identifier.model, document_id=identifier.id
    )
    if document and (document['found'] or document['exists']):
        object_class = identifier.object_class(mappings=MODEL_CLASSES)
        o = object_class()
        o.identifier = identifier
        for key,value in document['_source'].iteritems():
            setattr(o, key, value)
        return o
    return None

def get_object(identifier):
    document = docstore.get(
        HOSTS, index=INDEX,
        model=identifier.model, document_id=identifier.id
    )
    if document and (document['found'] or document['exists']):
        return build_object(identifier, document['_source'])
    return None


class Repository( object ):
    index = INDEX
    identifier = None
    fieldnames = []
    _organizations = []
    
    def __repr__( self ):
        return "<%s.%s %s:%s>" % (
            self.__module__, self.__class__.__name__,
            self.identifier.model,
            self.identifier.id
        )
    
    @staticmethod
    def get(identifier):
        return get_stub_object(identifier)
    
    def absolute_url( self ):
        return absolute_url(self.identifier)
    
    def cite_url( self ):
        return cite_url(self.identifier)

    def parent( self ):
        return None
    
    def children( self, page=1, page_size=DEFAULT_SIZE ):
        objects = []
        results = cached_query(
            host=HOSTS, index=INDEX, model='organization',
            query='id:"%s"' % self.identifier.id,
            fields=ORGANIZATION_LIST_FIELDS,
            sort=ORGANIZATION_LIST_SORT,
        )
        for hit in results['hits']['hits']:
            identifier = Identifier(hit['_id'])
            org = Organization.get(identifier)
            objects.append(org)
        return objects


class Organization( object ):
    index = INDEX
    identifier = None
    fieldnames = []
    _collections = []
    
    def __repr__( self ):
        return "<%s.%s %s:%s>" % (
            self.__module__, self.__class__.__name__,
            self.identifier.model,
            self.identifier.id
        )
    
    @staticmethod
    def get(identifier):
        return get_stub_object(identifier)
    
    def absolute_url( self ):
        return absolute_url(self.identifier)
    
    def cite_url( self ):
        return cite_url(self.identifier)
    
    def logo_url( self ):
        return org_logo_url(self.identifier)
    
    def children( self, page=1, page_size=DEFAULT_SIZE ):
        results = cached_query(
            host=HOSTS, index=INDEX, model='collection',
            query='id:"%s"' % self.identifier.id,
            fields=COLLECTION_LIST_FIELDS,
            sort=COLLECTION_LIST_SORT,
        )
        massaged = massage_query_results(results, page, page_size)
        objects = instantiate_query_objects(massaged)
        return objects
    
    def repository( self ):
        return None


class Collection( object ):
    index = INDEX
    identifier = None
    fieldnames = []
    signature_id = None
    
    def __repr__( self ):
        return "<%s.%s %s:%s>" % (
            self.__module__, self.__class__.__name__,
            self.identifier.model,
            self.identifier.id
        )
    
    @staticmethod
    def get(identifier):
        return get_object(identifier)
    
    def absolute_url( self ):
        return absolute_url(self.identifier)
    
    def backend_url( self ):
        return backend_url(self.identifier)
    
    def cite_url( self ):
        return cite_url(self.identifier)
    
    def children( self, page=1, page_size=DEFAULT_SIZE ):
        results = cached_query(
            host=HOSTS, index=INDEX, model='entity',
            query='id:"%s"' % self.identifier.id,
            fields=ENTITY_LIST_FIELDS,
            sort=ENTITY_LIST_SORT,
        )
        massaged = massage_query_results(results, page, page_size)
        objects = instantiate_query_objects(massaged)
        return objects
    
    def files( self, page=1, page_size=DEFAULT_SIZE ):
        """Gets all the files in a collection; paging optional.
        """
        files = []
        results = cached_query(
            host=HOSTS, index=INDEX, model='file',
            query='id:"%s"' % self.identifier.id,
            fields=FILE_LIST_FIELDS,
            sort=FILE_LIST_SORT
        )
        massaged = massage_query_results(results, page, page_size)
        objects = instantiate_query_objects(massaged)
        return objects
    
    def parent( self ):
        return Organization.get(self.identifier.parent(stubs=1))

    def org_logo_url( self ):
        return org_logo_url(self.identifier)
    
    def signature_url( self ):
        if self.signature_id:
            return signature_url(self.identifier, self.signature_id)
        return None
    
    def signature_url_local( self ):
        return media_url_local(self.signature_url())


ENTITY_OVERRIDDEN_FIELDS = {
    'topics': '_topics',
    'files': '_files',
}

class Entity( object ):
    index = INDEX
    identifier = None
    fieldnames = []
    signature_id = None
    _signature = None
    _topics = []
    _encyc_articles = []
    
    def __repr__( self ):
        return "<%s.%s %s:%s>" % (
            self.__module__, self.__class__.__name__,
            self.identifier.model,
            self.identifier.id
        )
    
    @staticmethod
    def get(identifier):
        return get_object(identifier)
    
    def absolute_url( self ):
        return absolute_url(self.identifier)
    
    def backend_url( self ):
        return backend_url(self.identifier)
    
    def cite_url( self ):
        return cite_url(self.identifier)
    
    def collection( self ):
        # TODO should be .parent()
        return Collection.get(self.identifier.parent())
    
    def children( self, page=1, page_size=DEFAULT_SIZE, role=None ):
        """Gets all the files in an entity; paging optional.
        
        @param index: start on this index in result set
        @param size: number of results to return
        @param role: String 'mezzanine' or 'master'
        """
        files = []
        query = 'id:"%s"' % self.identifier.id
        if role:
            query = 'id:"%s-%s"' % (self.identifier.id, role)
        results = cached_query(
            host=HOSTS, index=INDEX, model='file',
            query=query,
            fields=FILE_LIST_FIELDS,
            sort=FILE_LIST_SORT
        )
        massaged = massage_query_results(results, page, page_size)
        objects = instantiate_query_objects(massaged)
        return objects

    def org_logo_url( self ):
        return org_logo_url(self.identifier)
    
    def signature(self):
        if self.signature_id and not self._signature:
            oid = Identity.split_object_id(self.signature_id)
            self._signature = File.get(oid[1], oid[2], oid[3], oid[4], oid[5], oid[6])
        if self._signature:
            return self._signature
        return None
    
    def signature_url( self ):
        if self.signature_id:
            return signature_url(self.identifier, self.signature_id)
        return None
    
    def signature_url_local( self ):
        return media_url_local(self.signature_url())
    
    def topic_terms( self ):
        if hasattr(self, '_topics') and self._topics:
            topics = self._topics
        elif hasattr(self, 'topics') and self.topics:
            topics = self.topics
        else:
            topics = []
        return [faceting.Term('topics', int(tid)) for tid in topics]

    def encyc_articles( self ):
        if not self._encyc_articles:
            self._encyc_articles = []
            for term in self.topic_terms():
                for article in term.encyc_articles():
                    self._encyc_articles.append(article)
        return self._encyc_articles


class File( object ):
    index = INDEX
    identifier = None
    fieldnames = []
    _file_path = None
    _access_path = None
    
    def __repr__( self ):
        return "<%s.%s %s:%s>" % (
            self.__module__, self.__class__.__name__,
            self.identifier.model,
            self.identifier.id
        )
    
    @staticmethod
    def get(identifier):
        return get_object(identifier)
    
    def absolute_url( self ):
        return absolute_url(self.identifier)
    
    def access_path( self ):
        """S3 bucket-style path to access file, suitable for appending to MEDI_URL
        """
        if hasattr(self, 'access_rel') and self.access_rel and not self._access_path:
            self._access_path = '%s/%s' % (
                self.identifier.collection_id(),
                os.path.basename(self.access_rel)
            )
        return self._access_path
    
    def access_url( self ):
        if hasattr(self, 'access_rel') and self.access_rel:
            return settings.UI_THUMB_URL(self)
        return None
    
    def access_url_local( self ):
        return media_url_local(self.access_url())
    
    def backend_url( self ):
        return backend_url(identifier)
    
    def cite_url( self ):
        return cite_url(self.identifier)
    
    def parent( self ):
        return Entity.get(self.identifier.parent())

    def children( self ):
        return []
    
    def download_url( self ):
        return settings.UI_DOWNLOAD_URL(self)

    def org_logo_url( self ):
        return org_logo_url(self.identifier)
    
    def file_path(self):
        """S3 bucket-style path to original file, suitable for appending to MEDIA_URL
        """
        if hasattr(self, 'basename_orig') and self.basename_orig and not self._file_path:
            extension = os.path.splitext(self.basename_orig)[1]
            filename = self.identifier.id + extension
            self._file_path = os.path.join(self.identifier.collection_id(), filename)
        return self._file_path
