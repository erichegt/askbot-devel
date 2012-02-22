import os
import sys
import shutil
import subprocess

DIR1 = sys.argv[1]
DIR2 = sys.argv[2]
DEST_DIR = sys.argv[3]

def get_locale_list(path):
    """return names of directories within a locale dir"""
    items = os.listdir(path)
    result = list()
    for item in items:
        if os.path.isdir(os.path.join(path, item)):
            result.append(item)
    return result

def copy_locale_from(localeno, name = None):
    """copy entire locale without merging"""
    if localeno == 1:
        src = os.path.join(DIR1, name)
    elif localeno == 2:
        src = os.path.join(DIR2, name)
    shutil.copytree(src, os.path.join(DEST_DIR, name))

def merge_locales(name):
    """runs msgcat command on specified files
    and a locale name in DIR1 and DIR2"""
    run_msgcat(name, 'django.po')
    run_msgcat(name, 'djangojs.po')

def run_msgcat(locale_name, file_name):
    """run msgcat in locale on file name"""
    file_path = os.path.join(locale_name, 'LC_MESSAGES', file_name)
    dest_file = os.path.join(DEST_DIR, file_path)
    dest_dir = os.path.dirname(dest_file)
    if not os.path.exists(dest_dir):
        os.makedirs(os.path.dirname(dest_file))
    subprocess.call((
        'msgcat',
        os.path.join(DIR1, file_path),
        os.path.join(DIR2, file_path),
        '-o',
        dest_file
    ))

LOCALE_LIST1 = get_locale_list(DIR1)
LOCALE_LIST2 = get_locale_list(DIR2)

for locale in LOCALE_LIST1:
    print locale
    if locale not in LOCALE_LIST2:
        copy_locale_from(1, name = locale)
    else:
        merge_locales(locale)
        LOCALE_LIST2.remove(locale)

for locale in LOCALE_LIST2:
    print locale
    copy_locale_from(2, name = locale)
