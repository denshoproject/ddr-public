import json
import logging
logger = logging.getLogger(__name__)

from dateutil import parser

from django.conf import settings
from django.core.urlresolvers import reverse
from django.template import Context, Template
from django.utils.http import urlquote  as django_urlquote

from DDR import elasticsearch
from DDR import models as DDRmodels

from ui import faceting

MODEL_FIELDS = elasticsearch.model_fields()

HOST = settings.ELASTICSEARCH_HOST_PORT


# TODO reindex using parents/children (http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/docs-index_.html#parent-children)


# functions for GETing object data from ElasticSearch

def make_object_id( model, repo, org=None, cid=None, eid=None, role=None, sha1=None ):
    if   (model == 'file') and repo and org and cid and eid and role and sha1:
        return '%s-%s-%s-%s-%s-%s' % (repo, org, cid, eid, role, sha1)
    elif (model == 'entity') and repo and org and cid and eid:
        return '%s-%s-%s-%s' % (repo, org, cid, eid)
    elif (model == 'collection') and repo and org and cid:
        return '%s-%s-%s' % (repo, org, cid)
    elif (model == 'organization') and repo and org:
        return '%s-%s' % (repo, org)
    elif (model == 'repo') and repo:
        return repo
    return None

def massage_query_results( results ):
    """Take data from ES query, make a reasonable facsimile of the original object.
    """
    objects = []
    for hit in results.get('hits', [])['hits']:
        o = hit['_source']
        # copy ES results info to individual object source
        o['index'] = hit['_index']
        o['type'] = hit['_type']
        o['model'] = hit['_type']
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
        objects.append(o)
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
    for t in text:
        url = '/search/results/?query=%s:%s' % (fieldname, django_urlquote(t.strip()))
        termdata = {'url':url, 'term':t.strip(), 'title':t.strip()}
        if facet and facet['terms']:
            for term in facet['terms']:
                if term[0] == t:
                    termdata['title'] = term[1]
        lines.append(termdata)
    t = Template(FACET_TEMPLATE)
    c = Context({'facets': lines})
    return t.render(c)

def display_filesize(fieldname, text):
    t = Template(FILESIZE_TEMPLATE)
    c = Context({'text':text})
    return t.render(c)

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
    'string': display_string,
    'string_collapsed': display_string_collapsed,
}

def field_display_style( o, field ):
    for modelfield in MODEL_FIELDS[o.model]:
        if modelfield['name'] == field:
            return modelfield['elasticsearch']['display']
    return None

# ----------------------------------------------------------------------

def build_object( o, id, source ):
    """Build object from ES GET data.
    """
    facets = faceting.facets_list()
    o.id = id
    o.fields = []
    for field in DDRmodels.model_fields(o.model):
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
                    facet = faceting.get_facet(facets, fieldname)
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
    # parent object ids
    if o.model == 'file': o.repo,o.org,o.cid,o.eid,o.role,o.sha1 = o.id.split('-')
    elif o.model == 'entity': o.repo,o.org,o.cid,o.eid = o.id.split('-')
    elif o.model == 'collection': o.repo,o.org,o.cid = o.id.split('-')
    elif o.model == 'organization': o.repo,o.org = o.id.split('-')
    if o.model in ['file']: o.entity_id = '%s-%s-%s-%s' % (o.repo,o.org,o.cid,o.eid)
    if o.model in ['file','entity']: o.collection_id = '%s-%s-%s' % (o.repo,o.org,o.cid)
    if o.model in ['file','entity','collection']: o.organization_id = '%s-%s' % (o.repo,o.org)
    if o.model in ['file','entity','collection','organization']: o.repository_id = '%s' % (o.repo)
    return o


class Repository( object ):
    index = settings.DOCUMENT_INDEX
    model = 'repository'
    id = None
    repo = None
    fieldnames = []
    _organizations = []
    
    @staticmethod
    def get( repo ):
        # TODO add repo to ElasticSearch so we can do this the right way
        r = Repository()
        r.repo = repo
        r.id = make_object_id(r.model, repo)
        #build_object(r)
        return r
    
    def absolute_url( self ):
        return reverse('ui-repo', args=(self.repo))
    
    def organizations( self ):
        # TODO add repo to ElasticSearch so we can do this the right way
        #hits = elasticsearch.query(HOST, index=settings.DOCUMENT_INDEX, model='organization', query='id:"%s"' % self.id)
        #organizations = massage_hits(hits)
        if not self._organizations:
            org_ids = ['ddr-densho', 'ddr-jamsj', 'ddr-janm', 'ddr-jcch', 'ddr-njpa', 'ddr-one', 'ddr-qumulo', 'ddr-testing',]
            organizations = []
            for org_id in org_ids:
                repo,org = org_id.split('-')
                o = Organization.get(repo, org)
                self._organizations.append(o)
        return self._organizations


class Organization( object ):
    index = settings.DOCUMENT_INDEX
    model = 'organization'
    id = None
    repo = None
    org = None
    fieldnames = []
    _collections = []
    
    @staticmethod
    def get( repo, org ):
        # TODO add repo to ElasticSearch so we can do this the right way
        o = Organization()
        o.repo = repo
        o.org = org
        o.id = make_object_id(o.model, repo, org)
        #build_object(o)
        return o
    
    def absolute_url( self ):
        return reverse('ui-organization', args=(self.repo, self.org))
    
    def collections( self ):
        if not self._collections:
            results = elasticsearch.query(HOST, index=settings.DOCUMENT_INDEX, model='collection', query='id:"%s"' % self.id, sort='id',)
            self._collections = massage_query_results(results)
        return self._collections
    
    def parent( self ):
        return None


class Collection( object ):
    index = settings.DOCUMENT_INDEX
    model = 'collection'
    id = None
    repo = None
    org = None
    cid = None
    fieldnames = []
    _entities = []
    
    @staticmethod
    def get( repo, org, cid ):
        id = make_object_id(Collection.model, repo, org, cid)
        raw = elasticsearch.get(HOST, index=settings.DOCUMENT_INDEX, model=Collection.model, id=id)
        status = raw['status']
        response = json.loads(raw['response'])
        if (status == 200) and response['exists']:
            return build_object(Collection(), id, response['_source'])
        return None
    
    def absolute_url( self ):
        return reverse('ui-collection', args=(self.repo, self.org, self.cid))
    
    def entities( self ):
        if not self._entities:
            results = elasticsearch.query(HOST, index=settings.DOCUMENT_INDEX, model='entity', query='id:"%s"' % self.id, sort='id',)
            self._entities = massage_query_results(results)
        return self._entities
    
    def parent( self ):
        return Organization.get(self.repo, self.org)


class Entity( object ):
    index = settings.DOCUMENT_INDEX
    model = 'entity'
    id = None
    repo = None
    org = None
    cid = None
    eid = None
    fieldnames = []
    _files = []
    
    @staticmethod
    def get( repo, org, cid, eid ):
        id = make_object_id(Entity.model, repo, org, cid, eid)
        raw = elasticsearch.get(HOST, index=settings.DOCUMENT_INDEX, model=Entity.model, id=id)
        status = raw['status']
        response = json.loads(raw['response'])
        if (status == 200) and response['exists']:
            return build_object(Entity(), id, response['_source'])
        return None
    
    def absolute_url( self ):
        return reverse('ui-entity', args=(self.repo, self.org, self.cid, self.eid))
    
    def files( self ):
        if not self._files:
            results = elasticsearch.query(HOST, index=settings.DOCUMENT_INDEX, model='file', query='id:"%s"' % self.id, sort='id',)
            self._files = massage_query_results(results)
            for f in self._files:
                f['xmp'] = None
        return self._files
    
    def parent( self ):
        return Collection.get(self.repo, self.org, self.cid)


class File( object ):
    index = settings.DOCUMENT_INDEX
    model = 'file'
    id = None
    repo = None
    org = None
    cid = None
    eid = None
    role = None
    sha1 = None
    fieldnames = []
    
    @staticmethod
    def get( repo, org, cid, eid, role, sha1 ):
        id = make_object_id(File.model, repo, org, cid, eid, role, sha1)
        raw = elasticsearch.get(HOST, index=settings.DOCUMENT_INDEX, model=File.model, id=id)
        status = raw['status']
        response = json.loads(raw['response'])
        if (status == 200) and response['exists']:
            return build_object(File(), id, response['_source'])
        return None
    
    def absolute_url( self ):
        return reverse('ui-file', args=(self.repo, self.org, self.cid, self.eid, self.role, self.sha1))
    
    def access_url( self ):
        return settings.UI_THUMB_URL(self)
    
    def parent( self ):
        return Entity.get(self.repo, self.org, self.cid, self.eidde)
