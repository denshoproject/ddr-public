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
    # approved labels
    choices_dict = {
        key: val
        for key,val in FIELD_DEFINITIONS.get(field, {}).get('choices', [])
        if FIELD_DEFINITIONS.get(field) and FIELD_DEFINITIONS[field].get('choices')
    }
    # unique values and counts
    aggregations = models.field_values(hosts, index, field)
    # format
    choices = []
    for term,count in aggregations:
        if choices_dict.get(term):
            # approved terms have initial space so they sort first
            choice = (term, ' %s (%s)' % (choices_dict[term], count))
        else:
            choice = (term, '%s (%s)' % (term, count))
        choices.append(choice)
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
