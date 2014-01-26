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
    """massage the results
    """
    def rename(hit, fieldname):
        # Django templates can't display fields/attribs that start with underscore
        under = '_%s' % fieldname
        hit[fieldname] = hit.pop(under)
    hits = results['hits']['hits']
    for hit in hits:
        rename(hit, 'index')
        rename(hit, 'type')
        rename(hit, 'id')
        rename(hit, 'score')
        rename(hit, 'source')
        # assemble urls for each record type
        if hit.get('id', None):
            if hit['type'] == 'collection':
                try:
                    # TODO This helps us deal with bad data like ddr-testing-141-1 (an entity)
                    #      getting added to index as a collection
                    #      That problem should be solved so we can remove this.
                    repo,org,cid = hit['id'].split('-')
                    hit['url'] = reverse('ui-collection', args=[repo,org,cid])
                except:
                    hits.remove(hit)
            elif hit['type'] == 'entity':
                repo,org,cid,eid = hit['id'].split('-')
                hit['url'] = reverse('ui-entity', args=[repo,org,cid,eid])
            elif hit['type'] == 'file':
                repo,org,cid,eid,role,sha1 = hit['id'].split('-')
                hit['url'] = reverse('ui-file', args=[repo,org,cid,eid,role,sha1])
    return hits


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
        #hits = elasticsearch.query(HOST, model='organization', query='id:"%s"' % self.id)
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
        results = elasticsearch.query(HOST, model='collection', query='id:"%s"' % self.id, sort='id',)
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
        document = elasticsearch.get_document(HOST, index=INDEX, model=Collection.model, id=id)
        if document:
            o = Collection()
            o.fieldnames = models.model_fields(Collection.model)
            o.id = id
            o.fields = []
            for fieldname in o.fieldnames:
                if document.get(fieldname,None):
                    # direct attribute
                    setattr(o, fieldname, document[fieldname])
                    # key,value tuple for use in template
                    o.fields.append( (fieldname, document[fieldname]) )
            return o
        return None
    
    def entities( self ):
        results = elasticsearch.query(HOST, model='entity', query='id:"%s"' % self.id, sort='id',)
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
        document = elasticsearch.get_document(HOST, index=INDEX, model=Entity.model, id=id)
        if document:
            o = Entity()
            o.fieldnames = models.model_fields(Entity.model)
            o.id = id
            setattr(o, 'collection_id', '-'.join([repo,org,cid]))
            o.fields = []
            for fieldname in o.fieldnames:
                # entity JSON contains 'files' field that clashes with Entity.files() function
                if fieldname == 'files':
                    fieldname = '_files'
                if document.get(fieldname,None):
                    # direct attribute
                    setattr(o, fieldname, document[fieldname])
                    # key,value tuple for use in template
                    o.fields.append( (fieldname, document[fieldname]) )
            return o
        return None
    
    def files( self ):
        results = elasticsearch.query(HOST, model='file', query='id:"%s"' % self.id, sort='id',)
        files = massage_query_results(results)
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
        document = elasticsearch.get_document(HOST, index=INDEX, model=File.model, id=id)
        if document:
            o = File()
            o.fieldnames = models.model_fields(File.model)
            o.id = id
            setattr(o, 'entity_id', '-'.join([repo,org,cid,eid]))
            setattr(o, 'collection_id', '-'.join([repo,org,cid]))
            o.fields = []
            fieldnames = o.fieldnames
            for fieldname in o.fieldnames:
                if document.get(fieldname,None):
                    # direct attribute
                    setattr(o, fieldname, document[fieldname])
                    # key,value tuple for use in template
                    o.fields.append( (fieldname, document[fieldname]) )
            return o
        return None
    
    def access_url( self ):
        return settings.UI_THUMB_URL(self)
