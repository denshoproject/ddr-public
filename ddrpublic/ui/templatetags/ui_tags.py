import datetime
from django import template

register = template.Library()


def addthis():
    """AddThis button
    """
    t = template.loader.get_template('ui/addthis.html')
    return t.render(template.Context({}))

register.simple_tag(addthis)
