'''

..
    Red9 Studio Pack: Maya Pipeline Solutions
    Author: Mark Jackson
    email: rednineinfo@gmail.com
    
    Red9 blog : http://red9-consultancy.blogspot.co.uk/
    MarkJ blog: http://markj3d.blogspot.co.uk
    
    
    This is the Core of the MetaNode implementation of the systems.
    
    NOTE: if you're inheriting from 'MetaClass' in your own class you
    need to make sure that the registerMClassInheritanceMapping() is called
    such that the global RED9_META_REGISTERY is rebuilt and includes
    your inherited class.


Basic MetaClass Use:
--------------------

Now moved to the examples folder for more detailed explanations

- *Red9/examples/MetaData_Getting_started.py* 
- *Red9/examples/MetaRig_Morpheus.py* 

Also see the unittesting folder to see what the code can do and
what each function is expected to return

- *Red9/tests* 
    
'''


import maya.cmds as cmds
import maya.mel as mel
import maya.OpenMaya as OpenMaya
from functools import partial
from functools import wraps
import sys
import os
import uuid

import Red9.startup.setup as r9Setup
import Red9_General as r9General
import Red9_CoreUtils as r9Core
import Red9_AnimationUtils as r9Anim

# Language map is used for all UI's as a text mapping for languages
LANGUAGE_MAP = r9Setup.LANGUAGE_MAP


# =============================================
# NOTE: we can't import anything else here that imports this
# Module as it screw the Class Registry and we get Cyclic imports
# hence the r9Anim is LazyLoaded where needed
# import Red9_AnimationUtils as r9Anim
# =============================================


import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

try:
    import json as json
except:
    #Meta Fails under Maya2009 because of Python2.5 issues
    log.warning('json is not supported in Python2.5')
    #import Red9.packages.simplejson as json
    
    
global RED9_META_NODECACHE
RED9_META_NODECACHE = {}

global RED9_META_CALLBACKS
RED9_META_CALLBACKS = {}
RED9_META_CALLBACKS['Open'] = []
RED9_META_CALLBACKS['New'] = []
#RED9_META_CALLBACKS['DuplicatePre'] = []
#RED9_META_CALLBACKS['DuplicatePost'] = []
        

global __RED9_META_NODESTORE__
__RED9_META_NODESTORE__ = []

'''
CRUCIAL - REGISTER INHERITED CLASSES! ==============================================
Register available MetaClass's to a global so that other modules could externally 
extend the functionality and use the base MetaClass. Note we're building this up 
from only those active Python classes who inherit from MetaClass 
global RED9_META_REGISTERY 
====================================================================================
'''
def registerMClassInheritanceMapping():
    global RED9_META_REGISTERY
    RED9_META_REGISTERY={}
    RED9_META_REGISTERY['MetaClass']=MetaClass
    for mclass in r9General.itersubclasses(MetaClass):
        log.debug('registering : %s' % mclass)
        RED9_META_REGISTERY[mclass.__name__]=mclass
  
def printSubClassRegistry():
    for m in RED9_META_REGISTERY:
        print m
    
def getMClassMetaRegistry():
    '''
    Generic getWrapper to return the Registry from the global
    '''
    return RED9_META_REGISTERY

def getMClassInstances(mInstances):
    '''
    return a list of Registered metaClasses that are subclassed from the given
    classes. This is so in code/UI's you can group metaClasses by their
    inheritance . . . ie, give me all export metaClasses that are registered
    
    :param mInstanes: given metaClass to test inheritance - cls or [cls]
    '''
    subClasses=[]
    if not type(mInstances)==list:
        mInstances=[mInstances]
    for mClass in RED9_META_REGISTERY.values():
        for instance in mInstances:
            if issubclass(mClass, instance):
                subClasses.append(mClass)
    return subClasses

def mTypesToRegistryKey(mTypes):
    '''
    make sure we're dealing with a list of class keys to process
    against the registry. Allows us to pass in str 'MetaRig' or
    r9Meta.MetaRig to the args for type checking
    '''
    if not type(mTypes)==list:
        mTypes=[mTypes]
    keys=[]
    for cls in mTypes:
        try:
            keys.append(cls.__name__)
        except:
            keys.append(cls)
    return keys

def getMClassDataFromNode(node):
    '''
    from the node get the class to instantiate, this gives us a level of
    flexibility over mClass attr rather than pure hard coding as it was previously
    '''
    try:
        if cmds.attributeQuery('mClass', exists=True, node=node):
            mClass=cmds.getAttr('%s.%s' % (node,'mClass'))
            if mClass in RED9_META_REGISTERY:
                return mClass
            elif cmds.attributeQuery('mClassGrp', exists=True, node=node):
                mClass=cmds.getAttr('%s.%s' % (node,'mClassGrp'))
                if mClass in RED9_META_REGISTERY:
                    return mClass
        elif 'Meta%s' % cmds.nodeType(node) in RED9_META_REGISTERY.keys():
            return 'Meta%s' % cmds.nodeType(node)
    except:
        #node is ALREADY MetaClass instance?
        if issubclass(type(node), MetaClass):
            log.debug('getMClassFromNode was given an already instanciated MNode')
            return node.mClass
        else:
            raise StandardError('getMClassFromNode failed for node : %s' % node)

    
# NodeType Management ---------------------------
  
 
def registerMClassNodeMapping(nodeTypes=[]):
    '''
    Hook to allow you to extend the type of nodes included in all the
    getMeta searches. Allows you to expand into using nodes of any type
    as metaNodes
    
    :param nodeTypes: allows you to expand metaData and use any nodeType
                    default is always 'network'
 
    .. note::
        this now validates 'nodeTypes' against Maya registered nodeTypes before being
        allowed into the registry. Why, well lets say you have a new nodeType from a
        plugin but that plugin isn't currently loaded, this now stops that type being
        generically added by any custom boot sequence.
    '''
    baseTypes=['network','objectSet','HIKCharacterNode','HIKControlSetNode']
    
    global RED9_META_NODETYPE_REGISTERY
    if nodeTypes and RED9_META_NODETYPE_REGISTERY:
        baseTypes = RED9_META_NODETYPE_REGISTERY
    RED9_META_NODETYPE_REGISTERY = []
    
    if nodeTypes:
        if not type(nodeTypes)==list:
            nodeTypes=[nodeTypes]
        [baseTypes.append(n) for n in nodeTypes if not n in baseTypes]
        #baseTypes.extend(nodeTypes)
    try:
        MayaRegisteredNodes=cmds.allNodeTypes()
        
        for nType in baseTypes:
            if not nType in RED9_META_NODETYPE_REGISTERY and nType in MayaRegisteredNodes:
                log.debug('nodeType : "%s" : added to NODETYPE_REGISTRY' % nType)
                RED9_META_NODETYPE_REGISTERY.append(nType)
            else:
                log.debug('nType: "%s" is an invalid Maya NodeType' % nType)
    except:
        log.warning('registerMClassNodeMapping failure - seems to have issues in Maya2009')
        #raise StandardError('registerMClassNodeMapping failure - seems to have issues in Maya2009')
  
def printMetaTypeRegistry():
    for t in RED9_META_NODETYPE_REGISTERY:
        print t
    
def getMClassNodeTypes():
    '''
    Generic getWrapper for all nodeTypes registered in the Meta_NodeType global
    '''
    return RED9_META_NODETYPE_REGISTERY

def resetMClassNodeTypes():
    registerMClassNodeMapping(nodeTypes=None)

    
    
    
    
# NodeCache Management ---------------------------

def generateUUID():
    '''
    unique UUID used by the caching system
    '''
    return str(uuid.uuid4()).upper()
    
def registerMClassNodeCache(mNode):
    '''
    Add a given mNode to the global RED9_META_NODECACHE cache of currently instantiated 
    MetaNode objects.
    
    :param mNode: instantiated mNode to add
    '''
    global RED9_META_NODECACHE
    version=r9Setup.mayaVersion()

    if mNode.hasAttr('UUID') or version>=2015:
        try:
            if version<=2015:
                UUID=mNode.UUID
                if not UUID:
                    log.debug('CACHE : generating fresh UUID')
                    UUID=mNode.setUUID()
                elif UUID in RED9_META_NODECACHE.keys():
                    log.debug('CACHE : UUID is already registered in cache')
                    if not mNode.mNode == RED9_META_NODECACHE[UUID]:
                        log.debug('CACHE : %s : UUID is registered to a different node : modifying UUID: %s' % (UUID, mNode.mNode))
                        UUID=mNode.setUUID()
            else:
                UUID=cmds.ls(mNode.mNode, uuid=True)[0]
            if RED9_META_NODECACHE or not UUID in RED9_META_NODECACHE.keys():
                log.debug('CACHE : Adding to MetaNode UUID Cache : %s > %s' % (mNode.mNode, UUID))
                RED9_META_NODECACHE[UUID]=mNode
        except StandardError, err:
            #print err
            log.debug('CACHE : Failed to set UUID for mNode : %s' % mNode.mNode)
    else:
        log.debug('CACHE : UUID attr not bound to this node, must be an older system')
        if RED9_META_NODECACHE or not mNode.mNode in RED9_META_NODECACHE.keys():
            log.debug('CACHE : Adding to MetaNode Cache : %s' % mNode.mNode)
            RED9_META_NODECACHE[mNode.mNode]=mNode
            
def getMetaFromCache(mNode):
    '''
    Pull the given mNode from the RED9_META_NODECACHE if it's
    already be instantiated.
    
    :param mNode: str(name) of node from DAG
    '''
    try:
        if r9Setup.mayaVersion()<=2015:
            UUID=cmds.getAttr('%s.UUID' % mNode)
        else:
            UUID=cmds.ls(mNode, uuid=True)[0]
        if UUID in RED9_META_NODECACHE.keys():
            try:
                if RED9_META_NODECACHE[UUID].isValidMObject():
                    if not RED9_META_NODECACHE[UUID]._MObject == getMObject(mNode):
                        log.debug('CACHE : %s : UUID is already registered but to a different node : %s' % (UUID,mNode))
                        return
                    log.debug('CACHE : %s Returning mNode from UUID cache! = %s' % (mNode,UUID))
                    return RED9_META_NODECACHE[UUID]
                else:
                    log.debug('%s being Removed from the cache due to invalid MObject' % mNode)
                    cleanCache()
            except:
                log.debug('CACHE : inspection failure')
    except:
        if mNode in RED9_META_NODECACHE.keys():
            try:
                if RED9_META_NODECACHE[mNode].isValidMObject():
                    #print 'namebased returned from cache ', mNode
                    log.debug('CACHE : %s Returning mNode from nameBased cache!' % mNode)
                    return RED9_META_NODECACHE[mNode]
                else:
                    log.debug('%s being Removed from the cache due to invalid MObject' % mNode)
                    cleanCache()
            except:
                log.debug('CACHE : inspection failure')
        
def upgrade_toLatestBindings(*args):
    '''
    take a current scene and upgrade all the mNodes to include any new
    binding attrs that the base class may have been upgraded to use.
    '''
    for node in getMetaNodes():
        try:
            # mNodeUUID attrs used for the Cache system
            if node.hasAttr('mNodeUUID'):
                delattr(node, 'mNodeUUID')
            if not node.hasAttr('UUID'):
                node.addAttr('UUID', value='')
                uuid=node.setUUID()
                log.info('Upgraded node : %s  to UUID : %s' % (r9Core.nodeNameStrip(node.mNode), uuid))
                
            # mClassGrp attr used to ID systems and search with
            if not node.hasAttr('mClassGrp'):
                node.addAttr('mClassGrp', value='MetaClass', hidden=True)
                log.info('Upgraded node : %s  to mClassGrp' % r9Core.nodeNameStrip(node.mNode))
                
            # mSystemRoot - added to mark a node as a root in a system even if it's not physically a root
            if not node.hasAttr('mSystemRoot'):
                node.addAttr('mSystemRoot', value=False, hidden=True)
                log.info('Upgraded node : %s  to mSystemRoot' % r9Core.nodeNameStrip(node.mNode))
        except:
            log.info('Failed to Upgrade mNode : %s' % node)
    resetCache()
            
def printMetaCacheRegistry():
    '''
    print the current VALID Cache of instantiated MetaNodes 
    Note that we call a cleanCache before printing to remove any 
    currently invalid MObjects from the Cache.
    '''
    cleanCache()
    for k,v in RED9_META_NODECACHE.items():
        print '%s : %s : %s' % (k,r9Core.nodeNameStrip(v.mNode),v)
 
def cleanCache():
    '''
    Run through the current cache of metaNodes and confirm that they're 
    all still valid by testing the MObjectHandles.
    '''
    for k, v in RED9_META_NODECACHE.items():
        try:
            if not v.isValidMObject():
                RED9_META_NODECACHE.pop(k)
                log.debug('CACHE : %s being Removed from the cache due to invalid MObject' % k)
        except:
            log.debug('CACHE : clean failure')

def removeFromCache(mNodes):
    for k, v in RED9_META_NODECACHE.items():
        if not hasattr(mNodes, '__iter__'):
            mNodes=[mNodes]
        if v in mNodes:
            try:
                RED9_META_NODECACHE.pop(k)
                log.debug('CACHE : %s being Removed from the cache >> %s' % (r9Core.nodeNameStrip(k),r9Core.nodeNameStrip(v.mNode)))
            except:
                log.debug('CACHE : Failed to remove %s from cache')
    
def resetCache(*args):
    global RED9_META_NODECACHE
    RED9_META_NODECACHE={}

def resetCacheOnSceneNew(*args):
    resetCache()
    log.info('"file Open" or "file new" called - Red9 MetaCache being cleared')
    
def getMClassNodeCache():
    '''
    Generic getWrapper for all nodeTypes registered in the Meta_NodeType global
    '''
    return RED9_META_NODECACHE

def __preDuplicateCache(*args):
    '''
    DEPRICATED : PRE-DUPLICATE : on the duplicate call in Maya (bound to a callback) pre-store all current mNodes
    '''
    global __RED9_META_NODESTORE__
    __RED9_META_NODESTORE__= getMetaNodes(dataType='dag')
    #print 'pre-callback : nodelist :', __RED9_META_NODESTORE__
    
def __poseDuplicateCache(*args):
    '''
    DEPRICATED : POST-DUPLICATE : if we find the duplicate node in the cache re-generate it's UUID
    '''
    global __RED9_META_NODESTORE__
    
    #no metaNode in the cache so pull out fast
    if not __RED9_META_NODESTORE__:
        return

    newNodes=[node for node in getMetaNodes(dataType='dag') if not node in __RED9_META_NODESTORE__]
    for node in newNodes:
        #note we set this via cmds so that the node isn't instantiated until the UUID is modified
        if cmds.attributeQuery('UUID', node=node, exists=True):
            cmds.setAttr('%s.UUID' % node, generateUUID(), type='string')
    #print 'post-callback : nodelist :', newNodes

def getMObject(node):
    '''
    base wrapper to get the MObject from node
    '''
    mobj=OpenMaya.MObject()
    selList=OpenMaya.MSelectionList()
    selList.add(node)
    selList.getDependNode(0,mobj)
    return mobj
                    
# ====================================================================================
    
    
    
def attributeDataType(val):
    '''
    Validate the attribute type for all the cmds handling
    '''
    if issubclass(type(val),str):
        log.debug('Val : %s : is a string' % val)
        return 'string'
    if issubclass(type(val),unicode):
        log.debug('Val : %s : is a unicode' % val)
        return 'unicode'
    if issubclass(type(val),bool):
        log.debug('Val : %s : is a bool')
        return 'bool'
    if issubclass(type(val),int):
        log.debug('Val : %s : is a int')
        return 'int'
    if issubclass(type(val),float):
        log.debug('Val : %s : is a float')
        return 'float'
    if issubclass(type(val),dict):
        log.debug('Val : %s : is a dict')
        return 'complex'
    if issubclass(type(val),list):
        log.debug('Val : %s : is a list')
        return 'complex'
    if issubclass(type(val),tuple):
        log.debug('Val : %s : is a tuple')
        return 'complex'
        
#@pymelHandler
def isMetaNode(node, mTypes=[]):
    '''
    Simple bool, Maya Node is or isn't an mNode

    :param node: Maya node to test
    :param mTypes: only match given MetaClass's - str or class accepted
    .. note:: 
    
        this does not instantiate the mClass to query it like the
        isMetaNodeInherited which has to figure the subclass mapping
    '''
    mClassInstance=False
    if not node:
        return False
    if issubclass(type(node), MetaClass):
        node=node.mNode
        mClassInstance=True
    mClass=getMClassDataFromNode(node)
    if mClass:
        if mClass in RED9_META_REGISTERY:
            if mTypes:
                if mClass in mTypesToRegistryKey(mTypes):
                    return True
                else:
                    return False
            else:
                return True
        else:
            log.debug('isMetaNode>>InValid MetaClass attr : %s' % mClass)
            return False
    else:
        if mClassInstance:
            log.debug('isMetaNode = True : node is a Wrapped StandardMaya Node MClass instance')
            return True
        else:
            return False

#def isMetaNodeInherited(node, mInstances=[]):
#    '''
#    unlike isMetaNode which checks the node against a particular MetaClass,
#    this expands the check to see if the node is inherited from or a subclass of
#    a given Meta base class, ie, part of a system
#    TODO : we COULD return the instantiated metaClass object here rather than just a bool??
#    '''
#    if isMetaNode(node):
#        mClass=MetaClass(node) #instantiate the metaClass so we can work out subclass mapping
#        for inst in mTypesToRegistryKey(mInstances):
#            #log.debug('testing class inheritance: %s > %s' % ( inst, RED9_META_REGISTERY[inst],type(mClass)))
#            if issubclass(type(mClass), RED9_META_REGISTERY[inst]):
#                log.debug('MetaNode %s is of subclass >> %s' % (mClass,inst))
#                return True

def isMetaNodeInherited(node, mInstances=[]):
    '''
    unlike isMetaNode which checks the node against a particular MetaClass,
    this expands the check to see if the node is inherited from or a subclass of
    a given Meta base class, ie, part of a system
    TODO : we COULD return the instantiated metaClass object here rather than just a bool??
    '''
    if not node:
        return False
    if issubclass(type(node), MetaClass):
        node=node.mNode
    mClass=getMClassDataFromNode(node)
    if mClass and mClass in RED9_META_REGISTERY:
        for inst in mTypesToRegistryKey(mInstances):
            log.debug('testing class inheritance: %s > %s' % (inst, mClass))
            if issubclass(RED9_META_REGISTERY[mClass], RED9_META_REGISTERY[inst]):
                log.debug('MetaNode %s is of subclass >> %s' % (mClass,inst))
                return True
    return False

def isMetaNodeClassGrp(node, mClassGrps=[]):
    '''
    check the mClassGrp attr to see if it matches the given
    '''
    if not node:
        return False
    if issubclass(type(node), MetaClass):
        node=node.mNode
    if not hasattr(mClassGrps,'__iter__'):
        mClassGrps=[mClassGrps]
    for grp in mClassGrps:
        log.debug('mGroup testing: %s' % node)
        try:
            if cmds.getAttr('%s.mClassGrp' % node) == grp:
                return True
        except:
            log.debug('mNode has no MClassGrp attr, must be a legacy system and needs updating!! %s' % node)

            
@r9General.Timer
def getMetaNodes(mTypes=[], mInstances=[], mClassGrps=[], mAttrs=None, dataType='mClass', nTypes=None, mSystemRoot=False, **kws):
    '''
    Get all mClass nodes in scene and return as mClass objects if possible
    :param mTypes: only return meta nodes of a given type
    :param mInstances: idea - this will check subclass inheritance, ie, MetaRig would
            return ALL nodes who's class is inherited from MetaRig. Allows you to
            group the data more efficiently by base classes and their inheritance
    :param mClassGrps: checks the mClassGrp used to soft grp nodes and mark ones as a certain
            system type without looking at class inheritance. Good for marking key classes as bases
    :param mAttrs: uses the FilterNode.lsSearchAttributes call to match nodes via given attrs
    :param dataType: default='mClass' return the nodes already instantiated to
                the correct class object. If not then return the Maya node itself
    :param nTypes: only inspect nodes of a given Type
    '''
    mNodes=[]
    if not nTypes:
        nodes = cmds.ls(type=getMClassNodeTypes(), l=True)
    else:
        nodes = cmds.ls(type=nTypes, l=True)
    if not nodes:
        return mNodes
    for node in nodes:
        mNode=False
        if not mInstances:
            if isMetaNode(node, mTypes=mTypes):
                mNode=True
        else:
            if isMetaNodeInherited(node,mInstances):
                mNode=True
        if mNode:
            if mClassGrps:
                if not hasattr(mClassGrps,'__iter__'):
                    mClassGrps=[mClassGrps]
                if isMetaNodeClassGrp(node, mClassGrps):
                    mNodes.append(node)
            else:
                mNodes.append(node)
    if not mNodes:
        return mNodes
    if mAttrs:
        #lazy to avoid cyclic imports
        import Red9_CoreUtils as r9Core
        mNodes=r9Core.FilterNode().lsSearchAttributes(mAttrs, nodes=mNodes)
    if dataType=='mClass':
        return[MetaClass(node,**kws) for node in mNodes]
    else:
        return mNodes


def getMetaRigs(mInstances='MetaRig', mClassGrps=['MetaRig']):
    '''
    Wrapper over the get call to fire back specifically MetaRigs.
    We use mInstances rather than mTypes directly for MetaRig to 
    cope with people subclassing, then we clamp the search to the Root MetaRig
    using the mClassGrps variable. This probably will expand as it's tested
    '''
    mRigs=getMetaNodes(mInstances=mInstances, mClassGrps=mClassGrps)
    if mRigs:
        return mRigs
    else:
        return getMetaNodes(mTypes=mInstances)
    
def getUnregisteredMetaNodes():
    '''
    Inspect all nodes for the mClass attrs, then see if those nodes and mClass
    types are currently registered in the systems. This means you can inspect
    files from others who have bespoke MClass's and still see their node structures
    even though you won't be able to use or return their class objects
    '''
    mNodes=getMetaNodes(dataType='node')
    return [node for node in cmds.ls('*.mClass',l=True, o=True) if not node in mNodes]
    
    
@r9General.Timer
def getConnectedMetaNodes(nodes, source=True, destination=True, mTypes=[], mInstances=[], \
                          mAttrs=None, dataType='mClass', nTypes=None, **kws):
    '''
    From a given set of Maya Nodes return all connected mNodes
    Default return is mClass objects
    
    :param nodes: nodes to inspect for connected meta data, note these are cmds MAYA nodes
    :param source: `bool` clamp the search to the source side of the graph
    :param destination: `bool` clamp the search to the destination side of the graph
    :param mTypes: return only given MetaClass's
    :param mInstances: this will check subclass inheritance, ie, 'MetaRig' would
            return ALL nodes who's class is inherited from MetaRig. Allows you to
            group the data more efficiently by base classes and their inheritance
    :param mAttrs: uses the FilterNode.lsSearchAttributes call to match nodes via given attrs
    :param dataType: default='mClass' return the nodes already instantiated to
                    the correct class object. If not then return the Maya node
    :param nTypes: only return nodes of a given type, note this type must be registered to meta!
    '''
    mNodes=[]
    connections=[]
    
    if not nTypes:
        nTypes = getMClassNodeTypes()
    #if mTypes and not type(mTypes)==list:mTypes=[mTypes]
    for nType in nTypes:
    #for nType in getMClassNodeTypes():
        cons = cmds.listConnections(nodes, type=nType, s=source, d=destination, c=True)
        if cons:
            # NOTE we're only interested in connected nodes via message linked attrs
            for plug, node in zip(cons[::2], cons[1::2]):
                if cmds.getAttr(plug, type=True) == 'message':
                    if not node in connections:
                        connections.append(node)
                        log.debug(node)
    if not connections:
        return mNodes
    
    for node in connections:
        if not mInstances:
            if isMetaNode(node, mTypes=mTypes):
                mNodes.append(node)
        else:
            if isMetaNodeInherited(node,mInstances):
                mNodes.append(node)
    if mAttrs:
        #lazy to avoid cyclic imports
        import Red9_CoreUtils as r9Core
        mNodes=r9Core.FilterNode().lsSearchAttributes(mAttrs, nodes=mNodes)
    if dataType=='mClass':
        return [MetaClass(node,**kws) for node in set(mNodes)]
    else:
        return list(set(mNodes))
        
def getConnectedMetaSystemRoot(node, mTypes=[], ignoreTypes=[], mSystemRoot=True, **kws):
    '''
    From a given node see if it's part of a MetaData system, if so
    walk up the parent tree till you get to top meta node and return the class.
    
    :param ignoreTypes: if the given mClass node types are found to be systemRoots ignore them
        why, lets say we have a system with several mNodes that are technically the head of the 
        system and you need to skip a given type.
    :param mTypes: like the rest of Meta, if you give it a specific mType to find as root it will do 
        just that if that node is a root node in the system.
    :param mSystemRoot: whether to respect the mSystemRoot abort bool on the nodes, default=True
        
    .. note::
        this walks upstream only from the given node, so if you effectively have multiple root nodes
        in the system but wired to different parts of the network, and when walking upstream from the given
        you only get to one of ththose because of the network wiring, then that is correct.
    '''
    mNodes=getConnectedMetaNodes(node,**kws)
    if not mNodes:
        return
    else:
        mNode=mNodes[0]
    if not mTypes and type(mNode)==MetaRig:
        return mNode
    else:
        runaways=0
        parents=mNodes
        while parents and not runaways==100:
            for mNode in parents:
                log.debug('Walking network : %s' % mNode.mNode)
                
                if mSystemRoot and mNode.hasAttr('mSystemRoot') and mNode.mSystemRoot:
                    return mNode
                
                parent=getConnectedMetaNodes(mNode.mNode,source=True,destination=False)
                if not parent:
                    if ignoreTypes and isMetaNode(mNode, mTypes=ignoreTypes):
                        log.debug('node is top of tree but being ignored by the args : %s' % mNode)
                        continue
                    elif mTypes and isMetaNode(mNode, mTypes=mTypes):
                        log.debug('node is top of tree and of the correct mType match: %s' % mNode)
                        return mNode
                    if not mTypes:
                        log.debug('node is top of tree : %s' % mNode)
                        return mNode
                else:
                    if mTypes and isMetaNode(mNode, mTypes=mTypes):
                        log.debug('node is not top of the tree but matches the required mType filter: %s' % mNode)
                        return mNode
            runaways+=1
            parents=getConnectedMetaNodes(mNode.mNode,source=True,destination=False)


def  convertNodeToMetaData(nodes,mClass):
    '''
    pass in a node and convert it to a MetaNode, assuming that the nodeType
    is valid in the metaNodeTypesRegistry
    '''
    if not type(nodes)==list:
        nodes=[nodes]
    for node in nodes:
        mNode=MetaClass(node)
        mNode.addAttr('mClass', value=mTypesToRegistryKey(mClass)[0])
        mNode.addAttr('mNodeID', value=node.split('|')[-1].split(':')[-1])
        mNode.attrSetLocked('mClass', True)
        mNode.attrSetLocked('mNodeID', True)
    return [MetaClass(node) for node in nodes]

        
class MClassNodeUI(object):
    '''
    Simple UI to display all MetaNodes in the scene
    '''
    def __init__(self, mTypes=None, mInstances=None, mClassGrp=None, closeOnSelect=False, \
                 funcOnSelection=None, sortBy='byClass', allowMulti=True):
        '''
        :param mTypes: MetaNode class to search and display 'MetaRig'
        :param mInstances: MetaNode inheritance map, ie show all subclass of mType..
        :param closeOnSelect: on text select close the UI
        :param funcOnSelection: function to run where the selected mNode is expected
            as first arg, ie funcOnSelection=cmd.select so that when run the item is
            selected in the UI cmds.select(item) is run. Basically used as a dynamic callback
        :param sortBy: Sort the nodes found 'byClass' or 'byName'
        :param allowMulti: allow multiple selection in the UI
        '''
        self.mInstances=mInstances
        self.mTypes=mTypes
        self.mClassGrp=mClassGrp
        self.closeOnSelect=closeOnSelect
        self.func=funcOnSelection  # Given Function to run on the selected node when UI selected
        self.sortBy=sortBy
        self.allowMulti=allowMulti
        
        self.win = 'MetaClassFinder'
        self.mNodes=[]
        self.cachedforFilter=[]
        self.stripNamespaces=False
        self.shortname=False
        self.sortBy = 'class'
        
    @classmethod
    def show(cls):
        cls()._showUI()
        
    def _showUI(self):
        if cmds.window(self.win, exists=True):
            cmds.deleteUI(self.win, window=True)
        window = cmds.window(self.win, title=self.win)
        cmds.menuBarLayout()
        cmds.menu(l=LANGUAGE_MAP._Generic_.vimeo_menu)
        cmds.menuItem(l=LANGUAGE_MAP._MetaNodeUI_.vimeo_dev_part1,
                      ann=LANGUAGE_MAP._MetaNodeUI_.vimeo_dev_part1_ann,
                      c="import Red9.core.Red9_General as r9General;r9General.os_OpenFile('https://vimeo.com/100882408')")
        cmds.menuItem(l=LANGUAGE_MAP._MetaNodeUI_.vimeo_dev_part2,
                      ann=LANGUAGE_MAP._MetaNodeUI_.vimeo_dev_part2_ann,
                      c="import Red9.core.Red9_General as r9General;r9General.os_OpenFile('https://vimeo.com/100883383')")
        cmds.menuItem(l=LANGUAGE_MAP._MetaNodeUI_.vimeo_dev_part3,
                      ann=LANGUAGE_MAP._MetaNodeUI_.vimeo_dev_part3_ann,
                      c="import Red9.core.Red9_General as r9General;r9General.os_OpenFile('https://vimeo.com/102463373')")
        cmds.menuItem(divider=True)
        cmds.menuItem(l=LANGUAGE_MAP._MetaNodeUI_.vimeo_meta_part1,
                      ann=LANGUAGE_MAP._MetaNodeUI_.vimeo_meta_part1_ann,
                      c="import Red9.core.Red9_General as r9General;r9General.os_OpenFile('https://vimeo.com/61841345')")
        cmds.menuItem(l=LANGUAGE_MAP._MetaNodeUI_.vimeo_meta_part2,
                       ann=LANGUAGE_MAP._MetaNodeUI_.vimeo_meta_part2_ann,
                      c="import Red9.core.Red9_General as r9General;r9General.os_OpenFile('https://vimeo.com/62546103')")
        cmds.menuItem(l=LANGUAGE_MAP._MetaNodeUI_.vimeo_meta_part3,
                       ann=LANGUAGE_MAP._MetaNodeUI_.vimeo_meta_part3_ann,
                      c="import Red9.core.Red9_General as r9General;r9General.os_OpenFile('https://vimeo.com/64258996')")
        cmds.menuItem(l=LANGUAGE_MAP._MetaNodeUI_.vimeo_meta_part4,
                       ann=LANGUAGE_MAP._MetaNodeUI_.vimeo_meta_part4_ann,
                      c="import Red9.core.Red9_General as r9General;r9General.os_OpenFile('https://vimeo.com/72006183')")
        cmds.menuItem(divider=True)
        cmds.menuItem(divider=True)
        cmds.menuItem(l=LANGUAGE_MAP._Generic_.contactme,c=lambda *args:(r9Setup.red9ContactInfo()))
        cmds.menu(l=LANGUAGE_MAP._Generic_.debug)
        cmds.menuItem(l=LANGUAGE_MAP._MetaNodeUI_.print_registered_nodetypes,
                      ann=LANGUAGE_MAP._MetaNodeUI_.print_registered_nodetypes_ann,
                      c=self.printRegisteredNodeTypes)
        cmds.menuItem(l=LANGUAGE_MAP._MetaNodeUI_.print_registered_metaclasses,
                      ann=LANGUAGE_MAP._MetaNodeUI_.print_registered_metaclasses_ann,
                      c=self.printRegisteredMetaClasses)
        cmds.menuItem(l=LANGUAGE_MAP._MetaNodeUI_.print_metacached_node,
                      ann=LANGUAGE_MAP._MetaNodeUI_.print_metacached_nodes_ann,
                      c=self.printMetaNodeCache)
        
        cmds.menuItem(l=LANGUAGE_MAP._MetaNodeUI_.clear_cache,
                      ann=LANGUAGE_MAP._MetaNodeUI_.clear_cache_ann,
                      c=resetCache)
        cmds.menuItem(l=LANGUAGE_MAP._MetaNodeUI_.update_to_uuids,
                      ann=LANGUAGE_MAP._MetaNodeUI_.update_to_uuids_ann,
                      c=upgrade_toLatestBindings)
        cmds.scrollLayout('slMetaNodeScroll',rc=lambda *args:self.fitTextScrollFucker())
        cmds.columnLayout(adjustableColumn=True)
        cmds.separator(h=5, style='none')
        
        #Build the class options to filter by
        cmds.rowColumnLayout('rc_useMetaFilterUI', numberOfColumns=3,
                             columnWidth=[(1, 120), (2, 120), (3,200)],
                             columnSpacing=[(1, 10), (2, 10), (3,20)])
        cmds.checkBox('cb_filter_mTypes', label=LANGUAGE_MAP._MetaNodeUI_.mtypes_filter, v=False, cc=partial(self.__uicb_setfilterMode,'mTypes'))
        cmds.checkBox('cb_filter_mInstances', label=LANGUAGE_MAP._MetaNodeUI_.minstances_filter, v=False, cc=partial(self.__uicb_setfilterMode,'mInstance'))
        cmds.optionMenu('om_MetaUI_Filter', ni=len(RED9_META_REGISTERY),
                        ann=LANGUAGE_MAP._MetaNodeUI_.registered_metaclasses_ann,
                        cc=partial(self.fillScroll))
        for preset in sorted(RED9_META_REGISTERY):
            cmds.menuItem(l=preset)
        cmds.setParent('..')
        
        cmds.separator(h=10, style='in')
        cmds.rowColumnLayout(numberOfColumns=4,
                             columnWidth=[(1,70),(2,80),(3, 280), (4, 30)],
                             columnSpacing=[(1, 10), (2, 10)])
        cmds.checkBox('cb_shortname', label=LANGUAGE_MAP._MetaNodeUI_.shortname, v=False, cc=self.__filterResults)
        cmds.checkBox('cb_stripNS', label=LANGUAGE_MAP._MetaNodeUI_.stripnamespace, v=False, cc=self.__filterResults)
        try:
            cmds.textFieldGrp('filterByName', l=LANGUAGE_MAP._MetaNodeUI_.filter_by_name, text='', tcc=self.__filterResults, cw=((1,100),(2,170)))
        except:
            cmds.textFieldGrp('filterByName', l=LANGUAGE_MAP._MetaNodeUI_.filter_by_name, text='', cc=self.__filterResults, cw=((1,100),(2,170)))
        cmds.button(LANGUAGE_MAP._Generic_.clear, c=self.__clearFilter)
        cmds.setParent('..')
        
        cmds.separator(h=10, style='in')
        cmds.rowColumnLayout(numberOfColumns=4, columnWidth=[(1, 100), (2, 100), (3,100), (4,100)],
                             columnSpacing=[(1, 10), (2, 10), (3,10)])
        self.uircbMetaUIShowStatus = cmds.radioCollection('uircbMetaUIShowStatus')
        cmds.radioButton('metaUISatusAll', label=LANGUAGE_MAP._MetaNodeUI_.all, cc=partial(self.fillScroll))
        cmds.radioButton('metaUISatusValids', label=LANGUAGE_MAP._MetaNodeUI_.valids, cc=partial(self.fillScroll))
        cmds.radioButton('metaUISatusinValids', label=LANGUAGE_MAP._MetaNodeUI_.invalids, cc=partial(self.fillScroll))
        cmds.radioButton('metaUISatusUnregistered', label=LANGUAGE_MAP._MetaNodeUI_.unregistered, cc=partial(self.fillScroll))
        cmds.setParent('..')
        
        #You've passed in the filter types directly to the UI Class
        if self.mTypes or self.mInstances:
            #cmds.separator(h=15, style='none')
            cmds.rowColumnLayout('rc_useMetaFilterUI', e=True, en=False, vis=False)
            if self.mTypes:
                cmds.text(label='%s : %s' % (LANGUAGE_MAP._MetaNodeUI_.ui_launch_mtypes,self.mTypes))
            else:
                cmds.text(label='%s : %s' % (LANGUAGE_MAP._MetaNodeUI_.ui_launch_minstances,self.mInstances))
            cmds.separator(h=15, style='none')
            
        if not self.allowMulti:
            cmds.textScrollList('slMetaNodeList',font="fixedWidthFont")
        else:
            cmds.textScrollList('slMetaNodeList',font="fixedWidthFont", allowMultiSelection=True)
        cmds.popupMenu('r9MetaNodeUI_Popup')
        cmds.menuItem(label=LANGUAGE_MAP._MetaNodeUI_.graph_selected, command=partial(self.graphNetwork))
        cmds.menuItem(divider=True)
        cmds.menuItem(label=LANGUAGE_MAP._MetaNodeUI_.select_children,
                      ann=LANGUAGE_MAP._MetaNodeUI_.select_children_ann,
                      command=partial(self.doubleClick))
        cmds.menuItem(label=LANGUAGE_MAP._MetaNodeUI_.delete_selected,
                      ann=LANGUAGE_MAP._MetaNodeUI_.delete_selected_ann,
                      command=partial(self.deleteCall))
        cmds.menuItem(divider=True)
        cmds.menuItem(label=LANGUAGE_MAP._MetaNodeUI_.sort_by_classname, command=partial(self.fillScroll,'byClass'))
        cmds.menuItem(label=LANGUAGE_MAP._MetaNodeUI_.sort_by_nodename, command=partial(self.fillScroll,'byName'))
        cmds.menuItem(divider=True)
        cmds.menuItem(label=LANGUAGE_MAP._MetaNodeUI_.class_all_registered, command=partial(self.fillScroll,'byName'))
        cmds.menuItem(divider=True)
        cmds.menuItem(label=LANGUAGE_MAP._MetaNodeUI_.pro_connect_node, command=self.__uiCB_connectNode)
        cmds.menuItem(label=LANGUAGE_MAP._MetaNodeUI_.pro_disconnect_node, command=self.__uiCB_disconnectNode)
        cmds.menuItem(label=LANGUAGE_MAP._MetaNodeUI_.pro_test_pro_stubs, command=lambda x:r9Setup.PRO_PACK_STUBS().test_pro_stubs())
        cmds.button(label=LANGUAGE_MAP._Generic_.refresh, command=partial(self.fillScroll))
        cmds.separator(h=15,style='none')
        cmds.iconTextButton(style='iconOnly', bgc=(0.7,0,0), image1='Rocket9_buttonStrap2.bmp',
                                 c=lambda *args:(r9Setup.red9ContactInfo()),h=22,w=200)
        cmds.showWindow(window)
        cmds.radioCollection(self.uircbMetaUIShowStatus, edit=True, select='metaUISatusAll')
        self.fillScroll()
 
    def __uicb_setfilterMode(self, mode, *args):
        if mode=='mTypes':
            cmds.checkBox('cb_filter_mInstances', e=True, v=False)
        elif  mode=='mInstance':
            cmds.checkBox('cb_filter_mTypes', e=True, v=False)
        self.fillScroll(*args)
            
    def fitTextScrollFucker(self):
        '''
        bodge to resize tghe textScroll as the default Maya control is SHITE!
        '''
        cmds.textScrollList('slMetaNodeList',e=True,h=int(cmds.scrollLayout('slMetaNodeScroll',q=True,h=True))-170)
        cmds.textScrollList('slMetaNodeList',e=True,w=int(cmds.scrollLayout('slMetaNodeScroll',q=True,w=True))-20)

    def graphNetwork(self,*args):
        if r9Setup.mayaVersion()<2013:
            mel.eval('hyperGraphWindow( "", "DG")')
        else:
            mel.eval('NodeEditorWindow;NodeEditorGraphUpDownstream;')
        
    def selectCmd(self,*args):
        '''
        callback run on select in the UI, allows you to run the func passed
        in by the funcOnSelection arg
        '''
        indexes=cmds.textScrollList('slMetaNodeList',q=True,sii=True)
        if indexes:
            cmds.select(cl=True)
        for i in indexes:
            node=MetaClass(self.mNodes[i - 1])
            log.debug('selected : %s' % node)
            
            #func is a function passed into the UI via the funcOnSelection arg
            #this allows external classes to use this as a signal call on select
            if self.func:
                self.func(node.mNode)
            else:
                cmds.select(node.mNode,add=True)
                
        if self.closeOnSelect:
            cmds.deleteUI('MetaClassFinder',window=True)
    
    def deleteCall(self,*args):
        result = cmds.confirmDialog(
                title=str(LANGUAGE_MAP._MetaNodeUI_.confirm_delete),
                button=[str(LANGUAGE_MAP._Generic_.yes),
                        str(LANGUAGE_MAP._Generic_.cancel)],
                message=str(LANGUAGE_MAP._MetaNodeUI_.confirm_delete_message),
                defaultButton=str(LANGUAGE_MAP._Generic_.cancel),
                bgc=(0.5,0.1,0.1),
                cancelButton=str(LANGUAGE_MAP._Generic_.cancel),
                dismissString=str(LANGUAGE_MAP._Generic_.cancel))
        if result == str(LANGUAGE_MAP._Generic_.yes):
            try:
                indexes=cmds.textScrollList('slMetaNodeList',q=True,sii=True)
                if indexes:
                    for i in indexes:
                        MetaClass(self.mNodes[i - 1]).delete()
                self.fillScroll()
            except:
                log.warning('delete failed')
            
    def doubleClick(self,*args):
        '''
        run the generic meta.getChildren call and select the results
        '''
        cmds.select(cl=True)
        nodes=[]
        for i in cmds.textScrollList('slMetaNodeList',q=True,sii=True):
            nodes.extend(MetaClass(self.mNodes[i-1]).getChildren(walk=True))
        if nodes:
            cmds.select(nodes)
        else:
            log.warning('no child nodes found from given metaNode')
        #cmds.select(self.mNodes[cmds.textScrollList('slMetaNodeList',q=True,sii=True)[0]-1].getChildren(walk=True))
    
    def __fillScrollEntries(self):
        '''
        consistant way to fill the text data displayed
        '''
        baseNames=[]
        cmds.textScrollList('slMetaNodeList', edit=True, ra=True)
        width=len(self.mNodes[0])
        #figure out the width of the first cell
        for meta in self.mNodes:
            name=meta
            if self.stripNamespaces:
                name=meta.replace(':','')
            if self.shortname:
                name=name.split('|')[-1].split(':')[-1]
            if len(name)>width:
                width=len(name)
            baseNames.append(name)
        width+=3
        entries=zip(self.mNodes, baseNames)
        #fill the scroll list
        for meta,name in entries:
            cmds.textScrollList('slMetaNodeList', edit=True,
                                    append=('{0:<%i}:{1:}' % width).format(name, getMClassDataFromNode(meta)),
                                    sc=lambda *args:self.selectCmd(),
                                    dcc=lambda *x:self.doubleClick())
        
    def __filterResults(self, *args):
        '''
        rebuild the list based on the filter typed in, Note that results are 
        converted to upper before the match so it's case IN-sensitive
        '''
        self.shortname=False
        self.stripNamespaces=False
        filterby=cmds.textFieldGrp('filterByName', q=True, text=True)
        if filterby:
            self.mNodes=[]
            if self.cachedforFilter:
                #fill the scroll list
                self.mNodes = r9Core.filterListByString(self.cachedforFilter, filterby, matchcase=False)

        if cmds.checkBox('cb_shortname', q=True, v=True):
            self.shortname=True
        if cmds.checkBox('cb_stripNS', q=True, v=True):
            self.stripNamespaces=True
        self.__fillScrollEntries()
    
    def __clearFilter(self, *args):
        cmds.textFieldGrp('filterByName', e=True, text='')
        self.fillScroll()
        
    def fillScroll(self, sortBy=None, *args):  # , mClassToShow=None, *args):
        states=cmds.radioCollection(self.uircbMetaUIShowStatus, q=True, select=True)
        cmds.textScrollList('slMetaNodeList', edit=True, ra=True)
        self.dataType='node'
        if states=='metaUISatusinValids' or states=='metaUISatusValids':
            self.dataType='mClass'
        
        #build the metaNode list up from the filters =====================
        
        if states =='metaUISatusUnregistered':
            self.mNodes=getUnregisteredMetaNodes()
        
        elif cmds.rowColumnLayout('rc_useMetaFilterUI', q=True, en=True):
            mTypesFilter = cmds.checkBox('cb_filter_mTypes', q=True, v=True)
            mInstanceFilter = cmds.checkBox('cb_filter_mInstances', q=True, v=True)
            mCalssSelected = cmds.optionMenu('om_MetaUI_Filter', q=True, v=True)

            if mTypesFilter:
                self.mNodes=getMetaNodes(mTypes=mCalssSelected, mInstances=None, dataType=self.dataType)
                print 'mTypeFilter : ', mCalssSelected
            elif mInstanceFilter:
                self.mNodes=getMetaNodes(mTypes=None, mInstances=mCalssSelected, dataType=self.dataType)
                print 'mInstanceFilter : ', mCalssSelected
            else:
                self.mNodes=getMetaNodes(mTypes=self.mTypes, mInstances=self.mInstances, dataType=self.dataType)
        else:
            self.mNodes=getMetaNodes(mTypes=self.mTypes, mInstances=self.mInstances, dataType=self.dataType)
            print 'none', self.mTypes, self.mInstances
                        
        if not self.mNodes:
            log.warning('no metaNodes found that match the filters')
            return
        
        if states=='metaUISatusinValids':
            self.mNodes=[node.mNode for node in self.mNodes if not node.isValid()]
        if states=='metaUISatusValids':
            self.mNodes=[node.mNode for node in self.mNodes if node.isValid()]
            
        #Sort the list ==================================================
        if not sortBy:
            sortBy=self.sortBy
          
        if sortBy=='byClass':
            self.mNodes=sorted(self.mNodes, key=lambda x: getMClassDataFromNode(x).upper())
        elif sortBy=='byName':
            self.mNodes=sorted(self.mNodes, key=lambda x: x.upper())

        #fill the textScroller =========================================
        if self.mNodes:
            self.cachedforFilter=list(self.mNodes)  # cache the results so that the filter by name is fast!
            self.__fillScrollEntries()
 
    def __uiCB_connectNode(self, *args):
        '''
        PRO PACK : Given a single selected mNode from the UI and a single selected MAYA node, run
        connectChild with the given promtString as the attr
        '''
        indexes=cmds.textScrollList('slMetaNodeList',q=True,sii=True)
        if len(indexes)==1:
            mNode=MetaClass(self.mNodes[indexes[0]-1])
        else:
            raise StandardError('Connect Call only works with a single selected mNode from the UI')
        
        r9Setup.PRO_PACK_STUBS().MetaDataUI.uiCB_connectNode(mNode)
   
    def __uiCB_disconnectNode(self,*args):
        '''
        PRO PACK : Given a single selected mNode from the UI and selected MAYA nodes, run
        disconnectChild to remove them from the metaData system
        '''
        indexes=cmds.textScrollList('slMetaNodeList',q=True,sii=True)
        if len(indexes)==1:
            mNode=MetaClass(self.mNodes[indexes[0]-1])
        else:
            raise StandardError('Connect Call only works with a single selected mNode from the UI')
        
        r9Setup.PRO_PACK_STUBS().MetaDataUI.uiCB_disconnectNode(mNode)
        
    def printRegisteredNodeTypes(self,*args):
        print '\nRED9_META_NODETYPE_REGISTERY:\n============================='
        print getMClassNodeTypes()
        
    def printRegisteredMetaClasses(self,*args):
        data = getMClassMetaRegistry()
        print '\nRED9_META_REGISTERY:\n===================='
        for key, value in sorted(data.items()):
            print key, ' : ', value
            
    def printMetaNodeCache(self,*args):
        data = getMClassNodeCache()
        print '\nRED9_META_NODECACHE:\n===================='
        for key, value in sorted(data.items()):
            print key, ' : ', value

# Decorators ==========================================================

def nodeLockManager(func):
    '''
    Simple decorator to manage metaNodes which are locked. Why lock??
    Currently just the metaRig and therefore any subclasses of that are locked.
    The reason is that the Maya 'network' node I use has issues when certain
    connections are deleted, the node itself can get deleted and cleanup, removing
    the entire network! Try it, make a metaNode and key an attr on it, then run
    cutKeys...the node will be deleted.
    
    This decorator is used to manage the unlocking of self for all calls that
    require change access rights to the 'network' node itself.
    '''
    @wraps(func)
    def wrapper(*args, **kws):
        res=None
        err=None
        locked=False
        try:
            locked=False
            mNode=args[0]  # args[0] is self
            #log.debug('nodeLockManager > func : %s : metaNode / self: %s' % (func.__name__,mNode.mNode))
            if mNode.mNode and mNode._lockState:
                locked=True
                #log.debug('nodeLockManager > func : %s : node being unlocked' % func.__name__)
                cmds.lockNode(mNode.mNode,lock=False)
            res=func(*args, **kws)
        except StandardError, error:
            err=error
        finally:
            if locked:
                #log.debug('nodeLockManager > func : %s : node being relocked' % func.__name__)
                cmds.lockNode(mNode.mNode, lock=True)
            if err:
                traceback = sys.exc_info()[2]  # get the full traceback
                raise StandardError(StandardError(err), traceback)
            return res
    return wrapper

def pymelHandler(func):
    def wrapper(*args, **kws):
        res=None
        err=None
        try:
            #inputNodes=args[0]
            #if 'pymel' in str(type(inputNodes)):
            #    print 'pymel Node passed in!!!!!!!!!!'
            #    print 'type : ', args
            #    #args[0]=str(inputNodes)
            res=func(*args, **kws)
        except StandardError, error:
            err=error
        finally:
            if err:
                traceback = sys.exc_info()[2]  # get the full traceback
                raise StandardError(StandardError(err), traceback)
            return res
    return wrapper


# Main Meta Class ==========================================================

class MetaClass(object):
    
    cached = None
        
    def __new__(cls, *args, **kws):
        '''
        Idea here is if a MayaNode is passed in and has the mClass attr
        we pass that into the super(__new__) such that an object of that class
        is then instantiated and returned.
        '''
        mClass=None
        mNode=None
        MetaClass.cached = None
        
        if args:
            mNode=args[0]

            if mNode:
                MetaClass.cached = getMetaFromCache(mNode)  # Do Not run __new__ if the node is in the Cache
                log.debug('### MetaClass.cached being set in the __new__ ###')
                if MetaClass.cached:
                    return MetaClass.cached
            try:
                if isMetaNode(mNode):
                    mClass=getMClassDataFromNode(mNode)
            except:
                if issubclass(type(mNode), MetaClass):
                    log.debug('NodePassed is already an instanciated MetaNode!!')
                    #print type(mNode), mNode.cached
                    MetaClass.cached=True
                    return mNode
        if mClass:
            log.debug("mClass derived from MayaNode Attr : %s" % mClass)
            if mClass in RED9_META_REGISTERY:
                _registeredMClass=RED9_META_REGISTERY[mClass]
                try:
                    log.debug('### Instantiating existing mClass : %s >> %s ###' % (mClass,_registeredMClass))
                    return super(cls.__class__, cls).__new__(_registeredMClass,*args,**kws)
                except:
                    log.debug('Failed to initialize mClass : %s' % _registeredMClass)
                    pass
            else:
                raise StandardError('Node has an unRegistered mClass attr set')
        else:
            log.debug("mClass not found, given or registered")
            return super(cls.__class__, cls).__new__(cls)
    
    #@pymelHandler
    def __init__(self, node=None, name=None, nodeType='network', autofill='all', *args, **kws):
        '''
        Base Class for Meta support. This manages all the attribute and class 
        management for all subsequent inherited classes. This is the core of
        the MetaData factory API
        
        :param node: Maya Node - if given we test it for the mClass attribute, if it exists 
                we initialize a class of that type and return. If not passed in then we 
                make a new network node for the type given.
        :param name: only used on create, name to set for the new Maya Node (self.mNode)
        :param nodeType: allows you to specify a node of type to create as a new mClass node. 
                default is 'network', not that for any node to show up in the get 
                calls that type MUST be registered in the RED9_META_NODETYPE_REGISTERY
        :param autofill: 'str' cast all the MayaNode attrs into the class dict by default. 
                Updated: modes: 'all' or 'messageOnly'. all casts every attr, messageOnly 
                fills the node with just message linked attrs (designed for MetaClass work 
                with HIK characterNode)
                
        .. note::  
            mNode is now a wrap on the MObject so will always be in sync even if the node is renamed/parented
        '''
        if node and MetaClass.cached:
            log.debug('CACHE : Aborting __init__ on pre-cached MetaClass Object')
            return
        
        log.debug('Meta__init__ main args :: node=%s, name=%s, nodeType=%s' % (node, name, nodeType))
        #data that will not get pushed to the Maya node
        object.__setattr__(self, '_MObject', '')
        object.__setattr__(self, '_MObjectHandle', '')
        object.__setattr__(self, 'UNMANAGED', ['mNode',
                                               '_MObject',
                                               '_MObjectHandle',
                                               '_lockState',
                                               'lockState',
                                               '_forceAsMeta'])  # note - UNMANAGED bypasses the Maya node in setattr calls
        
        object.__setattr__(self, '_lockState', False)    # lock the Maya node so network cleanups don't accidentally delete it
        object.__setattr__(self, '_forceAsMeta', False)  # force all getAttr calls to return mClass objects even for starndard Maya nodes
        
        if not node:
            if not name:
                name=self.__class__.__name__
            #no MayaNode passed in so make a fresh network node (default)
            if not nodeType=='network' and not nodeType in RED9_META_NODETYPE_REGISTERY:
                raise IOError('nodeType : "%s" : is NOT yet registered in the "RED9_META_NODETYPE_REGISTERY", please use r9Meta.registerMClassNodeCache(nodeTypes=[%s]) to do so before making this node' % (nodeType,nodeType))
                #raise IOError()
                #return
            node=cmds.createNode(nodeType,name=name)
            self.mNode=node
            self.addAttr('mClass', value=str(self.__class__.__name__))  # ! MAIN ATTR !: used to know what class to instantiate.
            self.addAttr('mNodeID', value=name)                         # ! MAIN NODE ID !: used by pose systems to ID the node.
            self.addAttr('mClassGrp', value='MetaClass', hidden=True)   # ! CLASS GRP  : this is used mainly by MetaRig and other complex
                                                                        #                systems to denote a classes intended system base
            self.addAttr('mSystemRoot', value=False, hidden=True)       # ! SYSTEM ROOT : indicates that this node is the root of a system and
                                                                        #                therefore halts the 'getConnectedMetaSystemRoot' call
            if r9Setup.mayaVersion()<=2015:
                #print '__init__ setting uuid'
                self.addAttr('UUID', value='')          # ! Cache UUID attr which the Cache itself is in control of
            log.debug('New Meta Node Created')
            registerMClassNodeCache(self)
            cmds.setAttr('%s.%s' % (self.mNode,'mClass'), e=True,l=True)    # lock it
            cmds.setAttr('%s.%s' % (self.mNode,'mNodeID'),e=True,l=True)    # lock it
            #cmds.setAttr('%s.%s' % (self.mNode,'mClassGrp'),e=True,l=True)  # lock it
        else:
            self.mNode=node
            if not self.hasAttr('mNodeID'):
                #for casting None MetaData, standard Maya nodes into the api
                self.mNodeID=node.split('|')[-1].split(':')[-1]
            if isMetaNode(node):
                log.debug('Meta Node Passed in : %s' % node)
                registerMClassNodeCache(self)
            else:
                log.debug('Standard Maya Node being metaManaged')
                
        self.lockState=False
        
        #bind any default attrs up - note this should be overloaded where required
        self.__bindData__(*args, **kws)
        
        #This is useful! so we have a node with a lot of attrs, or just a simple node
        #this block if activated will auto-fill the object.__dict__ with all the available
        #Maya node attrs, so you get autocomplete on ALL attrs in the script editor!
        if autofill=='all' or autofill=='messageOnly':
            self.__fillAttrCache__(autofill)
        
        #register the class to the Cache
        #registerMClassNodeCache(self)
     
     
    def __bindData__(self, *args, **kws):
        '''
        This is intended as an entry point to allow you to bind whatever attrs or extras 
        you need at a class level. It's called by the __init__ ... 
        Intended to be overloaded as and when needed when inheriting from MetaClass
        
        ..note::
            To bind a new attr and serilaize it to the self.mNode (Maya node) 
            self.addAttr('newDefaultAttr',attrType='string')
            
            To bind a new attribute to the python object only, not serialized to Maya node 
            self.newClassAttr=None  :or:   self.__setattr__('newAttr',None)
        '''
        pass
    
    def isValid(self):
        '''
        a metaNode in this case is valid if it has connections, if not it's classed invalid
        '''
        if not self.isValidMObject():
            return False
        if self.hasAttr('mClass') and not cmds.listConnections(self.mNode):
            return False
        return True
        
    def isValidMObject(self):
        '''
        validate the MObject, without this Maya will crash if the pointer is no longer valid
        TODO: thinking of storing the dagPath when we fill in the mNode to start with and
        if this test fails, ie the scene has been reloaded, then use the dagPath to refind
        and refil the mNode property back in.... maybe??
        '''
        try:
            mobjHandle=object.__getattribute__(self, "_MObjectHandle")
            return mobjHandle.isValid()
        except:
            log.info('_MObjectHandle not yet setup')
     
    def isSystemRoot(self):
        '''
        used by the getConnectedMetaSystemRoot call to identify if this
        node is a top system node. Having his as an attr allows us to designate
        certain subsystems as root nodes in their own right. Ie, Facial controlBoard
        '''
        if self.hasAttr('mSystemRoot'):
            return self.mSystemRoot
        elif self.getParentMetaNode():
            return False
        
    #Cast the mNode attr to the actual MObject so it's no longer limited by string dagpaths
    #yes I know Pymel does this for us but I don't want the overhead!
    def __get_mNode(self):
        '''
        mNode is the pointer to the Maya object itself, retrieved via the MObject
        under the hood so it's always in sync.
        '''
        mobjHandle=object.__getattribute__(self, "_MObjectHandle")
        if mobjHandle:
            try:
                if not mobjHandle.isValid():
                    log.info('MObject is no longer valid - %s - object may have been deleted or the scene reloaded?'\
                              % object.__getattribute__(self,'mNodeID'))
                    return
                #if we have an object thats a dagNode, ensure we return FULL Path
                mobj=object.__getattribute__(self, "_MObject")
                if OpenMaya.MObject.hasFn(mobj, OpenMaya.MFn.kDagNode):
                    dPath = OpenMaya.MDagPath()
                    OpenMaya.MDagPath.getAPathTo(mobj,dPath)
                    return dPath.fullPathName()
                else:
                    depNodeFunc = OpenMaya.MFnDependencyNode(mobj)
                    return depNodeFunc.name()
            except StandardError,error:
                raise StandardError(error)
    def __set_mNode(self, node):
        if node:
            try:
                mobj=OpenMaya.MObject()
                selList=OpenMaya.MSelectionList()
                selList.add(node)
                selList.getDependNode(0,mobj)
                object.__setattr__(self, '_MObject', mobj)
                object.__setattr__(self, '_MObjectHandle',OpenMaya.MObjectHandle(mobj))
            except StandardError, error:
                raise StandardError(error)
         
    mNode = property(__get_mNode, __set_mNode)
    
    @property
    def mNodeMObject(self):
        '''
        exposed wrapper to return the MObject directly, this passes via the MObjectHandle
        to ensure that the MObject cached is still valid
        '''
        mobjHandle=object.__getattribute__(self, "_MObjectHandle")
        if mobjHandle:
            try:
                if not mobjHandle.isValid():
                    log.info('MObject is no longer valid - %s - object may have been deleted or the scene reloaded?'\
                              % object.__getattribute__(self,'mNodeID'))
                    return
                #if we have an object thats a dagNode, ensure we return FULL Path
                return object.__getattribute__(self, "_MObject")
            except StandardError,error:
                raise StandardError(error)
        
    #property managing the lockNode state of the mNode
    def __get_lockState(self):
        '''
        Lockstate is just that, the lockNode state of the Maya node
        '''
        return self._lockState
    def __set_lockState(self, state):
        try:
            cmds.lockNode(self.mNode, lock=state)
            self._lockState=state
        except:
            log.debug("can't set the nodeState for : %s" % self.mNode)
    lockState = property(__get_lockState, __set_lockState)


    def __repr__(self):
        if self.hasAttr('mClass'):
            return "%s(mClass: '%s', node: '%s')" % (self.__class__, self.mClass, self.mNode.split('|')[-1])
        else:
            return "%s(Wrapped Standard MayaNode, node: '%s')" % (self.__class__, self.mNode.split('|')[-1])
    
    def __eq__(self, obj):
        '''
        Equals calls are handled via the MObject cache
        '''
        if isinstance(obj, self.__class__):
            if obj._MObject and self._MObject:
                if obj._MObject == self._MObject:
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False
    
    @r9General.Timer
    def __fillAttrCache__(self, level):
        '''
        go through all the attributes on the given node and cast each one of them into
        the main object.__dict__ this means they all show in the scriptEditor and autocomplete!
        This is ONLY for ease of use when dot complete in Maya, nothing more
        '''
        if level=='messageOnly':
            attrs=self.listAttrsOfType(Type='message')
            #attrs=[attr for attr in cmds.listAttr(self.mNode) if cmds.getAttr('%s.%s' % (self.mNode,attr),type=True)=='message']
        else:
            #attrs=self.listAttrs()
            attrs=cmds.listAttr(self.mNode)

        for attr in attrs:
            try:
                #we only want to fill the __dict__ we don't want the overhead
                #of reading the attr data as thats done on demand.
                object.__setattr__(self, attr, None)
            except:
                pass
    
    def setUUID(self):
        '''
        unique UUID used by the caching system
        '''
        newUUID = generateUUID()
        self.UUID = newUUID
        log.debug('setting new UUID : %s on %s' % (newUUID, self.mNode))
        return newUUID
    
    def getUUID(self):
        return self.UUID
    
    # Attribuite Management block
    #-----------------------------------------------------------------------------------
           
    def __setEnumAttr__(self, attr, value):
        '''
        Enums : I'm allowing you to set value by either the index or the display text
        '''
        if attributeDataType(value)=='string':
            log.debug('set enum attribute by string :  %s' % value)
            enums=cmds.attributeQuery(attr, node=self.mNode, listEnum=True)[0].split(':')
            try:
                value=enums.index(value)
            except:
                raise ValueError('Invalid enum string passed in: string is not in enum keys')
        log.debug('set enum attribute by index :  %s' % value)
        cmds.setAttr('%s.%s' % (self.mNode, attr), value)
    
    def __setMessageAttr__(self, attr, value, force=True):
        '''
        Message : by default in the __setattr_ I'm assuming that the nodes you pass in are to be
        the ONLY connections to that msgLink and all other current connections will be deleted
        hence cleanCurrent=True
        '''
        if cmds.attributeQuery(attr, node=self.mNode, multi=True)==False:
            if attributeDataType(value)=='complex':
                raise ValueError("You can't connect multiple nodes to a singluar message plug via __setattr__")
            log.debug('set singular message attribute connection:  %s' % value)
            self.connectChild(value, attr, cleanCurrent=True, force=force)
        else:
            log.debug('set multi-message attribute connection:  %s' % value)
            self.connectChildren(value, attr, cleanCurrent=True, force=force)
    
    @nodeLockManager
    def __setattr__(self, attr, value, force=True, **kws):
        '''
        Overload the base setattr to manage the MayaNode itself
        '''
        object.__setattr__(self, attr, value)
        
        if attr not in self.UNMANAGED and not attr=='UNMANAGED':
            if cmds.attributeQuery(attr, exists=True, node=self.mNode):
                locked=False
                if self.attrIsLocked(attr) and force:
                    self.attrSetLocked(attr,False)
                    locked=True

                #Enums Handling
                if cmds.attributeQuery(attr, node=self.mNode, enum=True):
                    self.__setEnumAttr__(attr, value)
                          
                #Message Link handling
                elif cmds.attributeQuery(attr, node=self.mNode, message=True):
                    self.__setMessageAttr__(attr, value, force)
                          
                #Standard Attribute
                else:
                    attrString='%s.%s' % (self.mNode, attr)       # mayaNode.attribute for cmds.get/set calls
                    attrType=cmds.getAttr(attrString, type=True)  # the MayaNode attribute valueType
                    valueType=attributeDataType(value)            # DataType passed in to be set as Value
                    log.debug('valueType : %s' % valueType)
                    log.debug('setting %s attribute to value : %s' % (attrType,value))
                    
                    if attrType=='string':
                        if valueType=='string' or valueType=='unicode':
                            log.debug('set string attribute:  %s' % value)
                            cmds.setAttr(attrString, value, type='string')
                            return
                        elif valueType=='complex':
                            log.debug('set string attribute to complex :  %s' % self.__serializeComplex(value))
                            cmds.setAttr(attrString, self.__serializeComplex(value), type='string')
                            return
                        
                    elif attrType in ['double3','float3'] and valueType=='complex':
                        try:
                            cmds.setAttr(attrString, value[0], value[1], value[2])
                        except ValueError, error:
                            raise ValueError(error)
                    elif attrType == 'doubleArray':
                        cmds.setAttr(attrString, value, type='doubleArray')
                    elif attrType == 'matrix':
                        cmds.setAttr(attrString, value, type='matrix')
                        
                    #elif attrType=='TdataCompound': #ie blendShape weights = multi data or joint.minRotLimitEnable
                    #    pass
                    else:
                        try:
                            cmds.setAttr(attrString, value)
                        except StandardError,error:
                            log.debug('failed to setAttr %s - might be connected' % attrString)
                            raise StandardError(error)
                if locked:
                    self.attrSetLocked(attr,True)
            else:
                log.debug('attr : %s doesnt exist on MayaNode > class attr only' % attr)
    
    def __getMessageAttr__(self, attr):
        '''
        separated func as it's the kind of thing that other classes may want to overload
        the behaviour of the returns etc
        '''
        msgLinks=cmds.listConnections('%s.%s' % (self.mNode,attr),destination=True,source=True)
        if msgLinks:
            msgLinks=cmds.ls(msgLinks,l=True)
            if not cmds.attributeQuery(attr, node=self.mNode, m=True):  # singular message
                if isMetaNode(msgLinks[0]):
                    return MetaClass(msgLinks[0])
            for i,link in enumerate(msgLinks):
                if isMetaNode(link) or self._forceAsMeta:
                    msgLinks[i]=MetaClass(link)
                    log.debug('%s :  Connected data is an mClass Object, returning the Class' % link)
#             if not cmds.attributeQuery(attr, node=self.mNode, m=True):  # singular message
#                 #log.debug('getattr for multi-message attr: connections =[%s]' % ','.join(msgLinks))
#                 if isMetaNode(msgLinks[0]):
#                     return msgLinks[0]  # MetaClass(msgLinks[0])
            return msgLinks
        else:
            log.debug('nothing connected to msgLink %s.%s' % (self.mNode,attr))
            return []
                        
    def __getattribute__(self, attr):
        '''
        Overload the method to always return the MayaNode
        attribute if it's been serialized to the MayaNode
        '''
        #if callable(object.__getattribute__(self, attr)):
        #    log.debug("callable attr, bypassing tests : %s" % attr)
        #    return object.__getattribute__(self, attr)

        if callable(attr):
            log.debug("callable attr, bypassing tests : %s" % attr)
            return attr
        try:
            #stops recursion, do not getAttr on mNode here
            mNode=object.__getattribute__(self, "mNode")
            
            if not mNode or not cmds.objExists(mNode):
                attrVal=object.__getattribute__(self, attr)
                return attrVal
            else:
                #MayaNode processing - retrieve attrVals on the MayaNode
                if cmds.attributeQuery(attr, exists=True, node=mNode):
                    attrType=cmds.getAttr('%s.%s' % (mNode,attr),type=True)
                    
                    #Message Link handling
                    #=====================
                    if attrType=='message':
                        return self.__getMessageAttr__(attr)

                    #Standard Maya Attr handling
                    #===========================
                    attrVal=cmds.getAttr('%s.%s' % (mNode,attr))
                    if attrType=='string':
                        #for string data we pass it via the JSON decoder such that
                        #complex data can be managed and returned correctly
                        try:
                            attrVal=self.__deserializeComplex(attrVal)
                            if type(attrVal)==dict:
                                return attrVal
                                #log.debug('Making LinkedDict')
                                #return self.LinkedDict([self,attr],attrVal)
                        except:
                            log.debug('string is not JSON deserializable')
                    elif attrType=='double3' or attrType=='float3':
                        return attrVal[0]  # return (x,x,x) not [(x,x,x)] as standard Maya does
                else:
                    attrVal=object.__getattribute__(self, attr)
                return attrVal
        except StandardError,error:
            raise StandardError(error)
              
    def __serializeComplex(self, data):
        '''
        Serialize complex data such as dicts to a JSON string
        
        Test the len of the string, anything over 32000 (16bit) gets screwed by the
        Maya attribute template and truncated IF you happened to select the string in the
        Attribute Editor. For long strings we need to force lock the attr here!
        bit thanks to MarkJ for that as it was doing my head in!!
        http://markj3d.blogspot.co.uk/2012/11/maya-string-attr-32k-limit.html
        '''
        if len(data)>32700:
            log.debug('Warning >> Length of string is over 16bit Maya Attr Template limit - lock this after setting it!')
        return json.dumps(data)
    
    def __deserializeComplex(self, data):
        '''
        Deserialize data from a JSON string back to it's original complex data
        '''
        #log.debug('deserializing data via JSON')
        if type(data) == unicode:
            return json.loads(str(data))
        return json.loads(data)
    
    @nodeLockManager
    def __delattr__(self, attr):
        try:
            log.debug('attribute delete  : %s , %s' % (self,attr))
            object.__delattr__(self, attr)
            if cmds.attributeQuery(attr, exists=True, node=self.mNode):
                cmds.setAttr('%s.%s' % (self.mNode,attr), l=False)
                cmds.deleteAttr('%s.%s' % (self.mNode, attr))
                
        except StandardError,error:
            raise StandardError(error)
          
    def hasAttr(self, attr):
        '''
        simple wrapper check for attrs on the mNode itself.
        Note this is not run in some of the core internal calls in this baseClass
        '''
        return cmds.attributeQuery(attr, exists=True, node=self.mNode)
    
    def attrIsLocked(self,attr):
        '''
        check the attribute on the mNode to see if it's locked
        '''
        return cmds.getAttr('%s.%s' % (self.mNode,attr), l=True)
    
    @nodeLockManager
    def attrSetLocked(self, attr, state):
        '''
        set the lockState of a given attr on the mNode
        '''
        try:
            if not self.isReferenced():
                cmds.setAttr('%s.%s' % (self.mNode,attr), l=state)
        except StandardError,error:
            log.debug(error)
    
    @nodeLockManager
    def renameAttr(self, currentAttr, newName):
        '''
        wrap over cmds.renameAttr
        '''
        cmds.renameAttr('%s.%s' % (self.mNode, currentAttr), newName)
        
    @nodeLockManager
    def addAttr(self, attr, value=None, attrType=None, hidden=False, **kws):
        '''
        Wrapped version of Maya addAttr that manages the basic type flags for you
        whilst also setting the attr on the MayaNode/class object itself. 
        I now merge in **kws to the dict I pass to the add and set commands here so you 
        can specify all standard cmds.addAttr, setAttr flags in the same call.
        ie min, max, l, k, cb
        
        :param attr:  attribute name to add (standard 'longName' flag)
        :param value: initial value to set, if a value is given the attribute type is automatically 
            determined for you.
        :param attrType: specify the exact type of attr to add. By default I try and resolve 
            this for you from the type of value passed in.
        :param hidden: whether the attr is set available in the channelBox (only applies keyable attrs)

        .. note:: 
            specific attr management for given types below: 
            
            >>> double3: self.addAttr(attr='attrName', attrType='double3',value=(value1,value2,value3))
            >>> float3:  self.addAttr(attr='attrName', attrType='float3', value=(value1,value2,value3))
            >>> enum:    self.addAttr(attr='attrName', attrType='enum',   value=1, enumName='Centre:Left:Right')
            >>> doubleArray: self.addAttr(attr='attrName', attrType='doubleArray', value=[1.0,2.0,3.0,4.0,5.0])
            >>> complex: self.addAttr('jsonDict', {'a':1.0,'b':2.0,'c':3.3,'d':['a','b','c']})
        
        .. note::
            max values for int is 2,147,483,647 (int32)
        '''
        added=False
        if attrType and attrType=='enum' and not 'enumName' in kws:
            raise ValueError('enum attrType must be passed with "enumName" keyword in args')
        
        DataTypeKws = {'string': {'longName':attr, 'dt':'string'}, \
                     'unicode': {'longName':attr, 'dt':'string'}, \
                     'int': {'longName':attr, 'at':'long'}, \
                     'bool': {'longName':attr, 'at':'bool'}, \
                     'float': {'longName':attr, 'at':'double'}, \
                     'float3': {'longName':attr, 'at':'float3'}, \
                     'double3': {'longName':attr, 'at':'double3'}, \
                     'doubleArray':{'longName':attr, 'dt':'doubleArray'}, \
                     'enum': {'longName':attr, 'at':'enum'}, \
                     'complex': {'longName':attr, 'dt':'string'}, \
                     'message': {'longName':attr, 'at':'message', 'm':True, 'im':True}, \
                     'messageSimple':{'longName':attr, 'at':'message', 'm':False}}
                
        keyable=['int','float','bool','enum','double3']
        addCmdEditFlags=['min','minValue','max','maxValue','defaultValue','dv',
                             'softMinValue','smn','softMaxValue','smx','enumName']
        setCmdEditFlags=['keyable','k','lock','l','channelBox','cb']
            
        addkwsToEdit={}
        setKwsToEdit={}
        if kws:
            for kw,v in kws.items():
                if kw in addCmdEditFlags:
                    addkwsToEdit[kw]=v
                elif kw in setCmdEditFlags:
                    setKwsToEdit[kw]=v
                     
        #ATTR EXSISTS - EDIT CURRENT
        #---------------------------
        if cmds.attributeQuery(attr, exists=True, node=self.mNode):
            # if attr exists do we force the value here?? NOOOO as I'm using this only
            # to ensure that when we initialize certain classes base attrs exist with certain properties.
            log.debug('"%s" :  Attr already exists on the Node' % attr)
            try:
                # allow some of the standard edit flags to be run even if the attr exists
                if kws:
                    if addkwsToEdit:
                        cmds.addAttr('%s.%s' % (self.mNode, attr), e=True, **addkwsToEdit)
                        log.debug('addAttr Edit flags run : %s = %s' % (attr, addkwsToEdit))
                    if setKwsToEdit:
                        cmds.setAttr('%s.%s' % (self.mNode, attr), **setKwsToEdit)
                        log.debug('setAttr Edit flags run : %s = %s' % (attr, setKwsToEdit))
            except:
                if self.isReferenced():
                    log.debug('Trying to modify and attr on a reference node')
            return
            
        #ATTR IS NEW, CREATE IT
        #----------------------
        else:
            try:
                if not attrType:
                    attrType = attributeDataType(value)
                DataTypeKws[attrType].update(addkwsToEdit)  # merge in **kws, allows you to pass in all the standard addAttr kws
                log.debug('addAttr : valueType : %s > dataType kws: %s' % (attrType, DataTypeKws[attrType]))
                cmds.addAttr(self.mNode, **DataTypeKws[attrType])

                if attrType == 'double3' or attrType == 'float3':
                    attr1 = '%sX' % attr
                    attr2 = '%sY' % attr
                    attr3 = '%sZ' % attr
                    cmds.addAttr(self.mNode, longName=attr1, at='double', parent=attr, **kws)
                    cmds.addAttr(self.mNode, longName=attr2, at='double', parent=attr, **kws)
                    cmds.addAttr(self.mNode, longName=attr3, at='double', parent=attr, **kws)
                    object.__setattr__(self, attr1, None)  # don't set it, just add it to the object
                    object.__setattr__(self, attr2, None)  # don't set it, just add it to the object
                    object.__setattr__(self, attr3, None)  # don't set it, just add it to the object
                    if attrType in keyable and not hidden:
                        cmds.setAttr('%s.%s' % (self.mNode, attr1), e=True, keyable=True)
                        cmds.setAttr('%s.%s' % (self.mNode, attr2), e=True, keyable=True)
                        cmds.setAttr('%s.%s' % (self.mNode, attr3), e=True, keyable=True)
                elif attrType == 'doubleArray':
                    # have to initialize this type or Maya doesn't pick the attrType up!
                    cmds.setAttr('%s.%s' % (self.mNode, attr), [], type='doubleArray')
                else:
                    if attrType in keyable and not hidden:
                        cmds.setAttr('%s.%s' % (self.mNode, attr), e=True, keyable=True)
                if value:
                    self.__setattr__(attr, value, force=False)
                else:
                    # bind the attr to the python object if no value passed in
                    object.__setattr__(self, attr, None)
                    
                # allow the addAttr to set any secondarty kws via the setAttr calls
                if setKwsToEdit:
                    cmds.setAttr('%s.%s' % (self.mNode, attr), **setKwsToEdit)
                    log.debug('setAttr Edit flags run : %s = %s' % (attr, setKwsToEdit))
                    
                added=True
            except StandardError,error:
                raise StandardError(error)
        return added
     
    def listAttrsOfType(self, Type='message'):
        '''
        this is a fast method to list all attrs of type on the mNode
        
        >>> [attr for attr in cmds.listAttr(self.mNode) if cmds.getAttr('%s.%s' % (self.mNode,attr),type=True)=='message']
        
        Simply using the above cmds calls is DOG SLOW upto this which goes via the Api.
        TODO: expand the Type support here
        '''
        depNodeFn=OpenMaya.MFnDependencyNode(self.mNodeMObject)
        attrCount = depNodeFn.attributeCount()
        ret = []
        for i in range(attrCount):
            attrObject = depNodeFn.attribute(i)
            if Type:
                if Type=='message':
                    if not attrObject.hasFn(OpenMaya.MFn.kMessageAttribute):
                        continue
            mPlug = depNodeFn.findPlug(attrObject)
            ret.append(mPlug.name().split('.')[1])
        return ret
    
    
    # Utity Functions
    #-------------------------------------------------------------------------------------
         
    def shortName(self):
        return self.mNode.split('|')[-1].split(':')[-1]
                 
    def select(self, *args, **kws):
        '''
        args and kws are now passed through into the Maya select call
        '''
        cmds.select(self.mNode, *args, **kws)
        
    @nodeLockManager
    def rename(self, name, renameChildLinks=False):
        '''
        rename the mNode itself, again because we get the mNode via the MObject renaming is handled correctly
        
        :param name: new name for the mNode
        :param renameChildLinks: set to False by default, this will rename connections back to the mNode 
            from children who are connected directly to it, via an attr that matches the current mNode name. 
            These connected Attrs will be renamed to reflect the change in node name
        '''
        currentName=self.shortName()
        cmds.rename(self.mNode, name)
        # UNDER TEST
        if renameChildLinks:
            plugs=cmds.listConnections(self.mNode,s=True,d=True,p=True)
            for plug in plugs:
                split=plug.split('.')
                attr=split[-1].split('[')[0]
                child=split[0]
                #print 'attr : ', attr, ' child : ', child, ' plug : ', plug, ' curName : ', currentName
                if attr==currentName:
                    try:
                        child=MetaClass(child)
                        child.renameAttr(attr, name)
                        log.debug('Renamed Child attr to match new mNode name : %s.%s' % (child.mNode, attr))
                    except:
                        log.debug('Failed to rename attr : %s on node : %s' % (attr, child.mNode))
              
    def delete(self):
        '''
        delete the mNode and this class instance
        WORKAROUND: Looks like there's a bug in the Network node in that deletion of a node
        will also delete all other connected networks...BIG DEAL. AD are looking into this for us
        '''
        global RED9_META_NODECACHE
        
        if cmds.lockNode(self.mNode, q=True):
            cmds.lockNode(self.mNode,lock=False)
        #clear the node from the cache
        if RED9_META_NODECACHE:
            if self.hasAttr('UUID'):
                if self.UUID in RED9_META_NODECACHE.keys():
                    RED9_META_NODECACHE.pop(self.getUUID())
            elif self.mNode in RED9_META_NODECACHE.keys():
                RED9_META_NODECACHE.pop(self.mNode)
        #delete the Maya node and this python object
        cmds.delete(self.mNode)
        del(self)
    
    @nodeLockManager
    def convertMClassType(self, newMClass, **kws):
        '''
        change the current mClass type of the node and re-initialize the object
        '''
        if newMClass in RED9_META_REGISTERY:
            removeFromCache(self)
            self.mClass=newMClass
            #we reset the cache so that the UUID's are all updated to account for the change in mClass  
            #resetCache()
            return MetaClass(self.mNode, **kws)
        else:
            raise StandardError('given class is not in the mClass Registry : %s' % newMClass)


    # Reference / Namespace Management Block
    #---------------------------------------------------------------------------------
    
    def isReferenced(self):
        '''
        is node.mNode referenced?
        '''
        return cmds.referenceQuery(self.mNode,inr=True)
    
    def referenceNode(self):
        '''
        if referenced return the referenceNode itself
        '''
        if self.isReferenced():
            return cmds.referenceQuery(self.mNode, rfn=True)
    
    def referencePath(self, wcn=False):
        '''
        if referenced return the referenced filepath
        '''
        if self.isReferenced():
            return cmds.referenceQuery(cmds.referenceQuery(self.mNode, rfn=True), filename=True, wcn=wcn)
        
    def nameSpace(self):
        '''
        This flag has been modified to return just the direct namespace
        of the node, not all nested namespaces if found. Now returns a string
        '''
        if self.isReferenced():
            return cmds.referenceQuery(self.mNode, ns=True).replace(':','')
        ns=self.mNode.split(':')
        if len(ns)>1:
            return ns[:-1][0]
        return ''

    def nameSpaceFull(self, asList=False):
        '''
        the namespace call has been modified to only return the single 
        direct namespace of a node, not the nested. This new func will
        return the namespace in it's entirity either as a list or a 
        catenated string
        :param asList: either return the namespaces in a list or as a catenated string (default)
        '''
        ns=self.mNode.split(':')
        if len(ns)>1:
            if asList:
                return ns[:-1]
            else:
                return ':'.join(ns[:-1])
        else:
            if asList:
                return []
            else:
                return ''
                    
        
        
    # Connection Management Block
    #---------------------------------------------------------------------------------
    
    def _getNextArrayIndex(self, node, attr):
        '''
        get the next available index in a multiMessage array
        '''
        ind=cmds.getAttr('%s.%s' % (node,attr),multiIndices=True)
        if not ind:
            return 0
        else:
            for i in ind:
                if not cmds.listConnections('%s.%s[%i]' % (node,attr,i)):
                    return i
            return ind[-1]+1
    
    def isChildNode(self, node, attr=None, srcAttr=None):
        '''
        test if a node is already connected to the mNode via a given attr link.
        Why the wrap? well this gets over the issue of array index's in the connections
        
        cmds.isConnected('node.attr[0]','other.attr[0]')
        fails if simply asked:
        cmds.isConnected('node.attr',other.attr')
        '''
        if issubclass(type(node), MetaClass):
            node=node.mNode
        if attr:
            cons=cmds.ls(cmds.listConnections('%s.%s' % (self.mNode,attr),s=False,d=True,p=True),l=True)
        else:
            cons=cmds.ls(cmds.listConnections(self.mNode,s=False,d=True,p=True),l=True)
        if cons:
            for con in cons:
                if srcAttr:
                    if '%s.%s' % (cmds.ls(node,l=True)[0],srcAttr) in con:
                        return True
                else:
                    if '%s.' % cmds.ls(node,l=True)[0] in con:
                        return True
        return False
        
    @nodeLockManager
    def connectChildren(self, nodes, attr, srcAttr=None, cleanCurrent=False, force=True, allowIncest=False):
        '''
        Fast method of connecting multiple nodes to the mNode via a message attr link.
        This call generates a MULTI message on both sides of the connection and is designed
        for more complex parent child relationships
        
        :param nodes: Maya nodes to connect to this mNode
        :param attr: Name for the message attribute
        :param srcAttr: if given this becomes the attr on the child node which connects it
                        to self.mNode. If NOT given this attr is set to self.mNodeID
        :param cleanCurrent:  Disconnect and clean any currently connected nodes to this attr.
                        Note this is operating on the mNode side of the connection, removing
                        any currently connected nodes to this attr prior to making the new ones
        :param force: Maya's default connectAttr 'force' flag, if the srcAttr is already connected
                        to another node force the connection to the new attr
        :param allowIncest: Over-ride the default behaviour when dealing with child nodes that are
                        standard Maya Nodes not metaNodes. Default in this case is to NOT index manage
                        the plugs, this flag overloads that, allow multiple parents.
        TODO: check the attr type, if attr exists and is a non-multi messgae then don't run the indexBlock
        '''
        
        #make sure we have the attr on the mNode
        self.addAttr(attr, attrType='message')
        
        if not issubclass(type(nodes),list):
            nodes=[nodes]
        if cleanCurrent:
            self.__disconnectCurrentAttrPlugs(attr)  # disconnect/cleanup current plugs to this attr
        if not srcAttr:
            srcAttr=self.mNodeID  # attr on the nodes source side for the child connection
        if not nodes:
            #this allows 'None' to be passed into the set attr calls and in turn, allow
            #self.mymessagelink=None to clear all current connections
            return
        for node in nodes:
            ismeta=False
            if isMetaNode(node):
                ismeta=True
                if not issubclass(type(node), MetaClass):  # allows you to pass in an metaClass
                    MetaClass(node).addAttr(srcAttr, attrType='message')
                else:
                    node.addAttr(srcAttr, attrType='message')
                    node=node.mNode
            elif not cmds.attributeQuery(srcAttr, exists=True, node=node):
                if allowIncest:
                    MetaClass(node).addAttr(srcAttr, attrType='message')
                else:
                    cmds.addAttr(node, longName=srcAttr, at='message', m=True, im=False)
            try:
                #also we need to add the self.allowIncest flag to trigger managed message links like this.
                if not self.isChildNode(node, attr, srcAttr):
                    if ismeta or allowIncest:
                        if ismeta:
                            log.debug('connecting MetaData nodes via indexes :  %s.%s >> %s.%s' % (self.mNode,attr,node,srcAttr))
                        elif allowIncest:
                            log.debug('connecting Standard Maya nodes via indexes : %s.%s >> %s.%s' % (self.mNode,attr,node,srcAttr))
                        cmds.connectAttr('%s.%s[%i]' % (self.mNode, attr, self._getNextArrayIndex(self.mNode,attr)),
                                     '%s.%s[%i]' % (node, srcAttr, self._getNextArrayIndex(node,srcAttr)), f=force)
                    else:
                        log.debug('connecting %s.%s >> %s.%s' % (self.mNode,attr,node,srcAttr))
                        cmds.connectAttr('%s.%s' % (self.mNode,attr),'%s.%s' % (node,srcAttr), f=force)
                else:
                    raise StandardError('"%s" is already connected to metaNode "%s"' % (node,self.mNode))
            except StandardError,error:
                log.warning(error)
                
    @nodeLockManager
    def connectChild(self, node, attr, srcAttr=None, cleanCurrent=True, force=True):
        '''
        Fast method of connecting a node to the mNode via a message attr link. This call
        generates a NONE-MULTI message on both sides of the connection and is designed
        for simple parent child relationships.
        
        NOTE: this call by default manages the attr to only ONE CHILD to
        avoid this use cleanCurrent=False
        :param node: Maya node to connect to this mNode
        :param attr: Name for the message attribute
        :param srcAttr: If given this becomes the attr on the child node which connects it
                        to self.mNode. If NOT given this attr is set to self.mNodeID
        :param cleanCurrent: Disconnect and clean any currently connected nodes to this attr.
                        Note this is operating on the mNode side of the connection, removing
                        any currently connected nodes to this attr prior to making the new ones
        :param force: Maya's default connectAttr 'force' flag, if the srcAttr is already connected
                        to another node force the connection to the new attr
        TODO: do we move the cleanCurrent to the end so that if the connect fails you're not left
        with a half run setup?
        
        '''
        #make sure we have the attr on the mNode, if we already have a MULIT-message
        #should we throw a warning here???
        self.addAttr(attr, attrType='messageSimple')

        try:
            if cleanCurrent:
                self.__disconnectCurrentAttrPlugs(attr)  # disconnect/cleanup current plugs to this attr
            if not srcAttr:
                srcAttr=self.mNodeID  # attr on the nodes source side for the child connection
            if not node:
                #this allows 'None' to be passed into the set attr calls and in turn, allow
                #self.mymessagelink=None to clear all current connections
                return
            if isMetaNode(node):
                if not issubclass(type(node), MetaClass):  # allows you to pass in an metaClass
                    MetaClass(node).addAttr(srcAttr,attrType='messageSimple')
                else:
                    node.addAttr(srcAttr,attrType='messageSimple')
                    node=node.mNode
            elif not cmds.attributeQuery(srcAttr, exists=True, node=node):
                cmds.addAttr(node, longName=srcAttr, at='message', m=False)
                
            if not self.isChildNode(node, attr, srcAttr):
                cmds.connectAttr('%s.%s' % (self.mNode,attr),'%s.%s' % (node,srcAttr), f=force)
            else:
                raise StandardError('%s is already connected to metaNode' % node)
        except StandardError, error:
            log.warning(error)
    
    @nodeLockManager
    def connectParent(self, node, attr, srcAttr=None, cleanCurrent=True):
        '''
        Fast method of connecting message links to the mNode as parents
        :param nodes: Maya nodes to connect to this mNode
        :param attr: Name for the message attribute on eth PARENT!
        :param srcAttr: If given this becomes the attr on the node which connects it
                        to the parent. If NOT given this attr is set to parents shortName
        :param cleanCurrent: Exposed from teh connectChild code which is basically what this is running in reverse
        TODO: Modify so if a metaClass is passed in use it's addAttr cmd so the new
        attr is registered in the class given
        TODO: Manage connection Index like the connectChildren call does?
        '''
        if not issubclass(type(node), MetaClass):
            node=MetaClass(node)
        if not srcAttr:
            srcAttr=node.shortName()
        #self.addAttr(srcAttr, attrType='message')
        try:
#            if not cmds.attributeQuery(attr, exists=True, node=node):
#                #add to parent node
#                cmds.addAttr(node,longName=attr, at='message', m=False)
#            cmds.connectAttr('%s.%s' % (node,attr),'%s.%s' % (self.mNode,srcAttr))
            node.connectChild(self, attr, srcAttr, cleanCurrent=cleanCurrent)
        except StandardError,error:
                log.warning(error)
                
    @nodeLockManager
    def __disconnectCurrentAttrPlugs(self, attr):
        '''
        from a given attr on the mNode disconnect any current connections and
        clean up the plugs by deleting the existing attributes
        '''
        currentConnects=self.__getattribute__(attr)
        if currentConnects:
            if not isinstance(currentConnects,list):
                currentConnects=[currentConnects]
            for connection in currentConnects:
                try:
                    #log.debug('Disconnecting %s.%s >> from : %s' % (self.mNode,attr,connection))
                    self.disconnectChild(connection, attr=attr, deleteSourcePlug=True, deleteDestPlug=False)
                except:
                    log.warning('Failed to unconnect current message link')
                    
    @nodeLockManager
    def disconnectChild(self, node, attr=None, deleteSourcePlug=True, deleteDestPlug=True):
        '''
        disconnect a given child node from the mNode. Default is to remove
        the connection attribute in the process, cleaning up both sides of
        the connection. Note that the attrs only get removed if nothing
        else is connected to it, ie, it's safe to do so.
        :param node: the Maya node to disconnect from the mNode
        :param deleteSourcePlug: if True delete SOURCE side attribiute after disconnection
                        but ONLY if it's no longer connected to anything else.
        :param deleteDestPlug: if True delete the DESTINATION side attribiute after disconnection
                        but ONLY if it's no longer connected to anything else.
        
        >>> #testCode:
        >>> master  = r9Meta.MetaClass(name = 'master')
        >>> master2 = r9Meta.MetaClass(name = 'master2')
        >>> child1 = r9Meta.MetaClass(name = 'child1')
        >>> child2 = r9Meta.MetaClass(name = 'child2')
        >>> cube=cmds.ls(cmds.polyCube()[0],l=True)[0]
        >>> master.connectChildren([child1,child2,cube],'modules','puppet')
        >>> master2.connectChildren([child1.mNode,child2.mNode,cube],'time','master',force=True)
        >>> master.connectChildren([child1,child2],'time','master',cleanCurrent=True)
        >>> 
        >>> master.disconnectChild(child2,'time')
        >>> #or
        >>> master.disconnectChild(child2)
        '''
        sPlug=None
        dPlug=None
        sPlugMeta=None
        returnData=[]
        searchConnection='%s.' % self.mNode.split('|')[-1]
        if attr:
            searchConnection='%s.%s' % (self.mNode.split('|')[-1],attr)
        if isMetaNode(node):  # and issubclass(type(node), MetaClass):
            sPlugMeta=node
            node=node.mNode
        cons=cmds.listConnections(node,s=True,d=False,p=True,c=True)

        if not cons:
            raise StandardError('%s is not connected to the mNode %s' % (node,self.mNode))
        for sPlug,dPlug in zip(cons[0::2],cons[1::2]):
            log.debug('attr Connection inspected : %s << %s' % (sPlug,dPlug))
            #print 'searchCon : ', searchConnection
            #print 'dPlug : ', dPlug
            if searchConnection in dPlug:
                log.debug('Disconnecting %s >> %s as %s found in dPlug' % (dPlug,sPlug,searchConnection))
                cmds.disconnectAttr(dPlug,sPlug)
                returnData.append((dPlug,sPlug))

        if deleteSourcePlug:  # child node
            try:
                allowDelete=True
                attr=sPlug.split('[')[0]  # split any multi-indexing from the plug ie node.attr[0]
                if cmds.listConnections(attr):
                    allowDelete=False
                    log.debug('sourceAttr connections remaining: %s' % \
                              ','.join(cmds.listConnections(attr)))
                if allowDelete:
                    log.debug('Deleting deleteSourcePlug Attr %s' % (attr))
                    if sPlugMeta:
                        delattr(sPlugMeta,attr.split('.')[-1])
                    else:
                        cmds.deleteAttr(attr)
                else:
                    log.debug('deleteSourcePlug attr aborted as node still has connections')
            except StandardError,error:
                log.warning('Failed to Remove mNode Connection Attr')
                log.debug(error)
        if deleteDestPlug:  # self
            try:
                allowDelete=True
                attr=dPlug.split('[')[0]  # split any multi-indexing from the plug ie node.attr[0]
                if cmds.listConnections(attr):
                    allowDelete=False
                    log.debug('sourceAttr connections remaining: %s' % \
                              ','.join(cmds.listConnections(attr)))
                if allowDelete:
                    log.debug('Deleting deleteDestPlug Attr %s' % (attr))
                    delattr(self,attr.split('.')[-1])
                    #cmds.deleteAttr(attr)
                else:
                    log.debug('deleteDestPlug attr aborted as node still has connections')
            except StandardError,error:
                log.warning('Failed to Remove Node Connection Attr')
                log.debug(error)
                
        return returnData

    # Get Nodes Management Block
    #---------------------------------------------------------------------------------
    
    def addChildMetaNode(self, mClass, attr, srcAttr=None, nodeName=None, **kws):
        '''
        Generic call to add a MetaNode as a Child of self
        
        :param mClass: mClass to generate, given as a valid key to the 
            RED9_META_REGISTERY ie 'MetaRig' OR a class object, ie r9Meta.MetaRig
        :param attr: message attribute to wire the new node too
        :param name: optional name to give the new name
        '''
        key=mTypesToRegistryKey(mClass)[0]
        if key in RED9_META_REGISTERY:
            childClass=RED9_META_REGISTERY[key]
            mChild=childClass(name=nodeName,**kws)
            self.connectChild(mChild, attr, srcAttr=srcAttr, **kws)
            return mChild
        
    @r9General.Timer
    def getChildMetaNodes(self, walk=False, mAttrs=None, **kws):
        '''
        Find any connected Child MetaNodes to this mNode.
        
        :param walk: walk the connected network and return ALL children conntected in the tree 
        :param mAttrs: only return connected nodes that pass the given attribute filter 
        
        .. note:: 
            mAttrs is only searching attrs on the mNodes themselves, not all children
            and although there is no mTypes flag, you can use mAttrs to get childnodes of type
            by going getChildMetaNodes(mAttrs='mClass=MetaRig')
        
        .. note:: 
            Because the **kws are passed directly to the getConnectedMetaNods func, it will
            also take ALL of that functions **kws functionality in the initial search:
            source=True, destination=True, mTypes=[], mInstances=[], mAttrs=None, dataType='mClass'
        
        :TODO: allow this to walk over nodes, at the moment if the direct child isn't of the correct 
            type (if using the mTypes flag) then the walk will stop. This should continue over non matching 
            nodes down the hierarchy so all children are tested.
            !!!!!!!!!!!!!! THIS NEEDS FIXING ASAP !!!!!!!!!!!!!! or at least a flag to 'skip_over_unmatched'
        '''

        if not walk:
            return getConnectedMetaNodes(self.mNode, source=False, destination=True, mAttrs=mAttrs, dataType='mClass', **kws)
        else:
            metaNodes=[]
            children=getConnectedMetaNodes(self.mNode, source=False, destination=True, mAttrs=mAttrs, dataType='unicode', **kws)
 
            if children:
                runaways=0
                depth=0
                processed=[]
                extendedChildren=[]
                while children and runaways<=1000:
                    for child in children:
                        mNode=child
                        if mNode not in processed:
                            metaNodes.append(child)
                        else:
                            #print('skipping as node already processed : %s' % mNode)
                            children.remove(child)
                            continue
                            #log.info('mNode added to metaNodes : %s' % mNode)
                        children.remove(child)
                        processed.append(mNode)
                        #log.info( 'connections too : %s' % mNode)
                        extendedChildren.extend(getConnectedMetaNodes(mNode,source=False,destination=True,mAttrs=mAttrs, dataType='unicode', **kws))
                        #log.info('left to process : %s' % ','.join([c.mNode for c in children]))
                        if not children:
                            if extendedChildren:
                                log.debug('Child MetaNode depth extended %i' % depth)
                                #log.debug('Extended Depth child List: %s' % ','.join([c.mNode for c in extendedChildren]))
                                children.extend(extendedChildren)
                                extendedChildren=[]
                                depth+=1
                        runaways+=1
                return [MetaClass(node) for node in metaNodes]
        return []
    
    def getParentMetaNode(self, **kws):
        '''
        Find any connected Parent MetaNode to this mNode
        
        .. note::
            Because the **kws are passed directly to the getConnectedMetaNods func, it will
            also take ALL of that functions kws
            source=True, destination=True, mTypes=[], mInstances=[], mAttrs=None, dataType='mClass'
            
        TODO: implement a walk here to go upstream
        '''
        mNodes=getConnectedMetaNodes(self.mNode,source=True,destination=False, **kws)
        if mNodes:
            return mNodes[0]

    @r9General.Timer
    def getChildren(self, walk=True, mAttrs=None, cAttrs=[], nAttrs=[], asMeta=False, asMap=False):
        '''
        This finds all UserDefined attrs of type message and returns all connected nodes
        This is now being run in the MetaUI on doubleClick. This is a generic call, implemented
        and over-loaded on a case by case basis. At the moment the MetaRig class simple calls
        mRig.getRigCtrls() in the call, but it means that we don't call .mRig.getRigCtrls()
        in generic meta functions.
        
        :param walk: walk all subMeta connections and include all their children too
        :param mAttrs: only search connected mNodes that pass the given attribute filter (attr is at the metaSystems level)
        :param cAttrs: only pass connected children whos connection to the mNode matches the given attr (accepts wildcards)
        :param nAttrs: search returned MayaNodes for given set of attrs and only return matched nodes
        :param asMeta: return instantiated mNodes regardless of type
        :param asMap: return the data as a map such that {mNode.plugAttr:[nodes], mNode.plugAttr:[nodes]}
        
        .. note:: 
            mAttrs is only searching attrs on the mNodes themselves, not the children
            cAttrs is searching the connection attr names from the mNodes, uses the cmds.listAttr 'st' flag
        '''
        childMetaNodes=[self]
        children=[]
        attrMapData={}
        if walk:
            childMetaNodes.extend([node for node in self.getChildMetaNodes(walk=True, mAttrs=mAttrs)])
        for node in childMetaNodes:
            log.debug('MetaNode getChildren : %s >> %s' % (type(node), node.mNode))
            attrs = cmds.listAttr(node.mNode, ud=True, st=cAttrs)
            if attrs:
                for attr in attrs:
                    if cmds.getAttr('%s.%s' % (node.mNode, attr), type=True) == 'message':
                        msgLinked = cmds.listConnections('%s.%s' % (node.mNode, attr), destination=True, source=False)
                        if msgLinked:
                            if not nAttrs:
                                msgLinked = cmds.ls(msgLinked, l=True)  # cast to longNames!
                                if not asMap:
                                    children.extend(msgLinked)
                                else:
                                    attrMapData['%s.%s' % (node.mNode,attr)]=msgLinked
                            else:
                                for linkedNode in msgLinked:
                                    for attr in nAttrs:
                                        if cmds.attributeQuery(attr, exists=True, node=linkedNode):
                                            linkedNode = cmds.ls(linkedNode, l=True)  # cast to longNames!
                                            #children.extend(linkedNode)
                                            if not asMap:
                                                children.extend(linkedNode)
                                            else:
                                                attrMapData['%s.%s' % (node.mNode,attr)]=linkedNode
                                            break
                                            break
            else:
                log.debug('no matching attrs : %s found on node %s' % (cAttrs,node))
        if self._forceAsMeta or asMeta and not asMap:
            return [MetaClass(node) for node in children]
        if asMap:
            return attrMapData
        return children
    
    @staticmethod
    def getNodeConnectionMetaDataMap(node, mTypes=[]):  #  toself=False, allplugs=False):
        '''
        This is a generic wrapper to extract metaData connection info for any given node
        used currently to build the pose dict up, and compare / match the data on load.
        In the base implementation this gives you a dict of mNodeID and attr which the nodes is connected too.
        
        :param node: node to inspect and get the connection data back from 
        :return: mNodes={} which is directly pushed into the PoseFile under the [metaData] key 
        
        .. note::
            This is designed to be overloaded so you can craft your own metaData block in the
            poseFiles, allows you to craft the data you want to store against a node.
        '''
        if type(node)==list:
            raise StandardError("getNodeConnectionMetaDataMap: node must be a single node, not an list")
        mNodes={}
        #why not use the r9Meta.getConnectedMetaNodes ?? > well here we're using
        #the c=True flag to get both plugs back in one go to process later
        connections=[]
        for nType in getMClassNodeTypes():
            con=cmds.listConnections(node,type=nType,s=True,d=False,c=True,p=True)
            if con:
                connections.extend(con)
        if not connections:
            return connections

        log.debug('%s : connectionMap : %s' % (node.split('|')[-1].split(':')[-1],connections[1::2]))

        for con in connections[1::2]:
            data = con.split('.')  # attr
            if isMetaNode(data[0], mTypes=mTypes):
                mNodes['metaAttr'] = data[1]
                try:
                    mNodes['metaNodeID']=cmds.getAttr('%s.mNodeID' % data[0])
                except:
                    mNodes['metaNodeID']=node.split(':')[-1].split('|')[-1]
                return mNodes
            elif mTypes:
                continue
            if not mTypes:  # if not mTypes passed bail the loop and return the first connection
                return mNodes
        return mNodes

    def getNodeConnetionAttr(self, node):
        '''
        really light wrapper, designed to return the attr via which a node
        is connected to this metaNode
        
        :param node: node to test connection attr for
        
        .. note::
            This will be depricated soon and replaced by getNodeConnections which is
            more flexible as it returns and filters all plugs between self and the given node.
        '''
        log.debug('getNodeConnectionAttr will be depricated soon!!!!')
        for con in cmds.listConnections(node,s=True,d=False,p=True):
            if self.mNode in con.split('.')[0]:
                return con.split('.')[1]
        
    def getNodeConnections(self, node, filters=[]):
        '''
        really light wrapper, designed to return all connections
        between a given node and the mNode
        
        :param node: node to test connection attr for
        :param filters: filter string to match for the returns
        '''
        cons=[]
        for con in cmds.listConnections(node,s=True,d=False,p=True):
            if self.mNode in con.split('.')[0]:
                if filters:
                    for flt in filters:
                        if flt in con.split('.')[1]:
                            cons.append(con.split('.')[1])
                else:
                    cons.append(con.split('.')[1])
        return cons
            
def deleteEntireMetaRigStructure(searchNode=None):
    '''
    This is a hard core unplug and cleanup of all attrs added by the
    MetaRig, all connections and all nodes. Use CAREFULLY!
    '''
    import Red9_AnimationUtils as r9Anim  # lazy to stop cyclic as anim also import meta
    if searchNode and not cmds.objExists(searchNode):
        raise StandardError('given searchNode doesnt exist')
    if not searchNode:
        searchNode=cmds.ls(sl=True)[0]
    mRig=getConnectedMetaSystemRoot(searchNode)
    if not mRig:
        raise StandardError('No root MetaData system node found from given searchNode')
    mNodes=[]
    mNodes.append(mRig)
    mNodes.extend(mRig.getChildMetaNodes(walk=True))
    mNodes.reverse()
    
    for a in mNodes:
        print a
    
    for metaChild in mNodes:
        for child in metaChild.getChildren(walk=False):
            metaChild.disconnectChild(child)
            r9Anim.MirrorHierarchy().deleteMirrorIDs(child)
            #For the time being I'm adding the OLD mirror markers to this
            #call for the sake of cleanup on old rigs
            if cmds.attributeQuery('mirrorSide', exists=True, node=child):
                cmds.deleteAttr('%s.mirrorSide' % child)
            if cmds.attributeQuery('mirrorIndex', exists=True, node=child):
                cmds.deleteAttr('%s.mirrorIndex' % child)
            if cmds.attributeQuery('mirrorAxis', exists=True, node=child):
                cmds.deleteAttr('%s.mirrorAxis' % child)
        metaChild.delete()

def wireControlsToNewMetaRig(nodes, name=None, mRig=None):
    '''
    fast way to wire nodes to a blank MetaRig to gain some of the support
    features of the codebase without having to manually build a structured network
    
    :param nodes: nodes to wire as controllers to the MetaRig
    :param name: name of the MetaRig node
    :param mRig: optional mRig instance to add the controls too
    '''
    if not mRig:
        mRig=MetaRig(name=name)
    for node in nodes:
        mRig.addRigCtrl(node, r9Core.nodeNameStrip(node))
    return mRig
    
class MetaRig(MetaClass):
    '''
    Sub-class of Meta used as the back-bone of our internal rigging
    systems. This is the core of how we hook all our tools to meta
    in a seamless manner and bind some core functionality.
    '''
    def __init__(self,*args,**kws):
        '''
        :param name: name of the node and in this case, the RigSystem itself
        '''
        super(MetaRig, self).__init__(*args,**kws)

        if self.cached:
            log.debug('CACHE : Aborting __init__ on pre-cached %s Object' % self.__class__)
            return
        # note these are attrs on the mNode itself so we need to be careful when setting 
        # them to locked if this node is referenced.
        self.mClassGrp = 'MetaRig'      # get the Grp code marking this as a SystemBase
        self.mSystemRoot = True         # set this node to be a system root if True
        
        # general management vars
        self.CTRL_Prefix = 'CTRL'       # prefix for all connected CTRL_ links added
        self.rigGlobalCtrlAttr = 'CTRL_Main'  # attribute linked to the top globalCtrl in the rig
        self.lockState = True           # lock the node to avoid accidental removal
        self.parentSwitchAttr = ['parent']  # attr used for parentSwitching
        self.MirrorClass = None         # capital as this binds to the MirrorClass directly
        # self.poseSkippedAttrs = []    # attributes which are to be IGNORED by the posesaver, set by you for your needs!

    def __bindData__(self):
        self.addAttr('version',1.0)  # ensure these are added by default
        self.addAttr('rigType', '')  # ensure these are added by default
        self.addAttr('renderMeshes', attrType='message')
        self.addAttr('exportSkeletonRoot', attrType='messageSimple')
        self.addAttr('scaleSystem', attrType='messageSimple')
    
    @property
    def characterSet(self):
        '''
        return the first connected characterSet found to children
        '''
        for node in self.getChildren(walk=True):
            chSet=cmds.listConnections(node, type='character')
            if chSet:
                return chSet[0]
                 
    def addGenericCtrls(self, nodes):
        '''
        Pass in a list of objects to become generic, non specific
        controllers for a given setup. These are all connected to the same slot
        so don't have the search capability that the funct below gives
        '''
        self.connectChildren(nodes, 'RigCtrls')
        
    def addRigCtrl(self, node, ctrType, mirrorData=None, boundData=None):
        '''
        Add a single CTRL of managed type as a child of this mRig.
        
        :param node: Maya node to add 
        :param ctrType: Attr name to assign this too 
        :param mirrorData: {side:'Left', slot:int, axis:'translateX,rotateY,rotateZ'..} 
        :param boundData: {} any additional attrData, set on the given node as attrs 
        
        .. note::
            | mirrorData[slot] must NOT == 0 as it'll be handled as not set by the core.
            | ctrType >> 'Main' is the equivalent of the RootNode in the FilterNode calls.
            
        TODO: allow the mirror block to include an offset so that if you need to inverse AND offset 
        by 180 to get left and right working you can still do so.
        '''
        #import Red9_AnimationUtils as r9Anim  # lazy load to avoid cyclic imports
        
        if isinstance(node,list):
            raise StandardError('node must be a single Maya Object')
        
        self.connectChild(node,'%s_%s' % (self.CTRL_Prefix,ctrType))
        if mirrorData:
            mirror = r9Anim.MirrorHierarchy()
            axis=None
            if 'axis' in mirrorData:
                axis = mirrorData['axis']
            mirror.setMirrorIDs(node,
                                side=mirrorData['side'],
                                slot=mirrorData['slot'],
                                axis=axis)
        if boundData:
            if issubclass(type(boundData),dict):
                for key, value in boundData.iteritems():
                    log.debug('Adding boundData to node : %s:%s' %(key,value))
                    MetaClass(node).addAttr(key, value=value)
                         
    def getRigCtrls(self, walk=False, mAttrs=None):
        '''
        Depricated Code - use getChildren call now
        '''
        return self.getChildren(walk, mAttrs)
        
    def getChildren(self, walk=True, mAttrs=None, cAttrs=[], nAttrs=[], asMeta=False, asMap=False):
        '''
        Massively important bit of code, this is used by most bits of code
        to find the child controllers linked to this metaRig instance.
        
        .. note::
            MetaRig getChildren has overloads adding the CTRL_Prefix to the cAttrs so that
            the retunr is just the controllers in the rig. It also now has additional logic
            to add any FacialCore system chidren by adding it's internal CTRL_Prefix to the list
        '''
        if not cAttrs:
            cAttrs=['RigCtrls', '%s_*' % self.CTRL_Prefix]
            if self.getFacialSystem():
                cAttrs.append('%s_*' % self.FacialCore.CTRL_Prefix)

        return super(MetaRig, self).getChildren(walk=walk, mAttrs=mAttrs, cAttrs=cAttrs, nAttrs=nAttrs, asMeta=asMeta, asMap=asMap)
        #return self.getRigCtrls(walk=walk, mAttrs=mAttrs)
       
    def getSkeletonRoots(self):
        '''
        get the Skeleton Root, used in the poseSaver. By default this looks
        for a message link via the attr "exportSkeletonRoot" to the skeletons root jnt
        always returns a list!
        '''
        if self.hasAttr('exportSkeletonRoot') and self.exportSkeletonRoot:
            return self.exportSkeletonRoot
        elif self.hasAttr('skeletonRoot') and self.skeletonRoot:
            return self.skeletonRoot
        return None
    
    def getFacialSystem(self):
        '''
        if we have a FacialCore node return it
        '''
        if self.hasAttr('FacialCore'):
            if isMetaNode(self.FacialCore):
                return self.FacialCore

#    def getParentSwitchData(self):
#        '''
#        Simple func for over-loading. This returns a list of tuples [(node,attr)] for all
#        found parentSwitch attrs on your rig. This is used by the PoseLaoder to maintain
#        parentSwitching when a pose is applied.
#        Note: that by default I assume you use the same attr name for all parent switching
#        on your rig. If not then you'll have to over-load this more carefully.
#        '''
#        parentSwitches=[]
#        for child in self.getChildren(walk=True):
#            if cmds.attributeQuery(self.parentSwitchAttr, exists=True,node=child):
#                parentSwitches.append((child, self.parentSwitchAttr, cmds.getAttr('%s.%s' % (child,self.parentSwitchAttr))))
#        return parentSwitches


    # Generic presets so we can be consistent, these are really only examples
    #---------------------------------------------------------------------------------
    
    def addWristCtrl(self,node,side,axis=None):
        self.addRigCtrl(node,'%s_Wrist' % side[0],
                        mirrorData={'side':side, 'slot':1,'axis':axis})
    def addElbowCtrl(self,node,side,axis=None):
        self.addRigCtrl(node,'%s_Elbow' % side[0],
                        mirrorData={'side':side, 'slot':2,'axis':axis})
    def addClavCtrl(self,node,side,axis=None):
        self.addRigCtrl(node,'%s_Clav' % side[0],
                        mirrorData={'side':side, 'slot':3,'axis':axis})
    def addFootCtrl(self,node,side,axis=None):
        self.addRigCtrl(node,'%s_Foot' % side[0],
                        mirrorData={'side':side, 'slot':4,'axis':axis})
    def addKneeCtrl(self,node,side,axis=None):
        self.addRigCtrl(node,'%s_Knee' % side[0],
                        mirrorData={'side':side, 'slot':5,'axis':axis})
    def addPropCtrl(self,node,side,axis=None):
        self.addRigCtrl(node,'%s_Prop' % side[0],
                        mirrorData={'side':side, 'slot':6,'axis':axis})

    #NOTE: Main should be the Top World Space Control for the entire rig
    #====================================================================
    def addMainCtrl(self,node,side='Centre',axis=None):
        self.addRigCtrl(node,'Main',
                        mirrorData={'side':side, 'slot':1,'axis':axis})
    def addRootCtrl(self,node,side='Centre',axis=None):
        self.addRigCtrl(node,'Root',
                        mirrorData={'side':side, 'slot':2,'axis':axis})
    def addHipCtrl(self,node,side='Centre',axis=None):
        self.addRigCtrl(node,'Hips',
                        mirrorData={'side':side, 'slot':3,'axis':axis})
    def addChestCtrl(self,node,side='Centre',axis=None):
        self.addRigCtrl(node,'Chest',
                        mirrorData={'side':side, 'slot':4,'axis':axis})
    def addHeadCtrl(self,node,side='Centre',axis=None):
        self.addRigCtrl(node,'Head',
                        mirrorData={'side':side, 'slot':5,'axis':axis})
    def addNeckCtrl(self,node,side='Centre',axis=None):
        self.addRigCtrl(node,'Neck',
                        mirrorData={'side':side, 'slot':6,'axis':axis})
 
    def addSupportMetaNode(self, attr, nodeName=None, mClass='MetaRigSupport', **kws):
        '''
        Not sure the best way to do this, but was thinking that the main mRig
        node should be able to have sub MetaClass nodes to cleanly define
        what nodes are AnimCtrls, and what nodes you want to tag as Support
        subsystems, ie, ikSolvers and construction nodes within the rig
        
        :param attr: Attribute used in the message link. Note this is what you use
            to transerve the Dag tree so use something sensible!
        :param nodeName: Name of the MetaClass network node created
        :param mClass: the class to be used for the support node - 'MetaRigSupport' by default
        '''
        if not nodeName:
            nodeName=attr
        return self.addChildMetaNode(mClass, attr=attr, nodeName=nodeName, **kws)
  
    def addSupportNode(self, node, attr, boundData=None):
        '''
        Add a single MAYA node flagged as a SUPPORT node of managed type
        Really in the MetaRig design these should be wired to a MetaRigSupport node
        
        :param node: Maya node to add
        :param attr: Attr name to assign this too
        :param boundData: {} Data to set on the given node as attrs
        '''
        self.connectChild(node,'SUP_%s' % attr)
        if boundData:
            if issubclass(type(boundData),dict):
                for key, value in boundData.iteritems():
                    log.debug('Adding boundData to node : %s:%s' %(key,value))
                    MetaClass(node).addAttr(key, value=value)
                        
    def addMetaSubSystem(self, systemType, side, attr=None, nodeName=None, mClass='MetaRigSubSystem'):
        '''
        Basic design of a MetaRig is that you have sub-systems hanging off an mRig
        node, managing all controllers and data for a particular system, such as an
        Arm system.
        
        :param systemType: Attribute used in the message link. Note this is what you use
            to transerve the Dag tree so use something sensible!
        :param mirrorSide: Side to designate the system. This is an enum: Centre,Left,Right
        :param nodeName: Name of the MetaClass network node created
        :param mClass: the class to be used for the support node - 'MetaRigSubSystem' by default
        '''
        r9Anim.MirrorHierarchy()._validateMirrorEnum(side)  # ??? do we just let the enum __setattr__ handle this?

        if not attr:
            attr='%s_%s_System' % (side[0],systemType)
        if not nodeName:
            nodeName=attr
        subSystem=self.addChildMetaNode(mClass, attr=attr, nodeName=nodeName)
        
        #set the attrs on the newly created subSystem MetaNode
        subSystem.systemType=systemType
        subSystem.mirrorSide=side
        return subSystem
    
    def set_ctrlColour(self, colourIndex=4):
        '''
        set the override colour of a given nodes shapes
        '''
        for ctrl in self.getChildren(walk=False):
            shapes = cmds.listRelatives(ctrl,type='shape',f=True)
            if shapes:
                for shape in shapes:
                    cmds.setAttr('%s.overrideEnabled' % shape, 1)
                    cmds.setAttr('%s.overrideColor' % shape, colourIndex)
                                  
    def getMirrorData(self):
        '''
        Bind the MirrorObject to this instance of MetaRig.
        
        .. note::
            you must run this binding function before using any of
            the inbuilt mirror functions
        '''
        self.MirrorClass = r9Anim.MirrorHierarchy(nodes=self.getRigCtrls(walk=True))
        self.MirrorClass.getMirrorSets()
        log.debug('Filling the MirrorClass attr on demand')
        return self.MirrorClass
    
    def loadMirrorDataMap(self, mirrorMap):
        '''
        load a mirror setup onto this rig from a stored mirrorMap file
        '''
        if not self.MirrorClass:
            self.MirrorClass = self.getMirrorData()
        if not os.path.exists(mirrorMap):
            raise IOError('Given MirrorMap file not found : %s' % mirrorMap)
        r9Anim.MirrorHierarchy(self.getChildren()).loadMirrorSetups(mirrorMap)
    
    def getMirror_opposites(self, nodes, forceRefresh=False):
        '''
        from the given nodes return a map of the opposite pairs of controllers
        so if you pass in a right controller of mirrorIndex 4 you get back the
        left[4] mirror node and visa versa. Centre controllers pass straight through
        '''
        if not self.MirrorClass or forceRefresh:
            self.MirrorClass = self.getMirrorData()
        oppositeNodes=[]
        
        for node in nodes:
            side=self.MirrorClass.getMirrorSide(node)
            if not side:
                continue
            if side=='Left':
                oppositeNodes.append(self.MirrorClass.mirrorDict['Right'][str(self.MirrorClass.getMirrorIndex(node))]['node'])
            if side=='Right':
                oppositeNodes.append(self.MirrorClass.mirrorDict['Left'][str(self.MirrorClass.getMirrorIndex(node))]['node'])
            if side=='Centre':
                oppositeNodes.append(node)
        return oppositeNodes
    
    def getMirror_ctrlSets(self, set='Centre'):
        '''
        from  the metaNode grab all controllers and return sets of nodes
        based on their mirror side data
        '''
#         submNodes=mRig.getChildMetaNodes(mAttrs=['mirrorSide=2'], walk=True)
#         ctrls=[]
#         for node in submNodes:
#             ctrls.extend(node.getChildren())
#         return ctrls
        ctrls=[]
        if not self.MirrorClass:
            self.MirrorClass = self.getMirrorData()
        for _, value in self.MirrorClass.mirrorDict[set].items():
            ctrls.append(value['node'])
        return ctrls
                
    def mirror(self, nodes=None, mode='Anim'):
        '''
        direct mapper call to the Mirror functions
        '''
        if not self.MirrorClass:
            self.MirrorClass = self.getMirrorData()
        self.MirrorClass.mirrorData(nodes, mode)
    
    @nodeLockManager
    def poseCacheStore(self, attr=None, filepath=None, *args, **kws):
        '''
        intended as a cached pose for this mRig, if an attr is given then
        the cached pose is stored internally on the node so it can be loaded
        back from the mNode internally. If not given then the pose is cached
        on this object instance only.
        
        :param attr: optional - attr to store the cached pose to
        :param filepath: optional - path to store the pose too
        '''
        import Red9.core.Red9_PoseSaver as r9Pose  # lazy loaded
        self.poseCache=r9Pose.PoseData()
        self.poseCache.metaPose=True
        self.poseCache.poseSave(self.mNode, filepath=filepath, useFilter=True, *args, **kws)  # no path so cache against this pose instance
        if attr:
            if not self.hasAttr(attr):
                self.addAttr(attr, value=self.poseCache.poseDict, hidden=True)
            else:
                setattr(self, attr, self.poseCache.poseDict)
            self.attrSetLocked(attr,True)
        
    def poseCacheLoad(self, nodes=None, attr=None, filepath=None, *args, **kws):
        '''
        load a cached pose back to this mRig. If attr is given then its assumed
        that that attr is a cached poseDict on the mNode. If not given then it
        will load the cached pose from this objects instance, if there is one stored.
        
        :param nodes: if given load only the cached pose to the given nodes
        :param attr: optional - attr in which a pose has been stored internally on the mRig
        :param filepath: optional - posefile to load back
        
        :TODO: add relative flags so that they can pass through this call
        '''
        import Red9.core.Red9_PoseSaver as r9Pose  # lazy loaded
        if attr or filepath:
            self.poseCache=r9Pose.PoseData()
            self.poseCache.metaPose=True
            if attr:
                self.poseCache.poseDict=getattr(self,attr)
        if self.poseCache:
            if not nodes:
                self.poseCache.poseLoad(self.mNode, filepath=filepath, useFilter=True, *args, **kws)
            else:
                self.poseCache.poseLoad(nodes, filepath=filepath, useFilter=False, *args, **kws)
     
    def poseCompare(self, poseFile, supressWarning=False, compareDict='skeletonDict', filterMap=[], ignoreBlocks=[]):
        '''
        Integrated poseCompare, this checks the mRigs current pose against
        a given poseFile. This checks against the 'skeletonDict'
        
        :param poseFile: given .pose file with valid skeletonDict block
        :param supressWarning: if False raise the confirmDialogue
        :param compareDict: what block in the poseFile to compare the data against
        :param ignoreBlocks: used to stop certain blocks in the compare from causing a fail eg : ['missingKeys']
        :return: returns a 'PoseCompare' class object with all the compare data in it
        '''
        import Red9.core.Red9_PoseSaver as r9Pose  # lazy loaded
        self.poseCacheStore()
        compare=r9Pose.PoseCompare(self.poseCache,poseFile, compareDict=compareDict, filterMap=filterMap, ignoreBlocks=ignoreBlocks)
        if not compare.compare():
            info='Selected Pose is different to the rigs current pose\nsee script editor for debug details'
        else:
            info='Poses are the same'
        if not supressWarning:
            cmds.confirmDialog(title='Pose Compare Results',
                               button=['Close'],
                               message=info,
                               defaultButton='Close',
                               cancelButton='Close',
                               dismissString='Close')
        return compare
    
    def nodeVisibility(self, state, skip=[]):
        '''
        simple wrapper to hide all ctrls in the rig via their shapeNodes
        lodVisibility so it doesn't interfer with any display layers etc
        
        :param state: bool to pass to the lodVisibility attr
        :param skip: [] child attrs on the mNode to skip during the process allowing certain controllers not to be effected
        
        '''
        ctrlMap=self.getChildren(walk=True, asMap=True)
        for plug, ctrl in ctrlMap.items():
            #print plug
            if not plug.split('.')[-1] in skip:
                shapes=cmds.listRelatives(ctrl,type='shape',f=True)
                for shape in shapes:
                    cmds.setAttr('%s.lodVisibility' % shape, state)
            else:
                print plug, skip
    
    def hideNodes(self):
        '''
        wrap over the nodeVisibility to set False
        '''
        self.nodeVisibility(state=0,skip=['%s_Main' % self.CTRL_Prefix])
        
    def unHideNodes(self):
        '''
        wrap over the nodeVisibility to set True
        '''
        self.nodeVisibility(state=1,skip=['%s_Main' % self.CTRL_Prefix])
        
    @nodeLockManager
    def saveAttrMap(self, *args):
        '''
        store AttrMap to the metaRig, saving the chBox state of ALL attrs for ALL nodes in the hierarchy
        '''
        import Red9_CoreUtils as r9Core  # lazy loaded
        chn = r9Core.LockChannels()
        chn.saveChannelMap(filepath=None,
                           nodes=getattr(self,'%s_Main' % self.CTRL_Prefix),
                           hierarchy=True,
                           serializeNode=self.mNode)
        
    def loadAttrMap(self, *args):
        '''
        load AttrMap from the metaRig, returning the chBox state of ALL attrs for ALL nodes in the hierarchy
        '''
        import Red9_CoreUtils as r9Core  # lazy loaded
        chn = r9Core.LockChannels()
        chn.loadChannelMap(filepath=None,
                           nodes=getattr(self,'%s_Main' % self.CTRL_Prefix),
                           hierarchy=True,
                           serializeNode=self.mNode)
    
    @nodeLockManager
    def saveZeroPose(self, *args):
        '''
        serialize the r9Pose file to the node itself
        '''
        self.poseCacheStore(attr='zeroPose')

    def loadZeroPose(self, nodes=None, *args):
        '''
        load the zeroPose form the internal dict
        
        :param nodes: optional, load at subSystem level for given nodes
        '''
        self.poseCacheLoad(nodes=nodes, attr='zeroPose')
    
    def saveAnimation(self, filepath, incRoots=True):
        '''
        PRO_PACK : Binding of the animMap format for storing animation data out to file
        '''
        if r9Setup.has_pro_pack():
            from Red9.pro_pack.core.animation import AnimMap
            self.animMap=AnimMap()
            self.animMap.filepath=filepath
            self.animMap.metaPose=True
            self.animMap.settings.incRoots=incRoots
            self.animMap.saveData(self.mNode,storeThumbnail=False)
            
            print self.animMap.filepath
            
    def loadAnimation(self, filepath, offset=0, incRoots=True):
        '''
        PRO_PACK : Binding of the animMap format for loading animation data from
        an r9Anim file
        '''
        if r9Setup.has_pro_pack():
            from Red9.pro_pack.core.animation import AnimMap
            self.animMap=AnimMap()
            self.animMap.filepath=filepath
            self.animMap.metaPose=True
            self.animMap.settings.incRoots=incRoots
            self.animMap.offset=offset
            self.animMap.loadData(self.mNode)

    def getAnimationRange(self, nodes=None, setTimeline=False):
        '''
        return the extend of the animation range for this rig and / or the given controllers
        
        :param nodes: if given only retunr the extent of the animation data from the given nodes
        :param setTimeLine: if True set the playback timeranges also, default=False
        '''
        if not nodes:
            nodes=self.getChildren(walk=True)
        return r9Anim.animRangeFromNodes(nodes,setTimeline=setTimeline)
    
    
class MetaRigSubSystem(MetaRig):
    '''
    SubClass of the MRig, designed to organize Rig sub-systems (ie L_ArmSystem, L_LegSystem..)
    within a complex rig structure. This or MetaRig should have the Controllers wired to it
    '''
    def __init__(self,*args,**kws):
        super(MetaRigSubSystem, self).__init__(*args,**kws)
        self.mClassGrp = 'MetaClass'    # set the Grp removing the MetaRig systemBase Grp code
        self.mSystemRoot=False
        
    def __bindData__(self):
        self.addAttr('systemType', attrType='string')
        self.addAttr('mirrorSide',enumName='Centre:Left:Right',attrType='enum')
 
 
class MetaRigSupport(MetaClass):
    '''
    SubClass of MetaClass, designed to organize support nodes, solvers and other internal
    nodes within a complex rig structure which you may need to ID at a later date.
    Controllers should NOT be wired to this node
    '''
    def __init__(self,*args,**kws):
        super(MetaRigSupport, self).__init__(*args,**kws)
        
    def __bindData__(self):
        '''
        over-load and blank so that the MetaRig bindData doesn't get inherited
        '''
        pass
    
    def addSupportNode(self, node, attr, boundData=None):
        '''
        Add a single MAYA node flagged as a SUPPORT node of managed type
        
        :param node: Maya node to add
        :param attr: Attr name to assign this too
        :param boundData: {} Data to set on the given node as attrs
        '''
        self.connectChild(node,'SUP_%s' % attr)
        if boundData:
            if issubclass(type(boundData),dict):
                for key, value in boundData.iteritems():
                    log.debug('Adding boundData to node : %s:%s' %(key,value))
                    MetaClass(node).addAttr(key, value=value)
                    
                    
class MetaFacialRig(MetaRig):
    '''
    SubClass of the MetaRig, designed to be manage Facial systems in the MetaData
    Dag tree for organizing Facial Controllers and support nodes
    '''
    def __init__(self,*args,**kws):
        super(MetaFacialRig, self).__init__(*args,**kws)
        self.mClassGrp = 'MetaFacialRig'
        self.CTRL_Prefix='FACE'
        
    def __bindData__(self):
        '''
        over-load and blank so that the MetaRig bindData doesn't get inherited
        '''
        pass


class MetaFacialRigSupport(MetaClass):
    '''
    SubClass of the MetaClass, designed to organize support nodes, solvers and other internal
    nodes within a complex rig structure which you may need to ID at a later date.
    Controllers should NOT be wired to this node
    '''
    def __init__(self,*args,**kws):
        super(MetaFacialRigSupport, self).__init__(*args,**kws)
        self.CTRL_Prefix='SUP'
        
    def addSupportNode(self, node, attr, boundData=None):
        '''
        Add a single MAYA node flagged as a SUPPORT node of managed type.
        
        :param node: Maya node to add
        :param attr: Attr name to assign this too
        :param boundData: {} Data to set on the given node as attrs
        '''
        self.connectChild(node,'%s_%s' % (self.CTRL_Prefix,attr))
        if boundData:
            if issubclass(type(boundData),dict):
                for key, value in boundData.iteritems():
                    log.debug('Adding boundData to node : %s:%s' %(key,value))
                    MetaClass(node).addAttr(key, value=value)


class MetaHIKCharacterNode(MetaRig):
    '''
    Casting HIK directly to a metaClass so it's treated as meta by default.
    Why the hell not, it's a complex character node that is default in Maya
    and useful for management in the systems
    '''
    def __init__(self, *args, **kws):
        kws.setdefault('autofill','messageOnly')
        super(MetaHIKCharacterNode, self).__init__(*args,**kws)

    def __getMessageAttr__(self, attr):
        '''
        overloaded so that the main message wires return as single nodes
        '''
        data = super(MetaHIKCharacterNode,self).__getMessageAttr__(attr)
        if data:
            if type(data) == list:
                return data[0]
            return data
    
    def getHIKControlSetNode(self):
        controlNode=cmds.listConnections(self.mNode,type='HIKControlSetNode')
        if controlNode:
            return controlNode[0]
    
class MetaHIKControlSetNode(MetaRig):
    '''
    Casting HIK directly to a metaClass so it's treated as meta by default.
    Why the hell not, it's a complex character node that is default in Maya
    and useful for management in the systems
    '''
    def __init__(self, *args, **kws):
        kws.setdefault('autofill','messageOnly')
        super(MetaHIKControlSetNode, self).__init__(*args,**kws)
        self.CTRL_Main = self.Reference
        
    def __getMessageAttr__(self, attr):
        '''
        overloaded so that the main message wires return as single nodes
        '''
        data = super(MetaHIKControlSetNode,self).__getMessageAttr__(attr)
        if data:
            if type(data) == list:
                return data[0]
            return data
    
    def getHIKCharacterNode(self):
        return cmds.listConnections(self.mNode,type='HIKCharacterNode')[0]
        
    def getChildren(self, walk=False, mAttrs=None, cAttrs=None):
        '''
        Carefully over-loaded for HIK system
        '''
        children=[]
        attrs=cmds.listAttr(self.mNode)
        if attrs:
            for attr in attrs:
                if cmds.getAttr('%s.%s' % (self.mNode,attr),type=True)=='message':
                    effector=cmds.listConnections('%s.%s' % (self.mNode,attr),destination=False,source=True)
                    if effector:
                        for e in effector:
                            if cmds.nodeType(e) in ['hikIKEffector','hikFKJoint']:
                                children.extend(cmds.ls(e,l=True))
        return children
    


# EXPERIMENTAL CALLS ==========================================================

def monitorHUDaddCBAttrs():
    '''
    ChannelBox wrappers for the HUD : 
    Adds selected attrs from the CB to a MetaHUD node for monitoring,
    if HUD node already exists this will simply add more attrs to it
    '''
    import Red9_CoreUtils as r9Core
    node=cmds.ls(sl=True,l=True)[0]
    attrs=cmds.channelBox('mainChannelBox', q=True,selectedMainAttributes=True)
    currentHUDs=getMetaNodes(mTypes=MetaHUDNode,mAttrs='mNodeID=CBMonitorHUD')
    if not currentHUDs:
        metaHUD = MetaHUDNode(name='CBMonitorHUD')
    else:
        metaHUD=currentHUDs[0]
    if attrs:
        for attr in attrs:
            log.info('connecting cbAttr to meta: %s' % attr)
            monitoredAttr='%s_%s' % (r9Core.nodeNameStrip(node), attr)
            metaHUD.addMonitoredAttr(monitoredAttr,
                                     value=cmds.getAttr('%s.%s' % (node,attr)),
                                     refresh=False)
            cmds.connectAttr('%s.%s' % (node,attr), '%s.%s' % (metaHUD.mNode, monitoredAttr))
    metaHUD.refreshHud()
    cmds.select(node)
    
def monitorHUDManagement(func):
    '''
    ChannelBox wrappers for the HUD : kill any current MetaHUD headsUpDisplay blocks
    '''
    metaHUD=None
    currentHUDs=getMetaNodes(mTypes=MetaHUDNode,mAttrs='mNodeID=CBMonitorHUD')
    if currentHUDs:
        metaHUD=currentHUDs[0]
        
    if func=='delete':
        if metaHUD:
            metaHUD.delete()
        else:
            #No metaData node, scene may have been deleted but the HUD
            #may still be up and active
            HUDS=cmds.headsUpDisplay(lh=True)
            for hud in HUDS:
                if 'MetaHUDConnector' in hud:
                    print 'killing HUD : ',hud
                    cmds.headsUpDisplay(hud,remove=True)
    if func=='refreshHeadsUp':
        metaHUD.headsUpOnly=True
        metaHUD.refreshHud()
    if func=='refreshSliders':
        metaHUD.headsUpOnly=False
        metaHUD.refreshHud()
    if func=='kill':
        metaHUD.killHud()
        
                
def monitorHUDremoveCBAttrs():
    '''
    ChannelBox wrappers for the HUD : remove attrs from the MetaHUD
    '''
    import Red9_CoreUtils as r9Core
    currentHUDs=getMetaNodes(mTypes=MetaHUDNode,mAttrs='mNodeID=CBMonitorHUD')
    if currentHUDs:
        metaHUD=currentHUDs[0]
        node=cmds.ls(sl=True,l=True)[0]
        attrs=cmds.channelBox('mainChannelBox', q=True,selectedMainAttributes=True)
        if attrs:
            metaHUD.killHud()
            for attr in attrs:
                monitoredAttr='%s_%s' % (r9Core.nodeNameStrip(node), attr)
                print 'removing attr :',attr,monitoredAttr
                try:
                    metaHUD.removeMonitoredAttr(monitoredAttr)
                except:
                    pass
        metaHUD.refreshHud()
        
def hardKillMetaHUD(*args):
    '''
    If the MetaNodes are left behind in a scene and you can't remove them
    then this is a hard coded kill to remove the hud element. This situation 
    happens if you'd deleted the MetaHUDNode but left the draw on, meaning
    we now have invalid HUD data drawn.
    '''
    huds=getMetaNodes(mInstances=MetaHUDNode)
    if huds:
        for hud in huds:
            try:
                hud.killHud()
            except:
                log.debug('failed to remove HUD metanode')
    HUDS=cmds.headsUpDisplay(lh=True)
    if HUDS:
        for hud in HUDS:
            if 'MetaHUDConnector' in hud:
                cmds.headsUpDisplay(hud,remove=True)
        
# EXPERIMENTAL CALLS ==========================================================
     
     
class MetaHUDNode(MetaClass):
    '''
    SubClass of the MetaClass, designed as a simple interface
    for HUD management in Maya. Any monitored attrs added to the MetaNode
    will show in the HUD when drawn.
    
    The idea is that we have a single MetaNode with attrs that are monitored
    and managed for HUD display. To get an attr onto the HUD all you need to do
    is add it using addMonitoredAttr(), then drawHUD(). All I do is connect the HUD
    attr to the attr that you want to monitor, it just sits as a new wired node.
    
    :TODO: Look if we can link the Section and Block attrs to the refresh func 
        via an attrChange callback
    '''
    def __init__(self,*args,**kws):
        super(MetaHUDNode, self).__init__(*args,**kws)
        
        if self.cached:
            log.debug('CACHE : Aborting __init__ on pre-cached %s Object' % self.__class__)
            return
        
        self.hudGroupActive=False
        self.eventTriggers=cmds.headsUpDisplay(le=True)
        self._blocksize='small'
        self.headsUpOnly=True
        
        self.addAttr('monitorAttrCache', value='[]', attrType='string')  # cache the HUD names so this runs between sessions
        self.monitorAttrs=self.monitorAttrCache
        self.addAttr('section', 1)
        self.addAttr('block', 1)
        self.addAttr('allowExpansion', True)  # if a section can't contain all elements then expand to the section below
        self.addAttr('eventTrigger', attrType='enum', value=0,enumName=':'.join(['attachToRefresh','timeChanged']))

        HUDS=cmds.headsUpDisplay(lh=True)
        for hud in HUDS:
            if 'MetaHUDConnector' in hud:
                self.hudGroupActive=True
    
    def __compute__(self, attr, *args):
        '''
        The monitored attrs passs through this compute block before being draw. This
        allows us to modify the data being draw when over-loading this class.
        '''
        return getattr(self, attr)
                          
    def addMonitoredAttr(self, attr, value=None, attrType=None, refresh=True):
        '''
        wrapper that not only adds an attr to the metaNode, but also adds it
        to the internal list of attributes that are monitored and added
        to the HUD when drawn. 
        
        :param attr: attr to be added to the node for monitoring in the HUD
        :param value: Initial value of the attr so the node can figure out what type of attr it is
        :param attrType: specifiy the attr type directly
        :param refresh: whether to refresh the HUD after adding a new attr
        
        .. note::
            this ties in with the default addAttr call hence the args are very similar in function
        '''
        if not attr in self.monitorAttrs:
            self.addAttr(attr, value=value, attrType=attrType)
            self.monitorAttrs.append(attr)
            #serialize back to the node
            self.monitorAttrCache=self.monitorAttrs
            if self.hudGroupActive==True and refresh:
                try:
                    self.refreshHud()
                except:
                    log.debug('addMonitorAttr failed')
        else:
            log.info('Hud attr already exists on metaHud Node')
    
    def removeMonitoredAttr(self,attr):
        '''
        Remove an attr from the MetaNode and refresh the HUD to reflect the removal
        
        :param attr: attr to be removed from monitoring
        '''
        self.__delattr__(attr)
        
    #def getEventTrigger(self,*args):
    #    return self.eventTriggers[self.eventTrigger]
    
    def getHudDisplays(self):
        '''
        each line in the HUD is actually a separate HUD in itself so we need
        to carefully manage this list
        '''
        return ['MetaHUDConnector%s' % attr for attr in self.monitorAttrs]
            
    def drawHUD(self):
        '''
        Push the monitored attrs up to the Maya HUD in the viewport
        '''
        #Attributes:
        #        - Section 1, block 0, represents the top second slot of the view.
        #        - Set the _blocksize to "medium", instead of the default "small"
        #        - Assigned the HUD the label: "Position"
        #        - Defined the label font size to be large
        #        - Assigned the HUD a command to run on a SelectionChanged trigger
        #        - Attached the attributeChange node change to the SelectionChanged trigger
        #          to allow the update of the data on attribute changes.
            
        for i,attr in enumerate(self.monitorAttrs):
            section = self.section
            block=self.block+i
            if self.allowExpansion and i>17:
                section = self.section+5
                block = block-17
                i=0
                
            metaHudItem='MetaHUDConnector%s' % attr
            
            if self.headsUpOnly:
                if self.eventTrigger==1:  # timeChanged
                    cmds.headsUpDisplay(metaHudItem,
                                        section=section,
                                        block=block,
                                        blockSize=self._blocksize,
                                        label=attr,
                                        labelFontSize=self._blocksize,
                                        allowOverlap=True,
                                        #command=partial(getattr,self,attr),
                                        command=partial(self.__compute__,attr),
                                        event='timeChanged')
                else:
                    cmds.headsUpDisplay(metaHudItem,
                                        section=section,
                                        block=block,
                                        blockSize=self._blocksize,
                                        label=attr,
                                        labelFontSize=self._blocksize,
                                        allowOverlap=True,
                                        attachToRefresh=True,
                                        command=partial(self.__compute__,attr))
                                        #command=partial(getattr,self,attr))
            else:
                print 'node : ', self.mNode,' attrs : ', attr
                connectedData=cmds.listConnections('%s.%s' % (self.mNode,attr),
                                                   connections=True,
                                                   skipConversionNodes=True,
                                                   plugs=True)[-1].split('.')
                cmds.hudSliderButton(metaHudItem,
                                     section=section,
                                     block=block,
                                     vis=True,
                                     sliderLabel=attr,
                                     sliderDragCommand=partial(self.setSlidertoAttr, metaHudItem, '%s.%s' % (connectedData[0],connectedData[1])),
                                     value=0, type='float',
                                     sliderLabelWidth=150,
                                     valueWidth=60,
                                     sliderLength=150,
                                     bl='Reset',
                                     bw=60, bsh='rectangle',
                                     buttonReleaseCommand=partial(self.resetSlider, metaHudItem, '%s.%s' % (connectedData[0],connectedData[1])))
                try:
                    attrMin=cmds.attributeQuery(connectedData[1], node=connectedData[0], min=True)
                    if attrMin:
                        cmds.hudSliderButton(metaHudItem, e=True, min=attrMin[0])
                except:
                    cmds.hudSliderButton(metaHudItem, e=True, min=-1000)
                try:
                    attrMax=cmds.attributeQuery(connectedData[1], node=connectedData[0], max=True)
                    if attrMax:
                        cmds.hudSliderButton(metaHudItem, e=True, max=attrMax[0])
                except:
                    cmds.hudSliderButton(metaHudItem, e=True, max=1000)
                        
        self.hudGroupActive=True
   
    def getConnectedAttr(self, attr):
        return cmds.listConnections('%s.%s' % (self.mNode,attr),c=True,p=True)[-1]
    
    def getConnectedNode(self, attr):
        return cmds.listConnections('%s.%s' % (self.mNode,attr))[0]
       
    def setSlidertoAttr(self, slider, attr):
        cmds.setAttr(attr, cmds.hudSliderButton(slider, query=True, v=True))
        
    def resetSlider(self, slider, attr):
        '''
        If the HUD is made up of sliders this resets them
        
        :param slider: slider to reset in the HUD
        :param attr: attr to reset on the mNode
        '''
        value=0
        try:
            value=cmds.addAttr(q=True,dv=True)
        except:
            pass
        cmds.setAttr(attr, value)
        cmds.hudSliderButton(slider, e=True, v=value)
                                       
    def showHud(self,value):
        '''
        manage the visibility state of the HUD
        
        :param value: show or hide the HUD
        '''
        for hud in self.getHudDisplays():
            cmds.headsUpDisplay(hud, edit=True, visible=value)
             
    def killHud(self):
        '''
        kill the HUD display altogether
        '''
        for hud in self.getHudDisplays():
            if cmds.headsUpDisplay(hud,exists=True):
                cmds.headsUpDisplay(hud,remove=True)
        self.hudGroupActive=False
    
    def refreshHud(self):
        '''
        Refresh the HUD by killing it and re-drawing it from scratch
        '''
        if self.hudGroupActive==True:
            self.killHud()
        self.drawHUD()
            
    def delete(self):
        '''
        full cleanup, remove the metaNode and all HUDs in the process
        '''
        self.killHud()
        super(MetaHUDNode, self).delete()

    def __delattr__(self, attr):
        '''
        delete an attr on the metaNode and remove it from the monitored list
        '''
        wasActive=False
        if self.hudGroupActive==True:
            self.killHud()
            wasActive=True
        self.monitorAttrs.remove(attr)
        #serialize back to the node
        self.monitorAttrCache=self.monitorAttrs
        super(MetaHUDNode, self).__delattr__(attr)
        if wasActive==True:
            self.drawHUD()
            

class MetaTimeCodeHUD(MetaHUDNode):
    '''
    Generate's a HUD node connected to the main timecode attrs,
    allows us to show the actual internal timecode attrs as their 
    original SMPTE time's
    
    Crucial things to be aware of: 
    
    We construct timecode from 3 attrs on the given node: 
    timecode_ref        : the original timecode converted to milliseconds 
    timecode_count      : a linear curve that increments every frame based on the samplerate 
    timecode_samplerate : samplerate that the linear counter was generated against 
    
    SMPTE timecode is then reconstructed like so: 
    
    >>> r9Audio.milliseconds_to_Timecode(ref + ((count / samplerate) * 1000)) 
    >>> 
    >>> tcHUD=cFacialMeta.MetaTimeCodeHUD() 
    >>> tcHUD.addMonitoredTimecodeNode(cmds.ls(sl=True)[0]) 
    >>> tcHUD.drawHUD() 
    
    '''
    def __init__(self, *args, **kws):
        super(MetaTimeCodeHUD, self).__init__(*args, **kws)
        
        if self.cached:
            log.debug('CACHE : Aborting __init__ on pre-cached %s Object' % self.__class__)
            return
        
        import Red9.core.Red9_Audio as r9Audio
        self.func=r9Audio.milliseconds_to_Timecode
        tc=r9Audio.Timecode()
        self.tc_count = tc.count
        self.tc_samplerate = tc.samplerate
        self.tc_ref = tc.ref
        self.attrCache={}
        

    def addMonitoredTimecodeNode(self, nodes, valid=True):
        '''
        add a node with the TimeCode attrs on it to monitor
        '''
        if not type(nodes)==list:
            nodes=[nodes]

        for node in nodes:
            node=MetaClass(node)
            if not node.hasAttr(self.tc_ref):
                continue
            if node.nameSpace():
                monitoredAttr='%s_%s_%s' % (r9Core.nodeNameStrip(node.nameSpace()[0]),
                                        r9Core.nodeNameStrip(node.mNode),
                                        'Timecode')
            else:
                monitoredAttr='%s_%s' % (r9Core.nodeNameStrip(node.mNode),
                                        'Timecode')
            if not node.timecode_ref >1000 and valid:
                log.warning('%s : Skipping as timecode is invalid' % monitoredAttr)
                continue
            
            self.addMonitoredAttr(monitoredAttr, value=getattr(node, self.tc_count), refresh=False)
            cmds.connectAttr('%s.%s' % (node.mNode, self.tc_count), '%s.%s' % (self.mNode, monitoredAttr))
            
            #add the data that we can to the cache for speed
            self.attrCache[monitoredAttr]={'mNode':node, 'ref':getattr(node, self.tc_ref), 'samplerate':getattr(node, self.tc_samplerate)}
            
    def __compute__(self, attr, *args):
        '''
        Data computed on the refresh - convert all the attrs to meaningful timecode
        '''
        cacheData=self.attrCache[attr]
        try:
            return self.func(cacheData['ref'] + ((float(getattr(self, attr)) / cacheData['samplerate']) * 1000))
        except:
            return 'InvalidDataSet'
  
    def removeMonitoredAttr(self,attr):
        super(MetaTimeCodeHUD,self).removeMonitoredAttr(attr)
        self.attrCache.pop(attr)
        
    @r9General.Timer
    def connectTimecodeSystems(self, metaRigs=True):
        if metaRigs:
            rigs=getMetaNodes(mInstances=MetaRig)
            flt=r9Core.FilterNode([rig for rig in rigs if rig.isValid()])
            flt.settings.metaRig=True
        else:
            flt=r9Core.FilterNode()
            flt.settings.nodeTypes='transform'
        flt.settings.searchAttrs = self.tc_ref
        nodes=flt.ProcessFilter()
        if nodes:
            self.addMonitoredTimecodeNode(nodes)
        else:
            raise StandardError('No nodes found through the filters that contain timecode attrs')

            
'''
if we reload r9Meta on it's own then the registry used in construction of
the nodes will fall out of sync and invalidate the systems. This is a catch
to that.
'''
#registerMClassInheritanceMapping()

def metaData_sceneCleanups(*args):
    '''
    Registered on SceneOpen and SceneNew callbacks so that the MetaData Cache is cleared and 
    any registered HUD is killed off
    '''
    hardKillMetaHUD()
    resetCacheOnSceneNew()
    

#Setup the callbacks to clear the cache when required
if not RED9_META_CALLBACKS['Open']:
    RED9_META_CALLBACKS['Open'].append(OpenMaya.MSceneMessage.addCallback(OpenMaya.MSceneMessage.kBeforeOpen, metaData_sceneCleanups))
if not RED9_META_CALLBACKS['New']:
    RED9_META_CALLBACKS['New'].append(OpenMaya.MSceneMessage.addCallback(OpenMaya.MSceneMessage.kBeforeNew, metaData_sceneCleanups))

# if r9Setup.mayaVersion()<=2015:
#     #dulplicate cache callbacks so the UUIDs are managed correctly
#     if not RED9_META_CALLBACKS['DuplicatePre']:
#         RED9_META_CALLBACKS['DuplicatePre'].append(OpenMaya.MModelMessage.addBeforeDuplicateCallback(__preDuplicateCache))
#     if not RED9_META_CALLBACKS['DuplicatePost']:
#         RED9_META_CALLBACKS['DuplicatePost'].append(OpenMaya.MModelMessage.addAfterDuplicateCallback(__poseDuplicateCache))


