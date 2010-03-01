import os
import types

MODULES_PACKAGE = 'forum_modules'

MODULES_FOLDER = os.path.join(os.path.dirname(__file__), '../' + MODULES_PACKAGE)

MODULE_LIST = [
        __import__('forum_modules.%s' % f, globals(), locals(), ['forum_modules'])
        for f in os.listdir(MODULES_FOLDER)
        if os.path.isdir(os.path.join(MODULES_FOLDER, f)) and
           os.path.exists(os.path.join(MODULES_FOLDER, "%s/__init__.py" % f)) and
           not os.path.exists(os.path.join(MODULES_FOLDER, "%s/DISABLED" % f))
]

def get_modules_script(script_name):
    all = []

    for m in MODULE_LIST:
        try:
            all.append(__import__('%s.%s' % (m.__name__, script_name), globals(), locals(), [m.__name__]))
        except:
            pass

    return all

def get_modules_script_classes(script_name, base_class):
    scripts = get_modules_script(script_name)
    all_classes = {}

    for script in scripts:
        all_classes.update(dict([
            (n, c) for (n, c) in [(n, getattr(script, n)) for n in dir(script)]
            if isinstance(c, (type, types.ClassType)) and issubclass(c, base_class)
        ]))

    return all_classes

def get_all_handlers(name):
     handler_files = get_modules_script('handlers')

     return [
        h for h in [
            getattr(f, name) for f in handler_files
            if hasattr(f, name)
        ]

        if callable(h)
     ]

def get_handler(name, default):
    all = get_all_handlers(name)
    print(len(all))
    return len(all) and all[0] or default