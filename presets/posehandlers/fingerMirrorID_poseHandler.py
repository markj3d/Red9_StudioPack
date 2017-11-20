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

-----------------------------------------
RIG SPEC :  MetaData wired to Red9 ProRig
-----------------------------------------

This handler is designed to turn a folder into a finger pose library.
The rig must be either wired to Meta or wired to HIK. 
Required subMetaSystems : 'L_ArmSystem','R_ArmSystem'

If your Red9 ProRig has finger poses setup on the switch controllers then this
is the poseHandler you must run.

-----------------------------------
CASE : Fingers matched by MirrorID
-----------------------------------
for fingers where we want to match left and right fingers based on their mirrorIndex. 
The fingers must be wired to either finger or toe metaSubSystem.

This also manages mirrorInverse calls so that when loading a pose 
stored from the left fingers, any mirrorAxis setup will be inversed
when loading the data to the right, and visa versa

-------------------------------
INPUT : 
-------------------------------
if nothing is selected when the pose is loaded/saved then we prompt the 
user for a system to choose from. This supports the Left/Right Finger and Toe
systems on the Red9 ProRig. 
If we have something selected it's expected that that node is connected to a 
system which has a finger of toe system as a child. ie, for the left fingers you need
to have selected something from the left arm system.

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
        # see if we have a controller selected thats connected to an
        # appropriate subMetaSystem
        if not currentSelection:
            result = cmds.confirmDialog(
                                title='selection hint missing',
                                button=['L_Fingers', 'R_Fingers', 'L_Toes', 'R_Toes', 'Cancel'],
                                message='We need a hint to ID which finger system to load/save the data too,\nIdeally you should select something in the correct limb system that we can use',
                                defaultButton='Cancel',
                                cancelButton='Cancel',
                                icon='information',
                                dismissString='Cancel')
            if result == 'L_Fingers':
                msystem = metaNode.L_ArmSystem
            elif result == 'R_Fingers':
                msystem = metaNode.R_ArmSystem
            elif result == 'L_Toes':
                msystem = metaNode.L_LegSystem
            elif result == 'R_Toes':
                msystem = metaNode.R_LegSystem
        else:
            msystem = r9Meta.getConnectedMetaNodes(cmds.ls(sl=True))[0]

        # from selected node, or selected system find our finger / toe subSystem
        if not msystem.systemType.lower() in ['fingers', 'toes']:
            fingersystem = msystem.getChildMetaNodes(mAttrs=['systemType'])
            if fingersystem:
                fingersystem = fingersystem[0]
        else:
            fingersystem = msystem
        if not fingersystem or not fingersystem.systemType.lower() in ['fingers', 'toes']:
            raise IOError('no finger / toe metaSubSystems found from the selected node')

        print '\nFinger : PoseOverload Handler : %s >> subSystem: %s' % (metaNode, fingersystem)


#         if cmds.getAttr('%s.mirrorSide' % currentSelection[0]) == 1:
#             print '\nFinger : PoseOverload Handler : %s >> side: Left' % metaNode
#             filteredNodes = metaNode.L_ArmSystem.L_FingerSystem.getChildren()
#         elif cmds.getAttr('%s.mirrorSide' % currentSelection[0]) == 2:
#             print '\nFinger : PoseOverload Handler : %s >> side: Right' % metaNode
#             filteredNodes = metaNode.R_ArmSystem.R_FingerSystem.getChildren()

    # modify the actual PoseData object, changing the data to be matched on index
    # rather than using the standard name or metaMap matching
    poseObj.metaPose = False
    poseObj.matchMethod = 'mirrorIndex_ID'
    poseObj.mirrorInverse = True  # set the mirror inverse code to active to cope with mirror differences between Left and Right fingers

    if poseObj.useFilter:
        return fingersystem.getChildren()

    # selection only mode
    return currentSelection



# =================================================
# Main calls used internally in the PoseData class
# =================================================

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

