from collections import OrderedDict
from functools import total_ordering
import re

IDENTIFIERS = [
    
    # ------------------------------------------------------------------
    {
        'model': 'repository',
        'module': '',
        'class': 'DDR.models.Stub',
        'elastic_class': 'repo_models.elastic.ESRepository',
        'level': -2,
        'component': {
            'name': 'repo',
            'type': str,
            'form': {
                'type': 'CharField',
                'label': 'Repository Keyword',
                'max_length': 10,
            },
            'valid': ['ddr'],
        },
        'parents': [],
        'parents_all': [],
        'children': ['organization'],
        'children_all': ['organization'],
        'templates': {
            'id': [
                '{repo}',
            ],
            'path': {
                'rel': [
                    '',
                ],
                'abs': [
                    '{basepath}/{repo}',
                ],
            },
            'url': {
                'editor': [
                    '/ui/{repo}',
                ],
                'public': [
                    '/{repo}',
                ],
            },
        },
        'patterns': {
            'id': [
                r'^(?P<repo>[\w]+)$',
            ],
            'path': [
                r'(?P<basepath>[\w/-]+)/(?P<repo>[\w]+)/repository.json$',
                r'(?P<basepath>[\w/-]+)/(?P<repo>[\w]+)$',
                r'^repository.json$',
            ],
            'url': [
                r'/ui/(?P<repo>[\w]+)$',
                r'^/(?P<repo>[\w]+)$',
            ],
        },
        'files': {
            'json': 'repository.json',
        },
    },
    
    # ------------------------------------------------------------------
    {
        'model': 'organization',
        'module': '',
        'class': 'DDR.models.Stub',
        'elastic_class': 'repo_models.elastic.ESOrganization',
        'level': -1,
        'component': {
            'name': 'org',
            'type': str,
            'form': {
                'type': 'CharField',
                'label': 'Organization Keyword',
                'max_length': 32,
            },
            'valid': [
                'densho', 'hmwf', 'jamsj', 'janm', 'jcch', 'manz', 'njpa',
                'one', 'pc', 'dev', 'test', 'testing',
            ],
        },
        'parents': [],
        'parents_all': ['repository'],
        'children': ['collection'],
        'children_all': ['collection'],
        'templates': {
            'id': [
                '{repo}-{org}',
            ],
            'path': {
                'rel': [
                    '',
                ],
                'abs': [
                    '{basepath}/{repo}-{org}',
                ],
            },
            'url': {
                'editor': [
                    '/ui/{repo}-{org}',
                ],
                'public': [
                    '/{repo}/{org}',
                ],
            },
        },
        'patterns': {
            'id': [
                r'^(?P<repo>[\w]+)-(?P<org>[\w]+)$'
            ],
            'path': [
                r'(?P<basepath>[\w/-]+)/(?P<repo>[\w]+)-(?P<org>[\w]+)$',
                r'^organization.json$',
            ],
            'url': [
                r'/ui/(?P<repo>[\w]+)-(?P<org>[\w]+)$',
                r'^/(?P<repo>[\w]+)/(?P<org>[\w]+)$',
            ],
        },
        'files': {
            'json': 'organization.json',
        },
    },
    
    # ------------------------------------------------------------------
    {
        'model': 'collection',
        'module': 'repo_models.collection',
        'class': 'DDR.models.Collection',
        'elastic_class': 'repo_models.elastic.ESCollection',
        'level': 0,
        'component': {
            'name': 'cid',
            'type': int,
            'form': {
                'type': 'IntegerField',
                'label': 'Collection ID',
            },
            'valid': [],
        },
        'parents': [],
        'parents_all': ['organization'],
        'children': ['entity'],
        'children_all': ['entity'],
        'templates': {
            'id': [
                '{repo}-{org}-{cid}',
            ],
            'path': {
                'rel': [
                    '',
                ],
                'abs': [
                    '{basepath}/{repo}-{org}-{cid}',
                ],
            },
            'url': {
                'editor': [
                    '/ui/{repo}-{org}-{cid}',
                ],
                'public': [
                    '/{repo}/{org}/{cid}',
                ],
            },
        },
        'patterns': {
            'id': [
                r'^(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)$',
            ],
            'path': [
                r'(?P<basepath>[\w/-]+)/(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)',
                r'^collection.json$',
            ],
            'url': [
                r'/ui/(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)$',
                r'^/(?P<repo>[\w]+)/(?P<org>[\w]+)/(?P<cid>[\d]+)$',
            ],
        },
        'files': {
            'annex': '.git/annex',
            'changelog': 'changelog',
            'control': 'control',
            'ead': 'ead.xml',
            'files': 'files',
            'gitignore': '.gitignore',
            'git': '.git',
            'json': 'collection.json',
            'lock': 'lock',
        },
        'filename_regex': 'collection.json',
    },
    
    # ------------------------------------------------------------------
    {
        'model': 'entity',
        'module': 'repo_models.entity',
        'class': 'DDR.models.Entity',
        'elastic_class': 'repo_models.elastic.ESEntity',
        'level': 1,
        'component': {
            'name': 'eid',
            'type': int,
            'form': {
                'type': 'IntegerField',
                'label': 'Object ID',
            },
            'valid': [],
        },
        'parents': ['collection'],
        'parents_all': ['collection'],
        'children': ['segment', 'file'],
        'children_all': ['segment', 'file-role'],
        'templates': {
            'id': [
                '{repo}-{org}-{cid}-{eid}',
            ],
            'path': {
                'rel': [
                    'files/{repo}-{org}-{cid}-{eid}',
                ],
                'abs': [
                    '{basepath}/{repo}-{org}-{cid}/files/{repo}-{org}-{cid}-{eid}',
                ],
            },
            'url': {
                'editor': [
                    '/ui/{repo}-{org}-{cid}-{eid}',
                ],
                'public': [
                    '/{repo}/{org}/{cid}/{eid}',
                ],
            },
        },
        'patterns': {
            'id': [
                r'^(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)$',
            ],
            'path': [
                # ---------------------/collection-------/-----/entity
                r'(?P<basepath>[\w/-]+)/(?P<id0>[\w\d-]+)/files/(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)/entity.json',
                r'(?P<basepath>[\w/-]+)/(?P<id0>[\w\d-]+)/files/(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)',
                # ------/entity
                r'^files/(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)/entity.json$',
                r'^files/(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)$',
            ],
            'url': [
                # editor
                r'/ui/(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)$',
                # public
                r'^/(?P<repo>[\w]+)/(?P<org>[\w]+)/(?P<cid>[\d]+)/(?P<eid>[\d]+)$',
            ],
        },
        'files': {
            'changelog': 'changelog',
            'control': 'control',
            'files': 'files',
            'json': 'entity.json',
            'lock': 'lock',
            'mets': 'mets.xml',
        },
        'filename_regex': 'entity.json',
    },
    
    # ------------------------------------------------------------------
    {
        'model': 'segment',
        'module': 'repo_models.segment',
        'class': 'DDR.models.Entity',
        'elastic_class': 'repo_models.elastic.ESEntity',
        'level': 2,
        'component': {
            'name': 'sid',
            'type': int,
            'form': {
                'type': 'IntegerField',
                'label': 'Segment ID',
            },
            'valid': [],
        },
        'parents': ['entity'],
        'parents_all': ['entity'],
        'children': ['file'],
        'children_all': ['file-role'],
        'templates': {
            'id': [
                '{repo}-{org}-{cid}-{eid}-{sid}',
            ],
            'path': {
                'rel': [
                    'files/{repo}-{org}-{cid}-{eid}/files/{repo}-{org}-{cid}-{eid}-{sid}',
                ],
                'abs': [
                    '{basepath}/{repo}-{org}-{cid}/files/{repo}-{org}-{cid}-{eid}/files/{repo}-{org}-{cid}-{eid}-{sid}',
                ],
            },
            'url': {
                'editor': [
                    '/ui/{repo}-{org}-{cid}-{eid}-{sid}',
                ],
                'public': [
                    '/{repo}/{org}/{cid}/{eid}/{sid}',
                ],
            },
        },
        'patterns': {
            'id': [
                r'^(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)-(?P<sid>[\d]+)$',
            ],
            'path': [
                # ---------------------/collection-------/-----/entity-----------/-----/segment
                r'(?P<basepath>[\w/-]+)/(?P<id0>[\w\d-]+)/files/(?P<id1>[\w\d-]+)/files/(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)-(?P<sid>[\d]+)/entity.json$',
                r'(?P<basepath>[\w/-]+)/(?P<id0>[\w\d-]+)/files/(?P<id1>[\w\d-]+)/files/(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)-(?P<sid>[\d]+)$',
                # ------/entity-----------/-----/segment
                r'^files/(?P<id0>[\w\d-]+)/files/(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)-(?P<sid>[\d]+)/entity.json$',
                r'^files/(?P<id0>[\w\d-]+)/files/(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)-(?P<sid>[\d]+)$',
            ],
            'url': [
                # editor
                r'/ui/(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)-(?P<sid>[\d]+)$',
                # public
                r'^/(?P<repo>[\w]+)/(?P<org>[\w]+)/(?P<cid>[\d]+)/(?P<eid>[\d]+)/(?P<sid>[\d]+)$',
            ],
        },
        'files': {
            'changelog': 'changelog',
            'control': 'control',
            'files': 'files',
            'json': 'entity.json',
            'lock': 'lock',
            'mets': 'mets.xml',
        },
        'filename_regex': 'entity.json',
    },
    
    # ------------------------------------------------------------------
    {
        'model': 'file-role',
        'module': '',
        'class': 'DDR.models.Stub',
        'elastic_class': '',
        'level': 3,
        'component': {
            'name': 'role',
            'type': str,
            'form': {
                'type': 'CharField',
                'label': 'Role',
                'max_length': 32,
            },
            'valid': [
                'mezzanine',
                'master',
                'transcript',
                'gloss',
                'preservation',
                'administrative',
            ],
        },
        'parents': [],
        'parents_all': ['segment', 'entity'],
        'children': ['file'],
        'children_all': ['file'],
        'templates': {
            'id': [
                '{repo}-{org}-{cid}-{eid}-{sid}-{role}',
                '{repo}-{org}-{cid}-{eid}-{role}',
            ],
            'path': {
                'rel': [],
                'abs': [],
            },
            'url': {
                'editor': [
                    '/ui/{repo}-{org}-{cid}-{eid}-{sid}-{role}',
                    '/ui/{repo}-{org}-{cid}-{eid}-{role}',
                ],
                'public': [
                    '/{repo}/{org}/{cid}/{eid}/{sid}/{role}',
                    '/{repo}/{org}/{cid}/{eid}/{role}',
                ],
            },
        },
        'patterns': {
            'id': [
                r'^(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)-(?P<sid>[\d]+)-(?P<role>[a-zA-Z]+)$',
                r'^(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)-(?P<role>[a-zA-Z]+)$',
            ],
            'path': [
            ],
            'url': [
                # editor
                r'/ui/(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)-(?P<sid>[\d]+)-(?P<role>[a-zA-Z]+)$',
                r'/ui/(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)-(?P<role>[a-zA-Z]+)$',
                # public
                r'^/(?P<repo>[\w]+)/(?P<org>[\w]+)/(?P<cid>[\d]+)/(?P<eid>[\d]+)/(?P<sid>[\d]+)/(?P<role>[a-zA-Z]+)$',
                r'^/(?P<repo>[\w]+)/(?P<org>[\w]+)/(?P<cid>[\d]+)/(?P<eid>[\d]+)/(?P<role>[a-zA-Z]+)$',
            ],
        },
        'files': {
        },
    },

    # ------------------------------------------------------------------
    {
        'model': 'file',
        'module': 'repo_models.files',
        'class': 'DDR.models.File',
        'elastic_class': 'repo_models.elastic.ESFile',
        'level': 4,
        'component': {
            'name': 'sha1',
            'type': str,
            'form': {
                'type': 'CharField',
                'label': 'SHA1',
                'max_length': 10,
            },
            'valid': [],
        },
        'parents': ['segment', 'entity'],
        'parents_all': ['file-role'],
        'children': [],
        'children_all': [],
        'templates': {
            'id': [
                '{repo}-{org}-{cid}-{eid}-{sid}-{role}-{sha1}',
                '{repo}-{org}-{cid}-{eid}-{role}-{sha1}',
            ],
            'path': {
                'rel': [
                    # ----/entity------------------/-----/segment-----------------------/-----/file
                    'files/{repo}-{org}-{cid}-{eid}/files/{repo}-{org}-{cid}-{eid}-{sid}/files/{repo}-{org}-{cid}-{eid}-{sid}-{role}-{sha1}',
                    # ----/entity------------------/-----/file
                    'files/{repo}-{org}-{cid}-{eid}/files/{repo}-{org}-{cid}-{eid}-{role}-{sha1}',
                ],
                'abs': [
                    # ---------/collection--------/-----/entity------------------/-----/segment-----------------------/-----/file
                    '{basepath}/{repo}-{org}-{cid}/files/{repo}-{org}-{cid}-{eid}/files/{repo}-{org}-{cid}-{eid}-{sid}/files/{repo}-{org}-{cid}-{eid}-{sid}-{role}-{sha1}',
                    # ---------/collection--------/-----/entity------------------/-----/file
                    '{basepath}/{repo}-{org}-{cid}/files/{repo}-{org}-{cid}-{eid}/files/{repo}-{org}-{cid}-{eid}-{role}-{sha1}',
                ],
            },
            'url': {
                'editor': [
                    '/ui/{repo}-{org}-{cid}-{eid}-{sid}-{role}-{sha1}',
                    '/ui/{repo}-{org}-{cid}-{eid}-{role}-{sha1}',
                ],
                'public': [
                    '/{repo}/{org}/{cid}/{eid}/{sid}/{role}/{sha1}',
                    '/{repo}/{org}/{cid}/{eid}/{role}/{sha1}',
                ],
            },
        },
        'patterns': {
            'id': [
                r'^(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)-(?P<sid>[\d]+)-(?P<role>[a-zA-Z]+)-(?P<sha1>[\w]+)$',
                r'^(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)-(?P<role>[a-zA-Z]+)-(?P<sha1>[\w]+)$',
            ],
            'path': [
                # file-abs
                # ---------------------/collection-------/-----/entity-----------/-----/segment----------/-----/file
                r'(?P<basepath>[\w/-]+)/(?P<id0>[\w\d-]+)/files/(?P<id1>[\w\d-]+)/files/(?P<id2>[\w\d-]+)/files/(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)-(?P<sid>[\d]+)-(?P<role>[a-zA-Z]+)-(?P<sha1>[\w\d]+)\.(?P<ext>[\w]+)$',
                r'(?P<basepath>[\w/-]+)/(?P<id0>[\w\d-]+)/files/(?P<id1>[\w\d-]+)/files/(?P<id2>[\w\d-]+)/files/(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)-(?P<sid>[\d]+)-(?P<role>[a-zA-Z]+)-(?P<sha1>[\w\d]+)\.json$',
                r'(?P<basepath>[\w/-]+)/(?P<id0>[\w\d-]+)/files/(?P<id1>[\w\d-]+)/files/(?P<id2>[\w\d-]+)/files/(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)-(?P<sid>[\d]+)-(?P<role>[a-zA-Z]+)-(?P<sha1>[\w\d]+)$',
                # ---------------------/collection-------/-----/entity-----------/-----/file
                r'(?P<basepath>[\w/-]+)/(?P<id0>[\w\d-]+)/files/(?P<id1>[\w\d-]+)/files/(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)-(?P<role>[a-zA-Z]+)-(?P<sha1>[\w\d]+)\.(?P<ext>[\w]+)$',
                r'(?P<basepath>[\w/-]+)/(?P<id0>[\w\d-]+)/files/(?P<id1>[\w\d-]+)/files/(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)-(?P<role>[a-zA-Z]+)-(?P<sha1>[\w\d]+)\.json$',
                r'(?P<basepath>[\w/-]+)/(?P<id0>[\w\d-]+)/files/(?P<id1>[\w\d-]+)/files/(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)-(?P<role>[a-zA-Z]+)-(?P<sha1>[\w\d]+)$',
                # file-rel
                # ------/enity------------/-----/segment----------------/file
                r'^files/(?P<id0>[\w\d-]+)/files/(?P<id1>[\w\d-]+)/files/(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)-(?P<sid>[\d]+)-(?P<role>[a-zA-Z]+)-(?P<sha1>[\w\d]+)\.(?P<ext>[\w]+)$',
                r'^files/(?P<id0>[\w\d-]+)/files/(?P<id1>[\w\d-]+)/files/(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)-(?P<sid>[\d]+)-(?P<role>[a-zA-Z]+)-(?P<sha1>[\w\d]+)\.json$',
                r'^files/(?P<id0>[\w\d-]+)/files/(?P<id1>[\w\d-]+)/files/(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)-(?P<sid>[\d]+)-(?P<role>[a-zA-Z]+)-(?P<sha1>[\w\d]+)$',
                # ------/enity------------/-----/file
                r'^files/(?P<id0>[\w\d-]+)/files/(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)-(?P<role>[a-zA-Z]+)-(?P<sha1>[\w\d]+)\.(?P<ext>[\w]+)$',
                r'^files/(?P<id0>[\w\d-]+)/files/(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)-(?P<role>[a-zA-Z]+)-(?P<sha1>[\w\d]+)\.json$',
                r'^files/(?P<id0>[\w\d-]+)/files/(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)-(?P<role>[a-zA-Z]+)-(?P<sha1>[\w\d]+)$',
            ],
            'url': [
                # editor
                r'/ui/(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)-(?P<sid>[\d]+)-(?P<role>[a-zA-Z]+)-(?P<sha1>[\w]+)$',
                r'/ui/(?P<repo>[\w]+)-(?P<org>[\w]+)-(?P<cid>[\d]+)-(?P<eid>[\d]+)-(?P<role>[a-zA-Z]+)-(?P<sha1>[\w]+)$',
                # public
                r'^/(?P<repo>[\w]+)/(?P<org>[\w]+)/(?P<cid>[\d]+)/(?P<eid>[\d]+)/(?P<sid>[\d]+)/(?P<role>[a-zA-Z]+)/(?P<sha1>[\w]+)$',
                r'^/(?P<repo>[\w]+)/(?P<org>[\w]+)/(?P<cid>[\d]+)/(?P<eid>[\d]+)/(?P<role>[a-zA-Z]+)/(?P<sha1>[\w]+)$',
            ],
        },
        'files': {
            'access': '{id}-a.jpg',
            'json': '{id}.json',
        },
        'filename_regex': '-([\d]+)-([\w]+)-([\w\d]+).json',
    },
]


class Definitions():
    """Functions for parsing and extracting useful data from IDENTIFIERS
    """

    # ----------------------------------------------------------------------
    # Regex patterns used to link raw IDs/URLs/paths to models
    #
    # Regex patterns used to match IDs, paths, and URLs and extract model and tokens
    # Record format: (regex, memo, model)
    # TODO are we using ID_PATTERNS memos?
    #

    @staticmethod
    def id_patterns(identifiers):
        # (regex, memo, model) NOTE: 'memo' is not used for anything yet
        patterns = []
        for i in identifiers:
            for regex in i['patterns']['id']:
                p = (re.compile(regex), '', i['model'])
                patterns.append(p)
        patterns.reverse()
        return patterns

ID_PATTERNS = Definitions.id_patterns(IDENTIFIERS)


# ----------------------------------------------------------------------

def identify_object(text, patterns):
    """Split ID, path, or URL into model and tokens and assign to Identifier
    
    Like Django URL router, look for pattern than matches the given text.
    Patterns match to a model and the fields correspond to components of
    a legal object ID.
    Component names and values are assigned as attributes of the object.
    
    @param i: Identifier object
    @param text: str Text string to look for
    @param patterns: list Patterns in which to look
    @returns: dict groupdict resulting from successful regex match
    """
    model = None
    memo = None
    groupdict = None
    for tpl in patterns:
        m = re.match(tpl[0], text)
        if m:
            pattern,memo,model = tpl
            groupdict = m.groupdict()
            break
    ## validate components
    #for key in VALID_COMPONENTS.keys():
    #    val = groupdict.get(key, None)
    #    if val and (val not in VALID_COMPONENTS[key]):
    #        raise Exception('Invalid ID keyword: "%s"' % val)
    return model,memo,groupdict

def matches_pattern(text, patterns):
    """True if text matches one of patterns
    
    Used for telling what kind of pattern (id, path, url) an arg is.
    
    @param text: str
    @returns: dict of idparts including model
    """
    for tpl in patterns:
        pattern = tpl[0]
        model = tpl[-1]
        m = re.match(pattern, text)
        if m:
            idparts = {k:v for k,v in m.groupdict().items()}
            idparts['model'] = model
            return idparts
    return {}

def _is_id(text):
    """
    @param text: str
    @returns: dict of idparts including model
    """
    return matches_pattern(text, ID_PATTERNS)

def _is_path(text):
    """
    @param text: str
    @returns: dict of idparts including model
    """
    return matches_pattern(text, PATH_PATTERNS)

def _is_url(text):
    """
    @param text: str
    @returns: dict of idparts including model
    """
    return matches_pattern(text, URL_PATTERNS)

def _is_abspath(text):
    if isinstance(text, basestring) and os.path.isabs(text):
        return True
    return False

def _parse_args_kwargs(keys, args, kwargs):
    """Attempts to convert Identifier.__init__ args to kwargs.
    
    @param keys: list Whitelist of accepted kwargs
    @param args: list
    @param kwargs: dict
    """
    # TODO there's probably something in stdlib for this...
    blargs = {key:None for key in keys}
    if args:
        arg = None
        if len(args) >= 2: blargs['base_path'] = args[1]
        if len(args) >= 1: arg = args[0]
        if arg:
            # TODO refactor: lots of regex that's duplicated in identify_object
            if isinstance(arg, dict): blargs['parts'] = arg
            elif _is_id(arg): blargs['id'] = arg
            elif _is_url(arg): blargs['url'] = arg
            elif _is_abspath(arg): blargs['path'] = arg
    # kwargs override args
    if kwargs:
        for key,val in kwargs.items():
            if val and (key in keys):
                blargs[key] = val
    return blargs

KWARG_KEYS = [
    'id',
    'parts',
    'path',
    'url',
    'base_path',
]

@total_ordering
class Identifier(object):
    raw = None
    method = None
    model = None
    parts = OrderedDict()
    basepath = None
    id = None
    id_sort = None
    
    def __init__(self, *args, **kwargs):
        """
        NOTE: You will get faster performance with kwargs
        """
        blargs = _parse_args_kwargs(KWARG_KEYS, args, kwargs)
        if blargs['id']: self._from_id(blargs['id'])
        else:
            raise InvalidInputException('Could not grok Identifier input: %s' % blargs)

    def _from_id(self, object_id):
        """Make Identifier from object ID.
        
        >>> Identifier(id='ddr-testing-123-456')
        <Identifier ddr-testing-123-456>
        
        @param object_id: str
        @returns: Identifier
        """
        self.method = 'id'
        self.raw = object_id
        self.id = object_id
        model,memo,groupdict = identify_object(object_id, ID_PATTERNS)
        if not groupdict:
            raise MalformedIDException('Malformed ID: "%s"' % object_id)
        self.model = model
    
    def __repr__(self):
        return "<%s.%s %s:%s>" % (self.__module__, self.__class__.__name__, self.model, self.id)
    
    # NOTE: uses functools.total_ordering to derive the rest of rich comparisons
    # from __eq__ and __lt__.  Might be a performance problem.
    # https://docs.python.org/2/library/functools.html#functools.total_ordering
    def __eq__(self, other):
        """Enable Pythonic sorting"""
        return self.path_abs() == other.path_abs()
    
    def __lt__(self, other):
        """Enable Pythonic sorting"""
        return self._key() < other._key()
    
    def _key(self):
        """Key for Pythonic object sorting.
        Integer components are returned as ints, enabling natural sorting.
        """
        return self.id_sort
