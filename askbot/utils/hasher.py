import hashlib, os
from askbot.conf import settings as askbot_settings
use_skin = askbot_settings.ASKBOT_DEFAULT_SKIN
resource_revision = askbot_settings.MEDIA_RESOURCE_REVISION

def GetHashofDirs(directory, verbose=0):
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

if __name__ == '__main__':
    #directory = raw_input('directory:')
    #print GetHashofDirs(directory, 0)
    print GetHashofDirs('skins/default/media', 0)
