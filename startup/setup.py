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

THIS SHOULD NOT REQUIRE ANY OF THE RED9.core modules
'''
from Red9.startup import language_packs


__author__ = 'Mark Jackson'
__buildVersionID__ = 1.5
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

 Release         -version    -api     python    -qt       prefs      release    info
 -----------------------------------------------------------------------------------
 
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
------------------------------------------------------------------------------------
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
        print 'importing language map : %s' % language
        LANGUAGE_MAP = imp.load_source('language', os.path.join(language_path, language+'.py'))

set_language()


#=========================================================================================
# General Maya data  ---------------------------------------------------------------------
#=========================================================================================
 
def mayaVersion():
    #need to manage this better and use the API version,
    #eg: 2013.5 returns 2013
    return mel.eval('getApplicationVersionAsFloat')

def mayaVersionRelease():
    return cmds.about(api=True)

def mayaVersionQT():
    try:
        return cmds.about(qt=True)
    except:
        pass
    
def mayaPrefs():
    '''
    Root of Maya prefs folder
    '''
    return os.path.dirname(cmds.about(env=True))

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

def getCurrentFPS():
    '''
    returns the current frames per second as a number, rather than a useless string
    '''
    fpsDict = {"game": 15.0, "film": 24.0, "pal": 25.0, "ntsc": 30.0, "show": 48.0, "palf": 50.0, "ntscf": 60.0}
    return  fpsDict[cmds.currentUnit(q=True, fullName=True, time=True)]

  
# Menu Builders ------------------------------------------------------------------------
   
def menuSetup(parent='MayaWindow'):
    
    #if exists remove all items, means we can update on the fly by restarting the Red9 pack
    if cmds.menu('redNineMenuItemRoot', exists=True):
        cmds.deleteUI('redNineMenuItemRoot')
        log.info("Rebuilding Existing RedNine Menu")
        
    if cmds.window(parent, exists=True):
        if not cmds.window(parent, q=True, menuBar=True):
            #parent=cmds.window(parent, edit=True, menuBar=True)
            raise StandardError('given parent for Red9 Menu has no menuBarlayout %s' % parent)
        else:
            cmds.menu('redNineMenuItemRoot', l="RedNine", p=parent, tearOff=True, allowOptionBoxes=True)
            log.info('new Red9 Menu added to current window : %s' % parent)
    elif cmds.menu(parent, exists=True):
        cmds.menuItem('redNineMenuItemRoot', l='RedNine', sm=True, p=parent)
        log.info('new Red9 subMenu added to current Menu : %s' % parent)
    else:
        raise StandardError('given parent for Red9 Menu is invalid %s' % parent)
    try:
        #Add the main Menu items
        cmds.menuItem('redNineAnimItem',
                      l=LANGUAGE_MAP.MainMenus.animation_toolkit,
                      ann=LANGUAGE_MAP.MainMenus.animation_toolkit_ann,
                      p='redNineMenuItemRoot', echoCommand=True,
                      c="import Red9.core.Red9_AnimationUtils as r9Anim;r9Anim.AnimationUI.show()")
        cmds.menuItem('redNineSnapItem',
                      l=LANGUAGE_MAP.MainMenus.simple_snap,
                      ann=LANGUAGE_MAP.MainMenus.simple_snap_ann,
                      p='redNineMenuItemRoot', echoCommand=True,
                      c="import Red9.core.Red9_AnimationUtils as r9Anim;r9Anim.AnimFunctions.snap()")
        cmds.menuItem('redNineSearchItem',
                      l=LANGUAGE_MAP.MainMenus.searchui,
                      ann=LANGUAGE_MAP.MainMenus.searchui_ann,
                      p='redNineMenuItemRoot', echoCommand=True,
                      c="import Red9.core.Red9_CoreUtils as r9Core;r9Core.FilterNode_UI.show()")
        cmds.menuItem('redNineLockChnsItem',
                      l=LANGUAGE_MAP.MainMenus.lockchannels,
                      ann=LANGUAGE_MAP.MainMenus.lockchannels_ann,
                      p='redNineMenuItemRoot', echoCommand=True,
                      c="import Red9.core.Red9_CoreUtils as r9Core;r9Core.LockChannels.UI.show()")
        cmds.menuItem('redNineMetaUIItem',
                      l=LANGUAGE_MAP.MainMenus.metanodeui,
                      ann=LANGUAGE_MAP.MainMenus.metanodeui_ann,
                      p='redNineMenuItemRoot', echoCommand=True,
                      c="import Red9.core.Red9_Meta as r9Meta;r9Meta.MClassNodeUI.show()")
        cmds.menuItem('redNineReporterUIItem',
                      l=LANGUAGE_MAP.MainMenus.scene_reviewer,
                      ann=LANGUAGE_MAP.MainMenus.scene_reviewer_ann,
                      p='redNineMenuItemRoot', echoCommand=True,
                      c="import Red9.core.Red9_Tools as r9Tools;r9Tools.SceneReviewerUI.show()")
        cmds.menuItem('redNineMoCapItem',
                      l=LANGUAGE_MAP.MainMenus.mouse_mocap,
                      ann=LANGUAGE_MAP.MainMenus.mouse_mocap_ann,
                      p='redNineMenuItemRoot', echoCommand=True,
                      c="import Red9.core.Red9_Tools as r9Tools;r9Tools.RecordAttrs.show()")
        cmds.menuItem('redNineRandomizerItem',
                      l=LANGUAGE_MAP.MainMenus.randomize_keyframes,
                      ann=LANGUAGE_MAP.MainMenus.randomize_keyframes_ann,
                      p='redNineMenuItemRoot', echoCommand=True,
                      c="import Red9.core.Red9_AnimationUtils as r9Anim;r9Anim.RandomizeKeys.showOptions()")
        cmds.menuItem('redNineFilterCurvesItem',
                      l=LANGUAGE_MAP.MainMenus.interactive_curve_filter,
                      ann=LANGUAGE_MAP.MainMenus.interactive_curve_filter_ann,
                      p='redNineMenuItemRoot', echoCommand=True,
                      c="import Red9.core.Red9_AnimationUtils as r9Anim;r9Anim.FilterCurves.show()")
        cmds.menuItem('redNineMirrorUIItem',
                      l=LANGUAGE_MAP.MainMenus.mirror_setup,
                      ann=LANGUAGE_MAP.MainMenus.mirror_setup_ann,
                      p='redNineMenuItemRoot', echoCommand=True,
                      c="import Red9.core.Red9_AnimationUtils as r9Anim;r9Anim.MirrorSetup().show()")
        cmds.menuItem('redNineCameraTrackItem',
                      l='CameraTracker',sm=True,p='redNineMenuItemRoot')
        cmds.menuItem('redNineCamerTrackFixedItem',
                      l=LANGUAGE_MAP.MainMenus.camera_tracker_pan,
                      ann=LANGUAGE_MAP.MainMenus.camera_tracker_pan_ann,
                      p='redNineCameraTrackItem', echoCommand=True,
                      c="from Red9.core.Red9_AnimationUtils import CameraTracker as camTrack;camTrack.cameraTrackView(fixed=True)")
        if not mayaVersion()<=2009:
            cmds.menuItem(optionBox=True,
                      ann=LANGUAGE_MAP.MainMenus.tracker_tighness_ann,
                      p='redNineCameraTrackItem', echoCommand=True,
                      c="from Red9.core.Red9_AnimationUtils import CameraTracker as camTrack;camTrack(fixed=True)._showUI()")
        cmds.menuItem('redNineCamerTrackFreeItem',
                      l=LANGUAGE_MAP.MainMenus.camera_tracker_track,
                      ann=LANGUAGE_MAP.MainMenus.camera_tracker_track_ann,
                      p='redNineCameraTrackItem', echoCommand=True,
                      c="from Red9.core.Red9_AnimationUtils import CameraTracker as camTrack;camTrack.cameraTrackView(fixed=False)")
        if not mayaVersion()<=2009:
            cmds.menuItem(optionBox=True,
                      ann=LANGUAGE_MAP.MainMenus.tracker_tighness_ann,
                      p='redNineCameraTrackItem', echoCommand=True,
                      c="from Red9.core.Red9_AnimationUtils import CameraTracker as camTrack;camTrack(fixed=False)._showUI()")
        
        cmds.menuItem(divider=True,p='redNineMenuItemRoot')
        cmds.menuItem('redNineAnimBndItem',
                      l=LANGUAGE_MAP.MainMenus.animation_binder,
                      ann=LANGUAGE_MAP.MainMenus.animation_binder_ann,
                      p='redNineMenuItemRoot', echoCommand=True,
                      c="import Red9.core.AnimationBinder as animBnd;animBnd.AnimBinderUI()._UI()")
        cmds.menuItem(divider=True,p='redNineMenuItemRoot')
        
        cmds.menuItem('redNineHomepageItem',
                      l=LANGUAGE_MAP.MainMenus.red9_homepage,
                      ann=LANGUAGE_MAP.MainMenus.red9_homepage_ann,
                      p='redNineMenuItemRoot', echoCommand=True,
                      c="Red9.setup.red9_website_home()")
        cmds.menuItem('redNineBlogItem',
                      l=LANGUAGE_MAP.MainMenus.red9_blog,
                      ann=LANGUAGE_MAP.MainMenus.red9_blog_ann,
                      p='redNineMenuItemRoot', echoCommand=True,
                      c="Red9.setup.red9_blog()")
        cmds.menuItem('redNineVimeoItem',
                      l=LANGUAGE_MAP.MainMenus.red9_vimeo,
                      ann=LANGUAGE_MAP.MainMenus.red9_vimeo_ann,
                      p='redNineMenuItemRoot', echoCommand=True,
                      c="Red9.setup.red9_vimeo()")
        cmds.menuItem('redNineFacebookItem',
                      l=LANGUAGE_MAP.MainMenus.red9_facebook,
                      ann=LANGUAGE_MAP.MainMenus.red9_facebook_ann,
                      p='redNineMenuItemRoot', echoCommand=True,
                      c="Red9.setup.red9_facebook()")
        cmds.menuItem('redNineAPIDocItem',
                      l=LANGUAGE_MAP.MainMenus.red9_api_docs,
                      ann=LANGUAGE_MAP.MainMenus.red9_api_docs_ann,
                      p='redNineMenuItemRoot', echoCommand=True,
                      c="Red9.setup.red9_apidocs()")
        cmds.menuItem(l=LANGUAGE_MAP.MainMenus.red9_details,
                      c='Red9.setup.red9ContactInfo()',p='redNineMenuItemRoot')
        cmds.menuItem(divider=True,p='redNineMenuItemRoot')
        
        cmds.menuItem('redNineDebuggerItem', l=LANGUAGE_MAP.MainMenus.red9_debugger,sm=True,p='redNineMenuItemRoot')
        cmds.menuItem('redNineLostAnimItem', p='redNineDebuggerItem',
                      l=LANGUAGE_MAP.MainMenus.reconnect_anim,
                      ann=LANGUAGE_MAP.MainMenus.reconnect_anim_ann,
                      echoCommand=True, c="import Red9.core.Red9_AnimationUtils as r9Anim;r9Anim.ReconnectAnimData().show()")
        cmds.menuItem('redNineOpenCrashItem', p='redNineDebuggerItem',
                      l=LANGUAGE_MAP.MainMenus.open_last_crash,
                      ann=LANGUAGE_MAP.MainMenus.open_last_crash_ann,
                      echoCommand=True, c="import Red9.core.Red9_General as r9General;r9General.os_openCrashFile()")
        cmds.menuItem(divider=True,p='redNineDebuggerItem')
        cmds.menuItem('redNineDebugItem',
                      l=LANGUAGE_MAP.MainMenus.systems_debug,
                      ann=LANGUAGE_MAP.MainMenus.systems_debug_ann,
                      echoCommand=True, c="Red9.core._setlogginglevel_debug()")
        cmds.menuItem('redNineInfoItem',
                      l=LANGUAGE_MAP.MainMenus.systems_info,
                      ann=LANGUAGE_MAP.MainMenus.systems_info_ann,
                      echoCommand=True, c="Red9.core._setlogginglevel_info()")
        cmds.menuItem(divider=True,p='redNineDebuggerItem')
        
        cmds.menuItem(l=LANGUAGE_MAP.MainMenus.individual_debug, sm=True, p='redNineDebuggerItem')
        cmds.menuItem(l=LANGUAGE_MAP.MainMenus.debug+" : r9Core",
                      ann=LANGUAGE_MAP.MainMenus.individual_debug_ann,
                      echoCommand=True, c="Red9.core._setlogginglevel_debug('r9Core')")
        cmds.menuItem(l=LANGUAGE_MAP.MainMenus.debug+" : r9Meta",
                      ann=LANGUAGE_MAP.MainMenus.individual_debug_ann,
                      echoCommand=True, c="Red9.core._setlogginglevel_debug('r9Meta')")
        cmds.menuItem(l=LANGUAGE_MAP.MainMenus.debug+" : r9Anim",
                      ann=LANGUAGE_MAP.MainMenus.individual_debug_ann,
                      echoCommand=True, c="Red9.core._setlogginglevel_debug('r9Anim')")
        cmds.menuItem(l=LANGUAGE_MAP.MainMenus.debug+" : r9Tools",
                      ann=LANGUAGE_MAP.MainMenus.individual_debug_ann,
                      echoCommand=True, c="Red9.core._setlogginglevel_debug('r9Tools')")
        cmds.menuItem(l=LANGUAGE_MAP.MainMenus.debug+" : r9Pose",
                      ann=LANGUAGE_MAP.MainMenus.individual_debug_ann,
                      echoCommand=True, c="Red9.core._setlogginglevel_debug('r9Pose')")
        cmds.menuItem(l=LANGUAGE_MAP.MainMenus.debug+" : r9General",
                      ann=LANGUAGE_MAP.MainMenus.individual_debug_ann,
                      echoCommand=True, c="Red9.core._setlogginglevel_debug('r9General')")
        cmds.menuItem(l=LANGUAGE_MAP.MainMenus.debug+" : r9Audio",
                      ann=LANGUAGE_MAP.MainMenus.individual_debug_ann,
                      echoCommand=True, c="Red9.core._setlogginglevel_debug('r9Audio')")
        cmds.menuItem(l=LANGUAGE_MAP.MainMenus.individual_info,sm=True,p='redNineDebuggerItem')
        cmds.menuItem(l=LANGUAGE_MAP.MainMenus.info+" : r9Core",
                      ann=LANGUAGE_MAP.MainMenus.individual_info_ann,
                      echoCommand=True, c="Red9.core._setlogginglevel_info('r9Core')")
        cmds.menuItem(l=LANGUAGE_MAP.MainMenus.info+" : r9Meta",
                      ann=LANGUAGE_MAP.MainMenus.individual_info_ann,
                      echoCommand=True, c="Red9.core._setlogginglevel_info('r9Meta')")
        cmds.menuItem(l=LANGUAGE_MAP.MainMenus.info+" : r9Anim",
                      ann=LANGUAGE_MAP.MainMenus.individual_info_ann,
                      echoCommand=True, c="Red9.core._setlogginglevel_info('r9Anim')")
        cmds.menuItem(l=LANGUAGE_MAP.MainMenus.info+" : r9Tools",
                      ann=LANGUAGE_MAP.MainMenus.individual_info_ann,
                      echoCommand=True, c="Red9.core._setlogginglevel_info('r9Tools')")
        cmds.menuItem(l=LANGUAGE_MAP.MainMenus.info+" : r9Pose",
                      ann=LANGUAGE_MAP.MainMenus.individual_info_ann,
                      echoCommand=True, c="Red9.core._setlogginglevel_info('r9Pose')")
        cmds.menuItem(l=LANGUAGE_MAP.MainMenus.info+" : r9General",
                      ann=LANGUAGE_MAP.MainMenus.individual_info_ann,
                      echoCommand=True, c="Red9.core._setlogginglevel_info('r9General')")
        cmds.menuItem(l=LANGUAGE_MAP.MainMenus.info+" : r9Audio",
                      ann=LANGUAGE_MAP.MainMenus.individual_info_ann,
                      echoCommand=True, c="Red9.core._setlogginglevel_info('r9Audio')")
        cmds.menuItem(divider=True,p='redNineDebuggerItem')
        cmds.menuItem('redNineReloadItem',l=LANGUAGE_MAP.MainMenus.systems_reload, p='redNineDebuggerItem',
                      ann=LANGUAGE_MAP.MainMenus.systems_reload_ann,
                      echoCommand=True, c=reload_Red9)  # "Red9.core._reload()")
        cmds.menuItem(divider=True,p='redNineDebuggerItem')
        for language in get_language_maps():
            cmds.menuItem(l=LANGUAGE_MAP.MainMenus.language+" : %s" % language, c=partial(set_language,language),p='redNineDebuggerItem')
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
            cmds.menuItem('redNineOpenFolderItem',
                          l="Red9: Open in Explorer",
                          ann="Open the folder containing the current Maya Scene",
                          p=mainFileMenu,
                          echoCommand=True,
                          c="import maya.cmds as cmds;import Red9.core.Red9_General as r9General;r9General.os_OpenFileDirectory(cmds.file(q=True,sn=True))")
        # timeSlider additions
        if not cmds.menuItem('redNineTimeSliderCollapseItem',q=True,ex=True):
            if mayaVersion >= 2011:
                mel.eval('updateTimeSliderMenu TimeSliderMenu')
                
            TimeSliderMenu='TimeSliderMenu'
            cmds.menuItem(divider=True, p=TimeSliderMenu)
            cmds.menuItem(subMenu=True, label='Red9: Collapse Range', p=TimeSliderMenu)
            cmds.menuItem('redNineTimeSliderCollapseItem', label='Collapse : Selected Only',
                          ann='Collapse the keys in the selected TimeRange (Red highlighted)',
                          c='import Red9.core.Red9_CoreUtils as r9Core;r9Core.timeOffset_collapse(scene=False)')
            cmds.menuItem(label='Collapse : Full Scene',
                          ann='Collapse the keys in the selected TimeRange (Red highlighted)',
                          c='import Red9.core.Red9_CoreUtils as r9Core;r9Core.timeOffset_collapse(scene=True)')

            cmds.menuItem(subMenu=True, label='Red9: Insert Padding', p=TimeSliderMenu)
            cmds.menuItem(label='Pad : Selected Only',
                          ann='Insert time in the selected TimeRange (Red highlighted)',
                          c='import Red9.core.Red9_CoreUtils as r9Core;r9Core.timeOffset_addPadding(scene=False)')
            cmds.menuItem(label='Pad : Full Scene',
                          ann='Insert time in the selected TimeRange (Red highlighted)',
                          c='import Red9.core.Red9_CoreUtils as r9Core;r9Core.timeOffset_addPadding(scene=True)')
        else:
            log.debug('Red9 Timeslider menus already built')
    except:
        log.debug('gMainFileMenu not found >> catch for unitTesting')


# General Pack Data --------------------------------------------------------------------

def red9ButtonBGC(colour):
    '''
    Generic setting for the main button colours in the UI's
    '''
    if colour==1:
        return [0.6, 0.9, 0.65]
    if colour==2:
        return [0.5, 0.5, 0.5]
   
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
    return os.path.join(red9ModulePath(), 'presets')
    
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
    import Red9.core.Red9_General as r9General  # lazy load
    result=cmds.confirmDialog(title='Red9_StudioPack : build %f' % red9_getVersion(),
                       message=("Red9_ProPack Not Installed!\r\r"+
                                "Contact info@red9consultancy.com for more information"),
                       button=['Red9Consultancy.com','Get_Pro','Close'],messageAlign='center')
    if result == 'Get_Pro':
        log.warning('Red9 ProPack systems not yet available - watch this space!')
    if result =='Red9Consultancy.com':
        r9General.os_OpenFile('http://red9consultancy.com/')

# BOOT FUNCTS - Add and Build --------------------------------------------------------------
    
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
          
def addPluginPath():
    '''
    Make sure the plugin path has been added. If run as a module
    this will have already been added
    '''
    path=os.path.join(red9ModulePath(),'plug-ins')
    plugPaths=os.environ.get('MAYA_PLUG_IN_PATH')
    
    if not path in plugPaths:
        log.info('Adding Red9 Plug-ins to Plugin Paths : %s' % path)
        os.environ['MAYA_PLUG_IN_PATH']+='%s%s' % (os.pathsep,path)
    else:
        log.info('Red9 Plug-in Path already setup')
              
def addIconsPath():
    '''
    Make sure the icons path has been added. If run as a module
    this will have already been added
    '''
    path=os.path.join(red9ModulePath(),'icons')
    iconsPath=os.environ.get('XBMLANGPATH')
    
    if not path in iconsPath:
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
     
def sourceMelFolderContents(path):
    '''
    source all mel files in a given folder
    '''
    for script in [f for f in os.listdir(path) if f.lower().endswith('.mel')]:
        log.info('Sourcing mel script : %s' % script)
        mel.eval('source %s' % script)


#=========================================================================================
# PRO PACK ------------------------------------------------------------------------------
#=========================================================================================

PRO_PACK_STUBS=None

def has_pro_pack():
    '''
    Red9 Pro_Pack is available
    '''
    if os.path.exists(os.path.join(red9ModulePath(),'pro_pack')):
        return True

class ProPack_Error(Exception):
    '''
    custom exception so we can catch it
    '''
    def __init__(self):
        get_pro_pack()
        
class pro_pack_missing_stub(object):
    '''
    Exception to raised when the the Pro_Pack is missing 
    and the stubs are called
    '''
    def __init__(self):
        raise ProPack_Error()

             
def has_internal_systems():
    '''
    Red9 Consultancy internal modules only
    '''
    if os.path.exists(os.path.join(os.path.dirname(os.path.dirname(red9ModulePath())),'Red9_Internals')):
        return True

      
#=========================================================================================
# BOOT CALL ------------------------------------------------------------------------------
#=========================================================================================
    
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
    
    if has_pro_pack():
        cmds.evalDeferred("import Red9.pro_pack", lp=True)  # Unresolved Import
    if has_internal_systems():
        cmds.evalDeferred("import Red9_Internals", lp=True)  # Unresolved Import
           
def reload_Red9(*args):
    global LANGUAGE_MAP
    reload(LANGUAGE_MAP)
    import Red9.core
    Red9.core._reload()


PRO_PACK_STUBS=pro_pack_missing_stub


