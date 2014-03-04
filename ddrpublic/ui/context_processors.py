import logging
logger = logging.getLogger(__name__)

from django.conf import settings

from ui.forms import SearchForm


def sitewide(request):
    """Variables that need to be inserted into all templates.
    """
    return {
        'request': request,
        'hide_header_search': False,
        'search_form': SearchForm,
    }
