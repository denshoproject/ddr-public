from collections import OrderedDict
import logging
logger = logging.getLogger(__name__)

from django import forms
from django.conf import settings

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
    agg_fieldnames = [key for key in aggregations.keys()]
    form_fieldnames = [key for key in form.fields.keys()]
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
        self.fields = OrderedDict(fields)
    
    def update_doc_counts(self, response):
        update_doc_counts(self, response)


CAMP_CHOICES = [
    ('', 'All Camps'),
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

class NamesSearchForm(forms.Form):
    
    fulltext = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Search...',
            }
        )
    )
    
    filter_m_camp = forms.MultipleChoiceField(
        choices=CAMP_CHOICES,
        required=False,
    )
    
    def __init__( self, *args, **kwargs ):
        if kwargs.get('search_results'):
            self.search_results = kwargs.pop('search_results')
        super(NamesSearchForm, self).__init__(*args, **kwargs)
    
    def choice_aggs(self, aggregations):
        """Apply document counts from ES aggregations to form fields choices
        
        Choices are sorted in descending order by doc count.
        Choices with no doc counts are removed.
        
        @params aggregations: dict Aggregations section of raw ES results
        @returns: nothing, modifies form.choices in-place
        """
        aggs = docstore.aggs_dict(aggregations)
        for fieldname,choice_data in aggs.items():
            form_fieldname = 'filter_%s' % fieldname
            if self.fields.get(form_fieldname):
                
                # add score from aggregations to each choice tuple
                results_choices = []
                for keyword,label in self.fields[form_fieldname].choices:
                    # dict keys must be str, aggs keys are ints
                    if isinstance(keyword, int):
                        keyword = str(keyword)
                    # terms with zero doc_count are not in aggs so assign 0
                    count = aggs[fieldname].get(keyword, 0)
                    if count:
                        label = '%s (%s)' % (label, count)
                    results_choices.append( (keyword, label, count) )
                
                # sort doc_count desc
                self.fields[form_fieldname].choices = [
                    (keyword,label)
                    for keyword,label,count in sorted(
                        results_choices,
                        key=lambda choice: choice[2],
                        reverse=True
                    )
                    if count
                ]
