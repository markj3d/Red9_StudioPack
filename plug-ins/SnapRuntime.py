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
    kTimeFlag = "-te"
    kTimeLongFlag = "-timeEnabled" 
    kTransFlag = "-st"
    kTransLongFlag = "-snapTranslates" 
    kRotsFlag = "-sr"
    kRotsLongFlag = "-snapRotates" 
    
    def __init__(self):
        OpenMayaMPx.MPxCommand.__init__(self)  
        self.origTime=None
        self.origTrans=[] #store the original Trans for the UndoQueue
        self.origRots=[]  #store the original Rots for the UndoQueue
        self.TimeEnabled=False 
        self.MFntSource=None
        self.MFntDestin=None
        self.snapTranslation=True
        self.snapRotation=True
    
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
        #Add to the sectectionList
        selList=OpenMaya.MSelectionList()
        selList.add(node)
        selList.getDagPath(0,dagpath)
        #Make the Main Transform Nodes
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

        #Build the Arg List from the MSyntax/MArgDatabase, we need to 
        #do this as when called this object is in the API world not Python
        argData = OpenMaya.MArgDatabase(self.syntax(), args)
        if argData.isFlagSet(self.kSourceFlag):
            Source=argData.flagArgumentString(self.kSourceFlag, 0)
        if argData.isFlagSet(self.kDestinationFlag):
            Destin=argData.flagArgumentString(self.kDestinationFlag, 0)
        if argData.isFlagSet(self.kTimeFlag):
            self.TimeEnabled=argData.flagArgumentBool(self.kTimeFlag, 0)  
        if argData.isFlagSet(self.kTransFlag):
            self.snapTranslation=argData.flagArgumentBool(self.kTransFlag, 0)  
        if argData.isFlagSet(self.kRotsFlag):
            self.snapRotation=argData.flagArgumentBool(self.kRotsFlag, 0)  
            #print ('timeEnabled',self.TimeEnabled) 

        #Make the api.MFnTransorm Nodes
        self.MFntSource=self.__MFnTransformNode(Source)
        self.MFntDestin=self.__MFnTransformNode(Destin)
        
        #set the internal Time
        if self.TimeEnabled:
            #If we're not shifting timelines in the wrapper proc then
            #we don't want to set the AnimControl time as the scene is 
            #already at the correct frame
            self.origTime=apiAnim.MAnimControl().currentTime()
            apiAnim.MAnimControl.setCurrentTime(self.origTime)
        
        if self.snapTranslation:
            #--------------------------
            #DEAL WITH THE TRANSLATES :
            #--------------------------
            rotPivA=OpenMaya.MVector(self.MFntSource.rotatePivot(OpenMaya.MSpace.kWorld))
            rotPivB=OpenMaya.MVector(self.MFntDestin.rotatePivot(OpenMaya.MSpace.kWorld))
            self.origTrans=self.MFntDestin.getTranslation(OpenMaya.MSpace.kWorld)
            #We subtract the destinations translation from it's rotPivot, before adding it
            #to the source rotPiv. This compensates for offsets in the 2 nodes pivots
            targetTrans=(rotPivA + (self.origTrans - rotPivB))
            self.MFntDestin.setTranslation(targetTrans ,OpenMaya.MSpace.kWorld)
            result.append(targetTrans)
            
        if self.snapRotation:
            #-----------------------
            #DEAL WITH THE ROTATES :
            #-----------------------
            #Fill the Undo 
            self.origRots=OpenMaya.MQuaternion()
            self.MFntDestin.getRotation(self.origRots,OpenMaya.MSpace.kWorld)
            
            #Read the source Quaternions and copy to destination
            Quat = OpenMaya.MQuaternion()
            self.MFntSource.getRotation(Quat,OpenMaya.MSpace.kWorld)
            self.MFntDestin.setRotation(Quat,OpenMaya.MSpace.kWorld)
            result.append(Quat)
        
        #set the returns
        OpenMayaMPx.MPxCommand.clearResult()
        #Pass back the destination co-ordinates required
        #OpenMayaMPx.MPxCommand.setResult([targetTrans,Quat])
        OpenMayaMPx.MPxCommand.setResult(result)

        
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
        syntax.addFlag(cls.kTimeFlag, cls.kTimeLongFlag, OpenMaya.MSyntax.kBoolean)
        syntax.addFlag(cls.kTransFlag, cls.kTransLongFlag, OpenMaya.MSyntax.kBoolean)
        syntax.addFlag(cls.kRotsFlag, cls.kRotsLongFlag, OpenMaya.MSyntax.kBoolean)
        return syntax
    
    
    
# Initialize the plug-in 
def initializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject, "Red9", "1.0", "Any")
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
       
    