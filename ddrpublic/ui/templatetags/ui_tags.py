import datetime
from django import template

register = template.Library()

""" DEVELOPMENT
"""
@register.filter(name='fixurllocal')
def fixurllocal( value ):
	"""fix urls for local vm testing
	"""
	return value.replace("ddr.densho.org","192.168.56.101")
	
def homeslideitem( url, imgurl ):
	"""Slide item for homepage gallery
	"""
	t = template.loader.get_template('ui/homeslideitem.html')
	return t.render(template.Context({'url':url,'imgurl':imgurl}))
	
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
