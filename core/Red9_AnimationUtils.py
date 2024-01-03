'''
..
    Red9 Pro Pack: Maya Pipeline Solutions
    ======================================
     
    Author: Mark Jackson
    email: info@red9consultancy.com
     
    Red9 : http://red9consultancy.com
    Red9 Vimeo : https://vimeo.com/user9491246
    Twitter : @red9_anim
    Facebook : https://www.facebook.com/Red9Anim


    This is the core of the Animation Toolset Lib, a suite of tools
    designed from production experience to automate an animators life.

    Setup : Follow the Install instructions in the Modules package


Code examples:


 **ProcessNodes**

    All of the functions which have the ProcessNodes call share the same
    underlying functionality as described below. This is designed to process the
    given input nodes in a consistent manor across all the functions.
    Params: 'nodes' and 'filterSettings' are treated as special and build up a
    MatchedNode object that contains a tuple of matching pairs based on the given settings.


 **AnimFunctions example:**


    The main AnimFunctions class is designed to run with an r9Core.FilterNode
    object that is responsible for how we process hierarchies. If one isn't passed
    as an arg then the code simply processes the 'nodes' args in zipped pairs.
    See the documentation on the r9Core.MatchedNodeInputs for more detail.

    All the AnimFunctions such as copyKeys, copyAttrs etc use the same base setup

    >>> import Red9_CoreUtils as r9Core
    >>> import maya.cmds as cmds
    >>>
    >>> #===========================
    >>> # When Processing hierarchies:
    >>> #===========================
    >>> # The Filter_Settings object required for hierarchy processing is now bound to
    >>> # the class directly so you no longer need to create a filterSettigns object directly!
    >>> # Lets set the filter to process nodes with a given attr 'myControl' who's type is 'nurbscurve'
    >>> animFunc=r9Anim.AnimFunctions()
    >>> animFunc.settings.nodeTypes ='nurbsCurve'
    >>> animFunc.settings.searchAttrs = 'myControl'
    >>> animFunc.settings.printSettings()
    >>>
    >>> # now run any of the AnimFunctions and pass in nodes which with the filter active
    >>> # as above would be the 2 root nodes of the hierarchies to filter
    >>>
    >>> animFunc.copyAttributes(cmds.ls(sl=True,l=True))
    >>>
    >>> animFunc.snapTransform(nodes=cmds.ls(sl=True), time=r9Anim.timeLineRangeGet())
    >>>
    >>> #==============================
    >>> # When processing simple objects:
    >>> #==============================
    >>> # If you simply ignore the filterSettings you can just process given nodes directly
    >>> # the nodes are zipped into selected pairs obj[0]>obj[1], obj[2]>obj[3] etc
    >>> anim = r9Anim.AnimFunctions()
    >>> anim.snapTransform(nodes=cmds.ls(sl=True), time=r9Anim.timeLineRangeGet())

'''

from __future__ import print_function

import maya.cmds as cmds
import maya.mel as mel
import maya.OpenMaya as OpenMaya

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
import math
import traceback

import Red9.packages.configobj as configobj


import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

def logging_is_debug():
    if log.level == 10:
        return True

# global var so that the animUI is exposed to anything as a global object
global RED_ANIMATION_UI
RED_ANIMATION_UI = None

global RED_ANIMATION_UI_OPENCALLBACKS
RED_ANIMATION_UI_OPENCALLBACKS = []

'''
Callback globals so you can fire in commands prior to the UI opening,
we use this internally to fire an asset sync call on our project pose library
and to setup some additional paths.

def myProjectCallback(cls)
    cls.poseHandlerPaths=['MyProjects/resources/poseHandlers']
    cls.posePathProject ='My_projects/global/project/pose/lib'

r9Anim.RED_ANIMATION_UI_OPENCALLBACKS.append(myProjectCallback)

.. note::
    the function calls bound to the callback are passed the current instance of the animUI class
    as an arg so you can modify as you need. Also when the PoseUI RMB popup menu is built, IF paths in the list
    cls.poseHandlerPaths are valid, then we bind into that popup all valid poseHandler.py files
    found the given path. This allow you to add custom handler types and expose them through the UI directly,
    they will show up in the RMB popup as such: Fingers_poseHandler.py will show as 'Add Subfolder : FINGERS'
'''


# Language map is used for all UI's as a text mapping for languages
LANGUAGE_MAP = r9Setup.LANGUAGE_MAP

# ===========================================================================
# Generic Utility Functions
# ===========================================================================

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

def getChannelBoxSelection(longNames=False):
    '''
    return a list of attributes selected in the ChannelBox

    :param longNames: return the longNames of the attrs selected, else we default to Maya's short attr names
    '''
    attrs = cmds.channelBox('mainChannelBox', q=True, selectedMainAttributes=True)
    _attrs = []
    if attrs and longNames:
        for attr in attrs:
            try:
                _attrs.append(cmds.attributeQuery(attr, n=cmds.ls(sl=True, l=True)[0], ln=1))
            except:
                pass
        # attrs = [cmds.attributeQuery(a, n=cmds.ls(sl=True, l=True)[0], ln=1) for a in attrs]
    return attrs

def getNodeAttrStatus(node=None, asDict=True, incLocked=True):
    '''
    stub function/ wrapper of getChannelBoxAttrs as the name is a
    little misleading and not really what the function is doing in hindsight.
    '''
    return getChannelBoxAttrs(node=None, asDict=True, incLocked=True)

def is_compound_attr(node, attr):
    '''
    return True is a given attr is a compound attr. This has a catch in it to prevent errors
    in the code below when listAttr returns attrs that arne't technically legal when being queried
    ie, listAttr(node) where node is a parentConstraint and you get .target.targetWeight which can't be queried
    without some prior work
    '''
    try:
        selection = OpenMaya.MSelectionList()
        selection.add('%s.%s' % (node, attr))
        plug = OpenMaya.MPlug()
        selection.getPlug(0, plug)
        return plug.isCompound()
    except:
        return True
    
def getChannelBoxAttrs(node=None, asDict=True, incLocked=True, skipcompound=False):
    '''
    return the status of all attrs on the given node, either as a flat list or
    a dict. As dict it contains all data which controls the lock, keyable, hidden states etc

    statusDict={'keyable':attrs, 'nonKeyable':attrs, 'locked':attrs}

    :param node: given node.
    :param asDict: True returns a dict with keys 'keyable','locked','nonKeyable' of attrs
        False returns a list (non ordered) of all attr states.
    :param incLocked: True by default - whether to include locked channels in the return (only valid if not asDict)
    :param skipcompound: if True we remove the compound parent attrs from any return (ie double3 or float3 which
         prevents unlocked compounds like "rotate", "translate", "scale" from getting into the return
    '''
    statusDict = {}
    if not node:
        node = cmds.ls(sl=True, l=True)[0]
    
    if skipcompound:
        # skip double3 or float3 containters
        statusDict['keyable'] = [attr for attr in cmds.listAttr(node, keyable=True, unlocked=True) or [] \
                                 if not is_compound_attr(node, attr)]

        statusDict['locked'] = [attr for attr in cmds.listAttr(node, keyable=True, locked=True) or [] \
                                if not is_compound_attr(node, attr)]

        statusDict['nonKeyable']  = [attr for attr in cmds.listAttr(node, channelBox=True) or [] \
                                     if not is_compound_attr(node, attr)]
    else:
        statusDict['keyable'] = cmds.listAttr(node, keyable=True, unlocked=True)
        statusDict['locked'] = cmds.listAttr(node, keyable=True, locked=True)
        statusDict['nonKeyable']  = cmds.listAttr(node, channelBox=True)
    
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

def getSettableChannels(node=None, incStatics=True, skipcompound=False):
    '''
    return a list of settable attributes on a given node.

    :param node: node to inspect.
    :param incStatics: whether to include non-keyable static channels (On by default).
    :param skipcompound: if True we remove the compound parent attrs from any return (double3 or float3 at the moment
        this prevents unlocked componuds like "rotate", "translate", "scale" from getting into the return

    FIXME: BUG some Compound attrs such as constraints return invalid data for some of the
    base functions using this as they can't be simply set. Do we strip them here?
    ie: pointConstraint.target.targetWeight

    # TODO: need to check the blendshape channels are settable also!
    '''
    if not node:
        node = cmds.ls(sl=True, l=True)[0]
    if cmds.nodeType(node) == 'blendShape':
        return r9Core.getBlendTargetsFromMesh(node)

    if not incStatics:
        # keyable and unlocked only
        if not skipcompound:
            return cmds.listAttr(node, k=True, u=True)
        else:
            return [attr for attr in cmds.listAttr(node, k=True, u=True) or [] \
                        if not is_compound_attr(node, attr)]
    else:
        # all settable attrs in the channelBox
        return getChannelBoxAttrs(node, asDict=False, incLocked=False, skipcompound=skipcompound)

def nodesDriven(nodes, allowReferenced=False, skipLocked=False, nodes_only=False):
    '''
    return a list of those nodes that are actively constrained or connected to a pairBlend
    currently used to pre-validate nodes in the mirror class prior to running the actual mirror call

    :param allowReferenced: if True we allow all constraints to be returned, if False any constraints
        that are referenced are skipped. This by-passes internal rig constraints and only returns
        constraints made in the main scene.
    :parm skipLocked: if True we ignore the relevant channels that are constrained if the attrs themselves aren't keyable
    '''
    
    data = []

    for node in nodes:
        driven = []
        cons = []
        plug = cmds.listConnections(node, type='character', s=True, d=False, p=True)
        if not plug:
            plug = node
        if plug:
            cons = cmds.listConnections(plug, s=True, d=False, type='constraint', c=True)
            if not cons:
                cons = cmds.listConnections(node, s=True, d=False, type='pairBlend', c=True)
            if cons:
                cons = zip(cons[0::2], cons[1::2])
                for attr, con in cons:
                    if skipLocked:
                        if not cmds.getAttr(attr, k=True):
                            continue
                    if con not in driven:
                        driven.append(con)

                for con in driven:
                    if allowReferenced:
                        if not nodes_only:
                            data.append((node, con))
                        else:
                            if not node in data:
                                data.append(node)
                        log.info('%s is currently driven by >> %s' % (r9Core.nodeNameStrip(node), con))
                    elif not cmds.referenceQuery(con, inr=True):
                        if not nodes_only:
                            data.append((node, con))
                        else:
                            if not node in data:
                                data.append(node)
                        log.info('%s is currently driven by >> %s' % (r9Core.nodeNameStrip(node), con))
    return data

def getKeyedAttrs(nodes, attrs=[], returnkeyed=True, asMap=False):
    '''
    from a list of nodes return either all keyed or unkeyed attributes

    :param nodes: the list of nodes were going to test
    :param attrs: if given we only check against those given attrs
    :param returnKeyed: True by default, return all keyed attrs
    :param asMap: if true we return (attr, curve) rather than just the list of attrs, only valid if returnKeyed
    '''
    keylist = {}
    exclude = ['translate', 'rotate', 'scale']  # skip compounds
    for node in nodes:
        if not attrs:
            _attrs = getChannelBoxAttrs(node=node, asDict=True, incLocked=False).get('keyable') or []
        else:
            _attrs = attrs
        for attr in _attrs:
            if attr in exclude:
                continue
            try:
                curve = cmds.keyframe('%s.%s' % (node, attr), q=True, n=True)
                if returnkeyed and curve:
                    if node not in keylist:
                        keylist[node] = []
                    if asMap:
                        keylist[node].append((attr, curve[0]))
                    else:
                        keylist[node].append(attr)
                if not returnkeyed and not curve:
                    if node not in keylist:
                        keylist[node] = []
                    keylist[node].append(attr)
            except StandardError, err:
                log.debug(err)
    return keylist

def getAnimLayersFromGivenNodes(nodes):
    '''
    return all animLayers associated with the given nodes
    '''
    if not isinstance(nodes, list):
        # This is a hack as the cmds.animLayer call is CRAP. It doesn't mention
        # anywhere in the docs that you can even pass in Maya nodes, yet alone
        # that it has to take a list of nodes and fails with invalid flag if not
        nodes = [nodes]
    return cmds.animLayer(nodes, q=True, affectedLayers=True)

def getAnimLayerMembers(animLayers=[]):
    '''
    simple function to get the current object menmbers of the given animLayers
    
    :param animLayers: animLayers to inspect, if not given we inspect all animLayers
    '''
    nodes = []
    if not animLayers:
        animLayers =  cmds.ls(type='animLayer')
    for layer in animLayers:
        for dag in cmds.listConnections('%s.dagSetMembers' % layer, s=True, d=False) or []:
            node = cmds.ls(dag, l=True)[0]
            if not node in nodes:
                nodes.append(node)
    return nodes

def animLayersConfirmCheck(nodes=None, deleteMerged=True):
    '''
    return all animLayers associated with the given nodes

    :param nodes: nodes to check membership of animLayers. If not pass the check will be at sceneLevel
    :param deleteMerged: modifies the warning message
    '''
    animLayers = []
    message = ''
    if deleteMerged:
        message = 'AnimLayers found in scene:\nThis process needs to merge them down and they will NOT be restored afterwards'
    else:
        message = 'AnimLayers found in scene:\nThis process needs to merge them but they will be restored afterwards'
    if nodes:
        if not isinstance(nodes, list):
            nodes = [nodes]
        animLayers = getAnimLayersFromGivenNodes(nodes)
    else:
        animLayers = cmds.ls(type='animLayer')
    if animLayers and not len(animLayers) == 1:
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
    '''
    animLayers = getAnimLayersFromGivenNodes(nodes)
    if animLayers:
        try:
            # deal with Maya's optVars for animLayers as the call that sets the defaults
            # for these, via the UI call, is a local proc to the performAnimLayerMerge.
            deleteMerged = True
            if cmds.optionVar(exists='animLayerMergeDeleteLayers'):
                deleteMerged = cmds.optionVar(query='animLayerMergeDeleteLayers')
            cmds.optionVar(intValue=('animLayerMergeDeleteLayers', deleteBaked))

            if not cmds.optionVar(exists='animLayerMergeByTime'):
                cmds.optionVar(floatValue=('animLayerMergeByTime', 1.0))  # frame sampling

            # 'optionVar -floatValue animLayerMergeByTime 1' for this on or not?

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
            cmds.optionVar(intValue=('animLayerMergeDeleteLayers', deleteMerged))
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
    con = mel.eval(cmdstring)
    mel.eval(assembled)
    return con

def eulerSelected():
    '''
    cheap trick! for selected objects run a Euler Filter and then delete Static curves
    '''
    cmds.filterCurve(cmds.ls(sl=True, l=True))
    cmds.delete(cmds.ls(sl=True, l=True), sc=True)


def animCurveDrawStyle(style='simple', forceBuffer=True, showBufferCurves=False,
                       displayTangents=False, displayActiveKeyTangents=True, *args):
    '''
    Toggle the state of the graphEditor curve display, used in the Filter and Randomizer to
    simplify the display and the curve whilst processing. This allows you to also pass in
    the state directly, used by the UI close event to return the editor to the last cached state
    '''
    print('toggleCalled', style, showBufferCurves, displayTangents, displayActiveKeyTangents)
    if forceBuffer is not None:
        if forceBuffer:
            if r9Setup.mayaVersion() < 2017:
                mel.eval('doBuffer snapshot;')
            else:
                mel.eval('doBuffer snapshot graphEditor1GraphEd;')
    if style == 'simple':
        # print 'toggle On'
        mel.eval('animCurveEditor -edit -showBufferCurves 1 -displayTangents false -displayActiveKeyTangents false graphEditor1GraphEd;')
    elif style == 'full':
        # print 'toggleOff'
        cmd = 'animCurveEditor -edit'
        if showBufferCurves is not None:
            if showBufferCurves:
                cmd += ' -showBufferCurves 1'
            else:
                cmd += ' -showBufferCurves 0'
        if displayTangents is not None:
            if displayTangents:
                cmd += ' -displayTangents true'
            else:
                cmd += ' -displayTangents false'
        if displayActiveKeyTangents is not None:
            if displayActiveKeyTangents:
                cmd += ' -displayActiveKeyTangents true'
            else:
                cmd += ' -displayActiveKeyTangents false'
        mel.eval('%s graphEditor1GraphEd;' % cmd)


# ----------------------------------------------------------------------------
# TimeRange / AnimRange Functions ----
# ----------------------------------------------------------------------------

# class TimeRangeProcess_iterator():
#     '''
#     This replaces the timeLineRangeProcess function above and wraps it into
#     a more convenient iterator
#     '''
#     def __init__(self, start, end, step, incEnds=True, nodes=[]):
#         self.current = start
#         self.end = end
#         self.step = step
#         if step < 0:
#             self.current = end
#
#     def __iter__(self):
#         return self
#
#     def next(self):
#         if self.step > 0:
#             if self.current > self.end:
#                 raise StopIteration
#         else:
#             if self.current < self.end:
#                 raise StopIteration
#
#         self.current += self.step
#         return self.current - self.step

def animCurve_get_bounds(curve, bounds_only=False, skip_static=True):
    '''
    from a given anim curve find it's upper and lower bounds. By default we examine the keyValues
    for change and return the upper and lower bounds for change.

    :param curve: the anim curve to inspect
    :param bounds_only: if True we only return the key bounds, first and last key times,
        else we look at the changing values to find the bounds
    :param skip_static: if True we ignore static curves and return [], else we return
        the key bounds for the static keys, ignoring the keyValues
    '''
    keyList = cmds.keyframe(curve, q=True, vc=True, tc=True)
    if not keyList:
        return False
    keydata = zip(keyList[0::2], keyList[1::2])
    minV = keydata[0]
    maxV = keydata[-1]
    bounds = [minV[0], maxV[0]]

    if bounds_only:
        return bounds

    # find the min
    for t, v in keydata:
        if not r9Core.floatIsEqual(minV[1], v, 0.001):
            break
        bounds[0] = t
    # find the max
    for t, v in reversed(keydata):
        if not r9Core.floatIsEqual(maxV[1], v, 0.001):
            break
        bounds[1] = t

    if skip_static:
        if bounds[0] == maxV[0]:
            log.debug('curve is static : %s' % curve)
            return []
    else:
        if bounds[0] == maxV[0]:
            log.debug('curve is static : %s' % curve)
            return [minV[0], maxV[0]]
    return bounds

def animRangeFromNodes(nodes, setTimeline=True, decimals=-1, transforms_only=False, skip_static=True, bounds_only=True):
    '''
    return the extent of the animation range for the given objects
    :param nodes: nodes to examine for animation data
    :param setTimeLine: whether we should set the playback timeline to the extent of the found anim data
    :param decimals: int -1 default, this is the number of decimal places in the return, -1 = no clamp
    :param transforms_only: if True we only test translate (animCurveTL) and rotate (animCurveTA) data, added for skeleton fbx baked tests
    :param skip_static: if True we ignore static curves and return [], else we return
        the key bounds for the static keys, ignoring the keyValues
    :param bounds_only: if True we only return the key bounds, first and last key times,
        else we look at the changing values to find the actual animated bounds via keyValue changes
    '''
    minBounds = []
    maxBounds = []
    for anim in r9Core.FilterNode.lsAnimCurves(nodes, safe=True, allow_ref=True):
        if transforms_only and not cmds.nodeType(anim) in ['animCurveTL', 'animCurveTA']:
            continue
        bounds = animCurve_get_bounds(anim, bounds_only=bounds_only, skip_static=skip_static)

        if bounds:
            minBounds.append(bounds[0])
            maxBounds.append(bounds[1])
#         count = cmds.keyframe(anim, q=True, kc=True)
#         minBounds.append(cmds.keyframe(anim, q=True, index=[(0, 0)], tc=True)[0])
#         maxBounds.append(cmds.keyframe(anim, q=True, index=[(count - 1, count - 1)], tc=True)[0])
    if not minBounds and not maxBounds:
        return
    min_rng = min(minBounds)
    max_rng = max(maxBounds)
    if decimals >= 0:
        min_rng = round(min_rng, decimals)
        max_rng = round(max_rng, decimals)
    if setTimeline:
        cmds.playbackOptions(min=min_rng, max=max_rng)
        cmds.playbackOptions(ast=min_rng, aet=max_rng)
    return min_rng, max_rng

def timeLineRangeGet(always=True):
    '''
    Return the current PlaybackTimeline OR if a range is selected in the
    TimeLine, (Highlighted in Red) return that instead.

    :param always: always return a timeline range, if none selected return the playbackRange.
    :rtype: tuple
    :return: (start,end)
    '''
    playbackRange = None
    if not r9Setup.mayaIsBatch():
        PlayBackSlider = mel.eval('$tmpVar=$gPlayBackSlider')
        if cmds.timeControl(PlayBackSlider, q=True, rangeVisible=True):
            time = cmds.timeControl(PlayBackSlider, q=True, rangeArray=True)
            playbackRange = (time[0], time[1])
        elif always:
            playbackRange = (cmds.playbackOptions(q=True, min=True), cmds.playbackOptions(q=True, max=True))
    else:
        playbackRange = (cmds.playbackOptions(q=True, min=True), cmds.playbackOptions(q=True, max=True))
    return playbackRange

def timeLineRangeProcess(start, end, step=1, incEnds=True, nodes=[], process_animlayers=True):
    '''
    Simple wrapper function to take a given framerange and return
    a list[] containing the actual keys required for processing.
    This manages whether the step is negative, if so it reverses the
    times. When nodes are not given this is basically just a wrapper to the
    python range function, if nodes are given then we inspect and return the
    current keys between the start and end given, ignoring step except to reverse the data

    :param start: start frame
    :param end: end frame
    :param step: step between frame
    :param inEnds: when processing without nodes do we include the end frame in the return or exclude it
    :param nodes: inspect the nodes given for keyframes and use that data for the times returned
    :param process_animlayers: when True (default) we process all keys on all layers for the given nodes
    
    .. note::
        this is the base function that the ProPack smartBake functions use to extract the key time data
    '''
    startFrm = start
    endFrm = end
    keys = []
    if nodes:
        if not process_animlayers:
            keys = cmds.keyframe(nodes, q=True, time=(startFrm, endFrm))
        else:
            # look at all animCurve data for the given nodes
            curves = r9Core.FilterNode.lsAnimCurves(nodes)
            if curves:
                keys = cmds.keyframe(curves, q=True, time=(startFrm, endFrm))

        if not keys:
            log.debug('Warning :  No key times extracted from the given nodes, timeLineRange reverted to base range!')
        else:
            rng = sorted(list(set(keys)))
            if step < 0:
                rng.reverse()
            return rng

    # base range method of extraction, used if no nodes or node keytime extraction found nothing
    if step < 0:
        startFrm = end
        endFrm = start

    # ceil added so that fractional keys are stepped up to, range(int(1.0), int(3.5)) = [1, 2] NOT [1, 2, 3]
    rng = [time for time in range(int(startFrm), int(math.ceil(endFrm)), int(step))]
    if incEnds:
        rng.append(endFrm)
    return rng


def selectKeysByRange(nodes=None, animLen=False, bounds_only=True):
    '''
    select the keys from the selected or given nodes within the
    current timeRange or selectedTimerange

    :param nodes: the nodes to inspect, else we use the selected transform nodes
    :param animLen: use the curent timeLine range only
    :param bounds_only: if True we only use the key bounds, first and last key times,
        else we look at the changing values to find the actual animated bounds via keyValue changes
    '''
    if not nodes:
        nodes = cmds.ls(sl=True, type='transform')
    if not animLen:
        cmds.selectKey(nodes, time=timeLineRangeGet())
    else:
        cmds.selectKey(nodes, time=animRangeFromNodes(nodes, setTimeline=False, bounds_only=bounds_only))

def setTimeRangeToo(nodes=None, setall=True, bounds_only=True):
    '''
    set the playback timerange to be the animation range of the selected nodes.
    AnimRange is determined to be the extent of all found animation for a given node

    :param nodes: the nodes to inspect, else we use the selected transform nodes
    :param setall: also set the outer '-ast' / '-aet' timeranges
    :param bounds_only: if True we only use the key bounds, first and last key times,
        else we look at the changing values to find the actual animated bounds via keyValue changes
    '''
    if not nodes:
        nodes = cmds.ls(sl=True, type='transform')
    time = animRangeFromNodes(nodes, bounds_only=bounds_only)
    if time:
        cmds.currentTime(time[0])
        cmds.playbackOptions(min=time[0])
        cmds.playbackOptions(max=time[1])
        if setall:
            cmds.playbackOptions(ast=time[0])
            cmds.playbackOptions(aet=time[1])
    else:
        raise StandardError('given nodes have no found animation data')

def snap(source, destination, snapTranslates=True, snapRotates=True, snapScales=False, *args, **kws):
    '''
    simple wrapper over the AnimFunctions snap call

    :param source: the object we'll be aligning too
    :param destination: the object we'll be snapping
    :param snapTranslates: snap the translate data
    :param snapRotates: snap the rotate data
    '''
    AnimFunctions.snap([source, destination], snapTranslates=snapTranslates, snapRotates=snapRotates, snapScales=snapScales)


# def timeLineRangeSet(time):
#    '''
#    Return the current PlaybackTimeline OR if a range is selected in the
#    TimeLine, (Highlighted in Red) return that instead.
#    '''
#    PlayBackSlider = mel.eval('$tmpVar=$gPlayBackSlider')
#    time=cmds.timeControl(PlayBackSlider ,e=True, rangeArray=True, v=time)


# ----------------------------------------------------------------------------
# MAIN CALLS ----
# ----------------------------------------------------------------------------

class AnimationLayerContext(object):
    """
    Context Manager for merging animLayers down and restoring
    the data as is afterwards
    """
    def __init__(self, srcNodes, mergeLayers=True, restoreOnExit=True):
        self.srcNodes = srcNodes  # nodes to check for animLayer membership / process
        self.mergeLayers = mergeLayers  # mute the behaviour of this context
        self.restoreOnExit = restoreOnExit  # restore the original layers after processing
        self.keymode = None
        self.deleteBaked = True
        if self.restoreOnExit:
            self.deleteBaked = False
        self.animLayers = []
        self.layerCache = {}
        # log.debug('Context Manager : mergeLayers : %s, restoreOnExit : %s' % (self.mergeLayers, self.restoreOnExit))

    def __enter__(self):
        self.animLayers = getAnimLayersFromGivenNodes(self.srcNodes)

        # set to "Hybrid" just in case as we need the exposure of all keys for most functions
        self.keymode = cmds.optionVar(q='animLayerSelectionKey')
        cmds.optionVar(iv=('animLayerSelectionKey', 1))

        if self.animLayers:
            if self.mergeLayers:
                try:
                    for layer in self.animLayers:
                        self.layerCache[layer] = {'mute': cmds.animLayer(layer, q=True, mute=True),
                                                  'locked': cmds.animLayer(layer, q=True, lock=True)}
                        # force unlock all layers before the merge  : 25/09/19 bug on restoration with baseLayer locked
                        cmds.animLayer(layer, edit=True, lock=False)

                    mergeAnimLayers(self.srcNodes, deleteBaked=self.deleteBaked)

                    if self.restoreOnExit:
#                         # return the original mute and lock states and select the new
#                         # mergedLayer ready for the rest of the copy code to deal with
#                         for layer, cache in self.layerCache.items():
#                             for layer, cache in self.layerCache.items():
#                                 cmds.animLayer(layer, edit=True, mute=cache['mute'])
#                                 cmds.animLayer(layer, edit=True, lock=cache['locked'])
                        mel.eval("source buildSetAnimLayerMenu")
                        mel.eval('selectLayer("Merged_Layer")')
                except:
                    log.debug('CopyKeys internal : AnimLayer Merge Failed')
            else:
                log.warning('SrcNodes have animLayers, results may be erratic unless Baked!')

    def __exit__(self, exc_type, exc_value, traceback):
        cmds.optionVar(iv=('animLayerSelectionKey', self.keymode))
        if self.mergeLayers and self.restoreOnExit:
            if self.animLayers and cmds.animLayer('Merged_Layer', query=True, exists=True):
                cmds.delete('Merged_Layer')

            # return the original mute and lock states and select the new
            # mergedLayer ready for the rest of the copy code to deal with
            for layer, cache in self.layerCache.items():
                for layer, cache in self.layerCache.items():
                    cmds.animLayer(layer, edit=True, mute=cache['mute'])
                    cmds.animLayer(layer, edit=True, lock=cache['locked'])
        if exc_type:
            log.exception('%s : %s' % (exc_type, exc_value))

        # if this was false, it would re-raise the exception when complete
        return True


class AnimationUI(object):

    def __init__(self, dockUI=True):

        # WARNING HACK ALERT!
        # ====================
        # ensue we add the red9 icons path. This is set during the boot sequence BUT because
        # workspaces come up BEFORE we get access to the boot sequence we end up with an
        # AnimUI with no icons. This fixes that
        r9Setup.addIconsPath()
        # END ================

        self.buttonBgc = r9Setup.red9ButtonBGC(1)
        self.win = 'Red9AnimToolsWin'
        self.initial_winsize = (355, 790)
        self.initial_workspace_width = 355
        self.dockCnt = 'Red9AnimToolsDoc'
        self.workspaceCnt = 'Red9AnimToolsWorkspace'
        self.label = LANGUAGE_MAP._AnimationUI_.title
        self.internalConfigPath = False
        self.dock = dockUI
        self.uiBoot = True

        # take generic filterSettings Object
        self.filterSettings = r9Core.FilterNode_Settings()
        self.filterSettings.transformClamp = True
        self.presetDir = r9Setup.red9Presets()  # os.path.join(r9Setup.red9ModulePath(), 'presets')
        self.basePreset = 'Default.cfg'  # this is only ever run once, after which the data is pushed to the settings file

        # Pose Management variables
        self.posePath = None  # working variable
        self.posePathLocal = ''  # 'Local Pose Path not yet set'
        self.posePathProject = ''  # 'Project Pose Path not yet set'
        self.posePathMode = 'localPoseMode'  # or 'project' : mode of the PosePath field and UI
        self.poseSelected = None
        self.poseGridMode = 'thumb'  # or text
        self.poseRootMode = 'RootNode'  # or MetaRig
        self.poses = None
        self.poseButtonBGC = [0.27, 0.3, 0.3]
        self.poseButtonHighLight = r9Setup.red9ButtonBGC('green')
        self.poseProjectMute = False  # whether to disable the save and update funcs in Project mode

        # Default Red9 poseHandlers now bound here if found, used to extend Clients handling of data
        self.poseHandlerPaths = [os.path.join(self.presetDir, 'posehandlers')]

        # bind the ui element names to the class
        self.__uiElementBinding()

        # Internal config file setup for the UI state
        if self.internalConfigPath:
            self.ui_optVarConfig = os.path.join(self.presetDir, '__red9config__')
        else:
            self.ui_optVarConfig = os.path.join(r9Setup.mayaPrefs(), '__red9config__')
#         if not os.path.exists(self.ui_optVarConfig):

        self.ANIM_UI_OPTVARS = dict()
        self.ANIM_UI_OPTVARS['AnimationUI'] = {}
        self.__uiCache_readUIElements()

        # deal with screen resolution and scaling
        scaling_dpi = r9Setup.maya_screen_mapping()[3]
        if not scaling_dpi == 96.0:  # 100% which is what the UIs were setup under (1080p)
            factor = r9Setup.maya_dpi_scaling_factor()
            self.initial_workspace_width = self.initial_workspace_width * factor
            self.initial_winsize = [self.initial_winsize[0] * factor, self.initial_winsize[1] * factor]

    @classmethod
    def show(cls):
        '''
        main UI call. manages 2017 workspaces here..
        '''
        global RED_ANIMATION_UI
        global RED_ANIMATION_UI_OPENCALLBACKS

        animUI = cls()
        animUI.uiBoot = True
        animUI.close()  # close any previous instances
        RED_ANIMATION_UI = animUI

        if 'ui_docked' in animUI.ANIM_UI_OPTVARS['AnimationUI']:
            animUI.dock = eval(animUI.ANIM_UI_OPTVARS['AnimationUI']['ui_docked'])
        if r9General.getModifier() == 'Ctrl':
            if not animUI.dock:
                print('Switching dockState : True')
                animUI.dock = True
            else:
                print('Switching dockState : False')
                animUI.dock = False

#         if RED_ANIMATION_UI_OPENCALLBACKS:
#             for func in RED_ANIMATION_UI_OPENCALLBACKS:
#                 if callable(func):
#                     try:
#                         print 'calling RED_ANIMATION_UI_OPENCALLBACKS'
#                         log.debug('calling RED_ANIMATION_UI_OPENCALLBACKS')
#                         func(animUI)
#                     except:
#                         log.warning('RED_ANIMATION_UI_OPENCALLBACKS failed')

        # ========================================================
        # Maya 2017 we switch from dockControl to workspaceControl
        # ========================================================
        if r9Setup.mayaVersion() >= 2017:
            # seriously, delete it so that we force it to refresh and update the global RED_ANIMATION_UI?
            if cmds.workspaceControl(animUI.workspaceCnt, q=True, exists=True):
                cmds.workspaceControl(animUI.workspaceCnt, e=True, close=True)

            # if the workspace exists just show it, else bind the ui to it
            if not cmds.workspaceControl(animUI.workspaceCnt, q=True, exists=True):
                element = mel.eval('getUIComponentDockControl("Channel Box / Layer Editor", false);')  # get the channelBox element control
                windowcall = 'import Red9.core.Red9_AnimationUtils as r9Anim;animUI=r9Anim.AnimationUI();animUI._showUI();'
                cmds.workspaceControl(animUI.workspaceCnt, label="Red9_Animation",
                                      uiScript=windowcall,  # animUI._showUI,
                                      tabToControl=(element, -1),
                                      initialWidth=355,  # animUI.initial_workspace_width,  # this SHOULD work but fails to control minimum correctly
                                      initialHeight=animUI.initial_winsize[1],
                                      minimumWidth=animUI.initial_workspace_width,  # True
                                      widthProperty='fixed',
                                      retain=False,
                                      loadImmediately=False)
            else:
                log.debug('Workspace Red9 already exists, calling open')
            cmds.workspaceControl(animUI.workspaceCnt, e=True, vis=True)
            cmds.workspaceControl(animUI.workspaceCnt, e=True, r=True, rs=True)  # raise it
            if not animUI.dock:
                cmds.workspaceControl(animUI.workspaceCnt, e=True, fl=True)
        else:
            animUI._showUI()
            animUI.ANIM_UI_OPTVARS['AnimationUI']['ui_docked'] = animUI.dock
            animUI.__uiCache_storeUIElements()

        # load the anim ui callbacks after the load sequence seeing as we can't
        # pass in the animUI class directly to the workspace control

        # RED_ANIMATION_UI is a global so we can pick the animUI class backup after the workspace call!!
        if RED_ANIMATION_UI_OPENCALLBACKS:
            for func in RED_ANIMATION_UI_OPENCALLBACKS:
                if r9General.is_callable(func):
                    try:
                        print('calling RED_ANIMATION_UI_OPENCALLBACKS')
                        log.debug('calling RED_ANIMATION_UI_OPENCALLBACKS')
                        func(RED_ANIMATION_UI)
                    except:
                        log.warning('RED_ANIMATION_UI_OPENCALLBACKS failed')
            RED_ANIMATION_UI.__uiCache_loadUIElements()

        animUI.uiBoot = False

    def __uicloseEvent(self, *args):
        # print 'AnimUI close event called'
        self.__uiCache_storeUIElements()
        RED_ANIMATION_UI = None
        del(self)

    def __uiElementBinding(self):
        '''
        this is GASH! rather than have each ui element cast itself to the object as we used to do,
        we're now manually setting up those name maps to by-pass the way we have to call the UI in
        2017 via the workspace.... Maybe I'm missing something in the workspace setup but don't think so.
        Must see if there's a way of binding to the class object as you'd expect :(
        '''
        self.uitabMain = 'uitabMain'
        self.uiformMain = 'uiformMain'

        # CopyAttributes
        # ====================
        self.uicbCAttrHierarchy = 'uicbCAttrHierarchy'
        self.uicbCAttrToMany = 'uicbCAttrToMany'
        self.uicbCAttrChnAttrs = 'uicbCAttrChnAttrs'

        # CopyKeys
        # ====================
        self.uicbCKeyHierarchy = 'uicbCKeyHierarchy'
        self.uicbCKeyToMany = 'uicbCKeyToMany'
        self.uicbCKeyChnAttrs = 'uicbCKeyChnAttrs'
        self.uicbCKeyRange = 'uicbCKeyRange'
        self.uicbCKeyAnimLay = 'uicbCKeyAnimLay'
        self.uiffgCKeyStep = 'uiffgCKeyStep'

        # SnapTransforms
        # ====================
        self.uicbSnapRange = 'uicbSnapRange'
        self.uicbSnapTrans = 'uicbSnapTrans'
        self.uicbSnapPreCopyKeys = 'uicbSnapPreCopyKeys'
        self.uiifgSnapStep = 'uiifgSnapStep'
        self.uicbSnapHierarchy = 'uicbSnapHierarchy'
        self.uicbStapRots = 'uicbStapRots'
        self.uicbSnapPreCopyAttrs = 'uicbSnapPreCopyAttrs'
        self.uiifSnapIterations = 'uiifSnapIterations'

        # Stabilizer
        # ====================
        self.uicbStabRange = 'uicbStabRange'
        self.uicbStabTrans = 'uicbStabTrans'
        self.uicbStabRots = 'uicbStabRots'
        self.uiffgStabStep = 'uiffgStabStep'

        # TimeOffset
        # ====================
        self.uicbTimeOffsetHierarchy = 'uicbTimeOffsetHierarchy'
        self.uicbTimeOffsetScene = 'uicbTimeOffsetScene'
        self.uicbTimeOffsetPlayback = 'uicbTimeOffsetPlayback'
        self.uicbTimeOffsetRange = 'uicbTimeOffsetRange'
        self.uicbTimeOffsetFlocking = 'uicbTimeOffsetFlocking'
        self.uicbTimeOffsetRandom = 'uicbTimeOffsetRandom'
        self.uicbTimeOffsetRipple = 'uicbTimeOffsetRipple'
        self.uicbTimeOffsetStartfrm = 'uicbTimeOffsetStartfrm'
        self.uiffgTimeOffset = 'uiffgTimeOffset'
        self.uibtnTimeOffset = 'uibtnTimeOffset'

        self.uicbMirrorHierarchy = 'uicbMirrorHierarchy'

        # Hierarchy Controls
        # =====================
        self.uiclHierarchyFilters = 'uiclHierarchyFilters'
        self.uicbMetaRig = 'uicbMetaRig'
        self.uitfgSpecificNodeTypes = 'uitfgSpecificNodeTypes'
        self.uitfgSpecificAttrs = 'uitfgSpecificAttrs'
        self.uitfgSpecificPattern = 'uitfgSpecificPattern'
        self.uitslFilterPriority = 'uitslFilterPriority'
        self.uicbSnapPriorityOnly = 'uicbSnapPriorityOnly'
        self.uitslPresets = 'uitslPresets'
        self.uicbIncRoots = 'uicbIncRoots'

        # Pose Saver Tab
        # ===============
        self.uitfgPosePath = 'uitfgPosePath'
        self.uircbPosePathMethod = 'posePathMode'
        self.posePopupGrid = 'posePopupGrid'

        # SubFolder Scroller
        # =====================
        self.uitslPoseSubFolders = 'uitslPoseSubFolders'

        # Main PoseFields
        # =====================
        self.tfPoseSearchFilter = 'tfPoseSearchFilter'
        self.uitslPoses = 'uitslPoses'
        self.uiglPoseScroll = 'uiglPoseScroll'
        self.uiglPoses = 'uiglPoses'
        self.uicbPoseHierarchy = 'uicbPoseHierarchy'
        self.uitfgPoseRootNode = 'uitfgPoseRootNode'
        self.uitfgPoseMRootGrab = 'uitfgPoseMRootGrab'
        self.uicbPoseRelative = 'uicbPoseRelative'
        self.uicbPoseSpace = 'uicbPoseSpace'
        self.uiflPoseRelativeFrame = 'PoseRelativeFrame'
        self.uircbPoseRotMethod = 'relativeRotate'
        self.uircbPoseTranMethod = 'relativeTranslate'

    def close(self):
        if r9Setup.mayaVersion() >= 2017:
            if cmds.workspaceControl(self.workspaceCnt, q=True, exists=True):
                cmds.workspaceControl(self.workspaceCnt, e=True, close=True)
        else:
            # 2017 introduces workspaces and we use those instead of dockControls
            try:
                # Maya2011 dockControl introduced
                if cmds.dockControl(self.dockCnt, exists=True):
                    cmds.deleteUI(self.dockCnt, control=True)
            except:
                self.dock = False
        if cmds.window(self.win, exists=True):
            cmds.deleteUI(self.win, window=True)

    def _showUI(self, *args):
        '''
        PRIVATE FUNCTION, DO NOT CALL FROM CODE
        '''
        # Ensure this is recast, we've had issues with workspace control management!!
        global RED_ANIMATION_UI
        RED_ANIMATION_UI = self

        if not r9Setup.mayaVersion() >= 2017:
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

        self.MainLayout = cmds.scrollLayout('red9MainScroller', rc=self.__uiCB_resizeMainScroller, cr=True)
        self.form = cmds.formLayout(self.uiformMain, nd=100, parent=self.MainLayout)
        self.tabs = cmds.tabLayout(self.uitabMain, innerMarginWidth=5, innerMarginHeight=5)

        cmds.formLayout(self.form, edit=True, attachForm=((self.tabs, 'top', 0),
                                                          (self.tabs, 'left', 0),
                                                          (self.tabs, 'bottom', 0),
                                                          (self.tabs, 'right', 0)))

        # TAB1: ####################################################################

        self.AnimLayout = cmds.columnLayout(adjustableColumn=True)
        cmds.separator(h=5, style='none')

        # ====================
        # CopyAttributes
        # ====================
        cmds.frameLayout(label=LANGUAGE_MAP._AnimationUI_.copy_attrs, cll=True)  # , borderStyle='etchedOut')
        cmds.columnLayout(adjustableColumn=True)
        cmds.button(label=LANGUAGE_MAP._AnimationUI_.copy_attrs, bgc=self.buttonBgc,
                    ann=LANGUAGE_MAP._AnimationUI_.copy_attrs_ann,
                    command=partial(self.__uiCall, 'CopyAttrs'))

        cmds.separator(h=5, style='none')
        cmds.rowColumnLayout(numberOfColumns=3, columnWidth=[(1, 100), (2, 100), (3, 100)], columnSpacing=[(1, 10), (2, 10)])
        cmds.checkBox(self.uicbCAttrHierarchy, l=LANGUAGE_MAP._Generic_.hierarchy, al='left', v=False,
                                                ann=LANGUAGE_MAP._AnimationUI_.copy_attrs_hierarchy_ann,
                                                cc=lambda x: self.__uiCache_addCheckbox(self.uicbCAttrHierarchy))
        cmds.checkBox(self.uicbCAttrToMany, l=LANGUAGE_MAP._AnimationUI_.copy_to_many, al='left', v=False,
                                                ann=LANGUAGE_MAP._AnimationUI_.copy_attrs_to_many_ann)
        cmds.checkBox(self.uicbCAttrChnAttrs, ann=LANGUAGE_MAP._AnimationUI_.cbox_attrs_ann,
                                            l=LANGUAGE_MAP._AnimationUI_.cbox_attrs, al='left', v=False)
        cmds.setParent(self.AnimLayout)

        # ====================
        # CopyKeys
        # ====================
        cmds.separator(h=10, st='in')
        cmds.frameLayout(label=LANGUAGE_MAP._AnimationUI_.copy_keys, cll=True)  # , borderStyle='etchedOut')
        cmds.columnLayout(adjustableColumn=True)
        cmds.button(label=LANGUAGE_MAP._AnimationUI_.copy_keys, bgc=self.buttonBgc,
                    ann=LANGUAGE_MAP._AnimationUI_.copy_keys_ann,
                    command=partial(self.__uiCall, 'CopyKeys'))

        cmds.separator(h=5, style='none')
        cmds.rowColumnLayout(numberOfColumns=3, columnWidth=[(1, 100), (2, 100), (3, 100)], columnSpacing=[(1, 10), (2, 10)], rowSpacing=[(1, 5)])
        # cmds.rowColumnLayout(numberOfColumns=4, columnWidth=[(1, 75), (2, 80), (3, 80), (3, 80)], columnSpacing=[(1, 10), (2, 10)], rowSpacing=[(1,5)])

        cmds.checkBox(self.uicbCKeyHierarchy, l=LANGUAGE_MAP._Generic_.hierarchy, al='left', v=False,
                                            ann=LANGUAGE_MAP._AnimationUI_.copy_keys_hierarchy_ann,
                                            cc=lambda x: self.__uiCache_addCheckbox(self.uicbCKeyHierarchy))
        cmds.checkBox(self.uicbCKeyToMany, l=LANGUAGE_MAP._AnimationUI_.copy_to_many, al='left', v=False,
                                            ann=LANGUAGE_MAP._AnimationUI_.copy_keys_to_many_ann)
        cmds.checkBox(self.uicbCKeyChnAttrs, ann=LANGUAGE_MAP._AnimationUI_.cbox_attrs_ann,
                                            l=LANGUAGE_MAP._AnimationUI_.cbox_attrs, al='left', v=False)
        cmds.checkBox(self.uicbCKeyRange, l=LANGUAGE_MAP._AnimationUI_.timerange, al='left', v=False,
                                            ann=LANGUAGE_MAP._AnimationUI_.copy_keys_timerange_ann,
                                            cc=lambda x: self.__uiCache_addCheckbox(self.uicbCKeyRange))
        cmds.checkBox(self.uicbCKeyAnimLay, l=LANGUAGE_MAP._AnimationUI_.copy_keys_merge_layers, al='left', v=False,
                                            ann=LANGUAGE_MAP._AnimationUI_.copy_keys_merge_layers_ann,
                                            cc=lambda x: self.__uiCache_addCheckbox(self.uicbCKeyAnimLay))

        cmds.setParent('..')
        cmds.separator(h=10, style='in')
        cmds.rowColumnLayout(numberOfColumns=3, columnWidth=[(1, 100), (2, 100), (3, 100)], columnSpacing=[(1, 10), (2, 10)], rowSpacing=[(1, 5)])
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
        cmds.floatFieldGrp(self.uiffgCKeyStep, l=LANGUAGE_MAP._AnimationUI_.offset, value1=0, cw2=(40, 50))
        cmds.setParent(self.AnimLayout)

        # ====================
        # SnapTransforms
        # ====================
        cmds.separator(h=10, st='in')
        cmds.frameLayout(label=LANGUAGE_MAP._AnimationUI_.snaptransforms, cll=True)  # , borderStyle='etchedOut')
        cmds.columnLayout(adjustableColumn=True)
        cmds.button(label=LANGUAGE_MAP._AnimationUI_.snaptransforms, bgc=self.buttonBgc,
                     ann=LANGUAGE_MAP._AnimationUI_.snaptransforms_ann,
                     command=partial(self.__uiCall, 'Snap'))
        cmds.separator(h=5, style='none')

        # cmds.rowColumnLayout(numberOfColumns=3, columnWidth=[(1, 100), (2, 100), (3, 100)], columnSpacing=[(1, 10), (2, 10)], rowSpacing=[(1,2)])
        cmds.rowColumnLayout(numberOfColumns=4, columnWidth=[(1, 75), (2, 50), (3, 90), (4, 85)],
                             columnSpacing=[(1, 8), (2, 8), (3, 8)], rowSpacing=[(1, 2)])

        cmds.checkBox(self.uicbSnapRange, l=LANGUAGE_MAP._AnimationUI_.timerange, al='left', v=False,
                                            ann=LANGUAGE_MAP._AnimationUI_.snaptransforms_timerange_ann,
                                            cc=self.__uiCB_manageSnapTime)
        cmds.checkBox(self.uicbSnapTrans, l=LANGUAGE_MAP._AnimationUI_.trans, al='left', v=True,
                                           ann=LANGUAGE_MAP._AnimationUI_.trans_ann,
                                           cc=lambda x: self.__uiCache_addCheckbox(self.uicbSnapTrans))
        cmds.checkBox(self.uicbSnapPreCopyKeys, l=LANGUAGE_MAP._AnimationUI_.pre_copykeys, al='left',
                                                 ann=LANGUAGE_MAP._AnimationUI_.pre_copykeys_ann,
                                                 en=False, v=True)
        cmds.intFieldGrp(self.uiifgSnapStep, l=LANGUAGE_MAP._AnimationUI_.frmstep, en=False, value1=1, cw2=(45, 30),
                                              ann=LANGUAGE_MAP._AnimationUI_.frmstep_ann)

        cmds.checkBox(self.uicbSnapHierarchy, l=LANGUAGE_MAP._Generic_.hierarchy, al='left', v=False,
                                               ann=LANGUAGE_MAP._AnimationUI_.snaptransforms_hierarchy_ann,
                                               cc=self.__uiCB_manageSnapHierachy)
        cmds.checkBox(self.uicbStapRots, l=LANGUAGE_MAP._AnimationUI_.rots, al='left', v=True,
                                          ann='Track the Rotational data',
                                          cc=lambda x: self.__uiCache_addCheckbox(self.uicbStapRots))
        cmds.checkBox(self.uicbSnapPreCopyAttrs, l=LANGUAGE_MAP._AnimationUI_.pre_copyattrs, al='left', en=False, v=True,
                                                  ann=LANGUAGE_MAP._AnimationUI_.pre_copyattrs_ann)
        cmds.intFieldGrp(self.uiifSnapIterations, l=LANGUAGE_MAP._AnimationUI_.iteration, en=False, value1=1, cw2=(45, 30),
                                           ann=LANGUAGE_MAP._AnimationUI_.iteration_ann)

        cmds.setParent(self.AnimLayout)

        # ====================
        # Stabilizer
        # ====================
        cmds.separator(h=10, st='in')
        cmds.frameLayout(label=LANGUAGE_MAP._AnimationUI_.tracknstabilize, cll=True)  # , borderStyle='etchedOut')
        cmds.columnLayout(adjustableColumn=True)
        # cmds.rowColumnLayout(numberOfColumns=3, columnWidth=[(1, 100), (2, 100), (3, 100)], columnSpacing=[(1, 10), (2, 10), (3, 5)])
        cmds.rowColumnLayout(numberOfColumns=4, columnWidth=[(1, 100), (2, 55), (3, 55), (4, 100)], columnSpacing=[(1, 10), (3, 5)])
        cmds.checkBox(self.uicbStabRange, l=LANGUAGE_MAP._AnimationUI_.timerange, al='left', v=False,
                                            ann=LANGUAGE_MAP._AnimationUI_.snaptransforms_timerange_ann,
                                            cc=lambda x: self.__uiCache_addCheckbox(self.uicbStabRange))
        cmds.checkBox(self.uicbStabTrans, l=LANGUAGE_MAP._AnimationUI_.trans, al='left', v=True,
                                           ann=LANGUAGE_MAP._AnimationUI_.trans_ann,
                                           cc=lambda x: self.__uiCache_addCheckbox(self.uicbStabTrans))
        cmds.checkBox(self.uicbStabRots, l=LANGUAGE_MAP._AnimationUI_.rots, al='left', v=True,
                                          ann=LANGUAGE_MAP._AnimationUI_.rots_ann,
                                          cc=lambda x: self.__uiCache_addCheckbox(self.uicbStabRots))
        cmds.floatFieldGrp(self.uiffgStabStep, l=LANGUAGE_MAP._AnimationUI_.step, value1=1, cw2=(40, 50),
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

        # ====================
        # TimeOffset
        # ====================
        cmds.separator(h=10, st='in')
        cmds.frameLayout(label=LANGUAGE_MAP._AnimationUI_.timeoffset, cll=True)  # , borderStyle='etchedOut')
        cmds.columnLayout(adjustableColumn=True)
        # cmds.rowColumnLayout(numberOfColumns=4, columnWidth=[(1, 100), (2, 55), (3, 55), (4, 100)], columnSpacing=[(1, 10), (3, 5)])
        cmds.rowColumnLayout(numberOfColumns=3, columnWidth=[(1, 100), (2, 100), (3, 100)], columnSpacing=[(1, 10), (2, 10), (3, 5)], rowSpacing=[(1, 5), (2, 5)])
        cmds.checkBox(self.uicbTimeOffsetHierarchy,
                                            l=LANGUAGE_MAP._Generic_.hierarchy, al='left', en=True, v=False,
                                            ann=LANGUAGE_MAP._AnimationUI_.offset_hierarchy_ann,
                                            ofc=partial(self.__uiCB_manageTimeOffsetChecks, ''),
                                            onc=partial(self.__uiCB_manageTimeOffsetChecks, 'Hier'))
                                            # cc=lambda x: self.__uiCache_addCheckbox(self.uicbTimeOffsetHierarchy))
        cmds.checkBox(self.uicbTimeOffsetScene,
                                            l=LANGUAGE_MAP._AnimationUI_.offset_fullscene,
                                            ann=LANGUAGE_MAP._AnimationUI_.offset_fullscene_ann,
                                            al='left', v=False,
                                            ofc=partial(self.__uiCB_manageTimeOffsetChecks, ''),
                                            onc=partial(self.__uiCB_manageTimeOffsetChecks, 'Full'))
                                            # cc=lambda x: self.__uiCache_addCheckbox(self.uicbTimeOffsetScene))

        cmds.checkBox(self.uicbTimeOffsetPlayback, l=LANGUAGE_MAP._AnimationUI_.offset_timelines,
                                            ann=LANGUAGE_MAP._AnimationUI_.offset_timelines_ann,
                                            al='left', v=False, en=False,
                                            cc=lambda x: self.__uiCache_addCheckbox(self.uicbTimeOffsetPlayback))
        cmds.checkBox(self.uicbTimeOffsetRange,
                                            l=LANGUAGE_MAP._AnimationUI_.timerange, al='left', en=True, v=False,
                                            ann=LANGUAGE_MAP._AnimationUI_.offset_timerange_ann,
                                            cc=partial(self.__uiCB_manageTimeOffsetChecks, 'Timerange'))
        cmds.checkBox(self.uicbTimeOffsetFlocking,
                                            l=LANGUAGE_MAP._AnimationUI_.offset_flocking, al='left', en=True, v=False,
                                            ann=LANGUAGE_MAP._AnimationUI_.offset_flocking_ann,
                                            cc=lambda x: self.__uiCache_addCheckbox(self.uicbTimeOffsetFlocking))
        cmds.checkBox(self.uicbTimeOffsetRandom, l=LANGUAGE_MAP._AnimationUI_.offset_randomizer,
                                            ann=LANGUAGE_MAP._AnimationUI_.offset_randomizer_ann,
                                            al='left', v=False,
                                            cc=lambda x: self.__uiCache_addCheckbox(self.uicbTimeOffsetRandom))
        cmds.checkBox(self.uicbTimeOffsetRipple, l=LANGUAGE_MAP._AnimationUI_.offset_ripple,
                                            ann=LANGUAGE_MAP._AnimationUI_.offset_ripple_ann,
                                            al='left', v=False, en=False,
                                            cc=lambda x: self.__uiCache_addCheckbox(self.uicbTimeOffsetRipple))
        cmds.checkBox(self.uicbTimeOffsetStartfrm, l=LANGUAGE_MAP._AnimationUI_.offset_startfrm,
                                            ann=LANGUAGE_MAP._AnimationUI_.offset_startfrm_ann,
                                            al='left', v=False, en=False,
                                            ofc=partial(self.__uiCB_manageTimeOffsetChecks),
                                            onc=partial(self.__uiCB_manageTimeOffsetChecks),
                                            cc=lambda x: self.__uiCache_addCheckbox(self.uicbTimeOffsetStartfrm))

        cmds.separator(style='none')
        cmds.setParent('..')
        cmds.separator(h=2, style='none')

        cmds.rowColumnLayout(numberOfColumns=3, columnWidth=[(1, 250), (2, 60)], columnSpacing=[(2, 5)])
        cmds.button(self.uibtnTimeOffset, label=LANGUAGE_MAP._AnimationUI_.offsetby, bgc=self.buttonBgc,
                     ann=LANGUAGE_MAP._AnimationUI_.offset_ann,
                     command=partial(self.__uiCall, 'TimeOffset'))
        cmds.floatFieldGrp(self.uiffgTimeOffset, value1=1, ann=LANGUAGE_MAP._AnimationUI_.offset_frms_ann)
        cmds.setParent(self.AnimLayout)

        # ===================
        # Mirror Controls
        # ====================
        cmds.separator(h=10, st='in')
        cmds.frameLayout(label=LANGUAGE_MAP._AnimationUI_.mirror_controls, cll=True)  # , borderStyle='etchedOut')
        cmds.columnLayout(adjustableColumn=True)
        cmds.separator(h=3, st='none')
        cmds.rowColumnLayout(numberOfColumns=3, columnWidth=[(1, 100), (2, 100), (3, 100)], columnSpacing=[(1, 10), (2, 10), (3, 5)])
        cmds.checkBox(self.uicbMirrorHierarchy,
                                            l=LANGUAGE_MAP._Generic_.hierarchy, al='left', en=True, v=False,
                                            ann=LANGUAGE_MAP._AnimationUI_.mirror_hierarchy_ann,
                                            cc=lambda x: self.__uiCache_addCheckbox(self.uicbMirrorHierarchy))

        #cmds.rowColumnLayout(numberOfColumns=2, columnWidth=[(1, 160), (2, 160)], columnSpacing=[(2, 2)])
        cmds.button(label=LANGUAGE_MAP._AnimationUI_.mirror_animation, bgc=self.buttonBgc,
                     ann=LANGUAGE_MAP._AnimationUI_.mirror_animation_ann,
                     command=partial(self.__uiCall, 'MirrorAnim'))
        cmds.button(label=LANGUAGE_MAP._AnimationUI_.mirror_pose, bgc=self.buttonBgc,
                     ann=LANGUAGE_MAP._AnimationUI_.mirror_pose_ann,
                     command=partial(self.__uiCall, 'MirrorPose'))
        cmds.setParent('..')
        cmds.separator(h=10, st='in')

        cmds.rowColumnLayout(numberOfColumns=3, columnWidth=[(1, 100), (2, 100), (3, 100)], columnSpacing=[(1, 10), (2, 10), (3, 5)])
        #cmds.rowColumnLayout(numberOfColumns=3, columnWidth=[(1,160), (2, 80), (3, 80)], columnSpacing=[(3, 2)])
        cmds.text(l='Symmetry Anim : ')
        cmds.button(label='Anim : R >', bgc=self.buttonBgc,
                     ann=LANGUAGE_MAP._AnimationUI_.symmetry_animation_ann + ' : push Right to Left',
                     command=partial(self.__uiCall, 'SymmetryAnim_RL'))
        cmds.button(label='Anim : < L', bgc=self.buttonBgc,
                     ann=LANGUAGE_MAP._AnimationUI_.symmetry_animation_ann + ' : push Left to Right',
                     command=partial(self.__uiCall, 'SymmetryAnim_LR'))
        cmds.separator(h=3, st='in')
        cmds.separator(h=3, st='in')
        cmds.separator(h=3, st='in')
        cmds.text(l='Symmetry Pose : ')
        cmds.button(label='Pose : R >', bgc=self.buttonBgc,
                     ann=LANGUAGE_MAP._AnimationUI_.symmetry_pose_ann + ' : push Right to Left',
                     command=partial(self.__uiCall, 'SymmetryPose_RL'))
        cmds.button(label='Pose : < L', bgc=self.buttonBgc,
                     ann=LANGUAGE_MAP._AnimationUI_.symmetry_pose_ann + ' : push Left to Right',
                     command=partial(self.__uiCall, 'SymmetryPose_LR'))
        cmds.setParent('..')
        cmds.separator(h=10, st='in')
        cmds.text(l='Note: Symmetry is aimed at simple Z+ facing game loops\nor facial data, not complex full body data')
        cmds.setParent(self.AnimLayout)
        cmds.setParent(self.tabs)

        # TAB2: ####################################################################

        # =====================================================================
        # Hierarchy Controls Main filterSettings Object
        # =====================================================================

        self.FilterLayout = cmds.columnLayout(adjustableColumn=True)

        cmds.separator(h=15, style='none')
        cmds.text(LANGUAGE_MAP._AnimationUI_.hierarchy_descriptor)
        cmds.separator(h=20, style='in')

        # This bit is bullshit! the checkBox align flag is now obsolete so the label is always on the left regardless :(
        cmds.columnLayout(self.uiclHierarchyFilters, adjustableColumn=True, enable=True)
        cmds.rowColumnLayout(numberOfColumns=2, columnWidth=[(1, 120), (2, 200)], columnSpacing=[2, 3])
        cmds.text(label=LANGUAGE_MAP._AnimationUI_.metarig, align='right')
        cmds.checkBox(self.uicbMetaRig, ann=LANGUAGE_MAP._AnimationUI_.metarig_ann,
                                        l='',
                                        v=True,
                                        cc=lambda x: self.__uiCB_managePoseRootMethod(self.uicbMetaRig))
        cmds.setParent(self.uiclHierarchyFilters)

        cmds.textFieldGrp(self.uitfgSpecificNodeTypes, label=LANGUAGE_MAP._AnimationUI_.search_nodetypes,
                          text="", cw2=(120, 200), ann=LANGUAGE_MAP._AnimationUI_.search_nodetypes_ann)
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
        cmds.textFieldGrp(self.uitfgSpecificAttrs, label=LANGUAGE_MAP._AnimationUI_.search_attributes,
                          text="", cw2=(120, 200), ann=LANGUAGE_MAP._AnimationUI_.search_attributes_ann)
        cmds.textFieldGrp(self.uitfgSpecificPattern,
                                    label=LANGUAGE_MAP._AnimationUI_.search_pattern, text="", cw2=(120, 200),
                                    ann=LANGUAGE_MAP._AnimationUI_.search_pattern_ann)
        cmds.separator(h=5, style='none')
        cmds.text('Internal Node Priorities:')
        cmds.textScrollList(self.uitslFilterPriority, numberOfRows=8, allowMultiSelection=False,
                                               height=60, enable=True, append=self.filterSettings.filterPriority)
        cmds.popupMenu()
        cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.priorities_clear, command=lambda x: self.__uiSetPriorities('clear'))
        cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.priorities_set, command=lambda x: self.__uiSetPriorities('set'))
        cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.priorities_append, command=lambda x: self.__uiSetPriorities('append'))
        cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.priorities_remove, command=lambda x: self.__uiSetPriorities('remove'))
        cmds.menuItem(divider=True)
        cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.move_up, command=lambda x: self.__uiSetPriorities('moveUp'))
        cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.move_down, command=lambda x: self.__uiSetPriorities('moveDown'))
        cmds.checkBox(self.uicbSnapPriorityOnly, v=False,
                                                label=LANGUAGE_MAP._AnimationUI_.priorities_use_snap,
                                                onc=self.__uiCB_setPriorityFlag,
                                                cc=lambda x: self.__uiCache_addCheckbox('uicbSnapPriorityOnly'))
        cmds.separator(h=20, style='in')
        cmds.text(LANGUAGE_MAP._AnimationUI_.presets_available)
        cmds.textScrollList(self.uitslPresets, numberOfRows=8, allowMultiSelection=False,
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
        cmds.checkBox(self.uicbIncRoots, ann='include RootNodes in the Filter',
                                        l=LANGUAGE_MAP._AnimationUI_.include_roots,
                                        al='left', v=True,
                                        cc=self.__uiCache_storeUIElements)

        cmds.optionMenu('om_MatchMethod', label=LANGUAGE_MAP._AnimationUI_.match_method, w=70,
                        ann=LANGUAGE_MAP._AnimationUI_.match_method_ann,
                        cc=self.__uiCB_setMatchMethod)
        # for preset in ["base","stripPrefix","index"]:
        cmds.menuItem(l=LANGUAGE_MAP._AnimationUI_.match_base, ann=LANGUAGE_MAP._AnimationUI_.match_base_ann)
        cmds.menuItem(l=LANGUAGE_MAP._AnimationUI_.match_stripprefix, ann=LANGUAGE_MAP._AnimationUI_.match_stripprefix_ann)
        cmds.menuItem(l=LANGUAGE_MAP._AnimationUI_.match_index, ann=LANGUAGE_MAP._AnimationUI_.match_index_ann)
        cmds.menuItem(l=LANGUAGE_MAP._AnimationUI_.match_mirror, ann=LANGUAGE_MAP._AnimationUI_.match_mirror_ann)
        cmds.menuItem(l=LANGUAGE_MAP._AnimationUI_.match_metadata, ann=LANGUAGE_MAP._AnimationUI_.match_metadata_ann)
        cmds.menuItem(l=LANGUAGE_MAP._AnimationUI_.match_stripsuffix, ann=LANGUAGE_MAP._AnimationUI_.match_stripsuffix_ann)
        cmds.menuItem(l='commonPrefix', ann=LANGUAGE_MAP._AnimationUI_.match_stripprefix_ann)  # added 21/06/22
        cmds.menuItem(l='commonSuffix', ann=LANGUAGE_MAP._AnimationUI_.match_stripsuffix_ann)  # added 21/06/22
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

        # TAB3: ####################################################################

        # =====================================================================
        # Pose Saver Tab
        # =====================================================================

        self.poseUILayout = cmds.columnLayout(adjustableColumn=True)
        cmds.separator(h=10, style='none')
        cmds.textFieldButtonGrp(self.uitfgPosePath,
                                ann=LANGUAGE_MAP._AnimationUI_.pose_path,
                                text="",
                                bl=LANGUAGE_MAP._AnimationUI_.pose_path,
                                bc=lambda *x: self.__uiCB_setPosePath(fileDialog=True),
                                cc=lambda *x: self.__uiCB_setPosePath(path=None, fileDialog=False),
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
        cmds.rowColumnLayout(nc=3, columnWidth=[(1, 260), (2, 22), (3, 22)], columnSpacing=[(2, 20)])
        if r9Setup.mayaVersion() > 2012:  # tcc flag not supported in earlier versions
            self.searchFilter = cmds.textFieldGrp(self.tfPoseSearchFilter, label=LANGUAGE_MAP._AnimationUI_.search_filter, text='',
                                                cw=((1, 87), (2, 160)),
                                                ann=LANGUAGE_MAP._AnimationUI_.search_filter_ann,
                                                tcc=lambda x: self.__uiCB_fillPoses(searchFilter=cmds.textFieldGrp(self.tfPoseSearchFilter, q=True, text=True)))
        else:
            self.searchFilter = cmds.textFieldGrp(self.tfPoseSearchFilter, label=LANGUAGE_MAP._AnimationUI_.search_filter, text='',
                                                cw=((1, 87), (2, 160)), fcc=True,
                                                ann=LANGUAGE_MAP._AnimationUI_.search_filter_ann,
                                                cc=lambda x: self.__uiCB_fillPoses(searchFilter=cmds.textFieldGrp(self.tfPoseSearchFilter, q=True, text=True)))

        cmds.iconTextButton('sortByName', style='iconOnly', image1='sortByName.bmp',
                            w=22, h=20, ann=LANGUAGE_MAP._AnimationUI_.sortby_name,
                            c=lambda * args: self.__uiCB_fillPoses(rebuildFileList=True, sortBy='name'))

        cmds.iconTextButton('sortByDate', style='iconOnly', image1='sortByDate.bmp',
                            w=22, h=20, ann=LANGUAGE_MAP._AnimationUI_.sortby_date,
                            c=lambda * args:self.__uiCB_fillPoses(rebuildFileList=True, sortBy='date'))

        cmds.setParent('..')
        cmds.separator(h=10, style='none')

        # SubFolder Scroller
        cmds.textScrollList(self.uitslPoseSubFolders, numberOfRows=8,
                                                       allowMultiSelection=False,
                                                       height=350, vis=False)

        # Main PoseFields
        cmds.textScrollList(self.uitslPoses, numberOfRows=8, allowMultiSelection=False,
                                               # selectCommand=partial(self.__uiPresetSelection), \
                                               height=350, vis=False)
        self.posePopupText = cmds.popupMenu()

        cmds.scrollLayout(self.uiglPoseScroll, parent=self.poseUILayout,
                                                cr=True,
                                                height=350,
                                                hst=16,
                                                vst=16,
                                                vis=False,
                                                rc=self.__uiCB_gridResize)
        cmds.gridLayout(self.uiglPoses, cwh=(100, 100), cr=False, ag=True)
        self.posePopupGrid = cmds.popupMenu('posePopupGrid')

        cmds.setParent(self.poseUILayout)
        # cmds.rowColumnLayout(numberOfColumns=2, columnWidth=[(1, 162), (2, 162)])
        cmds.rowColumnLayout(numberOfColumns=3, columnWidth=[(1, 108), (2, 108), (3, 108)])
        cmds.button('loadPoseButton', label=LANGUAGE_MAP._AnimationUI_.pose_load, bgc=self.buttonBgc,
                     ann=LANGUAGE_MAP._AnimationUI_.pose_load_ann,
                     command=partial(self.__uiCall, 'PoseLoad'))
        cmds.button('blendPoseButton', label=LANGUAGE_MAP._AnimationUI_.pose_blend, bgc=self.buttonBgc,
                     ann=LANGUAGE_MAP._AnimationUI_.pose_blend_ann,
                     command=partial(self.__uiCall, 'PoseBlender'))
        cmds.button('savePoseButton', label=LANGUAGE_MAP._AnimationUI_.pose_save, bgc=self.buttonBgc,
                     ann=LANGUAGE_MAP._AnimationUI_.pose_save_ann,
                     command=partial(self.__uiCall, 'PoseSave'))
        cmds.setParent(self.poseUILayout)
        cmds.separator(h=10, style='in')

        cmds.rowColumnLayout(numberOfColumns=3, columnWidth=[(1, 70), (2, 240), (3, 15)], columnSpacing=[(3, 4)])
        cmds.checkBox(self.uicbPoseHierarchy,
                                            l=LANGUAGE_MAP._Generic_.hierarchy, al='left', en=True, v=False,
                                            ann=LANGUAGE_MAP._AnimationUI_.pose_hierarchy_ann,
                                            cc=lambda x: self.__uiCache_addCheckbox(self.uicbPoseHierarchy))
        cmds.textFieldButtonGrp(self.uitfgPoseRootNode,
                                            ann=LANGUAGE_MAP._AnimationUI_.pose_set_root_ann,
                                            text="",
                                            bl=LANGUAGE_MAP._AnimationUI_.pose_set_root,
                                            bc=self.__uiCB_setPoseRootNode,
                                            cw=[(1, 180), (2, 60)])

        # new simple grab button that replaces the hidden RMB popup action
        cmds.button(self.uitfgPoseMRootGrab, label='*', command=self.__uiCB_fill_mRigsPopup)

        # add the Popup menu for the selection of mRigs dynamically
        cmds.popupMenu('_setPose_mRigs_current', button=1, postMenuCommand=self.__uiCB_fill_mRigsPopup)

        cmds.setParent(self.poseUILayout)
        cmds.separator(h=10, style='in')
        cmds.rowColumnLayout(nc=2, columnWidth=[(1, 120), (2, 160)])
        cmds.checkBox(self.uicbPoseRelative,
                                            l=LANGUAGE_MAP._AnimationUI_.pose_relative, al='left', en=True, v=False,
                                            cc=self.__uiCB_enableRelativeSwitches)
        cmds.checkBox(self.uicbPoseSpace,
                                            l=LANGUAGE_MAP._AnimationUI_.pose_maintain_parents, al='left', en=True, v=False,
                                            cc=lambda *x: self.__uiCache_addCheckbox(self.uicbPoseSpace))
        cmds.setParent(self.poseUILayout)
        cmds.separator(h=5, style='none')
        cmds.frameLayout(self.uiflPoseRelativeFrame, label=LANGUAGE_MAP._AnimationUI_.pose_rel_methods, cll=True, en=False)
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

        cmds.frameLayout('PosePointCloud', label='Pose Point Cloud', cll=True, cl=True, en=True)
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
        # ====================
        # TabsEnd
        # ====================
        cmds.tabLayout(self.tabs, edit=True, tabLabel=((self.AnimLayout, LANGUAGE_MAP._AnimationUI_.tab_animlayout),
                                                       (self.poseUILayout, LANGUAGE_MAP._AnimationUI_.tab_poselayout),
                                                       (self.FilterLayout, LANGUAGE_MAP._AnimationUI_.tab_filterlayout)))
        # ====================
        # Header
        # ====================
        if not r9Setup.mayaVersion() == 2009:
            cmds.setParent(self.MainLayout)

        cmds.separator(h=10, style='none')
        self.r9strap = cmds.iconTextButton('r9strap',
                                           style='iconAndTextHorizontal', #'iconOnly',
                                           parent=self.MainLayout,
                                           bgc=(0.7, 0, 0),
                                           image1='Rocket9_buttonStrap.png',
                                           align='left',
                                           c=lambda * args: (r9Setup.red9ContactInfo()), h=24, w=340)

        # needed for 2009
        cmds.scrollLayout(self.uiglPoseScroll, e=True, h=330)

        # ====================================
        # Show and Dock - 2016 and below only
        # ====================================

        if not r9Setup.mayaVersion() >= 2017:
            if self.dock:
                try:
                    # Maya2011 QT docking
                    cmds.dockControl(self.dockCnt, area='right', label=self.label,
                                     content=animwindow,
                                     floating=False,
                                     allowedArea=['right', 'left'],
                                     width=self.initial_winsize[0])

                    cmds.evalDeferred("cmds.dockControl('%s', e=True, r=True)" % self.dockCnt)
                except:
                    # Dock failed, opening standard Window
                    cmds.showWindow(animwindow)
                    cmds.window(self.win, edit=True, widthHeight=self.initial_winsize)
                    self.dock = False
            else:
                cmds.showWindow(animwindow)
                cmds.window(self.win, edit=True, widthHeight=self.initial_winsize)

        # set the initial Interface up
        self.__uiPresetsUpdate()
        self.__uiPresetReset()
        self.__uiCache_loadUIElements()

    # ------------------------------------------------------------------------------
    # UI Callbacks ---
    # ------------------------------------------------------------------------------

    def __uiCB_manageSnapHierachy(self, *args):
        '''
        Disable all hierarchy filtering ui's when not running hierarchys
        '''
        val = False
        if cmds.checkBox(self.uicbSnapHierarchy, q=True, v=True):
            val = True
        cmds.intFieldGrp(self.uiifSnapIterations, e=True, en=val)
        cmds.checkBox(self.uicbSnapPreCopyAttrs, e=True, en=val)
        self.__uiCache_addCheckbox(self.uicbSnapHierarchy)

    def __uiCB_manageSnapTime(self, *args):
        '''
        Disable the frmStep and PreCopy when not running timeline
        '''
        val = False
        if cmds.checkBox(self.uicbSnapRange, q=True, v=True):
            val = True
        cmds.checkBox(self.uicbSnapPreCopyKeys, e=True, en=val)
        cmds.intFieldGrp(self.uiifgSnapStep, e=True, en=val)
        self.__uiCache_addCheckbox(self.uicbSnapRange)

    def __uiCB_manageTimeOffsetChecks(self, mode, *args):
        '''
        manage time mode switches
        '''
        if cmds.checkBox(self.uicbTimeOffsetStartfrm, q=True, v=False) and cmds.checkBox(self.uicbTimeOffsetRange, q=True, v=True):
            cmds.button(self.uibtnTimeOffset, e=True, l=LANGUAGE_MAP._AnimationUI_.offset_start)
        else:
            cmds.button(self.uibtnTimeOffset, e=True, l=LANGUAGE_MAP._AnimationUI_.offsetby)

        if any([mode == 'Full', mode == 'Hier', mode == 'Timerange']):
            # selected base flags
            cmds.checkBox(self.uicbTimeOffsetPlayback, e=True, en=False)
            cmds.checkBox(self.uicbTimeOffsetFlocking, e=True, en=False)
            cmds.checkBox(self.uicbTimeOffsetRandom, e=True, en=False)

            # switch main mode
            if mode == 'Full':
                cmds.checkBox(self.uicbTimeOffsetHierarchy, e=True, v=False)
                cmds.checkBox(self.uicbTimeOffsetPlayback, e=True, en=True)
                cmds.checkBox(self.uicbTimeOffsetFlocking, e=True, en=False)
                cmds.checkBox(self.uicbTimeOffsetRandom, e=True, en=False)
            elif mode == 'Hier':
                cmds.checkBox(self.uicbTimeOffsetScene, e=True, v=False)
                cmds.checkBox(self.uicbTimeOffsetPlayback, e=True, en=False)
                cmds.checkBox(self.uicbTimeOffsetFlocking, e=True, en=True)
                cmds.checkBox(self.uicbTimeOffsetRandom, e=True, en=True)
            elif mode == 'Timerange':
                if cmds.checkBox(self.uicbTimeOffsetRange, q=True, v=True):
                    cmds.checkBox(self.uicbTimeOffsetRipple, e=True, en=True)
                    cmds.checkBox(self.uicbTimeOffsetStartfrm, e=True, en=True)
                else:
                    cmds.checkBox(self.uicbTimeOffsetRipple, e=True, en=False)
                    cmds.checkBox(self.uicbTimeOffsetStartfrm, e=True, en=False)

            self.__uiCache_addCheckbox(self.uicbTimeOffsetHierarchy)
            self.__uiCache_addCheckbox(self.uicbTimeOffsetScene)
            self.__uiCache_addCheckbox(self.uicbTimeOffsetRange)

    def __uiCB_manageTimeOffsetState(self, *args):
        '''
        Manage timeOffset initial state
        '''
        if cmds.checkBox(self.uicbTimeOffsetHierarchy, q=True, v=True):
            self.__uiCB_manageTimeOffsetChecks('Heir')
        elif cmds.checkBox(self.uicbTimeOffsetScene, q=True, v=True):
            self.__uiCB_manageTimeOffsetChecks('Full')
        self.__uiCB_manageTimeOffsetChecks('Timerange')

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
        '''
        TESTING: fix for 4k as this used to force the UI into a wrong, un-managable size
        '''
        base_width = 350
        base_height = 440

        # grab the control sizes, unfortuunately Maya over the last few releases has
        # controlled docking in different ways 2016 was dockcontrol, 2017 are workspaces
        # hence all the different size calls below!
        if cmds.window(self.win, exists=True):
            newSize = cmds.window(self.win, q=True, wh=True)
            width = newSize[0]
            height = newSize[1]
        else:
            try:  # 2017 and up
#                width = cmds.workspaceControl(self.workspaceCnt, q=True, width=True)
                height = cmds.workspaceControl(self.workspaceCnt, q=True, height=True)
            except: # 2016 undocked docked controls don't give back size data correctly
#                width = cmds.scrollLayout(self.MainLayout, q=True, width=True)
                height = cmds.scrollLayout(self.MainLayout, q=True, height=True)

        if height > base_height:
            mapped = (height / r9Setup.maya_dpi_scaling_factor()) - 430
            cmds.scrollLayout(self.uiglPoseScroll, e=True, h=max(mapped, 200))
        return

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

    # ------------------------------------------------------------------------------
    # Preset FilterSettings Management ---
    # ------------------------------------------------------------------------------

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
        self.presets = r9Setup.red9Presets_get()
        cmds.textScrollList(self.uitslPresets, edit=True, ra=True)
        cmds.textScrollList(self.uitslPresets, edit=True, append=self.presets)

    def __uiPresetStore(self, *args):
        '''
        Write a new Config Preset for the current UI state. Launches a ConfirmDialog
        '''
        selected = cmds.textScrollList(self.uitslPresets, q=True, si=True)[0].split('.')[0]
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
            path = os.path.join(self.presetDir, '%s.cfg' % cmds.promptDialog(query=True, text=True))
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
        path = os.path.normpath(self.presetDir)
        subprocess.Popen('explorer "%s"' % path)

    def __uiPresetSelection(self, Read=True, store_change=True):
        '''
        Fill the UI from on config preset file selected in the UI

        :param Read: pull the settings back from the presets
        :param store_change: save the changed state of the preset back to the settings config

        note that the ONLY way to now add the "filerNode_preset" into the ANIM_UI_OPTVARS is to
        manually interact with the presets in the UI, store_change=True by default which injects the key
        '''
        if Read:
            preset = cmds.textScrollList(self.uitslPresets, q=True, si=True)[0]
            self.filterSettings.read(os.path.join(self.presetDir, preset))
            # fill the cache up for the ini file
            try:
                # we only store the change from the UI, this allows the basePreset to
                # be loaded but NOT stored
                if store_change:
                    self.ANIM_UI_OPTVARS['AnimationUI']['filterNode_preset'] = preset
            except:
                pass
            log.info('preset loaded : %s' % preset)

        # JUST reset the UI elements
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

        # rigData block specific
        if hasattr(self.filterSettings, 'rigData'):
            if 'snapPriority' in self.filterSettings.rigData \
                    and r9Core.decodeString(self.filterSettings.rigData['snapPriority']):
                cmds.checkBox(self.uicbSnapPriorityOnly, e=True, v=True)

        # manage the MatchMethod setting
        if self.filterSettings.metaRig:
            # self.matchMethod = 'metaData'
            cmds.optionMenu('om_MatchMethod', e=True, v='metaData')
        else:
            cmds.optionMenu('om_MatchMethod', e=True, v='stripPrefix')

        # need to run the callback on the PoseRootUI setup
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

        # this is kind of against the filterSettings Idea, shoe horned in here
        # as it makes sense from the UI standpoint
        self.filterSettings.rigData['snapPriority'] = cmds.checkBox(self.uicbSnapPriorityOnly, q=True, v=True)

    def __uiSetPriorities(self, mode='set', *args):
        if mode == 'set' or mode == 'clear':
            cmds.textScrollList('uitslFilterPriority', e=True, ra=True)
        if mode == 'set' or mode == 'append':
            node = [r9Core.nodeNameStrip(node) for node in cmds.ls(sl=True)]
            cmds.textScrollList('uitslFilterPriority', e=True, append=[r9Core.nodeNameStrip(node) for node in cmds.ls(sl=True)])

        if mode == 'moveUp' or mode == 'moveDown' or mode == 'remove':
            selected = cmds.textScrollList('uitslFilterPriority', q=True, si=True)[0]
            data = cmds.textScrollList('uitslFilterPriority', q=True, ai=True)
            cmds.textScrollList('uitslFilterPriority', e=True, ra=True)
        if mode == 'moveUp':
            data.insert(data.index(selected) - 1, data.pop(data.index(selected)))
            cmds.textScrollList('uitslFilterPriority', e=True, append=data)
            cmds.textScrollList('uitslFilterPriority', e=True, si=selected)
        if mode == 'moveDown':
            data.insert(data.index(selected) + 1, data.pop(data.index(selected)))
            cmds.textScrollList('uitslFilterPriority', e=True, append=data)
            cmds.textScrollList('uitslFilterPriority', e=True, si=selected)
        if mode == 'remove':
            data.remove(selected)
            cmds.textScrollList('uitslFilterPriority', e=True, append=data)
        self.__uiPresetFillFilter()
        self.__uiCache_storeUIElements()

    # -----------------------------------------------------------------------------
    # PoseSaver Path Management ---
    # ------------------------------------------------------------------------------

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
        self.poses = []
        if not os.path.exists(self.posePath):
            log.debug('posePath is invalid')
            return self.poses
        files = os.listdir(self.posePath)
        if files:
            if sortBy == 'name':
                files = r9Core.sortNumerically(files)
                # files.sort()
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
            filteredPoses = []
            filters = searchFilter.replace(' ', '').split(',')
            for pose in self.poses:
                for srch in filters:
                    if srch and srch.upper() in pose.upper():
                        if pose not in filteredPoses:
                            filteredPoses.append(pose)
        return filteredPoses

    def __validatePoseFunc(self, func):
        '''
        called in some of the funcs so that they either raise an error when called in 'Project' mode
        or raise a Confirm Dialog to let teh user decide. This behaviour is controlled by the var
        self.poseProjectMute
        '''
        if self.posePathMode == 'projectPoseMode':
            if self.poseProjectMute:
                raise StandardError('%s : function disabled in Project Pose Mode!' % func)
            else:
                result = cmds.confirmDialog(
                    title='Project Pose Modifications',
                    button=['Continue', 'Cancel'],
                    message='You are trying to modify a Project Pose\n\nPlease Confirm Action!',
                    defaultButton='Cancel',
                    icon='warning',
                    cancelButton='Cancel',
                    bgc=r9Setup.red9ButtonBGC('red'),
                    dismissString='Cancel')
                if result == 'Continue':
                    return True
                else:
                    log.info('Pose Project function : "%s" : aborted by user' % func)
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

        if mode == 'local' or mode == 'localPoseMode':
            self.posePath = r9General.formatPath_join(self.posePathLocal, self.getPoseSubFolder())
            if not os.path.exists(self.posePath):
                log.warning('No Matching Local SubFolder path found - Reverting to Root')
                self.__uiCB_clearSubFolders()
                self.posePath = self.posePathLocal

            self.posePathMode = 'localPoseMode'
            if self.poseProjectMute:
                cmds.button('savePoseButton', edit=True, en=True, bgc=r9Setup.red9ButtonBGC(1))
            cmds.textFieldButtonGrp(self.uitfgPosePath, edit=True, text=self.posePathLocal)

        elif mode == 'project' or mode == 'projectPoseMode':
            self.posePath = r9General.formatPath_join(self.posePathProject, self.getPoseSubFolder())
            if not os.path.exists(self.posePath):
                log.warning('No Matching Project SubFolder path found - Reverting to Root')
                self.__uiCB_clearSubFolders()
                self.posePath = self.posePathProject

            self.posePathMode = 'projectPoseMode'
            if self.poseProjectMute:
                cmds.button('savePoseButton', edit=True, en=False, bgc=r9Setup.red9ButtonBGC(2))
            cmds.textFieldButtonGrp(self.uitfgPosePath, edit=True, text=self.posePathProject)

        cmds.scrollLayout(self.uiglPoseScroll, edit=True, sp='up')  # scroll the layout to the top!

        self.ANIM_UI_OPTVARS['AnimationUI']['posePathMode'] = self.posePathMode

        if not os.path.exists(self.posePath):
            # path not valid clear all
            log.warning('No Current PosePath Set or Current Path is Invalid!')
            return

        self.__uiCB_fillPoses(rebuildFileList=True)

    def __uiCB_setPosePath(self, path=None, fileDialog=False, *args):
        '''
        Manage the PosePath textfield and build the PosePath
        '''
        if fileDialog:
            try:
                path = cmds.fileDialog2(fileMode=3, dir=cmds.textFieldButtonGrp(self.uitfgPosePath, q=True, text=True))[0]
            except:
                log.warning('No Folder Selected or Given')
                return
        else:
            if not path:
                path = cmds.textFieldButtonGrp(self.uitfgPosePath, q=True, text=True)

        if path and os.path.exists(path):
            self.posePath = r9General.formatPath(path)
        else:
            log.warning('Given Pose Path not found!')

        cmds.textFieldButtonGrp(self.uitfgPosePath, edit=True, text=self.posePath)
        cmds.textFieldButtonGrp('uitfgPoseSubPath', edit=True, text="")

        # internal cache for the 2 path modes
        if self.posePathMode == 'localPoseMode':
            self.posePathLocal = self.posePath
        else:
            self.posePathProject = self.posePath
        self.__uiCB_pathSwitchInternals()

    def __uiCB_pathSwitchInternals(self):
        '''
        fill the UI Cache and update the poses in eth UI
        '''
        self.__uiCB_fillPoses(rebuildFileList=True)

        # fill the cache up for the ini file
        self.ANIM_UI_OPTVARS['AnimationUI']['posePath'] = self.posePath
        self.ANIM_UI_OPTVARS['AnimationUI']['poseSubPath'] = self.getPoseSubFolder()
        self.ANIM_UI_OPTVARS['AnimationUI']['posePathLocal'] = self.posePathLocal
        self.ANIM_UI_OPTVARS['AnimationUI']['posePathProject'] = self.posePathProject
        self.ANIM_UI_OPTVARS['AnimationUI']['posePathMode'] = self.posePathMode
        self.__uiCache_storeUIElements()

    # SubFolder Pose Calls ----------
    def __uiCB_switchSubFolders(self, *args):
        '''
        switch the scroller from pose mode to subFolder select mode
        note we prefix the folder with '/' to help denote it's a folder in the UI
        '''
        basePath = cmds.textFieldButtonGrp(self.uitfgPosePath, query=True, text=True)

        # turn OFF the 2 main poseScrollers
        cmds.textScrollList(self.uitslPoses, edit=True, vis=False)
        cmds.scrollLayout(self.uiglPoseScroll, edit=True, vis=False)
        # turn ON the subFolder scroller
        cmds.textScrollList(self.uitslPoseSubFolders, edit=True, vis=True)
        cmds.textScrollList(self.uitslPoseSubFolders, edit=True, ra=True)

        if not os.path.exists(basePath):
            # path not valid clear all
            log.warning('No current PosePath set')
            return

        dirs = [subdir for subdir in os.listdir(basePath) if os.path.isdir(os.path.join(basePath, subdir))]
        if not dirs:
            log.warning('Folder has no subFolders for pose scanning')
        for subdir in dirs:
            cmds.textScrollList(self.uitslPoseSubFolders, edit=True,
                                            append='/%s' % subdir,
                                            sc=partial(self.__uiCB_setSubFolder))

    def __uiCB_setSubFolder(self, *args):
        '''
        Select a subFolder from the scrollList and update the systems
        '''
        basePath = cmds.textFieldButtonGrp(self.uitfgPosePath, query=True, text=True)
        subFolder = cmds.textScrollList(self.uitslPoseSubFolders, q=True, si=True)[0].split('/')[-1]

        cmds.textFieldButtonGrp('uitfgPoseSubPath', edit=True, text=subFolder)
        cmds.textScrollList(self.uitslPoseSubFolders, edit=True, vis=False)
        self.posePath = r9General.formatPath_join(basePath, subFolder)
        self.__uiCB_pathSwitchInternals()

    def __uiCB_clearSubFolders(self, *args):
        cmds.textScrollList(self.uitslPoseSubFolders, edit=True, vis=False)
        self.__uiCB_setPosePath()

    # ----------------------------------------------------------------------------
    # Build Pose UI calls  ---
    # ----------------------------------------------------------------------------

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
        return os.path.join(cmds.textFieldButtonGrp(self.uitfgPosePath, query=True, text=True),
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
        searchFilter = cmds.textFieldGrp(self.tfPoseSearchFilter, q=True, text=True)

        if rebuildFileList:
            self.buildPoseList(sortBy=sortBy)
            log.debug('Rebuilt Pose internal Lists')
            # Project mode and folder contains NO poses so switch to subFolders
            if not self.poses and self.posePathMode == 'projectPoseMode':
                log.warning('No Poses found in Root Project directory, switching to subFolder pickers')
#                 self.__uiCB_switchSubFolders()
#                 return

        log.debug('searchFilter  : %s : rebuildFileList : %s' % (searchFilter, rebuildFileList))

        # TextScroll Layout
        # ================================
        if not self.poseGridMode == 'thumb':
            cmds.textScrollList(self.uitslPoseSubFolders, edit=True, vis=False)  # subfolder scroll OFF
            cmds.textScrollList(self.uitslPoses, edit=True, vis=True)  # pose TexScroll ON
            cmds.scrollLayout(self.uiglPoseScroll, edit=True, vis=False)  # pose Grid OFF
            cmds.textScrollList(self.uitslPoses, edit=True, ra=True)  # clear textScroller

            if searchFilter:
                cmds.scrollLayout(self.uiglPoseScroll, edit=True, sp='up')

            for pose in r9Core.filterListByString(self.poses, searchFilter, matchcase=False) or []:  # self.buildFilteredPoseList(searchFilter):
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
                buttons = cmds.gridLayout(self.uiglPoses, q=True, ca=True)
                if buttons:
                    for button in buttons:
                        cmds.deleteUI(button)
            except StandardError, error:
                print(error)

            for pose in r9Core.filterListByString(self.poses, searchFilter, matchcase=False) or []:  # self.buildFilteredPoseList(searchFilter):
                try:
                    # :NOTE we prefix the buttons to get over the issue of non-numeric
                    # first characters which are stripped my Maya!
                    cmds.iconTextCheckBox('_%s' % pose, style='iconAndTextVertical',
                                            image=os.path.join(self.posePath, '%s.bmp' % pose),
                                            label=pose,
                                            bgc=self.poseButtonBGC,
                                            parent=self.uiglPoses,
                                            ann=pose,
                                            onc=partial(self.__uiCB_iconGridSelection, pose),
                                            ofc="import maya.cmds as cmds;cmds.iconTextCheckBox('_%s', e=True, v=True)" % pose)  # we DONT allow you to deselect
                except StandardError, error:
                    raise StandardError(error)

            if searchFilter:
                # with search scroll the list to the top as results may seem blank otherwise
                cmds.scrollLayout(self.uiglPoseScroll, edit=True, sp='up')

        # Finally Bind the Popup-menu
        cmds.evalDeferred(self.__uiCB_PosePopup)

    def __uiCB_fill_mRigsPopup(self, *args):
        '''
        Fill the Pose root mRig popup menu
        '''
        cmds.popupMenu('_setPose_mRigs_current', e=True, deleteAllItems=True)
        if self.poseRootMode == 'MetaRoot':
            # fill up the mRigs
            cmds.menuItem(label='AUTO RESOLVED : mRigs', p='_setPose_mRigs_current',
                          command=partial(self.__uiCB_setPoseRootNode, '****  AUTO__RESOLVED  ****'))
            cmds.menuItem(p='_setPose_mRigs_current', divider=True)
            #  cmds.menuItem(p='_setPose_mRigs_current', divider=True)
            for rig in r9Meta.getMetaRigs():
                if rig.hasAttr('exportTag') and rig.exportTag:
                    cmds.menuItem(label='%s :: %s' % (rig.exportTag.tagID, rig.mNode), p='_setPose_mRigs_current',
                              command=partial(self.__uiCB_setPoseRootNode, rig.mNode))
                else:
                    cmds.menuItem(label=rig.mNode, p='_setPose_mRigs_current',
                              command=partial(self.__uiCB_setPoseRootNode, rig.mNode))

    def __uiCB_PosePopup(self, *args):
        '''
        RMB popup menu for the Pose functions
        '''
        enableState = True
        if self.posePathMode == 'projectPoseMode' and self.poseProjectMute:
            enableState = False

        if self.poseGridMode == 'thumb':
            parent = self.posePopupGrid
            cmds.popupMenu(self.posePopupGrid, e=True, deleteAllItems=True)
        else:
            parent = self.posePopupText
            cmds.popupMenu(self.posePopupText, e=True, deleteAllItems=True)

        cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.pose_rmb_blender, p=parent, command=partial(self.__uiCall, 'PoseBlender'))
        cmds.menuItem(divider=True, p=parent)
        cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.pose_rmb_delete, en=enableState, p=parent, command=partial(self.__uiPoseDelete))
        cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.pose_rmb_rename, en=enableState, p=parent, command=partial(self.__uiPoseRename))
        cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.pose_rmb_selectinternal, p=parent, command=partial(self.__uiPoseSelectObjects))

        cmds.menuItem(divider=True, p=parent)
        cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.pose_rmb_update_pose, en=enableState, p=parent, command=partial(self.__uiPoseUpdate, False))
        cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.pose_rmb_update_pose_thumb, en=enableState, p=parent, command=partial(self.__uiPoseUpdate, True))

        if self.poseGridMode == 'thumb':
            cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.pose_rmb_update_thumb, p=parent, command=partial(self.__uiPoseUpdateThumb))

        cmds.menuItem(divider=True, p=parent)
        cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.pose_rmb_add_subfolder, en=enableState, p=parent, command=partial(self.__uiPoseMakeSubFolder))
        cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.pose_rmb_refresh, en=True, p=parent, command=lambda x: self.__uiCB_fillPoses(rebuildFileList=True))
        cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.pose_rmb_openfile, p=parent, command=partial(self.__uiPoseOpenFile))
        cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.pose_rmb_opendir, p=parent, command=partial(self.__uiPoseOpenDir))
        cmds.menuItem(divider=True, p=parent)

        # ProPack Additions ======
        _submenu = cmds.menuItem('red9PoseCompareSM', l=LANGUAGE_MAP._AnimationUI_.pose_rmb_compare, sm=True, p=parent)
        cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.pose_rmb_compare_skel, p=_submenu, command=partial(self.__uiCall, 'PoseCompareSkelDict'))
        cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.pose_rmb_compare_posedata, p=_submenu, command=partial(self.__uiCall, 'PoseComparePoseDict'))
 
        cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.pose_rmb_copyhandler, en=enableState, p=parent, command=partial(self.__uiPoseAddPoseHandler))
 
        _submenu = cmds.menuItem('red9PoseExportSM', l=LANGUAGE_MAP._AnimationUI_.pose_rmb_export_fbx_handler, sm=True, p=parent)
        cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.pose_rmb_export_fbx_handler_pose, p=_submenu, command=partial(self.__uiPoseExport_to_FBX, 'pose'))
        cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.pose_rmb_export_fbx_handler_dir, p=_submenu, command=partial(self.__uiPoseExport_to_FBX, 'dir'))
        cmds.menuItem(divider=True, p=parent)
        # ProPack End ============
        
        cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.pose_rmb_copypose, en=enableState, p=parent, command=partial(self.__uiPoseCopyToProject))

        cmds.menuItem(divider=True, p=parent)
        cmds.menuItem(label=LANGUAGE_MAP._AnimationUI_.pose_rmb_switchmode, p=parent, command=self.__uiCB_switchPoseMode)

        if self.poseGridMode == 'thumb':
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
                log.debug('Inspecting PoseHandlerPath : %s' % path)
                if os.path.exists(path):
                    poseHandlers = os.listdir(path)
                    if poseHandlers:
                        for handler in poseHandlers:
                            if handler.endswith('_poseHandler.py'):
                                handlerPath = os.path.join(path, handler)
                                log.debug('poseHandler file being bound to RMB popup : %s' % handlerPath)
                                cmds.menuItem(label='Add Subfolder : %s' % handler.replace('_poseHandler.py', '').upper(),
                                              en=True, p=parentPopup,
                                              command=partial(self.__uiPoseMakeSubFolder, handlerPath))

    def addPopupMenusFromFolderConfig(self, parentPopup):
        '''
        if the poseFolder has a poseHandler.py file see if it has the 'posePopupAdditions' func
        and if so, use that to extend the standard menu's
        '''
        if self.getPoseDir():
            poseHandler = r9Pose.getFolderPoseHandler(self.getPoseDir())
            if poseHandler:
                import imp
                import inspect
                print('Adding to menus From PoseHandler File!!!!')
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
            cells = int(cmds.scrollLayout(self.uiglPoseScroll, q=True, w=True) / cmds.gridLayout(self.uiglPoses, q=True, cw=True))
            if cells > 1:
                cmds.gridLayout(self.uiglPoses, e=True, nc=cells)
        else:
            log.debug('this call FAILS in 2009???')

    # ------------------------------------------------------------------------------
    # Main Pose Function Wrappers ---
    # ------------------------------------------------------------------------------

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
            name = cmds.promptDialog(query=True, text=True)
            try:
                return os.path.join(self.getPoseDir(), '%s.pose' % r9Core.validateString(name, fix=True))
            except ValueError, error:
                raise ValueError(error)

    def __uiCB_setPoseRootNode(self, specific=None, *args):
        '''
        This changes the mode for the Button that fills in rootPath in the poseUI
        Either fills with the given node, or fill it with the connected MetaRig

        :param specific: passed in directly from the UI calls
        '''
        rootNode = cmds.ls(sl=True, l=True)

        def fillTextField(text):
            # bound to a function so it can be passed onto the MetaNoode selector UI
            cmds.textFieldButtonGrp(self.uitfgPoseRootNode, e=True, text=text)

        if specific:
            fillTextField(specific)
            if self.poseRootMode == 'MetaRoot':
                if specific != '****  AUTO__RESOLVED  ****':
                    cmds.select(r9Meta.MetaClass(specific).ctrl_main)
                else:
                    cmds.select(cl=True)
        else:
            if self.poseRootMode == 'RootNode':
                if not rootNode:
                    raise StandardError('Warning nothing selected')
                fillTextField(rootNode[0])
            elif self.poseRootMode == 'MetaRoot':
                if rootNode:
                    # metaRig=r9Meta.getConnectedMetaNodes(rootNode[0])
                    metaRig = r9Meta.getConnectedMetaSystemRoot(rootNode[0])
                    if not metaRig:
                        raise StandardError("Warning selected node isn't connected to a MetaRig node")
                    fillTextField(metaRig.mNode)
                else:
                    metaRigs = r9Meta.getMetaNodes(dataType='mClass')
                    if metaRigs:
                        r9Meta.MClassNodeUI(closeOnSelect=True,
                                            funcOnSelection=fillTextField,
                                            mInstances=['MetaRig'],
                                            allowMulti=False)._showUI()
                    else:
                        raise StandardError("Warning: No MetaRigs found in the Scene")

        # fill the cache up for the ini file
        self.ANIM_UI_OPTVARS['AnimationUI']['poseRoot'] = cmds.textFieldButtonGrp(self.uitfgPoseRootNode, q=True, text=True)
        self.__uiCache_storeUIElements()

    def __uiCB_managePoseRootMethod(self, *args):
        '''
        Manage the PoseRootNode method, either switch to standard rootNode or MetaNode
        '''

        if cmds.checkBox('uicbMetaRig', q=True, v=True):
            self.poseRootMode = 'MetaRoot'
            cmds.textFieldButtonGrp(self.uitfgPoseRootNode, e=True, bl='MetaRoot')
            cmds.button(self.uitfgPoseMRootGrab, e=True, en=True)
        else:
            self.poseRootMode = 'RootNode'
            cmds.textFieldButtonGrp(self.uitfgPoseRootNode, e=True, bl='SetRoot')
            cmds.button(self.uitfgPoseMRootGrab, e=True, en=False)
        self.__uiCache_storeUIElements()

    def __uiCB_getPoseInputNodes(self):
        '''
        Node passed into the __PoseCalls in the UI
        '''
        # posenodes = []
        _selected = cmds.ls(sl=True, l=True)
        _rootSet = cmds.textFieldButtonGrp(self.uitfgPoseRootNode, q=True, text=True)
        if cmds.checkBox(self.uicbPoseHierarchy, q=True, v=True):
            # hierarchy processing so we MUST pass a root in
            if not _rootSet or not cmds.objExists(_rootSet):
                if _rootSet == '****  AUTO__RESOLVED  ****' and self.poseRootMode == 'MetaRoot':
                    if _selected:
                        return r9Meta.getConnectedMetaSystemRoot(_selected)
                raise StandardError('RootNode not Set for Hierarchy Processing')
            else:
                return _rootSet
        else:
            if _selected:
                return _selected
        if not _selected:
            raise StandardError('No Nodes Set or selected for Pose')
        return _selected

    def __uiCB_enableRelativeSwitches(self, *args):
        '''
        switch the relative mode on for the poseLaoder
        '''
        self.__uiCache_addCheckbox(self.uicbPoseRelative)
        state = cmds.checkBox(self.uicbPoseRelative, q=True, v=True)
        cmds.checkBox(self.uicbPoseSpace, e=True, en=False)
        cmds.checkBox(self.uicbPoseSpace, e=True, en=state)
        cmds.frameLayout(self.uiflPoseRelativeFrame, e=True, en=state)

    def __uiPoseDelete(self, *args):
        if not self.__validatePoseFunc('DeletePose'):
            return
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
        if not self.__validatePoseFunc('PoseRename'):
            return
        try:
            newName = self.__uiCB_savePosePath(self.getPoseSelected())
        except ValueError, error:
            raise ValueError(error)
        try:
            os.rename(self.getPosePath(), newName)
            os.rename(self.getIconPath(), '%s.bmp' % newName.split('.pose')[0])
        except:
            log.info('Failed to Rename Pose')
        self.__uiCB_fillPoses(rebuildFileList=True)
        pose = os.path.basename(newName.split('.pose')[0])
        self.__uiCB_selectPose(pose)

    def __uiPoseOpenFile(self, *args):
        import subprocess
        path = os.path.normpath(self.getPosePath())
        subprocess.Popen('notepad "%s"' % path)

    def __uiPoseOpenDir(self, *args):
        import subprocess
        path = os.path.normpath(self.getPoseDir())
        subprocess.Popen('explorer "%s"' % path)

    def __uiPoseUpdate(self, storeThumbnail, *args):
        if not self.__validatePoseFunc('UpdatePose'):
            return
        result = cmds.confirmDialog(
                title='PoseUpdate',
                message=('<< Replace & Update Pose file >>\n\n%s' % self.poseSelected),
                button=['OK', 'Cancel'],
                defaultButton='OK',
                cancelButton='Cancel',
                dismissString='Cancel')
        if result == 'OK':
            if storeThumbnail:
                try:
                    os.remove(self.getIconPath())
                except:
                    log.debug('unable to delete the Pose Icon file')
            self.__PoseSave(self.getPosePath(), storeThumbnail)
            self.__uiCB_selectPose(self.poseSelected)

    def __uiPoseUpdateThumb(self, *args):
        sel = cmds.ls(sl=True, l=True)
        cmds.select(cl=True)
        thumbPath = self.getIconPath()
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
        rootNode = cmds.textFieldButtonGrp(self.uitfgPoseRootNode, q=True, text=True)
        if rootNode and cmds.objExists(rootNode):
            self.__uiPresetFillFilter()  # fill the filterSettings Object
            pose = r9Pose.PoseData(self.filterSettings)
            pose.matchMethod = cmds.optionMenu('om_MatchMethod', q=True, v=True)
            pose._readPose(self.getPosePath())
            nodes = pose.matchInternalPoseObjects(rootNode)
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
        basePath = cmds.textFieldButtonGrp(self.uitfgPosePath, query=True, text=True)
        if not os.path.exists(basePath):
            raise StandardError('Base Pose Path is inValid or not yet set')
        promptstring = 'New Pose Folder Name'
        if handlerFile:
            promptstring = 'New %s POSE Folder Name' % os.path.basename(handlerFile).replace('_poseHandler.py', '').upper()
        result = cmds.promptDialog(
                title=promptstring,
                message='Enter Name:',
                button=['OK', 'Cancel'],
                defaultButton='OK',
                cancelButton='Cancel',
                dismissString='Cancel')
        if result == 'OK':
            subFolder = cmds.promptDialog(query=True, text=True)
            cmds.textFieldButtonGrp('uitfgPoseSubPath', edit=True, text=subFolder)
            self.posePath = r9General.formatPath_join(basePath, subFolder)
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
        syncSubFolder = True
        projectPath = self.posePathProject
        if not os.path.exists(self.posePathProject):
            raise StandardError('Project Pose Path is inValid or not yet set')
        if syncSubFolder:
            subFolder = self.getPoseSubFolder()
            projectPath = os.path.join(projectPath, subFolder)

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
                elif result == 'CopyToRoot':
                    projectPath = self.posePathProject
                else:
                    return

        log.info('Copying Local Pose: %s >> %s' % (self.poseSelected, projectPath))
        try:
            shutil.copy2(self.getPosePath(), projectPath)
            shutil.copy2(self.getIconPath(), projectPath)
        except:
            raise StandardError('Unable to copy pose : %s > to Project directory' % self.poseSelected)

    def __uiPoseAddPoseHandler(self, *args):
        '''
        PRO_PACK : Copy local pose to the Project Pose Folder
        '''
        r9Setup.PRO_PACK_STUBS().AnimationUI_stubs.uiCB_poseAddPoseHandler(self.posePath)

    def __uiPoseExport_to_FBX(self, mode='pose', *args):
        '''
        PRO_PACK : export the given pose / pose dir to single frame FBX files for MoBu usage
        '''
        if mode == 'pose':
            r9Setup.PRO_PACK_STUBS().AnimationUI_stubs.uiCB_poseExport_to_fbx(posepath=self.getPosePath())
        elif mode == 'dir':
            result = cmds.confirmDialog(
                    title='Export pose Dir to FBX',
                    message='This will export all poses in the current directory to single frame FBX files, Continue?',
                    button=['Confirm', 'Cancel'],
                    defaultButton='Confirm',
                    icon='warning',
                    cancelButton='Cancel',
                    dismissString='Cancel')
            if result == 'Confirm':
                r9Setup.PRO_PACK_STUBS().AnimationUI_stubs.uiCB_poseExport_to_fbx(pose_folder=self.getPoseDir())

    # ------------------------------------------------------------------------------
    # UI Elements ConfigStore Callbacks ---
    # ------------------------------------------------------------------------------

    def __uiCache_storeUIElements(self, *args):
        '''
        Store some of the main components of the UI out to an ini file
        '''
        if not self.uiBoot:
            log.debug('Red9 AnimUI : config file being written')
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
        self.uiBoot = True  # prevents the writing of the element changes during the loading
        try:
            log.debug('Red9 AnimUI : Loading UI Elements from the config file')

            def __uiCache_LoadCheckboxes():
                if 'AnimationUI' in self.ANIM_UI_OPTVARS:
                    if 'checkboxes' in self.ANIM_UI_OPTVARS['AnimationUI'] and \
                                self.ANIM_UI_OPTVARS['AnimationUI']['checkboxes']:
                        for cb, status in self.ANIM_UI_OPTVARS['AnimationUI']['checkboxes'].items():
                            try:
                                cmds.checkBox(cb, e=True, v=r9Core.decodeString(status))
                            except:
                                print('given checkbox no longer exists : %s' % cb)

            AnimationUI = self.ANIM_UI_OPTVARS['AnimationUI']

            if self.basePreset:
                # we have a basePreset but we don't yet have the "fileNode_preset" key in our
                # config as there's been no manual interaction with the presets ui. hence (store_change=False)
                if 'filterNode_preset' not in AnimationUI or not AnimationUI['filterNode_preset']:
                    try:
                        cmds.textScrollList(self.uitslPresets, e=True, si=self.basePreset)
                        self.__uiPresetSelection(Read=True, store_change=False)
                    except:
                        log.debug('given basePreset not found')
            # we already have the filerNode_preset in the config so we can write it (store_change=True)
            if 'filterNode_preset' in AnimationUI and AnimationUI['filterNode_preset']:
                try:
                    cmds.textScrollList(self.uitslPresets, e=True, si=AnimationUI['filterNode_preset'])
                    self.__uiPresetSelection(Read=True, store_change=True)  # ##not sure on this yet????
                except:
                    log.warning('Failed to load cached preset : %s' % AnimationUI['filterNode_preset'])

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
                if AnimationUI['poseRoot'] == '****  AUTO__RESOLVED  ****' or cmds.objExists(AnimationUI['poseRoot']):
                    cmds.textFieldButtonGrp(self.uitfgPoseRootNode, e=True, text=AnimationUI['poseRoot'])

            __uiCache_LoadCheckboxes()

            # callbacks
            if self.posePathMode:
                print('setting : ', self.posePathMode)
                cmds.radioCollection(self.uircbPosePathMethod, edit=True, select=self.posePathMode)
            self.__uiCB_enableRelativeSwitches()  # relativePose switch enables
            self.__uiCB_managePoseRootMethod()  # metaRig or SetRootNode for Pose Root
            self.__uiCB_switchPosePathMode(self.posePathMode)  # pose Mode - 'local' or 'project'
            self.__uiCB_manageSnapHierachy()  # preCopyAttrs
            self.__uiCB_manageSnapTime()  # preCopyKeys
            self.__uiCB_manageTimeOffsetState()

        except StandardError, err:
            log.debug('failed to complete UIConfig load')
            log.warning(err)
        finally:
            self.uiBoot = False

    def __uiCache_readUIElements(self):
        '''
        read the config ini file for the initial state of the ui
        '''
        try:
            log.debug('Red9 AnimUI : Reading UI Elements from the config file')
            if os.path.exists(self.ui_optVarConfig):
                self.filterSettings.read(self.ui_optVarConfig)  # use the generic reader for this
                self.ANIM_UI_OPTVARS['AnimationUI'] = configobj.ConfigObj(self.ui_optVarConfig)['AnimationUI']
            else:
                self.ANIM_UI_OPTVARS['AnimationUI'] = {}
        except:
            pass

    def __uiCache_addCheckbox(self, checkbox):
        '''
        Now shifted into a sub dic for easier processing
        '''
        log.debug('Red9 AnimUI : checkbox state changed')
        if 'checkboxes' not in self.ANIM_UI_OPTVARS['AnimationUI']:
            self.ANIM_UI_OPTVARS['AnimationUI']['checkboxes'] = {}
        self.ANIM_UI_OPTVARS['AnimationUI']['checkboxes'][checkbox] = cmds.checkBox(checkbox, q=True, v=True)
        self.__uiCache_storeUIElements()

    def __uiCache_resetDefaults(self, *args):
        log.debug('Red9 AnimUI : reset from "__red9animreset__" called')
        defaultConfig = os.path.join(self.presetDir, '__red9animreset__')
        # delete the current config file
        if os.path.exists(self.ui_optVarConfig):
            os.remove(self.ui_optVarConfig)
        # load the reset config from presets
        if os.path.exists(defaultConfig):
            __constants = dict(self.ANIM_UI_OPTVARS['AnimationUI'])
            self.ANIM_UI_OPTVARS['AnimationUI'] = configobj.ConfigObj(defaultConfig)['AnimationUI']

            # inject the path data back rather than just blank them off??
#             if 'posePathMode' in __constants and __constants['posePathMode']:
#                 self.ANIM_UI_OPTVARS['posePathMode'] = __constants['posePathMode']
            if 'posePathLocal' in __constants and __constants['posePathLocal']:
                self.ANIM_UI_OPTVARS['posePathLocal'] = __constants['posePathLocal']
            if 'posePathProject' in __constants and __constants['posePathProject']:
                self.ANIM_UI_OPTVARS['posePathProject'] = __constants['posePathProject']

            self.__uiCache_loadUIElements()

    # -----------------------------------------------------------------------------
    # MAIN UI FUNCTION CALLS ---
    # ------------------------------------------------------------------------------

    def __validate_roots(self):
        '''
        new wrapper func to return any mRig system roots from selected
        when processing in Hierarchy mode only! This now means that all the
        hierarchy checkbox in the UI will deal with the mRigs as a whole rather
        than at a system level
        '''
        objs = cmds.ls(sl=True)
        nodes = []
        if self.filterSettings.metaRig:
            for obj in objs:
                sysroot = r9Meta.getConnectedMetaSystemRoot(obj)
                if sysroot:
                    nodes.append(sysroot)
            return nodes
        return objs

    def __CopyAttrs(self):
        '''
        Internal UI call for CopyAttrs
        '''
        # print 'MatchMethod : ', self.matchMethod
        if not len(cmds.ls(sl=True, l=True)) >= 2:
            log.warning('Please Select at least 2 nodes to Process!!')
            return
        self.kws['toMany'] = cmds.checkBox(self.uicbCAttrToMany, q=True, v=True)
        if cmds.checkBox(self.uicbCAttrChnAttrs, q=True, v=True):
            self.kws['attributes'] = getChannelBoxSelection()
        if cmds.checkBox(self.uicbCAttrHierarchy, q=True, v=True):
            if self.kws['toMany']:
                AnimFunctions(filterSettings=self.filterSettings, matchMethod=self.matchMethod).copyAttrs_ToMultiHierarchy(self.__validate_roots(), **self.kws)
            else:
                AnimFunctions(filterSettings=self.filterSettings, matchMethod=self.matchMethod).copyAttributes(nodes=self.__validate_roots(), **self.kws)
        else:
            print(self.kws)
            AnimFunctions(matchMethod=self.matchMethod).copyAttributes(nodes=None, **self.kws)

    def __CopyKeys(self):
        '''
        Internal UI call for CopyKeys call
        '''
        if not len(cmds.ls(sl=True, l=True)) >= 2:
            log.warning('Please Select at least 2 nodes to Process!!')
            return
        self.kws['toMany'] = cmds.checkBox(self.uicbCKeyToMany, q=True, v=True)
        self.kws['pasteKey'] = cmds.optionMenu('om_PasteMethod', q=True, v=True)
        self.kws['mergeLayers'] = cmds.checkBox(self.uicbCKeyAnimLay, q=True, v=True)
        self.kws['timeOffset'] = cmds.floatFieldGrp(self.uiffgCKeyStep, q=True, v1=True)
        if cmds.checkBox(self.uicbCKeyRange, q=True, v=True):
            self.kws['time'] = timeLineRangeGet()
        if cmds.checkBox(self.uicbCKeyChnAttrs, q=True, v=True):
            self.kws['attributes'] = getChannelBoxSelection()
        if cmds.checkBox(self.uicbCKeyHierarchy, q=True, v=True):
            if self.kws['toMany']:
                AnimFunctions(filterSettings=self.filterSettings, matchMethod=self.matchMethod).copyKeys_ToMultiHierarchy(self.__validate_roots(), **self.kws)
            else:
                AnimFunctions(filterSettings=self.filterSettings, matchMethod=self.matchMethod).copyKeys(nodes=self.__validate_roots(), **self.kws)
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
        self.kws['iterations'] = cmds.intFieldGrp(self.uiifSnapIterations, q=True, v=True)[0]
        self.kws['step'] = cmds.intFieldGrp(self.uiifgSnapStep, q=True, v=True)[0]
        self.kws['pasteKey'] = cmds.optionMenu('om_PasteMethod', q=True, v=True)
        self.kws['mergeLayers'] = cmds.checkBox(self.uicbCKeyAnimLay, q=True, v=True)
        self.kws['snapTranslates'] = cmds.checkBox(self.uicbSnapTrans, q=True, v=True)
        self.kws['snapRotates'] = cmds.checkBox(self.uicbStapRots, q=True, v=True)

        if cmds.checkBox(self.uicbSnapRange, q=True, v=True):
            self.kws['time'] = timeLineRangeGet()
        if cmds.checkBox(self.uicbSnapPreCopyKeys, q=True, v=True):
            self.kws['preCopyKeys'] = True
        if cmds.checkBox(self.uicbSnapPreCopyAttrs, q=True, v=True):
            self.kws['preCopyAttrs'] = True
        if cmds.checkBox(self.uicbSnapHierarchy, q=True, v=True):
            self.kws['prioritySnapOnly'] = cmds.checkBox(self.uicbSnapPriorityOnly, q=True, v=True)
            AnimFunctions(filterSettings=self.filterSettings, matchMethod=self.matchMethod).snapTransform(nodes=self.__validate_roots(), **self.kws)
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
        step = cmds.floatFieldGrp(self.uiffgStabStep, q=True, v=True)[0]
        if direction == 'back':
            step = -step
        if cmds.checkBox(self.uicbStabRange, q=True, v=True):
            time = timeLineRangeGet()
        AnimFunctions.stabilizer(cmds.ls(sl=True, l=True), time, step,
                                 cmds.checkBox(self.uicbStabTrans, q=True, v=True),
                                 cmds.checkBox(self.uicbStabRots, q=True, v=True))

    def __TimeOffset(self):
        '''
        Internal UI call for TimeOffset
        '''
        offset = cmds.floatFieldGrp(self.uiffgTimeOffset, q=True, v=True)[0]
        self.kws['ripple'] = cmds.checkBox(self.uicbTimeOffsetRipple, q=True, v=True)
        if cmds.checkBox(self.uicbTimeOffsetRange, q=True, v=True):
            self.kws['timerange'] = timeLineRangeGet()
        if cmds.checkBox(self.uicbTimeOffsetStartfrm, q=True, en=True):
                self.kws['startfrm'] = cmds.checkBox(self.uicbTimeOffsetStartfrm, q=True, v=True)

        # process scene or fromSelected modes
        if cmds.checkBox(self.uicbTimeOffsetScene, q=True, v=True):
            r9Core.TimeOffset.fullScene(offset, cmds.checkBox(self.uicbTimeOffsetPlayback, q=True, v=True), **self.kws)
        else:
            self.kws['flocking'] = cmds.checkBox(self.uicbTimeOffsetFlocking, q=True, v=True)
            self.kws['randomize'] = cmds.checkBox(self.uicbTimeOffsetRandom, q=True, v=True)
            if cmds.checkBox(self.uicbTimeOffsetHierarchy, q=True, v=True):
                r9Core.TimeOffset.fromSelected(offset, filterSettings=self.filterSettings, mRigs=self.filterSettings.metaRig, **self.kws)
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
                nodes = Filter.processFilter()
                log.info('=============  Filter Test Results  ==============')
                print('\n'.join([node for node in nodes]))
                log.info('FilterTest : Object Count Returned : %s' % len(nodes))
                cmds.select(nodes)
            except:
                raise StandardError('Filter Returned Nothing')
        else:
            raise StandardError('No Root Node selected for Filter Testing')

    def __PoseSave(self, path=None, storeThumbnail=True):
        '''
        Internal UI call for PoseLibrary Save func, note that filterSettings is bound
        but only filled by the main __uiCall call
        '''
        # test the code behaviour under Project mode
        if not self.__validatePoseFunc('PoseSave'):
            return
        if not path:
            try:
                path = self.__uiCB_savePosePath()
            except ValueError, error:
                raise ValueError(error)

        poseHierarchy = cmds.checkBox(self.uicbPoseHierarchy, q=True, v=True)

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
        poseHierarchy = cmds.checkBox(self.uicbPoseHierarchy, q=True, v=True)
        poseRelative = cmds.checkBox(self.uicbPoseRelative, q=True, v=True)
        maintainSpaces = cmds.checkBox(self.uicbPoseSpace, q=True, v=True)
        rotRelMethod = cmds.radioCollection(self.uircbPoseRotMethod, q=True, select=True)
        tranRelMethod = cmds.radioCollection(self.uircbPoseTranMethod, q=True, select=True)

        if poseRelative and not cmds.ls(sl=True, l=True):
            log.warning('No node selected to use for reference!!')
            return

        relativeRots = 'projected'
        relativeTrans = 'projected'
        if not rotRelMethod == 'rotProjected':
            relativeRots = 'absolute'
        if not tranRelMethod == 'tranProjected':
            relativeTrans = 'absolute'

        path = self.getPosePath()
        log.info('PosePath : %s' % path)
        poseNode = r9Pose.PoseData(self.filterSettings)
        poseNode.prioritySnapOnly = cmds.checkBox(self.uicbSnapPriorityOnly, q=True, v=True)
        poseNode.matchMethod = self.matchMethod

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

        pb = r9Pose.PoseBlender(filepaths=[self.getPosePath()],
                              nodes=self.__uiCB_getPoseInputNodes(),
                              filterSettings=self.filterSettings,
                              useFilter=cmds.checkBox(self.uicbPoseHierarchy, q=True, v=True),
                              matchMethod=self.matchMethod)
        pb.show()

    def __PosePointCloud(self, func):
        '''
        .. note::
            this is dependent on EITHER a wire from the root of the pose to a GEO
            under the attr 'renderMeshes' OR the second selected object is the reference Mesh
            Without either of these you'll just get a locator as the PPC root
        '''
        objs = cmds.ls(sl=True)
        meshes = []
        mRef = r9Meta.MetaClass(self.__uiCB_getPoseInputNodes())
        if mRef.hasAttr('renderMeshes') and mRef.renderMeshes:
            meshes = mRef.renderMeshes
        elif len(objs) == 2:
            if cmds.nodeType(cmds.listRelatives(objs[1])[0]) == 'mesh':
                meshes = objs

        if func == 'make':
            if not objs:
                raise StandardError('you need to select a reference object to use as pivot for the PPCloud')
            rootReference = objs[0]
            if not meshes:
                # turn on locator visibility
                panel = cmds.getPanel(wf=True)
                if 'modelPanel' in panel:
                    cmds.modelEditor(cmds.getPanel(wf=True), e=True, locators=True)
                else:
                    cmds.modelEditor('modelPanel4', e=True, locators=True)
            self.ppc = r9Pose.PosePointCloud(self.__uiCB_getPoseInputNodes(),
                                             self.filterSettings,
                                             meshes=meshes)
            self.ppc.prioritySnapOnly = cmds.checkBox(self.uicbSnapPriorityOnly, q=True, v=True)
            self.ppc.buildOffsetCloud(rootReference)
            return
        # sync current instance
        if not hasattr(self, 'ppc') or not self.ppc:
            current = r9Pose.PosePointCloud.getCurrentInstances()
            if current:
                self.ppc = r9Pose.PosePointCloud(self.__uiCB_getPoseInputNodes(),
                                                 self.filterSettings,
                                                 meshes=meshes)
                self.ppc.syncdatafromCurrentInstance()
        # process current intance
        if self.ppc:
            if func == 'delete':
                self.ppc.delete()
            elif func == 'snap':
                self.ppc.applyPosePointCloud()
            elif func == 'update':
                self.ppc.updatePosePointCloud()

    def __MirrorPoseAnim(self, process, mirrorMode, side=None):
        '''
        Internal UI call for Mirror Animation / Pose

        :param process: mirror or symmetry
        :param mirrorMode: Anim or Pose
        '''
        nodes = cmds.ls(sl=True, l=True)
        if not nodes:
            log.warning('Nothing selected to process from!!')
            return

#         self.kws['pasteKey'] = cmds.optionMenu('om_PasteMethod', q=True, v=True)
        self.kws['pasteKey'] = 'replaceCompletely'  # replaced 25/02/20
        hierarchy = cmds.checkBox(self.uicbMirrorHierarchy, q=True, v=True)

        if hierarchy:
            nodes = self.__validate_roots()
        mirror = MirrorHierarchy(nodes=nodes,
                                     filterSettings=self.filterSettings,
                                     **self.kws)

        # Check for AnimLayers and throw the warning
        if mirrorMode == 'Anim':
            # slower as we're processing the mirrorSets twice for hierarchy
            # BUT this is vital info that the user needs prior to running.
            if hierarchy:
                animCheckNodes = mirror.getMirrorSets()
            else:
                animCheckNodes = nodes
            print(animCheckNodes)
            if not animLayersConfirmCheck(animCheckNodes):
                log.warning('Process Aborted by User')
                return

        if not hierarchy:
            if process == 'mirror':
                mirror.mirrorData(nodes, mode=mirrorMode)
            else:
                mirror.makeSymmetrical(nodes, mode=mirrorMode, primeAxis=side)
        else:
            if process == 'mirror':
                mirror.mirrorData(mode=mirrorMode)
            else:
                mirror.makeSymmetrical(mode=mirrorMode, primeAxis=side)

    # MAIN CALL
    # ------------------------------------------------------------------------------
    def __uiCall(self, func, *args):
        '''
        MAIN ANIMATION UI CALL
        Why not just call the procs directly? well this also manages the collection /pushing
        of the filterSettings data for all procs
        '''
        # issue : up to v2011 Maya puts each action into the UndoQueue separately
        # when called by lambda or partial - Fix is to open an UndoChunk to catch
        # everything in one block
        objs = cmds.ls(sl=True, l=True)
        self.kws = {}

        # If below 2011 then we need to store the undo in a chunk
        if r9Setup.mayaVersion() < 2011:
            cmds.undoInfo(openChunk=True)

        # Main Hierarchy Filters =============
        self.__uiPresetFillFilter()  # fill the filterSettings Object
        self.matchMethod = cmds.optionMenu('om_MatchMethod', q=True, v=True)

        # self.filterSettings.transformClamp = True

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
            elif func == 'MirrorAnim':
                self.__MirrorPoseAnim('mirror', 'Anim')
            elif func == 'MirrorPose':
                self.__MirrorPoseAnim('mirror', 'Pose')
            elif func == 'SymmetryPose_LR':
                self.__MirrorPoseAnim('symmetry', 'Pose', 'Left')
            elif func == 'SymmetryAnim_LR':
                self.__MirrorPoseAnim('symmetry', 'Anim', 'Left')
            elif func == 'SymmetryPose_RL':
                self.__MirrorPoseAnim('symmetry', 'Pose', 'Right')
            elif func == 'SymmetryAnim_RL':
                self.__MirrorPoseAnim('symmetry', 'Anim', 'Right')
        except r9Setup.ProPack_Error:
            log.warning('ProPack not Available')
        except StandardError, error:
            traceback = sys.exc_info()[2]  # get the full traceback
            raise StandardError(StandardError(error), traceback)
        if objs and not func == 'HierarchyTest':
            cmds.select(cl=True)
            for obj in objs:
                if cmds.objExists(obj):
                    cmds.select(objs, add=True)
        # close chunk
        if mel.eval('getApplicationVersionAsFloat') < 2011:
            cmds.undoInfo(closeChunk=True)

        self.__uiCache_storeUIElements()


# ===========================================================================
# Main AnimFunction code class
# ===========================================================================

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

    .. note::
        filterSettings is also now bound to the class and if no filterSettings object
        is passed into any of the calls we use the classes instance instead. Makes coding
        a lot more simple as you can take an instance of AnimFunctions and just fill it
        directly before running the functions.

    >>> # new functionality
    >>> animFunc=AnimFunctions()
    >>> animFunc.settings.nodeTypes=['nurbsCurve']
    >>> animFunc.settings.searchPattern=['ctrl']
    >>> animFunc.copyKeys([srcRootNode, destRootNode])
    >>>
    >>> # old functionality
    >>> settings=r9Core.FilterSettings()
    >>> settings.nodeTypes=['nurbsCurve']
    >>> settings.searchPattern=['ctrl']
    >>> animFunc.copyKeys([srcRootNode, destRootNode], filterSettigns=settings)

    '''
    def __init__(self, filterSettings=None, **kws):

        kws.setdefault('matchMethod', 'stripPrefix')
        self.matchMethod = kws['matchMethod']  # gives you the ability to modify the nameMatching method

        # make sure we have a settings object
        if filterSettings:
            if issubclass(type(filterSettings), r9Core.FilterNode_Settings):
                self.settings = filterSettings
            else:
                raise StandardError('filterSettings param requires an r9Core.FilterNode_Settings object')
            self.settings.printSettings()
        else:
            self.settings = r9Core.FilterNode_Settings()

    # ===========================================================================
    # Copy Keys
    # ===========================================================================

    def copyKeys_ToMultiHierarchy(self, nodes=None, time=(), pasteKey='replace',
                 attributes=None, filterSettings=None, matchMethod=None, mergeLayers=True, **kws):
        '''
        This isn't the best way by far to do this, but as a quick wrapper
        it works well enough. Really we need to process the nodes more intelligently
        prior to sending data to the copyKeys calls
        '''

        # this is so it carries on the legacy behaviour where these are always passed in
        if not filterSettings:
            filterSettings = self.settings
        if not matchMethod:
            matchMethod = self.matchMethod

        for node in nodes[1:]:
            self.copyKeys(nodes=[nodes[0], node],
                          time=time,
                          attributes=attributes,
                          pasteKey=pasteKey,
                          filterSettings=filterSettings,
                          toMany=False,
                          matchMethod=matchMethod,
                          mergeLayers=mergeLayers)

    # @r9General.Timer
    def copyKeys(self, nodes=None, time=(), pasteKey='replace', attributes=None,
                 filterSettings=None, toMany=False, matchMethod=None, mergeLayers=False, timeOffset=0, **kws):
        '''
        Copy Keys is a Hi-Level wrapper function to copy animation data between
        filtered nodes, either in hierarchies or just selected pairs.

        :param nodes: List of Maya nodes to process. This combines the filterSettings
            object and the MatchedNodeInputs.processMatchedPairs() call,
            making it capable of powerful hierarchy filtering and node matching methods.
        :param filterSettings: Passed into the FilterNode code to setup the hierarchy filters
            see docs on the FilterNode_Settings class'
            Note that this is also now bound to the class instance and if not passed in
            we use this classes instance of filterSettings cls.settings
        :param pasteKey: Uses the standard pasteKey option methods - merge,replace,
            insert etc. This is fed to the internal pasteKey method. Default=replace
        :param time: Copy over a given timerange - time=(start,end). Default is
            to use no timeRange. If time is passed in via the timeLineRange() function
            then it will consider the current timeLine PlaybackRange, OR if you have a
            highlighted range of time selected(in red) it'll use this instead.
        :param attributes: Only copy the given attributes[]
        :param matchMethod: arg passed to the match code, sets matchMethod used to match 2 node names, see r9Core.matchNodeLists for details
        :param mergeLayers: this pre-processes animLayers so that we have a single, temporary merged
            animLayer to extract a compiled version of the animData from. This gets deleted afterwards.

        TODO: this needs to support 'skipAttrs' param like the copyAttrs does - needed for the snapTransforms calls
        '''

        # this is so it carries on the legacy behaviour where these are always passed in
        if not filterSettings:
            filterSettings = self.settings
        if not matchMethod:
            matchMethod = self.matchMethod

        if logging_is_debug():
            log.debug('CopyKey params : \n \
 \tnodes=%s \t\n:time=%s \t\n: pasteKey=%s \t\n: attributes=%s \t\n: filterSettings=%s \t\n: matchMethod=%s \t\n: mergeLayers=%s \t\n: timeOffset=%s'
                    % (nodes, time, pasteKey, attributes, filterSettings, matchMethod, mergeLayers, timeOffset))

        # Build up the node pairs to process
        nodeList = r9Core.processMatchedNodes(nodes,
                                              filterSettings,
                                              toMany,
                                              matchMethod=matchMethod).MatchedPairs

        srcNodes = [src for src, _ in nodeList]

        # Manage AnimLayers - note to Autodesk, this should be internal to the cmds!
        with AnimationLayerContext(srcNodes, mergeLayers=mergeLayers, restoreOnExit=True):
            if nodeList:
                with r9General.HIKContext([d for _, d in nodeList]):
                    for src, dest in nodeList:
                        try:
                            if logging_is_debug():
                                log.debug('copyKeys : %s > %s' % (r9Core.nodeNameStrip(dest),
                                                                    r9Core.nodeNameStrip(src)))
                            if attributes:
                                # copy only specific attributes
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

    # ===========================================================================
    # Copy Attributes
    # ===========================================================================

    def copyAttrs_ToMultiHierarchy(self, nodes=None, attributes=None, skipAttrs=None,
                       filterSettings=None, matchMethod=None, **kws):
        '''
        This isn't the best way by far to do this, but as a quick wrapper
        it works well enough. Really we need to process the nodes more intelligently
        prior to sending data to the copyKeys calls
        '''
        # this is so it carries on the legacy behaviour where these are always passed in
        if not filterSettings:
            filterSettings = self.settings
        if not matchMethod:
            matchMethod = self.matchMethod

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
        :param filterSettings: Passed into the FilterNode code to setup the hierarchy filters
            see docs on the FilterNode_Settings class'
            Note that this is also now bound to the class instance and if not passed in
            we use this classes instance of filterSettings cls.settings
        :param attributes: Only copy the given attributes[]
        :param skipAttrs: Copy all Settable Attributes OTHER than the given, not
            used if an attributes list is passed
        :param matchMethod: arg passed to the match code, sets matchMethod used to match 2 node names, see r9Core.matchNodeLists for details

        '''
        if not matchMethod:
            matchMethod = self.matchMethod
        # this is so it carries on the legacy behaviour where these are always passed in
        if not filterSettings:
            filterSettings = self.settings

#         log.debug('CopyAttributes params : nodes=%s\n : attributes=%s\n : filterSettings=%s\n : matchMethod=%s\n'
#                    % (nodes, attributes, filterSettings, matchMethod))

        # build up the node pairs to process
        nodeList = r9Core.processMatchedNodes(nodes,
                                              filterSettings,
                                              toMany,
                                              matchMethod=matchMethod).MatchedPairs

        if nodeList:
            with r9General.HIKContext([d for _, d in nodeList]):
                for src, dest in nodeList:
                    try:
                        if attributes:
                            # copy only specific attributes
                            for attr in attributes:
                                if cmds.attributeQuery(attr, node=src, exists=True) \
                                    and cmds.attributeQuery(attr, node=dest, exists=True):
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
                                        if logging_is_debug():
                                            log.debug('copyAttr : %s.%s > %s.%s' % (r9Core.nodeNameStrip(dest),
                                                                            r9Core.nodeNameStrip(attr),
                                                                            r9Core.nodeNameStrip(src),
                                                                            r9Core.nodeNameStrip(attr)))
                                        cmds.setAttr('%s.%s' % (dest, attr), cmds.getAttr('%s.%s' % (src, attr)))
                                    except:
                                        if logging_is_debug():
                                            log.debug('failed to copyAttr : %s.%s > %s.%s' % (r9Core.nodeNameStrip(dest),
                                                                            r9Core.nodeNameStrip(attr),
                                                                            r9Core.nodeNameStrip(src),
                                                                            r9Core.nodeNameStrip(attr)))
                    except:
                        pass
        else:
            raise StandardError('Nothing found by the Hierarchy Code to process')
        return True

    # ===========================================================================
    # Transform Snapping
    # ===========================================================================

    # @r9General.Timer
#     @r9General.evalManager_idleAction
    def snapTransform(self, nodes=None, time=(), step=1, preCopyKeys=1, preCopyAttrs=1, filterSettings=None,
                      iterations=1, matchMethod=None, prioritySnapOnly=False, snapRotates=True, snapTranslates=True, 
                      snapScales=False, additionalCalls=[], cutkeys=False, smartbake=False, smartBakeRef=[], additionalCalls_pre=[], **kws):
        '''
        Snap objects over a timeRange. This wraps the default hierarchy filters
        so it's capable of multiple hierarchy filtering and matching methods.
        The resulting node lists are snapped over time and keyed.
        :requires: SnapRuntime plugin to be available

        :param nodes: List of Maya nodes to process. This combines the filterSettings
            object and the MatchedNodeInputs.processMatchedPairs() call,
            making it capable of powerful hierarchy filtering and node matching methods.
        :param filterSettings: Passed into the FilterNode code to setup the hierarchy filters
            see docs on the FilterNode_Settings class'
            Note that this is also now bound to the class instance and if not passed in
            we use this classes instance of filterSettings cls.settings
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
        :param matchMethod: arg passed to the match code, sets matchMethod used to match 2 node names, see r9Core.matchNodeLists for details
        :param prioritySnapOnly: if True ONLY snap the nodes in the filterPriority list within the filterSettings object = Super speed up!!
        :param snapTranslates: only snap the translate data
        :param snapRotates: only snap the rotate data
        :param snapScales: testing, match the scales but only in local space
        :param additionalCalls: [func, func...] additional functions to run AFTER the snap call during process... allowing you
            to add in specific matching calls to a SnapTransforms run whilst having the time increment correctly managed for you
        :param additionalCalls_pre:  [func, func...] additional functions to run BEFORE the snap call during process... allowing you
            to add in specific matching calls to a SnapTransforms run whilst having the time increment correctly managed for you
        :param cutkeys: when passing time do we clear current keys first, needed ideally if we're running with a step greater than 1
        :param smartbake: if True we ignore the step and find all current keyTimes on the nodes about to be processed, these key times
            are then respected during the process
        :param smartBakeRef: smartbake=True if given, used as reference nodes to extract keytimes from, else we look at all nodes about to be
            processed which isn't always what we want. If we still find no keytimes we revert to base range times with step given

        .. note::
            you can also pass the CopyKey kws in to the preCopy call, see copyKeys above

        .. note::
            by default when using the preCopyKeys flag we run a temp merge of any animLayers
            and copy that merged animLayer data for consistency. The layers are restored afterwards

        '''
        self.snapCacheData = {}  # TO DO - Cache the data and check after first run data is all valid
        self.nodesToSnap = []
        _smartBake_nodekeys = {}
        _smartBakeRef = list(smartBakeRef)  # so we don't mutate the input arg (pass by reference issues)
        # cutkeys = False

        # new management of the AnimContext to deal with 2019+
        eval_mode = 'static'
        if time:
            eval_mode = 'anim'

        # this is so it carries on the legacy behaviour where these are always passed in
        if not filterSettings:
            filterSettings = self.settings
        if not matchMethod:
            matchMethod = self.matchMethod

        if _smartBakeRef:
            smartbake = True
        if time and not type(time) == tuple:
            time = tuple(time)
        _keyed_attrs = []
        if snapTranslates:
            _keyed_attrs.extend(['tx', 'ty', 'tz'])
        if snapRotates:
            _keyed_attrs.extend(['rx', 'ry', 'rz'])
        if snapScales:
            _keyed_attrs.extend(['sx', 'sy', 'sz'])
        skipAttrs = ['translateX', 'translateY', 'translateZ', 'rotateX', 'rotateY', 'rotateZ', 'scaleX', 'scaleY', 'scaleZ']

        try:
            checkRunTimeCmds()
        except StandardError, error:
            raise StandardError(error)
        cancelled = False

        if logging_is_debug():
            log.debug('snapTransform params : nodes=%s : time=%s : step=%s : preCopyKeys=%s : \
                    preCopyAttrs=%s : filterSettings=%s : matchMethod=%s : prioritySnapOnly=%s : snapTransforms=%s : snapRotates=%s : snapScales=%s'
                       % (nodes, time, step, preCopyKeys, preCopyAttrs, filterSettings, matchMethod, prioritySnapOnly, snapTranslates, snapRotates, snapScales))

        # build up the node pairs to process
        nodeList = r9Core.processMatchedNodes(nodes, filterSettings, matchMethod=matchMethod)

        if nodeList.MatchedPairs:
            nodeList.MatchedPairs.reverse()  # reverse order so we're dealing with children before their parents
            # if prioritySnap then we snap align ONLY those nodes that
            # are in the filterSettings priority list. VAST speed increase
            # by doing this. If the list is empty we revert to turning the flag off
            if prioritySnapOnly and filterSettings.filterPriority:
                for pNode in filterSettings.filterPriority:
                    for src, dest in nodeList.MatchedPairs:
                        if re.search(pNode, r9Core.nodeNameStrip(dest)):
                            self.nodesToSnap.append((src, dest))
                skipAttrs = []  # reset as we need to now copy all attrs (mainly for sub nodes that aren't snapped)
            else:
                self.nodesToSnap = nodeList.MatchedPairs

            # smartbake handling - accumulate key data per node
            if smartbake and time:
                cutkeys = True
                if not _smartBakeRef:
                    for node in self.nodesToSnap:
                        _smartBakeRef.extend(node)  # have to take both as the src may have no keys, it may be driven
                for node in _smartBakeRef:
                    _keys = timeLineRangeProcess(time[0], time[1], step, incEnds=True, nodes=node)
                    if _keys:
                        _smartBake_nodekeys[node] = _keys
                if not _smartBakeRef:
                    raise IOError("ABORTED : SmartBake couldn't find any reference nodes with keys to base the data on!")

            # Primary AnimContext Manager to deal with EM / Cache settings
            with r9General.AnimationContext(eval_mode=eval_mode, timerange=time):
                if preCopyAttrs:
                    self.copyAttributes(nodes=nodeList, skipAttrs=skipAttrs, filterSettings=filterSettings, **kws)
                if time:
                        cmds.autoKeyframe(state=False)
                        # run a copyKeys pass to take all non transform data over
                        # maybe do a channel attr pass to get non-keyed data over too?
                        if preCopyKeys:
                            self.copyKeys(nodes=nodeList, time=time, filterSettings=filterSettings, **kws)

                        progressBar = r9General.ProgressBarContext(maxValue=time[1] - time[0], step=step, ismain=True)
                        
                        # grab the frms BEFORE we cut the keys in-case the nodes to process are part of the _smartbake list
                        keytimes = timeLineRangeProcess(time[0], time[1], step, incEnds=True, nodes=_smartBakeRef)

                        if cutkeys:
                            for _, dest in self.nodesToSnap:
                                # print 'cutting keys : ', time, dest
                                if snapTranslates:
                                    cmds.cutKey(dest, at='translate', time=time)
                                if snapRotates:
                                    cmds.cutKey(dest, at='rotate', time=time)
                                if snapScales:
                                    cmds.cutKey(dest, at='scale', time=time)

                        with progressBar:
                            for t in keytimes:  # timeLineRangeProcess(time[0], time[1], step, incEnds=True, nodes=_smartBakeRef):
                                if progressBar.isCanceled():
                                    cancelled = True
                                    break

                                dataAligned = False
                                processRepeat = iterations

                                # we'll use the API MTimeControl in the runtime function
                                # to update the scene without refreshing the Viewports
                                cmds.currentTime(t, e=True, u=False)

                                while not dataAligned:
                                    # PRE-SNAP additional calls
                                    if additionalCalls_pre:
                                        for func in additionalCalls_pre:
                                            log.debug('Additional Pre-Snap Func Called : %s' % func)
                                            func()

                                    for src, dest in self.nodesToSnap:
                                        # verify the src node has a key at the given accumulated keytime (if smartbake)
                                        if _smartBake_nodekeys and src in _smartBake_nodekeys.keys() and t not in _smartBake_nodekeys[src]:
                                            if logging_is_debug():
                                                log.debug('skipping time : %s : node : %s' % (t, r9Core.nodeNameStrip(src)))
                                        else:
#                                             cmds.matchTransform(src, dest, pos=snapTranslates, rot=snapRotates, scl=snapScales)  # still not an option
                                            try:
                                                cmds.SnapTransforms(source=src, destination=dest,
                                                                    timeEnabled=True,
    #                                                                 time=t,
                                                                    snapRotates=snapRotates,
                                                                    snapTranslates=snapTranslates,
                                                                    snapScales=snapScales)
                                                cmds.setKeyframe(dest, at=_keyed_attrs)
    
                                                if logging_is_debug():
                                                    log.debug('Snapfrm %s : source(%s) >> target(%s) ::  %s to %s' % (str(t),
                                                                                                                      r9Core.nodeNameStrip(src),
                                                                                                                      r9Core.nodeNameStrip(dest),
                                                                                                                      dest,
                                                                                                                      src))
                                            except Exception as err:
                                                if logging_is_debug():
                                                    log.debug('Snapfrm FAILED : %s : source(%s) >> target(%s) ::  %s to %s' % (str(t),
                                                                                                                      r9Core.nodeNameStrip(src),
                                                                                                                      r9Core.nodeNameStrip(dest),
                                                                                                                      dest,
                                                                                                                      src))
                                                    log.debug(traceback.format_exc())
                                    # standard POST-SNAP additional calls
                                    if additionalCalls:
                                        for func in additionalCalls:
                                            log.debug('Additional Func Called : %s' % func)
                                            func()

                                    processRepeat -= 1
                                    if not processRepeat:
                                        dataAligned = True
                                progressBar.updateProgress()
                else:
                    for _ in range(0, iterations):
                        # PRE-SNAP additional calls
                        if additionalCalls_pre:
                            for func in additionalCalls_pre:
                                log.debug('Additional Pre-Snap Func Called : %s' % func)
                                func()
                        for src, dest in self.nodesToSnap:  # nodeList.MatchedPairs:
                            cmds.SnapTransforms(source=src, destination=dest,
                                                timeEnabled=False,
                                                snapRotates=snapRotates,
                                                snapTranslates=snapTranslates,
                                                snapScales=snapScales)
                            if logging_is_debug():
                                log.debug('Snapfrm : source(%s) >> target(%s) :: %s to %s' % (r9Core.nodeNameStrip(src),
                                                                                              r9Core.nodeNameStrip(dest),
                                                                                              dest, src))
                        # standard POST-SNAP additional calls
                        if additionalCalls:
                            for func in additionalCalls:
                                log.debug('Additional Func Called : %s' % func)
                                func()
                            # self.snapCacheData[dest]=data
                            if logging_is_debug():
                                log.debug('Snapped : source(%s) >> target(%s) :: %s to %s' % (r9Core.nodeNameStrip(src),
                                                                                              r9Core.nodeNameStrip(dest),
                                                                                              dest, src))

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
    def snap(nodes=None, snapTranslates=True, snapRotates=True, snapScales=False, *args, **kws):
        '''
        This takes 2 given transform nodes and snaps them together. It takes into
        account offsets in the pivots of the objects. Uses the API MFnTransform nodes
        to calculate the data via a command plugin. This is a stripped down version
        of the snapTransforms cmd

        :param nodes: [src,dest]
        :param snapTranslates: snap the translate data
        :param snapRotates: snap the rotate data
        :param snapScales: snap the scale, this is LOCAL transforms only
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

        # pass to the plugin SnapCommand
        for node in nodes[1:]:
            cmds.SnapTransforms(source=nodes[0],
                                destination=node,
                                snapTranslates=snapTranslates,
                                snapRotates=snapRotates,
                                snapScales=snapScales,
                                timeEnabled=False)

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
        :param trans: track translates
        :param rots: track rotates
        '''
        # destObj = None  #Main Object being manipulated and keyed
        # snapRef = None  #Tracking ReferenceObject Used to Pass the transforms over
        deleteMe = []
        duration = step
        timeRange = []

        _keyed_attrs = []
        if trans:
            _keyed_attrs.extend(['tx', 'ty', 'tz'])
        if rots:
            _keyed_attrs.extend(['rx', 'ry', 'rz'])
        try:
            checkRunTimeCmds()
        except StandardError, error:
            raise StandardError(error)

        eval_mode = 'static'
        if time:
            eval_mode = 'anim'

        with r9General.AnimationContext(eval_mode=eval_mode, time=False):  # , cached_eval=False):
            if time:
                timeRange = timeLineRangeProcess(time[0], time[1], step, incEnds=True)  # this is a LIST of frames
                cmds.currentTime(timeRange[0], e=True)  # ensure that the initial time is updated
                duration = time[1] - time[0]
                log.debug('timeRange : %s', timeRange)

            if not nodes:
                nodes = cmds.ls(sl=True, l=True)

            destObj = nodes[-1]
            snapRef = cmds.createNode('transform', ss=True)
            deleteMe.append(snapRef)

            try:
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

                if time:
                    # Now run the snap against the reference node we've just made
                    # ==========================================================
                    progressBar = r9General.ProgressBarContext(duration, step=step, ismain=True)
                    with progressBar:
                        for time in timeRange:
                            if progressBar.isCanceled():
                                break
                            # Switched to using the Commands time query to stop  the viewport updates
                            cmds.currentTime(time, e=True, u=False)
                            cmds.SnapTransforms(source=snapRef, destination=destObj, timeEnabled=True, snapTranslates=trans, snapRotates=rots)
                            try:
                                cmds.setKeyframe(destObj, at=_keyed_attrs)
                            except:
                                log.debug('failed to set full keydata on %s' % destObj)
                            progressBar.updateProgress()
                else:
                    cmds.currentTime(cmds.currentTime(q=True) + step, e=True, u=False)
                    cmds.SnapTransforms(source=snapRef, destination=destObj, timeEnabled=True, snapTranslates=trans, snapRotates=rots)
                    try:
                        cmds.setKeyframe(destObj, at=_keyed_attrs)
                    except:
                        log.debug('failed to set full keydata on %s' % destObj)
            except StandardError, err:
                log.warning('Stabilizer Error %s' % err)
            finally:
                cmds.delete(deleteMe)
#                 cmds.select(nodes)

    def bindNodes(self, nodes=None, attributes=None, attributes_all_settable=False, filterSettings=None, bindMethod='connect',
                  matchMethod=None, manage_scales=False, unlock=False, **kws):
        '''
        bindNodes is a Hi-Level wrapper function to bind animation data between
        filtered nodes, either in hierarchies or just selected pairs. This has been uplifted to sync
        to the ProPack bind call for clarity

        :param nodes: List of Maya nodes to process. This combines the filterSettings
            object and the MatchedNodeInputs.processMatchedPairs() call,
            making it capable of powerful hierarchy filtering and node matching methods.
        :param filterSettings: Passed into the FilterNode code to setup the hierarchy filters
            see docs on the FilterNode_Settings class'
            Note that this is also now bound to the class instance and if not passed in
            we use this classes instance of filterSettings cls.settings
        :param attributes: Only process the given attributes[]
        :param attributes_all_settable: if True and bindMethod='connect' we process ALL settable channels on each node
        :param bindMethod: method of binding the data
        :param matchMethod: arg passed to the match code, sets matchMethod used to match 2 node names, see r9Core.matchNodeLists for details
        :param manage_scales: bool, do we also look at binding jnt scales where applicable, this only runs
            if the source jnt has incoming scale connections which would then be propagated via a scaleConstrain
        :param unlock: if True force unlock the required transform attrs on the destination skeleton first

        TODO: expose this to the UI's!!!!
        '''

        # this is so it carries on the legacy behaviour where these are always passed in
        if not filterSettings:
            filterSettings = self.settings
        if not matchMethod:
            matchMethod = self.matchMethod

        if logging_is_debug():
            log.debug('bindNodes params : nodes=%s : attributes=%s : filterSettings=%s : matchMethod=%s'
                       % (nodes, attributes, filterSettings, matchMethod))
         
        if not attributes:
            attributes = ['rotateX', 'rotateY', 'rotateZ', 'translateX', 'translateY', 'translateZ']
        if manage_scales:
            attributes.extend(['scaleX', 'scaleY', 'scaleZ', 'inverseScale'])


        # Build up the node pairs to process
        nodeList = r9Core.processMatchedNodes(nodes,
                                              filterSettings,
                                              toMany=False,
                                              matchMethod=matchMethod).MatchedPairs
        if nodeList:
            # bulk unlock the required attrs if unlock flag set
            if unlock:
                r9Core.LockChannels().processState([dest for src, dest in nodeList], attrs=attributes, mode='fullkey', hierarchy=True)

            for src, dest in nodeList:
                try:
                    if bindMethod == 'connect':
                        if attributes_all_settable:
                            _attributes = attributes + getSettableChannels(src, incStatics=False)
                        else:
                            _attributes = attributes
                        # Bind only specific attributes
                        for attr in _attributes:
                            log.info('Attr %s bindNode from %s to>> %s' % (attr, r9Core.nodeNameStrip(src),
                                                                          r9Core.nodeNameStrip(dest)))
                            try:
                                cmds.connectAttr('%s.%s' % (src, attr), '%s.%s' % (dest, attr), f=True)
                            except:
                                log.info('bindNode from %s to>> %s' % (r9Core.nodeNameStrip(src),
                                                                      r9Core.nodeNameStrip(dest)))
                    elif bindMethod == 'constraint':
                        try:
                            cmds.parentConstraint(src, dest, mo=True)
                        except:
                            chns = r9Anim.getSettableChannels(dest)
                            if all(['translateX' in chns, 'translateY' in chns, 'translateZ' in chns]):
                                cmds.pointConstraint(src, dest, mo=True)
                            elif all(['rotateX' in chns, 'rotateY' in chns, 'rotateZ' in chns]):
                                cmds.orientConstraint(src, dest, mo=True)
                            else:
                                log.info('Failed to Bind nodes: %s >> %s' % (src, dest))

                        # if we have incoming scale connections then run the scaleConstraint
                        if manage_scales and cmds.listConnections('%s.sx' % src):
                            try:
                                cmds.scaleConstraint(src, dest, mo=True)
                            except:
                                print('failed : scales ', dest)
                except:
                    pass
        else:
            raise StandardError('Nothing found by the Hierarchy Code to process')
        return True

    @staticmethod
    def inverseAnimChannels(node, channels=[], time=None):
        '''
        really basic method used in the Mirror calls
        '''
        if r9General.is_basestring(channels):
            channels = [channels]

        if not 'animCurve' in cmds.nodeType(node):
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
        if r9General.is_basestring(channels):
            channels = [channels]
        for chan in channels:
            try:
                cmds.setAttr('%s.%s' % (node, chan), cmds.getAttr('%s.%s' % (node, chan)) * -1)
            except:
                log.debug('failed to inverse %s.%s attr' % (node, chan))

    @staticmethod
    def inverseAnimCurves(nodes=None, curves=[], time=(), timePivot=None, mode='object', mRigs=False):
        '''
        really basic method to inverse anim curves for a given time, or for the current playback timerange

        :param nodes: nodes to find animCurves on IF curves were not specified directly
        :param curves: specific animCurves to act on, else we inspect the nodes given
        :param time: timerange to inverse, if not given we use the default timeLineRangeGet function as per
            all other Red9 timerange enabled calls
        :param timePivot: if given this is the pivot for the scale inverse, else we automatically work
            this out from the time ranges given
        :param mode: 'object' or 'keys' are we acting at the object level or at the selected keys level in the graphEditor?
            'object' is default
        :param mRigs: if we're in object mode then we modify the nodes to be all child members of linked mRig systems
        '''
        if not curves:
            if mode == 'object':
                if not nodes:
                    nodes = cmds.ls(sl=True, l=True)

                # New mrig section so that we can process rigs as entire entities for all the calls
                if mRigs:
                    _mrigs = []
                    for node in nodes:
                        mrig = r9Meta.getConnectedMetaSystemRoot(node)
                        if mrig and mrig not in _mrigs:
                            _mrigs.append(mrig)
                    if _mrigs:
                        nodes = []
                        for rig in _mrigs:
                            nodes.extend(rig.getChildren())

                if not curves:
                    curves = r9Core.FilterNode.lsAnimCurves(nodes, safe=True)
                if not time:
                    time = timeLineRangeGet()
            elif mode == 'keys':
                curves = cmds.keyframe(q=True, sl=True, n=True)
                if curves:
                    keys = sorted(cmds.keyframe(curves, sl=True, q=True, tc=True))
                    time = (keys[0], keys[-1])  # note the int conversion in case first key is on a sub-frame

        if not timePivot:
            timePivot = (float(time[0]) + float(time[1])) / 2

        if curves:
            log.info('AnimCurveInverse : timePivot=%f' % timePivot)
            if time:
                cmds.scaleKey(curves, timeScale=-1, timePivot=timePivot, time=time)
                log.info('AnimCurveInverse : time=(%s,%s)' % (time[0], time[1]))
            else:
                cmds.scaleKey(curves, timeScale=-1, timePivot=timePivot)
        else:
            log.warning('No Curves found or selected to act upon!')


class curveModifierContext(object):
    """
    Simple Context Manager to allow modifications to animCurves in the
    graphEditor interactively by simply managing the undo stack and making
    sure that selections are maintained
    NOTE that this is optimized to run with a floatSlider and used in both interactive
    Randomizer and FilterCurves
    """
    def __init__(self, initialUndo=False, undoFuncCache=[], undoDepth=1, processBlanks=False, reselectKeys=True, manageCache=True, undoChunkName='curveModifierContext'):
        '''
        :param initialUndo: on first process whether undo on entry to the context manager
        :param undoFuncCache: functions to catch in the undo stack
        :param undoDepth: depth of the undo stack to go to
        :param processBlanks: if undoFuncCache is empty but the last undoName is blank then we consider
            this a match and run the undo. Why, this is because it's bloody hard to get QT to register
            calls to the undo stack and that was blocking some of the ProPack functionality
        :param reselectKeys: if keys were selected on entry we reselect them based on their original timerange
        :param manageCache: Maya 2019 and above, manage the cache mode, stopping the fill mode from being 'syncAsync',
            this means that the cache is only filled on exit, if at all
        :param undoChunkName: name of the undoChunk created by this, default = 'curveModifierContext'
        '''
        self.initialUndo = initialUndo
        self.undoChunkName = undoChunkName
        self.undoFuncCache = undoFuncCache + [self.undoChunkName]
        self.undoDepth = undoDepth
        self.processBlanks = processBlanks
        self.reselectKeys = reselectKeys


#         self.cacheMode = None
#         if manageCache and r9Setup.mayaVersion() >= 2019:
#             self.cacheMode = cmds.cacheEvaluator(query=True, cacheFillMode=True)

    def undoCall(self):
        for _ in range(1, self.undoDepth + 1):
            # print 'undoCall stack : ', cmds.undoInfo(q=True, printQueue=True)
            if self.undoFuncCache:
                if [func for func in self.undoFuncCache if func in cmds.undoInfo(q=True, undoName=True)]:
                    # print func
                    cmds.undo()
            else:
                if self.processBlanks and not cmds.undoInfo(q=True, undoName=True):
                    # print 'processes blank func : '
                    cmds.undo()

    def __enter__(self):
        # turn the undo queue on if it's off
        if not cmds.undoInfo(q=True, state=True):
            cmds.undoInfo(state=True)
        if self.initialUndo:
            self.undoCall()
        cmds.undoInfo(openChunk=True, chunkName=self.undoChunkName)  # enter and create a named chunk

#         # manage the 2019 cache so we're not always filling it up on context drag
#         if self.cacheMode:
#             cmds.cacheEvaluator(cacheFillMode='syncOnly')

        self.range = None
        self.keysSelected = cmds.keyframe(q=True, n=True, sl=True)

        if self.keysSelected:
            self.range = cmds.keyframe(q=True, sl=True, timeChange=True)

    def __exit__(self, exc_type, exc_value, traceback):
        if self.reselectKeys and self.keysSelected and self.range:
            cmds.selectKey(self.keysSelected, t=(self.range[0], self.range[-1]))

#         if self.cacheMode:
#             cmds.cacheEvaluator(cacheFillMode=self.cacheMode)
#             print 'Cache Restored'

        cmds.undoInfo(closeChunk=True, chunkName=self.undoChunkName)
        if exc_type:
            log.exception('%s : %s' % (exc_type, exc_value))
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
        self.win = 'KeyRandomizerOptions'
        self.contextManager = curveModifierContext
        self.dragActive = False
        self.toggledState = False

        # catch the current state of the GrapthEditor so that the toggle respects it
        self.displayTangents = cmds.animCurveEditor('graphEditor1GraphEd', q=True, displayTangents=True)
        self.displayActiveKeyTangents = cmds.animCurveEditor('graphEditor1GraphEd', q=True, displayActiveKeyTangents=True)
        if cmds.animCurveEditor('graphEditor1GraphEd', q=True, showBufferCurves=True) == 'on':
            self.showBufferCurves = True
        else:
            self.showBufferCurves = False

    def noiseFunc(self, initialValue, randomRange, damp):
        '''
        really simple noise func, maybe I'll flesh this out at somepoint
        '''
        return initialValue + (random.uniform(randomRange[0], randomRange[1]) * damp)

    @classmethod
    def showOptions(cls):
        cls()._showUI()

    def _showUI(self):

            if cmds.window(self.win, exists=True):
                cmds.deleteUI(self.win, window=True)
            cmds.window(self.win, title=LANGUAGE_MAP._Randomizer_.title)  # , s=True, widthHeight=(320, 280))
            cmds.menuBarLayout()
            cmds.menu(l=LANGUAGE_MAP._Generic_.vimeo_menu)
            cmds.menuItem(l=LANGUAGE_MAP._Generic_.vimeo_help,
                          ann=LANGUAGE_MAP._Randomizer_.vimeo_randomizer_ann,
                          c="import Red9.core.Red9_General as r9General;r9General.os_OpenFile('https://vimeo.com/69270932')")
            # cmds.menuItem(divider=True)
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
            # cmds.checkBox('cb_rand_ignoreBounds',
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
                                    value=0,
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
            cmds.iconTextButton(style='iconAndTextHorizontal', bgc=(0.7, 0, 0), 
                                image1='Rocket9_buttonStrap_narrow.png',
                                align='left',
                                c=r9Setup.red9ContactInfo, h=24, w=275)
            cmds.separator(h=15, style='none')
            cmds.showWindow(self.win)
            cmds.window(self.win, e=True, widthHeight=(320, 280))
            self.__uicb_interactiveMode(False)
            self.__loadPrefsToUI()

            # set close event to restore stabndard GraphEditor curve status
            cmds.scriptJob(runOnce=True, uiDeleted=[self.win, lambda *x: animCurveDrawStyle(style='full', forceBuffer=False,
                                                                                      showBufferCurves=self.showBufferCurves,
                                                                                      displayTangents=self.displayTangents,
                                                                                      displayActiveKeyTangents=self.displayActiveKeyTangents)])

    def __uicb_setRanges(self, *args):
        cmds.floatSliderGrp('fsg_randfloatValue', e=True, maxValue=args[0])  # cmds.floatField('ffg_rand_intMax',q=True,v=True))

    def __uicb_toggleGraphDisplay(self, *args):
        if not self.toggledState:
            self.displayTangents = cmds.animCurveEditor('graphEditor1GraphEd', q=True, displayTangents=True)
            self.displayActiveKeyTangents = cmds.animCurveEditor('graphEditor1GraphEd', q=True, displayActiveKeyTangents=True)
            if cmds.animCurveEditor('graphEditor1GraphEd', q=True, showBufferCurves=True) == 'on':
                self.showBufferCurves = True
            else:
                self.showBufferCurves = False

            animCurveDrawStyle(style='simple', forceBuffer=True)
            self.toggledState = True
        else:
            animCurveDrawStyle(style='full', forceBuffer=False,
                                 showBufferCurves=self.showBufferCurves,
                                 displayTangents=self.displayTangents,
                                 displayActiveKeyTangents=self.displayActiveKeyTangents)
            self.toggledState = False

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

    def addNoise(self, curves, time=(), step=1, currentKeys=True, randomRange=[-1, 1], damp=1, percent=False, keepKeys=False):
        '''
        Simple noise function designed to add noise to keyframed animation data.

        :param curves: Maya animCurves to process
        :param time: timeRange to process
        :param step: frame step used in the processor
        :param currentKeys: ONLY randomize keys that already exists
        :param randomRange: range [upper, lower] bounds passed to teh randomizer
        :param damp: damping passed into the randomizer
        :param keepkeys: if True maintain current keys
        '''
        keyTimes = []
        if percent:
            damp = damp / 100
        if currentKeys:
            for curve in curves:
                # if keys/curves are already selected, process those only
                selectedKeys = cmds.keyframe(curve, q=True, vc=True, tc=True, sl=True)
                if selectedKeys:
                    keyData = selectedKeys
                else:
                    # else process all keys inside the time
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
                if keepKeys:
                    keyTimes = cmds.keyframe(curve, q=True)
                if percent:
                    # figure the upper and lower value bounds
                    randomRange = self.__calcualteRangeValue(cmds.keyframe(curve, q=True, vc=True, t=time))
                    log.debug('Percent data : randomRange=%f>%f, percentage=%f' % (randomRange[0], randomRange[1], damp))

                connection = [con for con in cmds.listConnections(curve, source=False, d=True, p=True)
                              if not cmds.nodeType(con) == 'hyperLayout'][0]

                for t in timeLineRangeProcess(time[0], time[1], step, incEnds=True):
                    if keepKeys:
                        if t in keyTimes:
                            continue
                    value = self.noiseFunc(cmds.getAttr(connection, t=t), randomRange, damp)
                    cmds.setKeyframe(connection, v=value, t=t)

    def curveMenuFunc(self, *args):
        self.__storePrefs()
        frmStep = 1
        damping = 1
        percent = False
        currentKeys = True

        if cmds.window(self.win, exists=True):
            currentKeys = cmds.checkBox('cb_rand_current', q=True, v=True)
            damping = cmds.floatFieldGrp('ffg_rand_damping', q=True, v1=True)
            frmStep = cmds.floatFieldGrp('ffg_rand_frmStep', q=True, v1=True)
            percent = cmds.checkBox('cb_rand_percent', q=True, v=True)
        else:
            if cmds.optionVar(exists='red9_randomizer_damp'):
                damping = cmds.optionVar(q='red9_randomizer_damp')
            if cmds.optionVar(exists='red9_randomizer_percent'):
                percent = cmds.optionVar(q='red9_randomizer_percent')
            if cmds.optionVar(exists='red9_randomizer_current'):
                currentKeys = cmds.optionVar(q='red9_randomizer_current')
            if cmds.optionVar(exists='red9_randomizer_frmStep'):
                frmStep = cmds.optionVar(q='red9_randomizer_frmStep')

        selectedCurves = cmds.keyframe(q=True, sl=True, n=True)
        if not selectedCurves:
            raise StandardError('No Keys or Anim curves selected!')

        self.addNoise(curves=selectedCurves,
                      step=frmStep,
                      damp=damping,
                      currentKeys=currentKeys,
                      percent=percent)


class FilterCurves(object):

    def __init__(self):
        self.win = LANGUAGE_MAP._CurveFilters_.title
        self.contextManager = curveModifierContext
        self.dragActive = False
        self.undoFuncCache = ['simplifyWrapper', 'snapAnimCurvesToFrms', 'resampleCurves']
        self.undoDepth = 1
        self.snapToFrame = False
        self.toggledState = False

        # cache the current state of the GrapthEditor so that the toggle respects it
        self.displayTangents = cmds.animCurveEditor('graphEditor1GraphEd', q=True, displayTangents=True)
        self.displayActiveKeyTangents = cmds.animCurveEditor('graphEditor1GraphEd', q=True, displayActiveKeyTangents=True)
        if cmds.animCurveEditor('graphEditor1GraphEd', q=True, showBufferCurves=True) == 'on':
            self.showBufferCurves = True
        else:
            self.showBufferCurves = False

    @classmethod
    def show(cls):
        cls()._showUI()

    def close(self):
        if cmds.window(self.win, exists=True):
            cmds.deleteUI(self.win, window=True)

    def _showUI(self):
        self.close()
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
                                # cc=self.snapAnimCurvesToFrms)  #set the dragActive state back to false on release
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
        cmds.iconTextButton(style='iconAndTextHorizontal', bgc=(0.7, 0, 0),
                            image1='Rocket9_buttonStrap.png',
                            c=r9Setup.red9ContactInfo,
                            align='left',
                            h=24, w=220)
        cmds.separator(h=20, style="none")
        cmds.showWindow(self.win)
        cmds.window(self.win, e=True, widthHeight=(410, 300))

        # set close event to restore standard GraphEditor curve status
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
            # cache the current state
            self.displayTangents = cmds.animCurveEditor('graphEditor1GraphEd', q=True, displayTangents=True)
            self.displayActiveKeyTangents = cmds.animCurveEditor('graphEditor1GraphEd', q=True, displayActiveKeyTangents=True)
            if cmds.animCurveEditor('graphEditor1GraphEd', q=True, showBufferCurves=True) == 'on':
                self.showBufferCurves = True
            else:
                self.showBufferCurves = False

            animCurveDrawStyle(style='simple', forceBuffer=True)
            self.toggledState = True
        else:
            animCurveDrawStyle(style='full', forceBuffer=False,
                               showBufferCurves=self.showBufferCurves,
                               displayTangents=self.displayTangents,
                               displayActiveKeyTangents=self.displayActiveKeyTangents)
            self.toggledState = False

    def __uicb_setToFrame(self, *args):
        # print args
        if args[0]:
            cmds.floatSliderGrp('fsg_resampleStep',
                                e=True,
                                pre=0)
            self.snapToFrame = True
            self.undoDepth = 2
        else:
            cmds.floatSliderGrp('fsg_resampleStep',
                                e=True,
                                pre=1)
            self.undoDepth = 1
            self.snapToFrame = False

    def simplifyWrapper(self, *args):
        '''
        straight simplify of curves using a managed cmds.simplfy call
        '''
        with self.contextManager(initialUndo=self.dragActive,
                                 undoFuncCache=self.undoFuncCache,
                                 undoDepth=self.undoDepth):
            self.dragActive = True  # turn on the undo management
            simplify = True
            if simplify:
                cmds.simplify(animation='keysOrObjects',
                               timeTolerance=cmds.floatSliderGrp('fsg_filtertimeValue', q=True, v=True),
                               valueTolerance=cmds.floatSliderGrp('fsg_filterfloatValue', q=True, v=True))
            else:
                print('testing filter call')
                objs = cmds.ls(sl=True)
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
        # print step
        curves = cmds.keyframe(q=True, sl=True, n=True)
        if not curves:
            curves = cmds.ls(sl=True, l=True)
            time = ()
        else:
            keys = sorted(cmds.keyframe(curves, sl=True, q=True, tc=True))
            time = (int(keys[0]), keys[-1])  # note the int conversion in case first key is on a sub-frame
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
    >>> # set the settings object to run metaData
    >>> mirror.settings.metaRig=True
    >>> mirror.settings.printSettings()
    >>> mirror.mirrorData(mode='Anim')

    >>> # useful code snippets:
    >>> # offset all selected nodes mirrorID by 5
    >>> mirror=r9Anim.MirrorHierarchy()
    >>> mirror.incrementIDs(cmds.ls(sl=True), offset=5)
    >>>
    >>> # set all the mirror axis on the selected
    >>> for node in cmds.ls(sl=True):
    >>>     mirror.setMirrorIDs(node,axis='translateX,rotateY,rotateZ')
    >>>
    >>> # copy mirrorId's from one node to another
    >>> for src, dest in zip(srcNodes, destNodes):
    >>>     mirror.copyMirrorIDs(src,dest)

    TODO: allow the mirror block to include an offset so that if you need to inverse AND offset
        by 180 to get left and right working you can still do so.
    '''

    def __init__(self, nodes=[], filterSettings=None, suppress=False, **kws):
        '''
        :param nodes: initial nodes to process
        :param filterSettings: filterSettings object to process hierarchies
        :param suppress: suppress the new warnings and validation call, default=False
        '''

        self.nodes = nodes
        if not type(self.nodes) == list:
            self.nodes = [self.nodes]

        self.suppresss_warnings = suppress

        # default Attributes used to define the system
        self.defaultMirrorAxis = ['translateX', 'rotateY', 'rotateZ']
        self.mirrorSide = 'mirrorSide'
        self.mirrorIndex = 'mirrorIndex'
        self.mirrorAxis = 'mirrorAxis'
        self.mirrorDict = {'Centre': {}, 'Left': {}, 'Right': {}}
        self.mergeLayers = True
        self.indexednodes = []  # all nodes to process - passed to the Animlayer context
        self.kws = kws  # allows us to pass kws into the copyKey and copyAttr call if needed, ie, pasteMethod!
        # print 'kws in Mirror call : ', self.kws

        # cache the function pointers for speed
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
            if side not in range(0, 3):
                raise ValueError('given mirror side is not a valid int entry: 0, 1 or 2')
            else:
                return True

#         # allow simple prefix rather than just full mirror sides
#         if side in ['C', 'L' ,'R']:
#             return True

        if side not in self.mirrorDict:
            raise ValueError('given mirror side is not a valid key: Left, Right or Centre')
        else:
            return True

    def _validateConstraints(self, nodes):
        '''
        check that none of the nodes about to be mirrored are constrained
        '''
        if not self.suppresss_warnings:
            constrained = nodesDriven(nodes, skipLocked=True)
            if constrained:
                result = cmds.confirmDialog(title='Pre Mirror Validations',
                                            message='Some nodes about to be mirrored are currently Driven by constraints or pairBlends, '
                                                    'are you sure you want to continue?\n\n'
                                                    'we recommend baking the nodes down before continuing',
                                            button=['Continue', 'Cancel'],
                                            defaultButton='OK',
                                            cancelButton='Cancel',
                                            icon='warning',
                                            dismissString='Cancel')
                if result == 'Continue':
                    return True
                return False
        return True

    def _validateKeyedNodes(self, nodes):
        '''
        used for the anim mirror, check that all nodes have keys else
        the mirror will be inconsistent
        '''
        if not self.suppresss_warnings:
            log_unused = ''
            unkeyed = getKeyedAttrs(nodes, returnkeyed=False)
            if unkeyed:
                for node, attrs in unkeyed.items():
                    log_unused += '\nMirrorAnim : Unkeyed attrs : %s : %s' % (node, attrs)
                print(log_unused)
                result = cmds.confirmDialog(title='Pre Mirror Validations : Animation Mode : Missing Key Daya',
                                            message='Some Nodes / Attributes about to be Mirrored do not have keyframe data.'
                                                    '\nWe recommend ensuring that all nodes have keys before continuing.'
                                                    '\n\nAre you sure you want to continue?'
                                                    '\n\nPlease see ScriptEditor for details\n',
                                            button=['Continue & Ignore', 'SetKeyframes (Recommended)', 'Cancel'],
                                            defaultButton='OK',
                                            cancelButton='Cancel',
                                            icon='warning',
                                            dismissString='Cancel')
                if result == 'Continue & Ignore':
                    return True
                if result == 'SetKeyframes (Recommended)':
                    for node, attrs in unkeyed.items():
                        try:
                            cmds.setKeyframe(node, attribute=attrs, t=cmds.playbackOptions(min=True))
                            log.debug('adding key to static attrs : %s > %s' % (node, attrs))
                        except:
                            log.warning('Failed to key static attrs : %s > %s' % (node, attrs))
                    return True
                return False
        return True

    def setMirrorIDs(self, node, side=None, slot=None, axis=None):
        '''
        Add/Set the default attrs required by the MirrorSystems.

        :param node: nodes to take the attrs
        :param side: valid values are 'Centre','Left', 'Right' or 0, 1, 2 or 'C', 'L', 'R'
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

        if side in ['C', 'L' ,'R']:
            side = ['C', 'L', 'R'].index(side)

        if self._validateMirrorEnum(side):
            mClass.addAttr(self.mirrorSide, attrType='enum', enumName='Centre:Left:Right', hidden=True)
            mClass.__setattr__(self.mirrorSide, side)
        if slot:
            mClass.addAttr(self.mirrorIndex, slot, hidden=True)
            mClass.__setattr__(self.mirrorIndex, slot)
        if axis:
            if axis == 'None':
                mClass.addAttr(self.mirrorAxis, attrType='string')
                mClass.mirrorAxis = ''
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
        pairs = zip(src, dest)
        for src, dest in pairs:
            axis = None
            src = r9Meta.MetaClass(src)
            if not src.hasAttr(self.mirrorAxis):
                log.warning('Node has no mirrorData : %s' % src.shortName())
                continue
            if src.hasAttr(self.mirrorAxis):
                axis = getattr(src, self.mirrorAxis)
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
                log.info('MirrorID incremented %i >> %i : %s' % (current, int(current) + offset, node))

    def getNodes(self):
        '''
        Get the list of nodes to start processing

        .. note::
            this has been modified to respect mRigs first to save you having to select the
            top level of hierarchy in the mRig itself. Instead we walk the children as expected
        '''
        return r9Core.FilterNode(self.nodes, filterSettings=self.settings).processFilter()

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
        This return the mirror data in a compiled manor for the poseSaver
        such that mirror data  for a node : Centre, ID 10 == Centre_10
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

        :param node: node return the axis from

        .. note::
            if mirrorAxis attr has been added to the node but is empty then
            no axis will be inversed at all. If the attr doesn't exist then the
            default inverse axis will be used
        '''
        if cmds.attributeQuery(self.mirrorAxis, node=node, exists=True):
            axis = cmds.getAttr('%s.%s' % (node, self.mirrorAxis))
            if not axis:
                return []
            else:
                # make sure we remove any trailing ',' also so we don't end up with empty entries
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
        self.indexednodes = nodes

        if not nodes and self.nodes:
            self.indexednodes = self.getNodes()

        if self.settings.metaRig and nodes:
            mrig = r9Meta.getConnectedMetaSystemRoot(self.indexednodes[0])
            print('Resolved MRig', mrig)
            self.indexednodes.extend(mrig.getMirror_opposites(self.indexednodes))

        if not self.indexednodes:
            raise StandardError('No mirrorMarkers found from the given node list/hierarchy')

        for node in set(self.indexednodes):
            try:
                side = self.getMirrorSide(node)
                index = self.getMirrorIndex(node)
                axis = self.getMirrorAxis(node)
                if logging_is_debug():
                    log.debug('Side : %s Index : %s>> node %s' %
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
            print('\nCentre MirrorLists =====================================================')
            for i in r9Core.sortNumerically(self.mirrorDict['Centre'].keys()):
                print('%s > %s' % (i, self.mirrorDict['Centre'][i]['node']))
            print('\nRight MirrorLists ======================================================')
            for i in r9Core.sortNumerically(self.mirrorDict['Right'].keys()):
                print('%s > %s' % (i, self.mirrorDict['Right'][i]['node']))
            print('\nLeft MirrorLists =======================================================')
            for i in r9Core.sortNumerically(self.mirrorDict['Left'].keys()):
                print('%s > %s' % (i, self.mirrorDict['Left'][i]['node']))
        else:
            print('\nCentre MirrorLists =====================================================')
            for i in r9Core.sortNumerically(self.mirrorDict['Centre'].keys()):
                print('%s > %s' % (i, r9Core.nodeNameStrip(self.mirrorDict['Centre'][i]['node'])))
            print('\nRight MirrorLists ======================================================')
            for i in r9Core.sortNumerically(self.mirrorDict['Right'].keys()):
                print('%s > %s' % (i, r9Core.nodeNameStrip(self.mirrorDict['Right'][i]['node'])))
            print('\nLeft MirrorLists =======================================================')
            for i in r9Core.sortNumerically(self.mirrorDict['Left'].keys()):
                print('%s > %s' % (i, r9Core.nodeNameStrip(self.mirrorDict['Left'][i]['node'])))
        if self.unresolved:
            for key, val in self.unresolved.items():
                if val:
                    print('\CLASHING %s Mirror Indexes =====================================================' % key)
                    for i in r9Core.sortNumerically(val):
                        print('clashing Index : %s : %s : %s' %
                              (key, i, ', '.join([r9Core.nodeNameStrip(n) for n in val[i]])))

    def switchPairData(self, objA, objB, mode='Anim'):
        '''
        take the left and right matched pairs and exchange the animData
        or poseData across between them

        :param objA:
        :param objB:
        :param mode: 'Anim' or 'Pose'

        '''
        if mode == 'Anim':
            transferCall = self.transferCallKeys  # AnimFunctions().copyKeys
        else:
            transferCall = self.transferCallAttrs  # AnimFunctions().copyAttributes

        # switch the anim data over via temp
        temp = cmds.duplicate(objA, name='DELETE_ME_TEMP', po=True)[0]
        transferCall([objA, temp], **self.kws)
        transferCall([objB, objA], **self.kws)
        transferCall([temp, objB], **self.kws)
        cmds.delete(temp)

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
            self.mergeLayers = True
        else:
            transferCall = self.transferCallAttrs  # AnimFunctions().copyAttributes
            inverseCall = AnimFunctions.inverseAttributes
            self.mergeLayers = False

        if primeAxis == 'Left':
            masterAxis = 'Left'
            slaveAxis = 'Right'
        else:
            masterAxis = 'Right'
            slaveAxis = 'Left'

        with AnimationLayerContext(self.indexednodes, mergeLayers=self.mergeLayers, restoreOnExit=False):
            for index, masterSide in self.mirrorDict[masterAxis].items():
                if index not in self.mirrorDict[slaveAxis].keys():
                    log.warning('No matching Index Key found for %s mirrorIndex : %s >> %s' %
                                (masterAxis, index, r9Core.nodeNameStrip(masterSide['node'])))
                else:
                    slaveData = self.mirrorDict[slaveAxis][index]
                    if logging_is_debug():
                        log.debug('SymmetricalPairs : %s >> %s' % (r9Core.nodeNameStrip(masterSide['node']),
                                             r9Core.nodeNameStrip(slaveData['node'])))
                    transferCall([masterSide['node'], slaveData['node']], **self.kws)
                    if logging_is_debug():
                        log.debug('Symmetrical Axis Inversion: %s' % ','.join(slaveData['axis']))
                    if slaveData['axis']:
                        inverseCall(slaveData['node'], slaveData['axis'])

    # @r9General.Timer
    def mirrorData(self, nodes=None, mode='Anim'):
        '''
        Using the FilterSettings obj find all nodes in the return that have
        the mirrorSide attr, then process the lists into Side and Index slots
        before Mirroring the animation data. Swapping left for right and
        inversing the required animCurves

        :param nodes: optional specific list of nodes to process, else we run the filterSetting code
            on the initial nodes past to the class
        :param mode: 'Anim' or 'Pose' process as a single pose or an animation

        TODO: Issue where if nodeA on Left has NO key data at all, and nodeB on right
        does, then nodeB will be left incorrect. We need to clean the data if there
        are no keys.
        
        TODO: Issue if left and right nodes have setLimits and we're doing purely a pose based mirror
        then we can get into a situation where the mirror fails. This is because we first do a copyAttr
        between the nodes, then we inverse the channels required. If the node on the side being inversed has limits 
        that don't allow that initial copy then the mirror will result in zero
        '''

        self.getMirrorSets(nodes)
        if not self.indexednodes:
            raise IOError('No nodes mirrorIndexed nodes found from given / selected nodes')

        if not self._validateConstraints(self.indexednodes):
            log.warning('Failed validation call - some nodes may be driven by constraints or pairBlends')
            return

        context_kws = {'time': False, 'undo': True, 'autokey': False}
        if mode == 'Anim':
            if not self._validateKeyedNodes(self.indexednodes):
                log.warning('Failed validation call - some nodes are unkeyed which will cause inconsistencies')
                return
            inverseCall = AnimFunctions.inverseAnimChannels
            self.mergeLayers = True
            context_kws['eval_mode'] = 'anim'
        else:
            inverseCall = AnimFunctions.inverseAttributes
            self.mergeLayers = False
            context_kws['eval_mode'] = 'static'

        with r9General.AnimationContext(**context_kws):
            with AnimationLayerContext(self.indexednodes, mergeLayers=self.mergeLayers, restoreOnExit=False):
                # Switch Pairs on the Left and Right and inverse the channels
                for index, leftData in self.mirrorDict['Left'].items():
                    if index not in self.mirrorDict['Right'].keys():
                        log.warning('No matching Index Key found for Left mirrorIndex : %s >> %s' % (index, r9Core.nodeNameStrip(leftData['node'])))
                    else:
                        rightData = self.mirrorDict['Right'][index]
                        if logging_is_debug():
                            log.debug('SwitchingPairs : %s >> %s' % (r9Core.nodeNameStrip(leftData['node']),
                                                                     r9Core.nodeNameStrip(rightData['node'])))
                        self.switchPairData(leftData['node'], rightData['node'], mode=mode)

                        if logging_is_debug():
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
        ConfigObj['mirror'] = self.mirrorDict
        ConfigObj.filename = filepath
        ConfigObj.write()

    def loadMirrorSetups(self, filepath=None, nodes=None, clearCurrent=True, matchMethod='base'):  # 'stripPrefix'):  # used to be 'base' for some reason??
        '''
        Load a Mirror Map to the nodes

        :param filepath: filepath to a mirrorMap, if none given then we assume that the internal mirrorDict is already setup
        :param nodes: nodes to load, or the root of a system to filter
        :param clearCurrent: if True then the load will first remove all current mirrormarkers
        :param matchMethod: arg passed to the match code, sets matchMethod used to match the data, see r9Core.matchNodeLists for details
        '''
        if filepath:
            if not os.path.exists(filepath):
                raise IOError('invalid filepath given')
            self.mirrorDict = configobj.ConfigObj(filepath)['mirror']

        nodesToMap = nodes
        if not nodesToMap:
            nodesToMap = list(self.nodes)
            nodesToMap.extend(cmds.listRelatives(nodesToMap, ad=True, f=True, type='transform'))
        # log.debug('nodes to load mirrors onto: %s' % ','.join(nodesToMap))

        progressBar = r9General.ProgressBarContext(len(nodesToMap))

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
                                axis = 'None'
                            else:
                                axis = ','.join(leftData['axis'])
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
                                    axis = 'None'
                                else:
                                    axis = ','.join(rightData['axis'])
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
                                    axis = 'None'
                                else:
                                    axis = ','.join(centreData['axis'])
                                self.setMirrorIDs(node, side='Centre', slot=int(index), axis=axis)  # ','.join(centreData['axis']))
                            else:
                                self.setMirrorIDs(node, side='Centre', slot=int(index))
                            break

                progressBar.updateProgress()
        self.printMirrorDict()

class MirrorSetup(object):

    def __init__(self):
        self.mirrorClass = MirrorHierarchy()
        self.mirrorClass.settings.hierarchy = True
        self.win = 'MirrorSetup'

    @classmethod
    def show(cls):
        cls()._showUI()

    def close(self):
        if cmds.window(self.win, exists=True):
            cmds.deleteUI(self.win, window=True)

    def _showUI(self):
        self.close()

        space = 10
        size = (275, 490)
        window = cmds.window(self.win, title=LANGUAGE_MAP._Mirror_Setup_.title, s=True)  # , widthHeight=size)
        cmds.menuBarLayout()
        cmds.menu(l=LANGUAGE_MAP._Generic_.vimeo_menu)
        cmds.menuItem(l=LANGUAGE_MAP._Generic_.vimeo_help,
                      c="import Red9.core.Red9_General as r9General;r9General.os_OpenFile('https://vimeo.com/57882801')")
        cmds.menuItem(divider=True)
        cmds.menuItem(l=LANGUAGE_MAP._Generic_.contactme, c=lambda *args: (r9Setup.red9ContactInfo()))

        cmds.menu(l=LANGUAGE_MAP._Generic_.tools)
        cmds.menuItem(l=LANGUAGE_MAP._Mirror_Setup_.increment_ids,
                      c=self.__increment_ids)

        cmds.columnLayout(adjustableColumn=False, columnAttach=('both', 5), cw=size[0])

        # mirror side
        cmds.separator(h=20, style='none')
        cmds.text(l=LANGUAGE_MAP._Mirror_Setup_.side, fn='boldLabelFont')
        cmds.separator(h=5, style='none')
        cmds.rowColumnLayout(nc=3, columnWidth=[(1, 90), (2, 90), (3, 90)], columnSpacing=[(1, space)])
        self.uircbMirrorSide = cmds.radioCollection('mirrorSide')
        cmds.radioButton('Right', label=LANGUAGE_MAP._Generic_.right, cc=self.__uicb_setupIndex)
        cmds.radioButton('Centre', label=LANGUAGE_MAP._Generic_.centre, cc=self.__uicb_setupIndex)
        cmds.radioButton('Left', label=LANGUAGE_MAP._Generic_.left, cc=self.__uicb_setupIndex)
        cmds.setParent('..')

        # mirror index
        cmds.separator(h=20, style='in')
        cmds.rowColumnLayout(nc=2, columnWidth=[(1, 110), (2, 60)])
        cmds.text(label=LANGUAGE_MAP._Mirror_Setup_.index, fn='boldLabelFont')
        cmds.intField('ifg_mirrorIndex', v=1, min=1, w=50)
        cmds.setParent('..')

        # Mirror axis
        cmds.separator(h=20, style='in')
        cmds.text(l=LANGUAGE_MAP._Mirror_Setup_.axis, fn='boldLabelFont')
        cmds.separator(h=5, style='none')
        cmds.rowColumnLayout(nc=2, columnWidth=[(1, 130), (2, 130)], columnSpacing=[(1, space)])
        cmds.checkBox('default', l=LANGUAGE_MAP._Mirror_Setup_.default_axis, v=True,
                      onc=lambda x: self.__uicb_setDefaults('default'),
                      ofc=lambda x: self.__uicb_setDefaults('custom'))
        cmds.checkBox('setDirectCopy', l=LANGUAGE_MAP._Mirror_Setup_.no_inverse, v=False,
                      ann=LANGUAGE_MAP._Mirror_Setup_.no_inverse_ann,
                      onc=lambda x: self.__uicb_setDefaults('direct'),
                      ofc=lambda x: self.__uicb_setDefaults('default'))
        cmds.setParent('..')
        cmds.separator(h=5, style='none')
        cmds.rowColumnLayout(ann=LANGUAGE_MAP._Generic_.attrs, numberOfColumns=3,
                                 columnWidth=[(1, 90), (2, 90), (3, 90)], columnSpacing=[(1, space)])
        cmds.checkBox('translateX', l='Trans X', v=False)  # LANGUAGE_MAP._Generic_.transX
        cmds.checkBox('translateY', l='Trans Y', v=False)  # LANGUAGE_MAP._Generic_.transY
        cmds.checkBox('translateZ', l='Trans Z', v=False)  # LANGUAGE_MAP._Generic_.transZ
        cmds.checkBox('rotateX', l='Rot X', v=False)  # LANGUAGE_MAP._Generic_.rotX
        cmds.checkBox('rotateY', l='Rot Y', v=False)  # LANGUAGE_MAP._Generic_.rotY
        cmds.checkBox('rotateZ', l='Rot Z', v=False)  # LANGUAGE_MAP._Generic_.rotZ
        cmds.setParent('..')

        cmds.separator(h=5, style='none')
        cmds.text(l='   '+LANGUAGE_MAP._Mirror_Setup_.custom_axis, al='left')
        cmds.separator(h=5, style='none')
        cmds.rowColumnLayout(numberOfColumns=2, columnWidth=[(1, 200), (2, 50)], columnSpacing=[(1, space)])
        cmds.textField('customAxis', ann=LANGUAGE_MAP._Mirror_Setup_.custom_axis_ann, text="")
        cmds.popupMenu()
        cmds.menuItem(label=LANGUAGE_MAP._Mirror_Setup_.grab_channel_box, command=self.__get_channelbox_attrs)
        cmds.button(label=LANGUAGE_MAP._Mirror_Setup_.channelbox,
                    ann=LANGUAGE_MAP._Mirror_Setup_.custom_axis_ann,
                    command=self.__get_channelbox_attrs)
        cmds.setParent('..')

        # commands
        cmds.separator(h=20, style='in')
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
        cmds.separator(h=20, style='in')
        cmds.rowColumnLayout(nc=2, columnWidth=[(1, 135), (2, 135)], columnSpacing=[(1, space)])
        cmds.checkBox('mirrorSaveLoadHierarchy', l=LANGUAGE_MAP._Generic_.hierarchy, v=True)
        cmds.checkBox('mirrorClearCurrent', l=LANGUAGE_MAP._Mirror_Setup_.clear, v=True)
        cmds.setParent('..')
        cmds.separator(h=5, style='none')
        cmds.rowColumnLayout(nc=2, columnWidth=[(1, 135), (2, 135)])
        cmds.button(label=LANGUAGE_MAP._Mirror_Setup_.save_configs, bgc=r9Setup.red9ButtonBGC(1),
                     ann=LANGUAGE_MAP._Mirror_Setup_.save_configs_ann,
                     command=lambda *args: (self.__saveMirrorSetups()))
        cmds.button(label=LANGUAGE_MAP._Mirror_Setup_.load_configs, bgc=r9Setup.red9ButtonBGC(1),
                     command=lambda *args: (self.__loadMirrorSetups()))
        cmds.setParent('..')
        cmds.separator(h=15, style='none')
        cmds.iconTextButton(style='iconAndTextHorizontal', bgc=(0.7, 0, 0),
                            image1='Rocket9_buttonStrap_narrow.png',
                            align='left',
                            c=r9Setup.red9ContactInfo, h=24, w=275)
        cmds.separator(h=15, style='none')
        cmds.showWindow(window)
        self.__uicb_setDefaults('default')
        #cmds.window(self.win, e=True, widthHeight=size)
        cmds.radioCollection('mirrorSide', e=True, select='Centre')
        self.__uicb_setupIndex()

    def __get_nodes(self):
        '''
        this is a wrap to manage mRig root systems
        '''
        nodes = cmds.ls(sl=True, l=True)
        if nodes:
            try:
                mrig = r9Meta.getConnectedMetaSystemRoot(nodes[0], mInstances=r9Meta.MetaRig)
                # Top level grp in the PuppetRig Systems
                if mrig and mrig.hasAttr('masterNode') and mrig.masterNode:
                    return mrig.masterNode
                if mrig and mrig.ctrl_main:
                    return [mrig.ctrl_main]
                else:
                    return nodes
                # return r9Meta.getConnectedMetaSystemRoot(nodes[0],mInstances=r9Meta.MetaRig).masterNode
            except:
                return nodes

    def __uicb_setupIndex(self, *args):
        '''
        New for MetaRig: If the node selected is part of an MRig when we switch
        the side we automatically bump the index counter to the next available index slot ;)
        '''
        nodes = cmds.ls(sl=True, l=True)
        if nodes:
            try:
                mRig = r9Meta.getConnectedMetaSystemRoot(nodes[0], mInstances=r9Meta.MetaRig)
                if mRig:
                    index = mRig.getMirror_nextSlot(side=cmds.radioCollection('mirrorSide', q=True, select=True), forceRefresh=True)
                    log.info('Setting up Next Available Index slot from connected MetaRig systems mirrorNodes')
                    cmds.intField('ifg_mirrorIndex', e=True, v=index)
            except:
                log.debug('No MetaRig systems found to debug index lists from')
                cmds.intField('ifg_mirrorIndex', e=True, v=1)

    def __get_channelbox_attrs(self, *args):
        '''
        pull the selected channel box attrs back to the custom txt field
        '''
        attrs = getChannelBoxSelection()
        if attrs:
            cmds.textField('customAxis', e=True, text=','.join(attrs))
        else:
            log.warning('No attributes currently selected in the ChannelBox')

    def __uicb_getMirrorIDsFromNode(self):
        '''
        set the flags based on the given nodes mirror setup
        '''
        node = cmds.ls(sl=True)[0]
        axis = None
        index = self.mirrorClass.getMirrorIndex(node)
        side = self.mirrorClass.getMirrorSide(node)
        cmds.textField('customAxis', e=True, text='')
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
            for a in list(axis):
                print('MirroAxis : ', a)
                if a == 'translateX':
                    cmds.checkBox('translateX', e=True, v=True)
                    axis.remove(a)
                elif a == 'translateY':
                    cmds.checkBox('translateY', e=True, v=True)
                    axis.remove(a)
                elif a == 'translateZ':
                    cmds.checkBox('translateZ', e=True, v=True)
                    axis.remove(a)
                elif a == 'rotateX':
                    cmds.checkBox('rotateX', e=True, v=True)
                    axis.remove(a)
                elif a == 'rotateY':
                    cmds.checkBox('rotateY', e=True, v=True)
                    axis.remove(a)
                elif a == 'rotateZ':
                    cmds.checkBox('rotateZ', e=True, v=True)
                    axis.remove(a)
            cmds.textField('customAxis', e=True, text=','.join(axis))
        else:
            cmds.checkBox('default', e=True, v=True)
            self.__uicb_setDefaults('default')

    def __printDebugs(self):
        self.mirrorClass.nodes = self.__get_nodes()  # cmds.ls(sl=True)
        self.mirrorClass.printMirrorDict()

    def __deleteMarkers(self):
        nodes = cmds.ls(sl=True, l=True)
        if nodes:
            for node in nodes:
                self.mirrorClass.deleteMirrorIDs(node)
                log.info('deleted MirrorMarkers from : %s' % r9Core.nodeNameStrip(node))

    def __uicb_setDefaults(self, mode):
        enable = False
        if mode == 'direct':
            cmds.checkBox('default', e=True, v=False)
        if mode == 'custom':
            enable = True
        cmds.checkBox('translateX', e=True, en=enable, v=False)
        cmds.checkBox('translateY', e=True, en=enable, v=False)
        cmds.checkBox('translateZ', e=True, en=enable, v=False)
        cmds.checkBox('rotateX', e=True, en=enable, v=False)
        cmds.checkBox('rotateY', e=True, en=enable, v=False)
        cmds.checkBox('rotateZ', e=True, en=enable, v=False)
        # now set
        if mode == 'default':
            cmds.checkBox('setDirectCopy', e=True, v=False)
            cmds.textField('customAxis', e=True, text='')
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
        if not cmds.textField('customAxis', q=True, text=True):
            if cmds.checkBox('default', q=True, v=True):
                return None
            elif cmds.checkBox('setDirectCopy', q=True, v=True):
                return 'None'

        axis = []
        custom = []
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
        if cmds.textField('customAxis', q=True, text=True):
            for attr in cmds.textField('customAxis', q=True, text=True).split(','):
                custom.append(attr.strip())
        if axis or custom:
            return ','.join(list(set(axis + custom)))
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
            message = "Add / Modify Mirror Markers on Multiple selected nodes?\n\n"\
                        "Choose to either set complete mirror Markers from the UI settings OR "\
                        "Modify part of the current mirror markers on the nodes\n\n"\
                        "* Set New : add complete new mirror markers\n"\
                        "* Axis : modify just the axis values on the nodes\n"\
                        "* Side : modify just the side markers\n"\
                        "* ID'S : change / increment just the mirror ID's\n\n"

            result = cmds.confirmDialog(
                title='Mirror Markers',
                message=message,
                icon='question',
                button=['Set New + Increment IDs', 'IDs : Modify / Increment', 'AXIS : Modify Only', 'SIDE : Modify Only', 'Cancel'],
                defaultButton='OK',
                cancelButton='Cancel',
                dismissString='Cancel')

            if result == 'Set New + Increment IDs':
                i = index
                for node in nodes:
                    self.mirrorClass.setMirrorIDs(node, side=str(side), slot=i, axis=axis)
                    log.info('MirrorMarkers added to : %s' % r9Core.nodeNameStrip(node))
                    i += 1
            elif result == 'IDs : Modify / Increment':
                i = index
                for node in nodes:
                    self.mirrorClass.setMirrorIDs(node, side=None, slot=i, axis=None)
                    log.info('MirrorMarkers Modified IDs to %i : %s' % (i, r9Core.nodeNameStrip(node)))
                    i += 1
            elif result == 'AXIS : Modify Only':
                for node in nodes:
                    self.mirrorClass.setMirrorIDs(node, side=None, slot=None, axis=axis)
                    log.info('MirrorMarkers Axis Modified %s : %s' % (axis, r9Core.nodeNameStrip(node)))
            elif result == 'SIDE : Modify Only':
                for node in nodes:
                    self.mirrorClass.setMirrorIDs(node, side=str(side), slot=None, axis=None)
                    log.info('MirrorMarkers Side Modified %s : %s' % (side, r9Core.nodeNameStrip(node)))
        else:
            self.mirrorClass.setMirrorIDs(nodes[0], side=str(side), slot=index, axis=axis)
            log.info('MirrorMarkers added to : %s' % r9Core.nodeNameStrip(nodes[0]))

    def __increment_ids(self, *args):
        objs = cmds.ls(sl=True, l=True)
        if objs:
            result = cmds.promptDialog(
                    title='Increment IDs',
                    message=LANGUAGE_MAP._Mirror_Setup_.increment_ids,
                    button=['Offset', 'Cancel'],
                    defaultButton='OK',
                    cancelButton='Cancel',
                    dismissString='Cancel')
            
            if result == 'Offset':
                offset = int(cmds.promptDialog(query=True, text=True))
                self.mirrorClass.incrementIDs(objs, offset)
                       
    def __saveMirrorSetups(self):
        filepath = cmds.fileDialog2(fileFilter="mirrorMap Files (*.mirrorMap *.mirrorMap);;", okc='Save', cap='Save MirrorSetups')[0]
        self.mirrorClass.nodes = cmds.ls(sl=True)
        if cmds.checkBox('mirrorSaveLoadHierarchy', q=True, v=True):
            self.mirrorClass.settings.hierarchy = True
            self.mirrorClass.nodes = self.__get_nodes()  # cmds.ls(sl=True)
        self.mirrorClass.saveMirrorSetups(filepath=filepath)

    def __loadMirrorSetups(self):
        filepath = cmds.fileDialog2(fileFilter="mirrorMap Files (*.mirrorMap *.mirrorMap);;", okc='Load', cap='Load MirrorSetups', fileMode=1)[0]
        if cmds.checkBox('mirrorSaveLoadHierarchy', q=True, v=True):
            self.mirrorClass.nodes = self.__get_nodes()  # cmds.ls(sl=True, l=True)
            self.mirrorClass.loadMirrorSetups(filepath=filepath, clearCurrent=cmds.checkBox('mirrorClearCurrent', q=True, v=True))
        else:
            self.mirrorClass.loadMirrorSetups(filepath=filepath, nodes=cmds.ls(sl=True, l=True), clearCurrent=cmds.checkBox('mirrorClearCurrent', q=True, v=True))


class CameraTracker():

    def __init__(self, fixed=True):
        self.win = 'CameraTrackOptions'
        self.fixed = fixed
        self.poseButtonHighLight = r9Setup.red9ButtonBGC('green')

    @staticmethod
    def cameraTrackView(start=None, end=None, step=None, fixed=True, keepOffset=False, cam=None, static=False):
        '''
        CameraTracker is a simple wrap over the internal viewFit call but this manages the data
        over time. Works by taking the current camera, in the current 3dView, and fitting it to
        frame the currently selected objects per frame, or rather per frameStep.

        :param start: start frame
        :param end: end frame
        :param step: frame step to increment between fit
        :param fixed: switch between tracking or panning framing fit
        :param keepOffset: keep the current camera offset rather than doing a full viewFit
        :param cam: if given use this camera else we use the current modelEditors camera
        :param static: if true we DON'T track, we just do a single frame - hook for the ProPack Playblast management

        TODO: add option for cloning the camera rather than using the current directly
        '''
        if not cmds.ls(sl=True):
            raise StandardError('Nothing selected to Track!')
        if not cam:
            cam = cmds.modelEditor(cmds.playblast(ae=True).split('|')[-1], q=True, camera=True)

#         cam = cmds.camera(name='CamTracker')[0]
#         mel.eval('cameraMakeNode 2 ""')
#         mel.eval('lookThroughModelPanel("%s","%s")' % (cam, cmds.playblast(ae=True).split('|')[-1]))

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
#         if not keepOffset:
#             if cmds.optionVar(exists='red9_cameraTrackKeepOffset'):
#                 keepOffset = cmds.optionVar(q='red9_cameraTrackKeepOffset')

        if static:
            cmds.viewFit(cam, animate=False)
            return

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

        if not static:
            with r9General.AnimationContext(eval_mode='anim'):
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

    def close(self):
        if cmds.window(self.win, exists=True):
            cmds.deleteUI(self.win, window=True)

    def _showUI(self):
        self.close()
        cmds.window(self.win, title=LANGUAGE_MAP._CameraTracker_.title, widthHeight=(300, 180))
        cmds.menuBarLayout()
        cmds.menu(l=LANGUAGE_MAP._Generic_.vimeo_menu)
        cmds.menuItem(l=LANGUAGE_MAP._Generic_.vimeo_help,
                      c="import Red9.core.Red9_General as r9General;r9General.os_OpenFile('https://vimeo.com/60960492')")
        cmds.menuItem(divider=True)
        cmds.menuItem(l=LANGUAGE_MAP._Generic_.contactme, c=lambda *args: (r9Setup.red9ContactInfo()))
        cmds.columnLayout(adjustableColumn=True)
        cmds.separator(h=15, style='none')
        cmds.text(LANGUAGE_MAP._CameraTracker_.info, ww=True)
        cmds.separator(h=15, style='none')
        cmds.intFieldGrp('CameraFrameStep', numberOfFields=1,
                         label=LANGUAGE_MAP._CameraTracker_.tracker_step, value1=10,
                         extraLabel=' %s' % LANGUAGE_MAP._CameraTracker_.frames,
                         cw=(1, 100),
                         cc=partial(self.__storePrefs))
        cmds.separator(h=15, style='none')
        cmds.rowColumnLayout(numberOfColumns=2, columnSpacing=[(1, 20)])
        cmds.checkBox('CBMaintainCurrent', l=LANGUAGE_MAP._CameraTracker_.maintain_frame, v=True, cc=partial(self.__storePrefs))
        cmds.setParent('..')
        cmds.separator(h=15, style='none')
        cmds.rowColumnLayout(numberOfColumns=2, columnWidth=[(1, 145), (2, 145)])
        if self.fixed:
            cmds.button('cameraTrackTrack',
                        label=LANGUAGE_MAP._CameraTracker_.pan,
                        bgc=self.poseButtonHighLight,
                        command=partial(self.__runTracker))
        else:
            cmds.button('cameraTrackTrack',
                        label=LANGUAGE_MAP._CameraTracker_.track,
                        bgc=self.poseButtonHighLight,
                        command=partial(self.__runTracker))
        cmds.button('cameraTrackAppy', label=LANGUAGE_MAP._Generic_.apply, bgc=self.poseButtonHighLight, command=partial(self.__storePrefs))
        cmds.setParent('..')
        cmds.separator(h=15, style='none')
        cmds.iconTextButton(style='iconAndTextHorizontal', bgc=(0.7, 0, 0),
                                image1='Rocket9_buttonStrap_narrow.png',
                                align='left',
                                c=lambda *args: (r9Setup.red9ContactInfo()), h=24, w=275)
        cmds.separator(h=15, style='none')
        cmds.showWindow(self.win)
        cmds.window(self.win, e=True, widthHeight=(290, 255))
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
        self.cameraTrackView(fixed=self.fixed, keepOffset=cmds.checkBox('CBMaintainCurrent', q=True, v=True))


class ReconnectAnimData(object):
    '''
    This is a method for debugging and re-connecting animation curves when theyve become
    disconnected from a scene. This happens occasionally when using referencing where the
    refEdits pointing to the connect calls get broken..
    '''
    def __init__(self):
        self.win = 'ReconnectAnimData'

    @classmethod
    def show(cls):
        cls()._showUI()

    def close(self):
        if cmds.window(self.win, exists=True):
            cmds.deleteUI(self.win, window=True)

    def _showUI(self):
        self.close()
        cmds.window(self.win, title=self.win, widthHeight=(300, 220))

        cmds.menuBarLayout()
        cmds.menu(l="Help")
        cmds.menuItem(l="Bug post -LostAnimPart1",
                      c="import Red9.core.Red9_General as r9General;r9General.os_OpenFile('http://markj3d.blogspot.co.uk/2011/07/lost-animation-when-loading-referenced.html')")
        cmds.menuItem(l="Bug post -LostAnimPart1",
                      c="import Red9.core.Red9_General as r9General;r9General.os_OpenFile('http://markj3d.blogspot.co.uk/2012/09/lost-animation-part2.html')")
        cmds.menuItem(l="Bug post -LostAnimPart3",
                      c="import Red9.core.Red9_General as r9General;r9General.os_OpenFile('http://markj3d.blogspot.co.uk/2014/09/lost-animation-part-3.html')")
        cmds.menuItem(divider=True)
        cmds.menuItem(l="Contact Me", c=lambda *args: (r9Setup.red9ContactInfo()))

        cmds.columnLayout('uicl_audioMain', adjustableColumn=True)
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

        cmds.iconTextButton(style='iconAndTextHorizontal', bgc=(0.7, 0, 0),
                            image1='Rocket9_buttonStrap.png',
                            align='left',
                            c=lambda *args: (r9Setup.red9ContactInfo()), h=24, w=200)
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
                    print('%s >> %s' % (anim, plug))
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
        nodes = cmds.ls(sl=True, l=True)
        chns = []

        # build up the main lists
        animCurves = cmds.ls(type='animCurve', s=True)
        [chns.extend(cmds.listAnimatable(node)) for node in nodes]

        for chn in chns:
            if stripNamespace:
                animCurveExpected = chn.split(':')[-1].split('|')[-1].replace('.', '_')
            else:
                animCurveExpected = chn.split('|')[-1].replace('.', '_')
            if animCurveExpected in animCurves:
                if not cmds.isConnected('%s.output' % animCurveExpected, chn):
                    print('%s >> %s' % (animCurveExpected, chn))
                    cmds.connectAttr('%s.output' % animCurveExpected, chn, force=True)
            elif stripLayerNaming:
                for curve in animCurves:
                    curveStripped = curve.replace('_Merged_Layer_inputB', '').rstrip('123456789')
                    if curveStripped == animCurveExpected:
                        if not cmds.isConnected(curve, chn):
                            print('%s >> %s' % (curve, chn))
                            cmds.connectAttr('%s.output' % curve, chn, force=True)
