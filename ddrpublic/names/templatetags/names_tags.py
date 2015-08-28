from django import template
from django.conf import settings


register = template.Library()
	
def record( record ):
    t = template.loader.get_template('names/list-object.html')
    return t.render(template.Context({'record':record}))
	
def names_paginate( paginator ):
    t = template.loader.get_template('names/names-paginate.html')
    return t.render(template.Context({'paginator':paginator}))

register.simple_tag(record)
register.simple_tag(names_paginate)
