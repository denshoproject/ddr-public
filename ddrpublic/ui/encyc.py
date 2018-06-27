"""
Links between ddrpublic and encyc-front
"""
import json
from urllib.parse import urlparse, urlunsplit

import requests

from django.conf import settings
from django.core.cache import cache

API_BASE = '/api/0.1'
API_ARTICLES_BASE = '/api/0.1/articles'
URLS_TITLES_CACHE_KEY = 'encyc:urls-titles'
URLS_TITLES_CACHE_TIMEOUT = 60 * 60 * 12


"""
[
    {
        "url": "http://encyclopedia.densho.org/api/0.1/articles/522nd%20Field%20Artillery%20Battalion/",
        "title": "522nd Field Artillery Battalion"
    },
    {
        "url": "http://encyclopedia.densho.org/api/0.1/articles/A%20Circle%20of%20Freedom:%20Lost%20and%20Restored%20(exhibition)/",
        "title": "A Circle of Freedom: Lost and Restored (exhibition)"
    },
]
"""

def map_encycurls_titles(rawdata):
    """Map various encyc URLs to article titles.
    
    @param rawdata: list
    @returns: dict
    """
    data = {}
    for item in rawdata:
        api_url = item['url']
        u = urlparse(api_url)
        article_path = u.path.replace(API_ARTICLES_BASE, '')
        article_url = urlunsplit(
            (u.scheme, u.netloc, article_path, '', '')
        )
        data[api_url] = item['title']
        data[article_url] = item['title']
        data[article_path] = item['title']
    return data
    
def article_urls_titles():
    """Get article URLs-to-titles dict from encyc-front and cache
    """
    data = {}
    key = URLS_TITLES_CACHE_KEY
    cached = cache.get(key)
    if not cached:
        url = '%s/api/0.1/articles/' % settings.ENCYC_BASE
        try:
            r = requests.get(url, timeout=10)
        except Timeout:
            r = None
        if r and r.status_code == 200:
            urls_titles = map_encycurls_titles(json.loads(r.text))
            cached = urls_titles
            cache.set(key, cached, URLS_TITLES_CACHE_TIMEOUT)
    return cached

def article_url_title(uri):
    """Get article title for URI, or fake it.
    
    Try to get title from encyc.article_urls_titles.
    If that fails (timeout?) unquote the URI and remove slashes.
    
    @param uri: URL of the article minus the domain name
    @returns: str title
    """
    
    return {
        'url': '%s%s' % (settings.ENCYC_BASE, uri),
        'title': article_urls_titles().get(uri),
    }
