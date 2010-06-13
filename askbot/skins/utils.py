import os

def get_skin_dirs():
    #todo: handle case of multiple skin directories
    d = os.path.dirname
    n = os.path.normpath
    j = os.path.join
    f = os.path.isfile
    skin_dirs = []
    skin_dirs.append( n(j(d(d(__file__)), 'skins')) )
    return skin_dirs

def get_skin_choices():
    #todo: expand this to handle custom skin directories
    dirs = get_skin_dirs()
    default_dir = dirs[0]
    items = os.listdir(default_dir)
    skin_list = ['default']
    for i in items:
        item_path = os.path.join(default_dir,i)
        if not os.path.isdir(item_path):
            continue
        if i == 'common':
            continue
        if i not in skin_list:
            skin_list.append(i)

    return [(i,i) for i in skin_list]

