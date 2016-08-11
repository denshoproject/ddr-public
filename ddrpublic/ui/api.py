import os

from django.conf import settings
from django.http import HttpResponseRedirect

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse

from DDR import docstore
from ui.identifier import Identifier, CHILDREN, CHILDREN_ALL
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

def pop_field(obj, fieldname):
    """Safely remove fields from objects.
    
    @param obj: dict
    @param fieldname: str
    """
    if obj.get(fieldname):
        obj.pop(fieldname)


# classes --------------------------------------------------------------

class ApiRepository(Repository):
    
    @staticmethod
    def api_get(repo, request):
        i = Identifier(parts={'model':'repository', 'repo':repo})
        idparts = [x for x in i.parts.itervalues()]
        document = docstore.get(
            settings.DOCSTORE_HOSTS, index=settings.DOCSTORE_INDEX,
            model=i.model, document_id=i.id)
        if document and (document['found'] or document['exists']):
            d = document['_source']
            d['repository_url'] = d['url']
            d['url'] = reverse('ui-api-repository', args=idparts, request=request)
            d['absolute_url'] = reverse('ui-repo', args=idparts, request=request)
            d['children'] = reverse('ui-api-organizations', args=idparts, request=request)
            return d
        return None

    @staticmethod
    def api_children(repo, request, limit=DEFAULT_LIMIT, offset=0):
        i = Identifier(parts={'model':'repository', 'repo':repo})
        data = api_children(CHILDREN_ALL[i.model], i.id, request, limit=limit, offset=offset)
        for d in data.get('results', []):
            oi = Identifier(d['id'])
            oidparts = [x for x in oi.parts.itervalues()]
            d['organization_url'] = d['url']
            d['url'] = reverse('ui-api-organization', args=oidparts, request=request)
            d['absolute_url'] = reverse('ui-organization', args=oidparts, request=request)
            d['logo_url'] = img_url(d['id'], 'logo.png', request)
        return data

class ApiOrganization(Organization):
    
    @staticmethod
    def api_get(repo, org, request):
        i = Identifier(parts={'model':'organization', 'repo':repo, 'org':org})
        idparts = [x for x in i.parts.itervalues()]
        document = docstore.get(
            settings.DOCSTORE_HOSTS, index=settings.DOCSTORE_INDEX,
            model=i.model, document_id=i.id)
        if document and (document['found'] or document['exists']):
            data = document['_source']
            data['url'] = reverse('ui-api-organization', args=idparts, request=request)
            data['absolute_url'] = reverse('ui-organization', args=idparts, request=request)
            data['children'] = reverse('ui-api-collections', args=idparts, request=request)
            data['logo_url'] = img_url(i.id, 'logo.png', request)
            return data
        return None

    @staticmethod
    def api_children(repo, org, request, limit=DEFAULT_LIMIT, offset=0):
        i = Identifier(parts={'model':'organization', 'repo':repo, 'org':org})
        data = api_children(CHILDREN_ALL[i.model], i.id, request, limit=limit, offset=offset)
        for d in data.get('results', []):
            ci = Identifier(d['id'])
            cidparts = [x for x in ci.parts.itervalues()]
            d['url'] = reverse('ui-api-collection', args=cidparts, request=request)
            d['absolute_url'] = reverse('ui-collection', args=cidparts, request=request)
            d['img_url'] = img_url(d['id'], access_filename(d.get('signature_id')), request)
        return data

class ApiCollection(Collection):
    
    @staticmethod
    def api_get(repo, org, cid, request):
        i = Identifier(parts={'model':'collection', 'repo':repo, 'org':org, 'cid':cid})
        idparts = [x for x in i.parts.itervalues()]
        document = docstore.get(
            settings.DOCSTORE_HOSTS, index=settings.DOCSTORE_INDEX,
            model=i.model, document_id=i.id)
        if document and (document['found'] or document['exists']):
            data = document['_source']
            data['url'] = reverse('ui-api-collection', args=idparts, request=request)
            data['absolute_url'] = reverse('ui-collection', args=idparts, request=request)
            data['children'] = reverse('ui-api-entities', args=idparts, request=request)
            data['img_path'] = os.path.join(i.id, access_filename(data.get('signature_id')))
            data['img_url'] = img_url(i.id, access_filename(data.get('signature_id')), request)
            pop_field(data, 'notes')
            return data
        return None

    @staticmethod
    def api_children(repo, org, cid, request, limit=DEFAULT_LIMIT, offset=0):
        i = Identifier(parts={'model':'collection', 'repo':repo, 'org':org, 'cid':cid})
        data = api_children(CHILDREN_ALL[i.model], i.id, request, limit=limit, offset=offset)
        for d in data.get('results', []):
            ei = Identifier(d['id'])
            eidparts = [x for x in ei.parts.itervalues()]
            d['url'] = reverse('ui-api-entity', args=eidparts, request=request)
            d['absolute_url'] = reverse('ui-entity', args=eidparts, request=request)
            d['img_path'] = os.path.join(i.id, access_filename(d.get('signature_id')))
            d['img_url'] = img_url(i.id, access_filename(d.get('signature_id')), request)
        return data

class ApiEntity(Entity):
    
    @staticmethod
    def api_get(repo, org, cid, eid, request):
        i = Identifier(parts={'model':'entity', 'repo':repo, 'org':org, 'cid':cid, 'eid':eid})
        idparts = [x for x in i.parts.itervalues()]
        document = docstore.get(
            settings.DOCSTORE_HOSTS, index=settings.DOCSTORE_INDEX,
            model=i.model, document_id=i.id)
        if document and (document['found'] or document['exists']):
            data = document['_source']
            data['url'] = reverse('ui-api-entity', args=idparts, request=request)
            data['absolute_url'] = reverse('ui-entity', args=idparts, request=request)
            data['children'] = reverse('ui-api-files', args=idparts, request=request)
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
            if data.get('access_rel'):
                data['img_path'] = os.path.join(collection_id, d['access_rel'])
                data['img_url'] = img_url(collection_id, d['access_rel'], request)
            else:
                data['img_path'] = None
                data['img_url'] = None
            pop_field(data, 'files')
            pop_field(data, 'notes')
            pop_field(data, 'parent')
            pop_field(data, 'status')
            pop_field(data, 'public')
            return data
        return None

    @staticmethod
    def api_children(repo, org, cid, eid, request, limit=DEFAULT_LIMIT, offset=0):
        i = Identifier(parts={'model':'entity', 'repo':repo, 'org':org, 'cid':cid, 'eid':eid})
        data = api_children(CHILDREN[i.model], i.id, request, limit=limit, offset=offset)
        for d in data['results']:
            fi = Identifier(d['id'])
            collection_id = fi.collection_id()
            fidparts = [x for x in fi.parts.itervalues()]
            d['url'] = reverse('ui-api-file', args=fidparts, request=request)
            d['absolute_url'] = reverse('ui-file', args=fidparts, request=request)
            if d.get('access_rel'):
                d['img_path'] = os.path.join(collection_id, d['access_rel'])
                d['img_url'] = img_url(collection_id, d['access_rel'], request)
            else:
                d['img_path'] = None
                d['img_url'] = None
            if fi.parts['role'] == 'mezzanine':
                extension = os.path.splitext(d['basename_orig'])[1]
                filename = d['id'] + extension
                path_rel = os.path.join(collection_id, filename)
                url = settings.MEDIA_URL + path_rel
                d['download_url'] = url
        return data

class ApiFile(File):
    
    @staticmethod
    def api_get(repo, org, cid, eid, role, sha1, request):
        i = Identifier(parts={'model':'file', 'repo':repo, 'org':org, 'cid':cid, 'eid':eid, 'role':role, 'sha1':sha1})
        idparts = [x for x in i.parts.itervalues()]
        collection_id = i.collection_id()
        document = docstore.get(
            settings.DOCSTORE_HOSTS, index=settings.DOCSTORE_INDEX,
            model=i.model, document_id=i.id)
        if document and (document['found'] or document['exists']):
            data = document['_source']
            data['url'] = reverse('ui-api-file', args=idparts, request=request)
            data['absolute_url'] = reverse('ui-file', args=idparts, request=request)
            if data.get('access_rel'):
                data['img_path'] = os.path.join(collection_id, data.get('access_rel'))
                data['img_url'] = img_url(collection_id, data.get('access_rel'), request)
            else:
                data['img_path'] = None
                data['img_url'] = None
            #def build_object(identifier, source, rename={} ):
            o = models.build_object(i, data)
            data['download_url'] = o.download_url()
            pop_field(data, 'public')
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
        data['objects'] = [
            reverse('ui-api-term-objects', args=[self.facet_id, tid], request=request)
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
    host = request.META['HTTP_HOST']
    path = request.META['PATH_INFO']
    if data.get('previous'):
        data['previous'] = 'http://%s%s%s' % (host, path, data['previous'])
    if data.get('next'):
        data['next'] = 'http://%s%s%s' % (host, path, data['next'])
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
    """
    http://DOMAIN/api/0.1/facet/{facet_id}/{term_id}/objects/?{internal=1}&{limit=5}
    """
    terms = {facet_id:term_id}
    fields = models.all_list_fields()
    sort = {'record_created': request.GET.get('record_created', ''),
            'record_lastmod': request.GET.get('record_lastmod', ''),}
    limit = request.GET.get('limit', 100)
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
        sort=sort,
        size=limit,
    )
    # post-processing. See *.api_children methods in .models.py
    documents = [hit['_source'] for hit in results['hits']['hits']]
    for d in documents:
        i = Identifier(d['id'])
        idparts = [x for x in i.parts.itervalues()]
        collection_id = i.collection_id()
        d['url'] = reverse('ui-api-%s' % i.model, args=idparts, request=request)
        d['absolute_url'] = reverse('ui-%s' % i.model, args=idparts, request=request)
        d['img_url'] = img_url(collection_id, access_filename(d['signature_id']), request)
        d['img_path'] = os.path.join(collection_id, access_filename(d['signature_id']))
    return Response(documents)
