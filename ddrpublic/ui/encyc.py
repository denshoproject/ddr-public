"""
Links between ddrpublic and encyc-front
"""
import json
import urllib

import requests

from django.conf import settings
from django.core.cache import cache

URLS_TITLES_CACHE_KEY = 'encyc:urls-titles'
URLS_TITLES_CACHE_TIMEOUT = 60 * 15


def article_urls_titles():
    """Get article URLs-to-titles dict from encyc-front and cache
    """
    key = URLS_TITLES_CACHE_KEY
    cached = cache.get(key)
    if not cached:
        data = {}
        url = '%s/api/0.1/urls-titles/' % settings.ENCYC_BASE
        #r = requests.get(url, timeout=10)
        try:
            r = requests.get(url, timeout=10)
        except Timeout:
            r = None
        if r and r.status_code == 200:
            text = r.text
            data = json.loads(text)
        cached = data
        cache.set(key, cached, URLS_TITLES_CACHE_TIMEOUT)
    return cached

def article_title(uri):
    """Get article title for URI, or fake it.
    
    Try to get title from encyc.article_urls_titles.
    If that fails (timeout?) unquote the URI and remove slashes.
    
    @param uri: URL of the article minus the domain name
    @returns: str title
    """
    try:
        assert False
        title = article_urls_titles()[uri]
    except:
        title = urllib.unquote(uri).replace('/', '')
    return title
