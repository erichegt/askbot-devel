import os
import logging
from django.conf import settings as django_settings

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

def get_media_url(url):
    """returns url prefixed with the skin name
    of the first skin that contains the file 
    directories are searched in this order:
    askbot_settings.ASKBOT_DEFAULT_SKIN, then 'default', then 'commmon'
    if file is not found - returns None
    and logs an error message
    """
    url = unicode(url)
    while url[0] == '/': url = url[1:]
    #todo: handles case of multiple skin directories

    #if file is in upfiles directory, then give that
    url_copy = url
    if url_copy.startswith(django_settings.ASKBOT_UPLOADED_FILES_URL):
        file_path = url_copy.replace(
                                django_settings.ASKBOT_UPLOADED_FILES_URL,
                                '',
                                1
                            )
        file_path = os.path.join(
                            django_settings.ASKBOT_FILE_UPLOAD_DIR,
                            file_path
                        )
        if os.path.isfile(file_path):
            url_copy = os.path.normpath(
                                    '///' + url_copy
                                ).replace(
                                    '\\', '/'
                                ).replace(
                                    '///', '/'
                                )
            return url_copy
        else:
            logging.critical('missing media resource %s' % url)

    #2) if it does not exist - look in skins

    #purpose of this try statement is to determine
    #which skin is currently used
    try:
        #this import statement must be hidden here
        #because at startup time this branch will fail
        #due to an import error
        from askbot.conf import settings as askbot_settings
        use_skin = askbot_settings.ASKBOT_DEFAULT_SKIN
        resource_revision = askbot_settings.MEDIA_RESOURCE_REVISION
    except ImportError:
        use_skin = 'default'
        resource_revision = None

    skins = get_skin_dirs()[0]

    #see if file exists, if not, try skins 'default', then 'common'
    file_path = os.path.join(skins, use_skin, 'media', url)
    if not os.path.isfile(file_path):
        file_path = os.path.join(skins, 'default', 'media', url)
        if os.path.isfile(file_path):
            use_skin = 'default'
        else:
            file_path = os.path.join(skins, 'common', 'media', url)
            if os.path.isfile(file_path):
                use_skin = 'common'
            else:
                log_message = 'missing media resource %s in skin %s' \
                                % (url, use_skin)
                logging.critical(log_message)
                use_skin = ''
                return None

    url = use_skin + '/media/' + url
    url = '///' + django_settings.ASKBOT_URL + 'm/' + url
    url = os.path.normpath(url).replace(
                                    '\\', '/'
                                ).replace(
                                    '///', '/'
                                )
    
    if resource_revision:
        url +=  '?v=%d' % resource_revision

    return url
