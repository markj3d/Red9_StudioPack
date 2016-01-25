'''
------------------------------------------
Red9 Studio Pack: Maya Pipeline Solutions
Author: Mark Jackson
email: rednineinfo@gmail.com

Red9 blog : http://red9-consultancy.blogspot.co.uk/
MarkJ blog: http://markj3d.blogspot.co.uk
------------------------------------------

This is the heart of the Red9 StudioPack's boot sequence, managing folder structures,
dependencies and menuItems.

#########  THIS SHOULD NOT REQUIRE ANY OF THE RED9.core modules  ##########
'''

#from Red9.startup import language_packs


__author__ = 'Mark Jackson'
__buildVersionID__ = 2.0
installedVersion= False


import sys
import os
import imp
import maya.cmds as cmds
import maya.mel as mel
from functools import partial

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

      
'''
 Maya Version Mapping History:
 ====================================

 Release         -version    -api     python    -qt       prefs      release    extra info
 -----------------------------------------------------------------------------------------
 
  2008          .  2008  .  ??????  .  2.5.1     na    .  2008    . 2007-09-01
  2009          .  2009  .  ??????  .  2.5.1     na    .  2009    . 2008-10-01
  2010          .  2010  .  201000  .  2.6.1     na    .  2010    . 2009-08-01
  2011 Hotfix2  .  2011  .  201102  .  2.6.4    4.5.3  .  2011    .
  2011 SAP      .  2011  .  201104  .  2.6.4    4.5.3  .  2011.5  . 2010-09-29  . 2011 binary compliant

  2012          .  2012  .  201200  .  2.6.4    4.7.1  .  2012    . 2011-04-01
  2012 SP1      .  2012  .  ??????  .  2.6.4    4.7.1  .  2012    .
  2012 SAP1     .  2012  .  ??????  .  2.6.4    4.7.1  .  2012    . 2012-01-26
  2012 SP2      .  2012  .  201217  .  2.6.4    4.7.1  .  2012    .
 
  2013 SP1      .  2013  .  201301  .  2.6.4    4.7.1  .  2013    . 2012-07-00
  2013 SP2      .  2013  .  201303  .  2.6.4    4.7.1  .  2013    . 2013-01-00
  2013 EXT      .  2013  .  201350? .  2.6.4    4.7.1  .  2013.5  . 2012-09-25  . 2013 binary incompatible
  2013 EXT2     .  2013  .  201355  .  2.6.4    4.7.1  .  2013.5  . 2013-01-22  . 2013 binary incompatible

  2014          .  2014  .  201400  .  2.6.4    4.8.2  .  2014    . 2013-04-10
  2015          .  2015  .  201500  .  2.7      4.8.5  .  2015    . 2014-04-15
  2016          .  2016  .  201600  .  2.7      4.8.5  .  2016    . 2015-04-15
  
------------------------------------------------------------------------------------------
'''


#=========================================================================================
# LANGUAGE MAPPING -----------------------------------------------------------------------
#=========================================================================================
   
#global LANGUAGE_MAP

import language_packs.language_english
LANGUAGE_MAP = language_packs.language_english

def get_language_maps():
    languages=[]
    language_path = os.path.join(os.path.dirname(__file__),'language_packs')
    packs = os.listdir(language_path)
    for p in packs:
        if p.startswith('language_') and p.endswith('.py'):
            languages.append(p.split('.py')[0])
    return languages
    
def set_language(language='language_english', *args):
    global LANGUAGE_MAP
    language_path = os.path.join(os.path.dirname(__file__),'language_packs')
    packs = get_language_maps()
    if language in packs:
        print 'Red9 : Importing Language Map : %s' % language
        LANGUAGE_MAP = imp.load_source('language', os.path.join(language_path, language+'.py'))

set_language()


# -----------------------------------------------------------------------------------------
# MAYA DATA  ---
# -----------------------------------------------------------------------------------------

MAYA_INTERNAL_DATA = {}  # cached Maya internal vars for speed

def mayaFullSpecs():
    print 'Maya version : ', mayaVersion()
    print 'Maya API version: ', mayaVersionRelease()
    print 'QT build: ', mayaVersionQT()
    print 'Prefs folder: ',mayaPrefs()
    print 'OS build: ', osBuild()
    
    print MAYA_INTERNAL_DATA
     
def mayaVersion():
    #need to manage this better and use the API version,
    #eg: 2013.5 returns 2013
    if 'version' in MAYA_INTERNAL_DATA and MAYA_INTERNAL_DATA['version']:
        return MAYA_INTERNAL_DATA['version']
    else:
        MAYA_INTERNAL_DATA['version'] = mel.eval('getApplicationVersionAsFloat')
        return MAYA_INTERNAL_DATA['version']

def mayaVersionRelease():
    if 'api' in MAYA_INTERNAL_DATA and MAYA_INTERNAL_DATA['api']:
        return MAYA_INTERNAL_DATA['api']
    else:
        MAYA_INTERNAL_DATA['api'] = cmds.about(api=True)
        return MAYA_INTERNAL_DATA['api']

def mayaVersionQT():
    try:
        if 'qt' in MAYA_INTERNAL_DATA and MAYA_INTERNAL_DATA['qt']:
            return MAYA_INTERNAL_DATA['qt']
        else:
            MAYA_INTERNAL_DATA['qt'] = cmds.about(qt=True)
            return MAYA_INTERNAL_DATA['qt']
    except:
        pass
    
def mayaPrefs():
    '''
    Root of Maya prefs folder
    '''
    if 'prefs' in MAYA_INTERNAL_DATA and MAYA_INTERNAL_DATA['prefs']:
        return MAYA_INTERNAL_DATA['prefs']
    else:
        MAYA_INTERNAL_DATA['prefs'] = os.path.dirname(cmds.about(env=True))
        return MAYA_INTERNAL_DATA['prefs']

def mayaUpAxis(setAxis=None):
    import maya.OpenMaya as OpenMaya
    if setAxis:
        if setAxis.lower()=='y':
            OpenMaya.MGlobal.setYAxisUp()
        if setAxis.lower()=='z':
            OpenMaya.MGlobal.setZAxisUp()
    else:
        vect=OpenMaya.MGlobal.upAxis()
        if vect.z:
            return 'z'
        if vect.y:
            return 'y'
    
def mayaIsBatch():
    return cmds.about(batch=True)

def osBuild():
    build = cmds.about(os=True)
    if build == 'win64':
        return 64
    elif build == 'win32':
        return 32

def getCurrentFPS():
    '''
    returns the current frames per second as a number, rather than a useless string
    '''
    fpsDict = {"game": 15.0, "film": 24.0, "pal": 25.0, "ntsc": 30.0, "show": 48.0, "palf": 50.0, "ntscf": 60.0}
    return  fpsDict[cmds.currentUnit(q=True, fullName=True, time=True)]

  

# -----------------------------------------------------------------------------------------
# MENU SETUPS ---
# -----------------------------------------------------------------------------------------
  
def menuSetup(parent='MayaWindow'):
    
    #if exists remove all items, means we can update on the fly by restarting the Red9 pack
    if cmds.menu('redNineMenuItemRoot', exists=True):
        cmds.deleteUI('redNineMenuItemRoot')
        log.info("Rebuilding Existing RedNine Menu")
        
    # parent is an existing window with an existing menuBar?
    if cmds.window(parent, exists=True):
        if not cmds.window(parent, q=True, menuBar=True):
            raise StandardError('given parent for Red9 Menu has no menuBarlayout %s' % parent)
        else:
            cmds.menu('redNineMenuItemRoot', l="RedNine", p=parent, tearOff=True, allowOptionBoxes=True)
            log.info('new Red9 Menu added to current window : %s' % parent)
    # parent is a menuBar?
    elif cmds.menuBarLayout(parent, exists=True):
        cmds.menu('redNineMenuItemRoot', l='RedNine', p=parent, tearOff=True, allowOptionBoxes=True)
        log.info('New Red9 Sound Menu added to current windows menuBar : %s' % parent)
    # parent is an existing menu?
    elif cmds.menu(parent, exists=True):
        cmds.menuItem('redNineMenuItemRoot', l='RedNine', sm=True, p=parent)
        log.info('new Red9 subMenu added to current Menu : %s' % parent)
    else:
        raise StandardError('given parent for Red9 Menu is invalid %s' % parent)
    try:
        cmds.menuItem('redNineProRootItem',
                      l='PRO : PACK', sm=True, p='redNineMenuItemRoot', tearOff=True,i='red9.jpg')
        
        # Holder Menus for Client code
        if get_client_modules():
            cmds.menuItem(divider=True,p='redNineMenuItemRoot')
            for client in get_client_modules():
                cmds.menuItem('redNineClient%sItem' % client,
                              l='CLIENT : %s' % client, sm=True, p='redNineMenuItemRoot', tearOff=True, i='red9.jpg')
        
        cmds.menuItem(divider=True,p='redNineMenuItemRoot')
        
        #Add the main Menu items
        cmds.menuItem('redNineAnimItem',
                      l=LANGUAGE_MAP._MainMenus_.animation_toolkit,
                      ann=LANGUAGE_MAP._MainMenus_.animation_toolkit_ann,
                      p='redNineMenuItemRoot', echoCommand=True,
                      c="import Red9.core.Red9_AnimationUtils as r9Anim;r9Anim.AnimationUI.show()")
        cmds.menuItem('redNineSnapItem',
                      l=LANGUAGE_MAP._MainMenus_.simple_snap,
                      ann=LANGUAGE_MAP._MainMenus_.simple_snap_ann,
                      p='redNineMenuItemRoot', echoCommand=True,
                      c="import Red9.core.Red9_AnimationUtils as r9Anim;r9Anim.AnimFunctions.snap()")
        cmds.menuItem('redNineSearchItem',
                      l=LANGUAGE_MAP._MainMenus_.searchui,
                      ann=LANGUAGE_MAP._MainMenus_.searchui_ann,
                      p='redNineMenuItemRoot', echoCommand=True,
                      c="import Red9.core.Red9_CoreUtils as r9Core;r9Core.FilterNode_UI.show()")
        cmds.menuItem('redNineLockChnsItem',
                      l=LANGUAGE_MAP._MainMenus_.lockchannels,
                      ann=LANGUAGE_MAP._MainMenus_.lockchannels_ann,
                      p='redNineMenuItemRoot', echoCommand=True,
                      c="import Red9.core.Red9_CoreUtils as r9Core;r9Core.LockChannels.UI.show()")
        cmds.menuItem('redNineMetaUIItem',
                      l=LANGUAGE_MAP._MainMenus_.metanodeui,
                      ann=LANGUAGE_MAP._MainMenus_.metanodeui_ann,
                      p='redNineMenuItemRoot', echoCommand=True,
                      c="import Red9.core.Red9_Meta as r9Meta;r9Meta.MClassNodeUI.show()")
        cmds.menuItem('redNineReporterUIItem',
                      l=LANGUAGE_MAP._MainMenus_.scene_reviewer,
                      ann=LANGUAGE_MAP._MainMenus_.scene_reviewer_ann,
                      p='redNineMenuItemRoot', echoCommand=True,
                      c="import Red9.core.Red9_Tools as r9Tools;r9Tools.SceneReviewerUI.show()")
        cmds.menuItem('redNineMoCapItem',
                      l=LANGUAGE_MAP._MainMenus_.mouse_mocap,
                      ann=LANGUAGE_MAP._MainMenus_.mouse_mocap_ann,
                      p='redNineMenuItemRoot', echoCommand=True,
                      c="import Red9.core.Red9_Tools as r9Tools;r9Tools.RecordAttrs.show()")
        cmds.menuItem('redNineRandomizerItem',
                      l=LANGUAGE_MAP._MainMenus_.randomize_keyframes,
                      ann=LANGUAGE_MAP._MainMenus_.randomize_keyframes_ann,
                      p='redNineMenuItemRoot', echoCommand=True,
                      c="import Red9.core.Red9_AnimationUtils as r9Anim;r9Anim.RandomizeKeys.showOptions()")
        cmds.menuItem('redNineFilterCurvesItem',
                      l=LANGUAGE_MAP._MainMenus_.interactive_curve_filter,
                      ann=LANGUAGE_MAP._MainMenus_.interactive_curve_filter_ann,
                      p='redNineMenuItemRoot', echoCommand=True,
                      c="import Red9.core.Red9_AnimationUtils as r9Anim;r9Anim.FilterCurves.show()")
        cmds.menuItem('redNineMirrorUIItem',
                      l=LANGUAGE_MAP._MainMenus_.mirror_setup,
                      ann=LANGUAGE_MAP._MainMenus_.mirror_setup_ann,
                      p='redNineMenuItemRoot', echoCommand=True,
                      c="import Red9.core.Red9_AnimationUtils as r9Anim;r9Anim.MirrorSetup().show()")
        cmds.menuItem('redNineCameraTrackItem',
                      l='CameraTracker',sm=True,p='redNineMenuItemRoot')
        cmds.menuItem('redNineCamerTrackFixedItem',
                      l=LANGUAGE_MAP._MainMenus_.camera_tracker_pan,
                      ann=LANGUAGE_MAP._MainMenus_.camera_tracker_pan_ann,
                      p='redNineCameraTrackItem', echoCommand=True,
                      c="from Red9.core.Red9_AnimationUtils import CameraTracker as camTrack;camTrack.cameraTrackView(fixed=True)")
        if not mayaVersion()<=2009:
            cmds.menuItem(optionBox=True,
                      ann=LANGUAGE_MAP._MainMenus_.tracker_tighness_ann,
                      p='redNineCameraTrackItem', echoCommand=True,
                      c="from Red9.core.Red9_AnimationUtils import CameraTracker as camTrack;camTrack(fixed=True)._showUI()")
        cmds.menuItem('redNineCamerTrackFreeItem',
                      l=LANGUAGE_MAP._MainMenus_.camera_tracker_track,
                      ann=LANGUAGE_MAP._MainMenus_.camera_tracker_track_ann,
                      p='redNineCameraTrackItem', echoCommand=True,
                      c="from Red9.core.Red9_AnimationUtils import CameraTracker as camTrack;camTrack.cameraTrackView(fixed=False)")
        if not mayaVersion()<=2009:
            cmds.menuItem(optionBox=True,
                      ann=LANGUAGE_MAP._MainMenus_.tracker_tighness_ann,
                      p='redNineCameraTrackItem', echoCommand=True,
                      c="from Red9.core.Red9_AnimationUtils import CameraTracker as camTrack;camTrack(fixed=False)._showUI()")
        
        cmds.menuItem(divider=True,p='redNineMenuItemRoot')
        cmds.menuItem('redNineAnimBndItem',
                      l=LANGUAGE_MAP._MainMenus_.animation_binder,
                      ann=LANGUAGE_MAP._MainMenus_.animation_binder_ann,
                      p='redNineMenuItemRoot', echoCommand=True,
                      c="import Red9.core.AnimationBinder as animBnd;animBnd.AnimBinderUI()._UI()")
        cmds.menuItem(divider=True,p='redNineMenuItemRoot')
        
        cmds.menuItem('redNineHomepageItem',
                      l=LANGUAGE_MAP._MainMenus_.red9_homepage,
                      ann=LANGUAGE_MAP._MainMenus_.red9_homepage_ann,
                      p='redNineMenuItemRoot', echoCommand=True,
                      c="Red9.setup.red9_website_home()")
        cmds.menuItem('redNineBlogItem',
                      l=LANGUAGE_MAP._MainMenus_.red9_blog,
                      ann=LANGUAGE_MAP._MainMenus_.red9_blog_ann,
                      p='redNineMenuItemRoot', echoCommand=True,
                      c="Red9.setup.red9_blog()")
        cmds.menuItem('redNineVimeoItem',
                      l=LANGUAGE_MAP._MainMenus_.red9_vimeo,
                      ann=LANGUAGE_MAP._MainMenus_.red9_vimeo_ann,
                      p='redNineMenuItemRoot', echoCommand=True,
                      c="Red9.setup.red9_vimeo()")
        cmds.menuItem('redNineFacebookItem',
                      l=LANGUAGE_MAP._MainMenus_.red9_facebook,
                      ann=LANGUAGE_MAP._MainMenus_.red9_facebook_ann,
                      p='redNineMenuItemRoot', echoCommand=True,
                      c="Red9.setup.red9_facebook()")
        cmds.menuItem('redNineAPIDocItem',
                      l=LANGUAGE_MAP._MainMenus_.red9_api_docs,
                      ann=LANGUAGE_MAP._MainMenus_.red9_api_docs_ann,
                      p='redNineMenuItemRoot', echoCommand=True,
                      c="Red9.setup.red9_apidocs()")
        cmds.menuItem(l=LANGUAGE_MAP._MainMenus_.red9_details,
                      c='Red9.setup.red9ContactInfo()',p='redNineMenuItemRoot')
        cmds.menuItem(divider=True,p='redNineMenuItemRoot')
        
        cmds.menuItem('redNineDebuggerItem', l=LANGUAGE_MAP._MainMenus_.red9_debugger,sm=True,p='redNineMenuItemRoot')
        cmds.menuItem('redNineLostAnimItem', p='redNineDebuggerItem',
                      l=LANGUAGE_MAP._MainMenus_.reconnect_anim,
                      ann=LANGUAGE_MAP._MainMenus_.reconnect_anim_ann,
                      echoCommand=True, c="import Red9.core.Red9_AnimationUtils as r9Anim;r9Anim.ReconnectAnimData().show()")
        cmds.menuItem('redNineOpenCrashItem', p='redNineDebuggerItem',
                      l=LANGUAGE_MAP._MainMenus_.open_last_crash,
                      ann=LANGUAGE_MAP._MainMenus_.open_last_crash_ann,
                      echoCommand=True, c="import Red9.core.Red9_General as r9General;r9General.os_openCrashFile()")
        cmds.menuItem(divider=True,p='redNineDebuggerItem')
        cmds.menuItem('redNineDebugItem',
                      l=LANGUAGE_MAP._MainMenus_.systems_debug,
                      ann=LANGUAGE_MAP._MainMenus_.systems_debug_ann,
                      echoCommand=True, c="Red9.core._setlogginglevel_debug()")
        cmds.menuItem('redNineInfoItem',
                      l=LANGUAGE_MAP._MainMenus_.systems_info,
                      ann=LANGUAGE_MAP._MainMenus_.systems_info_ann,
                      echoCommand=True, c="Red9.core._setlogginglevel_info()")
        cmds.menuItem(divider=True,p='redNineDebuggerItem')
        
        cmds.menuItem(l=LANGUAGE_MAP._MainMenus_.individual_debug, sm=True, p='redNineDebuggerItem')
        cmds.menuItem(l=LANGUAGE_MAP._MainMenus_.debug+" : r9Core",
                      ann=LANGUAGE_MAP._MainMenus_.individual_debug_ann,
                      echoCommand=True, c="Red9.core._setlogginglevel_debug('r9Core')")
        cmds.menuItem(l=LANGUAGE_MAP._MainMenus_.debug+" : r9Meta",
                      ann=LANGUAGE_MAP._MainMenus_.individual_debug_ann,
                      echoCommand=True, c="Red9.core._setlogginglevel_debug('r9Meta')")
        cmds.menuItem(l=LANGUAGE_MAP._MainMenus_.debug+" : r9Anim",
                      ann=LANGUAGE_MAP._MainMenus_.individual_debug_ann,
                      echoCommand=True, c="Red9.core._setlogginglevel_debug('r9Anim')")
        cmds.menuItem(l=LANGUAGE_MAP._MainMenus_.debug+" : r9Tools",
                      ann=LANGUAGE_MAP._MainMenus_.individual_debug_ann,
                      echoCommand=True, c="Red9.core._setlogginglevel_debug('r9Tools')")
        cmds.menuItem(l=LANGUAGE_MAP._MainMenus_.debug+" : r9Pose",
                      ann=LANGUAGE_MAP._MainMenus_.individual_debug_ann,
                      echoCommand=True, c="Red9.core._setlogginglevel_debug('r9Pose')")
        cmds.menuItem(l=LANGUAGE_MAP._MainMenus_.debug+" : r9General",
                      ann=LANGUAGE_MAP._MainMenus_.individual_debug_ann,
                      echoCommand=True, c="Red9.core._setlogginglevel_debug('r9General')")
        cmds.menuItem(l=LANGUAGE_MAP._MainMenus_.debug+" : r9Audio",
                      ann=LANGUAGE_MAP._MainMenus_.individual_debug_ann,
                      echoCommand=True, c="Red9.core._setlogginglevel_debug('r9Audio')")
        cmds.menuItem(l=LANGUAGE_MAP._MainMenus_.individual_info,sm=True,p='redNineDebuggerItem')
        cmds.menuItem(l=LANGUAGE_MAP._MainMenus_.info+" : r9Core",
                      ann=LANGUAGE_MAP._MainMenus_.individual_info_ann,
                      echoCommand=True, c="Red9.core._setlogginglevel_info('r9Core')")
        cmds.menuItem(l=LANGUAGE_MAP._MainMenus_.info+" : r9Meta",
                      ann=LANGUAGE_MAP._MainMenus_.individual_info_ann,
                      echoCommand=True, c="Red9.core._setlogginglevel_info('r9Meta')")
        cmds.menuItem(l=LANGUAGE_MAP._MainMenus_.info+" : r9Anim",
                      ann=LANGUAGE_MAP._MainMenus_.individual_info_ann,
                      echoCommand=True, c="Red9.core._setlogginglevel_info('r9Anim')")
        cmds.menuItem(l=LANGUAGE_MAP._MainMenus_.info+" : r9Tools",
                      ann=LANGUAGE_MAP._MainMenus_.individual_info_ann,
                      echoCommand=True, c="Red9.core._setlogginglevel_info('r9Tools')")
        cmds.menuItem(l=LANGUAGE_MAP._MainMenus_.info+" : r9Pose",
                      ann=LANGUAGE_MAP._MainMenus_.individual_info_ann,
                      echoCommand=True, c="Red9.core._setlogginglevel_info('r9Pose')")
        cmds.menuItem(l=LANGUAGE_MAP._MainMenus_.info+" : r9General",
                      ann=LANGUAGE_MAP._MainMenus_.individual_info_ann,
                      echoCommand=True, c="Red9.core._setlogginglevel_info('r9General')")
        cmds.menuItem(l=LANGUAGE_MAP._MainMenus_.info+" : r9Audio",
                      ann=LANGUAGE_MAP._MainMenus_.individual_info_ann,
                      echoCommand=True, c="Red9.core._setlogginglevel_info('r9Audio')")
        cmds.menuItem(divider=True,p='redNineDebuggerItem')
        cmds.menuItem('redNineReloadItem',l=LANGUAGE_MAP._MainMenus_.systems_reload, p='redNineDebuggerItem',
                      ann=LANGUAGE_MAP._MainMenus_.systems_reload_ann,
                      echoCommand=True, c=reload_Red9)
        cmds.menuItem(divider=True,p='redNineDebuggerItem')
        for language in get_language_maps():
            cmds.menuItem(l=LANGUAGE_MAP._MainMenus_.language+" : %s" % language, c=partial(set_language,language),p='redNineDebuggerItem')
    except:
        raise StandardError('Unable to parent Red9 Menu to given parent %s' % parent)

def addToMayaMenus():
    try:
        # fileMenu additions
        if not cmds.menuItem('redNineOpenFolderItem',q=True,ex=True):
            mainFileMenu=mel.eval("string $f=$gMainFileMenu")
            if not cmds.menu(mainFileMenu, q=True, ni=True):
                mel.eval('buildFileMenu()')
            cmds.menuItem(divider=True,p=mainFileMenu)
            cmds.menuItem('redNineCopyPathItem',
                          l=LANGUAGE_MAP._MainMenus_.copy_to_clipboard,
                          ann=LANGUAGE_MAP._MainMenus_.copy_to_clipboard_ann,
                          p=mainFileMenu,
                          echoCommand=True,
                          c="import maya.cmds as cmds;import Red9.core.Red9_General as r9General;r9General.Clipboard.setText(cmds.file(q=True,sn=True))")
            cmds.menuItem('redNineOpenFolderItem',
                          l=LANGUAGE_MAP._MainMenus_.open_in_explorer,
                          ann=LANGUAGE_MAP._MainMenus_.open_in_explorer_ann,
                          p=mainFileMenu,
                          echoCommand=True,
                          c="import maya.cmds as cmds;import Red9.core.Red9_General as r9General;r9General.os_OpenFileDirectory(cmds.file(q=True,sn=True))")

        # timeSlider additions
        if not cmds.menuItem('redNineTimeSliderCollapseItem',q=True,ex=True):
            if mayaVersion >= 2011:
                mel.eval('updateTimeSliderMenu TimeSliderMenu')
                
            TimeSliderMenu='TimeSliderMenu'
            cmds.menuItem(divider=True, p=TimeSliderMenu)
            cmds.menuItem(subMenu=True, label=LANGUAGE_MAP._MainMenus_.range_submenu, p=TimeSliderMenu)
            
            cmds.menuItem(label=LANGUAGE_MAP._MainMenus_.selectkeys_timerange,
                          ann=LANGUAGE_MAP._MainMenus_.selectkeys_timerange_ann,
                          c='import Red9.core.Red9_AnimationUtils as r9Anim;r9Anim.selectKeysByRange()')
            cmds.menuItem(label=LANGUAGE_MAP._MainMenus_.setrangetoo,
                          ann=LANGUAGE_MAP._MainMenus_.setrangetoo_ann,
                          c='import Red9.core.Red9_AnimationUtils as r9Anim;r9Anim.setTimeRangeToo()')

            cmds.menuItem(divider=True, p=TimeSliderMenu)
            cmds.menuItem('redNineTimeSliderCollapseItem', label=LANGUAGE_MAP._MainMenus_.collapse_time,
                          ann=LANGUAGE_MAP._MainMenus_.collapse_time_ann,
                          c='import Red9.core.Red9_CoreUtils as r9Core;r9Core.timeOffset_collapseUI()',
                          p=TimeSliderMenu)

            cmds.menuItem(subMenu=True, label=LANGUAGE_MAP._MainMenus_.insert_padding, p=TimeSliderMenu)
            cmds.menuItem(label=LANGUAGE_MAP._MainMenus_.pad_selected,
                          ann=LANGUAGE_MAP._MainMenus_.pad_selected_ann,
                          c='import Red9.core.Red9_CoreUtils as r9Core;r9Core.timeOffset_addPadding(scene=False)')
            cmds.menuItem(label=LANGUAGE_MAP._MainMenus_.pad_full_scene,
                          ann=LANGUAGE_MAP._MainMenus_.pad_full_scene_ann,
                          c='import Red9.core.Red9_CoreUtils as r9Core;r9Core.timeOffset_addPadding(scene=True)')
        else:
            log.debug('Red9 Timeslider menus already built')
    except:
        log.debug('gMainFileMenu not found >> catch for unitTesting')


def addAudioMenu(parent=None, rootMenu='redNineTraxRoot'):
    '''
    Red9 Sound Menu setup
    '''
    print 'AudioMenu: given parent : ',parent
    if not parent:
        cmds.menu(rootMenu, l=LANGUAGE_MAP._MainMenus_.sound_red9_sound, tearOff=True, allowOptionBoxes=True)
        print 'New r9Sound Menu added - no specific parent given so adding to whatever menu is currently being built!'
    else:
        # parent is a window containing a menuBar?
        if cmds.window(parent, exists=True):
            if not cmds.window(parent, q=True, menuBar=True):
                raise StandardError('given parent for Red9 Sound Menu has no menuBarlayout %s' % parent)
            else:
                cmds.menu(rootMenu, l=LANGUAGE_MAP._MainMenus_.sound_red9_sound, p=parent, tearOff=True, allowOptionBoxes=True)
                log.info('New Red9 Sound Menu added to current windows menuBar : %s' % parent)
        # parent is a menuBar?
        elif cmds.menuBarLayout(parent, exists=True):
            cmds.menu(rootMenu, l=LANGUAGE_MAP._MainMenus_.sound_red9_sound, p=parent, tearOff=True, allowOptionBoxes=True)
            log.info('New Red9 Sound Menu added to current windows menuBar : %s' % parent)
        # parent is a menu already?
        elif cmds.menu(parent, exists=True):
            cmds.menuItem(rootMenu, l=LANGUAGE_MAP._MainMenus_.sound_red9_sound, sm=True, p=parent, allowOptionBoxes=True)
            log.info('New Red9 Sound subMenu added to current Menu : %s' % parent)
        else:
            raise StandardError('given parent for Red9 Sound Menu is invalid %s' % parent)
    
#    if not parent:
#        print 'new r9Sound Menu added'
#        cmds.menu(rootMenu, l=LANGUAGE_MAP._MainMenus_.sound_red9_sound, tearOff=True, allowOptionBoxes=True)
#    else:
#        print 'new r9Sound Menu added to parent menu', parent
#        cmds.menu(rootMenu, l=LANGUAGE_MAP._MainMenus_.sound_red9_sound, tearOff=True, allowOptionBoxes=True, parent=parent)
        
    cmds.menuItem(l=LANGUAGE_MAP._MainMenus_.sound_offset_manager, p=rootMenu,
                  ann=LANGUAGE_MAP._MainMenus_.sound_offset_manager_ann,
                  c="import Red9.core.Red9_Audio as r9Audio;r9Audio.AudioToolsWrap().show()")
    cmds.menuItem(d=True)
    cmds.menuItem(l=LANGUAGE_MAP._MainMenus_.sound_activate_selected_audio, p=rootMenu,
                  ann=LANGUAGE_MAP._MainMenus_.sound_activate_selected_audio_ann,
                  c="import Red9.core.Red9_Audio as r9Audio;r9Audio.AudioHandler().setActive()")
    cmds.menuItem(l=LANGUAGE_MAP._MainMenus_.sound_set_timeline_to_selected, p=rootMenu,
                  ann=LANGUAGE_MAP._MainMenus_.sound_set_timeline_to_selected_ann,
                  c="import Red9.core.Red9_Audio as r9Audio;r9Audio.AudioHandler().setTimelineToAudio()")
    cmds.menuItem(l=LANGUAGE_MAP._MainMenus_.sound_focus_on_selected, p=rootMenu,
                  ann=LANGUAGE_MAP._MainMenus_.sound_focus_on_selected_ann,
                  c="import Red9.core.Red9_Audio as r9Audio;r9Audio.AudioHandler().setTimelineToAudio();r9Audio.AudioHandler().setActive()")
    cmds.menuItem(d=True)
    cmds.menuItem(l=LANGUAGE_MAP._MainMenus_.sound_mute_selected, p=rootMenu,
                  c="import Red9.core.Red9_Audio as r9Audio;r9Audio.AudioHandler().muteSelected(True)")
    cmds.menuItem(l=LANGUAGE_MAP._MainMenus_.sound_unmute_selected, p=rootMenu,
                  c="import Red9.core.Red9_Audio as r9Audio;r9Audio.AudioHandler().muteSelected(False)")
    cmds.menuItem(l=LANGUAGE_MAP._MainMenus_.sound_lock_selected, p=rootMenu,
                  ann=LANGUAGE_MAP._MainMenus_.sound_lock_selected_ann,
                  c="import Red9.core.Red9_Audio as r9Audio;r9Audio.AudioHandler().lockTimeInputs(True)")
    cmds.menuItem(l=LANGUAGE_MAP._MainMenus_.sound_unlock_selected, p=rootMenu,
                  ann=LANGUAGE_MAP._MainMenus_.sound_unlock_selected_ann,
                  c="import Red9.core.Red9_Audio as r9Audio;r9Audio.AudioHandler().lockTimeInputs(False)")
    cmds.menuItem(l=LANGUAGE_MAP._MainMenus_.sound_delete_selected, p=rootMenu,
                  ann=LANGUAGE_MAP._MainMenus_.sound_delete_selected_ann,
                  c="import Red9.core.Red9_Audio as r9Audio;r9Audio.AudioHandler().deleteSelected()")
    cmds.menuItem(l=LANGUAGE_MAP._MainMenus_.sound_format_soundnode_name, p=rootMenu,
                  ann=LANGUAGE_MAP._MainMenus_.sound_format_soundnode_name_ann,
                  c="import Red9.core.Red9_Audio as r9Audio;r9Audio.AudioHandler().formatNodes_to_Path()")
    cmds.menuItem(d=True)
    cmds.menuItem(l=LANGUAGE_MAP._MainMenus_.sound_combine_audio, p=rootMenu,
                  ann=LANGUAGE_MAP._MainMenus_.sound_combine_audio_ann,
                  c="import Red9.core.Red9_Audio as r9Audio;r9Audio.combineAudio()")
    cmds.menuItem(d=True)
    cmds.menuItem(l=LANGUAGE_MAP._MainMenus_.sound_open_audio_path, p=rootMenu,
                  ann=LANGUAGE_MAP._MainMenus_.sound_open_audio_path_ann,
                  c="import Red9.core.Red9_Audio as r9Audio;r9Audio.AudioNode().openAudioPath()")
    cmds.menuItem(l=LANGUAGE_MAP._MainMenus_.sound_inspect_wav, p=rootMenu,
                  ann=LANGUAGE_MAP._MainMenus_.sound_inspect_wav_ann,
                  c="import Red9.core.Red9_Audio as r9Audio;r9Audio.inspect_wav()")



# -----------------------------------------------------------------------------------------
# GENERAL RED9 DATA ---
# -----------------------------------------------------------------------------------------


def red9ButtonBGC(colour):
    '''
    Generic setting for the main button colours in the UI's
    '''
    if colour==1 or colour=='green':
        return [0.6, 1, 0.6]
    elif colour==2 or colour=='grey':
        return [0.5, 0.5, 0.5]
    elif colour==3 or colour=='red':
        return [1,0.3,0.3]
    elif colour==4 or colour=='white':
        return (0.75,0.8,0.8)
    elif colour==5 or colour=='dark':
        return (0.15,0.25,0.25)
   
def red9ContactInfo(*args):
    import Red9.core.Red9_General as r9General  # lazy load
    result=cmds.confirmDialog(title='Red9_StudioPack : build %f' % red9_getVersion(),
                       message=("Author: Mark Jackson\r\r"+
                                "Technical Animation Director\r\r"+
                                "Contact me at info@red9Consultancy.com for more information\r\r"+
                                "thanks for trying the toolset. If you have any\r"+
                                "suggestions or bugs please let me know!"),
                       button=['Red9Consultancy.com','ChangeLog','Close'],messageAlign='center')
    if result == 'ChangeLog':
        r9General.os_OpenFile(os.path.join(red9ModulePath(),'changeLog.txt'))
    if result =='Red9Consultancy.com':
        r9General.os_OpenFile('http://red9consultancy.com/')
        
def red9Presets():
    '''
    get the default presets dir for all filterSettings.cfg files
    '''
    return os.path.join(red9ModulePath(), 'presets')

def red9Presets_get():
    '''
    generic extraction of all cfg presets from the default location above
    '''
    try:
        configs=[p for p in os.listdir(red9Presets()) if p.endswith('.cfg')]
        configs.sort()
        return configs
    except:
        log.debug('failed to retrieve the presets')
    return []
  
def red9ModulePath():
    '''
    Returns the Main path to the Red9 root module folder
    '''
    return os.path.join(os.path.dirname(os.path.dirname(__file__)),'')

def red9MayaNativePath():
    '''
    Returns the MayaVersioned Hacked script path if valid and found
    '''
    _version=int(mayaVersion())
    path=os.path.join(red9ModulePath(),'startup','maya_native','maya_%s' % str(_version))
   
    if os.path.exists(path):
        return path
    else:
        log.info('Red9MayaHacked Folder not found for this build of Maya : %s' % path)
  
def red9_help(*args):
    '''
    open up the Red9 help docs
    '''
    import Red9.core.Red9_General as r9General  # lazy load
    helpFile=os.path.join(red9ModulePath(),'docs',r'Red9-StudioTools Help.pdf')
    r9General.os_OpenFile(helpFile)
    
def red9_blog(*args):
    '''
    open up the Red9 Blog
    '''
    import Red9.core.Red9_General as r9General  # lazy load
    r9General.os_OpenFile('http://red9-consultancy.blogspot.com/')
    
def red9_website_home(*args):
    '''
    open up the Red9 Consultancy homepage
    '''
    import Red9.core.Red9_General as r9General  # lazy load
    r9General.os_OpenFile('http://red9consultancy.com/')
    
def red9_facebook(*args):
    '''
    open up the Red9 Facebook Page
    '''
    import Red9.core.Red9_General as r9General  # lazy load
    r9General.os_OpenFile('http://www.facebook.com/Red9StudioPack/')
    
def red9_vimeo(*args):
    '''
    open up the Red9 Vimeo Channel
    '''
    import Red9.core.Red9_General as r9General  # lazy load
    r9General.os_OpenFile('https://vimeo.com/user9491246')
  
def red9_apidocs(*args):
    '''
    open up the Red9 Vimeo Channel
    '''
    import Red9.core.Red9_General as r9General  # lazy load
    apidocs=os.path.join(red9ModulePath(),'docs', 'html', 'index.html')
    r9General.os_OpenFile(apidocs)
    
def red9_getVersion():
    return __buildVersionID__

def red9_getAuthor():
    return __author__

def get_pro_pack(*args):
    try:
        #new pro_pack build calls
        import Red9.pro_pack.r9pro as r9pro
        r9pro.r9import('r9wtools')
        import r9wtools
        r9wtools.MailRegistration().show()
    except:
        #legacy
        import Red9.core.Red9_General as r9General  # lazy load
        result=cmds.confirmDialog(title='Red9_StudioPack : build %f' % red9_getVersion(),
                            message=("Red9_ProPack Not Installed!\r\r"+
                                     "Contact info@red9consultancy.com for more information"),
                            button=['Red9Consultancy.com','Get_Pro','Close'],messageAlign='center')
        if result == 'Get_Pro':
            log.warning('Red9 ProPack systems not yet available - watch this space!')
        if result =='Red9Consultancy.com':
            r9General.os_OpenFile('http://red9consultancy.com/')


# -----------------------------------------------------------------------------------------
# BOOT FUNCTIONS ---
# -----------------------------------------------------------------------------------------

def addScriptsPath(path):
    '''
    Add additional folders to the ScriptPath
    '''
    scriptsPath=os.environ.get('MAYA_SCRIPT_PATH')
    
    if os.path.exists(path):
        if not path in scriptsPath:
            log.info('Adding To Script Paths : %s' % path)
            os.environ['MAYA_SCRIPT_PATH']+='%s%s' % (os.pathsep,path)
        else:
            log.info('Red9 Script Path already setup : %s' % path)
    else:
        log.debug('Given Script Path is invalid : %s' % path)
          
def addPluginPath(path=None):
    '''
    Make sure the plugin path has been added. If run as a module
    this will have already been added
    '''
    if not path:
        path=os.path.join(red9ModulePath(),'plug-ins')
    plugPaths=os.environ.get('MAYA_PLUG_IN_PATH')
    if os.path.exists(path) and not path in plugPaths:
        log.info('Adding Red9 Plug-ins to Plugin Paths : %s' % path)
        os.environ['MAYA_PLUG_IN_PATH']+='%s%s' % (os.pathsep,path)
    else:
        log.info('Red9 Plug-in Path already setup')
              
def addIconsPath(path=None):
    '''
    Make sure the icons path has been added. If run as a module
    this will have already been added
    '''
    if not path:
        path=os.path.join(red9ModulePath(),'icons')
    iconsPath=os.environ.get('XBMLANGPATH')
    
    if os.path.exists(path) and not path in iconsPath:
        log.info('Adding Red9 Icons To XBM Paths : %s' % path)
        os.environ['XBMLANGPATH']+='%s%s' % (os.pathsep,path)
    else:
        log.info('Red9 Icons Path already setup')
             
def addPythonPackages():
    '''
    Add the packages folder which is where any external modules
    will be stored
    '''
    red9Packages=os.path.join(red9ModulePath(),'packages')
    
    if not red9Packages in sys.path:
        log.info('Adding Red9Packages To Python Paths : %s' % red9Packages)
        sys.path.append(red9Packages)
    else:
        log.info('Red9Packages Path already setup : %s' % red9Packages)
    
    # PySide Management for pre 2014 x64 builds
    if mayaVersion()<2014.0 and os.path.exists(os.path.join(red9Packages, 'PySide')):
        pysidePath=os.path.join(red9Packages, 'PySide')
        if mayaVersion()==2012.0:
            pysidePath=os.path.join(pysidePath, 'PySide_2012_x64')
        elif mayaVersion()==2013.0:
            pysidePath=os.path.join(pysidePath, 'PySide_2013_x64')
        if os.path.exists(pysidePath) and not pysidePath in sys.path:
            sys.path.append(pysidePath)
            log.info('Adding Red9Packages:PySide To Python Paths : %s' % pysidePath)
            
    # Python compiled folders, if they exists
    if mayaVersion()<=2014 and os.path.exists(os.path.join(red9Packages, 'python2.6')):
        sys.path.append(os.path.join(red9Packages, 'python2.6'))
    if mayaVersion()>=2015 and os.path.exists(os.path.join(red9Packages, 'python2.7')):
        sys.path.append(os.path.join(red9Packages, 'python2.7'))
     
def sourceMelFolderContents(path):
    '''
    source all mel files in a given folder
    '''
    for script in [f for f in os.listdir(path) if f.lower().endswith('.mel')]:
        log.info('Sourcing mel script : %s' % script)
        mel.eval('source %s' % script)


# -----------------------------------------------------------------------------------------
# PRO PACK ---
# -----------------------------------------------------------------------------------------

PRO_PACK_STUBS=None


def pro_pack_path():
    return os.path.join(red9ModulePath(),'pro_pack')

def has_pro_pack():
    '''
    Red9 Pro_Pack is available and activated as user
    '''
    if os.path.exists(pro_pack_path()):
        try:
            #new pro_pack call
            import Red9.pro_pack.r9pro as r9pro
            status=r9pro.checkr9user()
            if status and not issubclass(type(status),str):
                return True
            else:
                return False
        except:
            #we have the pro-pack folder so assume we're running legacy build (Dambusters support)
            return True
    else:
        return False

class ProPack_UIError(Exception):
    '''
    custom exception so we can catch it, this launched the 
    get ProPack UI
    '''
    def __init__(self, *args):
        get_pro_pack()
        
class ProPack_Error(Exception):
    '''
    custom exception so we can catch it. This is an in-function 
    error
    '''
    def __init__(self, *args):
        super(ProPack_Error, self).__init__('ProPack missing from setup!')
           
class pro_pack_missing_stub(object):
    '''
    Exception to raised when the the Pro_Pack is missing 
    and the stubs are called
    '''
    def __init__(self):
        raise ProPack_UIError()
    


# -----------------------------------------------------------------------------------------
# RED9 PRODUCTION MODULES ---
# -----------------------------------------------------------------------------------------
            
def has_internal_systems():
    '''
    Red9 Consultancy internal modules only
    '''
    if os.path.exists(internal_module_path()):
        return True

def internal_module_path():
    return os.path.join(os.path.dirname(os.path.dirname(red9ModulePath())),'Red9_Internals')


# -----------------------------------------------------------------------------------------
# CLIENT MODULES ---
# -----------------------------------------------------------------------------------------

def client_core_path():
    return os.path.join(os.path.dirname(os.path.dirname(red9ModulePath())),'Red9_ClientCore')

def has_client_modules():
    '''
    Red9 Client Modules is the distribution of bespoke code to clients
    that tightly integrates into our ProPack core
    '''
    if os.path.exists(client_core_path()):
        return True

def get_client_modules():
    '''
    get all client modules ready for the boot sequence
    
    #TODO: link this up with a management setup so we can determine
    which client to boot if we have multiple client repositories in the system.
    '''
    clients=[]
    if has_client_modules():
        for f in os.listdir(client_core_path()):
            if os.path.isdir(os.path.join(client_core_path(), f)):
                if not f.startswith('.'):
                    clients.append(f)
    return clients
                
def boot_client_projects():
    '''
    Boot all Client modules found in the Red9_ClientCore dir
    '''
    for client in get_client_modules():
        log.info('Booting Client Module : %s' % client)
        cmds.evalDeferred("import Red9_ClientCore.%s" % client, lp=True)  # Unresolved Import
        
def __reload_clients__():
    '''
    used in the main reload_Red9 call below to ensure that
    the reload sequence is correct for the MetaData registry
    '''
    for client in get_client_modules():
        try:
            path='Red9_ClientCore.%s' % client
            cmds.evalDeferred("import %s;%s._reload()" % (path,path), lp=True)  # Unresolved Import
            log.info('Reloaded Client : "%s"' % path)
        except:
            log.info('Client : "%s" : does not have a _reload func internally' % path)
        

# -----------------------------------------------------------------------------------------
# BOOT CALL ---
# -----------------------------------------------------------------------------------------
    
def start(Menu=True, MayaUIHooks=True, MayaOverloads=True, parentMenu='MayaWindow'):
    '''
    Main entry point for the StudioPack
    @param Menu: Add the Red9 Menu to the Maya Main Menus
    @param MayUIHooks: Add the Red9 hooks to Maya Native UI's
    @param MayaOverloads: run the Maya native script hacks for Red9 - integrates into native Maya ui's
    '''
    log.info('Red9 StudioPack v%s : author: %s' % (red9_getVersion(), red9_getAuthor()))
    log.info('Red9 StudioPack Setup Calls :: Booting from >> %s' % red9ModulePath())
    
    #check for current builds
#    currentBuild=False
#    try:
#        currentBuild = mel.eval('$temp=$buildInstalled')
#    except:
#        print 'Red9 : version not found'
#
#    if currentBuild:
#        print 'Red9 : StudioPack already found : v', currentBuild
#        if currentBuild<=red9_getVersion():
#            print 'Red9 StudioPack Start Aborted : v%f is already installed' % currentBuild
#            return
#    else:
#        print 'Red9 : no version currently loaded'
            

    #Ensure the Plug-in and Icon paths are up
    addPluginPath()
    addIconsPath()
    #Need to add a Mel Folder to the scripts path
    addScriptsPath(os.path.join(red9ModulePath(),'core'))
    
    #Add the Packages folder
    addPythonPackages()
    
    if not cmds.about(batch=True):
        if Menu:
            try:
                menuSetup(parent=parentMenu)
            except:
                log.debug('Red9 main menu Build Failed!')
                
        if MayaUIHooks:
            #Source Maya Hacked Mel files
            hacked=red9MayaNativePath()
            if hacked and MayaOverloads:
                addScriptsPath(os.path.join(red9ModulePath(),'startup','maya_native'))
                addScriptsPath(hacked)
                try:
                    mel.eval('source Red9_MelCore')
                    sourceMelFolderContents(hacked)
                except StandardError, error:
                    log.info(error)
        
            #Add custom items to standard built Maya menus
            addToMayaMenus()

    log.info('Red9 StudioPack Complete!')
    
    # Rearrangement of the Boot core systems to better structure the boot sequence
    
    # Boot main Red9.core
    cmds.evalDeferred("import Red9.core", lp=True)

    # Boot the Pro_Pack
    if has_pro_pack():
        cmds.evalDeferred("import Red9.pro_pack", lp=True)  # Unresolved Import
    # Boot the Red9_Internal systems
    if has_internal_systems():
        cmds.evalDeferred("import Red9_Internals", lp=True)  # Unresolved Import
    # Boot Client Codebases
    if has_client_modules():
        boot_client_projects()
        #cmds.evalDeferred("import Red9_ClientCore", lp=True)  # Unresolved Import
           
           
def reload_Red9(*args):
    '''
    careful reload of the systems to maintain the integrity of the 
    MetaData registry setups for pro_pack, client_core and internals
    '''
    #global LANGUAGE_MAP
    #reload(LANGUAGE_MAP)
    import Red9.core
    Red9.core._reload()
    
    if has_pro_pack():
        import Red9.pro_pack.core
        Red9.pro_pack.core._reload()
        
    if has_internal_systems():
        import Red9_Internals
        Red9_Internals._reload()

    if has_client_modules():
        __reload_clients__()


PRO_PACK_STUBS=pro_pack_missing_stub


