import logging
logger = logging.getLogger(__name__)
import os

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpRequest

from DDR.identifier import Identifier as DDRIdentifier
from DDR.identifier import format_id, IdentifierFormatException
from DDR.identifier import CHILDREN, CHILDREN_ALL


# TODO Hard-coded! Get this data from ddr-defs!
MODEL_CLASSES = {
    'file':         {'module': 'ui.models', 'class':'File', 'stub':0, 'templatedir':'files',},
    'segment':      {'module': 'ui.models', 'class':'Entity', 'stub':0, 'templatedir':'entities',},
    'entity':       {'module': 'ui.models', 'class':'Entity', 'stub':0, 'templatedir':'entities',},
    'collection':   {'module': 'ui.models', 'class':'Collection', 'stub':0, 'templatedir':'collections',},
    'organization': {'module': 'ui.models', 'class':'Organization', 'stub':1, 'templatedir':'',},
    'repository':   {'module': 'ui.models', 'class':'Repository', 'stub':1, 'templatedir':'',},
}


class Identifier(DDRIdentifier):

    def __init__(self, *args, **kwargs):
        if kwargs and 'request' in kwargs:
            logger.debug('kwargs %s' % kwargs)
            request = kwargs.pop('request')
        elif args and isinstance(args[0], HttpRequest):
            logger.debug('args %s' % args)
            argz = [a for a in args]
            args = argz
            request = args.pop(0)
        else:
            request = None
        if request:
            object_id = [
                part
                for part in request.META['PATH_INFO'].split(os.path.sep)
                if part
            ]
            kwargs['id'] = object_id
        super(Identifier, self).__init__(*args, **kwargs)
        
    def parent(self, stubs=False):
        """Parent of the Identifier
        
        @param stub: boolean An archival object not just a Stub
        """
        parent_parts = self._parent_parts()
        for model in self._parent_models(stubs):
            idparts = parent_parts
            idparts['model'] = model
            try:
                return Identifier(idparts, base_path=self.basepath)
            except IdentifierFormatException:
                pass
        return None

    def organization_id(self):
        #return self.parts.values()[:2]
        return format_id(self, 'organization')
    
    def organization(self):
        """Organization object to which the Identifier belongs, if any.
        """
        return self.__class__(id=self.organization_id())
    
    def breadcrumbs(self):
        """Returns list of URLs,titles for printing object breadcrumbs.
        
        >>> i = Identifier(id='ddr-test-123-456-master-acbde12345')
        >>> i.breadcrumbs()
        [
          {'url:'/ui/ddr-testing-300/', 'label':'ddr-testing-300'},
          {'url:'/ui/ddr-testing-300-1/', 'label':'1'},
          {'url:'/ui/ddr-testing-300-1/master/', 'label':'master'},
          {'url:'', 'label':'37409ecadb'},
        ]
        """
        INCLUDE = ['collection', 'entity', 'file',]
        crumbs = []
        for i in self.lineage(stubs=True):
            if i.model in INCLUDE:
                crumb = {
                    'identifier': i,
                    'url': reverse('ui-%s' % i.model, args=[i.id]),
                    'label': i.parts.values()[-1],
                }
                crumbs.append(crumb)
        crumbs.reverse()
        # display entire collection id
        crumbs[0]['label'] = crumbs[0]['identifier'].id
        # display role-sha1 for files
        if crumbs[-1]['identifier'].model == 'file':
            i = crumbs[-1]['identifier']
            label = '-'.join([i.parts['role'], i.parts['sha1']])
            crumbs[-1]['label'] = label
        return crumbs

