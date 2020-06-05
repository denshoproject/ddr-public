# TODO could much of this code be replaced by DDR.vocab?

from collections import defaultdict
import re
import urllib

from django.conf import settings
from django.core.cache import cache
from django.urls import reverse

from ui import docstore

FACETS_LIST_CACHE_KEY = 'facets:list'
FACETS_FACET_CACHE_KEY = 'facets:{name}'
FACETS_TERM_CACHE_KEY = 'facets:{facet_id}:{term_id}'


def facets_list():
    """Returns a list of facets in alphabetical order, with URLs
    """
    key = FACETS_LIST_CACHE_KEY
    cached = cache.get(key)
    if not cached:
        facets_list = []
        ds = docstore.Docstore()
        facets = ds.get_facets()
        for name in facets:
            data = ds.get(model='facet', document_id=name)
            if not data:
                raise Exception('"%s" facet data missing--were facets indexed?' % name)
            f = data['_source']
            f['name'] = name
            f['url'] = reverse('ui-browse-facet', args=[name])
            facets_list.append(f)
        cached = facets_list
        cache.set(key, cached, settings.ELASTICSEARCH_FACETS_TIMEOUT)
    return cached

def get_facet(name):
    """
    TODO Rethink this: we are getting all the terms and then throwing them away
         except for the one we want; just get the one we want.
    
    @param facet: str
    """
    key = FACETS_FACET_CACHE_KEY.format(name=name)
    cached = cache.get(key)
    if not cached:
        for f in facets_list():
            if f['name'] == name:
                if f['name'] in ['facility', 'topics']:
                    f['terms'] = sorted(f['terms'], key=lambda x: x['title'])
                cached = f
                cache.set(key, cached, settings.ELASTICSEARCH_FACETS_TIMEOUT)
    return cached

def get_facet_term( facet_id, term_id ):
    """
    @param facet: str
    @param term_id: int
    """
    key = FACETS_TERM_CACHE_KEY.format(facet_id=facet_id, term_id=term_id)
    cached = cache.get(key)
    if not cached:
        facet = get_facet(facet_id)
        for t in facet['terms']:
            if int(t['id']) == int(term_id):
                cached = t
        if cached:
            cache.set(key, cached, settings.ELASTICSEARCH_FACETS_TIMEOUT)
    return cached

def get_term_children(facet_id, term_dict):
    """
    @param term_dict: dict NOT a Term object!
    """
    assert isinstance(term_dict, dict)
    if not term_dict.get('_children'):
        children = []
        facet = get_facet(facet_id)
        for t in facet['terms']:
            if t.get('parent_id',None) \
            and (int(t['parent_id']) == int(term_dict['id'])):
                children.append(t)
    return children


class Facet(object):
    id = None
    name = None
    title = None
    description = None
    url = None
    _terms_raw = None
    _terms = None
    
    def __init__(self, id=None):
        """
        @param id: str
        """
        if id:
            self.id = id
            facet = get_facet(id)
            if facet:
                self.name = facet.get('name', None)
                self.title = facet.get('title', None)
                self.description = facet.get('description', None)
                self.url = facet.get('url', None)
                self._terms_raw = facet.get('terms', None)
    
    def __repr__(self):
        return "<Facet [%s] %s>" % (self.id, self.title)
    
    def url(self):
        return reverse('ui-browse-facet', args=[self.id,])
    
    def terms(self):
        if not self._terms:
            self._terms = []
            for t in self._terms_raw:
                term = Term(facet_id=self.id, term_id=t['id'])
                self._terms.append(term)
            self._terms_raw = None
        return self._terms
    
    def term_ancestors(self):
        """List of terms that have no parents.
        """
        ancestors = []
        for term in self.terms():
            if not term.parent():
                ancestors.append(term)
        ancestors.sort()
        return ancestors
    
    def tree(self):
        """Tree of terms under this term
        
        https://gist.github.com/hrldcpr/2012250
        """
        def tree():
            return defaultdict(tree)
        
        def add(t, path):
            for node in path:
                t = t[node]
        
        lines = []
        def prnt(t, depth=0):
            """return list of (term, depth) tuples
            
            variation on ptr() from the gist
            """
            for k in sorted(t.keys()):
                term = Term(self.id, int(k))
                #print("%s %2d %s" % ("".join(depth * indent), depth, term.title))
                term.depth = depth
                lines.append(term)
                depth += 1
                prnt(t[k], depth)
                depth -= 1
        
        terms = tree()
        for term in self.terms():
            path = [int(t.id) for t in term.path()]
            add(terms, path)
        prnt(terms)
        return lines


class Term(object):
    id = None
    parent_id = None
    _ancestors = []
    _siblings = []
    _children = []
    _path = None
    facet_id = None
    _title = None
    title = None
    description = None
    weight = None
    created = None
    modified = None
    encyc_urls = []
    _encyc_articles = []
    _facet = None
    
    def __init__(self, facet_id=None, term_id=None):
        """
        @param facet: str
        @param term_id: int
        """
        if facet_id and term_id:
            self.id = term_id
            self.facet_id = facet_id
            term = get_facet_term(facet_id, term_id)
            if term:
                self.parent_id = term.get('parent_id', None)
                self._ancestors = term.get('ancestors', [])
                self._siblings = term.get('siblings', [])
                self._children = term.get('children', [])
                self._title = term.get('_title', None)
                self.title = term.get('title', term.get('_title', None))
                self.description = term.get('description', None)
                self.weight = term.get('weight', None)
                self.created = term.get('created', None)
                self.modified = term.get('modified', None)
                self.encyc_urls = term.get('encyc_urls', [])
    
    def __repr__(self):
        if self.title:
            return "<Term [%s] %s>" % (self.id, self.title)
        return "<Term [%s] %s>" % (self.id, self._title)
    
    def url(self):
        return reverse('ui-browse-term', args=(self.facet_id, self.id))
    
    def facet(self):
        return Facet(self.facet_id)
    
    def path(self):
        """
        TODO refactor to use term._ancestors
        """
        if not self._path:
            term = self
            self._path = [term]
            while term.parent():
                term = term.parent()
                self._path.append(term)
            self._path.reverse()
        return self._path
    
    def ancestor(self):
        if self._ancestors:
            return Term(facet_id=self.facet_id, term_id=self._ancestors[0])
        return None
    
    def parent(self):
        if self.parent_id:
            return Term(facet_id=self.facet_id, term_id=self.parent_id)
        return None
    
    def children(self):
        terms = []
        for tid in self._children:
            term = Term(facet_id=self.facet_id, term_id=tid)
            terms.append(term)
        return terms
    
    def siblings(self):
        terms = []
        for tid in self._siblings:
            term = Term(facet_id=self.facet_id, term_id=tid)
            terms.append(term)
        return terms
    
    def encyc_articles(self):
        if self.encyc_urls and not self._encyc_articles:
            self._encyc_articles = [
                {
                    'url': '%s%s' % (settings.ENCYC_BASE, uri),
                    'title': urllib.unquote(uri).replace('/', '')
                }
                for uri in self.encyc_urls
            ]
        return self._encyc_articles


INT_IN_STRING = re.compile(r'^\d+$')

def extract_term_id( text ):
    """
    >>> extract_term_id('Manzanar [7]')
    '7'
    >>> extract_term_id('[7]')
    '7'
    >>> extract_term_id('7')
    '7'
    >>> extract_term_id(7)
    '7'
    """
    if ('[' in text) and (']' in text):
        term_id = text.split('[')[1].split(']')[0]
    elif re.match(INT_IN_STRING, text):
        term_id = text
    else:
        term_id = text
    return term_id

def facet_terms(facet):
    """
    If term is precoordinate all the terms are listed, with count of number of occurances (if any).
    If term is postcoordinate, all the terms come from the index, but there is not title/description.
    """
    facetterms = []
    ds = docstore.Docstore()
    results = ds.facet_terms(facet['name'], order='term')
    if facet.get('terms', []):
        # precoordinate
        # IMPORTANT: topics and facility term IDs are int. All others are str.
        term_counts = {}
        for t in results['terms']:
            term_id = extract_term_id(t['term'])
            term_count = t['count']
            if term_id and term_count:
                term_counts[term_id] = term_count
        # make URLs for terms
        for term in facet['terms']:
            term['url'] = reverse('ui-search-term-query', args=(facet['id'], term['id']))
        # add counts to terms
        for term in facet['terms']:
            term_id = term['id']
            if isinstance(term_id, int):
                term_id = str(term_id)
            term['count'] = term_counts.get(term_id, 0)
            facetterms.append(term)
    else:
        # postcoordinate
        for t in results['terms']:
            t['title'] = t['term']
            t['description'] = ''
            t['url'] = '/search/%s:%s/' % (facet['id'], t['term'])
            facetterms.append(t)
    return facetterms
