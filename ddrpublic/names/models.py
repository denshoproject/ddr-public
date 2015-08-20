import json
import logging
import os
import sys

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Index
from elasticsearch_dsl import Search, F
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
        body,records = search(
            hosts, index, filters={'m_familyno':[record.m_familyno]},
        )
        not_this_record = [r for r in records if not (r.m_pseudoid == record.m_pseudoid)]
        return not_this_record
    return []

def other_datasets(hosts, index, record):
    body,records = search(
        hosts, index, filters={'m_pseudoid':[record.m_pseudoid]},
    )
    not_this_record = [r for r in records if not (r.meta.id == record.meta.id)]
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
        sort='m_pseudoid', limit=1000
):
    """
    This function allows any combination of filters, even illogical ones
    """
    # remove empty filter args
    filters = {key:val for key,val in filters.iteritems() if val}
    if not (query or filters):
        return None,[]
    s = Search().doc_type(Record)
    if filters:
        for field,values in filters.iteritems():
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
    s = s.fields(definitions.FIELDS_MASTER)
    s = s.sort(sort)
    s = s[0:limit]
    body = s.to_dict()
    records = []
    for hit in s.execute():
        record = _from_hit(hit)
        if record:
            records.append(record)
    return body,records


def search_aggregation(hosts, index, field):
    s = Search().doc_type(Record)
    s.aggs.bucket('choices', 'terms', field=field)
    
    response = s.execute()
    records = [Record.from_hit(hit) for hit in response]
    return records
