'''
------------------------------------------
Red9 Studio Pack: Maya Pipeline Solutions
Author: Mark Jackson
email: rednineinfo@gmail.com

Red9 blog : http://red9-consultancy.blogspot.co.uk/
MarkJ blog: http://markj3d.blogspot.co.uk
------------------------------------------

================================================================

Advanced Pose Data management!

This is a template example for a poseHandler.py file that the 
PoseSaver now optionally looks for in any pose folder. If this 
file is found then the main poseCall runs one of the two main funcs 
below, by-passing the standard PoseData.getNodes() call and allowing 
you to tailor the poseSaver on a folder by folder level.

Why?? well without this you have no real way to tailor a pose to 
a given rig other than setting up the preset in the hierarchy filter 
and changing the rootNode. Now that's fine for individuals but in a 
production environment you may want more control. You may want to
have specific handlers for finger poses, facial etc and this allows 
all of that to be done, animators just switch to a folder and that 
folder controls how the data is processed.

NOTE: 'poseObj' arg is the actual PoseData class instance passed into 
the calls from the main class. This allows you to monkey-patch and modify
the internal object on the fly if you need too.


example:
This is an example I use at work for our finger pose folder just to 
show what can be done here. The key is that you have to return a list 
of nodes that are then pushed into the poseData for processing.

def getNodesOverload(poseObj,nodes,*args):

    #NOTE: poseObj already has an attr 'metaRig' which is filled  
    #automatically in the main buildInternalPoseData() call
    metaNode=poseObj.metaRig

    #catch the currently selected node
    currentSelection=cmds.ls(sl=True,l=True)

    #see if we have a left or right controller selected and switch to the
    #appropriate subMetaSystem
    if cmds.getAttr('%s.mirrorSide' % currentSelection[0])==1:
        filteredNodes=metaNode.L_ArmSystem.L_Fingers_System.getChildren()
        [filtered.append(node) for node in cmds.listRelatives(filtered,type='joint',ad=True,f=True)]
        
    elif cmds.getAttr('%s.mirrorSide' % currentSelection[0])==2:
        filteredNodes=metaNode.R_ArmSystem.R_Fingers_System.getChildren()
        [filtered.append(node) for node in cmds.listRelatives(filtered,type='joint',ad=True,f=True)]
        
    #modify the actual PoseData object, changing the data to be matched on index
    #rather than using the standard name or metaMap matching
    poseObj.metaPose=False
    poseObj.matchMethod='index'
    
    return filteredNodes


In the most basic case you could just construct a list of nodes
and return that!
================================================================
'''

import Red9.core.Red9_Meta as r9Meta
import maya.cmds as cmds


def getNodesOverload(poseObj, nodes, *args):

    # NOTE: poseObj already has an attr 'metaRig' which is filled
    # automatically in the main buildInternalPoseData() call
    metaNode = poseObj.metaRig
    currentSelection = cmds.ls(sl=True, l=True)
    filteredNodes=[]
    if not issubclass(type(metaNode), r9Meta.MetaHIKControlSetNode):
        # see if we have a left or right controller selected and switch to the
        # appropriate subMetaSystem
        if cmds.getAttr('%s.mirrorSide' % currentSelection[0]) == 1:
            filteredNodes = metaNode.L_ArmSystem.L_Fingers_System.getChildren()
            [filteredNodes.append(node) for node in cmds.listRelatives(filteredNodes, type='joint', ad=True, f=True)]
            
        elif cmds.getAttr('%s.mirrorSide' % currentSelection[0]) == 2:
            filteredNodes = metaNode.R_ArmSystem.R_Fingers_System.getChildren()
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

def poseGetNodesLoad(poseObj,nodes,*args):
    '''
    PoseLoad:
    this is an entry point used to over-load the main getNodes()
    function in the PoseData object. This allows you to modify, on 
    the fly the poseObj itself as poseObj arg is the class instance
    @param poseObj: the actual instance of the PoseData object
    @param nodes: original node list passed in from the UI 
    '''
    return getNodesOverload(poseObj,nodes,*args)
    
def poseGetNodesSave(poseObj,nodes,*args):
    '''
    PoseSave:
    this is an entry point used to over-load the main getNodes()
    function in the PoseData object. This allows you to modify, on 
    the fly the poseObj itself as poseObj arg is the class instance
    @param poseObj: the actual instance of the PoseData object
    @param nodes: original node list passed in from the UI 
    '''
    return getNodesOverload(poseObj,nodes,*args)
    
def posePopupAdditions(parent, ui=None):
    '''
    This run when the Pose PopUp menu is generated, allows us to add custom menu's to the 
    popUp and extend it's functionality as we need at a folder level!
    '''
    cmds.menuItem(divider=True)
    cmds.menuItem(parent=parent,label='Test Finger Menu 1!', command="print('Added Test Menu 1')")
    cmds.menuItem(parent=parent,label='Test Finger Menu 2!', command="print('Added Test Menu 2')")

