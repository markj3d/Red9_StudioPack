'''
This is intended as an example of how to sub-class metaData for your own systems,
I'll be going through this in Part4 of the MetaData series on the Red9 Vimeo Channel!


'''

import Red9.core.Red9_Meta as r9Meta
import maya.cmds as cmds


class MetaExportTagBase(r9Meta.MetaClass):
    '''
    Example Export base class inheriting from MetaClass
    '''
    def __init__(self,*args,**kws):
        super(MetaExportTagBase, self).__init__(*args,**kws) 
        
        #By default lockState=False meaning the MetaNode can easily be deleted 
        #from Maya. By locking it can't get cleaned accidentally.
        self.lockState=True 
                
    def __bindData__(self):
        '''
        bindData allows you to set default attrs on your node, any changes
        in this will be reflected everytime the node is instanciated
        '''
        self.addAttr('version',attrType='float',min=0,max=3)
        self.addAttr('exportPath', attrType='string')
        self.addAttr('exportRoot', attrType='messageSimple')
        
    def getExportPath(self):
        self.exportPath=cmds.file(q=True,sn=True)

    def getNodes(self):
        return self.exportRoot

    def  validate(self):
        return True
    
    
class MetaExportTag_Character(MetaExportTagBase):
    '''
    Example Export subclass for characters
    '''
    def __init__(self,*args,**kws):
        super(MetaExportTag_Character, self).__init__(*args,**kws) 
        
    def getNodes(self):
        '''
        overloaded get method for character skeleton for example
        '''
        return cmds.ls(cmds.listRelatives(self.exportRoot,type='joint',ad=True),l=True)

class MetaExportTag_Environment(MetaExportTagBase):
    '''
    Example Export subclass for environment
    '''
    def __init__(self,*args,**kws):
        super(MetaExportTag_Environment, self).__init__(*args,**kws) 
        
        


class MyMetaCharacter(r9Meta.MetaRig):
    '''
    Example custom mRig class inheriting from MetaRig
    '''
    def __init__(self,*args,**kws):
        super(MyMetaCharacter, self).__init__(*args,**kws) 
        self.lockState=True
        
    def __bindData__(self):
        '''
        bind our default attrs to this node
        '''
        self.addAttr('myRigType','')
        self.addAttr('myFloat', attrType='float', min=0, max=10)
        self.addAttr('myEnum', enumName='A:B:D:E:F', attrType='enum')

#     def getChildren(self, walk=False, mAttrs=None, cAttrs=None):
#         '''
#         overload call for getChildren
#         '''
#         pass
#        
#     def getSkeletonRoots(self):
#         '''
#         get the Skeleton Root, used in the poseSaver. By default this looks
#         for a message link via the attr "exportSkeletonRoot" to the skeletons root jnt
#         always returns a list!
#         '''
#         pass 
#         
#     def getNodeConnectionMetaDataMap(self, node, mTypes=[]):  
#         '''
#         This is used by the poseSaver to build up exactly what data we
#         store for the child nodes. It needs to return a dict which is then 
#         used by both the load and save pose calls to map the data
#         '''
#         pass
    
    #@r9Meta.nodeLockManager
    def delMyAttr(self):
        '''
        with self.lockState=True the Maya node used is node Locked so 
        in order to set any attrs on it, we need to manage the lockNode
        state. This is what the 'nodeLockManager' decorator is used for
        '''
        #del(self.myNew) #this will always work as it's managed internally
        
        #this will fail without the decorator
        cmds.deleteAttr('%s.myNew' % self.mNode)

  
class MyCameraMeta(r9Meta.MetaClass):
    '''
    Example showing that metaData isn't limited to 'network' nodes,
    by using the 'nodeType' arg in the class __init__ you can modify 
    the general behaviour such that meta creates any type of Maya node.
    '''
    def __init__(self,*args,**kws):
        super(MyCameraMeta, self).__init__(nodeType='camera',*args,**kws) 
        
 
     
#========================================================================
# This HAS to be at the END of this module so that the RED9_META_REGISTRY
# picks up all inherited subclasses contained within. 
# When this module is imported all subclasses will be added to the registry. 
# I have to do this as outside of a controlled production environment 
# I can't guarantee the Maya / Python boot sequence.
#========================================================================   
r9Meta.registerMClassInheritanceMapping()


#========================================================================
# This block is ONLY needed if you want to register other nodeTypes
# to the metaData systems as in the camera example above. Note that 
# ANY node can be used in Meta, this registry is ONLY needed if you 
# want a specific nodeType to be generated for full metaData handling
#======================================================================== 
r9Meta.registerMClassNodeMapping(nodeTypes='camera')

