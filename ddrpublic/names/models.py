import json
import logging
import os
import sys

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Index
from elasticsearch_dsl import Search, F, A
from elasticsearch_dsl.query import MultiMatch
from elasticsearch_dsl.connections import connections

from django.conf import settings
from django.core.urlresolvers import reverse

from namesdb import sourcefile
from namesdb import definitions
from namesdb.models import Record, DOC_TYPE


def make_hosts(text):
    hosts = []
    for host in text.split(','):
        h,p = host.split(':')
        hosts.append( {'host':h, 'port':p} )
    return hosts

def set_hosts_index(hosts, index):
    logging.debug('Connecting %s' % hosts)
    connections.create_connection(hosts=hosts)
    logging.debug('Index %s' % index)
    return Index(index)


class Rcrd(Record):
    
    class Meta:
        index = settings.NAMESDB_DOCSTORE_INDEX
        doc_type = DOC_TYPE

    def details(self):
        """
        Returns a list of (field, value) tuples for displaying values
        """
        details = []
        for field in definitions.DATASETS[self.m_dataset]:
            try:
                label = definitions.FIELD_DEFINITIONS[field]['label']
            except:
                pass
            if not label:
                label = field
            value = getattr(self, field, None)
            if value:
                details.append((field, label, value))
        return details
    
    def absolute_url(self):
        return reverse(
            'names-detail',
            kwargs={'id': self.meta.id}
        )

def same_familyno(hosts, index, record):
    if record.m_familyno:
        response = search(
            hosts, index, filters={'m_familyno':[record.m_familyno]},
        ).execute()
        not_this_record = [
            r for r in records(response)
            if not (r.m_pseudoid == record.m_pseudoid)
        ]
        return not_this_record
    return []

def other_datasets(hosts, index, record):
    response = search(
        hosts, index, filters={'m_pseudoid':[record.m_pseudoid]},
    ).execute()
    not_this_record = [
        r for r in records(response)
        if not (r.meta.id == record.meta.id)
    ]
    return not_this_record


def field_values(hosts, index, field):
    return Record.field_values(field)


def _hitvalue(hit, field):
    """Extract list-wrapped values from their lists.
    
    TODO use the one in namesdb
    
    For some reason, Search hit objects wrap values in lists.
    returns the value inside the list.
    
    @param hit: Elasticsearch search hit object
    @param field: str field name
    @return: value
    """
    v = hit.get(field)
    vtype = type(v)
    value = None
    if hit.get(field) and isinstance(hit[field], list):
        value = hit[field][0]
    elif hit.get(field):
        value = hit[field]
    return value

def _from_hit(hit):
    """Build Record object from Elasticsearch hit
    
    TODO use the one in namesdb
    
    @param hit
    @returns: Record
    """
    htype = type(hit)
    hit_d = hit.__dict__['_d_']
    m_pseudoid = _hitvalue(hit_d, 'm_pseudoid')
    m_dataset = _hitvalue(hit_d, 'm_dataset')
    if m_dataset and m_pseudoid:
        record = Rcrd(
            meta={'id': ':'.join([m_dataset, m_pseudoid])}
        )
        for field in definitions.FIELDS_MASTER:
            setattr(record, field, _hitvalue(hit_d, field))
        record.m_dataset = m_dataset
        return record
    return None

def search(
        hosts, index, query_type='multi_match', query='', filters={},
        sort='m_pseudoid', start=0, pagesize=10
):
    """
    This function allows any combination of filters, even illogical ones
    
    @returns: Search
    """
    ## remove empty filter args
    #filter_args = {key:val for key,val in filters.iteritems() if val}
    #if not (query or filter_args):
    #    return None,[]
    s = Search().doc_type(Record)
    if filters:
        for field,values in filters.iteritems():
            if values:
                # multiple terms for a field are OR-ed
                s = s.filter(
                    'or',
                    [
                        # In the Elasticsearch DSL examples, 'tags' is the field name.
                        # ex: s.filter("term", tags="python")
                        # Our field name is a var so we have to pass in a **dict
                        F('term', **{field: value})
                        for value in values
                    ]
                )
    if query:
        s = s.query(
            query_type, query=query, fields=definitions.FIELDS_MASTER
        )
    # aggregations
    if filters:
        for field in filters.iterkeys():
            s.aggs.bucket(field, 'terms', field=field, size=1000)
    s = s.fields(definitions.FIELDS_MASTER)
    s = s.sort(sort)
    s = s[start:start+pagesize]
    return s

def records(response):
    records = []
    for hit in response:
        record = _from_hit(hit)
        if record:
            records.append(record)
    return records

class Paginator(object):
    response = None
    thispage = -1
    pagesize = -1
    query = ''
    total = -1
    count = -1
    num_pages = -1
    first = 1
    last = -1
    prev = -1
    next = -1
    start = -1
    end = -1
    range = []
    object_list = []
    labels = {'first':'First', 'prev':'Previous', 'next':'Next', 'last':'Last'}
    
    def __init__(self, response, thispage, pagesize, context, query, **kwargs):
        self.response = response
        self.thispage = thispage
        self.pagesize = pagesize
        
        self.total = response.hits.total
        self.count = self.total
        self.num_pages,mod = divmod(self.total, self.pagesize)
        if mod:
            self.num_pages = self.num_pages + 1
        self.first = 1
        self.last = self.num_pages
        self.prev = self.thispage - 1
        if self.prev <= 0:
            self.prev = None
        self.next = self.thispage + 1
        if self.next > self.num_pages:
            self.next = None
        self.start,self.end = Paginator.start_end(self.thispage, self.pagesize)
        self.object_list = records(response)
        
        range_start = self.thispage - context
        if range_start <= 1:
            range_start = 1
        range_end = self.thispage + 1 + context
        if range_end > self.num_pages:
            range_end = self.num_pages
        self.range = range(range_start, range_end)

        qs = []
        for q in query.split('&'):
            if '=' in q:
                if q.split('=')[0] != 'page':
                    qs.append(q)
        self.query = '&'.join(qs)
    
    def __repr__(self):
        return "<Paginator %s/%s %s:%s>" % (self.thispage, self.num_pages, self.start, self.end)

    @staticmethod
    def start_end(thispage, pagesize, total=10000):
        start = (thispage - 1) * pagesize
        if start < 0:
            start = 0
        if start > total:
            start  = total
        end = start + pagesize
        if end > total:
            end = total
        return start,end
        
    

def search_aggregation(hosts, index, field):
    s = Search().doc_type(Record)
    s.aggs.bucket('choices', 'terms', field=field)
    
    response = s.execute()
    records = [Record.from_hit(hit) for hit in response]
    return records
