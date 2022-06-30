'''
------------------------------------------
Red9 Studio Pack : Maya Pipeline Solutions
email: rednineinfo@gmail.com
------------------------------------------

This has been wrapped in a MPxCommand primarily so that the undo is
registered/managed and added to the undoStack. This does however also
open the plugin up for use with any mel commands.

Command= SnapTransforms(flags)

flags:  -s / -source
        -d / -destination
        -te/ -timeEnabled
        -st / -snapTranslates
        -sr / -snapRotates
        -ss / -snapScales  ( local space only )

TODO: add flags for just rotate or translate processing
'''

import maya.OpenMayaAnim as apiAnim
import maya.OpenMayaMPx as OpenMayaMPx
import maya.OpenMaya as OpenMaya
import sys


class SnapTransforms(OpenMayaMPx.MPxCommand):
         
    kPluginCmdName="SnapTransforms"
    kSourceFlag = "-s"
    kSourceLongFlag = "-source"
    kDestinationFlag = "-d"
    kDestinationLongFlag = "-destination" 
    kTimeEnabledFlag = "-te"
    kTimeEnabledLongFlag = "-timeEnabled" 
    kTimeFlag = "-t"
    kTimeLongFlag = "-time" 
    kTransFlag = "-st"
    kTransLongFlag = "-snapTranslates" 
    kRotsFlag = "-sr"
    kRotsLongFlag = "-snapRotates" 
    kScalesFlag = "-ss"
    kScalesLongFlag = "-snapScales" 

    def __init__(self):
        OpenMayaMPx.MPxCommand.__init__(self)  
        self.origTime=None
        self.origTrans=None # store the original Trans for the UndoQueue
        self.origRots=None  # store the original Rots for the UndoQueue
        self.origScales=None  # store the original Scales for the UndoQueue
        self.TimeEnabled=False  # enable time, uses the current frame
        self.atFrame=None  # specific frame to snap
        self.MFntSource=None
        self.MFntDestin=None
        self.snapTranslation=True
        self.snapRotation=True
        self.snapScales=False

    def isUndoable(self):
        '''
        Required otherwise the undo block won't get registered
        '''
        return True

    @staticmethod
    def __MFnTransformNode(node):
        '''
        from a given transform node (passed as string) return the
        actual MFnTransform from the API
        '''
        dagpath=OpenMaya.MDagPath()
        # Add to the sectectionList
        selList=OpenMaya.MSelectionList()
        selList.add(node)
        selList.getDagPath(0,dagpath)
        # Make the Main Transform Nodes
        return OpenMaya.MFnTransform(dagpath)


    #===============================================================================
    # RUNTIME : Snap Align 2 transform Nodes 
    #===============================================================================
    def doIt(self, args):
        '''
        Main call: arguements passed back from the MSyntax/MArgDatabase
        are object names as strings.
        '''
        Source=None
        Destin=None
        result=[]

        # Build the Arg List from the MSyntax/MArgDatabase, we need to 
        # do this as when called this object is in the API world not Python
        argData = OpenMaya.MArgDatabase(self.syntax(), args)
        if argData.isFlagSet(self.kSourceFlag):
            Source=argData.flagArgumentString(self.kSourceFlag, 0)
        if argData.isFlagSet(self.kDestinationFlag):
            Destin=argData.flagArgumentString(self.kDestinationFlag, 0)
        if argData.isFlagSet(self.kTimeEnabledFlag):
            self.TimeEnabled=argData.flagArgumentBool(self.kTimeEnabledFlag, 0)
        if argData.isFlagSet(self.kTransFlag):
            self.snapTranslation=argData.flagArgumentBool(self.kTransFlag, 0)
        if argData.isFlagSet(self.kRotsFlag):
            self.snapRotation=argData.flagArgumentBool(self.kRotsFlag, 0)
        if argData.isFlagSet(self.kScalesFlag):
            self.snapScales=argData.flagArgumentBool(self.kScalesFlag, 0)
        if argData.isFlagSet(self.kTimeFlag):
            self.atFrame=argData.flagArgumentDouble(self.kTimeFlag, 0)

        # Make the api.MFnTransorm Nodes
        self.MFntSource=self.__MFnTransformNode(Source)
        self.MFntDestin=self.__MFnTransformNode(Destin)

        # set the internal Time
        if self.TimeEnabled:
            # If we're not shifting timelines in the wrapper proc then
            # we don't want to set the AnimControl time as the scene is 
            # already at the correct frame
            self.origTime = apiAnim.MAnimControl().currentTime()
            apiAnim.MAnimControl.setCurrentTime(self.origTime)

        if argData.isFlagSet(self.kTimeFlag):  # and not self.atFrame == None:
            self.origTime = OpenMaya.MTime(self.atFrame, OpenMaya.MTime.uiUnit())
            apiAnim.MAnimControl.setCurrentTime(OpenMaya.MTime(self.atFrame, OpenMaya.MTime.uiUnit()))

        if self.snapTranslation:
            # --------------------------
            # DEAL WITH THE TRANSLATES :
            # --------------------------
            rotPivA=OpenMaya.MVector(self.MFntSource.rotatePivot(OpenMaya.MSpace.kWorld))
            rotPivB=OpenMaya.MVector(self.MFntDestin.rotatePivot(OpenMaya.MSpace.kWorld))
            self.origTrans = self.MFntDestin.getTranslation(OpenMaya.MSpace.kWorld)
            # We subtract the destinations translation from it's rotPivot, before adding it
            # to the source rotPiv. This compensates for offsets in the 2 nodes pivots
            targetTrans = (rotPivA + (self.origTrans - rotPivB))
            self.MFntDestin.setTranslation(targetTrans, OpenMaya.MSpace.kWorld)

        if self.snapRotation:
            # -----------------------
            # DEAL WITH THE ROTATES :
            # -----------------------
            # Fill the Undo 
            self.origRots=OpenMaya.MQuaternion()
            self.MFntDestin.getRotation(self.origRots, OpenMaya.MSpace.kWorld)

            # Read the source Quaternions and copy to destination
            Quat = OpenMaya.MQuaternion()
            self.MFntSource.getRotation(Quat, OpenMaya.MSpace.kWorld)
            self.MFntDestin.setRotation(Quat, OpenMaya.MSpace.kWorld)

        if self.snapScales:
            # -----------------------
            # DEAL WITH THE SCALES : (local only) Testing
            # -----------------------
            # Fill the Undo 
            util = OpenMaya.MScriptUtil()
            util.createFromList( [1.0, 1.0, 1.0], 3 )
            scalepntr = util.asDoublePtr()
            self.MFntDestin.getScale(scalepntr)
            sx = OpenMaya.MScriptUtil().getDoubleArrayItem(scalepntr, 0)
            sy = OpenMaya.MScriptUtil().getDoubleArrayItem(scalepntr, 1)
            sz = OpenMaya.MScriptUtil().getDoubleArrayItem(scalepntr, 2)
            self.origScales=[sx, sy, sz]

            # Read the source scales and copy to destination
            self.MFntSource.getScale(scalepntr)
            self.MFntDestin.setScale(scalepntr)    

#             mmatrix = OpenMaya.MTransformationMatrix()
#             mmatrix.setScale(scalePtr, OpenMaya.MSpace.kWorld)

        # set the returns
        OpenMayaMPx.MPxCommand.clearResult()
        OpenMayaMPx.MPxCommand.setResult(True)

    def redoIt(self):
        pass
 
    def undoIt(self):
        '''
        Build up the undo command data
        '''
        if self.TimeEnabled:
            apiAnim.MAnimControl.setCurrentTime(self.origTime)
        if self.origTrans:
            self.MFntDestin.setTranslation(self.origTrans,OpenMaya.MSpace.kWorld)
        if self.origRots:
            self.MFntDestin.setRotation(self.origRots,OpenMaya.MSpace.kWorld)
        if self.origScales:
            util = OpenMaya.MScriptUtil()
            util.createFromList( self.origScales, 3 )
            scalepntr = util.asDoublePtr()
            self.MFntDestin.setScale(scalepntr)

    @classmethod
    def cmdCreator(cls):
        # Create the command
        return OpenMayaMPx.asMPxPtr( SnapTransforms() )

    # Syntax creator : Builds the argument strings up for the command
    @classmethod
    def syntaxCreator(cls):
        syntax = OpenMaya.MSyntax()
        syntax.addFlag(cls.kSourceFlag, cls.kSourceLongFlag, OpenMaya.MSyntax.kString)
        syntax.addFlag(cls.kDestinationFlag, cls.kDestinationLongFlag, OpenMaya.MSyntax.kString)
        syntax.addFlag(cls.kTimeEnabledFlag, cls.kTimeEnabledLongFlag, OpenMaya.MSyntax.kBoolean)
        syntax.addFlag(cls.kTransFlag, cls.kTransLongFlag, OpenMaya.MSyntax.kBoolean)
        syntax.addFlag(cls.kRotsFlag, cls.kRotsLongFlag, OpenMaya.MSyntax.kBoolean)
        syntax.addFlag(cls.kScalesFlag, cls.kScalesLongFlag, OpenMaya.MSyntax.kBoolean)
        syntax.addFlag(cls.kTimeFlag, cls.kTimeLongFlag, OpenMaya.MSyntax.kDouble)
        return syntax

# Initialize the plug-in 
def initializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject, "Red9", "1.5", "Any")
    try:
        mplugin.registerCommand( SnapTransforms.kPluginCmdName, SnapTransforms.cmdCreator, SnapTransforms.syntaxCreator )
    except:
        sys.stderr.write( "Failed to register command: %s\n" % SnapTransforms.kPluginCmdName )
        raise

# Uninitialize the plug-in 
def uninitializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        mplugin.deregisterCommand( SnapTransforms.kPluginCmdName )
    except:
        sys.stderr.write( "Failed to unregister command: %s\n" % SnapTransforms.kPluginCmdName )
        raise
