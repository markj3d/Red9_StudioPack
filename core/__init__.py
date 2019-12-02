'''

Red9 Studio Pack: Maya Pipeline Solutions
Author: Mark Jackson
email: rednineinfo@gmail.com

Red9 blog : http://red9-consultancy.blogspot.co.uk/
MarkJ blog: http://markj3d.blogspot.co.uk


Core is the library of Python modules that make the backbone of the Red9 Pack

:Note that the registerMClassInheritanceMapping() call is after all the imports
so that the global RED9_META_REGISTERY is built up correctly

'''

import Red9_General as r9General
import Red9_Meta as r9Meta
import Red9_Tools as r9Tools
import Red9_CoreUtils as r9Core
import Red9_AnimationUtils as r9Anim
import Red9_PoseSaver as r9Pose
import Red9_Audio as r9Audio



def _reload():
    '''
    reload carefully and re-register the RED9_META_REGISTRY
    '''
    reload(r9General)
    reload(r9Meta)
    reload(r9Tools)
    reload(r9Audio)
    reload(r9Core)
    reload(r9Anim)
    reload(r9Pose)

    r9Meta.metaData_sceneCleanups()
    r9Meta.registerMClassInheritanceMapping()
    print('Red9 Core Reloaded and META REGISTRY updated')

def _setlogginglevel_debug(module='all'):
    '''
    Dev wrapper to set the logging level to debug
    '''
    if module == 'r9Core' or  module == 'all':
        r9Core.log.setLevel(r9Core.logging.DEBUG)
        print('Red9_CoreUtils set to DEBUG state')
    if module == 'r9Anim' or  module == 'all':
        r9Anim.log.setLevel(r9Anim.logging.DEBUG)
        print('Red9_AnimationUtils set to DEBUG state')
    if module == 'r9General' or  module == 'all':
        Red9_General.log.setLevel(Red9_General.logging.DEBUG)
        print('Red9_General set to DEBUG state')
    if module == 'r9Tools' or  module == 'all':
        r9Tools.log.setLevel(r9Tools.logging.DEBUG)
        print('Red9_Tools set to DEBUG state')
    if module == 'r9Audio' or module == 'all':
        r9Audio.log.setLevel(r9Audio.logging.DEBUG)
        print('Red9_Audio set to DEBUG state')
    if module == 'r9Pose' or  module == 'all':
        r9Pose.log.setLevel(r9Pose.logging.DEBUG)
        print('Red9_PoseSaver set to DEBUG state')
    if module == 'r9Meta' or  module == 'all':
        r9Meta.log.setLevel(r9Meta.logging.DEBUG)
        print('Red9_Meta set to DEBUG state')


def _setlogginglevel_info(module='all'):
    '''
    Dev wrapper to set the logging to Info, usual state
    '''
    if module == 'r9Core' or  module == 'all':
        r9Core.log.setLevel(r9Core.logging.INFO)
        print('Red9_CoreUtils set to INFO state')
    if module == 'r9Anim' or  module == 'all':
        r9Anim.log.setLevel(r9Anim.logging.INFO)
        print('Red9_AnimationUtils set to INFO state')
    if module == 'r9General' or  module == 'all':
        Red9_General.log.setLevel(Red9_General.logging.INFO)
        print('Red9_General set to INFO state')
    if module == 'r9Tools' or  module == 'all':
        r9Tools.log.setLevel(r9Tools.logging.INFO)
        print('Red9_Tools set to INFO state')
    if module == 'r9Audio' or module == 'all':
        r9Audio.log.setLevel(r9Audio.logging.INFO)
        print('Red9_Audio set to DEBUG state')
    if module == 'r9Pose' or  module == 'all':
        r9Pose.log.setLevel(r9Pose.logging.INFO)
        print('Red9_PoseSaver set to INFO state')
    if module == 'r9Meta' or  module == 'all':
        r9Meta.log.setLevel(r9Meta.logging.INFO)
        print('Red9_Meta set to INFO state')


# ========================================================================
# This HAS to be at the END of this module so that the RED9_META_REGISTRY
# picks up all inherited subclasses when Red9.core is imported
# ========================================================================
r9Meta.registerMClassInheritanceMapping()
r9Meta.registerMClassNodeMapping()



