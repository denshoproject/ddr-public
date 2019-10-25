from collections import OrderedDict
from copy import deepcopy
import logging
logger = logging.getLogger(__name__)

from django import forms
from django.conf import settings
from django.core.cache import cache

from ui import docstore
from ui import search


# sorted version of facility and topics tree as choice fields
# {
#     'topics-choices': [
#         [u'topics-1', u'Immigration and citizenship'],
#         ...
#     ],
#     'facility-choices: [...],
# }
#FORMS_CHOICES = docstore.Docstore().es.get(
#    doc_type='forms',
#    id='forms-choices'
#)['_source']
# TODO should not be hard-coded - move to ddr-vocabs?
FORMS_CHOICES = {
    'm_camp-choices': [
        ('4-amache', 'Amache'),
        ('3-gilariver', 'Gila River'),
        ('5-heartmountain', 'Heart Mountain'),
        ('6-jerome', 'Jerome'),
        ('7-manzanar', 'Manzanar'),
        ('8-minidoka', 'Minidoka'),
        ('2-poston', 'Poston'),
        ('9-rohwer', 'Rohwer'),
        ('1-topaz', 'Topaz'),
        ('10-tulelake', 'Tule Lake'),
    ]
}
FORMS_CHOICES_DEFAULT = {
    'm_camp': [
        ('', 'All Camps'),
    ],
}

# Pretty labels for multiple choice fields
# (After initial search the choice lists come from search aggs lists
# which only include IDs and doc counts.)
# {
#     'topics': {
#         '1': u'Immigration and citizenship',
#         ...
#     },
#     'facility: {...},
# }
FORMS_CHOICE_LABELS = {}
for key in FORMS_CHOICES.keys():
    field = key.replace('-choices','')
    FORMS_CHOICE_LABELS[field] = {
        key: val
        for key,val in FORMS_CHOICES[key]
    }


class SearchForm(forms.Form):
    field_order = search.NAMESDB_SEARCH_PARAM_WHITELIST
    search_results = None
    
    def __init__( self, *args, **kwargs ):
        if kwargs.get('search_results'):
            self.search_results = kwargs.pop('search_results')
        super(SearchForm, self).__init__(*args, **kwargs)
        self.fields = self.construct_form(self.search_results)

    def construct_form(self, search_results):
        
        fields = OrderedDict()
        fields['fulltext'] = forms.CharField(
            required=False,
            widget=forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Search the Registry...',
                }
            ),
        )
        fields['m_camp'] = forms.ChoiceField(
            required=False,
            widget=forms.Select(
                attrs={
                    'class': 'form-control pointer',
                }
            ),
            choices=FORMS_CHOICES_DEFAULT['m_camp']
        )
        
        # fill in options and doc counts from aggregations
        if search_results and search_results.aggregations:
            for fieldname,aggs in search_results.aggregations.items():
                choices = deepcopy(FORMS_CHOICES_DEFAULT[fieldname])
                for item in aggs:
                    try:
                        label = FORMS_CHOICE_LABELS[fieldname][item['key']]
                    except:
                        label = item['key']
                    choice = (
                        item['key'],
                        '%s (%s)' % (label, item['doc_count'])
                    )
                    choices.append(choice)
                fields[fieldname].choices = choices
        
        return fields
