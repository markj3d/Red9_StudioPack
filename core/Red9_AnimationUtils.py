'''
..
    Red9 Studio Pack: Maya Pipeline Solutions
    Author: Mark Jackson
    email: rednineinfo@gmail.com
    
    Red9 blog : http://red9-consultancy.blogspot.co.uk/
    MarkJ blog: http://markj3d.blogspot.co.uk
    
    
    This is the core of the Animation Toolset Lib, a suite of tools
    designed from production experience to automate an animators life.
    
    Setup : Follow the Install instructions in the Modules package


Code examples: 

#######################
 ProcessNodes
#######################

    All of the functions which have the ProcessNodes call share the same
    underlying functionality as described below. This is designed to process the
    given input nodes in a consistent manor across all the functions.
    Params: 'nodes' and 'filterSettings' are treated as special and build up a
    MatchedNode object that contains a tuple of matching pairs based on the given settings.

#######################
 AnimFunctions example:
#######################
    
    The main AnimFunctions class is designed to run with an r9Core.FilterNode
    object that is responsible for how we process hierarchies. If one isn't passed
    as an arg then the code simply processes the 'nodes' args in zipped pairs. 
    See the documentation on the r9Core.MatchedNodeInputs for more detail.
    
    All the AnimFunctions such as copyKeys, copyAttrs etc use the same base setup
    
    >>> import Red9_CoreUtils as r9Core
    >>> import maya.cmds as cmds
    >>> 
    >>> #===========================
    >>> #When Processing hierarchies:
    >>> #===========================
    >>> #Make a settings object and set the internal filter to find all
    >>> #child nurbsCurves that have an attr called 'Control_Marker'
    >>> settings = r9Core.FilterNode_Settings()
    >>> settings.nodeTypes ='nurbsCurve'
    >>> settings.searchAttrs = 'Control_Marker'
    >>> settings.printSettings()
    >>> 
    >>> #Option 1: Run the snap using the settings object you just made
    >>> #'nodes' will be the two roots of the rig hierarchies to snap.
    >>> anim = r9Anim.AnimFunctions()
    >>> anim.snapTransform(nodes=cmds.ls(sl=True), time=r9Anim.timeLineRangeGet(), filterSettings=settings)
    >>> 
    >>> #Option 2: Run the snap by passing in an already processed MatchedNodeInput object
    >>> #Make the MatchedNode object and process the hierarchies by passing the settings object in
    >>> matched = r9Core.MatchedNodeInputs(nodes=cmds.ls(sl=True), filterSettings=settings)
    >>> matched.processMatchedPairs()
    >>> #see what's been filtered
    >>> for n in matched.MatchedPairs:
    >>>     print n 
    >>> 
    >>> #Rather than passing in the settings or nodes, pass in the already processed MatchedNode
    >>> anim.snapTransform(nodes=matched, time=r9Anim.timeLineRangeGet())
    >>>
    >>>
    >>> #==============================
    >>> #When processing simple objects:
    >>> #==============================
    >>> #If you simple ignore the filterSettings you can just process given nodes directly
    >>> #the nodes are zipped into selected pairs obj[0]>obj[1], obj[2]>obj[3] etc
    >>> anim = r9Anim.AnimFunctions()
    >>> anim.snapTransform(nodes=cmds.ls(sl=True), time=r9Anim.timeLineRangeGet())
        
'''


from __future__ import with_statement  # required only for Maya2009/8
import maya.cmds as cmds
import maya.mel as mel

import Red9.startup.setup as r9Setup
import Red9_CoreUtils as r9Core
import Red9_General as r9General
import Red9_PoseSaver as r9Pose
import Red9_Meta as r9Meta

from functools import partial
import os
import random
import sys
import re
import shutil

import Red9.packages.configobj as configobj
from Red9.startup.setup import ProPack_Error

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

# global var so that the animUI is exposed to anything as a global object
global RED_ANIMATION_UI

global RED_ANIMATION_UI_OPENCALLBACK
RED_ANIMATION_UI_OPENCALLBACK=None

'''
Callback globals so you can fire a command prior to the UI opening,
we use this internally to fire an asset sync call on our project pose library
and to setup some additional paths.

def myProjectCallback(cls)
    cls.poseHandlerPaths=['MyProjects/resources/poseHandlers']
    cls.posePathProject ='My_projects/global/project/pose/lib'
    
r9Anim.RED_ANIMATION_UI_OPENCALLBACK = myProjectCallback

NOTE:: the function call bound to the callback is passed the current instance of the animUI class 
as an arg so you can modify as you need. Also when the PoseUI popup menu is built, IF the internal path
cls.poseHandlerPaths is valid then we bind into that popup all valid poseHandler.py files
found the given path. This allow you to add custom handler types and expose them through the UI directly.
'''


# Language map is used for all UI's as a text mapping for languages
LANGUAGE_MAP = r9Setup.LANGUAGE_MAP

#===========================================================================
# Generic Utility Functions
#===========================================================================

def checkRunTimeCmds():
    '''
    Ensure the RedRuntime Command plugin is loaded.
    '''
    try:
        if not cmds.pluginInfo('SnapRuntime.py', query=True, loaded=True):
            try:
                cmds.loadPlugin('SnapRuntime.py')
            except:
                raise StandardError('SnapRuntime Plug-in could not be loaded')
    except:
        raise StandardError('SnapRuntime Plug-in not found')
 
def getChannelBoxSelection():
    '''
    return a list of attributes selected in the ChannelBox
    '''
    return cmds.channelBox('mainChannelBox', q=True, selectedMainAttributes=True)

def getNodeAttrStatus(node=None, asDict=True, incLocked=True):
    '''
    stub function/ wrapper of getChannelBoxAttrs as the name is a
    little misleading and not really what the function is doing in hindsight.
    '''
    return getChannelBoxAttrs(node=None, asDict=True, incLocked=True)

def getChannelBoxAttrs(node=None, asDict=True, incLocked=True):
    '''
    return the status of all attrs on the given node, either as a flat list or
    a dict. As dict it contains all data which controls the lock, keyable, hidden states etc
    
    statusDict={'keyable':attrs, 'nonKeyable':attrs, 'locked':attrs}
        
    :param node: given node.
    :param asDict: True returns a dict with keys 'keyable','locked','nonKeyable' of attrs 
        False returns a list (non ordered) of all attr states.
    :param incLocked: True by default - whether to include locked channels in the return (only valid if not asDict)
    '''
    statusDict={}
    if not node:
        node = cmds.ls(sl=True, l=True)[0]
    statusDict['keyable'] = cmds.listAttr(node, keyable=True, unlocked=True)
    statusDict['locked'] = cmds.listAttr(node, keyable=True, locked=True)
    statusDict['nonKeyable'] = cmds.listAttr(node, channelBox=True)
    if asDict:
        return statusDict
    else:
        attrs = []
        if statusDict['keyable']:
            attrs.extend(statusDict['keyable'])
        if statusDict['nonKeyable']:
            attrs.extend(statusDict['nonKeyable'])
        if incLocked and statusDict['locked']:
            attrs.extend(statusDict['locked'])
        return attrs

def getSettableChannels(node=None, incStatics=True):
    '''
    return a list of settable attributes on a given node.
    
    :param node: node to inspect.
    :param incStatics: whether to include non-keyable static channels (On by default).
    
    FIXME: BUG some Compound attrs such as constraints return invalid data for some of the
    base functions using this as they can't be simply set. Do we strip them here?
    ie: pointConstraint.target.targetWeight
    '''
    if not node:
        node = cmds.ls(sl=True, l=True)[0]
    if not incStatics:
        #keyable and unlocked only
        return cmds.listAttr(node, k=True, u=True)
    else:
        #all settable attrs in the channelBox
        return getChannelBoxAttrs(node, asDict=False, incLocked=False)
        

def getAnimLayersFromGivenNodes(nodes):
    '''
    return all animLayers associated with the given nodes
    '''
    if not isinstance(nodes, list):
        #This is a hack as the cmds.animLayer call is CRAP. It doesn't mention
        #anywhere in the docs that you can even pass in Maya nodes, yet alone
        #that it has to take a list of nodes and fails with invalid flag if not
        nodes=[nodes]
    return cmds.animLayer(nodes, q=True, affectedLayers=True)

     
def animLayersConfirmCheck(nodes=None, deleteMerged=True):
    '''
    return all animLayers associated with the given nodes
    
    :param nodes: nodes to check membership of animLayers. If not pass the check will be at sceneLevel
    :param deleteMerged: modifies the warning message
    '''
    animLayers=[]
    message=''
    if deleteMerged:
        message='AnimLayers found in scene:\nThis process needs to merge them down and they will NOT be restored afterwards'
    else:
        message='AnimLayers found in scene:\nThis process needs to merge them but they will be restored afterwards'
    if nodes:
        if not isinstance(nodes, list):
            nodes=[nodes]
        animLayers=getAnimLayersFromGivenNodes(nodes)
    else:
        animLayers=cmds.ls(type='animLayer')
    if animLayers and not len(animLayers)==1:
        result = cmds.confirmDialog(
                title='AnimLayers - Confirm',
                button=['Confirm - Merge', 'Cancel'],
                message=message,
                defaultButton='Confirm - Merge',
                cancelButton='Cancel',
                dismissString='Cancel')
        if result == 'Confirm - Merge':
            return True
        else:
            return False
    return True
        

def mergeAnimLayers(nodes, deleteBaked=True):
    '''
    from the given nodes find, merge and remove any animLayers found
    
    FOR THE LOVE OF GOD AUTODESK, fix animLayers and give us a decent api for them,
    oh, and stop building massive mel commands on the fly based on bloody optVars!!!!
    '''
    animLayers=getAnimLayersFromGivenNodes(nodes)
    if animLayers:
        try:
            #deal with Maya's optVars for animLayers as the call that sets the defaults 
            #for these, via the UI call, is a local proc to the performAnimLayerMerge.
            deleteMerged=True
            if cmds.optionVar(exists='animLayerMergeDeleteLayers'):
                deleteMerged=cmds.optionVar(query='animLayerMergeDeleteLayers')
            cmds.optionVar(intValue=('animLayerMergeDeleteLayers', deleteBaked))
            
            if not cmds.optionVar(exists='animLayerMergeByTime'):
                cmds.optionVar(floatValue=('animLayerMergeByTime', 1.0))
                                    
            mel.eval('animLayerMerge {"%s"}' % '","'.join(animLayers))

#        cmds.bakeResults(nodes,
#                         simulation=False,
#                         dic=False,
#                         removeBakedAttributeFromLayer=True,
#                         destinationLayer='Merged_Layer',
#                         smart=True,
#                         sampleBy=1,
#                         time=timeLineRangeGet())
        except:
            log.warning('animLayer Merge failed!')
        finally:
            cmds.optionVar(intValue=('animLayerMergeDeleteLayers',deleteMerged))
    return 'Merged_Layer'

def pointOnPolyCmd(nodes):
    '''
    This is a BUG FIX for Maya's command wrapping of the pointOnPolyCon
    which doesn't support namespaces. This deals with that limitation
    '''
    import maya.app.general.pointOnPolyConstraint
    cmds.select(nodes)
    sourceName = nodes[0].split('|')[-1]
    
    cmdstring = "string $constraint[]=`pointOnPolyConstraint -weight 1`;"
    assembled = maya.app.general.pointOnPolyConstraint.assembleCmd()
    
    if ':' in sourceName:
        nameSpace = sourceName.replace(sourceName.split(':')[-1], '')
        assembled = assembled.replace(nameSpace, '')
    print(cmdstring + assembled)
    con=mel.eval(cmdstring)
    mel.eval(assembled)
    return con
    
def eulerSelected():
    '''
    cheap trick! for selected objects run a Euler Filter and then delete Static curves
    '''
    cmds.filterCurve(cmds.ls(sl=True, l=True))
    cmds.delete(cmds.ls(sl=True, l=True), sc=True)

       
def animCurveDrawStyle(style='simple', forceBuffer=True,
                   showBufferCurves=False, displayTangents=False, displayActiveKeyTangents=True, *args):
    '''
    Toggle the state of the graphEditor curve display, used in the Filter and Randomizer to
    simplify the display and the curve whilst processing. This allows you to also pass in
    the state directly, used by the UI close event to return the editor to the last cached state
    '''
    print 'toggleCalled', style, showBufferCurves, displayTangents, displayActiveKeyTangents

    if style == 'simple':
        print 'toggle On'
        if forceBuffer:
            mel.eval('doBuffer snapshot;')
        mel.eval('animCurveEditor -edit -showBufferCurves 1 -displayTangents false -displayActiveKeyTangents false graphEditor1GraphEd;')
    elif style == 'full':
        print 'toggleOff'
        cmd='animCurveEditor -edit'
        if showBufferCurves:
            cmd+=' -showBufferCurves 1'
        else:
            cmd+=' -showBufferCurves 0'
        if displayTangents:
            cmd+=' -displayTangents true'
        else:
            cmd+=' -displayTangents false'
        if displayActiveKeyTangents:
            cmd+= ' -displayActiveKeyTangents true'
        else:
            cmd+= ' -displayActiveKeyTangents false'
        mel.eval('%s graphEditor1GraphEd;' % cmd)


    
# TimeRange / AnimRange Functions -------------------------------------------------

def animRangeFromNodes(nodes, setTimeline=True):
    '''
    return the extend of the animation range for the given objects
    :param nodes: nodes to examine for animation data
    :param setTimeLine: whether we should set the playback timeline to the extent of the found anim data
    '''
    minBounds=None
    maxBounds=None
    for anim in r9Core.FilterNode.lsAnimCurves(nodes, safe=True):
        count=cmds.keyframe(anim, q=True, kc=True)
        min=cmds.keyframe(anim, q=True, index=[(0,0)], tc=True)
        max=cmds.keyframe(anim, q=True, index=[(count-1,count-1)], tc=True)
        if not minBounds or min[0]<minBounds:
            minBounds=min[0]
        if not maxBounds or max[0]>maxBounds:
            maxBounds=max[0]
    if setTimeline:
        cmds.playbackOptions(min=minBounds,max=maxBounds)
    return minBounds,maxBounds

def timeLineRangeGet(always=True):
    '''
    Return the current PlaybackTimeline OR if a range is selected in the
    TimeLine, (Highlighted in Red) return that instead.
    
    :param always: always return a timeline range, if none selected return the playbackRange.
    :rtype: tuple
    :return: (start,end)
    '''
    playbackRange = None
    PlayBackSlider = mel.eval('$tmpVar=$gPlayBackSlider')
    if cmds.timeControl(PlayBackSlider, q=True, rangeVisible=True):
        time = cmds.timeControl(PlayBackSlider, q=True, rangeArray=True)
        playbackRange = (time[0], time[1])
    elif always:
        playbackRange = (cmds.playbackOptions(q=True, min=True), cmds.playbackOptions(q=True, max=True))
    return playbackRange

def timeLineRangeProcess(start, end, step, incEnds=True):
    '''
    Simple wrapper function to take a given framerange and return
    a list[] containing the actual keys required for processing.
    This manages whether the step is negative, if so it reverses the
    times. Basically just a wrapper to the python range function.
    '''
    startFrm = start
    endFrm = end
    if step < 0:
        startFrm = end
        endFrm = start
    rng=[time for time in range(int(startFrm), int(endFrm), int(step))]
    if incEnds:
        rng.append(endFrm)
    return rng

def selectKeysByRange(nodes=None, animLen=False):
    '''
    select the keys from the selected or given nodes within the
    current timeRange or selectedTimerange
    '''
    if not nodes:
        nodes=cmds.ls(sl=True,type='transform')
    if not animLen:
        cmds.selectKey(nodes,time=timeLineRangeGet())
    else:
        cmds.selectKey(nodes,time=animRangeFromNodes(nodes, setTimeline=False))
    
def setTimeRangeToo(nodes=None, setall=True):
    '''
    set the playback timerange to be the animation range of the selected nodes.
    AnimRange is determined to be the extent of all found animation for a given node
    '''
    if not nodes:
        nodes=cmds.ls(sl=True,type='transform')
    time=animRangeFromNodes(nodes)
    if time:
        cmds.currentTime(time[0])
        cmds.playbackOptions(min=time[0])
        cmds.playbackOptions(max=time[1])
        if setall:
            cmds.playbackOptions(ast=time[0])
            cmds.playbackOptions(aet=time[1])
    else:
        raise StandardError('given nodes have no found animation data')

     

#def timeLineRangeSet(time):
#    '''
#    Return the current PlaybackTimeline OR if a range is selected in the
#    TimeLine, (Highlighted in Red) return that instead.
#    '''
#    PlayBackSlider = mel.eval('$tmpVar=$gPlayBackSlider')
#    time=cmds.timeControl(PlayBackSlider ,e=True, rangeArray=True, v=time)


# MAIN CALLS -----------------------------------------------------------------

class AnimationLayerContext(object):
    """
    Context Manager for merging animLayers down and restoring 
    the data as is afterwards
    """
    def __init__(self, srcNodes, mergeLayers=True, restoreOnExit=True):
        self.srcNodes = srcNodes  # nodes to check for animLayer membership / process
        self.mergeLayers = mergeLayers  # mute the behaviour of this context
        self.restoreOnExit = restoreOnExit  # restore the original layers after processing
        
        self.deleteBaked=True
        if self.restoreOnExit:
            self.deleteBaked=False
        self.animLayers=[]
        log.debug('Context Manager : mergeLayers : %s, restoreOnExit : %s' % (self.mergeLayers, self.restoreOnExit))
    
    def __enter__(self):
        self.animLayers=getAnimLayersFromGivenNodes(self.srcNodes)
        if self.animLayers:
            if self.mergeLayers:
                try:
                    layerCache={}
                    for layer in self.animLayers:
                        layerCache[layer]={'mute':cmds.animLayer(layer, q=True, mute=True),
                                           'locked':cmds.animLayer(layer, q=True, lock=True)}
                    mergeAnimLayers(self.srcNodes, deleteBaked=self.deleteBaked)
                    if self.restoreOnExit:
                        #return the original mute and lock states and select the new
                        #MergedLayer ready for the rest of the copy code to deal with
                        for layer,cache in layerCache.items():
                            for layer,cache in layerCache.items():
                                cmds.animLayer(layer, edit=True, mute=cache['mute'])
                                cmds.animLayer(layer, edit=True, mute=cache['locked'])
                        mel.eval("source buildSetAnimLayerMenu")
                        mel.eval('selectLayer("Merged_Layer")')
                except:
                    log.debug('CopyKeys internal : AnimLayer Merge Failed')
            else:
                log.warning('SrcNodes have animLayers, results may be erratic unless Baked!')

    def __exit__(self, exc_type, exc_value, traceback):
        # Close the undo chunk, warn if any exceptions were caught:
        if self.mergeLayers and self.restoreOnExit:
            if self.animLayers and cmds.animLayer('Merged_Layer', query=True, exists=True):
                cmds.delete('Merged_Layer')
        if exc_type:
            log.exception('%s : %s'%(exc_type, exc_value))
        # If this was false, it would re-raise the exception when complete
        return True


class AnimationUI(object):
    
    def __init__(self, dockUI=True):
        self.buttonBgc = r9Setup.red9ButtonBGC(1)
        self.win = 'Red9AnimToolsWin'
        self.dockCnt = 'Red9AnimToolsDoc'
        self.label = LANGUAGE_MAP._AnimationUI_.title
        self.internalConfigPath=False
        self.dock = dockUI
        
        # take generic filterSettings Object
        self.filterSettings = r9Core.FilterNode_Settings()
        self.filterSettings.transformClamp = True
        self.presetDir = r9Setup.red9Presets()  # os.path.join(r9Setup.red9ModulePath(), 'presets')
        self.basePreset = ''
        
        # Pose Management variables
        self.posePath = None  # working variable
        self.posePathLocal = 'Local Pose Path not yet set'
        self.posePathProject = 'Project Pose Path not yet set'
        self.posePathMode = 'localPoseMode'  # or 'project' : mode of the PosePath field and UI
        self.poseSelected = None
        self.poseGridMode = 'thumb'  # or text
        self.poseRootMode = 'RootNode'  # or MetaRig
        self.poses = None
        self.poseButtonBGC = [0.27, 0.3, 0.3]
        self.poseButtonHighLight = r9Setup.red9ButtonBGC('green')  # [0.7, 0.95, 0.75]
        
        self.poseHandlerPaths=[]  # ['J:/Games/hf2/Tools/CryMayaCore/core/crycore/resources/poseHandlers']
        
        # Internal config file setup for the UI state
        if self.internalConfigPath:
            self.ui_optVarConfig = os.path.join(self.presetDir, '__red9config__')
        else:
            self.ui_optVarConfig = os.path.join(r9Setup.mayaPrefs(), '__red9config__')
        self.ANIM_UI_OPTVARS = dict()
        self.__uiCache_readUIElements()
        
        
    @classmethod
    def show(cls):
        global RED_ANIMATION_UI
        global RED_ANIMATION_UI_OPENCALLBACK
        animUI=cls()

        if 'ui_docked' in animUI.ANIM_UI_OPTVARS['AnimationUI']:
            animUI.dock = eval(animUI.ANIM_UI_OPTVARS['AnimationUI']['ui_docked'])

        if r9General.getModifier() == 'Ctrl':
            if not animUI.dock:
                print 'switching True'
                animUI.dock = True
            else:
                print 'switching false'
                animUI.dock = False
            #animUI.dock = False
   
        RED_ANIMATION_UI=animUI
        if callable(RED_ANIMATION_UI_OPENCALLBACK):
            try:
                log.debug('calling RED_ANIMATION_UI_OPENCALLBACK')
                RED_ANIMATION_UI_OPENCALLBACK(animUI)
            except:
                log.warning('RED_ANIMATION_UI_OPENCALLBACK failed')
                
        animUI._showUI()
        animUI.ANIM_UI_OPTVARS['AnimationUI']['ui_docked'] = animUI.dock
        animUI.__uiCache_storeUIElements()
    
    def __uicloseEvent(self,*args):
        print 'AnimUI close event called'
        self.__uiCache_storeUIElements()
        RED_ANIMATION_UI=None
        del(self)
    
#     def __del__(self):
#         if cmds.scriptJob(exists=self.jobOnDelete):
#             cmds.scriptJob(kill=self.jobOnDelete, force=True)
            
    def _showUI(self):
        
        try:
            #'Maya2011 dock delete'
            if cmds.dockControl(self.dockCnt, exists=True):
                cmds.deleteUI(self.dockCnt, control=True)
        except:
            self.dock=False
        
        if cmds.window(self.win, exists=True):
            cmds.deleteUI(self.win, window=True)
            
        animwindow = cmds.window(self.win, title=self.label)
        
        cmds.menuBarLayout()
        cmds.menu(l=LANGUAGE_MAP._Generic_.vimeo_menu)
        cmds.menuItem(l=LANGUAGE_MAP._AnimationUI_.vimeo_walkthrough,  # "Open Vimeo > WalkThrough v1.27",
                      c="import Red9.core.Red9_General as r9General;r9General.os_OpenFile('https://vimeo.com/56431983')")
        cmds.menuItem(l=LANGUAGE_MAP._AnimationUI_.vimeo_update,  # "Open Vimeo > Update v1.40",
                      c="import Red9.core.Red9_General as r9General;r9General.os_OpenFile('https://vimeo.com/78577760')")
        cmds.menuItem(l=LANGUAGE_MAP._AnimationUI_.vimeo_hierarchy_control,  # "Open Vimeo > HierarchyControl",
                      c="import Red9.core.Red9_General as r9General;r9General.os_OpenFile('https://vimeo.com/56551684')")
        cmds.menuItem(l=LANGUAGE_MAP._AnimationUI_.vimeo_track_stab,  # "Open Vimeo > Track or Stabilize",
                      c="import Red9.core.Red9_General as r9General;r9General.os_OpenFile('https://vimeo.com/33440361')")
        cmds.menuItem(l=LANGUAGE_MAP._AnimationUI_.vimeo_copykeys,  # "Open Vimeo > CopyKeys & TimeOffsets",
                      c="import Red9.core.Red9_General as r9General;r9General.os_OpenFile('https://vimeo.com/81731510')")
        cmds.menuItem(l=LANGUAGE_MAP._AnimationUI_.vimeo_mirrorsetup,  # "Open Vimeo > MirrorSetups",
                      c="import Red9.core.Red9_General as r9General;r9General.os_OpenFile('https://vimeo.com/57882801')")
        cmds.menuItem(l=LANGUAGE_MAP._AnimationUI_.vimeo_posesaver_advanced,  # "Open Vimeo > PoseSaver - Advanced Topics",
                      c="import Red9.core.Red9_General as r9General;r9General.os_OpenFile('https://vimeo.com/66269033')")
        cmds.menuItem(l=LANGUAGE_MAP._AnimationUI_.vimeo_posesaver_blending,  # "Open Vimeo > PoseSaver - Blending and maintain spaces",
                      c="import Red9.core.Red9_General as r9General;r9General.os_OpenFile('https://vimeo.com/88391202')")
        cmds.menuItem(divider=True)
        cmds.menuItem(l=LANGUAGE_MAP._Generic_.contactme, c=lambda *args: (r9Setup.red9ContactInfo()))
        cmds.menu(l=LANGUAGE_MAP._Generic_.tools)
        cmds.menuItem(l=LANGUAGE_MAP._Generic_.reset,
                      c=self.__uiCache_resetDefaults)
        self.MainLayout = cmds.scrollLayout('red9MainScroller', rc=self.__uiCB_resizeMainScroller)
        self.form = cmds.formLayout()
        self.tabs = cmds.tabLayout(innerMarginWidth=5, innerMarginHeight=5)
        cmds.formLayout(self.form, edit=True, attachForm=((self.tabs, 'top', 0),
                                                          (self.tabs, 'left', 0),
                                                          (self.tabs, 'bottom', 0),
                                                          (self.tabs, 'right', 0)))

        #TAB1: ####################################################################
        
        self.AnimLayout = cmds.columnLayout(adjustableColumn=True)
        cmds.separator(h=5, style='none')
        
        #====================
        # CopyAttributes
        #====================
        cmds.frameLayout(label=LANGUAGE_MAP._AnimationUI_.copy_attrs, cll=True, borderStyle='etchedOut')
        cmds.columnLayout(adjustableColumn=True)
        cmds.button(label=LANGUAGE_MAP._AnimationUI_.copy_attrs, bgc=self.buttonBgc,
                    ann=LANGUAGE_MAP._AnimationUI_.copy_attrs_ann,
                    command=partial(self.__uiCall, 'CopyAttrs'))
       
        cmds.separator(h=5, style='none')
        cmds.rowColumnLayout(numberOfColumns=3, columnWidth=[(1, 100), (2, 100), (3, 100)], columnSpacing=[(1, 10), (2, 10)])
        self.uicbCAttrHierarchy = cmds.checkBox('uicbCAttrHierarchy', l=LANGUAGE_MAP._Generic_.hierarchy, al='left', v=False,
                                                ann=LANGUAGE_MAP._AnimationUI_.copy_attrs_hierarchy_ann,
                                                cc=lambda x: self.__uiCache_addCheckbox('uicbCAttrHierarchy'))
        self.uicbCAttrToMany = cmds.checkBox('uicbCAttrToMany', l=LANGUAGE_MAP._AnimationUI_.copy_to_many, al='left', v=False,
                                                ann=LANGUAGE_MAP._AnimationUI_.copy_attrs_to_many_ann)
        self.uicbCAttrChnAttrs = cmds.checkBox(ann=LANGUAGE_MAP._AnimationUI_.cbox_attrs_ann,
                                            l=LANGUAGE_MAP._AnimationUI_.cbox_attrs, al='left', v=False)
        cmds.setParent(self.AnimLayout)
              
        #====================
        # CopyKeys
        #====================
        cmds.separator(h=10, st='in')
        cmds.frameLayout(label=LANGUAGE_MAP._AnimationUI_.copy_keys, cll=True, borderStyle='etchedOut')
        cmds.columnLayout(adjustableColumn=True)
        cmds.button(label=LANGUAGE_MAP._AnimationUI_.copy_keys, bgc=self.buttonBgc,
                    ann=LANGUAGE_MAP._AnimationUI_.copy_keys_ann,
                    command=partial(self.__uiCall, 'CopyKeys'))
       
        cmds.separator(h=5, style='none')
        cmds.rowColumnLayout(numberOfColumns=3, columnWidth=[(1, 100), (2, 100), (3, 100)], columnSpacing=[(1, 10), (2, 10)], rowSpacing=[(1,5)])
        #cmds.rowColumnLayout(numberOfColumns=4, columnWidth=[(1, 75), (2, 80), (3, 80), (3, 80)], columnSpacing=[(1, 10), (2, 10)], rowSpacing=[(1,5)])
       
        self.uicbCKeyHierarchy = cmds.checkBox('uicbCKeyHierarchy', l=LANGUAGE_MAP._Generic_.hierarchy, al='left', v=False,
                                            ann=LANGUAGE_MAP._AnimationUI_.copy_keys_hierarchy_ann,
                                            cc=lambda x: self.__uiCache_addCheckbox('uicbCKeyHierarchy'))
        self.uicbCKeyToMany = cmds.checkBox('uicbCKeyToMany', l=LANGUAGE_MAP._AnimationUI_.copy_to_many, al='left', v=False,
                                            ann=LANGUAGE_MAP._AnimationUI_.copy_keys_to_many_ann)
        self.uicbCKeyChnAttrs = cmds.checkBox(ann=LANGUAGE_MAP._AnimationUI_.cbox_attrs_ann,
                                            l=LANGUAGE_MAP._AnimationUI_.cbox_attrs, al='left', v=False)
        self.uicbCKeyRange = cmds.checkBox('uicbCKeyRange', l=LANGUAGE_MAP._AnimationUI_.timerange, al='left', v=False,
                                            ann=LANGUAGE_MAP._AnimationUI_.copy_keys_timerange_ann,
                                            cc=lambda x: self.__uiCache_addCheckbox('uicbCKeyRange'))
        self.uicbCKeyAnimLay = cmds.checkBox('uicbCKeyAnimLay', l=LANGUAGE_MAP._AnimationUI_.copy_keys_merge_layers, al='left', v=False,
                                            ann=LANGUAGE_MAP._AnimationUI_.copy_keys_merge_layers_ann,
                                            cc=lambda x: self.__uiCache_addCheckbox('uicbCKeyAnimLay'))
        
        cmds.setParent('..')
        cmds.separator(h=10, style='in')
        cmds.rowColumnLayout(numberOfColumns=3, columnWidth=[(1, 100), (2, 100), (3, 100)], columnSpacing=[(1, 10), (2, 10)], rowSpacing=[(1,5)])
        cmds.text(label='Paste Options : ')
        cmds.optionMenu('om_PasteMethod',
                        ann=LANGUAGE_MAP._AnimationUI_.paste_method_ann,
                        cc=partial(self.__uiCB_setCopyKeyPasteMethod))
        for preset in ["insert",
                       "replace",
                       "replaceCompletely",
                       "merge", "scaleInsert",
                       "scaleReplace",
                       "scaleMerge",
                       "fitInsert",
                       "fitReplace",
                       "fitMerge"]:
            cmds.menuItem(l=preset)
        cmds.optionMenu('om_PasteMethod', e=True, v='replace')
        self.uiffgCKeyStep = cmds.floatFieldGrp('uiffgCKeyStep', l=LANGUAGE_MAP._AnimationUI_.offset, value1=0, cw2=(40, 50))
        cmds.setParent(self.AnimLayout)


        #====================
        # SnapTransforms
        #====================
        cmds.separator(h=10, st='in')
        cmds.frameLayout(label=LANGUAGE_MAP._AnimationUI_.snaptransforms, cll=True, borderStyle='etchedOut')
        cmds.columnLayout(adjustableColumn=True)
        cmds.button(label=LANGUAGE_MAP._AnimationUI_.snaptransforms, bgc=self.buttonBgc,
                     ann=LANGUAGE_MAP._AnimationUI_.snaptransforms_ann,
                     command=partial(self.__uiCall, 'Snap'))
        cmds.separator(h=5, style='none')

        #cmds.rowColumnLayout(numberOfColumns=3, columnWidth=[(1, 100), (2, 100), (3, 100)], columnSpacing=[(1, 10), (2, 10)], rowSpacing=[(1,2)])
        cmds.rowColumnLayout(numberOfColumns=4, columnWidth=[(1, 75), (2, 50), (3, 90), (4, 85)],
                             columnSpacing=[(1, 8), (2, 8), (3, 8)], rowSpacing=[(1,2)])

        self.uicbSnapRange = cmds.checkBox('uicbSnapRange', l=LANGUAGE_MAP._AnimationUI_.timerange, al='left', v=False,
                                            ann=LANGUAGE_MAP._AnimationUI_.snaptransforms_timerange_ann,
                                            cc=self.__uiCB_manageSnapTime)
        self.uicbSnapTrans = cmds.checkBox('uicbStanTrans', l=LANGUAGE_MAP._AnimationUI_.trans, al='left', v=True,
                                           ann=LANGUAGE_MAP._AnimationUI_.trans_ann,
                                           cc=lambda x: self.__uiCache_addCheckbox('uicbStanTrans'))
        self.uicbSnapPreCopyKeys = cmds.checkBox('uicbSnapPreCopyKeys', l=LANGUAGE_MAP._AnimationUI_.pre_copykeys, al='left',
                                                 ann=LANGUAGE_MAP._AnimationUI_.pre_copykeys_ann,
                                                 en=False, v=True)
        self.uiifgSnapStep = cmds.intFieldGrp('uiifgSnapStep', l=LANGUAGE_MAP._AnimationUI_.frmstep, en=False, value1=1, cw2=(45, 30),
                                              ann=LANGUAGE_MAP._AnimationUI_.frmstep_ann)

        self.uicbSnapHierarchy = cmds.checkBox('uicbSnapHierarchy', l=LANGUAGE_MAP._Generic_.hierarchy, al='left', v=False,
                                               ann=LANGUAGE_MAP._AnimationUI_.snaptransforms_hierarchy_ann,
                                               cc=self.__uiCB_manageSnapHierachy)
        self.uicbStanRots = cmds.checkBox('uicbStanRots', l=LANGUAGE_MAP._AnimationUI_.rots, al='left', v=True,
                                          ann='Track the Rotational data',
                                          cc=lambda x: self.__uiCache_addCheckbox('uicbStanRots'))
        self.uicbSnapPreCopyAttrs = cmds.checkBox(l=LANGUAGE_MAP._AnimationUI_.pre_copyattrs, al='left', en=False, v=True,
                                                  ann=LANGUAGE_MAP._AnimationUI_.pre_copyattrs_ann)
        self.uiifSnapIterations = cmds.intFieldGrp('uiifSnapIterations', l=LANGUAGE_MAP._AnimationUI_.iteration, en=False, value1=1, cw2=(45, 30),
                                           ann=LANGUAGE_MAP._AnimationUI_.iteration_ann)

        cmds.setParent(self.AnimLayout)


        #====================
        # Stabilizer
        #====================
        cmds.separator(h=10, st='in')
        cmds.frameLayout(label=LANGUAGE_MAP._AnimationUI_.tracknstabilize, cll=True, borderStyle='etchedOut')
        cmds.columnLayout(adjustableColumn=True)
        #cmds.rowColumnLayout(numberOfColumns=3, columnWidth=[(1, 100), (2, 100), (3, 100)], columnSpacing=[(1, 10), (2, 10), (3, 5)])
        cmds.rowColumnLayout(numberOfColumns=4, columnWidth=[(1, 100), (2, 55), (3, 55), (4, 100)], columnSpacing=[(1, 10), (3, 5)])
        self.uicbStabRange = cmds.checkBox('uicbStabRange', l=LANGUAGE_MAP._AnimationUI_.timerange, al='left', v=False,
                                            ann=LANGUAGE_MAP._AnimationUI_.snaptransforms_timerange_ann,
                                            cc=lambda x: self.__uiCache_addCheckbox('uicbStabRange'))
        self.uicbStabTrans = cmds.checkBox('uicbStabTrans', l=LANGUAGE_MAP._AnimationUI_.trans, al='left', v=True,
                                           ann=LANGUAGE_MAP._AnimationUI_.trans_ann,
                                           cc=lambda x: self.__uiCache_addCheckbox('uicbStabTrans'))
        self.uicbStabRots = cmds.checkBox('uicbStabRots', l=LANGUAGE_MAP._AnimationUI_.rots, al='left', v=True,
                                          ann=LANGUAGE_MAP._AnimationUI_.rots_ann,
                                          cc=lambda x: self.__uiCache_addCheckbox('uicbStabRots'))
        self.uiffgStabStep = cmds.floatFieldGrp('uiffgStabStep', l=LANGUAGE_MAP._AnimationUI_.step, value1=1, cw2=(40, 50),
                                              ann=LANGUAGE_MAP._AnimationUI_.step_ann)
        cmds.setParent('..')
        cmds.rowColumnLayout(numberOfColumns=2, columnWidth=[(1, 160), (2, 160)], columnSpacing=[(2, 2)])
        cmds.button(label=LANGUAGE_MAP._AnimationUI_.track_process_back, bgc=self.buttonBgc,
                     ann=LANGUAGE_MAP._AnimationUI_.track_process_ann,
                     command=partial(self.__uiCall, 'StabilizeBack'))
        cmds.button(label=LANGUAGE_MAP._AnimationUI_.track_process_forward, bgc=self.buttonBgc,
                     ann=LANGUAGE_MAP._AnimationUI_.track_process_ann,
                     command=partial(self.__uiCall, 'StabilizeFwd'))
        cmds.setParent(self.AnimLayout)
        
        
        #====================
        # TimeOffset
        #====================
        cmds.separator(h=10, st='in')
        cmds.frameLayout(label=LANGUAGE_MAP._AnimationUI_.timeoffset, cll=True, borderStyle='etchedOut')
        cmds.columnLayout(adjustableColumn=True)
        #cmds.rowColumnLayout(numberOfColumns=4, columnWidth=[(1, 100), (2, 55), (3, 55), (4, 100)], columnSpacing=[(1, 10), (3, 5)])
        cmds.rowColumnLayout(numberOfColumns=3, columnWidth=[(1, 100), (2, 100), (3, 100)], columnSpacing=[(1, 10), (2, 10), (3, 5)], rowSpacing=[(1,5),(2,5)])
        self.uicbTimeOffsetHierarchy = cmds.checkBox('uicbTimeOffsetHierarchy',
                                            l=LANGUAGE_MAP._Generic_.hierarchy, al='left', en=True, v=False,
                                            ann=LANGUAGE_MAP._AnimationUI_.offset_hierarchy_ann,
                                            ofc=partial(self.__uiCB_manageTimeOffsetChecks, 'Off'),
                                            onc=partial(self.__uiCB_manageTimeOffsetChecks),
                                            cc=lambda x: self.__uiCache_addCheckbox('uicbTimeOffsetHierarchy'))
              
        self.uicbTimeOffsetScene = cmds.checkBox('uicbTimeOffsetScene',
                                            l=LANGUAGE_MAP._AnimationUI_.offset_fullscene,
                                            ann=LANGUAGE_MAP._AnimationUI_.offset_fullscene_ann,
                                            al='left', v=False,
                                            ofc=partial(self.__uiCB_manageTimeOffsetChecks, 'Off'),
                                            onc=partial(self.__uiCB_manageTimeOffsetChecks, 'Full'),
                                            cc=lambda x: self.__uiCache_addCheckbox('uicbTimeOffsetScene'))
        
        self.uicbTimeOffsetPlayback = cmds.checkBox('uicbTimeOffsetTimelines', l=LANGUAGE_MAP._AnimationUI_.offset_timelines,
                                            ann=LANGUAGE_MAP._AnimationUI_.offset_timelines_ann,
                                            al='left', v=False, en=False,
                                            cc=lambda x: self.__uiCache_addCheckbox('uicbTimeOffsetTimelines'))

        self.uicbTimeOffsetRange = cmds.checkBox('uicbTimeOffsetRange',
                                            l=LANGUAGE_MAP._AnimationUI_.timerange, al='left', en=True, v=False,
                                            ann=LANGUAGE_MAP._AnimationUI_.offset_timerange_ann,
                                            ofc=partial(self.__uiCB_manageTimeOffsetChecks, 'Ripple'),
                                            onc=partial(self.__uiCB_manageTimeOffsetChecks, 'Ripple'),
                                            cc=lambda x: self.__uiCache_addCheckbox('uicbTimeOffsetRange'))
        self.uicbTimeOffsetFlocking = cmds.checkBox('uicbTimeOffsetFlocking',
                                            l=LANGUAGE_MAP._AnimationUI_.offset_flocking, al='left', en=True, v=False,
                                            ann=LANGUAGE_MAP._AnimationUI_.offset_flocking_ann)
        self.uicbTimeOffsetRandom = cmds.checkBox('uicbTimeOffsetRandom', l=LANGUAGE_MAP._AnimationUI_.offset_randomizer,
                                            ann=LANGUAGE_MAP._AnimationUI_.offset_randomizer_ann,
                                            al='left', v=False)
        self.uicbTimeOffsetRipple = cmds.checkBox('uicbTimeOffsetRipple', l=LANGUAGE_MAP._AnimationUI_.offset_ripple,
                                            ann=LANGUAGE_MAP._AnimationUI_.offset_ripple_ann,
                                            al='left', v=False,
                                            cc=lambda x: self.__uiCache_addCheckbox('uicbTimeOffsetRipple'))
        cmds.separator(style='none')
        cmds.setParent('..')
        cmds.separator(h=2, style='none')
        cmds.rowColumnLayout(numberOfColumns=3, columnWidth=[(1, 250), (2, 60)], columnSpacing=[(2, 5)])
       
        cmds.button(label=LANGUAGE_MAP._AnimationUI_.offset, bgc=self.buttonBgc,
                     ann=LANGUAGE_MAP._AnimationUI_.offset_ann,
                     command=partial(self.__uiCall, 'TimeOffset'))
        self.uiffgTimeOffset = cmds.floatFieldGrp('uiffgTimeOffset', value1=1, ann=LANGUAGE_MAP._AnimationUI_.offset_frms_ann)
        cmds.setParent(self.AnimLayout)
        
        
        #====================
        # Mirror Controls
        #====================
        cmds.separator(h=10, st='in')
        cmds.frameLayout(label=LANGUAGE_MAP._AnimationUI_.mirror_controls, cll=True, borderStyle='etchedOut')
        cmds.columnLayout(adjustableColumn=True)

        cmds.rowColumnLayout(numberOfColumns=3, columnWidth=[(1, 100), (2, 100), (3, 100)], columnSpacing=[(1, 10), (2, 10), (3, 5)])
        self.uicbMirrorHierarchy = cmds.checkBox('uicbMirrorHierarchy',
                                            l=LANGUAGE_MAP._Generic_.hierarchy, al='left', en=True, v=False,
                                            ann=LANGUAGE_MAP._AnimationUI_.mirror_hierarchy_ann,
                                            cc=lambda x: self.__uiCache_addCheckbox('uicbMirrorHierarchy'))
              
        cmds.setParent('..')
        
        cmds.rowColumnLayout(numberOfColumns=2, columnWidth=[(1, 160), (2, 160)], columnSpacing=[(2, 2)])
        cmds.button(label=LANGUAGE_MAP._AnimationUI_.mirror_animation, bgc=self.buttonBgc,
                     ann=LANGUAGE_MAP._AnimationUI_.mirror_animation_ann,
                     command=partial(self.__uiCall, 'MirrorAnim'))
        cmds.button(label=LANGUAGE_MAP._AnimationUI_.mirror_pose, bgc=self.buttonBgc,
                     ann=LANGUAGE_MAP._AnimationUI_.mirror_pose_ann,
                     command=partial(self.__uiCall, 'MirrorPose'))
 
        cmds.button(label=LANGUAGE_MAP._AnimationUI_.symmetry_animation, bgc=self.buttonBgc,
                     ann=LANGUAGE_MAP._AnimationUI_.symmetry_animation_ann,
                     command=partial(self.__uiCall, 'SymmetryAnim'))
        cmds.button(label=LANGUAGE_MAP._AnimationUI_.symmetry_pose, bgc=self.buttonBgc,
                     ann=LANGUAGE_MAP._AnimationUI_.symmetry_pose_ann,
                     command=partial(self.__uiCall, 'SymmetryPose'))
        cmds.setParent(self.AnimLayout)
        cmds.setParent(self.tabs)
        
    
        #TAB2: ####################################################################
        
        #=====================================================================
        # Hierarchy Controls Main filterSettings Object
        #=====================================================================
        
        self.FilterLayout = cmds.columnLayout(adjustableColumn=True)
        
        cmds.separator(h=15, style='none')
        cmds.text(LANGUAGE_MAP._AnimationUI_.hierarchy_descriptor)
        cmds.separator(h=20, style='in')
                                          
        # This bit is bullshit! the checkBox align flag is now obsolete so the label is always on the left regardless :(
        self.uiclHierarchyFilters = cmds.columnLayout('uiclHierarchyFilters', adjustableColumn=True, enable=True)
        cmds.rowColumnLayout(numberOfColumns=2, columnWidth=[(1, 120), (2, 200)], columnSpacing=[2, 3])
        cmds.text(label=LANGUAGE_MAP._AnimationUI_.metarig, align='right')
        self.uicbMetaRig = cmds.checkBox('uicbMetaRig',
                                          ann=LANGUAGE_MAP._AnimationUI_.metarig_ann,
                                          l='',
                                          v=True,
                                          cc=lambda x: self.__uiCB_managePoseRootMethod('uicbMetaRig'))
        cmds.setParent(self.uiclHierarchyFilters)
        
        self.uitfgSpecificNodeTypes = cmds.textFieldGrp('uitfgSpecificNodeTypes',
                                            label=LANGUAGE_MAP._AnimationUI_.search_nodetypes, text="", cw2=(120, 200),
                                            ann=LANGUAGE_MAP._AnimationUI_.search_nodetypes_ann)
        cmds.popupMenu()
        cmds.menuItem(label=LANGUAGE_MAP._Generic_.clear_all, command=partial(self.__uiCB_addToNodeTypes, 'clearAll'))
        cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.nodetype_transform, command=partial(self.__uiCB_addToNodeTypes, 'transform'))
        cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.nodetype_nurbs_curves, command=partial(self.__uiCB_addToNodeTypes, 'nurbsCurve'))
        cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.nodetype_nurbs_surfaces, command=partial(self.__uiCB_addToNodeTypes, 'nurbsSurface'))
        cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.nodetype_joints, command=partial(self.__uiCB_addToNodeTypes, 'joint'))
        cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.nodetype_locators, command=partial(self.__uiCB_addToNodeTypes, 'locator'))
        cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.nodetype_meshes, command=partial(self.__uiCB_addToNodeTypes, 'mesh'))
        cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.nodetype_cameras, command=partial(self.__uiCB_addToNodeTypes, 'camera'))
        cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.nodetype_hikeff, command=partial(self.__uiCB_addToNodeTypes, 'hikIKEffector'))
        cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.nodetype_blendshape, command=partial(self.__uiCB_addToNodeTypes, 'blendShape'))
        self.uitfgSpecificAttrs = cmds.textFieldGrp('uitfgSpecificAttrs',
                                            label=LANGUAGE_MAP._AnimationUI_.search_attributes, text="", cw2=(120, 200),
                                            ann=LANGUAGE_MAP._AnimationUI_.search_attributes_ann)
        self.uitfgSpecificPattern = cmds.textFieldGrp('uitfgSpecificPattern',
                                            label=LANGUAGE_MAP._AnimationUI_.search_pattern, text="", cw2=(120, 200),
                                            ann=LANGUAGE_MAP._AnimationUI_.search_pattern_ann)
        cmds.separator(h=5, style='none')
        cmds.text('Internal Node Priorities:')
        self.uitslFilterPriority = cmds.textScrollList('uitslFilterPriority', numberOfRows=8, allowMultiSelection=False,
                                               height=60, enable=True, append=self.filterSettings.filterPriority)
        cmds.popupMenu()
        cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.priorities_clear, command=lambda x: self.__uiSetPriorities('clear'))
        cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.priorities_set, command=lambda x: self.__uiSetPriorities('set'))
        cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.priorities_append, command=lambda x: self.__uiSetPriorities('append'))
        cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.priorities_remove, command=lambda x: self.__uiSetPriorities('remove'))
        cmds.menuItem(divider=True)
        cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.move_up, command=lambda x: self.__uiSetPriorities('moveUp'))
        cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.move_down, command=lambda x: self.__uiSetPriorities('moveDown'))
        self.uicbSnapPriorityOnly = cmds.checkBox('uicbSnapPriorityOnly', v=False,
                                                label=LANGUAGE_MAP._AnimationUI_.priorities_use_snap,
                                                onc=self.__uiCB_setPriorityFlag,
                                                cc=lambda x: self.__uiCache_addCheckbox('uicbSnapPriorityOnly'))
        cmds.separator(h=20, style='in')
        cmds.text(LANGUAGE_MAP._AnimationUI_.presets_available)
        self.uitslPresets = cmds.textScrollList(numberOfRows=8, allowMultiSelection=False,
                                               selectCommand=partial(self.__uiPresetSelection),
                                               height=110)
        cmds.popupMenu()
        cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.presets_delete, command=partial(self.__uiPresetDelete))
        cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.presets_opendir, command=partial(self.__uiPresetOpenDir))
        cmds.separator(h=10, style='none')
        cmds.setParent(self.FilterLayout)
        cmds.separator('filterInfoTop', style='in', vis=False)
        try:
            cmds.text('filterSettingsInfo', label='', ww=True)
        except:
            cmds.text('filterSettingsInfo', label='')
        cmds.separator('filterInfoBase', style='in', vis=False)
        cmds.rowColumnLayout(numberOfColumns=2, columnWidth=[(1, 140), (2, 180)])
        self.uicbIncRoots = cmds.checkBox('uicbIncRoots',
                                            ann='include RootNodes in the Filter',
                                            l=LANGUAGE_MAP._AnimationUI_.include_roots,
                                            al='left', v=True,
                                            cc=self.__uiCache_storeUIElements)
        
        cmds.optionMenu('om_MatchMethod', label=LANGUAGE_MAP._AnimationUI_.match_method, w=70,
                        ann=LANGUAGE_MAP._AnimationUI_.match_method_ann,
                        cc=self.__uiCB_setMatchMethod)
        #for preset in ["base","stripPrefix","index"]:
        cmds.menuItem(l=LANGUAGE_MAP._AnimationUI_.match_base, ann=LANGUAGE_MAP._AnimationUI_.match_base_ann)
        cmds.menuItem(l=LANGUAGE_MAP._AnimationUI_.match_stripprefix, ann=LANGUAGE_MAP._AnimationUI_.match_stripprefix_ann)
        cmds.menuItem(l=LANGUAGE_MAP._AnimationUI_.match_index, ann=LANGUAGE_MAP._AnimationUI_.match_index_ann)
        cmds.menuItem(l=LANGUAGE_MAP._AnimationUI_.match_mirror, ann=LANGUAGE_MAP._AnimationUI_.match_mirror_ann)
        
        cmds.optionMenu('om_MatchMethod', e=True, v='stripPrefix')

        cmds.setParent(self.FilterLayout)
        cmds.separator(h=10, style='none')
        cmds.rowColumnLayout(numberOfColumns=2, columnWidth=[(1, 162), (2, 162)])
        cmds.button(label=LANGUAGE_MAP._AnimationUI_.filter_test, bgc=self.buttonBgc,
                     ann=LANGUAGE_MAP._AnimationUI_.filter_test_ann,
                     command=partial(self.__uiCall, 'HierarchyTest'))
        cmds.button(label=LANGUAGE_MAP._AnimationUI_.filter_store, bgc=self.buttonBgc,
                     ann=LANGUAGE_MAP._AnimationUI_.filter_store_ann,
                     command=partial(self.__uiPresetStore))
        cmds.setParent(self.FilterLayout)
        cmds.setParent(self.tabs)
        

        #TAB3: ####################################################################
        
        #=====================================================================
        # Pose Saver Tab
        #=====================================================================
        
        self.poseUILayout = cmds.columnLayout(adjustableColumn=True)
        cmds.separator(h=10, style='none')
        self.uitfgPosePath = cmds.textFieldButtonGrp('uitfgPosePath',
                                            ann=LANGUAGE_MAP._AnimationUI_.pose_path,
                                            text="",
                                            bl=LANGUAGE_MAP._AnimationUI_.pose_path,
                                            bc=lambda *x: self.__uiCB_setPosePath(fileDialog=True),
                                            cc=lambda *x: self.__uiCB_setPosePath(fileDialog=False),
                                            cw=[(1, 260), (2, 40)])
        
        cmds.rowColumnLayout(nc=2, columnWidth=[(1, 120), (2, 120)], columnSpacing=[(1, 10)])
        self.uircbPosePathMethod = cmds.radioCollection('posePathMode')
        cmds.radioButton('localPoseMode', label=LANGUAGE_MAP._AnimationUI_.pose_local,
                                        ann=LANGUAGE_MAP._AnimationUI_.pose_local_ann,
                                        onc=partial(self.__uiCB_switchPosePathMode, 'local'),
                                        ofc=partial(self.__uiCB_switchPosePathMode, 'project'))
        cmds.radioButton('projectPoseMode', label=LANGUAGE_MAP._AnimationUI_.pose_project,
                                        ann=LANGUAGE_MAP._AnimationUI_.pose_project_ann,
                                        onc=partial(self.__uiCB_switchPosePathMode, 'project'),
                                        ofc=partial(self.__uiCB_switchPosePathMode, 'local'))
        cmds.setParent(self.poseUILayout)
        
        cmds.rowColumnLayout(nc=2, columnWidth=[(1, 260), (2, 60)])
        cmds.textFieldButtonGrp('uitfgPoseSubPath',
                                            ann=LANGUAGE_MAP._AnimationUI_.pose_subfolders_ann,
                                            text="",
                                            bl=LANGUAGE_MAP._AnimationUI_.pose_subfolders,
                                            bc=self.__uiCB_switchSubFolders,
                                            ed=False,
                                            cw=[(1, 190), (2, 40)])
        cmds.button(label=LANGUAGE_MAP._AnimationUI_.pose_clear,
                     ann=LANGUAGE_MAP._AnimationUI_.pose_clear_ann,
                     command=partial(self.__uiCB_clearSubFolders))
        cmds.setParent(self.poseUILayout)
         
        cmds.separator(h=10, style='in')
        cmds.rowColumnLayout(nc=3, columnWidth=[(1, 260), (2, 22), (3, 22)], columnSpacing=[(2,20)])
        if r9Setup.mayaVersion() > 2012:  # tcc flag not supported in earlier versions
            self.searchFilter = cmds.textFieldGrp('tfPoseSearchFilter', label=LANGUAGE_MAP._AnimationUI_.search_filter, text='',
                                                cw=((1, 87), (2, 160)),
                                                ann=LANGUAGE_MAP._AnimationUI_.search_filter_ann,
                                                tcc=lambda x: self.__uiCB_fillPoses(searchFilter=cmds.textFieldGrp('tfPoseSearchFilter', q=True, text=True)))
        else:
            self.searchFilter = cmds.textFieldGrp('tfPoseSearchFilter', label=LANGUAGE_MAP._AnimationUI_.search_filter, text='',
                                                cw=((1, 87), (2, 160)), fcc=True,
                                                ann=LANGUAGE_MAP._AnimationUI_.search_filter_ann,
                                                cc=lambda x: self.__uiCB_fillPoses(searchFilter=cmds.textFieldGrp('tfPoseSearchFilter', q=True, text=True)))
        
        cmds.iconTextButton('sortByName', style='iconOnly', image1='sortByName.bmp',
                            w=22, h=20, ann=LANGUAGE_MAP._AnimationUI_.sortby_name,
                            c=lambda * args: self.__uiCB_fillPoses(rebuildFileList=True, sortBy='name'))
              
        cmds.iconTextButton('sortByDate', style='iconOnly', image1='sortByDate.bmp',
                            w=22, h=20, ann=LANGUAGE_MAP._AnimationUI_.sortby_date,
                            c=lambda * args:self.__uiCB_fillPoses(rebuildFileList=True, sortBy='date'))
              
        cmds.setParent('..')
        cmds.separator(h=10, style='none')
        
        # SubFolder Scroller
        self.uitslPoseSubFolders = cmds.textScrollList('uitslPoseSubFolders', numberOfRows=8,
                                                       allowMultiSelection=False,
                                                       height=350, vis=False)
        
        # Main PoseFields
        self.uitslPoses = cmds.textScrollList('uitslPoses', numberOfRows=8, allowMultiSelection=False,
                                               #selectCommand=partial(self.__uiPresetSelection), \
                                               height=350, vis=False)
        self.posePopupText = cmds.popupMenu()
        
        self.uiglPoseScroll = cmds.scrollLayout('uiglPoseScroll',
                                                cr=True,
                                                height=350,
                                                hst=16,
                                                vst=16,
                                                vis=False,
                                                rc=self.__uiCB_gridResize)
        self.uiglPoses = cmds.gridLayout('uiglPoses', cwh=(100, 100), cr=False, ag=True)
        self.posePopupGrid = cmds.popupMenu()
        
        cmds.setParent(self.poseUILayout)
        cmds.rowColumnLayout(numberOfColumns=2, columnWidth=[(1, 162), (2, 162)])
        cmds.button('loadPoseButton', label=LANGUAGE_MAP._AnimationUI_.pose_load, bgc=self.buttonBgc,
                     ann=LANGUAGE_MAP._AnimationUI_.pose_load_ann,
                     command=partial(self.__uiCall, 'PoseLoad'))
        cmds.button('savePoseButton', label=LANGUAGE_MAP._AnimationUI_.pose_save, bgc=self.buttonBgc,
                     ann=LANGUAGE_MAP._AnimationUI_.pose_save_ann,
                     command=partial(self.__uiCall, 'PoseSave'))
        cmds.setParent(self.poseUILayout)
        cmds.separator(h=10, style='in')
        cmds.rowColumnLayout(numberOfColumns=2, columnWidth=[(1, 80), (2, 250)])
        self.uicbPoseHierarchy = cmds.checkBox('uicbPoseHierarchy',
                                            l=LANGUAGE_MAP._Generic_.hierarchy, al='left', en=True, v=False,
                                            ann=LANGUAGE_MAP._AnimationUI_.pose_hierarchy_ann,
                                            cc=lambda x: self.__uiCache_addCheckbox('uicbPoseHierarchy'))
        self.uitfgPoseRootNode = cmds.textFieldButtonGrp('uitfgPoseRootNode',
                                            ann=LANGUAGE_MAP._AnimationUI_.pose_set_root_ann,
                                            text="",
                                            bl=LANGUAGE_MAP._AnimationUI_.pose_set_root,
                                            bc=self.__uiCB_setPoseRootNode,
                                            cw=[(1, 180), (2, 60)])

        cmds.setParent(self.poseUILayout)
        cmds.separator(h=10, style='in')
        cmds.rowColumnLayout(nc=2, columnWidth=[(1, 120), (2, 160)])
        self.uicbPoseRelative = cmds.checkBox('uicbPoseRelative',
                                            l=LANGUAGE_MAP._AnimationUI_.pose_relative, al='left', en=True, v=False,
                                            cc=self.__uiCB_enableRelativeSwitches)
        self.uicbPoseSpace = cmds.checkBox('uicbPoseSpace',
                                            l=LANGUAGE_MAP._AnimationUI_.pose_maintain_parents, al='left', en=True, v=False,
                                            cc=lambda *x: self.__uiCache_addCheckbox('uicbPoseSpace'))
        cmds.setParent(self.poseUILayout)
        cmds.separator(h=5, style='none')
        self.uiflPoseRelativeFrame = cmds.frameLayout('PoseRelativeFrame', label=LANGUAGE_MAP._AnimationUI_.pose_rel_methods, cll=True, en=False)
        cmds.rowColumnLayout(nc=3, columnWidth=[(1, 120), (2, 80), (3, 80)])
        
        self.uircbPoseRotMethod = cmds.radioCollection('relativeRotate')
        cmds.text(label=LANGUAGE_MAP._AnimationUI_.pose_rel_rotmethod)
        cmds.radioButton('rotProjected', label=LANGUAGE_MAP._AnimationUI_.pose_rel_projected)
        cmds.radioButton('rotAbsolute', label=LANGUAGE_MAP._AnimationUI_.pose_rel_absolute)
        self.uircbPoseTranMethod = cmds.radioCollection('relativeTranslate')
        cmds.text(label=LANGUAGE_MAP._AnimationUI_.pose_rel_tranmethod)
        cmds.radioButton('tranProjected', label=LANGUAGE_MAP._AnimationUI_.pose_rel_projected)
        cmds.radioButton('tranAbsolute', label=LANGUAGE_MAP._AnimationUI_.pose_rel_absolute)
        cmds.setParent(self.poseUILayout)
        
        cmds.radioCollection(self.uircbPoseRotMethod, edit=True, select='rotProjected')
        cmds.radioCollection(self.uircbPoseTranMethod, edit=True, select='tranProjected')
        
        self.uiflPosePointFrame = cmds.frameLayout('PosePointCloud', label='Pose Point Cloud', cll=True, cl=True, en=True)
        cmds.rowColumnLayout(nc=4, columnWidth=[(1, 80), (2, 80), (3, 80), (4, 80)])
        cmds.button(label=LANGUAGE_MAP._AnimationUI_.pose_pp_make, bgc=self.buttonBgc,
                     ann=LANGUAGE_MAP._AnimationUI_.pose_pp_make_ann,
                     command=partial(self.__uiCall, 'PosePC_Make'))
        cmds.button(label=LANGUAGE_MAP._AnimationUI_.pose_pp_delete, bgc=self.buttonBgc,
                     ann=LANGUAGE_MAP._AnimationUI_.pose_pp_delete_ann,
                     command=partial(self.__uiCall, 'PosePC_Delete'))
        cmds.button(label=LANGUAGE_MAP._AnimationUI_.pose_pp_snap, bgc=self.buttonBgc,
                     ann=LANGUAGE_MAP._AnimationUI_.pose_pp_snap_ann,
                     command=partial(self.__uiCall, 'PosePC_Snap'))
        cmds.button(label=LANGUAGE_MAP._AnimationUI_.pose_pp_update, bgc=self.buttonBgc,
                     ann=LANGUAGE_MAP._AnimationUI_.pose_pp_update_ann,
                     command=partial(self.__uiCall, 'PosePC_Update'))
        cmds.setParent(self.poseUILayout)
        #====================
        #TabsEnd
        #====================
        cmds.tabLayout(self.tabs, edit=True, tabLabel=((self.AnimLayout, LANGUAGE_MAP._AnimationUI_.tab_animlayout),
                                                       (self.poseUILayout, LANGUAGE_MAP._AnimationUI_.tab_poselayout),
                                                       (self.FilterLayout, LANGUAGE_MAP._AnimationUI_.tab_filterlayout)))
        #====================
        # Header
        #====================
        if not r9Setup.mayaVersion()==2009:
            cmds.setParent(self.MainLayout)
        cmds.separator(h=10, style='none')
        self.r9strap = cmds.iconTextButton('r9strap', style='iconOnly', bgc=(0.7, 0, 0), image1='Rocket9_buttonStrap2.bmp',
                             c=lambda * args: (r9Setup.red9ContactInfo()), h=22, w=340)
        
        # needed for 2009
        cmds.scrollLayout('uiglPoseScroll', e=True, h=330)
        
        #====================
        # Show and Dock
        #====================

#         floating = True
#         if self.dock:
#             floating = False
            
        if self.dock:
            try:
                # Maya2011 QT docking
                cmds.dockControl(self.dockCnt, area='right', label=self.label,
                                 content=animwindow,
                                 floating=False,
                                 allowedArea=['right', 'left'],
                                 width=350)
            except:
                # Dock failed, opening standard Window
                cmds.showWindow(animwindow)
                cmds.window(self.win, edit=True, widthHeight=(355, 720))
                self.dock = False
        else:
            cmds.showWindow(animwindow)
            cmds.window(self.win, edit=True, widthHeight=(355, 720))

            
        #Set the initial Interface up
        self.__uiPresetsUpdate()
        self.__uiPresetReset()
        self.__uiCache_loadUIElements()
        #self.jobOnDelete=cmds.scriptJob(uiDeleted=(self.win, self.__uicloseEvent), runOnce=1)
#         if not self.dock:
#             cmds.dockControl(self.dockCnt, edit=True, floating=True)
#             cmds.dockControl(self.dockCnt, edit=True, width=360, height=740)

    # UI Callbacks
    #------------------------------------------------------------------------------
        
    def __uiCB_manageSnapHierachy(self, *args):
        '''
        Disable all hierarchy filtering ui's when not running hierarchys
        '''
        val = False
        if cmds.checkBox(self.uicbSnapHierarchy, q=True, v=True):
            val=True
        cmds.intFieldGrp('uiifSnapIterations', e=True, en=val)
        cmds.checkBox(self.uicbSnapPreCopyAttrs, e=True, en=val)
        self.__uiCache_addCheckbox('uicbSnapHierarchy')
            
    def __uiCB_manageSnapTime(self, *args):
        '''
        Disable the frmStep and PreCopy when not running timeline
        '''
        val = False
        if cmds.checkBox(self.uicbSnapRange, q=True, v=True):
            val=True
        cmds.checkBox(self.uicbSnapPreCopyKeys, e=True, en=val)
        cmds.intFieldGrp('uiifgSnapStep', e=True, en=val)
        self.__uiCache_addCheckbox('uicbSnapRange')
        
    def __uiCB_manageTimeOffsetChecks(self, *args):
        '''
        Manage timeOffset checks
        '''
        if args[0] == 'Full':
            cmds.checkBox(self.uicbTimeOffsetHierarchy, e=True, v=False)
            cmds.checkBox(self.uicbTimeOffsetPlayback, e=True, en=True)
            cmds.checkBox(self.uicbTimeOffsetFlocking, e=True, en=False)
            cmds.checkBox(self.uicbTimeOffsetRandom, e=True, en=False)
            cmds.checkBox(self.uicbTimeOffsetRange, e=True, en=True)  # en=False)
        elif args[0] == 'Ripple':
            if cmds.checkBox(self.uicbTimeOffsetRange, q=True, v=True):
                cmds.checkBox(self.uicbTimeOffsetRipple, e=True, en=True)
            else:
                cmds.checkBox(self.uicbTimeOffsetRipple, e=True, en=False)
        else:
            cmds.checkBox(self.uicbTimeOffsetPlayback, e=True, en=False)
            cmds.checkBox(self.uicbTimeOffsetScene, e=True, v=False)
            cmds.checkBox(self.uicbTimeOffsetFlocking, e=True, en=True)
            cmds.checkBox(self.uicbTimeOffsetRandom, e=True, en=True)
            cmds.checkBox(self.uicbTimeOffsetRange, e=True, en=True)
        
    def __uiCB_addToNodeTypes(self, nodeType, *args):
        '''
        Manage the RMB PopupMenu entries for easy adding nodeTypes to the UI
        '''
        nodeTypes = []
        if nodeType == 'clearAll':
            cmds.textFieldGrp('uitfgSpecificNodeTypes', e=True, text="")
            return
        current = cmds.textFieldGrp('uitfgSpecificNodeTypes', q=True, text=True)
        if current:
            nodeTypes = current.split(',')
            if nodeType not in nodeTypes:
                nodeTypes.append(nodeType)
            else:
                nodeTypes.remove(nodeType)
        else:
            nodeTypes.append(nodeType)
        cmds.textFieldGrp('uitfgSpecificNodeTypes', e=True, text=','.join(nodeTypes))
 
    def __uiCB_resizeMainScroller(self, *args):
        if self.dock:
            #if not cmds.dockControl(self.dockCnt, query=True, floating=True):
            width=cmds.dockControl(self.dockCnt, q=True, w=True)
            height=cmds.dockControl(self.dockCnt, q=True, h=True)
        else:
            newSize=cmds.window(self.win, q=True, wh=True)
            width=newSize[0]
            height=newSize[1]
        if width>350:
            #cmds.scrollLayout(self.MainLayout, e=True, w=width) #new?
            cmds.formLayout(self.form, edit=True, w=width-10)
            #cmds.iconTextButton(self.r9strap, e=True, w=width-10)
        else:
            cmds.scrollLayout(self.MainLayout, e=True, w=350)
            
        if height>440:  # 440 
            cmds.scrollLayout('uiglPoseScroll', e=True, h=max(height-430, 200))
        
        print 'width self.dockCnt:', cmds.dockControl(self.dockCnt, q=True, w=True)
        print 'width self.MainLayout:', cmds.scrollLayout(self.MainLayout, q=True, w=True)
        print 'width self.form:', cmds.formLayout(self.form, q=True, w=True)
        print 'width poseScroll:', cmds.scrollLayout('uiglPoseScroll', q=True, w=True)
                                
    def __uiCB_setCopyKeyPasteMethod(self, *args):
        self.ANIM_UI_OPTVARS['AnimationUI']['keyPasteMethod'] = cmds.optionMenu('om_PasteMethod', q=True, v=True)
        self.__uiCache_storeUIElements()
        
    def __uiCB_setMatchMethod(self, *args):
        self.ANIM_UI_OPTVARS['AnimationUI']['matchMethod'] = cmds.optionMenu('om_MatchMethod', q=True, v=True)
        self.__uiCache_storeUIElements()
         
    def __uiCB_setPriorityFlag(self, *args):
        '''
        check if the priority list has any entries, if not this flag is invalid
        '''
        if not cmds.textScrollList('uitslFilterPriority', q=True, ai=True):
            log.warning("Internal Node Priority list is empty, you can't set this flag without something in the Priority list itself")
            cmds.checkBox('uicbSnapPriorityOnly', e=True, v=False)
            return
        
    # Preset FilterSettings Object Management
    #------------------------------------------------------------------------------
    
    def __uiPresetReset(self):
        '''
        Just reset the FilterUI widgets
        '''
        cmds.textFieldGrp('uitfgSpecificNodeTypes', e=True, text="")
        cmds.textFieldGrp('uitfgSpecificAttrs', e=True, text="")
        cmds.textFieldGrp('uitfgSpecificPattern', e=True, text="")
        cmds.textScrollList('uitslFilterPriority', e=True, ra=True)
        cmds.separator('filterInfoTop', e=True, vis=False)
        cmds.text('filterSettingsInfo', edit=True, label="")
        cmds.separator('filterInfoBase', e=True, vis=False)
        cmds.checkBox(self.uicbMetaRig, e=True, v=False)
        cmds.checkBox(self.uicbSnapPriorityOnly, e=True, v=False)
        
    def __uiPresetsUpdate(self):
        '''
        Fill the Preset TextField with files in the presets Dirs
        '''
        self.presets = os.listdir(self.presetDir)
        try:
            [self.presets.remove(hidden) for hidden in ['__red9config__', '.svn', '__config__'] \
                                            if hidden in self.presets]
        except:
            pass
        self.presets.sort()
        cmds.textScrollList(self.uitslPresets, edit=True, ra=True)
        cmds.textScrollList(self.uitslPresets, edit=True, append=self.presets)
        
    def __uiPresetStore(self, *args):
        '''
        Write a new Config Preset for the current UI state. Launches a ConfirmDialog
        '''
        selected=cmds.textScrollList(self.uitslPresets, q=True, si=True)[0].split('.')[0]
        result = cmds.promptDialog(
                title='Preset FileName',
                message='Enter Name:',
                button=['OK', 'Cancel'],
                defaultButton='OK',
                cancelButton='Cancel',
                text=selected,
                dismissString='Cancel')
        if result == 'OK':
            self.__uiPresetFillFilter()  # Fill the internal filterSettings object from the UI elements
            self.filterSettings.printSettings()
            path=os.path.join(self.presetDir, '%s.cfg' % cmds.promptDialog(query=True, text=True))
            self.filterSettings.write(path)
            self.__uiPresetsUpdate()
    
    def __uiPresetDelete(self, *args):
        '''
        Delete the selected preset file from disk
        '''
        preset = cmds.textScrollList(self.uitslPresets, q=True, si=True)[0]
        os.remove(os.path.join(self.presetDir, preset))
        self.__uiPresetsUpdate()
        
    def __uiPresetOpenDir(self, *args):
        import subprocess
        path=os.path.normpath(self.presetDir)
        subprocess.Popen('explorer "%s"' % path)
      
    def __uiPresetSelection(self, Read=True):
        '''
        Fill the UI from on config preset file selected in the UI
        '''
        if Read:
            preset = cmds.textScrollList(self.uitslPresets, q=True, si=True)[0]
            self.filterSettings.read(os.path.join(self.presetDir, preset))
            #fill the cache up for the ini file
            self.ANIM_UI_OPTVARS['AnimationUI']['filterNode_preset']=preset
            log.info('preset loaded : %s' % preset)
            
        #JUST reset the UI elements
        self.__uiPresetReset()
        
        if self.filterSettings.nodeTypes:
            cmds.textFieldGrp('uitfgSpecificNodeTypes', e=True,
                              text=r9General.forceToString(self.filterSettings.nodeTypes))
        if self.filterSettings.searchAttrs:
            cmds.textFieldGrp('uitfgSpecificAttrs', e=True,
                                text=r9General.forceToString(self.filterSettings.searchAttrs))
        if self.filterSettings.searchPattern:
            cmds.textFieldGrp('uitfgSpecificPattern', e=True,
                              text=r9General.forceToString(self.filterSettings.searchPattern))
        if self.filterSettings.filterPriority:
            cmds.textScrollList('uitslFilterPriority', e=True,
                              append=self.filterSettings.filterPriority)
        if self.filterSettings.infoBlock:
            cmds.separator('filterInfoTop', e=True, vis=True)
            cmds.text('filterSettingsInfo', edit=True,
                      label='  %s  ' % self.filterSettings.infoBlock)
            cmds.separator('filterInfoBase', e=True, vis=True)
        cmds.checkBox(self.uicbMetaRig, e=True, v=self.filterSettings.metaRig)
        cmds.checkBox(self.uicbIncRoots, e=True, v=self.filterSettings.incRoots)
        
        #rigData block specific
        if hasattr(self.filterSettings, 'rigData'):
            if 'snapPriority' in self.filterSettings.rigData \
                    and r9Core.decodeString(self.filterSettings.rigData['snapPriority']):
                cmds.checkBox(self.uicbSnapPriorityOnly, e=True, v=True)

        #need to run the callback on the PoseRootUI setup
        self.__uiCB_managePoseRootMethod()
        self.filterSettings.printSettings()
        self.__uiCache_storeUIElements()

    def __uiPresetFillFilter(self):
        '''
        Fill the internal filterSettings Object for the AnimationUI class calls
        Note we reset but leave the rigData cached as it's not all represented
        by the UI, some is cached only when the filter is read in
        '''
        self.filterSettings.resetFilters(rigData=False)
        self.filterSettings.transformClamp = True

        if cmds.textFieldGrp('uitfgSpecificNodeTypes', q=True, text=True):
            self.filterSettings.nodeTypes = (cmds.textFieldGrp('uitfgSpecificNodeTypes', q=True, text=True)).split(',')
        if cmds.textFieldGrp('uitfgSpecificAttrs', q=True, text=True):
            self.filterSettings.searchAttrs = (cmds.textFieldGrp('uitfgSpecificAttrs', q=True, text=True)).split(',')
        if cmds.textFieldGrp('uitfgSpecificPattern', q=True, text=True):
            self.filterSettings.searchPattern = (cmds.textFieldGrp('uitfgSpecificPattern', q=True, text=True)).split(',')
        if cmds.textScrollList('uitslFilterPriority', q=True, ai=True):
            self.filterSettings.filterPriority = cmds.textScrollList('uitslFilterPriority', q=True, ai=True)

        self.filterSettings.metaRig = cmds.checkBox(self.uicbMetaRig, q=True, v=True)
        self.filterSettings.incRoots = cmds.checkBox(self.uicbIncRoots, q=True, v=True)
        # If the above filters are blank, then the code switches to full hierarchy mode
        if not self.filterSettings.filterIsActive():
            self.filterSettings.hierarchy = True
            
        #this is kind of against the filterSettings Idea, shoe horned in here
        #as it makes sense from the UI standpoint
        self.filterSettings.rigData['snapPriority'] = cmds.checkBox(self.uicbSnapPriorityOnly, q=True, v=True)
        
    def __uiSetPriorities(self, mode='set', *args):
        if mode=='set' or mode=='clear':
            cmds.textScrollList('uitslFilterPriority', e=True, ra=True)
        if mode=='set' or mode=='append':
            node=[r9Core.nodeNameStrip(node) for node in cmds.ls(sl=True)]
            cmds.textScrollList('uitslFilterPriority', e=True, append=[r9Core.nodeNameStrip(node) for node in cmds.ls(sl=True)])
        
        if mode=='moveUp' or mode=='moveDown' or mode=='remove':
            selected=cmds.textScrollList('uitslFilterPriority', q=True, si=True)[0]
            data=cmds.textScrollList('uitslFilterPriority', q=True, ai=True)
            cmds.textScrollList('uitslFilterPriority', e=True, ra=True)
        if mode=='moveUp':
            data.insert(data.index(selected)-1, data.pop(data.index(selected)))
            cmds.textScrollList('uitslFilterPriority', e=True, append=data)
            cmds.textScrollList('uitslFilterPriority', e=True, si=selected)
        if mode=='moveDown':
            data.insert(data.index(selected)+1, data.pop(data.index(selected)))
            cmds.textScrollList('uitslFilterPriority', e=True, append=data)
            cmds.textScrollList('uitslFilterPriority', e=True, si=selected)
        if mode=='remove':
            data.remove(selected)
            cmds.textScrollList('uitslFilterPriority', e=True, append=data)
        self.__uiPresetFillFilter()
        self.__uiCache_storeUIElements()
    
    
    # ------------------------------------------------------------------------------
    # PoseSaver Path Management Callbacks ------------------------------------------
   
    def setPoseSelected(self, val=None, *args):
        '''
        set the PoseSelected cache for the UI calls
        '''
        if not self.poseGridMode == 'thumb':
            self.poseSelected = cmds.textScrollList(self.uitslPoses, q=True, si=True)[0]
        else:
            self.poseSelected = val
        log.debug('PoseSelected : %s' % self.poseSelected)
        
    def getPoseSelected(self):
        if not self.poseSelected:
            raise StandardError('No Pose Selected in the UI')
        return self.poseSelected

    def buildPoseList(self, sortBy='name'):
        '''
        Get a list of poses from the PoseRootDir, this allows us to
        filter much faster as it stops all the os calls, cached list instead
        '''
        self.poses=[]
        if not os.path.exists(self.posePath):
            log.debug('posePath is invalid')
            return self.poses
        files=os.listdir(self.posePath)
        if sortBy == 'name':
            files=r9Core.sortNumerically(files)
            #files.sort()
        elif sortBy == 'date':
            files.sort(key=lambda x: os.stat(os.path.join(self.posePath, x)).st_mtime)
            files.reverse()
        
        for f in files:
            if f.lower().endswith('.pose'):
                self.poses.append(f.split('.pose')[0])
        return self.poses
  
    def buildFilteredPoseList(self, searchFilter):
        '''
        build the list of poses to show in the poseUI
        TODO: hook up an order based by date in here as an option to tie into the UI
        '''
        filteredPoses = self.poses
        if searchFilter:
            filteredPoses=[]
            filters=searchFilter.replace(' ','').split(',')
            for pose in self.poses:
                for srch in filters:
                    if srch and srch.upper() in pose.upper():
                        if not pose in filteredPoses:
                            filteredPoses.append(pose)
        return filteredPoses
    
    def __validatePoseFunc(self, func):
        '''
        called in some of the funcs so that they raise an error when called in 'Project' mode
        '''
        if self.posePathMode == 'projectPoseMode':
            raise StandardError('%s : function disabled in Project Pose Mode!' % func)
        else:
            return True
         
    def __uiCB_selectPose(self, pose):
        '''
        select the pose in the UI from the name
        '''
        if pose:
            if not self.poseGridMode == 'thumb':
                cmds.textScrollList(self.uitslPoses, e=True, si=pose)
            else:
                self.__uiCB_iconGridSelection(pose)

    def __uiCB_switchPosePathMode(self, mode, *args):
        '''
        Switch the Pose mode from Project to Local. In project mode save is disabled.
        Both have different caches to store the 2 mapped root paths
        :param mode: 'local' or 'project', in project the poses are load only, save=disabled
        '''
        if mode == 'local' or mode =='localPoseMode':
            self.posePath = os.path.join(self.posePathLocal, self.getPoseSubFolder())
            if not os.path.exists(self.posePath):
                log.warning('No Matching Local SubFolder path found - Reverting to Root')
                self.__uiCB_clearSubFolders()
                self.posePath = self.posePathLocal
                
            self.posePathMode = 'localPoseMode'
            cmds.button('savePoseButton', edit=True, en=True, bgc=r9Setup.red9ButtonBGC(1))
            cmds.textFieldButtonGrp('uitfgPosePath', edit=True, text=self.posePathLocal)
        elif mode == 'project' or mode =='projectPoseMode':
            self.posePath = os.path.join(self.posePathProject, self.getPoseSubFolder())
            if not os.path.exists(self.posePath):
                log.warning('No Matching Project SubFolder path found - Reverting to Root')
                self.__uiCB_clearSubFolders()
                self.posePath = self.posePathProject
                
            self.posePathMode = 'projectPoseMode'
            cmds.button('savePoseButton', edit=True, en=False, bgc=r9Setup.red9ButtonBGC(2))
            cmds.textFieldButtonGrp('uitfgPosePath', edit=True, text=self.posePathProject)
        cmds.scrollLayout('uiglPoseScroll', edit=True, sp='up')  # scroll the layout to the top!
        
        self.ANIM_UI_OPTVARS['AnimationUI']['posePathMode'] = self.posePathMode
        self.__uiCB_fillPoses(rebuildFileList=True)
            
    def __uiCB_setPosePath(self, path=None, fileDialog=False):
        '''
        Manage the PosePath textfield and build the PosePath
        '''
        if fileDialog:
            try:
                if r9Setup.mayaVersion()>=2011:
                    self.posePath=cmds.fileDialog2(fileMode=3,
                                                dir=cmds.textFieldButtonGrp('uitfgPosePath',
                                                q=True,
                                                text=True))[0]
                else:
                    print 'Sorry Maya2009 and Maya2010 support is being dropped'
                    def setPosePath(fileName, fileType):
                        self.posePath=fileName
                    cmds.fileBrowserDialog(m=4, fc=setPosePath, ft='image', an='setPoseFolder', om='Import')
            except:
                log.warning('No Folder Selected or Given')
        else:
            if not path:
                self.posePath=cmds.textFieldButtonGrp('uitfgPosePath', q=True, text=True)
            else:
                self.posePath=path
                
        cmds.textFieldButtonGrp('uitfgPosePath', edit=True, text=self.posePath)
        cmds.textFieldButtonGrp('uitfgPoseSubPath', edit=True, text="")
        #internal cache for the 2 path modes
        if self.posePathMode=='localPoseMode':
            self.posePathLocal=self.posePath
        else:
            self.posePathProject=self.posePath
        self.__uiCB_pathSwitchInternals()
          
    def __uiCB_pathSwitchInternals(self):
        '''
        fill the UI Cache and update the poses in eth UI
        '''
        self.__uiCB_fillPoses(rebuildFileList=True)
    
        #fill the cache up for the ini file
        self.ANIM_UI_OPTVARS['AnimationUI']['posePath']=self.posePath
        self.ANIM_UI_OPTVARS['AnimationUI']['poseSubPath']=self.getPoseSubFolder()
        self.ANIM_UI_OPTVARS['AnimationUI']['posePathLocal']=self.posePathLocal
        self.ANIM_UI_OPTVARS['AnimationUI']['posePathProject']=self.posePathProject
        self.ANIM_UI_OPTVARS['AnimationUI']['posePathMode'] = self.posePathMode
        self.__uiCache_storeUIElements()
 
 
    # SubFolder Pose Calls ----------
    def __uiCB_switchSubFolders(self, *args):
        '''
        switch the scroller from pose mode to subFolder select mode
        note we prefix the folder with '/' to help denote it's a folder in the UI
        '''
        basePath=cmds.textFieldButtonGrp('uitfgPosePath', query=True, text=True)
        
        #turn OFF the 2 main poseScrollers
        cmds.textScrollList(self.uitslPoses, edit=True, vis=False)
        cmds.scrollLayout(self.uiglPoseScroll, edit=True, vis=False)
        #turn ON the subFolder scroller
        cmds.textScrollList(self.uitslPoseSubFolders, edit=True, vis=True)
        cmds.textScrollList(self.uitslPoseSubFolders, edit=True, ra=True)
        
        if not os.path.exists(basePath):
            #path not valid clear all
            log.warning('No current PosePath set')
            return
        
        dirs=[subdir for subdir in os.listdir(basePath) if os.path.isdir(os.path.join(basePath, subdir))]
        if not dirs:
            raise StandardError('Folder has no subFolders for pose scanning')
        for subdir in dirs:
            cmds.textScrollList(self.uitslPoseSubFolders, edit=True,
                                            append='/%s' % subdir,
                                            sc=partial(self.__uiCB_setSubFolder))
            
    def __uiCB_setSubFolder(self, *args):
        '''
        Select a subFolder from the scrollList and update the systems
        '''
        basePath = cmds.textFieldButtonGrp('uitfgPosePath', query=True, text=True)
        subFolder = cmds.textScrollList(self.uitslPoseSubFolders, q=True, si=True)[0].split('/')[-1]
        
        cmds.textFieldButtonGrp('uitfgPoseSubPath', edit=True, text=subFolder)
        cmds.textScrollList(self.uitslPoseSubFolders, edit=True, vis=False)
        self.posePath = os.path.join(basePath, subFolder)
        self.__uiCB_pathSwitchInternals()

                  
    def __uiCB_clearSubFolders(self, *args):
        cmds.textScrollList(self.uitslPoseSubFolders, edit=True, vis=False)
        self.__uiCB_setPosePath()
               
         

    # ----------------------------------------------------------------------------
    # Build Pose UI calls  -------------------------------------------------------
     
    def getPoseSubFolder(self):
        '''
        Return the given pose subFolder if set
        '''
        try:
            return cmds.textFieldButtonGrp('uitfgPoseSubPath', q=True, text=True)
        except:
            return ""
                
    def getPoseDir(self):
        '''
        Return the poseDir including subPath
        '''
        return os.path.join(cmds.textFieldButtonGrp('uitfgPosePath', query=True, text=True),
                            self.getPoseSubFolder())
        
    def getPosePath(self):
        '''
        Return the full posePath for loading
        '''
        return os.path.join(self.getPoseDir(), '%s.pose' % self.getPoseSelected())
        
    def getIconPath(self):
        '''
        Return the full posePath for loading
        '''
        return os.path.join(self.getPoseDir(), '%s.bmp' % self.getPoseSelected())
                           
    def __uiCB_fillPoses(self, rebuildFileList=False, searchFilter=None, sortBy='name', *args):
        '''
        Fill the Pose List/Grid from the given directory
        '''

        # Store the current mode to the Cache File
        self.ANIM_UI_OPTVARS['AnimationUI']['poseMode'] = self.poseGridMode
        self.__uiCache_storeUIElements()
        searchFilter = cmds.textFieldGrp('tfPoseSearchFilter', q=True, text=True)

        if rebuildFileList:
            self.buildPoseList(sortBy=sortBy)
            log.debug('Rebuilt Pose internal Lists')
            # Project mode and folder contains NO poses so switch to subFolders
            if not self.poses and self.posePathMode == 'projectPoseMode':
                log.warning('No Poses found in Root Project directory, switching to subFolder pickers')
                self.__uiCB_switchSubFolders()
                return
        log.debug('searchFilter  : %s : rebuildFileList : %s' % (searchFilter, rebuildFileList))

        # TextScroll Layout
        # ================================
        if not self.poseGridMode == 'thumb':
            cmds.textScrollList(self.uitslPoseSubFolders, edit=True, vis=False)  # subfolder scroll OFF
            cmds.textScrollList(self.uitslPoses, edit=True, vis=True)  # pose TexScroll ON
            cmds.scrollLayout(self.uiglPoseScroll, edit=True, vis=False)  # pose Grid OFF
            cmds.textScrollList(self.uitslPoses, edit=True, ra=True)  # clear textScroller
            
            if searchFilter:
                cmds.scrollLayout('uiglPoseScroll', edit=True, sp='up')
                
            for pose in r9Core.filterListByString(self.poses, searchFilter, matchcase=False):  # self.buildFilteredPoseList(searchFilter):
                cmds.textScrollList(self.uitslPoses, edit=True,
                                        append=pose,
                                        sc=partial(self.setPoseSelected))
        # Grid Layout
        # ================================
        else:
            cmds.textScrollList(self.uitslPoseSubFolders, edit=True, vis=False)  # subfolder scroll OFF
            cmds.textScrollList(self.uitslPoses, edit=True, vis=False)  # pose TexScroll OFF
            cmds.scrollLayout(self.uiglPoseScroll, edit=True, vis=True)  # pose Grid ON
            self.__uiCB_gridResize()

            # Clear the Grid if it's already filled
            try:
                [cmds.deleteUI(button) for button in cmds.gridLayout(self.uiglPoses, q=True, ca=True)]
            except StandardError, error:
                print error
            for pose in r9Core.filterListByString(self.poses, searchFilter, matchcase=False):  # self.buildFilteredPoseList(searchFilter):
                try:
                    #:NOTE we prefix the buttons to get over the issue of non-numeric
                    #first characters which are stripped my Maya!
                    cmds.iconTextCheckBox('_%s' % pose, style='iconAndTextVertical', \
                                            image=os.path.join(self.posePath, '%s.bmp' % pose), \
                                            label=pose, \
                                            bgc=self.poseButtonBGC, \
                                            parent=self.uiglPoses, \
                                            ann=pose, \
                                            onc=partial(self.__uiCB_iconGridSelection, pose), \
                                            ofc="import maya.cmds as cmds;cmds.iconTextCheckBox('_%s', e=True, v=True)" % pose)  # we DONT allow you to deselect
                except StandardError, error:
                    raise StandardError(error)
             
            if searchFilter:
                #with search scroll the list to the top as results may seem blank otherwise
                cmds.scrollLayout('uiglPoseScroll', edit=True, sp='up')
          
        # Finally Bind the Popup-menu
        self.__uiCB_PosePopup()

          
    def __uiCB_PosePopup(self):
        '''
        RMB popup menu for the Pose functions
        '''
        enableState=True
        if self.posePathMode=='projectPoseMode':
            enableState=False
            
        if self.poseGridMode=='thumb':
            parent=self.posePopupGrid
            cmds.popupMenu(self.posePopupGrid, e=True, deleteAllItems=True)
        else:
            parent=self.posePopupText
            cmds.popupMenu(self.posePopupText, e=True, deleteAllItems=True)
        
        cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.pose_rmb_blender, p=parent, command=partial(self.__uiCall, 'PoseBlender'))
        cmds.menuItem(divider=True, p=parent)
        cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.pose_rmb_delete, en=enableState, p=parent, command=partial(self.__uiPoseDelete))
        cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.pose_rmb_rename, en=enableState, p=parent, command=partial(self.__uiPoseRename))
        cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.pose_rmb_selectinternal, p=parent, command=partial(self.__uiPoseSelectObjects))
        
        cmds.menuItem(divider=True, p=parent)
        cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.pose_rmb_update_pose, en=enableState, p=parent, command=partial(self.__uiPoseUpdate, False))
        cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.pose_rmb_update_pose_thumb, en=enableState, p=parent, command=partial(self.__uiPoseUpdate, True))
        
        if self.poseGridMode=='thumb':
            cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.pose_rmb_update_thumb, p=parent, command=partial(self.__uiPoseUpdateThumb))
            
        cmds.menuItem(divider=True, p=parent)
        cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.pose_rmb_add_subfolder, en=enableState, p=parent, command=partial(self.__uiPoseMakeSubFolder))
        cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.pose_rmb_refresh, en=True, p=parent, command=lambda x: self.__uiCB_fillPoses(rebuildFileList=True))
        cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.pose_rmb_openfile, p=parent, command=partial(self.__uiPoseOpenFile))
        cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.pose_rmb_opendir, p=parent, command=partial(self.__uiPoseOpenDir))
        cmds.menuItem(divider=True, p=parent)
        cmds.menuItem('red9PoseCompareSM', l=LANGUAGE_MAP._AnimationUI_.pose_rmb_compare, sm=True, p=parent)
        cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.pose_rmb_compare_skel, p='red9PoseCompareSM', command=partial(self.__uiCall, 'PoseCompareSkelDict'))
        cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.pose_rmb_compare_posedata, p='red9PoseCompareSM', command=partial(self.__uiCall, 'PoseComparePoseDict'))

        cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.pose_rmb_copyhandler, en=enableState, p=parent, command=partial(self.__uiPoseAddPoseHandler))
        cmds.menuItem(divider=True, p=parent)
        cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.pose_rmb_copypose, en=enableState, p=parent, command=partial(self.__uiPoseCopyToProject))
        
        cmds.menuItem(divider=True, p=parent)
        cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.pose_rmb_switchmode, p=parent, command=self.__uiCB_switchPoseMode)

        if self.poseGridMode=='thumb':
            cmds.menuItem(divider=True, p=parent)
            cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.pose_rmb_grid_small, p=parent, command=partial(self.__uiCB_setPoseGrid, 'small'))
            cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.pose_rmb_grid_med, p=parent, command=partial(self.__uiCB_setPoseGrid, 'medium'))
            cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.pose_rmb_grid_large, p=parent, command=partial(self.__uiCB_setPoseGrid, 'large'))
            
        if self.posePath:
            cmds.menuItem(divider=True, p=parent)
            self.addPopupMenusFromFolderConfig(parent)
        if self.poseHandlerPaths:
            cmds.menuItem(divider=True, p=parent)
            self.addPopupMenus_PoseHandlers(parent)
    
    def addPopupMenus_PoseHandlers(self, parentPopup):
        '''
        for a given list of folders containing poseHandler files add these as 
        default 'make subfolder' types to the main poseUI popup menu
        '''
        if self.poseHandlerPaths:
            for path in self.poseHandlerPaths:
                if os.path.exists(path):
                    poseHandlers=os.listdir(path)
                    if poseHandlers:
                        for handler in poseHandlers:
                            if handler.endswith('_poseHandler.py'):
                                handlerPath=os.path.join(path,handler)
                                log.debug('poseHandler file being copied into new folder : %s' % handlerPath)
                                cmds.menuItem(label='Add Subfolder : %s' % handler.replace('_poseHandler.py', '').upper(),
                                              en=True, p=parentPopup,
                                              command=partial(self.__uiPoseMakeSubFolder, handlerPath))
                        
    def addPopupMenusFromFolderConfig(self, parentPopup):
        '''
        if the poseFolder has a poseHandler.py file see if it has the 'posePopupAdditions' func
        and if so, use that to extend the standard menu's
        '''
        poseHandler=r9Pose.getFolderPoseHandler(self.getPoseDir())
        if poseHandler:
            import imp
            import inspect
            print 'Adding to menus From PoseHandler File!!!!'
            tempPoseFuncs = imp.load_source(poseHandler.split('.py')[0], os.path.join(self.getPoseDir(), poseHandler))
            if [func for name, func in inspect.getmembers(tempPoseFuncs, inspect.isfunction) if name == 'posePopupAdditions']:
                # NOTE we pass in self so the new additions have the same access as everything else!
                tempPoseFuncs.posePopupAdditions(parentPopup, self)
            del(tempPoseFuncs)

    def __uiCB_setPoseGrid(self, size, *args):
        '''
        Set size of the Thumnails used in the PoseGrid Layout
        '''
        if size == 'small':
            cmds.gridLayout(self.uiglPoses, e=True, cwh=(75, 80), nc=4)
        if size == 'medium':
            cmds.gridLayout(self.uiglPoses, e=True, cwh=(100, 90), nc=3)
        if size == 'large':
            cmds.gridLayout(self.uiglPoses, e=True, cwh=(150, 120), nc=2)
        self.__uiCB_fillPoses()
        self.__uiCB_selectPose(self.poseSelected)
    
    def __uiCB_iconGridSelection(self, current=None, *args):
        '''
        Unselect all other iconTextCheckboxes than the currently selected
        without this you would be able to multi-select the thumbs
        
        .. note:: 
            because we prefix the buttons to get over the issue of non-numeric
            first characters we now need to strip the first character back off
        '''
        for button in cmds.gridLayout(self.uiglPoses, q=True, ca=True):
            if current and not button[1:] == current:
                cmds.iconTextCheckBox(button, e=True, v=False, bgc=self.poseButtonBGC)
            else:
                cmds.iconTextCheckBox(button, e=True, v=True, bgc=self.poseButtonHighLight)
        self.setPoseSelected(current)
        
    def __uiCB_gridResize(self, *args):
        if r9Setup.mayaVersion() >= 2010:
            cells = int(cmds.scrollLayout('uiglPoseScroll', q=True, w=True) / cmds.gridLayout('uiglPoses', q=True, cw=True))
            cmds.gridLayout('uiglPoses', e=True, nc=cells)
        else:
            log.debug('this call FAILS in 2009???')
    
    
    # ------------------------------------------------------------------------------
    # Main Pose Function Wrappers --------------------------------------------------
    
    def __uiCB_switchPoseMode(self, *args):
        '''
        Toggle PoseField mode between Grid mode and TextScroll
        '''
        if self.poseGridMode == 'thumb':
            self.poseGridMode = 'text'
        else:
            self.poseGridMode = 'thumb'
        self.__uiCB_fillPoses()
        self.__uiCB_selectPose(self.poseSelected)
              
    def __uiCB_savePosePath(self, existingText=None):
        '''
        Build the path for the pose to be saved too
        '''
        result = cmds.promptDialog(
                title='Pose',
                message='Enter Name:',
                button=['OK', 'Cancel'],
                text=existingText,
                defaultButton='OK',
                cancelButton='Cancel',
                dismissString='Cancel')
        if result == 'OK':
            name=cmds.promptDialog(query=True, text=True)
            try:
                if r9Core.validateString(name):
                    return os.path.join(self.getPoseDir(), '%s.pose' % name)
            except ValueError, error:
                raise ValueError(error)
   
    def __uiCB_setPoseRootNode(self, *args):
        '''
        This changes the mode for the Button that fills in rootPath in the poseUI
        Either fills with the given node, or fill it with the connected MetaRig
        '''
        rootNode=cmds.ls(sl=True, l=True)
        
        def fillTextField(text):
            #bound to a function so it can be passed onto the MetaNoode selector UI
            cmds.textFieldButtonGrp('uitfgPoseRootNode', e=True, text=text)
            
        if self.poseRootMode=='RootNode':
            if not rootNode:
                raise StandardError('Warning nothing selected')
            fillTextField(rootNode[0])
        elif self.poseRootMode=='MetaRoot':
            if rootNode:
                #metaRig=r9Meta.getConnectedMetaNodes(rootNode[0])
                metaRig=r9Meta.getConnectedMetaSystemRoot(rootNode[0])
                if not metaRig:
                    raise StandardError("Warning selected node isn't connected to a MetaRig node")
                fillTextField(metaRig.mNode)
            else:
                metaRigs=r9Meta.getMetaNodes(dataType='mClass')
                if metaRigs:
                    r9Meta.MClassNodeUI(closeOnSelect=True,\
                                        funcOnSelection=fillTextField,\
                                        mInstances=['MetaRig'],\
                                        allowMulti=False)._showUI()
                else:
                    
                    raise StandardError("Warning: No MetaRigs found in the Scene")
        #fill the cache up for the ini file
        self.ANIM_UI_OPTVARS['AnimationUI']['poseRoot']=cmds.textFieldButtonGrp('uitfgPoseRootNode', q=True, text=True)
        self.__uiCache_storeUIElements()
        
    def __uiCB_managePoseRootMethod(self, *args):
        '''
        Manage the PoseRootNode method, either switch to standard rootNode or MetaNode
        '''
        if cmds.checkBox('uicbMetaRig', q=True, v=True):
            self.poseRootMode='MetaRoot'
            cmds.textFieldButtonGrp('uitfgPoseRootNode', e=True, bl='MetaRoot')
        else:
            self.poseRootMode='RootNode'
            cmds.textFieldButtonGrp('uitfgPoseRootNode', e=True, bl='SetRoot')
        self.__uiCache_storeUIElements()
        
    def __uiCB_getPoseInputNodes(self):
        '''
        Node passed into the __PoseCalls in the UI
        '''
        posenodes=[]
        setRoot=cmds.textFieldButtonGrp('uitfgPoseRootNode', q=True, text=True)
        if cmds.checkBox('uicbPoseHierarchy', q=True, v=True):
            #hierarchy processing so we MUST pass a root in
            if not setRoot or not cmds.objExists(setRoot):
                raise StandardError('RootNode not Set for Hierarchy Processing')
            else:
                return setRoot
        else:
            posenodes=cmds.ls(sl=True, l=True)
        if not posenodes:
            raise StandardError('No Nodes Set or selected for Pose')
        return posenodes
    
    def __uiCB_enableRelativeSwitches(self, *args):
        '''
        switch the relative mode on for the poseLaoder
        '''
        self.__uiCache_addCheckbox('uicbPoseRelative')
        state = cmds.checkBox(self.uicbPoseRelative, q=True, v=True)
        cmds.checkBox('uicbPoseSpace', e=True, en=False)
        #if cmds.checkBox('uicbMetaRig',q=True,v=True):
        cmds.checkBox('uicbPoseSpace', e=True, en=state)
        cmds.frameLayout(self.uiflPoseRelativeFrame, e=True, en=state)
             
    def __uiPoseDelete(self, *args):
        self.__validatePoseFunc('DeletePose')
        result = cmds.confirmDialog(
                title='Confirm Pose Delete',
                button=['Yes', 'Cancel'],
                message='confirm deletion of pose file: "%s"' % self.poseSelected,
                defaultButton='Yes',
                cancelButton='Cancel',
                dismissString='Cancel')
        if result == 'Yes':
            try:
                os.remove(self.getPosePath())
            except:
                log.info('Failed to Delete PoseFile')
            try:
                os.remove(self.getIconPath())
            except:
                log.info('Failed to Delete PoseIcon')
            self.__uiCB_fillPoses(rebuildFileList=True)
        
    def __uiPoseRename(self, *args):
        try:
            newName=self.__uiCB_savePosePath(self.getPoseSelected())
        except ValueError, error:
            raise ValueError(error)
        try:
            os.rename(self.getPosePath(), newName)
            os.rename(self.getIconPath(), '%s.bmp' % newName.split('.pose')[0])
        except:
            log.info('Failed to Rename Pose')
        self.__uiCB_fillPoses(rebuildFileList=True)
        pose=os.path.basename(newName.split('.pose')[0])
        self.__uiCB_selectPose(pose)
        
    def __uiPoseOpenFile(self, *args):
        import subprocess
        path=os.path.normpath(self.getPosePath())
        subprocess.Popen('notepad "%s"' % path)
        
    def __uiPoseOpenDir(self, *args):
        import subprocess
        path=os.path.normpath(self.getPoseDir())
        subprocess.Popen('explorer "%s"' % path)
     
    def __uiPoseUpdate(self, storeThumbnail, *args):
        self.__validatePoseFunc('UpdatePose')
        result = cmds.confirmDialog(
                title='PoseUpdate',
                message=('<< Replace & Update Pose file >>\n\n%s' % self.poseSelected),
                button=['OK', 'Cancel'],
                defaultButton='OK',
                cancelButton='Cancel',
                dismissString='Cancel')
        if result=='OK':
            if storeThumbnail:
                try:
                    os.remove(self.getIconPath())
                except:
                    log.debug('unable to delete the Pose Icon file')
            self.__PoseSave(self.getPosePath(), storeThumbnail)
            self.__uiCB_selectPose(self.poseSelected)
    
    def __uiPoseUpdateThumb(self, *args):
        sel=cmds.ls(sl=True, l=True)
        cmds.select(cl=True)
        thumbPath=self.getIconPath()
        if os.path.exists(thumbPath):
            try:
                os.remove(thumbPath)
            except:
                log.error('Unable to delete the Pose Icon file')
        r9General.thumbNailScreen(thumbPath, 128, 128)
        if sel:
            cmds.select(sel)
        self.__uiCB_fillPoses()
        self.__uiCB_selectPose(self.poseSelected)

        
    def __uiPoseSelectObjects(self, *args):
        '''
        Select matching internal nodes
        '''
        rootNode=cmds.textFieldButtonGrp('uitfgPoseRootNode', q=True, text=True)
        if rootNode and cmds.objExists(rootNode):
            self.__uiPresetFillFilter()  # fill the filterSettings Object
            pose=r9Pose.PoseData(self.filterSettings)
            pose._readPose(self.getPosePath())
            nodes=pose.matchInternalPoseObjects(rootNode)
            if nodes:
                cmds.select(cl=True)
                [cmds.select(node, add=True) for node in nodes]
        else:
            raise StandardError('RootNode not Set for Hierarchy Processing')
      
    def __uiPoseMakeSubFolder(self, handlerFile=None, *args):
        '''
        Insert a new SubFolder to the posePath, makes the dir and sets
        it up in the UI to be the current active path
        '''
        basePath=cmds.textFieldButtonGrp('uitfgPosePath', query=True, text=True)
        if not os.path.exists(basePath):
            raise StandardError('Base Pose Path is inValid or not yet set')
        promptstring='New Pose Folder Name'
        if handlerFile:
            promptstring='New %s POSE Folder Name' % os.path.basename(handlerFile).replace('_poseHandler.py','').upper()
        result = cmds.promptDialog(
                title=promptstring,
                message='Enter Name:',
                button=['OK', 'Cancel'],
                defaultButton='OK',
                cancelButton='Cancel',
                dismissString='Cancel')
        if result == 'OK':
            subFolder=cmds.promptDialog(query=True, text=True)
            cmds.textFieldButtonGrp('uitfgPoseSubPath', edit=True, text=subFolder)
            self.posePath=os.path.join(basePath, subFolder)
            os.mkdir(self.posePath)
            if handlerFile and os.path.exists(handlerFile):
                shutil.copy(handlerFile, self.posePath)
            self.__uiCB_pathSwitchInternals()
                
    def __uiPoseCopyToProject(self, *args):
        '''
        Copy local pose to the Project Pose Folder
        TODO: have a way to let the user select the ProjectSubfolder the
        pose gets copied down too
        '''
        import shutil
        syncSubFolder=True
        projectPath=self.posePathProject
        if not os.path.exists(self.posePathProject):
            raise StandardError('Project Pose Path is inValid or not yet set')
        if syncSubFolder:
            subFolder=self.getPoseSubFolder()
            projectPath=os.path.join(projectPath, subFolder)
            
            if not os.path.exists(projectPath):
                result = cmds.confirmDialog(
                    title='Add Project Sub Folder',
                    message='Add a matching subFolder to the project pose path?',
                    button=['Make', 'CopyToRoot', 'Cancel'],
                    defaultButton='OK',
                    cancelButton='Cancel',
                    dismissString='Cancel')
                if result == 'Make':
                    try:
                        os.mkdir(projectPath)
                        log.debug('New Folder Added to ProjectPosePath: %s' % projectPath)
                    except:
                        raise StandardError('Failed to make the SubFolder path')
                elif result =='CopyToRoot':
                    projectPath=self.posePathProject
                else:
                    return
            
        log.info('Copying Local Pose: %s >> %s' % (self.poseSelected, projectPath))
        try:
            shutil.copy2(self.getPosePath(), projectPath)
            shutil.copy2(self.getIconPath(), projectPath)
        except:
            raise StandardError('Unable to copy pose : %s > to Project dirctory' % self.poseSelected)
                     
    def __uiPoseAddPoseHandler(self, *args):
        '''
        PRO_PACK : Copy local pose to the Project Pose Folder
        '''
        r9Setup.PRO_PACK_STUBS().AnimationUI_stubs.uiCB_poseAddPoseHandler(self.posePath)
        
        
    # ------------------------------------------------------------------------------
    # UI Elements ConfigStore Callbacks --------------------------------------------

    def __uiCache_storeUIElements(self, *args):
        '''
        Store some of the main components of the UI out to an ini file
        '''
        if not self.uiBoot:
            log.debug('UI configFile being written')
            ConfigObj = configobj.ConfigObj(indent_type='\t')
            self.__uiPresetFillFilter()  # fill the internal filterSettings obj
            self.ANIM_UI_OPTVARS['AnimationUI']['ui_docked'] = self.dock
            ConfigObj['filterNode_settings'] = self.filterSettings.__dict__
            ConfigObj['AnimationUI'] = self.ANIM_UI_OPTVARS['AnimationUI']
            ConfigObj.filename = self.ui_optVarConfig
            ConfigObj.write()
        
    def __uiCache_loadUIElements(self):
        '''
        Restore the main UI elements from the ini file
        '''
        self.uiBoot = True
        try:
            log.debug('Loading UI Elements from the config file')
            def __uiCache_LoadCheckboxes():
                #if self.ANIM_UI_OPTVARS['AnimationUI'].has_key('checkboxes'):
                if 'checkboxes' in self.ANIM_UI_OPTVARS['AnimationUI'] and \
                            self.ANIM_UI_OPTVARS['AnimationUI']['checkboxes']:
                    for cb, status in self.ANIM_UI_OPTVARS['AnimationUI']['checkboxes'].items():
                        cmds.checkBox(cb, e=True, v=r9Core.decodeString(status))
                
            AnimationUI = self.ANIM_UI_OPTVARS['AnimationUI']

            if self.basePreset:
                try:
                    cmds.textScrollList(self.uitslPresets, e=True, si=self.basePreset)
                    self.__uiPresetSelection(Read=True)
                except:
                    log.debug('given basePreset not found')
            if 'filterNode_preset' in AnimationUI and AnimationUI['filterNode_preset']:
                cmds.textScrollList(self.uitslPresets, e=True, si=AnimationUI['filterNode_preset'])
                self.__uiPresetSelection(Read=True)  # ##not sure on this yet????
            if 'keyPasteMethod' in AnimationUI and AnimationUI['keyPasteMethod']:
                cmds.optionMenu('om_PasteMethod', e=True, v=AnimationUI['keyPasteMethod'])
            if 'matchMethod' in AnimationUI and AnimationUI['matchMethod']:
                cmds.optionMenu('om_MatchMethod', e=True, v=AnimationUI['matchMethod'])
            if 'poseMode' in AnimationUI and AnimationUI['poseMode']:
                self.poseGridMode = AnimationUI['poseMode']
            if 'posePathMode' in AnimationUI and AnimationUI['posePathMode']:
                self.posePathMode = AnimationUI['posePathMode']
            if 'posePathLocal' in AnimationUI and AnimationUI['posePathLocal']:
                self.posePathLocal = AnimationUI['posePathLocal']
            if 'posePathProject' in AnimationUI and AnimationUI['posePathProject']:
                self.posePathProject = AnimationUI['posePathProject']
            if 'poseSubPath' in AnimationUI and AnimationUI['poseSubPath']:
                cmds.textFieldButtonGrp('uitfgPoseSubPath', edit=True, text=AnimationUI['poseSubPath'])
            if 'poseRoot' in AnimationUI and AnimationUI['poseRoot']:
                if cmds.objExists(AnimationUI['poseRoot']):
                    cmds.textFieldButtonGrp('uitfgPoseRootNode', e=True, text=AnimationUI['poseRoot'])
                    
            __uiCache_LoadCheckboxes()
            
            #callbacks
            if self.posePathMode:
                print 'setting : ', self.posePathMode
                cmds.radioCollection(self.uircbPosePathMethod, edit=True, select=self.posePathMode)
            self.__uiCB_enableRelativeSwitches()  # relativePose switch enables
            self.__uiCB_managePoseRootMethod()  # metaRig or SetRootNode for Pose Root
            self.__uiCB_switchPosePathMode(self.posePathMode)  # pose Mode - 'local' or 'project'
            self.__uiCB_manageSnapHierachy()  # preCopyAttrs
            self.__uiCB_manageSnapTime()  # preCopyKeys
            
            
        except StandardError, err:
            log.debug('failed to complete UIConfig load')
            log.warning(err)
        finally:
            self.uiBoot=False
                
    def __uiCache_readUIElements(self):
        '''
        read the config ini file for the initial state of the ui
        '''
        try:
            if os.path.exists(self.ui_optVarConfig):
                self.filterSettings.read(self.ui_optVarConfig)  # use the generic reader for this
                self.ANIM_UI_OPTVARS['AnimationUI']=configobj.ConfigObj(self.ui_optVarConfig)['AnimationUI']
            else:
                self.ANIM_UI_OPTVARS['AnimationUI']={}
        except:
            pass
        
    def __uiCache_addCheckbox(self, checkbox):
        '''
        Now shifted into a sub dic for easier processing
        '''
        if not 'checkboxes' in self.ANIM_UI_OPTVARS['AnimationUI']:
            self.ANIM_UI_OPTVARS['AnimationUI']['checkboxes'] = {}
        self.ANIM_UI_OPTVARS['AnimationUI']['checkboxes'][checkbox] = cmds.checkBox(checkbox, q=True, v=True)
        self.__uiCache_storeUIElements()
    
    def __uiCache_resetDefaults(self, *args):
        defaultConfig=os.path.join(self.presetDir, '__red9animreset__')
        if os.path.exists(defaultConfig):
            self.ANIM_UI_OPTVARS['AnimationUI']=configobj.ConfigObj(defaultConfig)['AnimationUI']
            self.__uiCache_loadUIElements()
        
        
    # MAIN UI FUNCTION CALLS
    #------------------------------------------------------------------------------
    
    def __CopyAttrs(self):
        '''
        Internal UI call for CopyAttrs
        '''
        if not len(cmds.ls(sl=True, l=True)) >= 2:
            log.warning('Please Select at least 2 nodes to Process!!')
            return
        self.kws['toMany'] = cmds.checkBox(self.uicbCAttrToMany, q=True, v=True)
        if cmds.checkBox(self.uicbCAttrChnAttrs, q=True, v=True):
            self.kws['attributes'] = getChannelBoxSelection()
        if cmds.checkBox(self.uicbCAttrHierarchy, q=True, v=True):
            if self.kws['toMany']:
                AnimFunctions(matchMethod=self.matchMethod).copyAttrs_ToMultiHierarchy(cmds.ls(sl=True, l=True),
                                                          filterSettings=self.filterSettings,
                                                          **self.kws)
            else:
                AnimFunctions(matchMethod=self.matchMethod).copyAttributes(nodes=None, filterSettings=self.filterSettings, **self.kws)
        else:
            print self.kws
            AnimFunctions(matchMethod=self.matchMethod).copyAttributes(nodes=None, **self.kws)
            
    def __CopyKeys(self):
        '''
        Internal UI call for CopyKeys call
        '''
        if not len(cmds.ls(sl=True, l=True)) >= 2:
            log.warning('Please Select at least 2 nodes to Process!!')
            return
        self.kws['toMany'] = cmds.checkBox(self.uicbCKeyToMany, q=True, v=True)
        self.kws['pasteKey']=cmds.optionMenu('om_PasteMethod', q=True, v=True)
        self.kws['mergeLayers']=cmds.checkBox('uicbCKeyAnimLay', q=True, v=True)
        self.kws['timeOffset']=cmds.floatFieldGrp('uiffgCKeyStep', q=True,v1=True)
        if cmds.checkBox(self.uicbCKeyRange, q=True, v=True):
            self.kws['time'] = timeLineRangeGet()
        if cmds.checkBox(self.uicbCKeyChnAttrs, q=True, v=True):
            self.kws['attributes'] = getChannelBoxSelection()
        if cmds.checkBox(self.uicbCKeyHierarchy, q=True, v=True):
            if self.kws['toMany']:
                AnimFunctions(matchMethod=self.matchMethod).copyKeys_ToMultiHierarchy(cmds.ls(sl=True, l=True),
                                                          filterSettings=self.filterSettings,
                                                          **self.kws)
            else:
                AnimFunctions(matchMethod=self.matchMethod).copyKeys(nodes=None, filterSettings=self.filterSettings, **self.kws)
        else:
            AnimFunctions(matchMethod=self.matchMethod).copyKeys(nodes=None, **self.kws)
    
    def __Snap(self):
        '''
        Internal UI call for Snap Transforms
        '''
        if not len(cmds.ls(sl=True, l=True)) >= 2:
            log.warning('Please Select at least 2 nodes to Process!!')
            return
        self.kws['preCopyKeys'] = False
        self.kws['preCopyAttrs'] = False
        self.kws['prioritySnapOnly'] = False
        self.kws['iterations'] = cmds.intFieldGrp('uiifSnapIterations', q=True, v=True)[0]
        self.kws['step'] = cmds.intFieldGrp('uiifgSnapStep', q=True, v=True)[0]
        self.kws['pasteKey'] = cmds.optionMenu('om_PasteMethod', q=True, v=True)
        self.kws['mergeLayers'] = True
        self.kws['snapTranslates'] = cmds.checkBox('uicbStanTrans', q=True, v=True)
        self.kws['snapRotates'] = cmds.checkBox('uicbStanRots', q=True, v=True)

        if cmds.checkBox(self.uicbSnapRange, q=True, v=True):
            self.kws['time'] = timeLineRangeGet()
        if cmds.checkBox(self.uicbSnapPreCopyKeys, q=True, v=True):
            self.kws['preCopyKeys'] = True
        if cmds.checkBox(self.uicbSnapPreCopyAttrs, q=True, v=True):
            self.kws['preCopyAttrs'] = True
        if cmds.checkBox(self.uicbSnapHierarchy, q=True, v=True):
            self.kws['prioritySnapOnly'] = cmds.checkBox(self.uicbSnapPriorityOnly, q=True, v=True)
            AnimFunctions(matchMethod=self.matchMethod).snapTransform(nodes=None, filterSettings=self.filterSettings, **self.kws)
        else:
            AnimFunctions(matchMethod=self.matchMethod).snapTransform(nodes=None, **self.kws)
    
    def __Stabilize(self, direction):
        '''
        Internal UI call for Stabilize
        '''
        if not len(cmds.ls(sl=True, l=True)) >= 1:
            log.warning('Please Select at least 1 nodes to Process!!')
            return
        time = ()
        step = cmds.floatFieldGrp('uiffgStabStep', q=True, v=True)[0]
        if direction=='back':
            step=-step
        if cmds.checkBox(self.uicbStabRange, q=True, v=True):
            time = timeLineRangeGet()
        AnimFunctions.stabilizer(cmds.ls(sl=True, l=True), time, step,
                                 cmds.checkBox(self.uicbStabTrans, q=True, v=True),
                                 cmds.checkBox(self.uicbStabRots, q=True, v=True))
                                      
    def __TimeOffset(self):
        '''
        Internal UI call for TimeOffset
        '''
        offset = cmds.floatFieldGrp('uiffgTimeOffset', q=True, v=True)[0]
        if cmds.checkBox(self.uicbTimeOffsetRange, q=True, v=True):
            self.kws['timerange'] = timeLineRangeGet()
        self.kws['ripple'] = cmds.checkBox(self.uicbTimeOffsetRipple, q=True, v=True)
            
        if cmds.checkBox(self.uicbTimeOffsetScene, q=True, v=True):
            r9Core.TimeOffset.fullScene(offset, cmds.checkBox(self.uicbTimeOffsetPlayback, q=True, v=True), **self.kws)
        else:
            self.kws['flocking']= cmds.checkBox(self.uicbTimeOffsetFlocking, q=True, v=True)
            self.kws['randomize'] = cmds.checkBox(self.uicbTimeOffsetRandom, q=True, v=True)

            #self.kws['option'] = "insert" #, "segmentOver"
            if cmds.checkBox(self.uicbTimeOffsetHierarchy, q=True, v=True):
                r9Core.TimeOffset.fromSelected(offset, filterSettings=self.filterSettings, **self.kws)
            else:
                r9Core.TimeOffset.fromSelected(offset, **self.kws)
   
    def __Hierarchy(self):
        '''
        Internal UI call for Test Hierarchy
        '''
        if cmds.ls(sl=True):
            Filter = r9Core.FilterNode(cmds.ls(sl=True, l=True), filterSettings=self.filterSettings)
            try:
                self.filterSettings.printSettings()
                cmds.select(Filter.ProcessFilter())
                log.info('=============  Filter Test Results  ==============')
                print('\n'.join([node for node in Filter.intersectionData]))
                log.info('FilterTest : Object Count Returned : %s' % len(Filter.intersectionData))
            except:
                raise StandardError('Filter Returned Nothing')
        else:
            raise StandardError('No Root Node selected for Filter Testing')
    
    def __PoseSave(self, path=None, storeThumbnail=True):
        '''
        Internal UI call for PoseLibrary Save func, note that filterSettings is bound
        but only filled by the main __uiCall call
        '''
        if not path:
            try:
                path=self.__uiCB_savePosePath()
            except ValueError, error:
                raise ValueError(error)
        poseHierarchy = cmds.checkBox('uicbPoseHierarchy', q=True, v=True)

#         #Work to hook the poseSave directly to the metaRig.poseCacheStore func directly
#         if self.filterSettings.metaRig and r9Meta.isMetaNodeInherited(self.__uiCB_getPoseInputNodes(),
#                                                                       mInstances=r9Meta.MetaRig):
#             print 'active MetaNode, calling poseCacheSave from metaRig subclass'
#             r9Meta.MetaClass(self.__uiCB_getPoseInputNodes()).poseCacheStore(filepath=path,
#                                                                              storeThumbnail=storeThumbnail)
#         else:
        r9Pose.PoseData(self.filterSettings).poseSave(self.__uiCB_getPoseInputNodes(),
                                                      path,
                                                      useFilter=poseHierarchy,
                                                      storeThumbnail=storeThumbnail)
        log.info('Pose Stored to : %s' % path)
        self.__uiCB_fillPoses(rebuildFileList=True)
            
    def __PoseLoad(self):
        '''
        Internal UI call for PoseLibrary Load func, note that filterSettings is bound
        but only filled by the main __uiCall call
        '''
        poseHierarchy = cmds.checkBox('uicbPoseHierarchy', q=True, v=True)
        poseRelative = cmds.checkBox('uicbPoseRelative', q=True, v=True)
        maintainSpaces = cmds.checkBox('uicbPoseSpace', q=True, v=True)
        rotRelMethod = cmds.radioCollection(self.uircbPoseRotMethod, q=True, select=True)
        tranRelMethod = cmds.radioCollection(self.uircbPoseTranMethod, q=True, select=True)
        
        if poseRelative and not cmds.ls(sl=True, l=True):
            log.warning('No node selected to use for reference!!')
            return
        
        relativeRots='projected'
        relativeTrans='projected'
        if not rotRelMethod=='rotProjected':
            relativeRots='absolute'
        if not tranRelMethod=='tranProjected':
            relativeTrans='absolute'
            
        path=self.getPosePath()
        log.info('PosePath : %s' % path)
        poseNode=r9Pose.PoseData(self.filterSettings)
        poseNode.prioritySnapOnly=cmds.checkBox(self.uicbSnapPriorityOnly, q=True, v=True)
        
        poseNode.matchMethod=self.matchMethod  # needs proving as not fully tested yet!!
        
        poseNode.poseLoad(self.__uiCB_getPoseInputNodes(),
                                                      path,
                                                      useFilter=poseHierarchy,
                                                      relativePose=poseRelative,
                                                      relativeRots=relativeRots,
                                                      relativeTrans=relativeTrans,
                                                      maintainSpaces=maintainSpaces)
    
    def __PoseCompare(self, compareDict='skeletonDict', *args):
        '''
        PRO_PACK : Internal UI call for Pose Compare func, note that filterSettings is bound
        but only filled by the main __uiCall call
        '''
        r9Setup.PRO_PACK_STUBS().AnimationUI_stubs.uiCB_poseCompare(filterSettings=self.filterSettings,
                                                                    nodes=self.__uiCB_getPoseInputNodes(),
                                                                    posePath=self.getPosePath(),
                                                                    compareDict=compareDict)
    
    def __PoseBlend(self):
        '''
        TODO: allow this ui and implementation to blend multiple poses at the same time
        basically we'd add a new poseObject per pose and bind each one top the slider
        but with a consistent poseCurrentCache via the _cacheCurrentNodeStates() call
        '''
        objs=cmds.ls(sl=True,l=True)
        poseNode = r9Pose.PoseData(self.filterSettings)
        poseNode.filepath = self.getPosePath()
        poseNode.useFilter = cmds.checkBox('uicbPoseHierarchy', q=True, v=True)
        poseNode.matchMethod=self.matchMethod
        poseNode.processPoseFile(self.__uiCB_getPoseInputNodes())
        self._poseBlendUndoChunkOpen=False
        if objs:
            cmds.select(objs)
        
        def blendPose(*args):
            if not self._poseBlendUndoChunkOpen:
                cmds.undoInfo(openChunk=True)
                self._poseBlendUndoChunkOpen=True
                log.debug('Opening Undo Chunk for PoseBlender')
            poseNode._applyData(percent=cmds.floatSliderGrp('poseBlender', q=True, v=True))
        
        def closeChunk(*args):
            cmds.undoInfo(closeChunk=True)
            self._poseBlendUndoChunkOpen = False
            log.debug('Closing Undo Chunk for PoseBlender')
             
        if cmds.window('poseBlender', exists=True):
            cmds.deleteUI('poseBlender')
        cmds.window('poseBlender')
        cmds.columnLayout()
        cmds.floatSliderGrp('poseBlender',
                            label='Blend Pose:  "%s"  ' % self.getPoseSelected(),
                            field=True,
                            minValue=0.0,
                            maxValue=100.0,
                            value=0,
                            dc=blendPose,
                            cc=closeChunk)
        cmds.showWindow()
            
    def __PosePointCloud(self, func):
        '''
        Note: this is dependant on EITHER a wire from the root of the pose to a GEO
        under the attr 'renderMeshes' OR the second selected object is the reference Mesh
        Without either of these you'll just get a locator as the PPC root
        '''
        objs=cmds.ls(sl=True)
        rootReference=objs[0]
        meshes=[]
        mRef=r9Meta.MetaClass(self.__uiCB_getPoseInputNodes())
        if mRef.hasAttr('renderMeshes') and mRef.renderMeshes:
            meshes=mRef.renderMeshes
        elif len(objs)==2:
            if cmds.nodeType(cmds.listRelatives(objs[1])[0])=='mesh':
                meshes=objs  # [1]
        if func=='make':
            if not objs:
                raise StandardError('you need to select a reference object to use as pivot for the PPCloud')
            #if cmds.ls('*posePointCloud', r=True):
            #    raise StandardError('PosePointCloud already exists in scsne')
            if not meshes:
                #turn on locator visibility
                panel=cmds.getPanel(wf=True)
                if 'modelPanel' in panel:
                    cmds.modelEditor(cmds.getPanel(wf=True), e=True, locators=True)
                else:
                    cmds.modelEditor('modelPanel4', e=True, locators=True)
            self.ppc=r9Pose.PosePointCloud(self.__uiCB_getPoseInputNodes(),
                                           self.filterSettings,
                                           meshes=meshes)
            self.ppc.prioritySnapOnly=cmds.checkBox(self.uicbSnapPriorityOnly, q=True, v=True)
            self.ppc.buildOffsetCloud(rootReference)
        elif func=='delete':
            self.ppc.delete()
        elif func=='snap':
            #self.ppc.applyPosePointCloud()
            self.ppc.applyPosePointCloud()
        elif func=='update':
            self.ppc.updatePosePointCloud()
         
    def __MirrorPoseAnim(self, process, mirrorMode):
        '''
        Internal UI call for Mirror Animation / Pose
        '''

        if not cmds.ls(sl=True, l=True):
            log.warning('Nothing selected to process from!!')
            return
  
        self.kws['pasteKey'] = cmds.optionMenu('om_PasteMethod', q=True, v=True)
        hierarchy=cmds.checkBox('uicbMirrorHierarchy', q=True, v=True)
        
        mirror=MirrorHierarchy(nodes=cmds.ls(sl=True, l=True),
                               filterSettings=self.filterSettings,
                               **self.kws)
        
        #Check for AnimLayers and throw the warning
        if mirrorMode=='Anim':
            #slower as we're processing the mirrorSets twice for hierarchy
            #BUT this is vital info that the user needs prior to running.
            if hierarchy:
                animCheckNodes=mirror.getMirrorSets()
            else:
                animCheckNodes=cmds.ls(sl=True, l=True)
            print animCheckNodes
            if not animLayersConfirmCheck(animCheckNodes):
                log.warning('Process Aborted by User')
                return

        if not hierarchy:
            if process=='mirror':
                mirror.mirrorData(cmds.ls(sl=True, l=True), mode=mirrorMode)
            else:
                mirror.makeSymmetrical(cmds.ls(sl=True, l=True), mode=mirrorMode)
        else:
            if process=='mirror':
                mirror.mirrorData(mode=mirrorMode)
            else:
                mirror.makeSymmetrical(mode=mirrorMode)

                      
    # MAIN CALL
    #------------------------------------------------------------------------------
    def __uiCall(self, func, *args):
        '''
        MAIN ANIMATION UI CALL
        Why not just call the procs directly? well this also manages the collection /pushing
        of the filterSettings data for all procs
        '''
        #issue : up to v2011 Maya puts each action into the UndoQueue separately
        #when called by lambda or partial - Fix is to open an UndoChunk to catch
        #everything in one block
        self.kws = {}

        #If below 2011 then we need to store the undo in a chunk
        if r9Setup.mayaVersion() < 2011:
            cmds.undoInfo(openChunk=True)
            
        # Main Hierarchy Filters =============
        self.__uiPresetFillFilter()  # fill the filterSettings Object
        self.matchMethod = cmds.optionMenu('om_MatchMethod', q=True, v=True)
#         if cmds.checkBox('uicbMatchMethod', q=True, v=True):
#             self.matchMethod='stripPrefix'
#         else:
#             self.matchMethod='base'
        #self.filterSettings.transformClamp = True
         
        try:
            if func == 'CopyAttrs':
                self.__CopyAttrs()
            elif func == 'CopyKeys':
                self.__CopyKeys()
            elif func == 'Snap':
                self.__Snap()
            elif func == 'StabilizeFwd':
                self.__Stabilize('fwd')
            elif func == 'StabilizeBack':
                self.__Stabilize('back')
            elif func == 'TimeOffset':
                self.__TimeOffset()
            elif func == 'HierarchyTest':
                self.__Hierarchy()
            elif func == 'PoseSave':
                self.__PoseSave()
            elif func == 'PoseLoad':
                self.__PoseLoad()
            elif func == 'PoseCompareSkelDict':
                self.__PoseCompare(compareDict='skeletonDict')
            elif func == 'PoseComparePoseDict':
                self.__PoseCompare(compareDict='poseDict')
            elif func == 'PosePC_Make':
                self.__PosePointCloud('make')
            elif func == 'PosePC_Delete':
                self.__PosePointCloud('delete')
            elif func == 'PosePC_Snap':
                self.__PosePointCloud('snap')
            elif func == 'PosePC_Update':
                self.__PosePointCloud('update')
            elif func == 'PoseBlender':
                self.__PoseBlend()
            elif func =='MirrorAnim':
                self.__MirrorPoseAnim('mirror', 'Anim')
            elif func =='MirrorPose':
                self.__MirrorPoseAnim('mirror', 'Pose')
            elif func =='SymmetryPose':
                self.__MirrorPoseAnim('symmetry', 'Pose')
            elif func =='SymmetryAnim':
                self.__MirrorPoseAnim('symmetry', 'Anim')
                
        except r9Setup.ProPack_Error:
            log.warning('ProPack not Available')
        except StandardError, error:
            traceback = sys.exc_info()[2]  # get the full traceback
            raise StandardError(StandardError(error), traceback)

        # close chunk
        if mel.eval('getApplicationVersionAsFloat') < 2011:
            cmds.undoInfo(closeChunk=True)
            
        self.__uiCache_storeUIElements()
            
       
    
#===========================================================================
# Main AnimFunction code class
#===========================================================================
       
class AnimFunctions(object):
    '''
    Most of the main Animation Functions take a settings object which is 
    responsible for hierarchy processing. See r9Core.FilterNode and 
    r9Core.Filter_Settings for more details. These are then passed to
    the r9Core.MatchedNodeInputs class which is designed specifically
    to process two hierarchies and filter them for matching pairs.
    What this means is that all the anim functions deal with hierarchies
    in the same manor making it very simple to extend.
    
    Generic filters passed into r9Core.MatchedNodeInputs class:
        * setting.nodeTypes: list[] - search for child nodes of type (wraps cmds.listRelatives types=)
        * setting.searchAttrs: list[] - search for child nodes with Attrs of name
        * setting.searchPattern: list[] - search for nodes with a given nodeName searchPattern
        * setting.hierarchy: bool = lsHierarchy code to return all children from the given nodes
        * setting.metaRig: bool = use the MetaRig wires to build the initial Object list up
        
    .. note:: 
        with all the search and hierarchy settings OFF the code performs
        a dumb copy, no matching and no Hierarchy filtering, copies using
        selected pairs obj[0]>obj[1], obj[2]>obj[3] etc


    '''
    def __init__(self, **kws):
        kws.setdefault('matchMethod', 'stripPrefix')
        
        self.matchMethod=kws['matchMethod']  # gives you the ability to modify the nameMatching method
              
    #===========================================================================
    # Copy Keys
    #===========================================================================

    def copyKeys_ToMultiHierarchy(self, nodes=None, time=(), pasteKey='replace',
                 attributes=None, filterSettings=None, matchMethod=None, mergeLayers=True, **kws):
        '''
        This isn't the best way by far to do this, but as a quick wrapper
        it works well enough. Really we need to process the nodes more intelligently
        prior to sending data to the copyKeys calls
        '''
        for node in nodes[1:]:
            self.copyKeys(nodes=[nodes[0], node],
                          time=time,
                          attributes=attributes,
                          pasteKey=pasteKey,
                          filterSettings=filterSettings,
                          toMany=False,
                          matchMethod=matchMethod,
                          mergeLayers=mergeLayers)
               
    @r9General.Timer
    def copyKeys(self, nodes=None, time=(), pasteKey='replace', attributes=None,
                 filterSettings=None, toMany=False, matchMethod=None, mergeLayers=False, timeOffset=0, **kws):
        '''
        Copy Keys is a Hi-Level wrapper function to copy animation data between
        filtered nodes, either in hierarchies or just selected pairs.
                
        :param nodes: List of Maya nodes to process. This combines the filterSettings
            object and the MatchedNodeInputs.processMatchedPairs() call,
            making it capable of powerful hierarchy filtering and node matching methods.
        :param filterSettings: Passed into the decorator and onto the FilterNode code
            to setup the hierarchy filters - See docs on the FilterNode_Settings class
        :param pasteKey: Uses the standard pasteKey option methods - merge,replace,
            insert etc. This is fed to the internal pasteKey method. Default=replace
        :param time: Copy over a given timerange - time=(start,end). Default is
            to use no timeRange. If time is passed in via the timeLineRange() function
            then it will consider the current timeLine PlaybackRange, OR if you have a
            highlighted range of time selected(in red) it'll use this instead.
        :param attributes: Only copy the given attributes[]
        :param matchMethod: arg passed to the match code, sets matchMethod used to match 2 node names
        :param mergeLayers: this pre-processes animLayers so that we have a single, temporary merged
            animLayer to extract a compiled version of the animData from. This gets deleted afterwards.
        
        TODO: this needs to support 'skipAttrs' param like the copyAttrs does - needed for the snapTransforms calls
        '''
        if not matchMethod:
            matchMethod=self.matchMethod
        log.debug('CopyKey params : nodes=%s : time=%s : pasteKey=%s : attributes=%s : filterSettings=%s : matchMethod=%s'\
                   % (nodes, time, pasteKey, attributes, filterSettings, matchMethod))
                
        #Build up the node pairs to process
        nodeList = r9Core.processMatchedNodes(nodes,
                                              filterSettings,
                                              toMany,
                                              matchMethod=matchMethod).MatchedPairs
        
        srcNodes=[src for src, _ in nodeList]
        
        # Manage AnimLayers - note to Autodesk, this should be internal to the cmds!
        with AnimationLayerContext(srcNodes, mergeLayers=mergeLayers, restoreOnExit=True):
            if nodeList:
                with r9General.HIKContext([d for _, d in nodeList]):
                    for src, dest in nodeList:
                        try:
                            if attributes:
                                #copy only specific attributes
                                for attr in attributes:
                                    if cmds.copyKey(src, attribute=attr, hierarchy=False, time=time):
                                        cmds.pasteKey(dest, attribute=attr, option=pasteKey, timeOffset=timeOffset)
                            else:
                                if cmds.copyKey(src, hierarchy=False, time=time):
                                    cmds.pasteKey(dest, option=pasteKey, timeOffset=timeOffset)
                        except:
                            log.debug('Failed to copyKeys between : %s >> %s' % (src, dest))
            else:
                raise StandardError('Nothing found by the Hierarchy Code to process')
        return True
    
    
    #===========================================================================
    # Copy Attributes
    #===========================================================================

    def copyAttrs_ToMultiHierarchy(self, nodes=None, attributes=None, skipAttrs=None, \
                       filterSettings=None, matchMethod=None, **kws):
        '''
        This isn't the best way by far to do this, but as a quick wrapper
        it works well enough. Really we need to process the nodes more intelligently
        prior to sending data to the copyKeys calls
        '''
        for node in nodes[1:]:
            self.copyAttributes(nodes=[nodes[0], node],
                          attributes=attributes,
                          filterSettings=filterSettings,
                          skipAttrs=skipAttrs,
                          toMany=False,
                          matchMethod=matchMethod)
            

    def copyAttributes(self, nodes=None, attributes=None, skipAttrs=None,
                       filterSettings=None, toMany=False, matchMethod=None, **kws):
        '''
        Copy Attributes is a Hi-Level wrapper function to copy Attribute data between
        filtered nodes, either in hierarchies or just selected pairs.
                
        :param nodes: List of Maya nodes to process. This combines the filterSettings
            object and the MatchedNodeInputs.processMatchedPairs() call,
            making it capable of powerful hierarchy filtering and node matching methods.
        :param filterSettings: Passed into the decorator and onto the FilterNode code
            to setup the hierarchy filters - See docs on the FilterNode_Settings class
        :param attributes: Only copy the given attributes[]
        :param skipAttrs: Copy all Settable Attributes OTHER than the given, not
            used if an attributes list is passed
        :param matchMethod: arg passed to the match code, sets matchMethod used to match 2 node names

        '''
        if not matchMethod:
            matchMethod=self.matchMethod
        log.debug('CopyAttributes params : nodes=%s\n : attributes=%s\n : filterSettings=%s\n : matchMethod=%s\n'
                   % (nodes, attributes, filterSettings, matchMethod))
        
        #Build up the node pairs to process
        nodeList = r9Core.processMatchedNodes(nodes,
                                              filterSettings,
                                              toMany,
                                              matchMethod=matchMethod).MatchedPairs
        
        if nodeList:
            with r9General.HIKContext([d for _, d in nodeList]):
                for src, dest in nodeList:
                    try:
                        if attributes:
                            #copy only specific attributes
                            for attr in attributes:
                                if cmds.attributeQuery(attr, node=src, exists=True) \
                                    and cmds.attributeQuery(attr, node=src, exists=True):
                                    cmds.setAttr('%s.%s' % (dest, attr), cmds.getAttr('%s.%s' % (src, attr)))
                        else:
                            attrs = []
                            settableAttrs = getSettableChannels(src, incStatics=True)
                            if skipAttrs:
                                attrs = set(settableAttrs) - set(skipAttrs)
                            else:
                                attrs = settableAttrs
                                
                            for attr in attrs:
                                if cmds.attributeQuery(attr, node=dest, exists=True):
                                    try:
                                        log.debug('copyAttr : %s.%s > %s.%s' % (r9Core.nodeNameStrip(dest),
                                                                        r9Core.nodeNameStrip(attr),
                                                                        r9Core.nodeNameStrip(src),
                                                                        r9Core.nodeNameStrip(attr)))
                                        cmds.setAttr('%s.%s' % (dest, attr), cmds.getAttr('%s.%s' % (src, attr)))
                                    except:
                                        log.debug('failed to copyAttr : %s.%s > %s.%s' % (r9Core.nodeNameStrip(dest),
                                                                        r9Core.nodeNameStrip(attr),
                                                                        r9Core.nodeNameStrip(src),
                                                                        r9Core.nodeNameStrip(attr)))
                    except:
                        pass
        else:
            raise StandardError('Nothing found by the Hierarchy Code to process')
        return True
    
    
    #===========================================================================
    # Transform Snapping
    #===========================================================================
    
    @r9General.Timer
    def snapTransform(self, nodes=None, time=(), step=1, preCopyKeys=1, preCopyAttrs=1, filterSettings=None,
                      iterations=1, matchMethod=None, prioritySnapOnly=False, snapRotates=True, snapTranslates=True, **kws):
        '''
        Snap objects over a timeRange. This wraps the default hierarchy filters
        so it's capable of multiple hierarchy filtering and matching methods.
        The resulting node lists are snapped over time and keyed.
        :requires: SnapRuntime plugin to be available
        
        :param nodes: List of Maya nodes to process. This combines the filterSettings
            object and the MatchedNodeInputs.processMatchedPairs() call,
            making it capable of powerful hierarchy filtering and node matching methods.
        :param filterSettings: Passed into the decorator and onto the FilterNode code
            to setup the hierarchy filters - See docs on the FilterNode_Settings class
        :param time: Copy over a given timerange - time=(start,end). Default is
            to use no timeRange. If time is passed in via the timeLineRange() function
            then it will consider the current timeLine PlaybackRange, OR if you have a
            highlighted range of time selected(in red) it'll use this instead.
        :param step: Time Step between processing when using kws['time'] range
            this accepts negative values to run the time backwards if required
        :param preCopyKeys: Run a CopyKeys pass prior to snap - this means that
            all channels that are keyed have their data taken across
        :param preCopyAttrs: Run a CopyAttrs pass prior to snap - this means that
            all channel Values on all nodes will have their data taken across
        :param iterations: Number of times to process the frame.
        :param matchMethod: arg passed to the match code, sets matchMethod used to match 2 node names
        :param prioritySnapOnly: if True ONLY snap the nodes in the filterPriority list withing the filterSettings object = Super speed up!!
        :param snapTranslates: only snap the translate data
        :param snapRotates: only snap the rotate data
        
        .. note:: 
            you can also pass the CopyKey kws in to the preCopy call, see copyKeys above
        
        .. note:: 
            using prioritySnap with animLayers may produce unexpected results! CopyKeys doesn't yet
            deal correctly with animLayer data when copying, it will only copy from the first active layer,
            really need to merge layers down first!!
        
        '''
        self.snapCacheData = {}  # TO DO - Cache the data and check after first run data is all valid
        self.nodesToSnap = []
        skipAttrs = ['translateX', 'translateY', 'translateZ', 'rotateX', 'rotateY', 'rotateZ']
        if not matchMethod:
            matchMethod = self.matchMethod
        try:
            checkRunTimeCmds()
        except StandardError, error:
            raise StandardError(error)
        cancelled = False
        
        log.debug('snapTransform params : nodes=%s : time=%s : step=%s : preCopyKeys=%s : \
preCopyAttrs=%s : filterSettings=%s : matchMethod=%s : prioritySnapOnly=%s : snapTransforms=%s : snapRotates=%s' \
                   % (nodes, time, step, preCopyKeys, preCopyAttrs, filterSettings, matchMethod, prioritySnapOnly, snapTranslates, snapRotates))
        
        #Build up the node pairs to process
        nodeList = r9Core.processMatchedNodes(nodes, filterSettings, matchMethod=matchMethod)
        if nodeList.MatchedPairs:
            nodeList.MatchedPairs.reverse()  # reverse order so we're dealing with children before their parents
            #if prioritySnap then we snap align ONLY those nodes that
            #are in the filterSettings priority list. VAST speed increase
            #by doing this. If the list is empty we revert to turning the flag off
            if prioritySnapOnly and filterSettings.filterPriority:
                for pNode in filterSettings.filterPriority:
                    for src, dest in nodeList.MatchedPairs:
                        if re.search(pNode, r9Core.nodeNameStrip(dest)):
                            self.nodesToSnap.append((src, dest))
                skipAttrs = []  # reset as we need to now copy all attrs
            else:
                self.nodesToSnap=nodeList.MatchedPairs
                
            if preCopyAttrs:
                self.copyAttributes(nodes=nodeList, skipAttrs=skipAttrs, filterSettings=filterSettings, **kws)
            if time:
                with r9General.AnimationContext():  # Context manager to restore settings
                    cmds.autoKeyframe(state=False)
                    #run a copyKeys pass to take all non transform data over
                    #maybe do a channel attr pass to get non-keyed data over too?
                    if preCopyKeys:
                        self.copyKeys(nodes=nodeList, time=time, filterSettings=filterSettings, **kws)
                    
                    progressBar = r9General.ProgressBarContext(time[1]-time[0])
                    progressBar.setStep(step)
                    count=0
                    
                    with progressBar:
                        for t in timeLineRangeProcess(time[0], time[1], step, incEnds=True):
                            if progressBar.isCanceled():
                                cancelled =True
                                break
                            dataAligned = False
                            processRepeat = iterations
                           
                            while not dataAligned:
                                for src, dest in self.nodesToSnap:  # nodeList.MatchedPairs:
                                    #we'll use the API MTimeControl in the runtime function
                                    #to update the scene without refreshing the Viewports
                                    cmds.currentTime(t, e=True, u=False)
                                    #pass to the plug-in SnapCommand
                                    cmds.SnapTransforms(source=src, destination=dest,
                                                        timeEnabled=True,
                                                        snapRotates=snapRotates,
                                                        snapTranslates=snapTranslates)
                                    #fill the snap cache for error checking later
                                    #self.snapCacheData[dest]=data
                                    if snapTranslates:
                                        cmds.setKeyframe(dest, at='translate')
                                    if snapRotates:
                                        cmds.setKeyframe(dest, at='rotate')
                                    log.debug('Snapfrm %s : %s - %s : to : %s' % (str(t), r9Core.nodeNameStrip(src), dest, src))

                                processRepeat -= 1
                                if not processRepeat:
                                    dataAligned = True
                            progressBar.setProgress(count)
                            count+=step
            else:
                for _ in range(0, iterations):
                    for src, dest in self.nodesToSnap:  # nodeList.MatchedPairs:
                        cmds.SnapTransforms(source=src, destination=dest,
                                            timeEnabled=False,
                                            snapRotates=snapRotates,
                                            snapTranslates=snapTranslates)
                        #self.snapCacheData[dest]=data
                        log.debug('Snapped : %s - %s : to : %s' % (r9Core.nodeNameStrip(src), dest, src))
                         
            if cancelled and preCopyKeys:
                cmds.undo()
        else:
            raise StandardError('Nothing found by the Hierarchy Code to process')
        return True


    def snapValidateResults(self):
        '''
        Run through the stored snap values to see if, once everything is processed,
        all the nodes still match. ie, you snap the Shoulders and strore the results,
        then at the end of the process you find that the Shoulders aren't in the same
        position due to a driver controller shifting it because of hierarchy issues.
        TO IMPLEMENT
        '''
        raise NotImplemented
    
    @staticmethod
    def snap(nodes=None, snapTranslates=True, snapRotates=True):
        '''
        This takes 2 given transform nodes and snaps them together. It takes into
        account offsets in the pivots of the objects. Uses the API MFnTransform nodes
        to calculate the data via a command plugin. This is a stripped down version
        of the snapTransforms cmd
        '''
        try:
            checkRunTimeCmds()
        except StandardError, error:
            raise StandardError(error)
        
        if not nodes:
            nodes = cmds.ls(sl=True, l=True)
        if nodes:
            if not len(nodes) >= 2:
                raise StandardError('Please select at least 2 base objects for the SnapAlignment')
        else:
            raise StandardError('Please select at least 2 base objects for the SnapAlignment')
        
        #pass to the plugin SnapCommand
        for node in nodes[1:]:
            cmds.SnapTransforms(source=nodes[0], destination=node, snapTranslates=snapTranslates, snapRotates=snapRotates)
 
        
    @staticmethod
    def stabilizer(nodes=None, time=(), step=1, trans=True, rots=True):
        '''
        This is designed with 2 specific functionalities:
        If you have a single node selected it will stabilize it regardless
        of it's inputs or parent hierarchy animations
        If you pass in 2 objects then it will Track B to A (same order as constraints)
        This is primarily designed to aid in MoCap cleanup and character interactions.
        This now also allows for Component based track inputs, ie, track this
        nodes to this poly's normal

        :param nodes: either single (Stabilize) or twin to track
        :param time: [start,end] for a frameRange
        :param step: int value for frame advance between process runs
        '''
        
        #destObj = None  #Main Object being manipulated and keyed
        #snapRef = None  #Tracking ReferenceObject Used to Pass the transforms over
        deleteMe = []
        
        #can't use the anim context manager here as that resets the currentTime
        autokeyState = cmds.autoKeyframe(query=True, state=True)
        cmds.autoKeyframe(state=False)
        
        try:
            checkRunTimeCmds()
        except StandardError, error:
            raise StandardError(error)
        
        if time:
            timeRange = timeLineRangeProcess(time[0], time[1], step, incEnds=True)
            cmds.currentTime(timeRange[0], e=True)  # ensure that the initial time is updated
        else:
            timeRange = [cmds.currentTime(q=True) + step]
        log.debug('timeRange : %s', timeRange)
        
        if not nodes:
            nodes = cmds.ls(sl=True, l=True)
             
        destObj = nodes[-1]
        snapRef = cmds.spaceLocator()[0]
        deleteMe.append(snapRef)
        
        # Generate the reference node that we'll use to snap too
        # ==========================================================
        if len(nodes) == 2:
            # Tracker Mode 2 nodes passed in - Reference taken against the source node position
            offsetRef = nodes[0]
            
            if cmds.nodeType(nodes[0]) == 'mesh':  # Component level selection method
                if r9Setup.mayaVersion() >= 2011:
                    offsetRef = cmds.spaceLocator()[0]
                    deleteMe.append(offsetRef)
                    cmds.select([nodes[0], offsetRef])
                    pointOnPolyCmd([nodes[0], offsetRef])
                else:
                    raise StandardError('Component Level Tracking is only available in Maya2011 upwards')
            
            cmds.parent(snapRef, offsetRef)
            cmds.SnapTransforms(source=destObj, destination=snapRef, snapTranslates=trans, snapRotates=rots)
        else:
            # Stabilizer Mode - take the reference from the node position itself
            cmds.SnapTransforms(source=destObj, destination=snapRef, snapTranslates=trans, snapRotates=rots)

        #Now run the snap against the reference node we've just made
        #==========================================================
        for time in timeRange:
            #Switched to using the Commands time query to stop  the viewport updates
            cmds.currentTime(time, e=True, u=False)
            cmds.SnapTransforms(source=snapRef, destination=destObj, timeEnabled=True, snapTranslates=trans, snapRotates=rots)
            try:
                if trans:
                    cmds.setKeyframe(destObj, at='translate')
            except:
                log.debug('failed to set translate key on %s' % destObj)
            try:
                if rots:
                    cmds.setKeyframe(destObj, at='rotate')
            except:
                log.debug('failed to set rotate key on %s' % destObj)
                      
        cmds.delete(deleteMe)
        cmds.autoKeyframe(state=autokeyState)
        cmds.select(nodes)
        
        
    def bindNodes(self, nodes=None, attributes=None, filterSettings=None,
                  bindMethod='connect', matchMethod=None, **kws):
        '''
        bindNodes is a Hi-Level wrapper function to bind animation data between
        filtered nodes, either in hierarchies or just selected pairs.
                
        :param nodes: List of Maya nodes to process. This combines the filterSettings
            object and the MatchedNodeInputs.processMatchedPairs() call,
            making it capable of powerful hierarchy filtering and node matching methods.
        :param filterSettings: Passed into the decorator and onto the FilterNode code
            to setup the hierarchy filters - See docs on the FilterNode_Settings class
        :param attributes: Only copy the given attributes[]
        :param bindMethod: method of binding the data
        :param matchMethod: arg passed to the match code, sets matchMethod used to match 2 node names
        #TODO: expose this to the UI's!!!!
        '''
        
        if not matchMethod:
            matchMethod=self.matchMethod
        log.debug('bindNodes params : nodes=%s : attributes=%s : filterSettings=%s : matchMethod=%s' \
                   % (nodes, attributes, filterSettings, matchMethod))

        #Build up the node pairs to process
        nodeList = r9Core.processMatchedNodes(nodes,
                                              filterSettings,
                                              toMany=False,
                                              matchMethod=matchMethod).MatchedPairs
        if nodeList:
            for src, dest in nodeList:
                try:
                    if bindMethod=='connect':
                        if not attributes:
                            attributes = ['rotateX', 'rotateY', 'rotateZ', 'translateX', 'translateY', 'translateZ']
                        #Bind only specific attributes
                        for attr in attributes:
                            log.info('Attr %s bindNode from %s to>> %s' %(attr, r9Core.nodeNameStrip(src),
                                                                          r9Core.nodeNameStrip(dest)))
                            try:
                                cmds.connectAttr('%s.%s' % (src, attr), '%s.%s' % (dest, attr), f=True)
                            except:
                                log.info('bindNode from %s to>> %s' %(r9Core.nodeNameStrip(src),
                                                                      r9Core.nodeNameStrip(dest)))
                    if bindMethod=='constraint':
                        cmds.parentConstraint(src, dest, mo=True)
                except:
                    pass
        else:
            raise StandardError('Nothing found by the Hierarchy Code to process')
        return True
          
    @staticmethod
    def inverseAnimChannels(node, channels, time=None):
        '''
        really basic method used in the Mirror calls
        '''
        #for chan in channels:
            #cmds.scaleKey('%s_%s' % (node,chan),vs=-1)
        if not channels:
            log.debug('abort: no animChannels passed in to inverse')
            return
        if time:
            cmds.scaleKey(node, valueScale=-1, attribute=channels, time=time)
        else:
            cmds.scaleKey(node, valueScale=-1, attribute=channels)
            
            
    @staticmethod
    def inverseAttributes(node, channels):
        '''
        really basic method used in the Mirror calls
        '''
        for chan in channels:
            try:
                cmds.setAttr('%s.%s' % (node, chan), cmds.getAttr('%s.%s' % (node, chan)) * -1)
            except:
                log.debug(cmds.getAttr('%s.%s' % (node, chan)) * -1)
                log.debug('failed to inverse %s.%s attr' % (node, chan))
  

class curveModifierContext(object):
    """
    Simple Context Manager to allow modifications to animCurves in the
    graphEditor interactively by simply managing the undo stack and making
    sure that selections are maintained
    NOTE that this is optimized to run with a floatSlider and used in both interactive
    Randomizer and FilterCurves
    """
    def __init__(self, initialUndo=False, undoFuncCache=[], undoDepth=1):
        '''
        :param initialUndo: on first process whether undo on entry to the context manager
        :param undoFuncCache: functions to catch in the undo stack
        :param undoDepth: depth of the undo stack to go to
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
        
        self.range=None
        self.keysSelected=cmds.keyframe(q=True, n=True, sl=True)
        
        if self.keysSelected:
            self.range=cmds.keyframe(q=True, sl=True, timeChange=True)
            
    def __exit__(self, exc_type, exc_value, traceback):
        if self.keysSelected and self.range:
            cmds.selectKey(self.keysSelected, t=(self.range[0], self.range[-1]))
        cmds.undoInfo(closeChunk=True)
        if exc_type:
            log.exception('%s : %s'%(exc_type, exc_value))
        # If this was false, it would re-raise the exception when complete
        return True



class RandomizeKeys(object):
    '''
    This is a simple implementation of a Key Randomizer, designed to add
    noise to animations.
    
    TODO: add in methods to generate secades type of flicking randomization, current
    implementation is too regular.
    '''
    def __init__(self):
        self.win='KeyRandomizerOptions'
        self.contextManager=curveModifierContext
        self.dragActive=False
        self.toggledState=False
        
        #catch the current state of the GrapthEditor so that the toggle respects it
        self.displayTangents = cmds.animCurveEditor('graphEditor1GraphEd', q=True, displayTangents=True)
        self.displayActiveKeyTangents = cmds.animCurveEditor('graphEditor1GraphEd', q=True, displayActiveKeyTangents=True)
        if cmds.animCurveEditor('graphEditor1GraphEd', q=True, showBufferCurves=True)=='on':
            self.showBufferCurves = True
        else:
            self.showBufferCurves = False
        
    def noiseFunc(self, initialValue, randomRange, damp):
        '''
        really simple noise func, maybe I'll flesh this out at somepoint
        '''
        return initialValue + (random.uniform(randomRange[0], randomRange[1])*damp)
    
    @classmethod
    def showOptions(cls):
        cls()._showUI()
        
    def _showUI(self):
                 
            if cmds.window(self.win, exists=True):
                cmds.deleteUI(self.win, window=True)
            cmds.window(self.win, title=LANGUAGE_MAP._Randomizer_.title, s=True, widthHeight=(320, 280))
            cmds.menuBarLayout()
            cmds.menu(l=LANGUAGE_MAP._Generic_.vimeo_menu)
            cmds.menuItem(l=LANGUAGE_MAP._Generic_.vimeo_help,
                          ann=LANGUAGE_MAP._Randomizer_.vimeo_randomizer_ann,
                          c="import Red9.core.Red9_General as r9General;r9General.os_OpenFile('https://vimeo.com/69270932')")
            #cmds.menuItem(divider=True)
            cmds.menuItem(l=LANGUAGE_MAP._Generic_.contactme, c=r9Setup.red9ContactInfo)
            cmds.columnLayout(adjustableColumn=True, columnAttach=('both', 5))
            cmds.separator(h=15, style='none')
            
            cmds.floatFieldGrp('ffg_rand_damping', l=LANGUAGE_MAP._Randomizer_.strength_value, v1=1, precision=2)
            cmds.floatFieldGrp('ffg_rand_frmStep', l=LANGUAGE_MAP._Randomizer_.frame_step, v1=1, en=False, precision=2)
            cmds.separator(h=20, style='in')

            cmds.rowColumnLayout(numberOfColumns=2, columnWidth=[(1, 150), (2, 150)])
            cmds.checkBox('cb_rand_current',
                          l=LANGUAGE_MAP._Randomizer_.current_keys_only, v=True,
                          ann=LANGUAGE_MAP._Randomizer_.current_keys_only_ann,
                          cc=self.__uicb_currentKeysCallback)
            cmds.checkBox('cb_rand_percent',
                          l=LANGUAGE_MAP._Randomizer_.pre_normalize, v=True,
                          ann=LANGUAGE_MAP._Randomizer_.pre_normalize_ann,
                          cc=self.__uicb_percentageCallback)
            #cmds.checkBox('cb_rand_ignoreBounds',
            #              l='Ignore Start and End Keys', v=True,
            #              ann='Remove the first and last key from processing, maintaining any animation cycles')
            cmds.setParent('..')
            cmds.separator(h=15, style='in')
            cmds.checkBox('interactiveRand', value=False,
                          l=LANGUAGE_MAP._Randomizer_.interactive_mode,
                          ann=LANGUAGE_MAP._Randomizer_.interactive_mode_ann,
                          onc=lambda *x: self.__uicb_interactiveMode(True),
                          ofc=lambda *x: self.__uicb_interactiveMode(False))
            cmds.separator(h=10, style='none')
                
            cmds.rowColumnLayout('interactiveLayout', numberOfColumns=3, columnWidth=[(1, 220), (2, 40), (3, 30)])
            cmds.floatSliderGrp('fsg_randfloatValue',
                                    field=True,
                                    minValue=0,
                                    maxValue=1.0,
                                    pre=2,
                                    value=0,\
                                    columnWidth=[(1, 40), (2, 100)],
                                    dc=self.interactiveWrapper)
            cmds.floatField('ffg_rand_intMax', v=1, precision=2, cc=self.__uicb_setRanges)
            cmds.text(label=LANGUAGE_MAP._Generic_.max)
            cmds.setParent('..')

            cmds.separator(h=15, style='none')
            
            cmds.rowColumnLayout(numberOfColumns=3, columnWidth=[(1, 100), (2, 100), (3, 100)])
            cmds.button(label=LANGUAGE_MAP._Generic_.apply, bgc=r9Setup.red9ButtonBGC(1),
                         command=self.curveMenuFunc)
            cmds.button(label=LANGUAGE_MAP._Randomizer_.save_pref, bgc=r9Setup.red9ButtonBGC(1),
                         command=self.__storePrefs)
            cmds.button(label=LANGUAGE_MAP._Randomizer_.toggle_buffers, bgc=r9Setup.red9ButtonBGC(1),
                         command=self.__uicb_toggleGraphDisplay)
            cmds.setParent('..')
            
            cmds.separator(h=15, style='none')
            cmds.iconTextButton(style='iconOnly', bgc=(0.7, 0, 0), image1='Rocket9_buttonStrap2.bmp',
                                 c=r9Setup.red9ContactInfo, h=22, w=200)
            cmds.showWindow(self.win)
            cmds.window('KeyRandomizerOptions', e=True, widthHeight=(320, 280))
            self.__uicb_interactiveMode(False)
            self.__loadPrefsToUI()
            
            #set close event to restore stabndard GraphEditor curve status
            cmds.scriptJob(runOnce=True, uiDeleted=[self.win, lambda *x:animCurveDrawStyle(style='full', forceBuffer=False,
                                                                                      showBufferCurves=self.showBufferCurves,
                                                                                      displayTangents=self.displayTangents,
                                                                                      displayActiveKeyTangents=self.displayActiveKeyTangents)])

    def __uicb_setRanges(self, *args):
        cmds.floatSliderGrp('fsg_randfloatValue', e=True, maxValue=args[0])  # cmds.floatField('ffg_rand_intMax',q=True,v=True))
   
    def __uicb_toggleGraphDisplay(self, *args):
        if not self.toggledState:
            self.displayTangents=cmds.animCurveEditor('graphEditor1GraphEd', q=True, displayTangents=True)
            self.displayActiveKeyTangents = cmds.animCurveEditor('graphEditor1GraphEd', q=True, displayActiveKeyTangents=True)
            if cmds.animCurveEditor('graphEditor1GraphEd', q=True, showBufferCurves=True)=='on':
                self.showBufferCurves = True
            else:
                self.showBufferCurves = False
                
            animCurveDrawStyle(style='simple', forceBuffer=True)
            self.toggledState=True
        else:
            animCurveDrawStyle(style='full', forceBuffer=False,
                                 showBufferCurves=self.showBufferCurves,
                                 displayTangents=self.displayTangents,
                                 displayActiveKeyTangents=self.displayActiveKeyTangents)
            self.toggledState=False
                        
    def __uicb_interactiveMode(self, mode):
        if mode:
            if not cmds.checkBox('cb_rand_current', q=True, v=True):
                cmds.checkBox('interactiveRand', e=True, v=False)
                log.warning('Interactive is ONLY supported in "CurrentKeys" Mode')
                return
            cmds.floatFieldGrp('ffg_rand_damping', e=True, en=False)
            cmds.rowColumnLayout('interactiveLayout', e=True, en=True)
        else:
            cmds.floatFieldGrp('ffg_rand_damping', e=True, en=True)
            cmds.rowColumnLayout('interactiveLayout', e=True, en=False)
            
    def __uicb_currentKeysCallback(self, *args):
        if cmds.checkBox('cb_rand_current', q=True, v=True):
            cmds.floatFieldGrp('ffg_rand_frmStep', e=True, en=False)
        else:
            cmds.floatFieldGrp('ffg_rand_frmStep', e=True, en=True)
            cmds.checkBox('interactiveRand', e=True, v=False)
            self.__uicb_interactiveMode(False)

    def __uicb_percentageCallback(self, *args):
        if not cmds.checkBox('cb_rand_percent', q=True, v=True):
            cmds.floatFieldGrp('ffg_rand_damping', e=True, label='strength : value')
        else:
            cmds.floatFieldGrp('ffg_rand_damping', e=True, label='strength : normalized %')
            
    def __storePrefs(self, *args):
        if cmds.window(self.win, exists=True):
            cmds.optionVar(floatValue=('red9_randomizer_damp', cmds.floatFieldGrp('ffg_rand_damping', q=True, v1=True)))
            cmds.optionVar(intValue=('red9_randomizer_current', cmds.checkBox('cb_rand_current', q=True, v=True)))
            cmds.optionVar(intValue=('red9_randomizer_percent', cmds.checkBox('cb_rand_percent', q=True, v=True)))
            cmds.optionVar(floatValue=('red9_randomizer_frmStep', cmds.floatFieldGrp('ffg_rand_frmStep', q=True, v1=True)))
            log.debug('stored out ramdomizer prefs')
        
    def __loadPrefsToUI(self):
        if cmds.optionVar(exists='red9_randomizer_damp'):
            cmds.floatFieldGrp('ffg_rand_damping', e=True, v1=cmds.optionVar(q='red9_randomizer_damp'))
        if cmds.optionVar(exists='red9_randomizer_current'):
            cmds.checkBox('cb_rand_current', e=True, v=cmds.optionVar(q='red9_randomizer_current'))
        if cmds.optionVar(exists='red9_randomizer_percent'):
            cmds.checkBox('cb_rand_percent', e=True, v=cmds.optionVar(q='red9_randomizer_percent'))
        if cmds.optionVar(exists='red9_randomizer_frmStep'):
            cmds.floatFieldGrp('ffg_rand_frmStep', e=True, v1=cmds.optionVar(q='red9_randomizer_frmStep'))
        self.__uicb_currentKeysCallback()
        self.__uicb_percentageCallback()
    
    def __calcualteRangeValue(self, keyValues):
        vals = sorted(keyValues)
        rng = abs(vals[0] - vals[-1]) / 2
        if rng > 1.0:
            return [-rng, rng]
        else:
            return [-1, 1]
   
    def interactiveWrapper(self, *args):
        with self.contextManager(self.dragActive, undoFuncCache=['interactiveWrapper']):
            self.dragActive = True
            self.addNoise(cmds.keyframe(q=True, sl=True, n=True), time=(), step=1,
                          currentKeys=True,
                          damp=cmds.floatSliderGrp('fsg_randfloatValue', q=True, v=True),
                          percent=cmds.checkBox('cb_rand_percent', q=True, v=True))
                                
    def addNoise(self, curves, time=(), step=1, currentKeys=True, randomRange=[-1, 1], damp=1, percent=False):
        '''
        Simple noise function designed to add noise to keyframed animation data.
        
        :param curves: Maya animCurves to process
        :param time: timeRange to process
        :param step: frame step used in the processor
        :param currentKeys: ONLY randomize keys that already exists
        :param randomRange: range [upper, lower] bounds passed to teh randomizer
        :param damp: damping passed into the randomizer
        '''
        if percent:
            damp=damp/100
        if currentKeys:
            for curve in curves:
                #if keys/curves are already selected, process those only
                selectedKeys = cmds.keyframe(curve, q=True, vc=True, tc=True, sl=True)
                if selectedKeys:
                    keyData=selectedKeys
                else:
                    #else process all keys inside the time
                    keyData = cmds.keyframe(curve, q=True, vc=True, tc=True, t=time)
                for t, v in zip(keyData[::2], keyData[1::2]):
                    if percent:
                        # figure the upper and lower value bounds
                        randomRange = self.__calcualteRangeValue(keyData[1::2])
                        log.debug('Percent data : randomRange=%f>%f, percentage=%f' % (randomRange[0], randomRange[1], damp))
                    value = self.noiseFunc(v, randomRange, damp)
                    cmds.setKeyframe(curve, v=value, t=t)
        else:  # allow to ADD keys at 'step' frms
            if not time:
                selectedKeyTimes = sorted(list(set(cmds.keyframe(q=True, tc=True))))
                if selectedKeyTimes:
                    time = (selectedKeyTimes[0], selectedKeyTimes[-1])
            for curve in curves:
                if percent:
                    # figure the upper and lower value bounds
                    randomRange = self.__calcualteRangeValue(cmds.keyframe(curve, q=True, vc=True, t=time))
                    log.debug('Percent data : randomRange=%f>%f, percentage=%f' % (randomRange[0], randomRange[1], damp))
                    
                connection=[con for con in cmds.listConnections(curve, source=False, d=True, p=True)
                            if not cmds.nodeType(con)=='hyperLayout'][0]
                            
                for t in timeLineRangeProcess(time[0], time[1], step, incEnds=True):
                    value = self.noiseFunc(cmds.getAttr(connection, t=t), randomRange, damp)
                    cmds.setKeyframe(connection, v=value, t=t)
                    
    def curveMenuFunc(self, *args):
        self.__storePrefs()
        frmStep=1
        damping=1
        percent=False
        currentKeys=True
        
        if cmds.window(self.win, exists=True):
            currentKeys = cmds.checkBox('cb_rand_current', q=True, v=True)
            damping = cmds.floatFieldGrp('ffg_rand_damping', q=True, v1=True)
            frmStep = cmds.floatFieldGrp('ffg_rand_frmStep', q=True, v1=True)
            percent = cmds.checkBox('cb_rand_percent', q=True, v=True)
        else:
            if cmds.optionVar(exists='red9_randomizer_damp'):
                damping=cmds.optionVar(q='red9_randomizer_damp')
            if cmds.optionVar(exists='red9_randomizer_percent'):
                percent=cmds.optionVar(q='red9_randomizer_percent')
            if cmds.optionVar(exists='red9_randomizer_current'):
                currentKeys=cmds.optionVar(q='red9_randomizer_current')
            if cmds.optionVar(exists='red9_randomizer_frmStep'):
                frmStep=cmds.optionVar(q='red9_randomizer_frmStep')
        
        selectedCurves=cmds.keyframe(q=True, sl=True, n=True)
        if not selectedCurves:
            raise StandardError('No Keys or Anim curves selected!')
        
        self.addNoise(curves=selectedCurves,
                      step=frmStep,
                      damp=damping,
                      currentKeys=currentKeys,
                      percent=percent)
                            

 
class FilterCurves(object):
    
    def __init__(self):
        self.win=LANGUAGE_MAP._CurveFilters_.title
        self.contextManager=curveModifierContext
        self.dragActive=False
        self.undoFuncCache=['simplifyWrapper', 'snapAnimCurvesToFrms', 'resampleCurves']
        self.undoDepth = 1
        self.snapToFrame=False
        self.toggledState=False
        
        #cache the current state of the GrapthEditor so that the toggle respects it
        self.displayTangents=cmds.animCurveEditor('graphEditor1GraphEd', q=True, displayTangents=True)
        self.displayActiveKeyTangents = cmds.animCurveEditor('graphEditor1GraphEd', q=True, displayActiveKeyTangents=True)
        if cmds.animCurveEditor('graphEditor1GraphEd', q=True, showBufferCurves=True)=='on':
            self.showBufferCurves = True
        else:
            self.showBufferCurves = False

    @classmethod
    def show(cls):
        cls()._showUI()
    
    def _showUI(self):
        if cmds.window(self.win, exists=True):
            cmds.deleteUI(self.win, window=True)
        cmds.window(self.win, title=self.win)
        cmds.menuBarLayout()
        cmds.menu(l=LANGUAGE_MAP._Generic_.vimeo_menu)
        cmds.menuItem(l=LANGUAGE_MAP._Generic_.vimeo_help,
                          ann=LANGUAGE_MAP._CurveFilters_.vimeo_randomize_ann,
                          c="import Red9.core.Red9_General as r9General;r9General.os_OpenFile('https://vimeo.com/69270932')")
        cmds.menuItem(divider=True)
        cmds.menuItem(l=LANGUAGE_MAP._Generic_.contactme, c=r9Setup.red9ContactInfo)
        cmds.columnLayout(adjustableColumn=True)
        
        cmds.text(label=LANGUAGE_MAP._CurveFilters_.curve_resampler)
        cmds.separator(h=5, style='none')
        cmds.rowColumnLayout(numberOfColumns=2, cw=((1, 350), (2, 40)))
        cmds.floatSliderGrp('fsg_resampleStep',
                                label=LANGUAGE_MAP._CurveFilters_.resample,
                                field=True,
                                minValue=1,
                                maxValue=10.0,
                                pre=1,
                                value=1,
                                columnWidth=[(1, 80), (2, 50), (3, 100)],
                                dc=self.resampleCurves)
                                #cc=self.snapAnimCurvesToFrms)  #set the dragActive state back to false on release
        cmds.floatField('stepRange', v=10, pre=2,
                        cc=self.__uicb_setMaxRanges,
                        dc=self.__uicb_setMaxRanges)
        cmds.setParent('..')
        cmds.separator(h=25, style='in')
           
        cmds.text(label=LANGUAGE_MAP._CurveFilters_.curve_simplifier)
        cmds.separator(h=5, style='none')
        cmds.rowColumnLayout(numberOfColumns=2, cw=((1, 350), (2, 40)))
        cmds.floatSliderGrp('fsg_filtertimeValue',
                                label=LANGUAGE_MAP._CurveFilters_.time_tolerance,
                                field=True,
                                minValue=0.05,
                                maxValue=10.0,
                                pre=2,
                                value=0,
                                columnWidth=[(1, 80), (2, 50), (3, 50)],
                                dc=self.simplifyWrapper,
                                cc=self.snapAnimCurvesToFrms)
        cmds.floatField('timeRange', v=10, pre=2,
                        cc=self.__uicb_setMaxRanges,
                        dc=self.__uicb_setMaxRanges)
        cmds.floatSliderGrp('fsg_filterfloatValue',
                                label=LANGUAGE_MAP._CurveFilters_.value_tolerance,
                                field=True,
                                minValue=0,
                                maxValue=1.0,
                                pre=2,
                                value=0,
                                columnWidth=[(1, 80), (2, 50), (3, 50)],
                                dc=self.simplifyWrapper,
                                cc=self.snapAnimCurvesToFrms)
        cmds.floatField('valueRange', v=1, pre=2,
                        cc=self.__uicb_setMaxRanges,
                        dc=self.__uicb_setMaxRanges)
        cmds.setParent('..')
        cmds.separator(h=20, style='in')
        cmds.rowColumnLayout(numberOfColumns=3, cw=[(1, 100), (2, 120), (3, 120)], cs=((1, 20), (2, 30)))
        cmds.checkBox('snapToFrames', value=self.snapToFrame,
                      label=LANGUAGE_MAP._CurveFilters_.snap_to_frame,
                      ann=LANGUAGE_MAP._CurveFilters_.snap_to_frame_ann,
                      cc=self.__uicb_setToFrame)
        cmds.button(label=LANGUAGE_MAP._CurveFilters_.delete_redundants,
                    ann=LANGUAGE_MAP._CurveFilters_.delete_redundants_ann,
                    command='import maya.cmds as cmds;cmds.delete(sc=True)')
        cmds.button(label=LANGUAGE_MAP._CurveFilters_.single_process,
                    ann=LANGUAGE_MAP._CurveFilters_.single_process_ann,
                    command=self.simplifyWrapper)
        cmds.setParent('..')
        
        cmds.separator(h=20, style="in")
        cmds.rowColumnLayout(numberOfColumns=2, cw=((1, 200), (2, 200)))
        cmds.button(label=LANGUAGE_MAP._CurveFilters_.reset_all, bgc=r9Setup.red9ButtonBGC(1),
                         command=self.__uicb_resetSliders)
        cmds.button(label=LANGUAGE_MAP._CurveFilters_.toggle_buffers, bgc=r9Setup.red9ButtonBGC(1),
                         command=self.__uicb_toggleGraphDisplay)
        cmds.setParent('..')
      
        cmds.separator(h=20, style="none")
        cmds.iconTextButton(style='iconOnly', bgc=(0.7, 0, 0), image1='Rocket9_buttonStrap2.bmp',
                                 c=r9Setup.red9ContactInfo,
                                 h=22, w=220)
        cmds.showWindow(self.win)
        cmds.window(self.win, e=True, widthHeight=(410, 300))
         
        #set close event to restore standard GraphEditor curve status
        cmds.scriptJob(runOnce=True, uiDeleted=[self.win, lambda *x:animCurveDrawStyle(style='full', forceBuffer=False,
                                                                                      showBufferCurves=self.showBufferCurves,
                                                                                      displayTangents=self.displayTangents,
                                                                                      displayActiveKeyTangents=self.displayActiveKeyTangents)])

    def __uicb_setMaxRanges(self, *args):
        cmds.floatSliderGrp('fsg_filtertimeValue', e=True, maxValue=cmds.floatField("timeRange", q=True, v=True))
        cmds.floatSliderGrp('fsg_filterfloatValue', e=True, maxValue=cmds.floatField("valueRange", q=True, v=True))
        cmds.floatSliderGrp('fsg_resampleStep', e=True, maxValue=cmds.floatField("stepRange", q=True, v=True))
    
    def __uicb_resetSliders(self, *args):
        cmds.floatSliderGrp('fsg_filtertimeValue', e=True, v=0)
        cmds.floatSliderGrp('fsg_filterfloatValue', e=True, v=0)
        cmds.floatSliderGrp('fsg_resampleStep', e=True, v=1)
        self.contextManager(self.dragActive,
                            undoFuncCache=self.undoFuncCache,
                            undoDepth=self.undoDepth).undoCall()
    
    def __uicb_toggleGraphDisplay(self, *args):
        if not self.toggledState:
            #cache the current state
            self.displayTangents=cmds.animCurveEditor('graphEditor1GraphEd', q=True, displayTangents=True)
            self.displayActiveKeyTangents = cmds.animCurveEditor('graphEditor1GraphEd', q=True, displayActiveKeyTangents=True)
            if cmds.animCurveEditor('graphEditor1GraphEd', q=True, showBufferCurves=True)=='on':
                self.showBufferCurves = True
            else:
                self.showBufferCurves = False
                
            animCurveDrawStyle(style='simple', forceBuffer=True)
            self.toggledState=True
        else:
            animCurveDrawStyle(style='full', forceBuffer=False,
                               showBufferCurves=self.showBufferCurves,
                               displayTangents=self.displayTangents,
                               displayActiveKeyTangents=self.displayActiveKeyTangents)
            self.toggledState=False
        
    def __uicb_setToFrame(self, *args):
        #print args
        if args[0]:
            cmds.floatSliderGrp('fsg_resampleStep',
                                e=True,
                                pre=0)
            self.snapToFrame=True
            self.undoDepth=2
        else:
            cmds.floatSliderGrp('fsg_resampleStep',
                                e=True,
                                pre=1)
            self.undoDepth=1
            self.snapToFrame=False
                                  
    def simplifyWrapper(self, *args):
        '''
        straight simplify of curves using a managed cmds.simplfy call
        '''
        with self.contextManager(self.dragActive,
                                 undoFuncCache=self.undoFuncCache,
                                 undoDepth=self.undoDepth):
            self.dragActive=True  # turn on the undo management
            simplify=True
            if simplify:
                cmds.simplify(animation='keysOrObjects',
                               timeTolerance=cmds.floatSliderGrp('fsg_filtertimeValue', q=True, v=True),
                               valueTolerance=cmds.floatSliderGrp('fsg_filterfloatValue', q=True, v=True))
            else:
                print 'testing filter call'
                objs=cmds.ls(sl=True)
                cmds.filterCurve(objs, f='simplify',
                                 timeTolerance=cmds.floatSliderGrp('fsg_filterfloatValue', q=True, v=True))
    
    def resampleCurves(self, *args):
        '''
        straight resample of curves using a managed cmds.bakeResults call
        :param args[0]: this is the step used in the resample
        '''
        step = args[0]
        if self.snapToFrame:
            step = int(args[0])
        #print step
        curves = cmds.keyframe(q=True, sl=True, n=True)
        if not curves:
            curves = cmds.ls(sl=True, l=True)
            time = ()
        else:
            keys = sorted(cmds.keyframe(curves, sl=True, q=True, tc=True))
            time = (int(keys[0]), keys[-1])  # note the int convertion in case frist key is on a sub-frame
        with self.contextManager(True, undoFuncCache=self.undoFuncCache):
            cmds.bakeResults(curves, t=time, sb=step, pok=True)

    def snapAnimCurvesToFrms(self, *args):
        '''
        called after the interaction filters, snap
        '''
        if self.snapToFrame:
            cmds.snapKey(timeMultiple=1)
            
            
class MirrorHierarchy(object):
    
    '''
    This class is designed to mirror pose and animation data on any given
    hierarchy. The hierarchy is filtered like everything else in the Red9
    pack, using a filterSettings node thats passed into the __init__
    
    >>> mirror=MirrorHierarchy(cmds.ls(sl=True)[0])
    >>> #set the settings object to run metaData
    >>> mirror.settings.metaRig=True
    >>> mirror.settings.printSettings()
    >>> mirror.mirrorData(mode='Anim')
    
    >>># Useful snippets:
    >>># offset all selected nodes mirrorID by 5
    >>>mirror=r9Anim.MirrorHierarchy()
    >>>mirror.incrementIDs(cmds.ls(sl=True), offset=5)
    >>>
    >>># set all the mirror axis on the selected
    >>>for node in cmds.ls(sl=True):
    >>>    mirror.setMirrorIDs(node,axis='translateX,rotateY,rotateZ')
    >>>
    >>># copy mirrorId's from one node to another
    >>>for src, dest in zip(srcNodes, destNodes):
    >>>    mirror.copyMirrorIDs(src,dest)
    
    TODO: We need to do a UI for managing these marker attrs and the Index lists
    
    TODO: allow the mirror block to include an offset so that if you need to inverse AND offset 
        by 180 to get left and right working you can still do so.
    '''
    
    def __init__(self, nodes=[], filterSettings=None, **kws):
        '''
        :param nodes: initial nodes to process
        :param filterSettings: filterSettings object to process hierarchies
        '''
        
        self.nodes = nodes
        if not type(self.nodes) == list:
            self.nodes = [self.nodes]
        
        # default Attributes used to define the system
        self.defaultMirrorAxis = ['translateX', 'rotateY', 'rotateZ']
        self.mirrorSide = 'mirrorSide'
        self.mirrorIndex = 'mirrorIndex'
        self.mirrorAxis = 'mirrorAxis'
        self.mirrorDict = {'Centre': {}, 'Left': {}, 'Right': {}}
        self.mergeLayers = True
        self.indexednodes = []  # all nodes to process - passed to the Animlayer context
        self.kws = kws  # allows us to pass kws into the copyKey and copyAttr call if needed, ie, pasteMethod!
        #print 'kws in Mirror call : ', self.kws
        
        #cache the function pointers for speed
        self.transferCallKeys = AnimFunctions().copyKeys
        self.transferCallAttrs = AnimFunctions().copyAttributes
        
        # make sure we have a settings object
        if filterSettings:
            if issubclass(type(filterSettings), r9Core.FilterNode_Settings):
                self.settings = filterSettings
            else:
                raise StandardError('filterSettings param requires an r9Core.FilterNode_Settings object')
        else:
            self.settings = r9Core.FilterNode_Settings()
            
        # ensure we use the mirrorSide attr search ensuring all nodes
        # returned are part of the Mirror system
        self.settings.searchAttrs.append(self.mirrorSide)
    
    def _validateMirrorEnum(self, side):
        '''
        validate the given side to make sure it's formatted correctly before setting the data
        '''
        if not side:
            return False
        if type(side) == int:
            if not side in range(0, 3):
                raise ValueError('given mirror side is not a valid int entry: 0, 1 or 2')
            else:
                return True
        if not side in self.mirrorDict:
            raise ValueError('given mirror side is not a valid key: Left, Right or Centre')
        else:
            return True
        
    def setMirrorIDs(self, node, side=None, slot=None, axis=None):
        '''
        Add/Set the default attrs required by the MirrorSystems.
        
        :param node: nodes to take the attrs
        :param side: valid values are 'Centre','Left' or 'Right' or 0, 1, 2
        :param slot: bool Mainly used to pair up left and right paired controllers
        :param axis: eg 'translateX,rotateY,rotateZ' simple comma separated string
            If this is set then it overrides the default mirror axis.
            These are the channels who have their attribute/animCurve values inversed
            during mirror. NOT we allow axis to have a null string 'None' so it can be
            passed in blank when needed
            
        .. note:: 
            slot index can't be ZERO
        '''
        # Note using the MetaClass as all the type checking
        # and attribute handling is done for us
        mClass = r9Meta.MetaClass(node)
        if self._validateMirrorEnum(side):
            mClass.addAttr(self.mirrorSide, attrType='enum', enumName='Centre:Left:Right', hidden=True)
            mClass.__setattr__(self.mirrorSide, side)
        if slot:
            mClass.addAttr(self.mirrorIndex, slot, hidden=True)
            mClass.__setattr__(self.mirrorIndex, slot)
        if axis:
            if axis == 'None':
                mClass.addAttr(self.mirrorAxis, attrType='string')
                mClass.mirrorAxis=''
            else:
                mClass.addAttr(self.mirrorAxis, axis)
                mClass.__setattr__(self.mirrorAxis, axis)
        else:
            if mClass.hasAttr(self.mirrorAxis):
                delattr(mClass, self.mirrorAxis)
        del(mClass)  # cleanup
        
    def deleteMirrorIDs(self, node):
        '''
        Remove the given node from the MirrorSystems
        '''
        mClass = r9Meta.MetaClass(node)
        try:
            mClass.__delattr__(self.mirrorSide)
        except:
            pass
        try:
            mClass.__delattr__(self.mirrorIndex)
        except:
            pass
        try:
            mClass.__delattr__(self.mirrorAxis)
        except:
            pass
        del(mClass)
    
    def copyMirrorIDs(self, src, dest):
        '''
        Copy mirrorIDs between nodes, note the nodes list passed in is zipped into pairs
        This will copy all the mirrorData from src to dest, useful for copying data between 
        systems when the MirrorMap fails due to naming.
        '''
        pairs=zip(src, dest)
        for src, dest in pairs:
            axis=None
            src=r9Meta.MetaClass(src)
            if not src.hasAttr(self.mirrorAxis):
                log.warning('Node has no mirrorData : %s' % src.shortName())
                continue
            if src.hasAttr(self.mirrorAxis):
                axis=getattr(src, self.mirrorAxis)
            self.setMirrorIDs(dest,
                              side=str(cmds.getAttr('%s.%s' % (src.mNode, self.mirrorSide), asString=True)),
                              slot=getattr(src, self.mirrorIndex),
                              axis=axis)

    def incrementIDs(self, nodes, offset):
        '''
        offset the mirrorIndex on selected nodes by a given offset
        '''
        for node in nodes:
            current = self.getMirrorIndex(node)
            if current:
                cmds.setAttr('%s.%s' % (node, self.mirrorIndex), (int(current) + offset))
        
    def getNodes(self):
        '''
        Get the list of nodes to start processing
        '''
        return r9Core.FilterNode(self.nodes, filterSettings=self.settings).ProcessFilter()
     
    def getMirrorSide(self, node):
        '''
        This is an enum Attr to denote the Side of the controller in the Mirror system
        '''
        try:
            return cmds.getAttr('%s.%s' % (node, self.mirrorSide), asString=True)
        except:
            log.debug('%s node has no "mirrorSide" attr' % r9Core.nodeNameStrip(node))
            
    def getMirrorIndex(self, node):
        '''
        get the mirrorIndex, these slots are used to denote matching pairs
        such that Left and Right Controllers to switch will have the same index
        '''
        try:
            return int(cmds.getAttr('%s.%s' % (node, self.mirrorIndex)))
        except:
            log.debug('%s node has no "mirrorIndex" attr' % r9Core.nodeNameStrip(node))
   
    def getMirrorCompiledID(self, node):
        '''
        This return the mirror data in a compiled mannor for the poseSaver
        such that mirror data  for a node : Center, ID 10 == Center_10
        '''
        try:
            return '%s_%s' % (self.getMirrorSide(node), self.getMirrorIndex(node))
        except:
            log.debug('%s node has no MirrorData' % r9Core.nodeNameStrip(node))
            return ''
    
    def getMirrorAxis(self, node):
        '''
        get any custom attributes set at node level to inverse, if none found
        return the default axis setup in the __init__
        NOTE: if mirrorAxis attr has been added to the node but is empty then
        no axis will be inversed at all. If the attr doesn't exist then the
        default inverse axis will be used
        '''
        if cmds.attributeQuery(self.mirrorAxis, node=node, exists=True):
            axis = cmds.getAttr('%s.%s' % (node, self.mirrorAxis))
            if not axis:
                return []
            else:
                #make sure we remove any trailing ',' also so we don't end up with empty entries
                return axis.rstrip(',').split(',')
        else:
            return self.defaultMirrorAxis
        
    def getMirrorSets(self, nodes=None):
        '''
        Filter the given nodes into the mirrorDict
        such that {'Centre':{id:node,},'Left':{id:node,},'Right':{id:node,}}
        :param nodes: only process a given list of nodes, else run the filterSettings 
            call from the initial nodes passed to the class
        '''
        # reset the current Dict prior to rescanning
        self.mirrorDict = {'Centre': {}, 'Left': {}, 'Right': {}}
        self.unresolved = {'Centre': {}, 'Left': {}, 'Right': {}}
        self.indexednodes=nodes
        
        if not nodes and self.nodes:
            self.indexednodes = self.getNodes()

        if not self.indexednodes:
            raise StandardError('No mirrorMarkers found from the given node list/hierarchy')
        
        for node in self.indexednodes:
            try:
                side = self.getMirrorSide(node)
                index = self.getMirrorIndex(node)
                axis = self.getMirrorAxis(node)
                log.debug('Side : %s Index : %s>> node %s' % \
                          (side, index, r9Core.nodeNameStrip(node)))
                # self.mirrorDict[side][str(index)]=node #NOTE index is cast to string!
                if str(index) in self.mirrorDict[side]:
                    log.warning('Mirror index ( %s : %i ) already assigned : currently node : %s,  duplicate node : %s' %
                                    (side, index,
                                     r9Core.nodeNameStrip(self.mirrorDict[side][str(index)]['node']),
                                     r9Core.nodeNameStrip(node)))
                    if not str(index) in self.unresolved[side]:
                        self.unresolved[side][str(index)] = [self.mirrorDict[side][str(index)]['node']]
                    self.unresolved[side][str(index)].append(node)
                    continue
                
                self.mirrorDict[side][str(index)] = {}
                self.mirrorDict[side][str(index)]['node'] = node
                self.mirrorDict[side][str(index)]['axis'] = axis
                if cmds.attributeQuery(self.mirrorAxis, node=node, exists=True):
                    self.mirrorDict[side][str(index)]['axisAttr'] = True
                else:
                    self.mirrorDict[side][str(index)]['axisAttr'] = False
                
            except StandardError, error:
                log.debug(error)
                log.info('Failed to add Node to Mirror System : %s' % r9Core.nodeNameStrip(node))
                
        return self.indexednodes
    
    def printMirrorDict(self, short=True):
        '''
        Pretty print the Mirror Dict
        '''
        self.getMirrorSets()
        if not short:
            print '\nCenter MirrorLists ====================================================='
            for i in r9Core.sortNumerically(self.mirrorDict['Centre'].keys()):
                print '%s > %s' % (i, self.mirrorDict['Centre'][i]['node'])
            print '\nRight MirrorLists ======================================================'
            for i in r9Core.sortNumerically(self.mirrorDict['Right'].keys()):
                print '%s > %s' % (i, self.mirrorDict['Right'][i]['node'])
            print '\nLeft MirrorLists ======================================================='
            for i in r9Core.sortNumerically(self.mirrorDict['Left'].keys()):
                print '%s > %s' % (i, self.mirrorDict['Left'][i]['node'])
        else:
            print '\nCenter MirrorLists ====================================================='
            for i in r9Core.sortNumerically(self.mirrorDict['Centre'].keys()):
                print '%s > %s' % (i, r9Core.nodeNameStrip(self.mirrorDict['Centre'][i]['node']))
            print '\nRight MirrorLists ======================================================'
            for i in r9Core.sortNumerically(self.mirrorDict['Right'].keys()):
                print '%s > %s' % (i, r9Core.nodeNameStrip(self.mirrorDict['Right'][i]['node']))
            print '\nLeft MirrorLists ======================================================='
            for i in r9Core.sortNumerically(self.mirrorDict['Left'].keys()):
                print '%s > %s' % (i, r9Core.nodeNameStrip(self.mirrorDict['Left'][i]['node']))
        if self.unresolved:
            for key, val in self.unresolved.items():
                if val:
                    print '\CLASHING %s Mirror Indexes =====================================================' % key
                    for i in r9Core.sortNumerically(val):
                        print 'clashing Index : %s : %s : %s' % \
                        (key, i, ', '.join([r9Core.nodeNameStrip(n) for n in val[i]]))
                          
    def switchPairData(self, objA, objB, mode='Anim'):
        '''
        take the left and right matched pairs and exchange the animData
        or poseData across between them

        '''
        objs = cmds.ls(sl=True, l=True)
        if mode == 'Anim':
            transferCall = self.transferCallKeys  # AnimFunctions().copyKeys
        else:
            transferCall = self.transferCallAttrs  # AnimFunctions().copyAttributes
        
        # switch the anim data over via temp
        cmds.select(objA)
        cmds.duplicate(name='DELETE_ME_TEMP', po=True)
        temp = cmds.ls(sl=True, l=True)[0]
        log.debug('temp %s:' % temp)
        transferCall([objA, temp], **self.kws)
        transferCall([objB, objA], **self.kws)
        transferCall([temp, objB], **self.kws)
        cmds.delete(temp)
        
        if objs:
            cmds.select(objs)
    
    def makeSymmetrical(self, nodes=None, mode='Anim', primeAxis='Left'):
        '''
        similar to the mirrorData except this is designed to take the data from an object in
        one side of the mirrorDict and pass that data to the opposite matching node, thus
        making the anim/pose symmetrical according to the mirror setups.
        Really useful for facial setups!
        
        :param nodes: optional specific listy of nodes to process, else we run the filterSetting code 
            on the initial nodes past to the class
        :param mode: 'Anim' ot 'Pose' process as a single pose or an animation
        :param primeAxis: 'Left' or 'Right' whether to take the data from the left or right side of the setup
        '''
        self.getMirrorSets(nodes)
    
        if not self.indexednodes:
            raise IOError('No nodes mirrorIndexed nodes found from given / selected nodes')
        
        if mode == 'Anim':
            transferCall = self.transferCallKeys  # AnimFunctions().copyKeys
            inverseCall = AnimFunctions.inverseAnimChannels
            self.mergeLayers=True
        else:
            transferCall = self.transferCallAttrs  # AnimFunctions().copyAttributes
            inverseCall = AnimFunctions.inverseAttributes
            self.mergeLayers=False
            
        if primeAxis == 'Left':
            masterAxis = 'Left'
            slaveAxis = 'Right'
        else:
            masterAxis = 'Right'
            slaveAxis = 'Left'
            
        with AnimationLayerContext(self.indexednodes, mergeLayers=self.mergeLayers, restoreOnExit=False):
            for index, masterSide in self.mirrorDict[masterAxis].items():
                if not index in self.mirrorDict[slaveAxis].keys():
                    log.warning('No matching Index Key found for %s mirrorIndex : %s >> %s' % \
                                (masterAxis, index, r9Core.nodeNameStrip(masterSide['node'])))
                else:
                    slaveData = self.mirrorDict[slaveAxis][index]
                    log.debug('SymmetricalPairs : %s >> %s' % (r9Core.nodeNameStrip(masterSide['node']), \
                                         r9Core.nodeNameStrip(slaveData['node'])))
                    transferCall([masterSide['node'], slaveData['node']], **self.kws)
                    
                    log.debug('Symmetrical Axis Inversion: %s' % ','.join(slaveData['axis']))
                    if slaveData['axis']:
                        inverseCall(slaveData['node'], slaveData['axis'])
             
    def mirrorData(self, nodes=None, mode='Anim'):
        '''
        Using the FilterSettings obj find all nodes in the return that have
        the mirrorSide attr, then process the lists into Side and Index slots
        before Mirroring the animation data. Swapping left for right and
        inversing the required animCurves
        
        :param nodes: optional specific listy of nodes to process, else we run the filterSetting code 
            on the initial nodes past to the class
        :param mode: 'Anim' ot 'Pose' process as a single pose or an animation
        
        TODO: Issue where if nodeA on Left has NO key data at all, and nodeB on right
        does, then nodeB will be left incorrect. We need to clean the data if there
        are no keys.
        '''

        self.getMirrorSets(nodes)
        if not self.indexednodes:
            raise IOError('No nodes mirrorIndexed nodes found from given / selected nodes')
        
        if mode == 'Anim':
            inverseCall = AnimFunctions.inverseAnimChannels
            self.mergeLayers=True
        else:
            inverseCall = AnimFunctions.inverseAttributes
            self.mergeLayers=False
            
        # with r9General.HIKContext(nodes):
        with AnimationLayerContext(self.indexednodes, mergeLayers=self.mergeLayers, restoreOnExit=False):
            # Switch Pairs on the Left and Right and inverse the channels
            for index, leftData in self.mirrorDict['Left'].items():
                if not index in self.mirrorDict['Right'].keys():
                    log.warning('No matching Index Key found for Left mirrorIndex : %s >> %s' % (index, r9Core.nodeNameStrip(leftData['node'])))
                else:
                    rightData = self.mirrorDict['Right'][index]
                    log.debug('SwitchingPairs : %s >> %s' % (r9Core.nodeNameStrip(leftData['node']), \
                                         r9Core.nodeNameStrip(rightData['node'])))
                    self.switchPairData(leftData['node'], rightData['node'], mode=mode)
                    
                    log.debug('Axis Inversions: left: %s' % ','.join(leftData['axis']))
                    log.debug('Axis Inversions: right: %s' % ','.join(rightData['axis']))
                    if leftData['axis']:
                        inverseCall(leftData['node'], leftData['axis'])
                    if rightData['axis']:
                        inverseCall(rightData['node'], rightData['axis'])
                    
            # Inverse the Centre Nodes
            for data in self.mirrorDict['Centre'].values():
                inverseCall(data['node'], data['axis'])
     
    def saveMirrorSetups(self, filepath):
        '''
        Store the mirrorSetups out to file
        '''
        self.getMirrorSets()
        self.printMirrorDict()
        ConfigObj = configobj.ConfigObj(indent_type='\t')
        ConfigObj['mirror']=self.mirrorDict
        ConfigObj.filename = filepath
        ConfigObj.write()
        
    def loadMirrorSetups(self, filepath, nodes=None, clearCurrent=True, matchMethod='base'):
        if not os.path.exists(filepath):
            raise IOError('invalid filepath given')
        self.mirrorDict = configobj.ConfigObj(filepath)['mirror']
        nodesToMap=nodes
        
        if not nodesToMap:
            nodesToMap=list(self.nodes)
            nodesToMap.extend(cmds.listRelatives(nodesToMap, ad=True, f=True, type='transform'))
        #log.debug('nodes to load mirrors onto: %s' % ','.join(nodesToMap))
        
        progressBar = r9General.ProgressBarContext(len(nodesToMap))
        progressBar.setStep(1)
        count=0
 
        with progressBar:
            for node in nodesToMap:
                if progressBar.isCanceled():
                    break
                
                found = False
                if clearCurrent:
                    self.deleteMirrorIDs(node)
                for index, leftData in self.mirrorDict['Left'].items():
                    if r9Core.matchNodeLists([node], [leftData['node']], matchMethod=matchMethod):
                        log.debug('NodeMatched: %s, Side=Left, index=%i, axis=%s' % (node, int(index), leftData['axis']))
                        if r9Core.decodeString(leftData['axisAttr']):
                            if not leftData['axis']:
                                axis='None'
                            else:
                                axis=','.join(leftData['axis'])
                            self.setMirrorIDs(node, side='Left', slot=int(index), axis=axis)  # ','.join(leftData['axis']))
                        else:
                            self.setMirrorIDs(node, side='Left', slot=int(index))
                        found = True
                        break
                if not found:
                    for index, rightData in self.mirrorDict['Right'].items():
                        if r9Core.matchNodeLists([node], [rightData['node']], matchMethod=matchMethod):
                            log.debug('NodeMatched: %s, Side=Right, index=%i, axis=%s' % (node, int(index), rightData['axis']))
                            if r9Core.decodeString(rightData['axisAttr']):
                                if not rightData['axis']:
                                    axis='None'
                                else:
                                    axis=','.join(rightData['axis'])
                                self.setMirrorIDs(node, side='Right', slot=int(index), axis=axis)  # ','.join(rightData['axis']))
                            else:
                                self.setMirrorIDs(node, side='Right', slot=int(index))
                            found = True
                            break
                if not found:
                    for index, centreData in self.mirrorDict['Centre'].items():
                        if r9Core.matchNodeLists([node], [centreData['node']], matchMethod=matchMethod):
                            log.debug('NodeMatched: %s, Side=Centre, index=%i, axis=%s' % (node, int(index), centreData['axis']))
                            if r9Core.decodeString(centreData['axisAttr']):
                                if not centreData['axis']:
                                    axis='None'
                                else:
                                    axis=','.join(centreData['axis'])
                                self.setMirrorIDs(node, side='Centre', slot=int(index), axis=axis)  # ','.join(centreData['axis']))
                            else:
                                self.setMirrorIDs(node, side='Centre', slot=int(index))
                            break
   
                progressBar.setProgress(count)
                count += 1
                   
class MirrorSetup(object):

    def __init__(self):
        self.mirrorClass=MirrorHierarchy()
        self.mirrorClass.settings.hierarchy=True
        self.win='MirrorSetup'
        
    @classmethod
    def show(cls):
        cls()._showUI()
        
    def _showUI(self):
                 
        if cmds.window(self.win, exists=True):
            cmds.deleteUI(self.win, window=True)
        window = cmds.window(self.win, title=LANGUAGE_MAP._Mirror_Setup_.title, s=False, widthHeight=(280, 410))
        cmds.menuBarLayout()
        cmds.menu(l=LANGUAGE_MAP._Generic_.vimeo_menu)
        cmds.menuItem(l=LANGUAGE_MAP._Generic_.vimeo_help, \
                      c="import Red9.core.Red9_General as r9General;r9General.os_OpenFile('https://vimeo.com/57882801')")
        cmds.menuItem(divider=True)
        cmds.menuItem(l=LANGUAGE_MAP._Generic_.contactme, c=lambda *args: (r9Setup.red9ContactInfo()))
        cmds.columnLayout(adjustableColumn=True, columnAttach=('both', 5))
        cmds.separator(h=15, style='none')
        cmds.text(l=LANGUAGE_MAP._Mirror_Setup_.side)
        cmds.rowColumnLayout(nc=3, columnWidth=[(1, 90), (2, 90), (3, 90)])
        self.uircbMirrorSide = cmds.radioCollection('mirrorSide')
        cmds.radioButton('Right', label=LANGUAGE_MAP._Generic_.right)
        cmds.radioButton('Centre', label=LANGUAGE_MAP._Generic_.centre)
        cmds.radioButton('Left', label=LANGUAGE_MAP._Generic_.left)
        cmds.setParent('..')
        cmds.separator(h=15, style='in')
        cmds.rowColumnLayout(nc=2, columnWidth=[(1, 110), (2, 60)])
        cmds.text(label=LANGUAGE_MAP._Mirror_Setup_.index)
        cmds.intField('ifg_mirrorIndex', v=1, min=1, w=50)
        cmds.setParent('..')
        cmds.separator(h=15, style='in')
        cmds.text(l=LANGUAGE_MAP._Mirror_Setup_.axis)
        cmds.separator(h=5, style='none')
        cmds.rowColumnLayout(nc=2, columnWidth=[(1, 130), (2, 130)])
        cmds.checkBox('default', l=LANGUAGE_MAP._Mirror_Setup_.default_axis, v=True,
                      onc=lambda x: self.__uicb_setDefaults('default'),
                      ofc=lambda x: self.__uicb_setDefaults('custom'))
        cmds.checkBox('setDirectCopy',l=LANGUAGE_MAP._Mirror_Setup_.no_inverse, v=False,
                      ann=LANGUAGE_MAP._Mirror_Setup_.no_inverse_ann,
                      onc=lambda x:self.__uicb_setDefaults('direct'),  # cmds.checkBox('default',e=True, v=False),
                      ofc=lambda x:self.__uicb_setDefaults('default'))  # cmds.checkBox('default',e=True, v=True))
        cmds.setParent('..')
        cmds.separator(h=5, style='none')
        cmds.rowColumnLayout(ann=LANGUAGE_MAP._Generic_.attrs, numberOfColumns=3,
                                 columnWidth=[(1, 90), (2, 90), (3, 90)])
        cmds.checkBox('translateX', l=LANGUAGE_MAP._Generic_.transX, v=False)
        cmds.checkBox('translateY', l=LANGUAGE_MAP._Generic_.transY, v=False)
        cmds.checkBox('translateZ', l=LANGUAGE_MAP._Generic_.transZ, v=False)
        cmds.checkBox('rotateX', l=LANGUAGE_MAP._Generic_.rotX, v=False)
        cmds.checkBox('rotateY', l=LANGUAGE_MAP._Generic_.rotY, v=False)
        cmds.checkBox('rotateZ', l=LANGUAGE_MAP._Generic_.rotZ, v=False)
        cmds.setParent('..')
        cmds.separator(h=15, style='in')
        cmds.button(label=LANGUAGE_MAP._Mirror_Setup_.refresh, bgc=r9Setup.red9ButtonBGC(1),
                     command=lambda *args: (self.__uicb_getMirrorIDsFromNode()))
        cmds.separator(h=15, style='none')
        cmds.button(label=LANGUAGE_MAP._Mirror_Setup_.add_update, bgc=r9Setup.red9ButtonBGC(1),
                     ann=LANGUAGE_MAP._Mirror_Setup_.add_update_ann,
                     command=lambda *args: (self.__setMirrorIDs()))
        cmds.rowColumnLayout(nc=2, columnWidth=[(1, 135), (2, 135)])
        cmds.button(label=LANGUAGE_MAP._Mirror_Setup_.print_debugs, bgc=r9Setup.red9ButtonBGC(1),
                     ann=LANGUAGE_MAP._Mirror_Setup_.print_debugs_ann,
                     command=lambda *args: (self.__printDebugs()))
        cmds.button(label=LANGUAGE_MAP._Mirror_Setup_.delete, bgc=r9Setup.red9ButtonBGC(1),
                     command=lambda *args: (self.__deleteMarkers()))
        cmds.setParent('..')
        cmds.separator(h=15, style='in')
        cmds.rowColumnLayout(nc=2, columnWidth=[(1, 135), (2, 135)])
        cmds.checkBox('mirrorSaveLoadHierarchy', l=LANGUAGE_MAP._Generic_.hierarchy, v=False)
        cmds.checkBox('mirrorClearCurrent', l=LANGUAGE_MAP._Mirror_Setup_.clear, v=True)
        cmds.setParent('..')
        cmds.rowColumnLayout(nc=2, columnWidth=[(1, 135), (2, 135)])
        cmds.button(label=LANGUAGE_MAP._Mirror_Setup_.save_configs, bgc=r9Setup.red9ButtonBGC(1),
                     ann=LANGUAGE_MAP._Mirror_Setup_.save_configs_ann,
                     command=lambda *args: (self.__saveMirrorSetups()))
        cmds.button(label=LANGUAGE_MAP._Mirror_Setup_.load_configs, bgc=r9Setup.red9ButtonBGC(1),
                     command=lambda *args: (self.__loadMirrorSetups()))
        cmds.setParent('..')
        cmds.separator(h=15, style='none')
        cmds.iconTextButton(style='iconOnly', bgc=(0.7, 0, 0), image1='Rocket9_buttonStrap2.bmp',
                             c=r9Setup.red9ContactInfo, h=22, w=200)
        cmds.showWindow(window)
        self.__uicb_setDefaults('default')
        cmds.window(self.win, e=True, widthHeight=(280, 410))
        cmds.radioCollection('mirrorSide', e=True, select='Centre')

    def __uicb_getMirrorIDsFromNode(self):
        '''
        set the flags based on the given nodes mirror setup
        '''
        node = cmds.ls(sl=True)[0]
        axis = None
        index = self.mirrorClass.getMirrorIndex(node)
        side = self.mirrorClass.getMirrorSide(node)
        cmds.checkBox('setDirectCopy', e=True, v=False)
        cmds.checkBox('default', e=True, v=False)
        
        if side and index:
            cmds.radioCollection('mirrorSide', e=True, select=side)
            cmds.intField('ifg_mirrorIndex', e=True, v=index)
        else:
            raise StandardError('mirror Data not setup on this node')
        
        if cmds.attributeQuery(self.mirrorClass.mirrorAxis, node=node, exists=True):
            axis = self.mirrorClass.getMirrorAxis(node)
            if not axis:
                cmds.checkBox('setDirectCopy', e=True, v=True)
                return
            
        if axis:
            self.__uicb_setDefaults('custom')
            for a in axis:
                if a == 'translateX':
                    cmds.checkBox('translateX', e=True, v=True)
                elif a == 'translateY':
                    cmds.checkBox('translateY', e=True, v=True)
                elif a == 'translateZ':
                    cmds.checkBox('translateZ', e=True, v=True)
                elif a == 'rotateX':
                    cmds.checkBox('rotateX', e=True, v=True)
                elif a == 'rotateY':
                    cmds.checkBox('rotateY', e=True, v=True)
                elif a == 'rotateZ':
                    cmds.checkBox('rotateZ', e=True, v=True)
        else:
            cmds.checkBox('default', e=True, v=True)
            self.__uicb_setDefaults('default')
        
    def __printDebugs(self):
        self.mirrorClass.nodes = cmds.ls(sl=True)
        self.mirrorClass.printMirrorDict()
    
    def __deleteMarkers(self):
        nodes = cmds.ls(sl=True, l=True)
        if nodes:
            for node in nodes:
                self.mirrorClass.deleteMirrorIDs(node)
                log.info('deleted MirrorMarkers from : %s' % r9Core.nodeNameStrip(node))
        
    def __uicb_setDefaults(self, mode):
        enable=False
        if mode =='direct':
            cmds.checkBox('default', e=True, v=False)
        if mode =='custom':
            enable=True
        cmds.checkBox('translateX', e=True, en=enable, v=False)
        cmds.checkBox('translateY', e=True, en=enable, v=False)
        cmds.checkBox('translateZ', e=True, en=enable, v=False)
        cmds.checkBox('rotateX', e=True, en=enable, v=False)
        cmds.checkBox('rotateY', e=True, en=enable, v=False)
        cmds.checkBox('rotateZ', e=True, en=enable, v=False)
        # now set
        if mode=='default':
            cmds.checkBox('setDirectCopy', e=True, v=False)
            for axis in self.mirrorClass.defaultMirrorAxis:
                if axis == 'translateX':
                    cmds.checkBox('translateX', e=True, v=True)
                elif axis == 'translateY':
                    cmds.checkBox('translateY', e=True, v=True)
                elif axis == 'translateZ':
                    cmds.checkBox('translateZ', e=True, v=True)
                elif axis == 'rotateX':
                    cmds.checkBox('rotateX', e=True, v=True)
                elif axis == 'rotateY':
                    cmds.checkBox('rotateY', e=True, v=True)
                elif axis == 'rotateZ':
                    cmds.checkBox('rotateZ', e=True, v=True)

    def __ui_getMirrorAxis(self):
        '''
        note this is a string
        '''
        if cmds.checkBox('default', q=True, v=True):
            return None
        elif cmds.checkBox('setDirectCopy', q=True, v=True):
            return 'None'
        else:
            axis = []
            if cmds.checkBox('translateX', q=True, v=True):
                axis.append('translateX')
            if cmds.checkBox('translateY', q=True, v=True):
                axis.append('translateY')
            if cmds.checkBox('translateZ', q=True, v=True):
                axis.append('translateZ')
            if cmds.checkBox('rotateX', q=True, v=True):
                axis.append('rotateX')
            if cmds.checkBox('rotateY', q=True, v=True):
                axis.append('rotateY')
            if cmds.checkBox('rotateZ', q=True, v=True):
                axis.append('rotateZ')
            if axis:
                return ','.join(axis)
            else:
                return 'None'
                  
    def __setMirrorIDs(self):
        nodes = cmds.ls(sl=True)
        
        # mirrorSlot
        index = cmds.intField('ifg_mirrorIndex', q=True, v=True)
        # mirrorSide
        side = cmds.radioCollection('mirrorSide', q=True, select=True)
        # mirrorAxis
        axis = self.__ui_getMirrorAxis()
        
        if len(nodes) > 1:
  
            result = cmds.confirmDialog(
                title='Mirror Markers',
                message='Add incremented Mirror Markers to Muliple selected nodes?',
                button=['OK', 'Cancel'],
                defaultButton='OK',
                cancelButton='Cancel',
                dismissString='Cancel')
            if result == 'OK':
                i = index
                for node in nodes:
                    self.mirrorClass.setMirrorIDs(node, side=str(side), slot=i, axis=axis)
                    log.info('MirrorMarkers added to : %s' % r9Core.nodeNameStrip(node))
                    i += 1
        else:
            self.mirrorClass.setMirrorIDs(nodes[0], side=str(side), slot=index, axis=axis)
            log.info('MirrorMarkers added to : %s' % r9Core.nodeNameStrip(nodes[0]))
    
    def __saveMirrorSetups(self):
        filepath = cmds.fileDialog2(fileFilter="mirrorMap Files (*.mirrorMap *.mirrorMap);;", okc='Save', cap='Save MirrorSetups')[0]
        self.mirrorClass.nodes = cmds.ls(sl=True)
        if cmds.checkBox('mirrorSaveLoadHierarchy', q=True, v=True):
            self.mirrorClass.settings.hierarchy = True
        self.mirrorClass.saveMirrorSetups(filepath=filepath)

    def __loadMirrorSetups(self):
        filepath = cmds.fileDialog2(fileFilter="mirrorMap Files (*.mirrorMap *.mirrorMap);;", okc='Load', cap='Load MirrorSetups', fileMode=1)[0]
        if cmds.checkBox('mirrorSaveLoadHierarchy', q=True, v=True):
            self.mirrorClass.nodes = cmds.ls(sl=True, l=True)
            self.mirrorClass.loadMirrorSetups(filepath=filepath, clearCurrent=cmds.checkBox('mirrorClearCurrent', q=True, v=True))
        else:
            self.mirrorClass.loadMirrorSetups(filepath=filepath, nodes=cmds.ls(sl=True, l=True), clearCurrent=cmds.checkBox('mirrorClearCurrent', q=True, v=True))



class CameraTracker():
    
    def __init__(self, fixed=True):
        self.win = 'CameraTrackOptions'
        self.fixed = fixed
    
    @staticmethod
    def cameraTrackView(start=None, end=None, step=None, fixed=True, keepOffset=False):
        '''
        CameraTracker is a simple wrap over the internal viewFit call but this manages the data
        over time. Works by taking the current camera, in the current 3dView, and fitting it to
        frame the currently selected objects per frame, or rather per frameStep.
        
        :param start: start frame
        :param end: end frame
        :param step: frame step to increment between fit
        :param fixed: switch between tracking or panning framing fit
        :param keepOffset: keep the current camera offset rather than doing a full viewFit
        
        TODO:: 
            add option for cloning the camera rather than using the current directly
        '''
        if not cmds.ls(sl=True):
            raise StandardError('Nothing selected to Track!')
        cam = cmds.modelEditor(cmds.playblast(ae=True).split('|')[-1], q=True, camera=True)
        cmds.cutKey(cam, cl=True, t=(), f=())
        
        if not start:
            start = timeLineRangeGet()[0]
        if not end:
            end = timeLineRangeGet()[1]
        if not step:
            if cmds.optionVar(exists='red9_cameraTrackStep'):
                step = cmds.optionVar(q='red9_cameraTrackStep')
            else:
                step = 10
        if not keepOffset:
            if cmds.optionVar(exists='red9_cameraTrackKeepOffset'):
                keepOffset = cmds.optionVar(q='red9_cameraTrackKeepOffset')
                   
        if fixed:
            if keepOffset:
                cachedTransform = cmds.getAttr('%s.translate' % cam)[0]
            else:
                # not sure about this?
                cmds.viewFit(cam, animate=False)
        else:
            if keepOffset:
                cachedTransform = cmds.getAttr('%s.translate' % cam)[0]
                cmds.viewFit(cam, animate=False)
                shifted = cmds.getAttr('%s.translate' % cam)[0]
                offset = [(cachedTransform[0] - shifted[0]), (cachedTransform[1] - shifted[1]), (cachedTransform[2] - shifted[2])]
            
        for i in timeLineRangeProcess(start, end, step, incEnds=True):
            cmds.currentTime(i)
            if fixed:
                # fixed transform, panning camera
                cmds.viewLookAt(cam)
                if keepOffset:
                    cmds.setAttr('%s.translate' % cam, cachedTransform[0], cachedTransform[1], cachedTransform[2])
            else:
                # transform tracking camera
                cmds.viewFit(cam, animate=False)
                if keepOffset:
                    cmds.move(offset[0], offset[1], offset[2], cam, r=True)
                    cmds.refresh()
            cmds.setKeyframe(cam, t=i)
        cmds.filterCurve(cam)

    @classmethod
    def show(cls):
        cls()._showUI()
    
    def _showUI(self):
        if cmds.window(self.win, exists=True):
            cmds.deleteUI(self.win, window=True)
        cmds.window(self.win, title=LANGUAGE_MAP._CameraTracker_.title, widthHeight=(263, 180))
        cmds.menuBarLayout()
        cmds.menu(l=LANGUAGE_MAP._Generic_.vimeo_menu)
        cmds.menuItem(l=LANGUAGE_MAP._Generic_.vimeo_help, \
                      c="import Red9.core.Red9_General as r9General;r9General.os_OpenFile('https://vimeo.com/60960492')")
        cmds.menuItem(divider=True)
        cmds.menuItem(l=LANGUAGE_MAP._Generic_.contactme, c=lambda *args: (r9Setup.red9ContactInfo()))
        cmds.columnLayout(adjustableColumn=True)
        cmds.separator(h=15, style='none')
        cmds.intFieldGrp('CameraFrameStep', numberOfFields=1,
                         label=LANGUAGE_MAP._CameraTracker_.tracker_step, value1=10,
                         extraLabel=LANGUAGE_MAP._CameraTracker_.frames,
                         cw=(1, 100),
                         cc=partial(self.__storePrefs))
        cmds.separator(h=15, style='none')
        cmds.checkBox('CBMaintainCurrent', l=LANGUAGE_MAP._CameraTracker_.maintain_frame, v=True, cc=partial(self.__storePrefs))
        cmds.separator(h=15, style='none')
        cmds.rowColumnLayout(numberOfColumns=2, columnWidth=[(1, 130), (2, 130)])
        if self.fixed:
            cmds.button('cameraTrackTrack', label=LANGUAGE_MAP._CameraTracker_.pan, command=partial(self.__runTracker))
        else:
            cmds.button('cameraTrackTrack', label=LANGUAGE_MAP._CameraTracker_.track, command=partial(self.__runTracker))
        cmds.button('cameraTrackAppy', label=LANGUAGE_MAP._Generic_.apply, command=partial(self.__storePrefs))
        cmds.setParent('..')
        cmds.separator(h=15, style='none')
        cmds.iconTextButton(style='iconOnly', bgc=(0.7, 0, 0), image1='Rocket9_buttonStrap2.bmp',
                             c=lambda *args: (r9Setup.red9ContactInfo()), h=22, w=200)
        cmds.showWindow(self.win)
        cmds.window(self.win, e=True, widthHeight=(263, 180))
        self.__loadPrefsToUI()

    def __storePrefs(self, *args):
        if cmds.window(self.win, exists=True):
            cmds.optionVar(intValue=('red9_cameraTrackStep', cmds.intFieldGrp('CameraFrameStep', q=True, v1=True)))
            cmds.optionVar(intValue=('red9_cameraTrackKeepOffset', cmds.checkBox('CBMaintainCurrent', q=True, v=True)))
            log.debug('stored out cameraTracker prefs')

    def __loadPrefsToUI(self):
        if cmds.optionVar(exists='red9_cameraTrackStep'):
            cmds.intFieldGrp('CameraFrameStep', e=True, v1=cmds.optionVar(q='red9_cameraTrackStep'))
        if cmds.optionVar(exists='red9_cameraTrackKeepOffset'):
            cmds.checkBox('CBMaintainCurrent', e=True, v=cmds.optionVar(q='red9_cameraTrackKeepOffset'))
            
    def __runTracker(self, *args):
        self.__storePrefs()
        self.cameraTrackView(fixed=self.fixed)


class ReconnectAnimData(object):
    
    def __init__(self):
        self.win = 'ReconnectAnimData'
        
    @classmethod
    def show(cls):
        cls()._showUI()
    
    def _showUI(self):
        if cmds.window(self.win, exists=True):
            cmds.deleteUI(self.win, window=True)
        cmds.window(self.win, title=self.win, widthHeight=(300, 220))
        
        cmds.menuBarLayout()
        cmds.menu(l="Help")
        cmds.menuItem(l="Bug post -LostAnimPart1", \
                      c="import Red9.core.Red9_General as r9General;r9General.os_OpenFile('http://markj3d.blogspot.co.uk/2011/07/lost-animation-when-loading-referenced.html')")
        cmds.menuItem(l="Bug post -LostAnimPart1", \
                      c="import Red9.core.Red9_General as r9General;r9General.os_OpenFile('http://markj3d.blogspot.co.uk/2012/09/lost-animation-part2.html')")
        cmds.menuItem(l="Bug post -LostAnimPart3", \
                      c="import Red9.core.Red9_General as r9General;r9General.os_OpenFile('http://markj3d.blogspot.co.uk/2014/09/lost-animation-part-3.html')")
        cmds.menuItem(divider=True)
        cmds.menuItem(l="Contact Me", c=lambda *args: (r9Setup.red9ContactInfo()))
        
        cmds.columnLayout('uicl_audioMain',adjustableColumn=True)
        cmds.separator(h=10, style='none')
        cmds.text(l='BUG: Symtoms - Maya file loaded but character\nwas left in T-Pose and all animation looks lost!', align='center')
        cmds.separator(h=15, style='none')
        cmds.button(label='Reconnect Via >> Referenced ChSet',
                    ann='Select the CharacterSet that you want to try and recover',
                    command=ReconnectAnimData.reConnectReferencedAnimData)
        
        cmds.separator(h=15, style='in')
        cmds.checkBox('StripNamespaces', l='StripNamespaces in Match', v=True)
        cmds.checkBox('AllowMergedLayers', l='Strip MergedLayer data conventions', v=False)
        cmds.button(label='Reconnect Via >> Blind Names & Selected Nodes',
                    ann='Select nodes or CharacterSet that you want to recover via a blind animCurve name match methods',
                    command=self.__uiCB_reConnectAnimDataBlind)
        cmds.separator(h=15, style='none')

        cmds.iconTextButton(style='iconOnly', bgc=(0.7, 0, 0), image1='Rocket9_buttonStrap2.bmp',
                             c=lambda *args: (r9Setup.red9ContactInfo()), h=22, w=200)
        cmds.showWindow(self.win)
        cmds.window(self.win, e=True, widthHeight=(300, 210))
    
    def __uiCB_reConnectAnimDataBlind(self, *args):
        ReconnectAnimData.reConnectAnimDataBlind(stripNamespace=cmds.checkBox('StripNamespaces', q=True, v=True),
                                                 stripLayerNaming=cmds.checkBox('AllowMergedLayers', q=True, v=True))
                                                                             
    @staticmethod
    def reConnectReferencedAnimData(*args):
        '''
        As per my blog posts on Lost Animaton's see here for details:
        http://markj3d.blogspot.co.uk/2011/07/lost-animation-when-loading-referenced.html
        
        '''
        import pymel.core as pm
        
        objs = pm.ls(sl=True, st=True)
        if not objs:
            raise StandardError('nothing selected to process, please select the characterSet of the broken reference')
        
        cSet, nodetype = objs
        refNode = cSet.referenceFile().refNode
    
        if not nodetype == 'character':
            raise StandardError('You must select a CharacterSet to reconnect')
        if not refNode:
            raise StandardError('Given characterSet is not from a referenced file')
        
        animCurves = refNode.listConnections(type='animCurve', s=True)
        cSetPlugs = pm.aliasAttr(cSet, q=True)
        
        for plug in cSetPlugs[::2]:
            for anim in animCurves:
                if anim.split(':')[-1].endswith(plug):
                    print '%s >> %s' % (anim, plug)
                    pm.connectAttr('%s.output' % anim, '%s.%s' % (cSet, plug), force=True)
                    
                    
    @staticmethod
    def reConnectAnimDataBlind(stripNamespace=True, stripLayerNaming=False, *args):
        '''
        Blind reconnect based on names. As per my blog posts on Lost Animaton's see here for details:
        http://markj3d.blogspot.co.uk/2012/09/lost-animation-part2.html
        
        :param stripNamespace: Change this to False if the curves are not in the rootNamespace but
            in the sameNamespace as the controllers.
        :param stripLayerNaming: allows for the additional 'Merged_Layer_inputB' naming conventions
        '''
        nodes=cmds.ls(sl=True,l=True)
        chns=[]
        
        #build up the main lists
        animCurves=cmds.ls(type='animCurve',s=True)
        [chns.extend(cmds.listAnimatable(node)) for node in nodes]
            
        for chn in chns:
            if stripNamespace:
                animCurveExpected=chn.split(':')[-1].split('|')[-1].replace('.','_')
            else:
                animCurveExpected=chn.split('|')[-1].replace('.','_')
            if animCurveExpected in animCurves:
                if not cmds.isConnected('%s.output' % animCurveExpected,chn):
                    print '%s >> %s' % (animCurveExpected,chn)
                    cmds.connectAttr('%s.output' % animCurveExpected,chn,force=True)
            elif stripLayerNaming:
                for curve in animCurves:
                    curveStripped=curve.replace('_Merged_Layer_inputB','').rstrip('123456789')
                    if curveStripped == animCurveExpected:
                        if not cmds.isConnected(curve, chn):
                            print '%s >> %s' % (curve, chn)
                            cmds.connectAttr('%s.output' % curve,chn,force=True)
        
        
    
    
    
    
