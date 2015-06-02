import os

from django.conf import settings
from django.http import HttpResponseRedirect

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse

from DDR import docstore
from DDR.models import Identity
from ui.models import Repository, Organization, Collection, Entity, File
from ui.views import filter_if_branded
from ui import faceting
from ui import models

DEFAULT_LIMIT = 25


# helpers --------------------------------------------------------------

URL_FIELDS = ['ancestors', 'siblings', 'children']

def http_host(request):
    return 'http://%s' % request.META['HTTP_HOST']

def add_url_host(request, data):
    host = http_host(request)
    for key,val in data.iteritems():
        if key and val \
        and isinstance(val, basestring) \
        and (('url' in key) or (key in URL_FIELDS)) \
        and ('http://' not in val):
            data[key] = '%s%s' % (host, val)

def add_host_list(request, data):
    host = http_host(request)
    new = []
    for val in data:
        if val \
        and isinstance(val, basestring) \
        and ('http://' not in val):
            val = '%s%s' % (host, val)
        new.append(val)
    return new

def term_urls(request, data, facet_id, fieldname):
    """Convert facet term IDs to links to term API nodes.
    """
    topics_urls = [
        reverse('ui-api-term', args=(facet_id, tid), request=request)
        for tid in data.get(fieldname, [])
        if tid
    ]
    data[fieldname] = topics_urls

def api_children(model, object_id, request, limit=DEFAULT_LIMIT, offset=0):
    """Return object children list in Django REST Framework format.
    
    Returns a paged list with count/previous/next metadata
    
    @returns: dict
    """
    q = 'id:"%s"' % object_id
    sort = docstore._clean_sort(models.MODEL_LIST_SETTINGS[model]['sort'])
    fields = ','.join(models.MODEL_LIST_SETTINGS[model]['fields'])
    es = docstore._get_connection(settings.DOCSTORE_HOSTS)
    results = es.search(
        index=settings.DOCSTORE_INDEX,
        doc_type=model,
        q=q,
        body={},
        sort=sort,
        _source_include=fields,
        from_=offset,
        size=limit,
    )
    #
    count = results['hits']['total']
    previous,next_ = None,None
    p = offset - limit
    n = offset + limit
    if p < 0:
        p = None
    if n >= count:
        n = None
    if p is not None:
        previous = '?limit=%s&offset=%s' % (limit, p)
    if n:
        next_ = '?limit=%s&offset=%s' % (limit, n)
    #
    data = {
        "count": count,
        "previous": previous,
        "next": next_,
        "results": [hit['_source'] for hit in results['hits']['hits']],
    }
    return data

def access_filename(file_id):
    """
    TODO This is probably redundant. D-R-Y!
    """
    if file_id:
        return '%s-a.jpg' % file_id
    return file_id

def img_url(bucket, filename, request):
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
    internal = request.GET.get(settings.MEDIA_URL_LOCAL_MARKER, 0)
    if internal and isinstance(internal, basestring) and internal.isdigit():
        internal = int(internal)
    if bucket and filename and internal:
        return '%s%s/%s' % (settings.MEDIA_URL_LOCAL, bucket, filename)
    elif bucket and filename:
        return '%s%s/%s' % (settings.MEDIA_URL, bucket, filename)
    return None


# classes --------------------------------------------------------------

class ApiRepository(Repository):
    
    @staticmethod
    def api_get(repo, request):
        id = Identity.make_object_id(Repository.model, repo)
        document = docstore.get(
            settings.DOCSTORE_HOSTS, index=settings.DOCSTORE_INDEX,
            model=Repository.model, document_id=id)
        if document and (document['found'] or document['exists']):
            d = document['_source']
            d['repository_url'] = d['url']
            d['url'] = reverse('ui-api-repository', args=(repo,), request=request)
            d['absolute_url'] = reverse('ui-repo', args=(repo,), request=request)
            d['children'] = reverse('ui-api-organizations', args=(repo,), request=request)
            return d
        return None

    @staticmethod
    def api_children(repo, request, limit=DEFAULT_LIMIT, offset=0):
        object_id = Identity.make_object_id(Repository.model, repo)
        data = api_children(Organization.model, object_id, request, limit=limit, offset=offset)
        for d in data.get('results', []):
            oidparts = Identity.split_object_id(d['id'])
            oidparts.pop(0)
            d['organization_url'] = d['url']
            d['url'] = reverse('ui-api-organization', args=oidparts, request=request)
            d['absolute_url'] = reverse('ui-organization', args=oidparts, request=request)
            d['logo_url'] = img_url(d['id'], 'logo.png', request)
        return data

class ApiOrganization(Organization):
    
    @staticmethod
    def api_get(repo, org, request):
        oidparts = [repo,org]
        id = Identity.make_object_id(Organization.model, repo,org)
        document = docstore.get(
            settings.DOCSTORE_HOSTS, index=settings.DOCSTORE_INDEX,
            model=Organization.model, document_id=id)
        if document and (document['found'] or document['exists']):
            data = document['_source']
            data['url'] = reverse('ui-api-organization', args=oidparts, request=request)
            data['absolute_url'] = reverse('ui-organization', args=oidparts, request=request)
            data['children'] = reverse('ui-api-collections', args=oidparts, request=request)
            data['logo_url'] = img_url(id, 'logo.png', request)
            return data
        return None

    @staticmethod
    def api_children(repo, org, request, limit=DEFAULT_LIMIT, offset=0):
        object_id = Identity.make_object_id(Organization.model, repo,org)
        data = api_children(Collection.model, object_id, request, limit=limit, offset=offset)
        for d in data.get('results', []):
            cidparts = Identity.split_object_id (d['id'])
            cidparts.pop(0)
            d['url'] = reverse('ui-api-collection', args=cidparts, request=request)
            d['absolute_url'] = reverse('ui-collection', args=cidparts, request=request)
            d['img_url'] = img_url(d['id'], access_filename(d.get('signature_file')), request)
        return data

class ApiCollection(Collection):
    
    @staticmethod
    def api_get(repo, org, cid, request):
        cidparts = [repo,org,cid]
        id = Identity.make_object_id(Collection.model, repo, org, cid)
        document = docstore.get(
            settings.DOCSTORE_HOSTS, index=settings.DOCSTORE_INDEX,
            model=Collection.model, document_id=id)
        if document and (document['found'] or document['exists']):
            data = document['_source']
            data['url'] = reverse('ui-api-collection', args=cidparts, request=request)
            data['absolute_url'] = reverse('ui-collection', args=cidparts, request=request)
            data['children'] = reverse('ui-api-entities', args=cidparts, request=request)
            data['img_url'] = img_url(id, access_filename(data.get('signature_file')), request)
            data.pop('notes')
            return data
        return None

    @staticmethod
    def api_children(repo, org, cid, request, limit=DEFAULT_LIMIT, offset=0):
        cidparts = [repo,org,cid]
        object_id = Identity.make_object_id(Collection.model, repo,org,cid)
        collection_id = object_id
        data = api_children(Entity.model, object_id, request, limit=limit, offset=offset)
        for d in data.get('results', []):
            eidparts = Identity.split_object_id(d['id'])
            eidparts.pop(0)
            d['url'] = reverse('ui-api-entity', args=eidparts, request=request)
            d['absolute_url'] = reverse('ui-entity', args=eidparts, request=request)
            d['img_url'] = img_url(collection_id, access_filename(d.get('signature_file')), request)
        return data

class ApiEntity(Entity):
    
    @staticmethod
    def api_get(repo, org, cid, eid, request):
        eidparts = [repo, org, cid, eid]
        id = Identity.make_object_id(Entity.model, repo, org, cid, eid)
        collection_id = Identity.make_object_id(Collection.model, repo,org,cid)
        document = docstore.get(
            settings.DOCSTORE_HOSTS, index=settings.DOCSTORE_INDEX,
            model=Entity.model, document_id=id)
        if document and (document['found'] or document['exists']):
            data = document['_source']
            data['url'] = reverse('ui-api-entity', args=eidparts, request=request)
            data['absolute_url'] = reverse('ui-entity', args=eidparts, request=request)
            data['children'] = reverse('ui-api-files', args=eidparts, request=request)
            data['facility'] = [
                reverse('ui-api-term', args=('facility', oid), request=request)
                for oid in document['_source'].get('facility', [])
                if oid
            ]
            data['topics'] = [
                reverse('ui-api-term', args=('topics', oid), request=request)
                for oid in document['_source'].get('topics', [])
                if oid
            ]
            #persons
            data['img_url'] = img_url(collection_id, access_filename(data.get('signature_file')), request)
            data.pop('files')
            data.pop('notes')
            data.pop('parent')
            data.pop('status')
            data.pop('public')
            return data
        return None

    @staticmethod
    def api_children(repo, org, cid, eid, request, limit=DEFAULT_LIMIT, offset=0):
        eidparts = [repo,org,cid,eid]
        object_id = Identity.make_object_id(Entity.model, repo,org,cid,eid)
        collection_id = Identity.make_object_id(Collection.model, repo,org,cid)
        data = api_children(File.model, object_id, request, limit=limit, offset=offset)
        for d in data['results']:
            model,repo,org,cid,eid,role,sha1 = Identity.split_object_id(d['id'])
            fidparts = [repo,org,cid,eid,role,sha1]
            d['url'] = reverse('ui-api-file', args=fidparts, request=request)
            d['absolute_url'] = reverse('ui-file', args=fidparts, request=request)
            d['img_url'] = img_url(collection_id, d['access_rel'], request)
            if role == 'mezzanine':
                extension = os.path.splitext(d['basename_orig'])[1]
                filename = d['id'] + extension
                path_rel = os.path.join(collection_id, filename)
                url = settings.MEDIA_URL + path_rel
                d['download_url'] = url
        return data

class ApiFile(File):
    
    @staticmethod
    def api_get(repo, org, cid, eid, role, sha1, request):
        fidparts = [repo,org,cid,eid,role,sha1]
        id = Identity.make_object_id(File.model, repo,org,cid,eid,role,sha1)
        collection_id = Identity.make_object_id(Collection.model, repo,org,cid)
        document = docstore.get(
            settings.DOCSTORE_HOSTS, index=settings.DOCSTORE_INDEX,
            model=File.model, document_id=id)
        if document and (document['found'] or document['exists']):
            data = document['_source']
            data['url'] = reverse('ui-api-file', args=fidparts, request=request)
            data['absolute_url'] = reverse('ui-file', args=fidparts, request=request)
            data['img_url'] = img_url(collection_id, data.get('access_rel'), request)
            o = models.build_object(ApiFile(), id, data)
            data['download_url'] = o.download_url()
            data.pop('public')
            return data
        return None

class ApiFacet(faceting.Facet):

    def api_data(self, request):
        data = {
            'id': self.id,
            'name': self.name,
            'title': self.title,
            'description': self.description,
            'url': reverse('ui-api-facet', args=[self.id,], request=request),
            'absolute_url': reverse('ui-browse-facet', args=[self.id,], request=request),
        }
        data['terms'] = [
            {
                'id': term.id,
                'title': term.title,
                'url': reverse('ui-api-term', args=(term.facet_id, term.id), request=request),
                'absolute_url': reverse('ui-browse-term', args=(term.facet_id, term.id), request=request),
            }
            for term in self.terms()
        ]
        return data
    
    def terms(self):
        if not self._terms:
            self._terms = []
            for t in self._terms_raw:
                term = ApiTerm(facet_id=self.id, term_id=t['id'])
                self._terms.append(term)
            self._terms_raw = None
        return self._terms

class ApiTerm(faceting.Term):
        
    def api_data(self, request):
        data = {
            'id': self.id,
            'parent_id': self.parent_id,
            'parent_url': '',
            'facet_id': self.facet_id,
            'title': self.title,
            'description': self.description,
            'weight': self.weight,
            'created': self.created,
            'modified': self.modified,
            'encyclopedia': self.encyc_urls,
            'url': reverse('ui-api-term', args=(self.facet_id, self.id), request=request),
            'absolute_url': self.url(),
        }
        if self.parent_id:
            data['parent_url'] = reverse(
                'ui-api-term',
                args=[self.facet_id, self.parent_id],
                request=request)
        data['ancestors'] = [
            reverse('ui-api-term', args=[self.facet_id, tid], request=request)
            for tid in self._ancestors
        ]
        data['siblings'] = [
            reverse('ui-api-term', args=[self.facet_id, tid], request=request)
            for tid in self._siblings
        ]
        data['children'] = [
            reverse('ui-api-term', args=[self.facet_id, tid], request=request)
            for tid in self._children
        ]
        return data


# views ----------------------------------------------------------------

@api_view(['GET'])
def index(request, format=None):
    repo = 'ddr'
    data = {
        'repository': reverse('ui-api-repository', args=[repo,], request=request),
        'facets': reverse('ui-api-facets', request=request),
    }
    return Response(data)


def _list(request, data):
    path = request.META['PATH_INFO']
    if data.get('previous'):
        data['previous'] = '%s%s%s' % (host, path, data['previous'])
    if data.get('next'):
        data['next'] = '%s%s%s' % (host, path, data['next'])
    return Response(data)
    
@api_view(['GET'])
def organizations(request, repo, format=None):
    offset = int(request.GET.get('offset', 0))
    data = ApiRepository.api_children(repo, request, offset=offset)
    return _list(request, data)

@api_view(['GET'])
def collections(request, repo, org, format=None):
    offset = int(request.GET.get('offset', 0))
    data = ApiOrganization.api_children(repo, org, request, offset=offset)
    return _list(request, data)

@api_view(['GET'])
def entities(request, repo, org, cid, format=None):
    offset = int(request.GET.get('offset', 0))
    data = ApiCollection.api_children(repo, org, cid, request, offset=offset)
    return _list(request, data)

@api_view(['GET'])
def files(request, repo, org, cid, eid, format=None):
    offset = int(request.GET.get('offset', 0))
    data = ApiEntity.api_children(repo, org, cid, eid, request, offset=offset)
    return _list(request, data)


def _detail(request, data):
    """Common function for detail views.
    """
    if not data:
	return Response(status=status.HTTP_404_NOT_FOUND)
    return Response(data)

@api_view(['GET'])
def repository(request, repo, format=None):
    data = ApiRepository.api_get(repo, request)
    return _detail(request, data)

@api_view(['GET'])
def organization(request, repo, org, format=None):
    data = ApiOrganization.api_get(repo, org, request)
    return _detail(request, data)

@api_view(['GET'])
def collection(request, repo, org, cid, format=None):
    filter_if_branded(request, repo, org)
    data = ApiCollection.api_get(repo, org, cid, request)
    return _detail(request, data)

@api_view(['GET'])
def entity(request, repo, org, cid, eid, format=None):
    filter_if_branded(request, repo, org)
    data = ApiEntity.api_get(repo, org, cid, eid, request)
    return _detail(request, data)

@api_view(['GET'])
def file(request, repo, org, cid, eid, role, sha1, format=None):
    filter_if_branded(request, repo, org)
    data = ApiFile.api_get(repo, org, cid, eid, role, sha1, request)
    return _detail(request, data)

@api_view(['GET'])
def facet_index(request, format=None):
    data = {
        'topics': reverse('ui-api-facet', args=['topics',], request=request),
        'facility': reverse('ui-api-facet', args=['facility',], request=request),
    }
    return Response(data)

@api_view(['GET'])
def facet(request, facet, format=None):
    facet = ApiFacet(facet)
    data = facet.api_data(request)
    return Response(data)

@api_view(['GET'])
def term(request, facet_id, term_id, format=None):
    term = ApiTerm(facet_id=facet_id, term_id=term_id)
    data = term.api_data(request)
    return Response(data)

@api_view(['GET'])
def term_objects(request, facet_id, term_id, format=None):
    terms = {facet_id:term_id}
    fields = models.all_list_fields()
    sort = {'record_created': request.GET.get('record_created', ''),
            'record_lastmod': request.GET.get('record_lastmod', ''),}
    # filter by partner
    filters = {}
    repo,org = None,None
    if repo and org:
        filters['repo'] = repo
        filters['org'] = org
    # do the query
    results = models.cached_query(
        settings.DOCSTORE_HOSTS, settings.DOCSTORE_INDEX,
        terms=terms, filters=filters,
        fields=fields,
        sort=sort
    )
    # post-processing. See *.api_children methods in .models.py
    documents = [hit['_source'] for hit in results['hits']['hits']]
    for d in documents:
        idparts = Identity.split_object_id(d['id'])
        model = idparts.pop(0)
        collection_id = Identity.make_object_id(Collection.model, idparts[0], idparts[1], idparts[2])
        d['url'] = reverse('ui-api-%s' % model, args=idparts, request=request)
        d['absolute_url'] = reverse('ui-%s' % model, args=idparts, request=request)
        d['img_url'] = img_url(collection_id, access_filename(d['signature_file']), request)
    return Response(documents)
