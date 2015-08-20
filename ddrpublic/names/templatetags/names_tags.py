from django import template
from django.conf import settings


register = template.Library()
	
def record( record ):
    t = template.loader.get_template('names/list-object.html')
    return t.render(template.Context({'record':record}))

register.simple_tag(record)
