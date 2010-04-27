import types

def is_string_like(maybe):
    """Test value to see if it acts like a string"""
    try:
        maybe+""
    except TypeError:
        return 0
    else:
        return 1


def is_list_or_tuple(maybe):
    return isinstance(maybe, (types.TupleType, types.ListType))
