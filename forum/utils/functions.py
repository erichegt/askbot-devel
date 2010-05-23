def get_from_dict_or_object(source, key):
    try:
        return source[key]
    except:
        return getattr(source,key)

def is_iterable(thing):
    if hasattr(thing, '__iter__'):
        return True
    else:
        return isinstance(thing, basestring)
