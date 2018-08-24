import Red9.core.Red9_Meta as r9Meta
import maya.cmds as cmds
import os

def getNodesOverload(poseObj, nodes, *args):
    # do your stuff and filtering
    poseObj.matchMethod = 'metaData'
    return poseObj.getNodes(nodes)

def poseGetNodesLoad(poseObj, nodes, *args):
    '''
    Over load the loading such that it's always
    loaded locally to the HeadCtrl

    Why load in relative space????????????
    '''
    print 'OVERLOADED FACIAL HANDLERS'
    cmds.select(poseObj.metaRig.FACE_Neck)
    return getNodesOverload(poseObj, nodes, *args)

def poseGetNodesSave(poseObj, nodes, *args):
    '''
    If the poseName matches an attr on the metaFacial node then 
    push the SDK data back to the controls so that the pose can
    be stored correctly
    '''
    print 'OVERLOADED FACIAL HANDLERS'
    poseName = os.path.basename(poseObj.filepath).split('.pose')[0].split('_neg')[0]
    # print 'poseObject metaRig already set?????? ', poseObj.metaRig

    if not poseObj.useFilter:
        # print 'filter not active : finding FacialCore'
        nodes = poseObj.metaRig.get_sdk_target_current_ctrls(poseName)
    else:
        print 'filter active : rootNode should be the FacialCore:'

    if poseObj.metaRig.hasAttr(poseName) and poseName in poseObj.metaRig.coreControlChans:
        poseObj.metaRig.copy_xforms_sdk_grp_to_ctrl(poseName, accumulated=False)
    else:
        poseObj.metaRig.copy_xforms_sdk_grp_to_ctrl(poseName, accumulated=True)
        # print 'pushing SDK Transforms to Ctrls : %s' % poseName
    return getNodesOverload(poseObj, nodes, *args)

def posePopupAdditions(parent, poseUIObj=None):
    '''
    This run when the Pose PopUp menu is generated, allows us to add custom menu's to the 
    popUp and extend it's functionality as we need at a folder level!
    '''
    cmds.menuItem(divider=True, parent=parent)
    cmds.menuItem(parent=parent, label='Push Selected Pose to SDK!', command=lambda x: pushPoseFromLib(poseUIObj))

def pushPoseFromLib(poseUIObj):
    mFacial = r9Meta.getMetaNodes(mTypes='Red9_MetaFacialCore')[0]
    posepath = poseUIObj.getPoseDir()
    poseName = os.path.basename(poseUIObj.getPoseSelected())
    print 'posepath', posepath
    print 'poseName', poseName
    mFacial.poses_pull_from_library(posepath, poseName)
