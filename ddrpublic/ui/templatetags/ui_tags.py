import datetime

from django import template
from django.conf import settings
from django.core.cache import cache

from DDR.models import Identity
from ui.models import make_object_url


register = template.Library()

@register.filter(name='ddrvalue')
def ddrvalue( fields, field ):
    """retrieves displayvalue from ddr object fields list matched by fieldname
    """
    try:
        val = [item for item in fields if item[0] == field]
        return val[0][2]
    except:
        return ''

def homeslideitem( fid ):
    """Slide item for homepage gallery
    """
    key = 'ddrpublic:index_slides:%s' % fid
    timeout = 60*5
    cached = cache.get(key)
    if not cached:
        parts = Identity.split_object_id(fid)
        model = parts.pop(0)
        
        class FakeFile(object):
            pass
        fake_file = FakeFile()
        fake_file.collection_id = Identity.make_object_id(
            'collection', parts[0], parts[1], parts[2]
        )
        fake_file.access_rel = '%s-a.jpg' % fid
        img_url = settings.UI_THUMB_URL(fake_file)
        
        t = template.loader.get_template('ui/homeslideitem.html')
        cached = t.render(template.Context({
            'url': make_object_url(parts[:3]),
            'imgurl': img_url
        }))
        cache.set(key, cached, timeout)
    return cached
	
def collection( obj ):
    """list-view collection template
    """
    t = template.loader.get_template('ui/collections/list-object.html')
    return t.render(template.Context({'object':obj}))

def entity( obj ):
    """list-view entity template
    """
    t = template.loader.get_template('ui/entities/list-object.html')
    return t.render(template.Context({'object':obj}))

def file( obj ):
    """list-view file template
    """
    t = template.loader.get_template('ui/files/list-object.html')
    return t.render(template.Context({'object':obj}))

def addthis():
    """AddThis button
    """
    t = template.loader.get_template('ui/addthis.html')
    return t.render(template.Context({}))

def cite( url ):
    """Citation tag
    """
    t = template.loader.get_template('ui/cite-tag.html')
    c = template.Context({'url':url})
    return t.render(c)
	
def rightspanel( code ):
    """Item rights notice
    """
    t = template.loader.get_template('ui/rightspanel-tag.html')
    c = template.Context({'code':code})
    return t.render(c)

register.simple_tag(homeslideitem)
register.simple_tag(collection)
register.simple_tag(entity)
register.simple_tag(file)
register.simple_tag(addthis)
register.simple_tag(cite)
register.simple_tag(rightspanel)
