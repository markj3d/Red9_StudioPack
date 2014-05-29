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


__author__ = 'Mark Jackson'
__buildVersionID__ = 1.43
installedVersion= False

import sys
import os
import maya.cmds as cmds
import maya.mel as mel

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

------------------------------------------------------------------------------------
'''

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

def mayaUpAxis():
    import maya.OpenMaya as OpenMaya
    vect=OpenMaya.MGlobal.upAxis()
    if vect.z:
        return 'z'
    if vect.y:
        return 'y'
    
    
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
        cmds.menuItem('redNineAnimItem',l="AnimationToolkit",
                      ann="Main Red9 Animation Toolkit - Note: CTRL+click opens this non-docked",
                      p='redNineMenuItemRoot', echoCommand=True,
                      c="import Red9.core.Red9_AnimationUtils as r9Anim;r9Anim.AnimationUI.show()")
        cmds.menuItem('redNineSnapItem',l="Simple Snap",ann="Simple Snap transforms",
                      p='redNineMenuItemRoot', echoCommand=True,
                      c="import Red9.core.Red9_AnimationUtils as r9Anim;r9Anim.AnimFunctions.snap()")
        cmds.menuItem('redNineSearchItem',l="SearchUI",ann="Main Red9 Search toolkit",
                      p='redNineMenuItemRoot', echoCommand=True,
                      c="import Red9.core.Red9_CoreUtils as r9Core;r9Core.FilterNode_UI.show()")
        cmds.menuItem('redNineLockChnsItem',l="LockChannels",ann="Manage Channel States",
                      p='redNineMenuItemRoot', echoCommand=True,
                      c="import Red9.core.Red9_CoreUtils as r9Core;r9Core.LockChannels.UI.show()")
        cmds.menuItem('redNineMetaUIItem',l="MetaNodeUI",ann="MetaNode Scene Searcher",
                      p='redNineMenuItemRoot', echoCommand=True,
                      c="import Red9.core.Red9_Meta as r9Meta;r9Meta.MClassNodeUI.show()")
        cmds.menuItem('redNineReporterUIItem',l="Scene Reviewer",ann="Launch the Scene Review Reporter",
                      p='redNineMenuItemRoot', echoCommand=True,
                      c="import Red9.core.Red9_Tools as r9Tools;r9Tools.SceneReviewerUI.show()")
        cmds.menuItem('redNineMoCapItem',l="MouseMoCap",ann="Record the Mouse Input to selected object",
                      p='redNineMenuItemRoot', echoCommand=True,
                      c="import Red9.core.Red9_Tools as r9Tools;r9Tools.RecordAttrs.show()")
        cmds.menuItem('redNineRandomizerItem',l="Randomize Keyframes",
                      ann="Randomize selected Keys - also available in the GraphEditor>curve menu",
                      p='redNineMenuItemRoot', echoCommand=True,
                      c="import Red9.core.Red9_AnimationUtils as r9Anim;r9Anim.RandomizeKeys.showOptions()")
        
        cmds.menuItem('redNineFilterCurvesItem',l="Interactive Curve Filter",
                      ann="Interactive Curve Filter - also available in the GraphEditor>curve menu",
                      p='redNineMenuItemRoot', echoCommand=True,
                      c="import Red9.core.Red9_AnimationUtils as r9Anim;r9Anim.FilterCurves.show()")
        
    
        cmds.menuItem('redNineMirrorUIItem',l="MirrorSetup",
                      ann="Temp UI to help setup the Mirror Markers on a rig",
                      p='redNineMenuItemRoot', echoCommand=True,
                      c="import Red9.core.Red9_AnimationUtils as r9Anim;r9Anim.MirrorSetup().show()")
        
        cmds.menuItem('redNineCameraTrackItem',l='CameraTracker',sm=True,p='redNineMenuItemRoot')
        cmds.menuItem('redNineCamerTrackFixedItem',l="CameraTracker > panning",
                      ann="Panning Camera : CameraTrack the current view with the current camera",
                      p='redNineCameraTrackItem', echoCommand=True,
                      c="from Red9.core.Red9_AnimationUtils import CameraTracker as camTrack;camTrack.cameraTrackView(fixed=True)")
        if not mayaVersion()<=2009:
            cmds.menuItem(optionBox=True,
                      ann="setup the tracker step and tightness",
                      p='redNineCameraTrackItem', echoCommand=True,
                      c="from Red9.core.Red9_AnimationUtils import CameraTracker as camTrack;camTrack(fixed=True)._showUI()")
        cmds.menuItem('redNineCamerTrackFreeItem',l="CameraTracker > tracking",
                      ann="Tracking Camera : CameraTrack the current view with the current camera",
                      p='redNineCameraTrackItem', echoCommand=True,
                      c="from Red9.core.Red9_AnimationUtils import CameraTracker as camTrack;camTrack.cameraTrackView(fixed=False)")
        if not mayaVersion()<=2009:
            cmds.menuItem(optionBox=True,
                      ann="setup the tracker step and tightness",
                      p='redNineCameraTrackItem', echoCommand=True,
                      c="from Red9.core.Red9_AnimationUtils import CameraTracker as camTrack;camTrack(fixed=False)._showUI()")
        
        cmds.menuItem(divider=True,p='redNineMenuItemRoot')
        cmds.menuItem('redNineAnimBndItem',l="Animation Binder",ann="My Autodesk MasterClass toolset",
                      p='redNineMenuItemRoot', echoCommand=True,
                      c="import Red9.core.AnimationBinder as animBnd;animBnd.AnimBinderUI()._UI()")
        cmds.menuItem(divider=True,p='redNineMenuItemRoot')
        cmds.menuItem('redNineBlogItem',l="Red9_Blog",ann="Open Red9Blog",
                      p='redNineMenuItemRoot', echoCommand=True,
                      c="Red9.setup.red9_blog()")
        cmds.menuItem('redNineVimeoItem',l="Red9_Vimeo Channel",ann="Open Red9Vimeo Channel",
                      p='redNineMenuItemRoot', echoCommand=True,
                      c="Red9.setup.red9_vimeo()")
        cmds.menuItem('redNineFacebookItem',l="Red9_Facebook",ann="Open Red9Facebook page",
                      p='redNineMenuItemRoot', echoCommand=True,
                      c="Red9.setup.red9_facebook()")
        cmds.menuItem('redNineAPIDocItem',l="Red9_API Docs",ann="Open Red9 API code reference page",
                      p='redNineMenuItemRoot', echoCommand=True,
                      c="Red9.setup.red9_apidocs()")
        cmds.menuItem(l="Red9_Details",c='Red9.setup.red9ContactInfo()',p='redNineMenuItemRoot')
        cmds.menuItem(divider=True,p='redNineMenuItemRoot')
        
        cmds.menuItem('redNineDebuggerItem',l='Red9 Debugger',sm=True,p='redNineMenuItemRoot')
        cmds.menuItem('redNineLostAnimItem',l="Reconnect Lost Anim", p='redNineDebuggerItem',
                      ann="Reconnect lost animation data via a chSet - see my blog post for more details",
                      echoCommand=True, c="import Red9.core.Red9_AnimationUtils as r9Anim;r9Anim.reConnectReferencedAnimData()")
        cmds.menuItem(divider=True,p='redNineDebuggerItem')
        cmds.menuItem('redNineDebugItem',l="systems: DEBUG",ann="Turn all the logging to Debug",
                      echoCommand=True, c="Red9.core._setlogginglevel_debug()")
        cmds.menuItem('redNineInfoItem',l="systems: INFO",ann="Turn all the logging to Info only",
                      echoCommand=True, c="Red9.core._setlogginglevel_info()")
        cmds.menuItem(divider=True,p='redNineDebuggerItem')
        
        cmds.menuItem(l='Individual DEBUG',sm=True,p='redNineDebuggerItem')
        cmds.menuItem(l="Debug : r9Core",ann="Turn all the logging to Debug",
                      echoCommand=True, c="Red9.core._setlogginglevel_debug('r9Core')")
        cmds.menuItem(l="Debug : r9Meta",ann="Turn all the logging to Debug",
                      echoCommand=True, c="Red9.core._setlogginglevel_debug('r9Meta')")
        cmds.menuItem(l="Debug : r9Anim",ann="Turn all the logging to Debug",
                      echoCommand=True, c="Red9.core._setlogginglevel_debug('r9Anim')")
        cmds.menuItem(l="Debug : r9Tools",ann="Turn all the logging to Debug",
                      echoCommand=True, c="Red9.core._setlogginglevel_debug('r9Tools')")
        cmds.menuItem(l="Debug : r9Pose",ann="Turn all the logging to Debug",
                      echoCommand=True, c="Red9.core._setlogginglevel_debug('r9Pose')")
        cmds.menuItem(l="Debug : r9General",ann="Turn all the logging to Debug",
                      echoCommand=True, c="Red9.core._setlogginglevel_debug('r9General')")
        cmds.menuItem(l="Debug : r9Audio",ann="Turn all the logging to Debug",
                      echoCommand=True, c="Red9.core._setlogginglevel_debug('r9Audio')")
        cmds.menuItem(l='Individual INFO',sm=True,p='redNineDebuggerItem')
        cmds.menuItem(l="Info : r9Core",ann="Turn all the logging to Info only",
                      echoCommand=True, c="Red9.core._setlogginglevel_info('r9Core')")
        cmds.menuItem(l="Info : r9Meta",ann="Turn all the logging to Info only",
                      echoCommand=True, c="Red9.core._setlogginglevel_info('r9Meta')")
        cmds.menuItem(l="Info : r9Anim",ann="Turn all the logging to Info only",
                      echoCommand=True, c="Red9.core._setlogginglevel_info('r9Anim')")
        cmds.menuItem(l="Info : r9Tools",ann="Turn all the logging to Info only",
                      echoCommand=True, c="Red9.core._setlogginglevel_info('r9Tools')")
        cmds.menuItem(l="Info : r9Pose",ann="Turn all the logging to Info only",
                      echoCommand=True, c="Red9.core._setlogginglevel_info('r9Pose')")
        cmds.menuItem(l="Info : r9General",ann="Turn all the logging to Info only",
                      echoCommand=True, c="Red9.core._setlogginglevel_info('r9General')")
        cmds.menuItem(l="Info : r9Audio",ann="Turn all the logging to Info only",
                      echoCommand=True, c="Red9.core._setlogginglevel_info('r9Audio')")
        cmds.menuItem(divider=True,p='redNineDebuggerItem')
        cmds.menuItem('redNineReloadItem',l="systems: reload()", p='redNineDebuggerItem',
                      ann="Force a complete reload on the core of Red9",
                      echoCommand=True, c="Red9.core._reload()")
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
                          l="Red9: OpenSceneFolder",
                          ann="Open the folder containing the current Maya Scene",
                          p=mainFileMenu,
                          echoCommand=True,
                          c="import maya.cmds as cmds;import Red9.core.Red9_General as r9General;r9General.os_OpenFileDirectory(cmds.file(q=True,sn=True))")
        # timeSlider additions
        if not cmds.menuItem('redNineTimeSliderItem',q=True,ex=True):
            if mayaVersion >= 2011:
                mel.eval('updateTimeSliderMenu TimeSliderMenu')
                
            TimeSliderMenu='TimeSliderMenu'
            cmds.menuItem(divider=True, p=TimeSliderMenu)
            cmds.menuItem(subMenu=True, label='Red9: Collapse Range', p=TimeSliderMenu)
            cmds.menuItem(label='Collapse : Selected Only',
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
    result=cmds.confirmDialog(title='Red9_StudioPack : build %f' % red9_getVersion(),
                       message=("Author: Mark Jackson\r\r"+
                                "Technical Animation Director\r\r"+
                                "Contact me at rednineinfo@gmail.com for more information\r\r"+
                                "thanks for trying the toolset. If you have any\r"+
                                "suggestions or bugs please let me know!"),
                       button=['thankyou','ChangeLog'],messageAlign='center')
    if result == 'ChangeLog':
        import Red9.core.Red9_General as r9General  # lazy load
        r9General.os_OpenFile(os.path.join(red9ModulePath(),'changeLog.txt'))
    
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

     
def sourceMelFolderContents(path):
    '''
    source all mel files in a given folder
    '''
    for script in [f for f in os.listdir(path) if f.lower().endswith('.mel')]:
        log.info('Sourcing mel script : %s' % script)
        mel.eval('source %s' % script)



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
    #AddPythonPackages()
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
        
    #mel.eval('global float $buildInstalled=%f' % red9_getVersion())
    
    log.info('Red9 StudioPack Complete!')

    
    