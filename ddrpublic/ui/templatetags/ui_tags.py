import datetime
import os
import re

from django import template
from django.conf import settings

from ui.models import MODEL_PLURALS

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

@register.filter(name='segmentoneline')
def segmentoneline( description):
    """returns one line description for segment list; trims at first paragraph tag
    """
    if '<p>' in description:
        oneline = description[0:description.find('<p>')]
    elif '<P>' in description:
        oneline = description[0:description.find('<P>')]
    else:
        oneline = description
    return oneline

@register.filter(name='formaticon')
def formaticon( code ):
    """returns fa icon for the given entity.format code
    """
    icon = 'fa-file-text-o'
    if code == 'img':
        icon = 'fa-file-image-o'
    elif code == 'vh' or code == 'av':
        icon = 'fa-film'
    return icon

@register.filter(name='legacydenshouid')
def legacydenshouid( value ):
    """returns plain legacy denshouid
    """
    uid = ''
    p = re.compile('\[denshouid:[ ]*([a-z_\-0-9]+)\]')
    m = p.findall(value)
    if m is not None:
        uid = m[0]
    return uid

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
	
def breadcrumbs( crumbs, link_endpoint=0 ):
    """breadcrumbs up to and including collection
    """
    if not link_endpoint:
        crumbs[-1]['url'] = ''
    t = template.loader.get_template('ui/breadcrumbs.html')
    return t.render(template.Context({'breadcrumbs':crumbs}))

def document( obj ):
    """list-view document template
    """
    try:
        model_plural = MODEL_PLURALS[obj['model']]
    except:
        return """<div class="media " style="border:2px dashed red;">%s</div>""" % str(obj)
    template_path = 'ui/%s/list-object.html' % model_plural
    t = template.loader.get_template(template_path)
    return t.render(template.Context({'object':obj}))

def galleryitem( obj ):
    """gallery-view item template
    """
    try:
        model_plural = MODEL_PLURALS[obj['model']]
    except:
        return """<div class="media " style="border:2px dashed red;">%s</div>""" % str(obj)
    template_path = 'ui/%s/gallery-object.html' % model_plural
    t = template.loader.get_template(template_path)
    return t.render(template.Context({'object':obj}))

def listitem( obj ):
    """list-view item template
    """
    try:
        model_plural = MODEL_PLURALS[obj['model']]
    except:
        return """<div class="media " style="border:2px dashed red;">%s</div>""" % str(obj)
    template_path = 'ui/%s/list-object.html' % model_plural
    t = template.loader.get_template(template_path)
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

def rightsbadge( code ):
    """Item rights badge
    """
    if code:
        template_name = 'ui/license-{}.html'.format(code)
    else:
        template_name = 'ui/license.html'
    t = template.loader.get_template(template_name)
    c = template.Context({'code':code})
    return t.render(c)

register.simple_tag(homeslideitem)
register.simple_tag(breadcrumbs)
register.simple_tag(document)
register.simple_tag(galleryitem)
register.simple_tag(listitem)
register.simple_tag(addthis)
register.simple_tag(cite)
register.simple_tag(rightspanel)
register.simple_tag(rightsbadge)
