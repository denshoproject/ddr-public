import logging
logger = logging.getLogger(__name__)

from django import forms
from django.conf import settings
from django.core.cache import cache

from ui import docstore
from ui import models

class SearchForm(forms.Form):
    
    fulltext = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(
            attrs={
                'id': 'id_query',
                'class': 'form-control',
                'placeholder': 'Search...',
            }
        )
    )
    
    filter_format = forms.MultipleChoiceField(
        choices=models.FORMAT_CHOICES,
        required=False,
    )
    filter_genre = forms.MultipleChoiceField(
        choices=models.GENRE_CHOICES,
        required=False,
    )
    filter_topics = forms.MultipleChoiceField(
        choices=models.topics_flattened(),
        required=False,
    )
    filter_facility = forms.MultipleChoiceField(
        choices=models.facilities(),
        required=False,
    )
    filter_rights = forms.MultipleChoiceField(
        choices=models.RIGHTS_CHOICES,
        required=False,
    )
    
    def choice_aggs(self, aggregations):
        """Apply document counts from ES aggregations to form fields choices
        
        Choices are sorted in descending order by doc count.
        Choices with no doc counts are removed.
        
        @params aggregations: dict Aggregations section of raw ES results
        @returns: nothing, modifies form.choices in-place
        """
        aggs = docstore.aggs_dict(aggregations)
        for fieldname,choice_data in aggs.iteritems():
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
