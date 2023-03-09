from collections import OrderedDict
import datetime
import json
import logging
import os
import sys

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q

from django.conf import settings
from django.core.cache import cache

from rest_framework.exceptions import NotFound
from rest_framework.reverse import reverse

from elastictools import docstore
from elastictools import search
from namesdb import sourcefile
from namesdb import definitions
from namesdb.models import Record, DOC_TYPE

# set default hosts and index
DOCSTORE = docstore.Docstore('ddr', settings.DOCSTORE_HOST, settings)

NAME_RECORD_DOCTYPE = 'namesdbrecord'

SEARCH_RETURN_FIELDS = [
]

SEARCH_PARAM_WHITELIST = [
    'fulltext',
    'model',
    'models',
    'parent',
    'id', '_id', 'meta.id', 'm_dataset', 'm_pseudoid', 'm_camp', 'm_familyno',
]
SEARCH_MODELS = ['namesdbrecord']
SEARCH_INCLUDE_FIELDS = definitions.SEARCH_FIELDS
SEARCH_NESTED_FIELDS = []
SEARCH_AGG_FIELDS = {'m_camp': 'm_camp'}

DATASET_LABELS = definitions.FIELD_DEFINITIONS['m_dataset']['choices']
CAMP_LABELS = {
    '4-amache': 'Amache',
    '3-gilariver': 'Gila River',
    '5-heartmountain': 'Heart Mountain',
    '6-jerome': 'Jerome',
    '7-manzanar': 'Manzanar',
    '8-minidoka': 'Minidoka',
    '2-poston': 'Poston',
    '9-rohwer': 'Rohwer',
    '1-topaz': 'Topaz',
    '10-tulelake': 'Tule Lake',
}
STATES = {
    'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas',
    'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut',
    'DE': 'Delaware', 'DC': 'District of Columbia', 'FL': 'Florida',
    'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho', 'IL': 'Illinois',
    'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas', 'KY': 'Kentucky',
    'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland', 'MA': 'Massachusetts',
    'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi', 'MO': 'Missouri',
    'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada', 'NH': 'New Hampshire',
    'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York',
    'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio',
    'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island',
    'SC': 'South Carolina', 'SD': 'South Dakota', 'TN': 'Tennessee',
    'TX': 'Texas', 'UT': 'Utah', 'VT': 'Vermont', 'VA': 'Virginia',
    'WA': 'Washington', 'WV': 'West Virginia', 'WI': 'Wisconsin',
    'WY': 'Wyoming',
}

def format_name_record(document, request, listitem=False):
    """
    @param document: dict Raw results from docstore.Docstore().es.get
    @param request: Django HttpRequest
    @param listitem: bool
    @returns: OrderedDict
    """
    model = NAME_RECORD_DOCTYPE
    if hasattr(document, 'meta'):
        oid = document.meta.id
        document = document.to_dict()
    if document.get('_source'):
        oid = document['_id']
        document = document['_source']
    elif document.get('m_dataset') and document.get('m_pseudoid'):
        oid = ':'.join([document.get('m_dataset'), document.get('m_pseudoid')])
    else:
        oid = document.pop('id')
    
    d = OrderedDict()
    d['id'] = oid
    # links
    d['links'] = OrderedDict()
    d['links']['html'] = reverse(
        'names-detail', args=[oid], request=request
    )
    d['links']['json'] = reverse(
        'names-api-name', args=[oid], request=request
    )
    # everything else
    if listitem:
        for key in definitions.SEARCH_FIELDS:
            if document.get(key):
                d[key] = document[key]
    else:
        for key in definitions.FIELD_DEFINITIONS_NAMES:
            if document.get(key):
                d[key] = document[key]
    # pretty versions of certain values
    if d.get('m_camp'):
        d['m_camp_label'] = CAMP_LABELS.get(d['m_camp'])
    if d.get('m_originalstate'):
        d['m_originalstate_label'] = STATES.get(d['m_originalstate'])
    if d.get('m_dataset'):
        d['m_dataset_label'] = DATASET_LABELS.get(d['m_dataset'])
    return d

FORMATTERS = {
    'namesdbrecord': format_name_record,
}


class NameRecord(object):

    @staticmethod
    def make_id(document):
        return ':'.join([
            document['m_dataset'], document['m_pseudoid']
        ])

    @staticmethod
    def get(oid, request):
        """Returns document as OrderedDict of fields:values
        
        @param oid: str Object ID
        @param request: Django HttpRequest
        @returns: OrderedDict
        """
        document = DOCSTORE.es.get(
            index=NAME_RECORD_DOCTYPE,
            id=oid
        )
        if not document:
            raise NotFound()
        data = format_name_record(document, request)
        HIDDEN_FIELDS = []
        for field in HIDDEN_FIELDS:
            pop_field(data, field)
        return data

    @staticmethod
    def fields_enriched(record, label=False, description=False, list_fields=[]):
        """Returns an OrderedDict of (field, value) tuples for displaying values
        
        # list fields and values in order
        >>> for field in record.details.values:
        >>>     print(field.label, field.value)
        
        # access individual values
        >>> record.details.m_dataset.label
        >>> record.details.m_dataset.value
        
        @param record: OrderedDict (not an elasticsearch_dsl..Hit)
        @param label: boolean Get pretty label for fields.
        @param description: boolean Get pretty description for fields. boolean
        @param list_fields: list If non-blank get pretty values for these fields.
        @returns: OrderedDict
        """
        details = []
        fieldnames  = definitions.DATASETS[record['m_dataset']]
        # some datasets do not have the 'm_dataset' field
        if 'm_dataset' not in fieldnames:
             fieldnames.insert(0, 'm_dataset')
        for fieldname in fieldnames:
            value = record.get(fieldname)
            field_def = definitions.FIELD_DEFINITIONS.get(fieldname, {})
            display = field_def.get('display', None)
            if value and display:
                # display datetimes as dates
                if isinstance(value, datetime.datetime):
                    value = value.date()
                data = {
                    'field': fieldname,
                    'label': fieldname,
                    'description': '',
                    'value_raw': value,
                    'value': value,
                }
                if (not list_fields) or (fieldname in list_fields):
                    # get pretty value from FIELD_DEFINITIONS
                    choices = field_def.get('choices', {})
                    if choices and choices.get(value, None):
                        data['value'] = choices[value]
                if label:
                    data['label'] = field_def.get('label', fieldname)
                if description:
                    data['description'] = field_def.get('description', '')
                item = (fieldname, data)
                details.append(item)
        return OrderedDict(details)

    @staticmethod
    def other_datasets(record):
        """Lists occurances of the m_pseudoid in other datasets
        
        @param hosts: list settings.DOCSTORE_HOST
        @returns: list of Records
        """
        #response = search(
        #    hosts, index, filters={'m_pseudoid':[record.m_pseudoid]},
        #).execute()
        #not_this_record = [
        #    r for r in records(response)
        #    if not (r.meta.id == record.meta.id)
        #]
        #return not_this_record
        params = {'m_pseudoid': record_m_pseudoid_nospaces}
        searcher = search.Searcher(DOCSTORE)
        searcher.prepare(
            params=params,
            params_whitelist=SEARCH_PARAM_WHITELIST,
            search_models=SEARCH_MODELS,
            sort=[],
            fields=SEARCH_INCLUDE_FIELDS,
            fields_nested=SEARCH_NESTED_FIELDS,
            fields_agg=SEARCH_AGG_FIELDS,
            wildcards=False,
        )
        results = searcher.execute(limit=10000, offset=0)
        not_this_record = [
            r for r in results.objects
            if not (NameRecord.make_id(r) == record['id'])
        ]
        return not_this_record

    @staticmethod
    def same_familyno(record, request):
        """Lists other Records with the same m_familyno.
        
        @returns: list of Records
        """
        if record.get('m_familyno'):
            familyno = record['m_familyno']
        elif record.get('m_altfamilyid'):
            familyno = record['m_altfamilyid']
        else:
            return []
        params = {'m_familyno': familyno}
        searcher = search.Searcher(DOCSTORE)
        searcher.prepare(
            params=params,
            params_whitelist=SEARCH_PARAM_WHITELIST,
            search_models=SEARCH_MODELS,
            sort=[],
            fields=SEARCH_INCLUDE_FIELDS,
            fields_nested=SEARCH_NESTED_FIELDS,
            fields_agg=SEARCH_AGG_FIELDS,
            wildcards=False,
        )
        results = searcher.execute(limit=10000, offset=0)
        not_this_record = [
            format_name_record(r, request)
            for r in results.objects
            if not (NameRecord.make_id(r) == record['id'])
        ]
        return not_this_record
