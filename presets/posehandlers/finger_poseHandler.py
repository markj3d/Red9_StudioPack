'''
------------------------------------------
Red9 Studio Pack: Maya Pipeline Solutions
Author: Mark Jackson
email: rednineinfo@gmail.com

Red9 blog : http://red9-consultancy.blogspot.co.uk/
MarkJ blog: http://markj3d.blogspot.co.uk
------------------------------------------

================================================================

Advanced Pose Data management. 

---------------------------------------
RIG SPEC :  MetaData wired or HIK WIRED
---------------------------------------
This handler is designed to turn a folder into a finger pose library.
The rig must be either wired to Meta or wired to HIK. 
Required subMetaSystems : 'L_ArmSystem','R_ArmSystem'

-------------------------------
CASE : Fingers matched by Index
-------------------------------
for fingers where we want to match left and right fingers 
based on their hierarchy index ONLY...ie left and right finger 
should have the same hierarchy under the wrist

-------------------------------
INPUT : 
-------------------------------
the code requires you to select a controller on either the left or right 
side of the rig that has mirror markers on it. From this we determine which
finger systems (left or right) to load the data onto

================================================================
'''

import Red9.core.Red9_Meta as r9Meta
import maya.cmds as cmds


def getNodesOverload(poseObj, nodes, *args):

    # NOTE: poseObj already has an attr 'metaRig' which is filled
    # automatically in the main buildInternalPoseData() call
    metaNode = poseObj.metaRig
    currentSelection = cmds.ls(sl=True, l=True)
    filteredNodes = []

    if not issubclass(type(metaNode), r9Meta.MetaHIKControlSetNode):
        # see if we have a left or right controller selected and switch to the
        # appropriate subMetaSystem

        if cmds.getAttr('%s.mirrorSide' % currentSelection[0]) == 1:
            print '\nFinger : PoseOverload Handler : %s >> side: Left' % metaNode
            filteredNodes = metaNode.L_ArmSystem.L_FingerSystem.getChildren()
            [filteredNodes.append(node) for node in cmds.listRelatives(filteredNodes, type='joint', ad=True, f=True)]

        elif cmds.getAttr('%s.mirrorSide' % currentSelection[0]) == 2:
            print '\nFinger : PoseOverload Handler : %s >> side: Right' % metaNode
            filteredNodes = metaNode.R_ArmSystem.R_FingerSystem.getChildren()
            [filteredNodes.append(node) for node in cmds.listRelatives(filteredNodes, type='joint', ad=True, f=True)]
    else:
        if currentSelection[0] == metaNode.LeftWristEffector or currentSelection[0] == metaNode.LeftHand:
            [filteredNodes.append(node) for node in cmds.listRelatives(metaNode.LeftHand, type='joint', ad=True, f=True)]
        elif currentSelection[0] == metaNode.RightWristEffector or currentSelection[0] == metaNode.RightHand:
            [filteredNodes.append(node) for node in cmds.listRelatives(metaNode.RightHand, type='joint', ad=True, f=True)]

    # modify the actual PoseData object, changing the data to be matched on index
    # rather than using the standard name or metaMap matching
    poseObj.metaPose = False
    poseObj.matchMethod = 'index'

    return filteredNodes



#=================================================
# Main calls used internally in the PoseData class
#=================================================

def poseGetNodesLoad(poseObj, nodes, *args):
    '''
    PoseLoad:
    this is an entry point used to over-load the main getNodes()
    function in the PoseData object. This allows you to modify, on 
    the fly the poseObj itself as poseObj arg is the class instance
    @param poseObj: the actual instance of the PoseData object
    @param nodes: original node list passed in from the UI 
    '''
    return getNodesOverload(poseObj, nodes, *args)

def poseGetNodesSave(poseObj, nodes, *args):
    '''
    PoseSave:
    this is an entry point used to over-load the main getNodes()
    function in the PoseData object. This allows you to modify, on 
    the fly the poseObj itself as poseObj arg is the class instance
    @param poseObj: the actual instance of the PoseData object
    @param nodes: original node list passed in from the UI 
    '''
    return getNodesOverload(poseObj, nodes, *args)

def posePopupAdditions(parent, ui=None):
    '''
    This run when the Pose PopUp menu is generated, allows us to add custom menu's to the 
    popUp and extend it's functionality as we need at a folder level!
    '''
    cmds.menuItem(divider=True)
    cmds.menuItem(parent=parent, label='Test Finger Menu 1!', command="print('Added Test Menu 1')")
    cmds.menuItem(parent=parent, label='Test Finger Menu 2!', command="print('Added Test Menu 2')")

