import logging
logger = logging.getLogger(__name__)

from django import forms
from django.conf import settings
from django.utils.datastructures import SortedDict

from namesdb.definitions import FIELD_DEFINITIONS
from names import models


def field_choices(hosts, index, field):
    """
    - Get unique field values and counts (aggregations).
    - Get approved value labels from definitions.
    - Package into django.forms-friendly choices list.
    """
    # TODO get these for all fields at once? cache?
    aggregations = models.field_values(hosts, index, field)
    choices_dict = {
        key: val
        for key,val in FIELD_DEFINITIONS.get(field, {}).get('choices', [])
        if FIELD_DEFINITIONS.get(field) and FIELD_DEFINITIONS[field].get('choices')
    }
    choices = [
        (term, choices_dict.get(term, term))
        for term,count in aggregations
    ]
    return sorted(choices, key=lambda x: x[1])

class SearchForm(forms.Form):
    m_dataset = forms.MultipleChoiceField(required=False, choices=[], widget=forms.CheckboxSelectMultiple)
    m_camp = forms.MultipleChoiceField(required=False, choices=[], widget=forms.CheckboxSelectMultiple)
    m_originalstate = forms.MultipleChoiceField(required=False, choices=[], widget=forms.CheckboxSelectMultiple)
    m_gender = forms.MultipleChoiceField(required=False, choices=[], widget=forms.CheckboxSelectMultiple)
    m_birthyear = forms.MultipleChoiceField(required=False, choices=[], widget=forms.CheckboxSelectMultiple)
    query = forms.CharField(required=False, max_length=255)
    
    def __init__( self, *args, **kwargs ):
        hosts = kwargs.pop('hosts')
        index = kwargs.pop('index')
        super(SearchForm, self).__init__(*args, **kwargs)
        self.fields['m_dataset'].choices = field_choices(hosts, index, 'm_dataset')
        self.fields['m_camp'].choices = field_choices(hosts, index, 'm_camp')
        self.fields['m_originalstate'].choices = field_choices(hosts, index, 'm_originalstate')
        self.fields['m_gender'].choices = field_choices(hosts, index, 'm_gender')
        self.fields['m_birthyear'].choices = field_choices(hosts, index, 'm_birthyear')
    
    def update_doc_counts(self, response):
        """Add aggregations doc_counts to field choice labels
        """
        aggregations = response.aggregations.to_dict()
        agg_fieldnames = [key for key in aggregations.iterkeys()]
        form_fieldnames = [key for key in self.fields.iterkeys()]
        for fieldname in form_fieldnames:
            if fieldname in agg_fieldnames:
                field_aggs_dict = {
                    d['key']: d['doc_count']
                    for d in aggregations[fieldname]['buckets']
                }
                new_choices = []
                for keyword,label in self.fields[fieldname].choices:
                    count = field_aggs_dict.get(keyword, None)
                    if count is not None:
                        label = '%s (%s)' % (label, count)
                    new_choices.append( (keyword, label) )
                self.fields[fieldname].choices = new_choices

def construct_form(hosts, index, filters):
    fields = []
    fields.append(('query', forms.CharField(required=False, max_length=255)))
    for field_name in filters:
        fobject = forms.MultipleChoiceField(
            required=False,
            choices=field_choices(hosts, index, field_name),
            widget=forms.CheckboxSelectMultiple
        )
        fields.append((field_name, fobject))
    fields = SortedDict(fields)
    return fields

class FlexiSearchForm(forms.Form):
    """Construct form from any combination of Record filter fields.
    """
    def __init__( self, *args, **kwargs ):
        hosts = kwargs.pop('hosts')
        index = kwargs.pop('index')
        filters = kwargs.pop('filters')
        super(FlexiSearchForm, self).__init__(*args, **kwargs)
        self.fields = construct_form(hosts, index, filters)
