import logging
logger = logging.getLogger(__name__)

from django import forms
from django.conf import settings

class SearchForm(forms.Form):
    fulltext = forms.CharField(
        max_length=255,
        required=False,
    )
    language = forms.MultipleChoiceField(
        choices=[
            ('eng', 'English'),
            ('jpn', 'Japanese'),
            ('chi', 'Chinese'),
        ],
        required=False,
    )
    topics = forms.MultipleChoiceField(
        choices=[
            ('1', 'Immigration and citizenship'),
            ('15', 'Community activities'),
            ('29', 'Religion and churches'),
            ('36', 'Race and racism'),
            ('120', 'Activism and involvement'),
        ],
        required=False,
    )
