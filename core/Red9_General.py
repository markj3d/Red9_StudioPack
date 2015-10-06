'''
..
    Red9 Studio Pack: Maya Pipeline Solutions
    Author: Mark Jackson
    email: rednineinfo@gmail.com
    
    Red9 blog : http://red9-consultancy.blogspot.co.uk/
    MarkJ blog: http://markj3d.blogspot.co.uk
    

    This is the General library of utils used throughout the modules
    These are abstract general functions
    
    NOTHING IN THIS MODULE SHOULD REQUIRE RED9

'''
from __future__ import with_statement  # required only for Maya2009/8
from functools import wraps
import maya.cmds as cmds
import maya.mel as mel
import os
import time
import inspect
import sys
import tempfile
import subprocess
import json
import itertools

#Only valid Red9 import
import Red9.startup.setup as r9Setup


import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)



# Generic Utility Functions ---
#---------------------------------------------------------------------------------

def getCurrentFPS():
    '''
    returns the current frames per second as a number, rather than a useless string
    '''
    fpsDict = {"game":15.0, "film":24.0, "pal":25.0, "ntsc":30.0, "show":48.0, "palf":50.0, "ntscf":60.0}
    return fpsDict[cmds.currentUnit(q=True, fullName=True, time=True)]


def forceToString(text):
    '''
    simple function to ensure that data can be passed correctly into
    textFields for the UI (ensuring lists are converted)
    '''
    if issubclass(type(text), list):
        return ','.join(text)
    else:
        return text
    
def formatPath(path):
    '''
    take a path and format it to forward slashes with catches for the exceptions
    '''
    return os.path.normpath(path).replace('\\','/').replace('\t','/t').replace('\n','/n').replace('\a', '/a')
    
def itersubclasses(cls, _seen=None):
    """
    itersubclasses(cls)
    http://code.activestate.com/recipes/576949-find-all-subclasses-of-a-given-class/
    Iterator to yield full inheritance from a given class, including subclasses. This
    is used in the MetaClass to build the RED9_META_REGISTERY inheritance dict
    """
    if _seen is None:
        _seen = set()
    try:
        subs = cls.__subclasses__()
    except TypeError:  # fails only when cls is type
        subs = cls.__subclasses__(cls)
    for sub in subs:
        if sub not in _seen:
            _seen.add(sub)
            yield sub
            for sub in itersubclasses(sub, _seen):
                yield sub
                

def inspectFunctionSource(value):
    '''
    This is a neat little wrapper over the mel "whatIs" and Pythons inspect
    module that finds the given functions source filePath, either Mel or Python
    and opens the original file in the default program.
    Great for developers
    Supports all Mel functions, and Python Class / functions
    '''
    path=None
    #sourceType=None
    #Inspect for MEL
    log.debug('inspecting given command: %s' % value)
    #if issubclass(sourceType(value),str):
    try:
        path=mel.eval('whatIs("%s")' % value)
        if path and not path=="Command":
            path=path.split("in: ")[-1]
            #if path:
                #sourceType='mel'
        elif path=="Command":
            cmds.warning('%s : is a Command not a script' % value)
            return False
    except StandardError, error:
        log.info(error)
    #Inspect for Python
    if not path or not os.path.exists(path):
        log.info('This is not a known Mel command, inspecting Python libs for : %s' % value)
        try:
            log.debug('value :  %s' % value)
            log.debug('value isString : ', isinstance(value, str))
            log.debug('value callable: ', callable(value))
            log.debug('value is module : ', inspect.ismodule(value))
            log.debug('value is method : ', inspect.ismethod(value))
            if isinstance(value, str):
            #if not callable(value):
                value=eval(value)
            path=inspect.getsourcefile(value)
            if path:
                #sourceType='python'
                log.info('path : %s' % path)
        except StandardError, error:
            log.exception(error)
            
    #Open the file with the default editor
    #FIXME: If Python and you're a dev then the .py file may be set to open in the default
    #Python runtime/editor and won't open as expected. Need to look at this.
    if path and os.path.exists(path):
        log.debug('NormPath : %s' % os.path.normpath(path))
        os.startfile(os.path.normpath(path))
        return True
    else:
        log.warning('No valid path or functions found matches selection')
        return False
    

def getScriptEditorSelection():
        '''
        this is a hack to bypass an issue with getting the data back from the
        ScriptEditorHistory scroll. We need to copy the selected text to the
        clipboard then pull it back afterwards.
        '''
        import Red9.packages.pyperclip as pyperclip
        control=mel.eval("$v=$gLastFocusedCommandControl")
        executer=mel.eval("$v=$gLastFocusedCommandExecuter")
        reporter=mel.eval("$v=$gLastFocusedCommandReporter")
        func=""
        if control==executer:
            func=cmds.cmdScrollFieldExecuter(control, q=True, selectedText=True)
        elif control == reporter:
            cmds.cmdScrollFieldReporter(reporter, e=True, copySelection=True)
            #func=Clipboard.getText()
            #pyperclip.py : IN TESTING : Platform independant clipboard support
            func=pyperclip.paste()
        log.info('command caught: %s ' % func)
        return func



# Context Managers and Decorators ---
#---------------------------------------------------------------------------------

def Timer(func):
    '''
    Simple timer decorator
    '''
    @wraps(func)
    def wrapper(*args, **kws):
        t1 = time.time()
        res=func(*args, **kws)
        t2 = time.time()

        functionTrace=''
        try:
            #module if found
            mod = inspect.getmodule(args[0])
            functionTrace+='%s >>' % mod.__name__.split('.')[-1]
        except:
            log.debug('function module inspect failure')
        try:
            #class function is part of, if found
            cls = args[0].__class__
            functionTrace+='%s.' % args[0].__class__.__name__
        except:
            log.debug('function class inspect failure')
        functionTrace += func.__name__
        log.debug('TIMER : %s: took %0.3f ms' % (functionTrace, (t2 - t1) * 1000.0))
        #log.info('%s: took %0.3f ms' % (func.func_name, (t2-t1)*1000.0))
        return res
    return wrapper


def runProfile(func):
    '''
    run the profiler - only ever used when debugging /optimizing function call speeds.
    visualize the data using 'runsnakerun' to view the profiles and debug
    '''
    import cProfile
    from time import gmtime, strftime
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        currentTime = strftime("%d-%m-%H.%M.%S", gmtime())
        dumpFileName = 'c:/%s(%s).profile' % (func.__name__, currentTime)
        def command():
            func(*args, **kwargs)
        profile = cProfile.runctx("command()", globals(), locals(), dumpFileName)
        return profile
    return wrapper
    
    
class AnimationContext(object):
    """
    Simple Context Manager for restoring Animation settings
    """
    def __init__(self):
        self.autoKeyState=None
        self.timeStore=None
        
    def __enter__(self):
        self.autoKeyState=cmds.autoKeyframe(query=True, state=True)
        self.timeStore=cmds.currentTime(q=True)
        cmds.undoInfo(openChunk=True)

    def __exit__(self, exc_type, exc_value, traceback):
        # Close the undo chunk, warn if any exceptions were caught:
        cmds.autoKeyframe(state=self.autoKeyState)
        cmds.currentTime(self.timeStore)
        log.info('autoKeyState restored: %s' % self.autoKeyState)
        log.info('currentTime restored: %f' % self.timeStore)
        cmds.undoInfo(closeChunk=True)
        if exc_type:
            log.exception('%s : %s'%(exc_type, exc_value))
        # If this was false, it would re-raise the exception when complete
        return True
    

class undoContext(object):
    """
    Simple Context Manager for chunking the undoState
    """
    def __init__(self, initialUndo=False, undoFuncCache=[], undoDepth=1):
        '''
        If initialUndo is True then the context manager will manage what to do on entry with
        the undoStack. The idea is that if True the code will look at the last functions in the
        undoQueue and if any of those mantch those in the undoFuncCache, it'll undo them to the
        depth given. 
        WHY?????? This is specifically designed for things like floatFliders where you've
        set a function to act on the 'dc' flag, (drag command) by passing that func through this
        each drag will only go into the stack once, enabling you to drag as much as you want
        and return to the initial state, pre ALL drags, in one chunk. 
        
        :param initialUndo: on first process whether undo on entry to the context manager
        :param undoFuncCache: only if initialUndo = True : functions to catch in the undo stack
        :param undoDepth: only if initialUndo = True : depth of the undo stack to go to
        
        .. note ::
            When adding funcs to this you CAN'T call the 'dc' command on any slider with a lambda func,
            it has to call a specific func to catch in the undoStack. See Red9_AnimationUtils.FilterCurves
            code for a live example of this setup.
        '''
        self.initialUndo = initialUndo
        self.undoFuncCache = undoFuncCache
        self.undoDepth = undoDepth
    
    def undoCall(self):
        for _ in range(1, self.undoDepth + 1):
            #log.depth('undoDepth : %s' %  i)
            if [func for func in self.undoFuncCache if func in cmds.undoInfo(q=True, undoName=True)]:
                cmds.undo()
                      
    def __enter__(self):
        if self.initialUndo:
            self.undoCall()
        cmds.undoInfo(openChunk=True)

    def __exit__(self, exc_type, exc_value, traceback):
        cmds.undoInfo(closeChunk=True)
        if exc_type:
            log.exception('%s : %s'%(exc_type, exc_value))
        # If this was false, it would re-raise the exception when complete
        return True
    

class ProgressBarContext(object):
    '''
    Context manager to make it easier to wrap progressBars
    
    >>> #Example of using this in code
    >>> 
    >>> step=5
    >>> progressBar=r9General.ProgressBarContext(1000)
    >>> progressBar.setStep(step)
    >>> count=0
    >>> 
    >>> #now do your code but increment and check the progress state
    >>> with progressBar:
    >>>     for i in range(1:1000):
    >>>        if progressBar.isCanceled():
    >>>             print 'process cancelled'
    >>>             return
    >>>         progressBar.setProgress(count)
    >>>         count+=step
    
    '''
    def __init__(self, maxValue=100, interruptable=True):
        self.disable=False
        if r9Setup.mayaIsBatch():
            self.disable=True
            return
            
        if maxValue <= 0:
            raise ValueError("Max has to be greater than 0")
        self._maxValue = maxValue
        self._interruptable = interruptable
        
        self._gMainProgressBar = mel.eval('$gmtmp = $gMainProgressBar')
                
    def isCanceled(self):
        if not self.disable:
            return cmds.progressBar(self._gMainProgressBar, query=True, isCancelled=True)

    def setText(self, text):
        if not self.disable:
            cmds.progressBar(self._gMainProgressBar, edit=True, status=text)

    def setMaxValue(self, value):
        if not self.disable:
            cmds.progressBar(self._gMainProgressBar, edit=True, maxValue=int(value))
        
    def setStep(self, value):
        if not self.disable:
            cmds.progressBar(self._gMainProgressBar, edit=True, step=int(value))
    
    def setProgress(self, value):
        if not self.disable:
            cmds.progressBar(self._gMainProgressBar, edit=True, progress=int(value))
        
    def reset(self):
        if not self.disable:
            self.setMaxValue(self._maxValue)
            self.setText("")

    def __enter__(self):
        if not self.disable:
            cmds.progressBar(self._gMainProgressBar,
                              edit=True,
                              beginProgress=True,
                              step=1,
                              isInterruptable=self._interruptable,
                              maxValue=self._maxValue)
    
    def __exit__(self, exc_type, exc_value, traceback):
        if not self.disable:
            cmds.progressBar(self._gMainProgressBar, edit=True, endProgress=True)
            if exc_type:
                log.exception('%s : %s'%(exc_type, exc_value))
            del(self)
            return False  # False so that the exceptiopn gets re-raised
    
       
class HIKContext(object):
    """
    Simple Context Manager for restoring HIK Animation settings and managing HIK callbacks
    """
    def __init__(self, NodeList):
        self.objs=cmds.ls(sl=True, l=True)
        self.NodeList=NodeList
        self.managedHIK = False

    def __enter__(self):
        try:
            #We set the keying group mainly for the copyKey code, stops the entire rig being
            #manipulated on copy of single effector data
            self.keyingGroups=cmds.keyingGroup(q=True, fil=True)
            if [node for node in self.NodeList if cmds.nodeType(node) == 'hikIKEffector'\
                or cmds.nodeType(node) == 'hikFKJoint']:
                self.managedHIK = True
                
            if self.managedHIK:
                cmds.keyingGroup(fil="NoKeyingGroups")
                log.info('Processing HIK Mode >> using HIKContext Manager:')
                cmds.select(self.NodeList)
                mel.eval("hikManipStart 1 1")
        except:
            self.managedHIK = False

    def __exit__(self, exc_type, exc_value, traceback):
        if self.managedHIK:
            cmds.keyingGroup(fil=self.keyingGroups)
            cmds.select(self.NodeList)
            mel.eval("hikManipStop")
            log.info('Exit HIK Mode >> HIKContext Manager:')
        if exc_type:
            log.exception('%s : %s'%(exc_type, exc_value))
        if self.objs:
            cmds.select(self.objs)
        return True
                
    
class SceneRestoreContext(object):
    """
    Simple Context Manager for restoring Scene Global settings
    
    Basically we store the state of all the modelPanels and timeLine
    setups. Think of it like this, you export a scene, file -new, then re-import it
    but you've now lost all the scenes UI and setups. This is capable of returning 
    the UI to the previous state. Maybe this could be a tool in it's own write?
    
    Things stored:
        * All UI viewport states, display and settings
        * currentTime, timeRanges, timeUnits, sceneUnits, upAxis
        * Main cameras and transforms for the 4 main modelPanels
        * active sound and sound displays
        
    >>> from Red9.core.Red9_General import SceneRestoreContext as sceneStore
    >>> with sceneStore:    
    >>>     #do something to modify the scene setup
    >>>     cmds.currentTime(100)
    >>> 
    >>> #out of the context manager the scene will be restored as it was 
    >>> #before the code entered the context. (with sceneStore:)
    """
    def __init__(self):
        self.gPlayBackSlider=mel.eval("string $temp=$gPlayBackSlider")
        self.dataStore={}

    def __enter__(self):
        self.storeSettings()

    def __exit__(self, exc_type, exc_value, traceback):
        self.restoreSettings()
        if exc_type:
            log.exception('%s : %s'%(exc_type, exc_value))
        return True
    
    def storeSettings(self):
        '''
        main work function, store all UI settings
        '''
        self.dataStore['autoKey'] = cmds.autoKeyframe(query=True, state=True)
        
        # timeline management
        self.dataStore['currentTime'] = cmds.currentTime(q=True)
        self.dataStore['minTime'] = cmds.playbackOptions(q=True, min=True)
        self.dataStore['maxTime'] = cmds.playbackOptions(q=True, max=True)
        self.dataStore['startTime'] = cmds.playbackOptions(q=True, ast=True)
        self.dataStore['endTime'] = cmds.playbackOptions(q=True, aet=True)
        self.dataStore['playSpeed'] = cmds.playbackOptions(query=True, playbackSpeed=True)
        
        # unit management
        self.dataStore['timeUnit'] = cmds.currentUnit(q=True, fullName=True, time=True)
        self.dataStore['sceneUnits'] = cmds.currentUnit(q=True, fullName=True, linear=True)
        self.dataStore['upAxis'] = cmds.upAxis(q=True, axis=True)

        #viewport colors
        self.dataStore['displayGradient'] = cmds.displayPref(q=True, displayGradient=True)

        #objects colors
        self.dataStore['curvecolor'] = cmds.displayColor("curve", q=True, dormant=True)
        
        #panel management
        self.dataStore['panelStore'] = {}
        for panel in ['modelPanel1', 'modelPanel2', 'modelPanel3', 'modelPanel4']:
            if not cmds.modelPanel(panel, q=True, exists=True):
                continue
            self.dataStore['panelStore'][panel] = {}
            self.dataStore['panelStore'][panel]['settings'] = cmds.modelEditor(panel, q=True, sts=True)
            activeCam = cmds.modelPanel(panel, q=True, camera=True)
            if not cmds.nodeType(activeCam) == 'camera':
                activeCam = cmds.listRelatives(activeCam, f=True)[0]
            self.dataStore['panelStore'][panel]['activeCam'] = activeCam
                        
        #camera management
        #TODO : store the camera field of view etc also
        self.dataStore['cameraTransforms']={}
        for cam in ['persp', 'top', 'side', 'front']:
            try:
                self.dataStore['cameraTransforms'][cam] = [cmds.getAttr('%s.translate' % cam),
                                                     cmds.getAttr('%s.rotate' % cam),
                                                     cmds.getAttr('%s.scale' % cam)]
            except:
                log.debug("Camera doesn't exists : %s" % cam)
            
        #sound management
        self.dataStore['activeSound'] = cmds.timeControl(self.gPlayBackSlider, q=True, s=1)
        self.dataStore['displaySound'] = cmds.timeControl(self.gPlayBackSlider, q=True, ds=1)
    
    def restoreSettings(self):
        '''
        restore all UI settings
        '''
        cmds.autoKeyframe(state=self.dataStore['autoKey'])
        
        #timeline management
        cmds.currentTime(self.dataStore['currentTime'])
        cmds.playbackOptions(min=self.dataStore['minTime'])
        cmds.playbackOptions(max=self.dataStore['maxTime'])
        cmds.playbackOptions(ast=self.dataStore['startTime'])
        cmds.playbackOptions(aet=self.dataStore['endTime'])
        cmds.playbackOptions(ps=self.dataStore['playSpeed'])
        
        #unit management
        cmds.currentUnit(time=self.dataStore['timeUnit'])
        cmds.currentUnit(linear=self.dataStore['sceneUnits'])
        cmds.upAxis(axis=self.dataStore['upAxis'])
        
        log.info('Restored PlayBack / Timeline setup')

        #viewport colors
        cmds.displayPref(displayGradient=self.dataStore['displayGradient'])
        cmds.displayRGBColor(resetToSaved=True)

        #objects colors
        cmds.displayColor("curve", self.dataStore['curvecolor'], dormant=True)
        
        #panel management
        for panel, data in self.dataStore['panelStore'].items():
            try:
                cmdString = data['settings'].replace('$editorName', panel)
                mel.eval(cmdString)
                log.info("Restored Panel Settings Data >> %s" % panel)
                mel.eval('lookThroughModelPanel("%s","%s")' % (data['activeCam'], panel))
                log.info("Restored Panel Active Camera Data >> %s >> cam : %s" % (panel, data['activeCam']))
            except:
                log.debug("Failed to fully Restore ActiveCamera Data >> %s >> cam : %s" % (panel, data['activeCam']))
            
        # camera management
        for cam, settings in self.dataStore['cameraTransforms'].items():
            try:
                cmds.setAttr('%s.translate' % cam, settings[0][0][0], settings[0][0][1], settings[0][0][2])
                cmds.setAttr('%s.rotate' % cam, settings[1][0][0], settings[1][0][1], settings[1][0][2])
                cmds.setAttr('%s.scale' % cam, settings[2][0][0], settings[2][0][1], settings[2][0][2])
                log.info('Restored Default Camera Transform Data : % s' % cam)
            except:
                log.debug("Failed to fully Restore Default Camera Transform Data : % s" % cam)

        #sound management
        if self.dataStore['displaySound']:
            cmds.timeControl(self.gPlayBackSlider, e=True, ds=1, sound=self.dataStore['activeSound'])
            log.info('Restored Audio setup')
        else:
            cmds.timeControl(self.gPlayBackSlider, e=True, ds=0)
        log.debug('Scene Restored fully')
        return True
    
                    
# General ---
#---------------------------------------------------------------------------------

def thumbNailScreen(filepath, width, height, mode='api'):
    path='%s.bmp' % os.path.splitext(filepath)[0]
    if mode=='api':
        thumbnailApiFromView(path, width, height)
        log.debug('API Thumb > path : %s' % path)
    else:
        thumbnailFromPlayBlast(path, width, height)
        log.debug('Playblast Thumb > path : %s' % path)
    

def thumbnailFromPlayBlast(filepath, width, height):
    '''
    Generate a ThumbNail of the screen
    Note: 'cf' flag is broken in 2012
    :param filepath: path to Thumbnail
    :param width: width of capture
    :param height: height of capture
    '''
    filepath=os.path.splitext(filepath)[0]
    filename=os.path.basename(filepath)
    filedir=os.path.dirname(filepath)
    
    #get modelPanel and camera
    win = cmds.playblast(activeEditor=True).split('|')[-1]
    cam = cmds.modelPanel(win, q=True, camera=True)
    if not cmds.nodeType(cam) == 'camera':
        cam = cmds.listRelatives(cam)[0]
    
    storedformat = cmds.getAttr('defaultRenderGlobals.imageFormat')
    storedResolutionGate = cmds.getAttr('%s.filmFit' % cam)
    
    cmds.setAttr('defaultRenderGlobals.imageFormat', 20)
    cmds.setAttr('%s.filmFit' % cam, 2)  # set to Vertical so we don't get so much overscan
    
    cmds.playblast(frame=cmds.currentTime(q=True),  # startTime=cmds.currentTime(q=True),
                          # endTime=cmds.currentTime(q=True),
                          format="image",
                          filename=filepath,
                          width=width,
                          height=height,
                          percent=100,
                          quality=90,
                          forceOverwrite=True,
                          framePadding=0,
                          showOrnaments=False,
                          compression="BMP",
                          viewer=False)
    cmds.setAttr('defaultRenderGlobals.imageFormat', storedformat)
    cmds.setAttr('%s.filmFit' % cam, storedResolutionGate)
    #Why do this rename? In Maya2012 the 'cf' flag fails which means you have to use
    #the 'f' flag and that adds framePadding, crap I know! So we strip it and rename
    #the file after it's made.
    try:
        newfile=[f for f in os.listdir(filedir)
                 if f.split('.bmp')[0].split('.')[0] == filename and not
                 '.pose' in f]
        log.debug('Original Playblast file : %s' % newfile)
        os.rename(os.path.join(filedir, newfile[0]), '%s.bmp' % filepath)
        log.debug('Thumbnail Renamed : %s' % ('%s.bmp' % filepath))
        return '%s.bmp' % filepath
    except:
        pass

def thumbnailApiFromView(filename, width, height, compression='bmp', modelPanel='modelPanel4'):
    '''
    grab the thumbnail direct from the buffer?
    TODO: not yet figured out how you crop the data here?
    '''
    import maya.OpenMaya as OpenMaya
    import maya.OpenMayaUI as OpenMayaUI
    
    #Grab the last active 3d viewport
    view = None
    if modelPanel is None:
        view = OpenMayaUI.M3dView.active3dView()
    else:
        try:
            view = OpenMayaUI.M3dView()
            OpenMayaUI.M3dView.getM3dViewFromModelEditor(modelPanel, view)
        except:
            #in case the given modelPanel doesn't exist!!
            view = OpenMayaUI.M3dView.active3dView()

    #read the color buffer from the view, and save the MImage to disk
    image = OpenMaya.MImage()
    view.readColorBuffer(image, True)
    image.resize(width, height, True)
    image.writeToFile(filename, compression)
    log.info('API Thumbname call path : %s' % filename)


def getModifier():
    '''
    return the modifier key pressed
    '''
    mods = cmds.getModifiers()
    if (mods & 1) > 0:
        return 'Shift'
    if (mods & 2) > 0:
        return 'CapsLock'
    if (mods & 4) > 0:
        return 'Ctrl'
    if (mods & 8) > 0:
        return 'Alt'
    else:
        return False

    
# OS functions ---
#---------------------------------------------------------------------------------

class Clipboard:
    '''
    Get or Set data to the Windows clipboard...Used in the inspect code to grab the
    ScriptEditor's selected history
    CURRENTLY NOT BEING CALLED - switched to pyperclip.py module
    '''
    
    @staticmethod
    def getText():
        '''
        Get clipboard text if available
        '''
        import ctypes
        
        # declare win32 API
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        if not user32.OpenClipboard(0):
            return ''
        
        CF_TEXT = 1
        hClipMem = user32.GetClipboardData(CF_TEXT)
        kernel32.GlobalLock.restype = ctypes.c_char_p
        value = kernel32.GlobalLock(hClipMem)
        kernel32.GlobalUnlock(hClipMem)
        user32.CloseClipboard()

        if isinstance(value, str):
            return value
        elif hasattr(value, 'decode'):
            return value.decode(sys.getfilesystemencoding())
        else:
            return ''

    @staticmethod
    def setText(value):
        '''
        Set clipbard text
        '''
        import ctypes
        if not value:
            raise IOError('No text passed to the clipboard')
        if isinstance(value, unicode):
            value=str(value)
        if not isinstance(value, str):
            raise TypeError('value should be of str type')

        # declare win32 API
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        GlobalLock = kernel32.GlobalLock
        memcpy = ctypes.cdll.msvcrt.memcpy

        CF_TEXT = 1
        GHND = 66

        buf = ctypes.c_buffer(value.encode(sys.getfilesystemencoding()))
        bufferSize = ctypes.sizeof(buf)
        hGlobalMem = kernel32.GlobalAlloc(GHND, bufferSize)
        GlobalLock.restype = ctypes.c_void_p
        lpGlobalMem = GlobalLock(hGlobalMem)
        memcpy(lpGlobalMem, ctypes.addressof(buf), bufferSize)
        kernel32.GlobalUnlock(hGlobalMem)
        
        if user32.OpenClipboard(0):
            user32.EmptyClipboard()
            user32.SetClipboardData(CF_TEXT, hGlobalMem)
            user32.CloseClipboard()
            log.info('Data set to clipboard : %s' % value)
            return True


def os_OpenFileDirectory(path):
    '''
    open the given folder in the default OS browser
    '''
    import subprocess
    path=os.path.abspath(path)
    if sys.platform == 'win32':
        subprocess.Popen('explorer /select, "%s"' % path)
    elif sys.platform == 'darwin':  # macOS
        subprocess.Popen(['open', path])
    else:  # linux
        try:
            subprocess.Popen(['xdg-open', path])
        except OSError:
            raise OSError('unsupported xdg-open call??')
    
def os_OpenFile(filePath, *args):
    '''
    open the given file in the default program for this OS
    '''
    import subprocess
    #log.debug('filePath : %s' % filePath)
    #filePath=os.path.abspath(filePath)
    #log.debug('abspath : %s' % filePath)
    if sys.platform == 'win32':
        os.startfile(filePath)
    elif sys.platform == 'darwin':  # macOS
        subprocess.Popen(['open', filePath])
    else:  # linux
        try:
            subprocess.Popen(['xdg-open', filePath])
        except OSError:
            raise OSError('unsupported xdg-open call??')

def os_formatPath(path):
    '''
    take the given path and format it for Maya path
    '''
    return os.path.normpath(path).replace('\\','/').replace('\t','/t').replace('\n','/n').replace('\a', '/a')
    
def os_listFiles(folder, filters=[], byDate=False, fullPath=False):
    '''
    simple os wrap to list a dir with filters for file type and sort byDate
    
    :param folder: folder to dir list
    :param filters: list of file extensions to filter for
    :param byData: sort the list by modified date, newest first!
    '''
    files = os.listdir(folder)
    filtered=[]
    if filters:
        for f in files:
            for flt in filters:
                if f.lower().endswith(flt):
                    filtered.append(f)
        files=filtered
    if byDate and files:
        files.sort(key=lambda x: os.stat(os.path.join(folder, x)).st_mtime)
        files.reverse()
    if fullPath:
        files=[os_formatPath(os.path.join(folder, f)) for f in files]
    return files
    
def os_openCrashFile(openDir=False):
    '''
    Open the default temp dir where Maya stores it's crash files and logs
    '''
    tempdir=tempfile.gettempdir()
    if openDir:
        os_OpenFileDirectory(tempdir)
    else:
        mayafiles = os_listFiles(tempdir, filters=['.ma','.mb'], byDate=True, fullPath=True)
        cmds.file(mayafiles[0], open=True, f=True)
        
def os_fileCompare(file1, file2, openDiff=False):
    '''
    Pass in 2 files for diffComparision. If files are identical, ie there are no
    differences then the code returns 0
    
    :param file1: first file to compare with second file
    :param file2: second file to compare against the first
    :param openDiff: if a difference was found then boot Diffmerge UI, highlighting the diff
    
    .. note::
        
        This is a stub function that requires Diffmerge.exe, you can download from 
        https://sourcegear.com/diffmerge/.
        Once downloaded drop it here Red9/pakcages/diffMerge.exe
    '''
    outputDir=tempfile.gettempdir()
    
    diffmerge=os.path.join(r9Setup.red9ModulePath(),'packages','diffMerge.exe')
    if not os.path.exists(diffmerge):
        diffmerge=os.path.join(r9Setup.red9ModulePath(),'packages','DiffMerge','sgdm.exe')
    if os.path.exists(diffmerge):
        process=subprocess.Popen([diffmerge, '-d', os.path.join(outputDir, 'diffmergeOutput.diff'), file1, file2],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,
                                 universal_newlines=True)
        #output = process.communicate()
        process.wait()
        retcode = process.poll()
        if not retcode:
            log.info('Files are Identical')
            return retcode
        elif retcode==1:
            log.info('Files are not Identical - use the openDiff flag to open up the differences in the editor')
            if openDiff:
                process=subprocess.Popen([diffmerge, file1, file2], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
            return retcode
        elif retcode==2:
            raise IOError('Files failed to compare - issues prevented the compare processing both files')
            return retcode
    else:
        log.warning('Diffmerge commandline was not found, compare aborted')
    


def writeJson(filepath=None, content=None):
    '''
    write json file to disk

    :param filepath: file pat to drive where to write the file
    :param content: file content
    :return: None
    '''

    if filepath:
        path = os.path.dirname(filepath)

    if not os.path.exists(path):
        os.makedirs(path)

    name = open(filepath, "w")
    name.write(json.dumps(content, sort_keys=True, indent=4))
    name.close()


def readJson(filepath=None):
    '''
    file pat to drive where to read the file

    :param filepath:
    :return:
    '''
    if os.path.exists(filepath):
        name = open(filepath, 'r')
        try:
            return json.load(name)
        except ValueError:
            pass

class abcIndex(object):
    '''
    Alphabetic iterator
    '''
    def __init__(self, lower=True):
        if lower:
            self.__abc = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
                          'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
        else:
            self.__abc = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
                          'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']

        self.__iter = 0
        self.__iterator = None
        self.__Iterate()

    def __Iterate(self):
        self.__iter += 1
        self.__iterator = itertools.permutations(self.__abc, self.__iter)

    def next(self):
        '''
        Return and Alphabetic index
        '''
        try:
            temp = ''.join([x for x in self.__iterator.next()])
        except StopIteration:
            self.__Iterate()
            temp = ''.join([x for x in self.__iterator.next()])
        return '%s' % temp
    
    
    
    