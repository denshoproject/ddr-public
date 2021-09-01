from collections import OrderedDict
import logging
logger = logging.getLogger(__name__)

from django import forms
from django.conf import settings
from django.core.cache import cache

from ui import docstore
from ui import search


def forms_choice_labels():
    key = 'ddrpublic:forms_choice_labels'
    timeout = 60 * 60 * 1
    cached = cache.get(key)
    if cached:
        return cached
    else:
        # sorted version of facility and topics tree as choice fields
        # {
        #     'topics-choices': [
        #         [u'topics-1', u'Immigration and citizenship'],
        #         ...
        #     ],
        #     'facility-choices: [...],
        # }
        try:
            forms_choices = docstore.Docstore().es.get(
                index='forms',
                id='forms-choices'
            )['_source']
        except docstore.NotFoundError as err:
            t = type(err)
            raise Exception(f'{t} {err} (You probably need to run "ddrindex vocabs").')
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
        forms_choice_labels = {}
        for key in forms_choices.keys():
            field = key.replace('-choices','')
            forms_choice_labels[field] = {
                c[0].split('-')[1]: c[1]
                for c in forms_choices[key]
            }
        cache.set(key, forms_choice_labels, timeout)
    return forms_choice_labels

class SearchForm(forms.Form):
    field_order = search.SEARCH_PARAM_WHITELIST
    search_results = None
    
    def __init__( self, *args, **kwargs ):
        if kwargs.get('search_results'):
            self.search_results = kwargs.pop('search_results')
        super(SearchForm, self).__init__(*args, **kwargs)
        self.fields = self.construct_form(self.search_results)

    def construct_form(self, search_results):
        fields = [
            (
                'fulltext',
                forms.CharField(
                    max_length=255,
                    required=False,
                    widget=forms.TextInput(
                        attrs={
                            'id': 'id_query',
                            'class': 'form-control',
                            'placeholder': 'Search...',
                        }
                    ),
                )
            ),
            (
                'parent',
                forms.CharField(
                    max_length=255,
                    required=False,
                    widget=forms.TextInput(
                        attrs={
                            'id': 'id_parent',
                        }
                    ),
                )
            ),
            (
                'models',
                forms.MultipleChoiceField(
                    label='Models',
                    choices=[(model,model) for model in search.SEARCH_MODELS],
                    required=False,
                )
            ),
        ]
        
        # fill in options and doc counts from aggregations
        if search_results and search_results.aggregations:
            for fieldname,aggs in search_results.aggregations.items():
                choices = []
                for item in aggs:
                    try:
                        label = forms_choice_labels()[fieldname][item['key']]
                    except:
                        label = item['key']
                    choice = (
                        item['key'],
                        '%s (%s)' % (label, item['doc_count'])
                    )
                    choices.append(choice)
                if choices:
                    fields.append((
                        fieldname,
                        forms.MultipleChoiceField(
                            label=search.SEARCH_FORM_LABELS.get(
                                fieldname, fieldname),
                            choices=choices,
                            required=False,
                        ),
                    ))
        
        # Django Form object takes an OrderedDict rather than list
        fields = OrderedDict(fields)
        return fields
