import json
import logging
logger = logging.getLogger(__name__)
import os

from dateutil import parser
import envoy
import requests

from django.conf import settings
from django.core.urlresolvers import reverse

HOST_PORT = '%s:%s' % (settings.ELASTICSEARCH_HOST, settings.ELASTICSEARCH_PORT)

MAX_SIZE = 1000000



def _clean_dict(data):
    """Remove null or empty fields; ElasticSearch chokes on them.
    """
    if data and isinstance(data, dict):
        for key in data.keys():
            if not data[key]:
                del(data[key])



def settings():
    """Get Elasticsearch's current settings.
    
    curl -XGET 'http://localhost:9200/twitter/_settings'
    """
    url = 'http://%s/_status' % (HOST_PORT)
    r = requests.get(url)
    return json.loads(r.text)

def status():
    """Get Elasticsearch's current settings.
    
    curl -XGET 'http://localhost:9200/_status'
    """
    url = 'http://%s/_status' % (HOST_PORT)
    r = requests.get(url)
    return json.loads(r.text)



def get(index, model, id):
    """
    GET http://192.168.56.101:9200/ddr/collection/{repo}-{org}-{cid}
    """
    url = 'http://%s/%s/%s/%s' % (HOST_PORT, index, model, id)
    headers = {'content-type': 'application/json'}
    r = requests.get(url, headers=headers)
    data = json.loads(r.text)
    if data.get('exists', False):
        hits = []
        if data and data.get('_source', None) and data['_source'].get('d', None):
            hits = data['_source']['d']
        return hits
    return None

def query(index='ddr', model=None, query='', filters={}, sort='', fields='', size=MAX_SIZE):
    """Run a query, get a list of zero or more hits.
    
    curl -XGET 'http://localhost:9200/twitter/tweet/_search?q=user:kimchy&pretty=true'
    
    @param index: Name of the target index.
    @param model: Type of object ('collection', 'entity', 'file')
    @param query: User's search text
    @param filters: dict
    @param sort: str
    @param fields: str
    @param size: int Number of results to return
    @returns list of hits (dicts)
    """
    _clean_dict(filters)
    _clean_dict(sort)
    if model and query:
        url = 'http://%s/%s/%s/_search?q=%s' % (HOST_PORT, index, model, query)
    else:
        url = 'http://%s/%s/_search?q=%s' % (HOST_PORT, index, query)
    
    payload = {'size':size,}
    if fields:  payload['fields'] = fields
    if filters: payload['filter'] = {'term':filters}
    if sort:    payload['sort'  ] = sort
    logger.debug(str(payload))
    
    headers = {'content-type': 'application/json'}
    r = requests.post(url, data=json.dumps(payload), headers=headers)
    data = json.loads(r.text)
    hits = []
    if data and data.get('hits', None):
        hits = data['hits']['hits']
    return hits

def massage_hits( hits ):
    """massage the results
    """
    def rename(hit, fieldname):
        # Django templates can't display fields/attribs that start with underscore
        under = '_%s' % fieldname
        hit[fieldname] = hit.pop(under)
    for hit in hits:
        rename(hit, 'index')
        rename(hit, 'type')
        rename(hit, 'id')
        rename(hit, 'score')
        rename(hit, 'source')
        # extract certain fields for easier display
        for field in hit['source']['d'][1:]:
            if field.keys():
                if field.keys()[0] == 'id': hit['id'] = field['id']
                if field.keys()[0] == 'title': hit['title'] = field['title']
                if field.keys()[0] == 'record_created': hit['record_created'] = parser.parse(field['record_created'])
                if field.keys()[0] == 'record_lastmod': hit['record_lastmod'] = parser.parse(field['record_lastmod'])
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
