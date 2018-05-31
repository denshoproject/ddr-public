# stub

import logging
logger = logging.getLogger(__name__)

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import Http404, redirect, render


def list(request, oid):
    return render(request, 'ui/narrators/list.html', {})

def detail(request, oid):
    return render(request, 'ui/narrators/detail.html', {})
