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
from DDR.models import MODELS_DIR, MODELS, MODULES
from DDR.models import Identity

from ui import faceting


DEFAULT_SIZE = 10

REPOSITORY_LIST_FIELDS = ['id', 'title', 'description', 'url',]
ORGANIZATION_LIST_FIELDS = ['id', 'title', 'description', 'url',]
COLLECTION_LIST_FIELDS = ['id', 'title', 'description', 'signature_file',]
ENTITY_LIST_FIELDS = ['id', 'title', 'description', 'signature_file',]
FILE_LIST_FIELDS = ['id', 'basename_orig', 'label', 'access_rel','sort',]

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

def make_object_url( parts ):
    """Takes a list of object ID parts and returns URL for that object.
    """
    if len(parts) == 6: return reverse('ui-file', args=parts)
    elif len(parts) == 4: return reverse('ui-entity', args=parts)
    elif len(parts) == 3: return reverse('ui-collection', args=parts)
    return None

def backend_url( object_type, object_id ):
    """Debug link to ElasticSearch page for the object.
    """
    if settings.DEBUG:
        return 'http://%s/%s/%s/%s' % (HOSTS, INDEX, object_type, object_id)
    return ''

def cite_url( model, object_id ):
    """Link to object's citation page
    """
    return reverse('ui-cite', args=(model, object_id))

def org_logo_url( organization_id ):
    """Link to organization logo image
    """
    return os.path.join(settings.MEDIA_URL, organization_id, 'logo.png')

def signature_url( signature_file ):
    """
    @param signature_file: str File ID
    """
    oid = Identity.split_object_id(signature_file)
    model = oid.pop(0)
    cid = Identity.make_object_id('collection', oid[0], oid[1], oid[2])
    return '%s%s/%s-a.jpg' % (settings.MEDIA_URL, cid, signature_file)

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
                oid = Identity.split_object_id(o['id'])
                if o['type'] == 'collection':
                    o['url'] = reverse('ui-collection', args=oid[1:])
                elif o['type'] == 'entity':
                    o['url'] = reverse('ui-entity', args=oid[1:])
                elif o['type'] == 'file':
                    o['url'] = reverse('ui-file', args=oid[1:])
    return objects

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
    for modelfield in model_fields(o.model):
        if modelfield['name'] == field:
            return modelfield['elasticsearch']['display']
    return None

# ----------------------------------------------------------------------

def model_fields(model):
    """Get list of fields from ES
    
    @param model: str Name of model
    @returns: list of field names
    """
    key = 'ddrpublic:%s:fields' % model
    cached = cache.get(key)
    if not cached:
        cached = []
        for m,module in MODULES.iteritems():
            if m == model:
                cached = module.FIELDS
        cache.set(key, cached, 60*1)
    return cached

def build_object( o, id, source, rename={} ):
    """Build object from ES GET data.
    
    NOTE: This only works on object types listed in DDR.models.MODULES.
    
    'rename' contains fields in 'source' that are to be given alternate names.
    Entity.files() and .topics() methods override the original fields.
    
    @param o: Blank object to build on.
    @param id: str DDR ID of the object.
    @param source: dict Contents of Elasticsearch document (document['_source']).
    @param rename: dict of {'fieldnames': 'alternate_names'}.
    """
    o.id = id
    o.fields = []
    for field in model_fields(o.model):
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
    # parent object ids
    oid = Identity.split_object_id(o.id)
    if o.model == 'file': m, o.repo,o.org,o.cid,o.eid,o.role,o.sha1 = oid
    elif o.model == 'entity': m, o.repo,o.org,o.cid,o.eid = oid
    elif o.model == 'collection': m, o.repo,o.org,o.cid = oid
    elif o.model == 'organization': m, o.repo,o.org = oid
    elif o.model == 'repository': m, o.repo = oid
    if o.model in ['file']:
        o.entity_id = Identity.make_object_id('entity', o.repo,o.org,o.cid,o.eid,o.role,o.sha1)
    if o.model in ['file','entity']:
        o.collection_id = Identity.make_object_id('collection', o.repo, o.org, o.cid)
    if o.model in ['file','entity','collection']:
        o.organization_id = Identity.make_object_id('org', o.repo,o.org)
    if o.model in ['file','entity','collection','organization']:
        o.repository_id = Identity.make_object_id('repo', o.repo)
    # signature file
    if source.get('signature_file', None):
        o.signature_file = source['signature_file']
    return o

def process_query_results( results, page, page_size ):
    objects = []
    massaged = massage_query_results(results, page, page_size)
    for hit in massaged:
        if hit.get('placeholder', None):
            objects.append(hit)
        else:
            if hit['model'] in ['repository', 'organization', 'collection', 'entity', 'file']:
                if hit['model'] == 'repository': object_class = Repository()
                elif hit['model'] == 'organization': object_class = Organization()
                elif hit['model'] == 'collection': object_class = Collection()
                elif hit['model'] == 'entity': object_class = Entity()
                elif hit['model'] == 'file': object_class = File()
                o = build_object(object_class, hit['id'], hit)
                if o:
                    objects.append(o)
                else:
                    objects.append(hit)
    return objects

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


# ----------------------------------------------------------------------


class Repository( object ):
    index = INDEX
    model = 'repository'
    id = None
    repo = None
    fieldnames = []
    _organizations = []
    
    def __repr__( self ):
        return '<ui.models.Repository %s>' % self.id
    
    @staticmethod
    def get( repo ):
        id = Identity.make_object_id(Repository.model, repo)
        document = docstore.get(HOSTS, index=INDEX, model=Repository.model, document_id=id)
        if document and (document['found'] or document['exists']):
            o = Repository()
            for key,value in document['_source'].iteritems():
                setattr(o, key, value)
            return o
        return None
    
    def absolute_url( self ):
        return reverse('ui-repo', args=(self.repo))
    
    def cite_url( self ):
        return cite_url('repo', self.id)
    
    def organizations( self, page=1, page_size=DEFAULT_SIZE ):
        objects = []
        results = cached_query(host=HOSTS, index=INDEX, model='organization',
                               query='id:"%s"' % self.id,
                               fields=ORGANIZATION_LIST_FIELDS,
                               sort=ORGANIZATION_LIST_SORT,)
        for hit in results['hits']['hits']:
            model,repo,org = Identity.split_object_id(hit['_id'])
            org = Organization.get(repo, org)
            objects.append(org)
        return objects


class Organization( object ):
    index = INDEX
    model = 'organization'
    id = None
    repo = None
    org = None
    fieldnames = []
    _collections = []
    
    def __repr__( self ):
        return '<ui.models.Organization %s>' % self.id
    
    @staticmethod
    def get( repo, org ):
        id = Identity.make_object_id(Organization.model, repo, org)
        document = docstore.get(HOSTS, index=INDEX, model=Organization.model, document_id=id)
        if document and (document['found'] or document['exists']):
            o = Organization()
            for key,value in document['_source'].iteritems():
                setattr(o, key, value)
            return o
        return None
    
    def absolute_url( self ):
        return reverse('ui-organization', args=(self.repo, self.org))
    
    def cite_url( self ):
        return cite_url('org', self.id)
    
    def logo_url( self ):
        return org_logo_url( self.id )
    
    def collections( self, page=1, page_size=DEFAULT_SIZE ):
        results = cached_query(host=HOSTS, index=INDEX, model='collection',
                               query='id:"%s"' % self.id,
                               fields=COLLECTION_LIST_FIELDS,
                               sort=COLLECTION_LIST_SORT,)
        objects = process_query_results( results, page, page_size )
        return objects
    
    def repository( self ):
        return None


class Collection( object ):
    index = INDEX
    model = 'collection'
    id = None
    repo = None
    org = None
    cid = None
    fieldnames = []
    signature_file = None
    
    def __repr__( self ):
        return '<ui.models.Collection %s>' % self.id
    
    @staticmethod
    def get( repo, org, cid ):
        id = Identity.make_object_id(Collection.model, repo, org, cid)
        document = docstore.get(HOSTS, index=INDEX, model=Collection.model, document_id=id)
        if document and (document['found'] or document['exists']):
            return build_object(Collection(), id, document['_source'])
        return None
    
    def absolute_url( self ):
        return reverse('ui-collection', args=(self.repo, self.org, self.cid))
    
    def backend_url( self ):
        return backend_url('collection', self.id)
    
    def cite_url( self ):
        return cite_url('collection', self.id)
    
    def entities( self, page=1, page_size=DEFAULT_SIZE ):
        results = cached_query(host=HOSTS, index=INDEX, model='entity',
                               query='id:"%s"' % self.id,
                               fields=ENTITY_LIST_FIELDS,
                               sort=ENTITY_LIST_SORT,)
        objects = process_query_results( results, page, page_size )
        return objects
    
    def files( self, page=1, page_size=DEFAULT_SIZE ):
        """Gets all the files in a collection; paging optional.
        """
        files = []
        results = cached_query(host=HOSTS, index=INDEX, model='file',
                               query='id:"%s"' % self.id,
                               fields=FILE_LIST_FIELDS,
                               sort=FILE_LIST_SORT)
        objects = process_query_results( results, page, page_size )
        return objects
    
    def organization( self ):
        return Organization.get(self.repo, self.org)

    def org_logo_url( self ):
        return org_logo_url( '-'.join([self.repo, self.org]) )
    
    def signature_url( self ):
        if self.signature_file:
            return signature_url(self.signature_file)
        return None
    
    def signature_url_local( self ):
        return media_url_local(self.signature_url())


ENTITY_OVERRIDDEN_FIELDS = {
    'topics': '_topics',
    'files': '_files',
}

class Entity( object ):
    index = INDEX
    model = 'entity'
    id = None
    repo = None
    org = None
    cid = None
    eid = None
    fieldnames = []
    signature_file = None
    _signature = None
    _topics = []
    _encyc_articles = []
    
    def __repr__( self ):
        return '<ui.models.Entity %s>' % self.id
    
    @staticmethod
    def get( repo, org, cid, eid ):
        id = Identity.make_object_id(Entity.model, repo, org, cid, eid)
        document = docstore.get(HOSTS, index=INDEX, model=Entity.model, document_id=id)
        if document and (document['found'] or document['exists']):
            return build_object(Entity(), id, document['_source'], ENTITY_OVERRIDDEN_FIELDS)
        return None
    
    def absolute_url( self ):
        return reverse('ui-entity', args=(self.repo, self.org, self.cid, self.eid))
    
    def backend_url( self ):
        return backend_url('entity', self.id)
    
    def cite_url( self ):
        return cite_url('entity', self.id)
    
    def files( self, page=1, page_size=DEFAULT_SIZE, role=None ):
        """Gets all the files in an entity; paging optional.
        
        @param index: start on this index in result set
        @param size: number of results to return
        @param role: String 'mezzanine' or 'master'
        """
        files = []
        query = 'id:"%s"' % self.id
        if role:
            query = 'id:"%s-%s"' % (self.id, role)
        results = cached_query(host=HOSTS, index=INDEX, model='file',
                               query=query,
                               fields=FILE_LIST_FIELDS,
                               sort=FILE_LIST_SORT)
        objects = process_query_results( results, page, page_size )
        return objects

    def org_logo_url( self ):
        return org_logo_url( '-'.join([self.repo, self.org]) )
    
    def collection( self ):
        return Collection.get(self.repo, self.org, self.cid)
    
    def signature(self):
        if self.signature_file and not self._signature:
            oid = Identity.split_object_id(self.signature_file)
            self._signature = File.get(oid[1], oid[2], oid[3], oid[4], oid[5], oid[6])
        if self._signature:
            return self._signature
        return None
    
    def signature_url( self ):
        if self.signature_file:
            return signature_url(self.signature_file)
        return None
    
    def signature_url_local( self ):
        return media_url_local(self.signature_url())
    
    def topics( self ):
        return [faceting.Term('topics', int(tid)) for tid in self._topics]

    def encyc_articles( self ):
        if not self._encyc_articles:
            self._encyc_articles = []
            for term in self.topics():
                for article in term.encyc_articles():
                    self._encyc_articles.append(article)
        return self._encyc_articles


class File( object ):
    index = INDEX
    model = 'file'
    id = None
    repo = None
    org = None
    cid = None
    eid = None
    role = None
    sha1 = None
    fieldnames = []
    _file_path = None
    _access_path = None
    
    def __repr__( self ):
        return '<ui.models.File %s>' % self.id
    
    @staticmethod
    def get( repo, org, cid, eid, role, sha1 ):
        id = Identity.make_object_id(File.model, repo, org, cid, eid, role, sha1)
        document = docstore.get(HOSTS, index=INDEX, model=File.model, document_id=id)
        if document and (document['found'] or document['exists']):
            return build_object(File(), id, document['_source'])
        return None
    
    def absolute_url( self ):
        return reverse('ui-file', args=(self.repo, self.org, self.cid, self.eid, self.role, self.sha1))
    
    def access_path( self ):
        """S3 bucket-style path to access file, suitable for appending to MEDIA_URL
        """
        if hasattr(self, 'access_rel') and self.access_rel and not self._access_path:
            self._access_path = '%s/%s' % (self.collection_id, self.access_rel)
        return self._access_path
    
    def access_url( self ):
        if hasattr(self, 'access_rel') and self.access_rel:
            return settings.UI_THUMB_URL(self)
        return None
    
    def access_url_local( self ):
        return media_url_local(self.access_url())
    
    def backend_url( self ):
        return backend_url('file', self.id)
    
    def cite_url( self ):
        return cite_url('file', self.id)
    
    def entity( self ):
        return Entity.get(self.repo, self.org, self.cid, self.eid)
    
    def download_url( self ):
        return settings.UI_DOWNLOAD_URL(self)

    def org_logo_url( self ):
        return org_logo_url( '-'.join([self.repo, self.org]) )
    
    def file_path(self):
        """S3 bucket-style path to original file, suitable for appending to MEDIA_URL
        """
        if hasattr(self, 'basename_orig') and self.basename_orig and not self._file_path:
            extension = os.path.splitext(self.basename_orig)[1]
            filename = self.id + extension
            self._file_path = os.path.join(self.collection_id, filename)
        return self._file_path
