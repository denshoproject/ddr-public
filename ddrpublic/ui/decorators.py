from functools import wraps


UI_STATE = {
    'liststyle': ['gallery', 'list'],
    'searchfilters': ['open', 'closed'],
}
UI_STATE_DEFAULTS = {
    'liststyle': 'gallery',
    'searchfilters': 'open',
}

def ui_state(f):
    """Sets defaults for UI state
    """
    @wraps(f)
    def wrapper(*args, **kwargs):

        request = args[0]
        for key,val in UI_STATE_DEFAULTS.items():
            if UI_STATE_DEFAULTS.get(key) and not request.session.get(key):
                request.session[key] = UI_STATE_DEFAULTS[key]
        
        return f(*args, **kwargs)
    return wrapper
