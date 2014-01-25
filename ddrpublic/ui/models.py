from django.conf import settings

import elasticsearch

INDEX = 'ddr'


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

def get_object_fields( index, model, object_id ):
    get = elasticsearch.get(index=index, model=model, id=object_id)
    if get:
        fields = []
        for field in get:
            for k,v in field.iteritems():
                fields.append((k,v))
        return fields
    return None
def get_organization_fields( object_id ): return get_object_fields(index, 'organization', object_id)
def get_collection_fields( object_id ): return get_object_fields(index, 'collection', object_id)
def get_entity_fields( object_id ): return get_object_fields(index, 'entity', object_id)
def get_file_fields( object_id ): return get_object_fields(index, 'file', object_id)

def get_object( index, model, object_id ):
    fields = get_object_fields(index, model, object_id)
    if fields:
        o = {'fieldnames': [], 'fields': [],}
        for k,v in fields:
            o['fieldnames'].append(k)
            o['fields'].append((k,v))
            o[k] = v
        return o
    return None
def get_organization( index, object_id ): return get_object_fields(index, 'organization', object_id)
def get_collection( index, object_id ): return get_object_fields(index, 'colllaection', object_id)
def get_entity( index, object_id ): return get_object_fields(index, 'entity', object_id)
def get_file( index, object_id ): return get_object_fields(index, 'file', object_id)

def build_object( obj, fields ):
    obj.fieldnames = []
    obj.fields = []
    for k,v in fields:
        # entity JSON contains 'files' field that clashes with Entity.files() function
        if (k == 'files') and (obj.model == 'entity'):
            k = '_files'
        obj.fieldnames.append(k)
        obj.fields.append((k,v))
        setattr(obj, k, v)
    
    # parent object ids
    if   obj.model == 'collection':
        pass
    elif obj.model == 'entity':
        repo,org,cid,eid = obj.id.split('-')
        obj.collection_id = '-'.join([repo,org,cid])
    elif obj.model == 'file':
        repo,org,cid,eid,role,sha1 = obj.id.split('-')
        obj.collection_id = '-'.join([repo,org,cid])
        obj.entity_id = '-'.join([repo,org,cid,eid])


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
        #hits = elasticsearch.query(model='organization', query='id:"%s"' % self.id)
        #organizations = elasticsearch.massage_hits(hits)
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
        hits = elasticsearch.query(model='collection', query='id:"%s"' % self.id, sort='id',)
        collections = elasticsearch.massage_hits(hits)
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
        fields = get_object_fields(INDEX, Collection.model, id)
        if fields:
            c = Collection()
            build_object(c, fields)
            return c
        return None
    
    def entities( self ):
        hits = elasticsearch.query(model='entity', query='id:"%s"' % self.id, sort='id',)
        entities = elasticsearch.massage_hits(hits)
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
        fields = get_object_fields(INDEX, Entity.model, id)
        if fields:
            e = Entity()
            build_object(e, fields)
            return e
        return None
    
    def files( self ):
        hits = elasticsearch.query(model='file', query='id:"%s"' % self.id, sort='id',)
        files = elasticsearch.massage_hits(hits)
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
        fields = get_object_fields(INDEX, File.model, id)
        if fields:
            f = File()
            build_object(f, fields)
            return f
        return None
