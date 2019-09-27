'''
cmds : sphinx-build -b html X:\Red9\docs\source X:\Red9\docs\html
'''

import os
# import time
# import pymel.core as pCore

THISDIR = os.path.dirname(__file__)
OUTPUTHTML = THISDIR + "/html"
SOURCEFOLDER = "%s/source" % THISDIR

# starttime = time.strftime("%H")
# time.gmtime


if __name__ == "__main__":
    #while time.strftime("%H") == starttime:
#     print 'SRC : ', SOURCEFOLDER
#     print 'OUTPUT : ', OUTPUTHTML
    cmd = "sphinx-build -b html %s %s" % (SOURCEFOLDER, OUTPUTHTML)
    os.system(cmd)

