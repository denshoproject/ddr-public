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
from DDR.models import model_fields as ddr_model_fields, MODELS_DIR, MODELS
from DDR.models import make_object_id, split_object_id

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
                if o['type'] == 'collection':
                    repo,org,cid = o['id'].split('-')
                    o['url'] = reverse('ui-collection', args=[repo,org,cid])
                elif o['type'] == 'entity':
                    repo,org,cid,eid = o['id'].split('-')
                    o['url'] = reverse('ui-entity', args=[repo,org,cid,eid])
                elif o['type'] == 'file':
                    repo,org,cid,eid,role,sha1 = o['id'].split('-')
                    o['url'] = reverse('ui-file', args=[repo,org,cid,eid,role,sha1])
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
    modelfields = docstore._model_fields(MODELS_DIR, MODELS)
    for modelfield in modelfields[o.model]:
        if modelfield['name'] == field:
            return modelfield['elasticsearch']['display']
    return None

# ----------------------------------------------------------------------


def build_object( o, id, source ):
    """Build object from ES GET data.
    """
    o.id = id
    o.fields = []
    for field in ddr_model_fields(o.model):
        fieldname = field['name']
        label = field.get('label', field['name'])
        if source.get(fieldname,None):
            # direct attribute
            setattr(o, fieldname, source[fieldname])
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
    # rename entity.files to entity._files
    ohasattr = hasattr(o, 'files')
    if (o.model == 'entity') and hasattr(o, 'files'):
        o._files = o.files
        try:
            delattr(o, 'files')
        except:
            pass
    # rename entity.topics -> entity._topics
    if (o.model == 'entity') and hasattr(o, 'topics'):
        o._topics = o.topics
        try:
            delattr(o, 'topics')
        except:
            pass
    # parent object ids
    if o.model == 'file': o.repo,o.org,o.cid,o.eid,o.role,o.sha1 = o.id.split('-')
    elif o.model == 'entity': o.repo,o.org,o.cid,o.eid = o.id.split('-')
    elif o.model == 'collection': o.repo,o.org,o.cid = o.id.split('-')
    elif o.model == 'organization': o.repo,o.org = o.id.split('-')
    elif o.model == 'repository': o.repo = o.id.split('-')
    if o.model in ['file']: o.entity_id = '%s-%s-%s-%s' % (o.repo,o.org,o.cid,o.eid)
    if o.model in ['file','entity']: o.collection_id = '%s-%s-%s' % (o.repo,o.org,o.cid)
    if o.model in ['file','entity','collection']: o.organization_id = '%s-%s' % (o.repo,o.org)
    if o.model in ['file','entity','collection','organization']: o.repository_id = '%s' % (o.repo)
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

def cached_query(host, index, model='', query='', terms={}, filters={}, fields=[], sort=[]):
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
                                 fields=fields, sort=sort)
        cache.set(key, cached, settings.ELASTICSEARCH_QUERY_TIMEOUT)
    return cached


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
        id = make_object_id(Repository.model, repo)
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
        results = cached_query(host=HOSTS, index=INDEX, model='organization',
                               query='id:"%s"' % self.id,
                               fields=ORGANIZATION_LIST_FIELDS,
                               sort=ORGANIZATION_LIST_SORT,)
        objects = process_query_results( results, page, page_size )
        for o in objects:
            for hit in results['hits']['hits']:
                fields = hit['fields']
                if fields.get('id',None) and fields['id'] == o.id:
                    o.url = fields.get('url', None)
                    o.title = fields.get('title', o.id)
                    o.description = fields.get('description', None)
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
        id = make_object_id(Organization.model, repo, org)
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
        id = make_object_id(Collection.model, repo, org, cid)
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
            return '%s%s/%s-a.jpg' % (settings.MEDIA_URL, self.id, self.signature_file)
        return None


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
    _topics = []
    
    def __repr__( self ):
        return '<ui.models.Entity %s>' % self.id
    
    @staticmethod
    def get( repo, org, cid, eid ):
        id = make_object_id(Entity.model, repo, org, cid, eid)
        document = docstore.get(HOSTS, index=INDEX, model=Entity.model, document_id=id)
        if document and (document['found'] or document['exists']):
            return build_object(Entity(), id, document['_source'])
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
    
    def signature_url( self ):
        if self.signature_file:
            return '%s%s/%s-a.jpg' % (settings.MEDIA_URL, self.collection_id, self.signature_file)
        return None
    
    def topics( self ):
        return [faceting.Term('topics', int(tid)) for tid in self._topics]



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
    
    def __repr__( self ):
        return '<ui.models.File %s>' % self.id
    
    @staticmethod
    def get( repo, org, cid, eid, role, sha1 ):
        id = make_object_id(File.model, repo, org, cid, eid, role, sha1)
        document = docstore.get(HOSTS, index=INDEX, model=File.model, document_id=id)
        if document and (document['found'] or document['exists']):
            return build_object(File(), id, document['_source'])
        return None
    
    def absolute_url( self ):
        return reverse('ui-file', args=(self.repo, self.org, self.cid, self.eid, self.role, self.sha1))
    
    def access_url( self ):
        if hasattr(self, 'access_rel') and self.access_rel:
            return settings.UI_THUMB_URL(self)
        return None
    
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
