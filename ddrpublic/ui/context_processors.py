from datetime import datetime
import logging
logger = logging.getLogger(__name__)
import os

import envoy

from django.conf import settings

from ui.forms import SearchForm


def git_commit():
    """Returns the ddr-local repo's most recent Git commit.
    """
    try:
        commit = envoy.run('git log --pretty=format:"%H" -1').std_out
    except:
        commit = 'unknown'
    return commit

def sitewide(request):
    """Variables that need to be inserted into all templates.
    """
    return {
        'request': request,
        'hide_header_search': False,
        'search_form': SearchForm,
        'time': datetime.now().isoformat(),
        'pid': os.getpid(),
        'host': os.uname()[1],
        'commit': git_commit()[:7],
    }
