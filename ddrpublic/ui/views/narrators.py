# stub

import logging
logger = logging.getLogger(__name__)

from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import Http404, redirect, render
from django.urls import reverse


def list(request, oid):
    return render(request, 'ui/narrators/list.html', {})

def detail(request, oid):
    return render(request, 'ui/narrators/detail.html', {})
