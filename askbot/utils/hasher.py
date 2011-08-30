import hashlib, os
import logging
from askbot.conf import settings as askbot_settings
from askbot.skins.utils import get_path_to_skin, get_skin_choices


def get_hash_of_dirs(directory):
  SHAhash = hashlib.sha1()
  if not os.path.exists (directory):
    return -1
    
  try:
    for root, dirs, files in os.walk(directory):
      for names in files:
        filepath = os.path.join(root,names)
        try:
          f1 = open(filepath, 'rb')
        except:
          # You can't open the file for some reason
          f1.close()
          continue

	while 1:
	  # Read file in as little chunks
  	  buf = f1.read(4096)
	  if not buf : break
	  SHAhash.update(hashlib.sha1(buf).hexdigest())
        f1.close()

  except:
    import traceback
    # Print the stack traceback
    traceback.print_exc()
    return -2

  return SHAhash.hexdigest()

def update_revision(skin = None):
    resource_revision = askbot_settings.MEDIA_RESOURCE_REVISION
    if skin:
        if skin in get_skin_choices():
            skin_path = get_path_to_skin(skin)
        else:
            raise MediaNotFound('Skin not found') 
    else:
        skin_path = get_path_to_skin(askbot_settings.ASKBOT_DEFAULT_SKIN)

    current_hash = get_hash_of_dirs(skin_path)

    if current_hash != askbot_settings.MEDIA_RESOURCE_REVISION_HASH:
        askbot_settings.update('MEDIA_RESOURCE_REVISION', resource_revision + 1)
        askbot_settings.update('MEDIA_RESOURCE_REVISION_HASH', current_hash) 
        logging.debug('MEDIA_RESOURCE_REVISION changed')
