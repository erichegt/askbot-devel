"""Utilities for loading modules"""

def load_module(mod_path):
    """an equivalent of:
    from some.where import module
    import module
    """
    assert(mod_path[0] != '.')
    path_bits = mod_path.split('.')
    if len(path_bits) > 1:
        mod_name = path_bits.pop()
        mod_prefix = '.'.join(path_bits)
        _mod = __import__(mod_prefix, globals(), locals(), [mod_name,], -1)
        return getattr(_mod, mod_name)
    else:
        return __import__(mod_path, globals(), locals(), [], -1)
