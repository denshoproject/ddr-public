import json
import logging
import os
import sys

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Index
from elasticsearch_dsl import Search
from elasticsearch_dsl.query import MultiMatch
from elasticsearch_dsl.connections import connections

from namesdb import sourcefile
from namesdb import definitions
from namesdb.models import Record


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


def field_values(hosts, index, field):
    return Record.field_values(field)

def search_multimatch(hosts, index, query, sort='m_pseudoid'):
    logging.info('query: "%s"' % query)
    
    s = Search().doc_type(Record)
    s = s.fields(definitions.FIELDS_MASTER)
    s = s.sort(sort)
    s = s.query(
        'multi_match', query=query, fields=definitions.FIELDS_MASTER
    )[0:10000]
    response = s.execute()
    records = [Record.from_hit(hit) for hit in response]
    return records

def search_aggregation(hosts, index, field):
    s = Search().doc_type(Record)
    s.aggs.bucket('choices', 'terms', field=field)
    
    response = s.execute()
    records = [Record.from_hit(hit) for hit in response]
    return records
