import datetime
import os

from django import template
from django.conf import settings


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

def homeslideitem( target_url, img_src ):
    """Slide item for homepage gallery
    
    @param target_url: str Target URL path, no domain.
    @param img_src: str Source img path, MEDIA_URL_LOCAL will be prepended.
    """
    img_url = os.path.join(settings.MEDIA_URL_LOCAL, img_src)
    t = template.loader.get_template('ui/homeslideitem.html')
    return t.render(template.Context({
        'target_url': target_url,
        'img_url': img_url,
        'MEDIA_URL': settings.MEDIA_URL,
    }))
	
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
