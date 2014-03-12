

#Entry point for the Red9 Studio Pack. Copy this file to your
#C:\user\xxxxx\Documents\maya\20xx\scripts folder and edit the path 
#below to point to the folder containing the Red9 folder.

#Note: the first 2 lines arent needed if you dropped the Red9 folder
#into the Maya scripts directory in your prefs, or any directory already 
#on a Python path

#repoint the path to folder that contains the Red9 folder
#NOT to the Red9 folder itself

import sys
sys.path.append('O:\Animation\Red9_Release')

#then to launch
import Red9
Red9.start()
