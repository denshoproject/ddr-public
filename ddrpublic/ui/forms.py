import logging
logger = logging.getLogger(__name__)

from django import forms
from django.conf import settings
from django.core.cache import cache

from ui import api

from repo_models.entity import FORMAT_CHOICES
from repo_models.entity import GENRE_CHOICES
from repo_models.entity import RIGHTS_CHOICES


def flatten(path, indent='--'):
    paths = [x for x in path.split(':')]
    # TODO replace instead of make new list
    flat = []
    for x in paths[:-1]:
        flat.append(indent)
    flat.append(paths[-1])
    return ''.join(flat)

def topics_flattened():
    oid = 'topics'
    request = None
    key = 'search:filters:%s' % oid
    cached = cache.get(key)
    if not cached:
        terms = api.ApiFacet.make_tree(
            api.ApiFacet.api_children(
                oid, request,
                sort=[('sort','asc')],
                limit=10000, raw=True
                )
            )
        choices = [
            (term['id'], term['path'])
            for term in terms
        ]
        cached = choices
        cache.set(key, cached, 15) # settings.ELASTICSEARCH_QUERY_TIMEOUT)
    return cached

TOPICS_CHOICES = topics_flattened()

def facilities():
    oid = 'facility'
    request = None
    key = 'search:filters:%s' % oid
    cached = cache.get(key)
    if not cached:
        terms = api.ApiFacet.api_children(
            oid, request,
            sort=[('title','asc')],
            limit=10000, raw=True
        )
        # for some reason ES does not sort
        terms = sorted(terms, key=lambda term: term['title'])
        cached = [
            (term['id'], term['title'])
            for term in terms
        ]
        cache.set(key, cached, 15) # settings.ELASTICSEARCH_QUERY_TIMEOUT)
    return cached

FACILITY_CHOICES = facilities()

MODELS_CHOICES = [
    ('collection', 'Collection'),
    ('entity', 'Entity'),
    ('segment', 'Segment'),
    ('file', 'File'),
    ('narrator', 'Narrator'),
    ('term', 'Topic Term'),
]
LANGUAGE_CHOICES = [
    ('eng', 'English'),
    ('jpn', 'Japanese'),
    ('chi', 'Chinese'),
]

FORM_FIELDNAMES = {
    'format': 'format_',
}

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
    
    format_ = forms.MultipleChoiceField(
        choices=FORMAT_CHOICES,
        required=False,
    )
    genre = forms.MultipleChoiceField(
        choices=GENRE_CHOICES,
        required=False,
    )
    topics = forms.MultipleChoiceField(
        choices=TOPICS_CHOICES,
        required=False,
    )
    facility = forms.MultipleChoiceField(
        choices=FACILITY_CHOICES,
        required=False,
    )
    rights = forms.MultipleChoiceField(
        choices=RIGHTS_CHOICES,
        required=False,
    )
    
    def choice_aggs(self, aggregations):
        """Apply document counts from ES aggregations to form fields choices
        """
        aggs = api.aggs_dict(aggregations)
        for fieldname,choice_data in aggs.iteritems():
            # 'format' is reserved word
            form_fieldname = FORM_FIELDNAMES.get(fieldname, fieldname)
            if self.fields.get(form_fieldname):
                results_choices = []
                for keyword,label in self.fields[form_fieldname].choices:
                    if isinstance(keyword, int):
                        keyword = str(keyword)
                    if keyword in aggs[fieldname].keys():
                        label_w_count = '%s (%s)' % (label, aggs[fieldname][keyword])
                        results_choices.append( (keyword,label_w_count) )
                self.fields[form_fieldname].choices = results_choices
