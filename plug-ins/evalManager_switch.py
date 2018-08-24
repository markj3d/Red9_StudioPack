'''
------------------------------------------
Red9 Studio Pack : Maya Pipeline Solutions
email: rednineinfo@gmail.com
------------------------------------------

This has been wrapped in a MPxCommand purely so that switching the evalManager
state in 2016 is registered to the undoStack for other functions to manage

Command= evalManager_switch(mode='off')

flags:  -m / -mode

'''

import maya.OpenMayaMPx as OpenMayaMPx
import maya.OpenMaya as OpenMaya
import maya.cmds as cmds
import sys



class evalManager_switch(OpenMayaMPx.MPxCommand):
                     
    kPluginCmdName="evalManager_switch"
    kModeFlag = "-m"
    kModeLongFlag = "-mode"
    
    def __init__(self):
        OpenMayaMPx.MPxCommand.__init__(self)  
        self.undostate=cmds.evaluationManager(mode=True,q=True)[0]
    
    def isUndoable(self):
        '''
        Required otherwise the undo block won't get registered
        '''
        return True
           
    def doIt(self, args):
        '''
        simple switch of the evalManager JUST to get it registered in the undo stack
        '''
        argData = OpenMaya.MArgDatabase(self.syntax(), args)
        if argData.isFlagSet(self.kModeFlag):
            mode=argData.flagArgumentString(self.kModeFlag, 0)
        cmds.evaluationManager(mode=mode)
        #sys.stdout.write("evalManager_switch.doIt : setting mode=%s\n" % mode)
        OpenMayaMPx.MPxCommand.clearResult()
        OpenMayaMPx.MPxCommand.setResult(self.undostate)
        
    def redoIt(self):
        pass
             
    def undoIt(self):
        '''
        Build up the undo command data
        '''
        #sys.stdout.write("evalManager_switch.undoIt : mode=%s\n" % self.undostate)
        cmds.evaluationManager(mode=self.undostate)
        
    @classmethod
    def cmdCreator(cls):
        # Create the command
        return OpenMayaMPx.asMPxPtr(evalManager_switch())
    
    # Syntax creator : Builds the argument strings up for the command
    @classmethod
    def syntaxCreator(cls):
        syntax = OpenMaya.MSyntax()
        syntax.addFlag(cls.kModeFlag, cls.kModeLongFlag, OpenMaya.MSyntax.kString)
        return syntax
    
  
# Initialize the plug-in 
def initializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject, "Red9", "1.0", "Any")
    try:
        mplugin.registerCommand(evalManager_switch.kPluginCmdName, evalManager_switch.cmdCreator, evalManager_switch.syntaxCreator )
    except:
        sys.stderr.write( "Failed to register command: %s\n" % evalManager_switch.kPluginCmdName )
        raise

# Uninitialize the plug-in 
def uninitializePlugin(mobject):
    mplugin = OpenMayaMPx.MFnPlugin(mobject)
    try:
        mplugin.deregisterCommand( evalManager_switch.kPluginCmdName )
    except:
        sys.stderr.write( "Failed to unregister command: %s\n" % evalManager_switch.kPluginCmdName )
        raise
       
    