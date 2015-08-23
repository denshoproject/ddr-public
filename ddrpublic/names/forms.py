from collections import OrderedDict
import logging
logger = logging.getLogger(__name__)

from django import forms
from django.conf import settings
from django.utils.datastructures import SortedDict

from namesdb.definitions import FIELD_DEFINITIONS
from names import models


def field_choices(hosts, index, fieldname):
    """
    - Get unique field values and counts (aggregations).
    - Get approved value labels from definitions.
    - Package into django.forms-friendly choices list.
    """
    # TODO get these for all fields at once? cache?
    aggregations = models.field_values(hosts, index, fieldname)
    choices_dict = FIELD_DEFINITIONS.get(fieldname, {}).get('choices', OrderedDict([]))
    choices = [
        (term, '%s (%s)' % (choices_dict.get(term, term), count))
        for term,count in aggregations
    ]
    return sorted(choices, key=lambda x: x[1])
    
def update_doc_counts(form, response):
    """Add aggregations doc_counts to field choice labels
    """
    if hasattr(response, 'get') and response.get('aggregations', None):
        aggregations = response.aggregations.to_dict()
    else:
        aggregations = {}
    agg_fieldnames = [key for key in aggregations.iterkeys()]
    form_fieldnames = [key for key in form.fields.iterkeys()]
    for fieldname in form_fieldnames:
        if fieldname in agg_fieldnames:
            field_aggs_dict = {
                d['key']: d['doc_count']
                for d in aggregations[fieldname]['buckets']
            }
            new_choices = []
            for keyword,label in form.fields[fieldname].choices:
                count = field_aggs_dict.get(keyword, None)
                if count is not None:
                    label = '%s (%s)' % (label, count)
                new_choices.append( (keyword, label) )
            form.fields[fieldname].choices = new_choices

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
        update_doc_counts(self, response)


class FlexiSearchForm(forms.Form):
    """Construct form from any combination of Record filter fields.
    """
    def __init__( self, *args, **kwargs ):
        hosts = kwargs.pop('hosts')
        index = kwargs.pop('index')
        filters = kwargs.pop('filters')
        super(FlexiSearchForm, self).__init__(*args, **kwargs)
        fields = []
        fields.append(('query', forms.CharField(required=False, max_length=255)))
        for field_name in filters:
            fobject = forms.MultipleChoiceField(
                required=False,
                choices=field_choices(hosts, index, field_name),
                widget=forms.CheckboxSelectMultiple
            )
            fields.append((field_name, fobject))
        self.fields = SortedDict(fields)
    
    def update_doc_counts(self, response):
        update_doc_counts(self, response)
