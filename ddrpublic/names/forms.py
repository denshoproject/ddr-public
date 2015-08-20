import logging
logger = logging.getLogger(__name__)

from django import forms
from django.conf import settings

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
    dataset = forms.MultipleChoiceField(choices=[], widget=forms.CheckboxSelectMultiple)
    camps = forms.MultipleChoiceField(choices=[], widget=forms.CheckboxSelectMultiple)
    originalstate = forms.MultipleChoiceField(choices=[], widget=forms.CheckboxSelectMultiple)
    gender = forms.MultipleChoiceField(choices=[], widget=forms.CheckboxSelectMultiple)
    birthyear = forms.MultipleChoiceField(choices=[], widget=forms.CheckboxSelectMultiple)
    query = forms.CharField(max_length=255)
    
    def __init__( self, *args, **kwargs ):
        super(SearchForm, self).__init__(*args, **kwargs)
        hosts = settings.NAMESDB_DOCSTORE_HOSTS
        index = models.set_hosts_index(hosts, settings.NAMESDB_DOCSTORE_INDEX)
        self.fields['dataset'].choices = field_choices(hosts, index, 'm_dataset')
        self.fields['camps'].choices = field_choices(hosts, index, 'm_camp')
        self.fields['originalstate'].choices = field_choices(hosts, index, 'm_originalstate')
        self.fields['gender'].choices = field_choices(hosts, index, 'm_gender')
        self.fields['birthyear'].choices = field_choices(hosts, index, 'm_birthyear')
