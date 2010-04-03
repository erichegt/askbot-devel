def get_from_dict_or_object(object,key):
    try:
        return object[key]
    except:
        return getattr(object,key)
