import json
import logging
logger = logging.getLogger(__name__)

from dateutil import parser

from django.conf import settings
from django.core.urlresolvers import reverse

from DDR import elasticsearch
from DDR import models

INDEX = 'ddr'

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

def build_object( o, id, source ):
    """Build object from ES GET data.
    """
    o.id = id
    o.fields = []
    for field in models.model_fields(o.model):
        fieldname = field['name']
        label = field.get('label', field['name'])
        if source.get(fieldname,None):
            # direct attribute
            setattr(o, fieldname, source[fieldname])
            # fieldname,label,value tuple for use in template
            o.fields.append( (fieldname, label, source[fieldname]) )
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
    index = INDEX
    model = 'repository'
    id = None
    repo = None
    fieldnames = []
    
    @staticmethod
    def get( repo ):
        # TODO add repo to ElasticSearch so we can do this the right way
        r = Repository()
        r.repo = repo
        r.id = make_object_id(r.model, repo)
        #build_object(r)
        return r
    
    def organizations( self ):
        # TODO add repo to ElasticSearch so we can do this the right way
        #hits = elasticsearch.query(HOST, index=INDEX, model='organization', query='id:"%s"' % self.id)
        #organizations = massage_hits(hits)
        organizations = ['ddr-densho', 'ddr-testing',]
        return organizations


class Organization( object ):
    index = INDEX
    model = 'organization'
    id = None
    repo = None
    org = None
    fieldnames = []
    
    @staticmethod
    def get( repo, org ):
        # TODO add repo to ElasticSearch so we can do this the right way
        o = Organization()
        o.repo = repo
        o.org = org
        o.id = make_object_id(o.model, repo, org)
        #build_object(o)
        return o
    
    def collections( self ):
        results = elasticsearch.query(HOST, index=INDEX, model='collection', query='id:"%s"' % self.id, sort='id',)
        collections = massage_query_results(results)
        return collections


class Collection( object ):
    index = INDEX
    model = 'collection'
    id = None
    repo = None
    org = None
    cid = None
    fieldnames = []
    
    @staticmethod
    def get( repo, org, cid ):
        id = make_object_id(Collection.model, repo, org, cid)
        raw = elasticsearch.get(HOST, index=INDEX, model=Collection.model, id=id)
        status = raw['status']
        response = json.loads(raw['response'])
        if (status == 200) and response['exists']:
            return build_object(Collection(), id, response['_source'])
        return None
    
    def entities( self ):
        results = elasticsearch.query(HOST, index=INDEX, model='entity', query='id:"%s"' % self.id, sort='id',)
        entities = massage_query_results(results)
        return entities


class Entity( object ):
    index = INDEX
    model = 'entity'
    id = None
    repo = None
    org = None
    cid = None
    eid = None
    fieldnames = []
    
    @staticmethod
    def get( repo, org, cid, eid ):
        id = make_object_id(Entity.model, repo, org, cid, eid)
        raw = elasticsearch.get(HOST, index=INDEX, model=Entity.model, id=id)
        status = raw['status']
        response = json.loads(raw['response'])
        if (status == 200) and response['exists']:
            return build_object(Entity(), id, response['_source'])
        return None
    
    def files( self ):
        results = elasticsearch.query(HOST, index=INDEX, model='file', query='id:"%s"' % self.id, sort='id',)
        files = massage_query_results(results)
        for f in files:
            f['xmp'] = None
        return files


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
    
    @staticmethod
    def get( repo, org, cid, eid, role, sha1 ):
        id = make_object_id(File.model, repo, org, cid, eid, role, sha1)
        raw = elasticsearch.get(HOST, index=INDEX, model=File.model, id=id)
        status = raw['status']
        response = json.loads(raw['response'])
        if (status == 200) and response['exists']:
            return build_object(File(), id, response['_source'])
        return None
    
    def access_url( self ):
        return settings.UI_THUMB_URL(self)
