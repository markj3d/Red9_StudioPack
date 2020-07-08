'''

..
    Red9 Studio Pack: Maya Pipeline Solutions
    Author: Mark Jackson
    email: rednineinfo@gmail.com

    Red9 blog : http://red9-consultancy.blogspot.co.uk/
    MarkJ blog: http://markj3d.blogspot.co.uk


    This is the Core of the MetaNode implementation of the systems.

    .. note::
        if you're inheriting from 'MetaClass' in your own class you
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

from __future__ import print_function

import maya.cmds as cmds
import maya.mel as mel
import maya.OpenMaya as OpenMaya
from functools import partial
from functools import wraps
import sys
import os
import uuid
import types
import inspect
import traceback


import Red9.startup.setup as r9Setup
import Red9_General as r9General
import Red9_CoreUtils as r9Core
import Red9_AnimationUtils as r9Anim

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

def logging_is_debug():
    if log.level == 10:
        return True

# Language map is used for all UI's as a text mapping for languages
LANGUAGE_MAP = r9Setup.LANGUAGE_MAP


# =============================================
# NOTE: we can't import anything else here that imports this
# Module as it screw the Class Registry and we get Cyclic imports
# hence the r9Anim is LazyLoaded where needed
# import Red9_AnimationUtils as r9Anim
# =============================================

try:
    import json as json
except:
    # Meta Fails under Maya2009 because of Python2.5 issues
    log.warning('json is not supported in Python2.5')
    # import Red9.packages.simplejson as json


global RED9_META_NODECACHE
RED9_META_NODECACHE = {}

global __RED9_META_NODESTORE__
__RED9_META_NODESTORE__ = []

global RED9_META_REGISTERY
RED9_META_REGISTERY = {}

global RED9_META_INHERITANCE_MAP
RED9_META_INHERITANCE_MAP = {}

if 'RED9_META_CALLBACKS' in globals():
    log.debug('RED9_META_CALLBACKS already setup')
else:
    log.debug('initializing the RED9_META_CALLBACKS')
    global RED9_META_CALLBACKS
    RED9_META_CALLBACKS = {}
    RED9_META_CALLBACKS['Open'] = []
    RED9_META_CALLBACKS['New'] = []
    # RED9_META_CALLBACKS['DuplicatePre'] = []
    # RED9_META_CALLBACKS['DuplicatePost'] = []


'''
CRUCIAL - REGISTER INHERITED CLASSES! ==============================================
Register available MetaClass's to a global so that other modules could externally
extend the functionality and use the base MetaClass. Note we're building this up
from only those active Python classes who inherit from MetaClass
global RED9_META_REGISTERY
====================================================================================
'''


# ----------------------------------------------------------------------------
# --- FactoryClass registry --- --------------------------
# ----------------------------------------------------------------------------

def registerMClassInheritanceMapping():
    '''
    build up the master global registry of all available subclasses from r9Meta.MetaClass,
    this build up 2 global dicts:
    RED9_META_REGISTERY : {'className': class pointer}
    RED9_META_INHERITANCE_MAP : {'className': {'full': [list of inherited class pointers]},
                                              {'short': [list of inherited class.__names__]}}
    '''
    global RED9_META_REGISTERY
    RED9_META_REGISTERY = {}
    global RED9_META_INHERITANCE_MAP
    RED9_META_INHERITANCE_MAP = {}

    RED9_META_REGISTERY['MetaClass'] = MetaClass
    RED9_META_INHERITANCE_MAP['MetaClass'] = {}
    RED9_META_INHERITANCE_MAP['MetaClass']['full'] = [MetaClass]
    RED9_META_INHERITANCE_MAP['MetaClass']['short'] = [MetaClass.__name__]

    for mclass in r9General.itersubclasses(MetaClass):
        log.debug('registering : %s' % mclass)
        RED9_META_REGISTERY[mclass.__name__] = mclass
        RED9_META_INHERITANCE_MAP[mclass.__name__] = {}
        RED9_META_INHERITANCE_MAP[mclass.__name__]['full'] = list(inspect.getmro(mclass))
        RED9_META_INHERITANCE_MAP[mclass.__name__]['short'] = [n.__name__ for n in inspect.getmro(mclass)]

def printSubClassRegistry():
    for m in RED9_META_REGISTERY:
        print(m)

def getMClassMetaRegistry():
    '''
    Generic getWrapper to return the Registry from the global
    '''
    return RED9_META_REGISTERY

def create_mNode_from_gatherInfo(data):
    '''
    a simple wrapper to re-construct the correct mNode from a dict() built by
    the MetaClass.gatherInfo_mNode() call. This is primarily aimed at the new
    load_connection_datamap call in ProPack to rebuild entire networks from a
    map file without having to write complex macros to rebuild a system and
    all it's wiring.
    '''
    if data['mClass'] in RED9_META_REGISTERY:
        mNode = RED9_META_REGISTERY[data['mClass']](node=None,
                                            name=data['mNode'],
                                            nodeType=data['nodeType'],
                                            autofill='False')
        mNode.mClassGrp = data['mClassGrp']
        mNode.mSystemRoot = data['mSystemRoot']

        # custom attrs handled by the base class as defaults
        if 'systemType' in data and mNode.hasAttr('systemType'):
            mNode.systemType = data['systemType']
        if 'mirrorSide' in data and mNode.hasAttr('mirrorSide'):
            mNode.mirrorSide = data['mirrorSide']
        return mNode

def getMClassInstances(mInstances):
    '''
    return a list of Registered metaClasses that are subclassed from the given
    classes. This is so in code/UI's you can group metaClasses by their
    inheritance . . . ie, give me all export metaClasses that are registered

    :param mInstanes: given metaClass to test inheritance - cls or [cls]
    '''
    subClasses = []
    if not type(mInstances) == list:
        mInstances = [mInstances]
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
    if not type(mTypes) == list:
        mTypes = [mTypes]
    keys = []
    for cls in mTypes:
        try:
            keys.append(cls.__name__)
        except:
            keys.append(cls)
    # remove the key if it's not registered!
    return [key for key in keys if key in RED9_META_REGISTERY.keys()] or []

def getMClassDataFromNode(node, checkInstance=True):
    '''
    from the node get the class to instantiate, this gives us a level of
    flexibility over mClass attr rather than pure hard coding as it was previously

    :param node: node to retrieve the mClass binding from
    :param checkInstance: bool, specify whether to test the given node as a per existing instance
            this check is purely for speed internally so we don't check the same thing over and over again
    '''
    if checkInstance:
        # node is ALREADY MetaClass instance?
        if issubclass(type(node), MetaClass):
            log.debug('getMClassFromNode was given an already instantiated MNode')
            return node.mClass
    try:
        mClass = cmds.getAttr('%s.%s' % (node, 'mClass'))
        if mClass in RED9_META_REGISTERY:
            return mClass
        else:
            mClass = cmds.getAttr('%s.%s' % (node, 'mClassGrp'))
            if mClass in RED9_META_REGISTERY:
                return mClass
    except:
        # Node has no mClass attr BUT in certain circumstances we can register
        # default node Types to Meta (HIK for example) so we need to check
        _nodetype = cmds.nodeType(node)
        if 'Meta%s' % _nodetype in RED9_META_REGISTERY.keys():
            return 'Meta%s' % _nodetype
        else:
            for key in RED9_META_REGISTERY.keys():
                if key.lower() == _nodetype.lower():
                    return key

# def getMClassDataFromNode(node):
#    '''
#    from the node get the class to instantiate, this gives us a level of
#    flexibility over mClass attr rather than pure hard coding as it was previously
#    '''
#    try:
#        if cmds.attributeQuery('mClass', exists=True, node=node):
#            mClass=cmds.getAttr('%s.%s' % (node,'mClass'))
#            if mClass in RED9_META_REGISTERY:
#                return mClass
#            elif cmds.attributeQuery('mClassGrp', exists=True, node=node):
#                mClass=cmds.getAttr('%s.%s' % (node,'mClassGrp'))
#                if mClass in RED9_META_REGISTERY:
#                    return mClass
#        elif 'Meta%s' % cmds.nodeType(node) in RED9_META_REGISTERY.keys():
#            return 'Meta%s' % cmds.nodeType(node)
#    except:
#        #node is ALREADY MetaClass instance?
#        if issubclass(type(node), MetaClass):
#            log.debug('getMClassFromNode was given an already instanciated MNode')
#            return node.mClass
#        else:
#            raise StandardError('getMClassFromNode failed for node : %s' % node)


# ----------------------------------------------------------------------------
# --- NodeType registry --- ----
# ----------------------------------------------------------------------------

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
    baseTypes = ['network', 'objectSet', 'HIKCharacterNode', 'HIKControlSetNode', 'imagePlane']

    global RED9_META_NODETYPE_REGISTERY
    if nodeTypes and RED9_META_NODETYPE_REGISTERY:
        baseTypes = RED9_META_NODETYPE_REGISTERY
    RED9_META_NODETYPE_REGISTERY = []

    if nodeTypes:
        if not type(nodeTypes) == list:
            nodeTypes = [nodeTypes]
        [baseTypes.append(n) for n in nodeTypes if n not in baseTypes]
        # baseTypes.extend(nodeTypes)
    try:
        MayaRegisteredNodes = cmds.allNodeTypes()

        for nType in baseTypes:
            if nType not in RED9_META_NODETYPE_REGISTERY and nType in MayaRegisteredNodes:
                log.debug('nodeType : "%s" : added to NODETYPE_REGISTRY' % nType)
                RED9_META_NODETYPE_REGISTERY.append(nType)
            else:
                log.debug('nType: "%s" is an invalid Maya NodeType' % nType)
    except:
        log.warning('registerMClassNodeMapping failure - seems to have issues in Maya2009')
        # raise StandardError('registerMClassNodeMapping failure - seems to have issues in Maya2009')

def printMetaTypeRegistry():
    for t in RED9_META_NODETYPE_REGISTERY:
        print(t)

def getMClassNodeTypes():
    '''
    Generic getWrapper for all nodeTypes registered in the Meta_NodeType global
    '''
    return RED9_META_NODETYPE_REGISTERY

def resetMClassNodeTypes():
    registerMClassNodeMapping(nodeTypes=None)


# ----------------------------------------------------------------------------
# --- NodeCache management --- ---------------------------
# ----------------------------------------------------------------------------

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
    version = r9Setup.mayaVersion()

    # Maya 2016 onwards UUID management  ---------
    if version >= 2016:
        UUID = cmds.ls(mNode.mNode, uuid=True)[0]
        if UUID in RED9_META_NODECACHE.keys():
            # log.debug('CACHE : UUID is already registered in cache')
            if not mNode == RED9_META_NODECACHE[UUID]:
                log.debug('CACHE : %s : UUID is registered to a different node : modifying UUID: %s' % (UUID, mNode.mNode))
                UUID = mNode.setUUID()

    # Maya 2015 and below only -------------------
    elif mNode.hasAttr('UUID'):
        try:
            UUID = mNode.UUID
            if not UUID:
                # log.debug('CACHE : generating fresh UUID')
                UUID = mNode.setUUID()
            elif UUID in RED9_META_NODECACHE.keys():
                # log.debug('CACHE : UUID is already registered in cache')
                if not mNode == RED9_META_NODECACHE[UUID]:
                    log.debug('CACHE : %s : UUID is registered to a different node : modifying UUID: %s' % (UUID, mNode.mNode))
                    UUID = mNode.setUUID()
        except StandardError, err:
            log.debug('CACHE : Failed to set UUID for mNode : %s' % mNode.mNode)

    else:
        # log.debug('CACHE : UUID attr not bound to this node, must be an older system')
        if RED9_META_NODECACHE or mNode.mNode not in RED9_META_NODECACHE.keys():
            # log.debug('CACHE : Adding to MetaNode Cache : %s' % mNode.mNode)
            RED9_META_NODECACHE[mNode.mNode] = mNode
            return

    if RED9_META_NODECACHE or UUID not in RED9_META_NODECACHE.keys():
        # log.debug('CACHE : Adding to MetaNode UUID Cache : %s > %s' % (mNode.mNode, UUID))
        RED9_META_NODECACHE[UUID] = mNode

    mNode._lastUUID = UUID

#    if mNode.hasAttr('UUID') or version>=2016:
#        try:
#            if version<2016:
#                UUID=mNode.UUID
#                if not UUID:
#                    log.debug('CACHE : generating fresh UUID')
#                    UUID=mNode.setUUID()
#                elif UUID in RED9_META_NODECACHE.keys():
#                    log.debug('CACHE : UUID is already registered in cache')
#                    if not mNode.mNode == RED9_META_NODECACHE[UUID]:
#                        log.debug('CACHE : %s : UUID is registered to a different node : modifying UUID: %s' % (UUID, mNode.mNode))
#                        UUID=mNode.setUUID()
#            else:
#                UUID=cmds.ls(mNode.mNode, uuid=True)[0]
#            if RED9_META_NODECACHE or not UUID in RED9_META_NODECACHE.keys():
#                log.debug('CACHE : Adding to MetaNode UUID Cache : %s > %s' % (mNode.mNode, UUID))
#                RED9_META_NODECACHE[UUID]=mNode
#        except StandardError, err:
#            #print err
#            log.debug('CACHE : Failed to set UUID for mNode : %s' % mNode.mNode)
#    else:
#        log.debug('CACHE : UUID attr not bound to this node, must be an older system')
#        if RED9_META_NODECACHE or not mNode.mNode in RED9_META_NODECACHE.keys():
#            log.debug('CACHE : Adding to MetaNode Cache : %s' % mNode.mNode)
#            RED9_META_NODECACHE[mNode.mNode]=mNode


def getMetaFromCache(mNode):
    '''
    Pull the given mNode from the RED9_META_NODECACHE if it's
    already be instantiated.

    :param mNode: str(name) of node from DAG
    '''
    try:
        if r9Setup.mayaVersion() < 2016:
            UUID = cmds.getAttr('%s.UUID' % mNode)  # if this fails we bail to the mNode name block
        else:
            UUID = cmds.ls(mNode, uuid=True)[0]

        if UUID in RED9_META_NODECACHE.keys():
            try:
                if RED9_META_NODECACHE[UUID].isValidMObject():
                    if not RED9_META_NODECACHE[UUID]._MObject == getMObject(mNode):
                        log.debug('CACHE ABORTED : %s : UUID is already registered but to a different node : %s' % (UUID, mNode))
                        mNode.setUUID()
                        return
                    # log.debug('CACHE : %s Returning mNode from UUID cache! = %s' % (mNode, UUID))
                    return RED9_META_NODECACHE[UUID]
                else:
                    # log.debug('%s being Removed from the cache due to invalid MObject' % mNode)
                    cleanCache()
            except:
                log.debug('CACHE : inspection failure')
    except:
        if mNode in RED9_META_NODECACHE.keys():
            try:
                if RED9_META_NODECACHE[mNode].isValidMObject():
                    if not RED9_META_NODECACHE[mNode]._MObject == getMObject(mNode):
                        # log.debug('CACHE : %s : ID is already registered but MObjects are different, node may have been renamed' % mNode)
                        return
                    # print 'namebased returned from cache ', mNode
                    # log.debug('CACHE : %s Returning mNode from nameBased cache!' % mNode)
                    return RED9_META_NODECACHE[mNode]
                else:
                    # log.debug('%s being Removed from the cache due to invalid MObject' % mNode)
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
                uuid = node.setUUID()
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
    for k, v in RED9_META_NODECACHE.items():
        print('%s : %s : %s' % (k, r9Core.nodeNameStrip(v.mNode), v))

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
    '''
    remove instanciated mNodes from the cache
    '''
    for k, v in RED9_META_NODECACHE.items():
        if not type(mNodes) == list:
            mNodes = [mNodes]
        if v and v in mNodes:
            try:
                RED9_META_NODECACHE.pop(k)
                if logging_is_debug():
                    log.debug('CACHE : %s being Removed from the cache >> %s' % (r9Core.nodeNameStrip(k),
                                                                             r9Core.nodeNameStrip(v.mNode)))
            except:
                log.debug('CACHE : Failed to remove %s from cache')

def resetCache(*args):
    '''
    reset the global cache, called after SceneOpen or NewScene
    '''
    global RED9_META_NODECACHE
    RED9_META_NODECACHE = {}

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
    __RED9_META_NODESTORE__ = getMetaNodes(dataType='dag')
    # print 'pre-callback : nodelist :', __RED9_META_NODESTORE__

def __poseDuplicateCache(*args):
    '''
    DEPRICATED : POST-DUPLICATE : if we find the duplicate node in the cache re-generate it's UUID
    '''
    global __RED9_META_NODESTORE__

    # no metaNode in the cache so pull out fast
    if not __RED9_META_NODESTORE__:
        return

    newNodes = [node for node in getMetaNodes(dataType='dag') if node not in __RED9_META_NODESTORE__]
    for node in newNodes:
        # note we set this via cmds so that the node isn't instantiated until the UUID is modified
        # if cmds.attributeQuery('UUID', node=node, exists=True):
        if cmds.objExists('%s.%s' % (node, 'UUID')):
            cmds.setAttr('%s.UUID' % node, generateUUID(), type='string')
    # print 'post-callback : nodelist :', newNodes

def getMObject(node):
    '''
    base wrapper to get the MObject from node
    '''
    mobj = OpenMaya.MObject()
    selList = OpenMaya.MSelectionList()
    selList.add(node)
    selList.getDependNode(0, mobj)
    return mobj


# ----------------------------------------------------------------------------
# --- Decorators --- ------------------------------------------------------
# ----------------------------------------------------------------------------

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
        res = None
        err = None
        locked = False
        try:
            locked = False
            mNode = args[0]  # args[0] is self
            # log.debug('nodeLockManager > func : %s : metaNode / self: %s' % (func.__name__,mNode.mNode))
            if mNode.mNode and mNode._lockState:
                locked = True
                # log.debug('nodeLockManager > func : %s : node being unlocked' % func.__name__)
                cmds.lockNode(mNode.mNode, lock=False)
            res = func(*args, **kws)
        except StandardError, error:
            err = error
        finally:
            if locked:
                # log.debug('nodeLockManager > func : %s : node being relocked' % func.__name__)
                cmds.lockNode(mNode.mNode, lock=True)
            if err:
                traceback = sys.exc_info()[2]  # get the full traceback
                raise StandardError(StandardError(err), traceback)
            return res
    return wrapper

def pymelHandler(func):
    def wrapper(*args, **kws):
        res = None
        err = None
        try:
            # inputNodes=args[0]
            # if 'pymel' in str(type(inputNodes)):
            #    print 'pymel Node passed in!!!!!!!!!!'
            #    print 'type : ', args
            #    #args[0]=str(inputNodes)
            res = func(*args, **kws)
        except StandardError, error:
            err = error
        finally:
            if err:
                traceback = sys.exc_info()[2]  # get the full traceback
                raise StandardError(StandardError(err), traceback)
            return res
    return wrapper


# ----------------------------------------------------------------------------
# --- MetaData Utilities --- -------------------
# ----------------------------------------------------------------------------

def attributeDataType(val):
    '''
    Validate the attribute type for all the cmds handling
    '''
    if issubclass(type(val), str):
        # log.debug('Val : %s : is a string' % val)
        return 'string'
    if issubclass(type(val), unicode):
        # log.debug('Val : %s : is a unicode' % val)
        return 'unicode'
    if issubclass(type(val), bool):
        # log.debug('Val : %s : is a bool')
        return 'bool'
    if issubclass(type(val), int):
        # log.debug('Val : %s : is a int')
        return 'int'
    if issubclass(type(val), float):
        # log.debug('Val : %s : is a float')
        return 'float'
    if issubclass(type(val), dict):
        # log.debug('Val : %s : is a dict')
        return 'complex'
    if issubclass(type(val), list):
        # log.debug('Val : %s : is a list')
        return 'complex'
    if issubclass(type(val), tuple):
        # log.debug('Val : %s : is a tuple')
        return 'complex'

# @pymelHandler
# @r9General.Timer
def isMetaNode(node, mTypes=[], checkInstance=True, returnMClass=False):
    '''
    Simple bool, Maya Node is or isn't an mNode

    :param node: Maya node to test
    :param mTypes: only match given MetaClass's - str or class accepted
    :param checkInstance: bool, used only internally for optimisation
    :param returnMClass: if True return the str(mClass) that this node is bound too

    .. note::

        this does not instantiate the mClass to query it like the
        isMetaNodeInherited which has to figure the subclass mapping
    '''
    mClassInstance = False
    if not node:
        return False

    if checkInstance:
        if issubclass(type(node), MetaClass):
            node = node.mNode
            mClassInstance = True

    mClass = getMClassDataFromNode(node, checkInstance=checkInstance)
    if mClass:
        if mClass in RED9_META_REGISTERY:
            if mTypes:
                if mClass in mTypesToRegistryKey(mTypes):
                    if returnMClass:
                        return mClass
                    return True
                else:
                    return False
            else:
                if returnMClass:
                    return mClass
                return True
        else:
            log.debug('isMetaNode>>InValid MetaClass attr : %s' % mClass)
            return False
    else:
        if mClassInstance:
            log.debug('isMetaNode = True : node is a Wrapped StandardMaya Node MClass instance')
            if returnMClass:
                return mClassInstance.mClass
            return True
        else:
            return False

# def isMetaNodeInherited(node, mInstances=[]):
#     '''
#     unlike isMetaNode which checks the node against a particular MetaClass,
#     this expands the check to see if the node is inherited from or a subclass of
#     a given Meta base class, ie, part of a system
#     TODO : we COULD return the instantiated metaClass object here rather than just a bool??
#     '''
#     if not node:
#         return False
#     if issubclass(type(node), MetaClass):
#         node = node.mNode
#     mClass = getMClassDataFromNode(node)
#     if mClass and mClass in RED9_META_REGISTERY:
#         for inst in mTypesToRegistryKey(mInstances):
#             # log.debug('testing class inheritance: %s > %s' % (inst, mClass))
#             if issubclass(RED9_META_REGISTERY[mClass], RED9_META_REGISTERY[inst]):
#                 log.debug('MetaNode %s is of subclass >> %s' % (mClass, inst))
#                 return True
#     return False

def isMetaNodeInherited(node, mInstances=[], mode='short'):
    '''
    unlike isMetaNode which checks the node against a particular MetaClass,
    this expands the check to see if the node is inherited from or a subclass of
    a given Meta base class, ie, part of a system

    :param node: node we're wanting to test
    :param mInstances: list of instances we want to validate against
    :param mode: 'short' or 'full' how we determine the inheritance, either full class
        inheritance OR from the RED9_META_INHERITANCE_MAP[key] (string)

    .. note::
        this has been modified to bypass the issue of the same subclass being imported
        in a different space in the inheritance and breaking the standard issubclass()
        testing. This was an issue as r9Pro.metadata_pro for clients is imported via the .r9Co
        handlers and can break things.
        We now us a new global registry r9Meta.RED9_META_INHERITANCE_MAP which stores
        each classes inheritance in long and short form on boot.
    '''
    if not node:
        return False
    if issubclass(type(node), MetaClass):
        node = node.mNode
    mClass = getMClassDataFromNode(node)
    if mClass and mClass in RED9_META_REGISTERY:
        for inst in mTypesToRegistryKey(mInstances):
            if mode == 'full':
                # FULL CLASS INHERITANCE : test the full inheritance mapping
                # log.debug('testing class inheritance: %s > %s' % (inst, mClass))
                if RED9_META_REGISTERY[inst] in RED9_META_INHERITANCE_MAP[mClass]['full']:
                    # log.debug('MetaNode %s is of subclass >> %s' % (mClass, inst))
                    return True
            elif mode == 'short':
                # SHORT CLASS NAME : test ONLY the short class name, regardless of where the class was imported or how
                # log.debug('testing class inheritance: %s > %s' % (inst, mClass))
                if inst in RED9_META_INHERITANCE_MAP[mClass]['short']:
                    # log.debug('MetaNode %s is of subclass >> %s' % (mClass, inst))
                    return True
            else:
                # original issubclass test
                # log.debug('testing class inheritance: %s > %s' % (inst, mClass))
                if issubclass(RED9_META_REGISTERY[mClass], RED9_META_REGISTERY[inst]):
                    # log.debug('MetaNode %s is of subclass >> %s' % (mClass, inst))
                    return True
    return False

def isMetaNodeClassGrp(node, mClassGrps=[]):
    '''
    check the mClassGrp attr to see if it matches the given
    '''
    if not node:
        return False
    if issubclass(type(node), MetaClass):
        node = node.mNode
#     if not hasattr(mClassGrps, '__iter__'):
    if r9General.is_basestring(mClassGrps):
        mClassGrps = [mClassGrps]
    for grp in mClassGrps:
        # log.debug('mGroup testing: %s' % node)
        try:
            if cmds.getAttr('%s.mClassGrp' % node) == grp:
                return True
        except:
            log.debug('mNode has no MClassGrp attr, must be a legacy system and needs updating!! %s' % node)

@r9General.Timer
def getMetaNodes(mTypes=[], mInstances=[], mClassGrps=[], mAttrs=None, dataType='mClass', nTypes=None, mSystemRoot=False, byname=[], **kws):
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
    :param byname: [] a specific list of node names to search for
    '''
    mNodes = []
    if not nTypes:
        if byname:
            nodes = cmds.ls(byname, type=getMClassNodeTypes(), l=True)
        else:
            nodes = cmds.ls(type=getMClassNodeTypes(), l=True)
    else:
        if byname:
            nodes = cmds.ls(byname, type=nTypes, l=True)
        else:
            nodes = cmds.ls(type=nTypes, l=True)
    if not nodes:
        return mNodes
    for node in nodes:
        mNode = False
        if not mInstances:
            if isMetaNode(node, mTypes=mTypes):
                mNode = True
        else:
            if isMetaNodeInherited(node, mInstances):
                mNode = True
        if mNode:
            if mClassGrps:
#                 if not hasattr(mClassGrps, '__iter__'):
                if r9General.is_basestring(mClassGrps):
                    mClassGrps = [mClassGrps]
                if isMetaNodeClassGrp(node, mClassGrps):
                    mNodes.append(node)
            else:
                mNodes.append(node)
    if not mNodes:
        return mNodes
    if mAttrs:
        # lazy to avoid cyclic imports
        import Red9_CoreUtils as r9Core
        mNodes = r9Core.FilterNode().lsSearchAttributes(mAttrs, nodes=mNodes)
    if dataType == 'mClass':
        return[MetaClass(node, **kws) for node in mNodes]
    else:
        return mNodes


def getMetaRigs(mInstances='MetaRig', mClassGrps=['MetaRig']):
    '''
    Wrapper over the get call to fire back specifically MetaRigs.
    We use mInstances rather than mTypes directly for MetaRig to
    cope with people subclassing, then we clamp the search to the Root MetaRig
    using the mClassGrps variable. This probably will expand as it's tested
    '''
    # try the Red9 Production Rig nodes first
    mRigs = getMetaNodes(mInstances=['Red9_MetaRig', 'Pro_MetaRig'], mClassGrps=['Pro_BodyRig'])
    fRigs = getMetaNodes(mInstances=['Pro_MetaRig_FacialUI'], mClassGrps=['Pro_FacialUI'])
    if mRigs or fRigs:
        return mRigs + fRigs

    # not found, lets widen to all instances of MetaRig with mClassGrp also set
    mRigs = getMetaNodes(mInstances=mInstances, mClassGrps=mClassGrps)
    if mRigs:
        return mRigs

    # ok widen again to all instances of MetaRig, ignoring the mClassGroup
    mRigs = getMetaNodes(mTypes=mInstances)
    if mRigs:
        return getMetaNodes(mTypes=mInstances)
    else:
        # final try, mInstances of MetaRig
        return getMetaNodes(mInstances=mInstances)

def getMetaRigs_fromSelected(singular=False):
    '''
    light wrap over the getMetaRigs function to return a list of mRigs connected
    to the selected nodes
    '''
    allrigs = getMetaRigs()
    nodes = cmds.ls(sl=True)
    mrigs = []
    if nodes:
        for node in nodes:
            rig = getConnectedMetaSystemRoot(node)
            if rig and rig in allrigs and rig not in mrigs:
                mrigs.append(rig)
                if singular:
                    return rig
    return mrigs


def getUnregisteredMetaNodes():
    '''
    Inspect all nodes for the mClass attrs, then see if those nodes and mClass
    types are currently registered in the systems. This means you can inspect
    files from others who have bespoke MClass's and still see their node structures
    even though you won't be able to use or return their class objects
    '''
    mNodes = getMetaNodes(dataType='node')
    return [node for node in cmds.ls('*.mClass', l=True, o=True) if node not in mNodes]


@r9General.Timer
def getConnectedMetaNodes(nodes, source=True, destination=True, mTypes=[], mInstances=[],
                          mAttrs=None, dataType='mClass', nTypes=None, skipTypes=[], skipInstances=[], **kws):
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
    :param skipTypes: if given this is a list of specific mNode types that will be skipped during the
        search WITHOUT instantiating their mNodes
    :param skipInstances: if given this is a list of specific mNode mInstances types that will be skipped during the
        search WITHOUT instantiating their mNodes
    '''
    mNodes = []
    connections = []

    if not nTypes:
        nTypes = getMClassNodeTypes()
    # if mTypes and not type(mTypes)==list:mTypes=[mTypes]
    for nType in nTypes:
        cons = cmds.listConnections(nodes, type=nType, s=source, d=destination, c=True, shapes=True)  # modified 07/02/19 shapes flag for imageplane support
        if cons:
            # NOTE we're only interested in connected nodes via message linked attrs
            for plug, node in zip(cons[::2], cons[1::2]):
                if cmds.getAttr(plug, type=True) == 'message':
                    if node not in connections:
                        connections.append(node)
                        # log.debug(node)
    if not connections:
        return mNodes

    for node in connections:
        addNode = False
        if not mInstances:
            if isMetaNode(node, mTypes=mTypes):
                addNode = True
                # mNodes.append(node)
        else:
            if isMetaNodeInherited(node, mInstances):
                addNode = True
                # mNodes.append(node)
        if skipTypes:
            if isMetaNode(node, mTypes=skipTypes):
                if logging_is_debug():
                    log.debug('skipping node mType found >> %s = %s' % (node, getMClassDataFromNode(node)))
                addNode = False
        if skipInstances:
            if isMetaNodeInherited(node, skipInstances):
                if logging_is_debug():
                    log.debug('skipping node mInstance found >> %s = %s' % (node, getMClassDataFromNode(node)))
                addNode = False
        if addNode:
            mNodes.append(node)

    if mAttrs:
        # lazy to avoid cyclic imports
        import Red9_CoreUtils as r9Core
        mNodes = r9Core.FilterNode().lsSearchAttributes(mAttrs, nodes=mNodes)
    if dataType == 'mClass':
        return [MetaClass(node, **kws) for node in set(mNodes)]
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
        you only get to one of those because of the network wiring, then that is correct.
    '''
    mNodes = getConnectedMetaNodes(node, **kws)
    if not mNodes:
        if isMetaNode(node):
            log.info('given node is an mNode with no connections, returning node')
            return MetaClass(node)
        return
    else:
        mNode = mNodes[0]
    if not mTypes and type(mNode) == MetaRig:
        return mNode
    else:
        runaways = 0
        parents = mNodes
        while parents and not runaways == 100:
            for mNode in parents:
                log.debug('Walking network : %s' % mNode.mNode)

                if mSystemRoot and mNode.hasAttr('mSystemRoot') and mNode.mSystemRoot:
                    return mNode

                parent = getConnectedMetaNodes(mNode.mNode, source=True, destination=False)
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
            runaways += 1
            parents = getConnectedMetaNodes(mNode.mNode, source=True, destination=False)
    return False

@nodeLockManager
def convertMClassType(cls, newMClass, **kws):
    '''
    change the current mClass type of the given class instance. This used to be
    an internal func in eth baseClass but that seemed to make no sense as
    you're mutating the class dynamically

    :param cls: initialize mClass object t9o mutate
    :param newMClass: new class definition for the given cls

    .. note::
        If you're converting a StandardWrapped Maya node to a fully fledged mNode then you also
        need to ensure that that NODETYPE is registered to meta or else it won't get picked up
        when you run any of the gets.
    '''
    newMClass = mTypesToRegistryKey(newMClass)[0]
    if newMClass in RED9_META_REGISTERY:
        try:
            removeFromCache(cls)
            if not cls.hasAttr('mClass'):
                log.debug('Converting StandardWrapped MayaNode to a fully fledged mClass instance')
                convertNodeToMetaData(cls.mNode, newMClass)
            else:
                cls.mClass = newMClass
            return MetaClass(cls.mNode, **kws)
        except StandardError, err:
            log.debug('Failed to convert self to new mClassType : %s' % newMClass)
            traceback = sys.exc_info()[2]  # get the full traceback
            raise StandardError(StandardError(err), traceback)
    else:
        raise StandardError('given class is not in the mClass Registry : %s' % newMClass)

def convertNodeToMetaData(nodes, mClass):
    '''
    pass in a node and convert it to a MetaNode, assuming that the nodeType
    is valid in the metaNodeTypesRegistry.

    :param nodes: nodes to cast to mClass instances
    :param mClass: mClass class to convert them too

    .. note::
        ideally you should use the convertMClassType func now as that wraps this if the
        nodes passed in aren't already instanitated or bound to meta
    '''
    if not type(nodes) == list:
        nodes = [nodes]
    for node in nodes:
        log.debug('converting node %s >> to %s mNode' % (r9Core.nodeNameStrip(node), mClass))
        mNode = MetaClass(node)
        mNode.addAttr('mClass', value=mTypesToRegistryKey(mClass)[0])
        mNode.addAttr('mNodeID', value=node.split('|')[-1].split(':')[-1])
        mNode.attrSetLocked('mClass', True)
        mNode.attrSetLocked('mNodeID', True)
    return [MetaClass(node) for node in nodes]

def delete_mNode(mNode):
    '''
    wrapper to delete a given mNode via the standard mClass call
    rather than the mNodes internal class.delete() call to avoid
    subclass issues when calling super().delete()
    '''
    global RED9_META_NODECACHE
    if cmds.lockNode(mNode.mNode, q=True):
        cmds.lockNode(mNode.mNode, lock=False)
    # clear the node from the cache
    removeFromCache([mNode])

    cmds.delete(mNode.mNode)
    del(mNode)

def createMetaNode(mType=None, *args, **kws):
    '''
    cheers Josh for this suggestion and code snippet ;)
    '''
    _str_func = 'createMetaNode'

    if not type(mType) in [unicode, str]:
        try:
            mType = mType.__name__
        except Exception, err:
            raise ValueError, "mType not a string and not a usable class name. mType: {0}".format(mType)
    if mType not in RED9_META_REGISTERY:
        raise ValueError, "mType not found in class registry. mType: {0}".format(mType)

    _call = RED9_META_REGISTERY.get(mType)

    log.debug("|{0}| >> mType: {1} | class: {2}".format(_str_func, mType, _call))

    try:
        return _call(*args, **kws)
    except Exception, err:
        log.info("|{0}| >> mType: {1} | class: {2}".format(_str_func, mType, _call))
        if args:
            log.info("|{0}| >> Args...".format(_str_func))
            for i, arg in enumerate(args):
                log.info("    arg {0}: {1}".format(i, arg))
        if kws:
            log.info("|{0}| >> Kws...".format(_str_func))
            for items in kws.items():
                log.info("    kw: {0}".format(items))

        for arg in err.args:
            log.error(arg)
        raise Exception, err


class MClassNodeUI(object):
    '''
    Simple UI to display all MetaNodes in the scene
    '''
    def __init__(self, mTypes=None, mInstances=None, mClassGrp=None, closeOnSelect=False,
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
        self.mInstances = mInstances
        self.mTypes = mTypes
        self.mClassGrp = mClassGrp
        self.closeOnSelect = closeOnSelect
        self.func = funcOnSelection  # Given Function to run on the selected node when UI selected
        self.sortBy = sortBy
        self.allowMulti = allowMulti

        self.win = 'MetaClassFinder'
        self.mNodes = []
        self.cachedforFilter = []
        self.stripNamespaces = False
        self.shortname = False
        self.sortBy = 'class'
        self.selected = []

    @classmethod
    def show(cls):
        cls()._showUI()

    def close(self):
        if cmds.window(self.win, exists=True):
            cmds.deleteUI(self.win, window=True)

    def _showUI(self):
        self.close()
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
        cmds.menuItem(l=LANGUAGE_MAP._Generic_.contactme, c=lambda *args: (r9Setup.red9ContactInfo()))
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
        cmds.scrollLayout('slMetaNodeScroll', rc=lambda *args: self.__uicb_fitTextScroll(), cr=True)
        cmds.columnLayout(adjustableColumn=True)
        cmds.separator(h=5, style='none')

        # Build the class options to filter by
        try:
            cmds.rowColumnLayout('rc_useMetaFilterUI', numberOfColumns=3, adj=2,  # maya 2018 upwards has a new adj flag for rowColumns
                                 columnWidth=[(1, 120), (2, 120), (3, 200)],
                                 columnSpacing=[(1, 10), (2, 10), (3, 20)])
        except:
            cmds.rowColumnLayout('rc_useMetaFilterUI', numberOfColumns=3,
                                 columnWidth=[(1, 120), (2, 120), (3, 200)],
                                 columnSpacing=[(1, 10), (2, 10), (3, 20)])
        cmds.checkBox('cb_filter_mTypes', label=LANGUAGE_MAP._MetaNodeUI_.mtypes_filter, v=False,
                      cc=partial(self.__uicb_setfilterMode, 'mTypes'))
        cmds.checkBox('cb_filter_mInstances', label=LANGUAGE_MAP._MetaNodeUI_.minstances_filter, v=False,
                      cc=partial(self.__uicb_setfilterMode, 'mInstance'))
        cmds.optionMenu('om_MetaUI_Filter', ni=len(RED9_META_REGISTERY),
                        ann=LANGUAGE_MAP._MetaNodeUI_.registered_metaclasses_ann,
                        cc=partial(self.fillScroll))
        for preset in sorted(RED9_META_REGISTERY):
            cmds.menuItem(l=preset)
        cmds.setParent('..')

        cmds.separator(h=10, style='in')
        try:
            cmds.rowColumnLayout(numberOfColumns=4, adj=2,   # maya 2018 upwards has a new adj flag for rowColumns
                                columnWidth=[(1, 80), (2, 85), (3, 280), (4, 30)],
                                columnSpacing=[(1, 10), (2, 10)])
        except:
            cmds.rowColumnLayout(numberOfColumns=4,
                                columnWidth=[(1, 80), (2, 85), (3, 280), (4, 30)],
                                columnSpacing=[(1, 10), (2, 10)])
        cmds.checkBox('cb_shortname', label=LANGUAGE_MAP._MetaNodeUI_.shortname, v=False, cc=self.__filterResults)
        cmds.checkBox('cb_stripNS', label=LANGUAGE_MAP._MetaNodeUI_.stripnamespace, v=False, cc=self.__filterResults)
        try:
            cmds.textFieldGrp('filterByName', l=LANGUAGE_MAP._MetaNodeUI_.filter_by_name, text='', tcc=self.__filterResults, cw=((1, 100), (2, 170)))
        except:
            cmds.textFieldGrp('filterByName', l=LANGUAGE_MAP._MetaNodeUI_.filter_by_name, text='', cc=self.__filterResults, cw=((1, 100), (2, 170)))
        cmds.button(LANGUAGE_MAP._Generic_.clear, c=self.__clearFilter)
        cmds.setParent('..')

        cmds.separator(h=10, style='in')
        cmds.rowColumnLayout(numberOfColumns=4, columnWidth=[(1, 100), (2, 100), (3, 100), (4, 100)],
                             columnSpacing=[(1, 10), (2, 10), (3, 10)])
        self.uircbMetaUIShowStatus = cmds.radioCollection('uircbMetaUIShowStatus')
        cmds.radioButton('metaUISatusAll', label=LANGUAGE_MAP._MetaNodeUI_.all, cc=partial(self.fillScroll))
        cmds.radioButton('metaUISatusValids', label=LANGUAGE_MAP._MetaNodeUI_.valids, cc=partial(self.fillScroll))
        cmds.radioButton('metaUISatusinValids', label=LANGUAGE_MAP._MetaNodeUI_.invalids, cc=partial(self.fillScroll))
        cmds.radioButton('metaUISatusUnregistered', label=LANGUAGE_MAP._MetaNodeUI_.unregistered, cc=partial(self.fillScroll))
        cmds.setParent('..')

        # You've passed in the filter types directly to the UI Class
        if self.mTypes or self.mInstances:
            # cmds.separator(h=15, style='none')
            cmds.rowColumnLayout('rc_useMetaFilterUI', e=True, en=False, vis=False)
            if self.mTypes:
                cmds.text(label='%s : %s' % (LANGUAGE_MAP._MetaNodeUI_.ui_launch_mtypes, self.mTypes))
            else:
                cmds.text(label='%s : %s' % (LANGUAGE_MAP._MetaNodeUI_.ui_launch_minstances, self.mInstances))
            cmds.separator(h=15, style='none')

        if not self.allowMulti:
            cmds.textScrollList('slMetaNodeList', font="fixedWidthFont")
        else:
            cmds.textScrollList('slMetaNodeList', font="fixedWidthFont", allowMultiSelection=True)
        cmds.popupMenu('r9MetaNodeUI_Popup')
        cmds.menuItem(label=LANGUAGE_MAP._MetaNodeUI_.graph_selected, command=partial(self.graphNetwork))
        cmds.menuItem(divider=True)
        cmds.menuItem(label=LANGUAGE_MAP._MetaNodeUI_.rename_mNode, command=partial(self.__uiCB_renameNode))
        cmds.menuItem(label=LANGUAGE_MAP._MetaNodeUI_.select_children,
                      ann=LANGUAGE_MAP._MetaNodeUI_.select_children_ann,
                      command=partial(self.doubleClick))
        cmds.menuItem(label=LANGUAGE_MAP._MetaNodeUI_.delete_selected,
                      ann=LANGUAGE_MAP._MetaNodeUI_.delete_selected_ann,
                      command=partial(self.deleteCall))
        cmds.menuItem(divider=True)
        cmds.menuItem(label=LANGUAGE_MAP._MetaNodeUI_.sort_by_classname, command=partial(self.fillScroll, 'byClass'))
        cmds.menuItem(label=LANGUAGE_MAP._MetaNodeUI_.sort_by_nodename, command=partial(self.fillScroll, 'byName'))
        cmds.menuItem(divider=True)
        cmds.menuItem(label=LANGUAGE_MAP._MetaNodeUI_.class_all_registered, command=partial(self.fillScroll, 'byName'))
        cmds.menuItem(label=LANGUAGE_MAP._MetaNodeUI_.class_print_inheritance, command=self.__uiCB_printInheritance)
        cmds.menuItem(divider=True)
        cmds.menuItem(label=LANGUAGE_MAP._MetaNodeUI_.pro_connect_node, command=self.__uiCB_connectNode)
        cmds.menuItem(label=LANGUAGE_MAP._MetaNodeUI_.pro_disconnect_node, command=self.__uiCB_disconnectNode)

        cmds.menuItem(divider=True)
        cmds.menuItem(l=LANGUAGE_MAP._MetaNodeUI_.pro_addchild_metanode, sm=True)
        for name, _ in sorted(getMClassMetaRegistry().items()):
            cmds.menuItem(label=name, command=partial(self.__uiCB_connectChildMetaNode, name))

        cmds.button(label=LANGUAGE_MAP._Generic_.refresh, command=partial(self.fillScroll))
        cmds.separator(h=15, style='none')
        cmds.iconTextButton(style='iconOnly', bgc=(0.7, 0, 0), image1='Rocket9_buttonStrap2.bmp',
                                 c=lambda *args: (r9Setup.red9ContactInfo()), h=22, w=200)
        cmds.showWindow(window)
        cmds.radioCollection(self.uircbMetaUIShowStatus, edit=True, select='metaUISatusAll')
        self.fillScroll()

    def __uicb_setfilterMode(self, mode, *args):
        if mode == 'mTypes':
            cmds.checkBox('cb_filter_mInstances', e=True, v=False)
        elif mode == 'mInstance':
            cmds.checkBox('cb_filter_mTypes', e=True, v=False)
        self.fillScroll(*args)

    def __uicb_fitTextScroll(self):
        '''
        bodge to resize the textScroll
        '''
#         if not r9Setup.maya_screen_mapping()[0]:
        cmds.textScrollList('slMetaNodeList', e=True,
                                h=int((cmds.scrollLayout('slMetaNodeScroll', q=True, h=True) / r9Setup.maya_dpi_scaling_factor()) - 170))
#         else:
#             # using the same dynamic remapping values to recalculate width and height for 4k
#             height = cmds.scrollLayout('slMetaNodeScroll', q=True, h=True)
#             mapped = r9Core.ui_dpi_scaling_factors(height=height) - 170
#             cmds.textScrollList('slMetaNodeList', e=True, h=mapped)

    def graphNetwork(self, *args):
        if r9Setup.mayaVersion() < 2013:
            mel.eval('hyperGraphWindow( "", "DG")')
        else:
            mel.eval('NodeEditorWindow;NodeEditorGraphUpDownstream;')

    def selectCmd(self, *args):
        '''
        callback run on select in the UI, allows you to run the func passed
        in by the funcOnSelection arg
        '''
        self.selected = []
        indexes = cmds.textScrollList('slMetaNodeList', q=True, sii=True)
        if indexes:
            cmds.select(cl=True)
        for i in indexes:
            node = MetaClass(self.mNodes[i - 1])
            self.selected.append(node)
            log.debug('selected : %s' % node)

            # func is a function passed into the UI via the funcOnSelection arg
            # this allows external classes to use this as a signal call on select
            if self.func:
                self.func(node.mNode)
            else:
                cmds.select(node.mNode, add=True, noExpand=True)

        if self.closeOnSelect:
            cmds.deleteUI('MetaClassFinder', window=True)

    def deleteCall(self, *args):
        result = cmds.confirmDialog(
                title=str(LANGUAGE_MAP._MetaNodeUI_.confirm_delete),
                button=[str(LANGUAGE_MAP._Generic_.yes),
                        str(LANGUAGE_MAP._Generic_.cancel)],
                message=str(LANGUAGE_MAP._MetaNodeUI_.confirm_delete_message),
                defaultButton=str(LANGUAGE_MAP._Generic_.cancel),
                bgc=(0.5, 0.1, 0.1),
                cancelButton=str(LANGUAGE_MAP._Generic_.cancel),
                dismissString=str(LANGUAGE_MAP._Generic_.cancel))
        if result == str(LANGUAGE_MAP._Generic_.yes):
            try:
                indexes = cmds.textScrollList('slMetaNodeList', q=True, sii=True)
                if indexes:
                    for i in indexes:
                        MetaClass(self.mNodes[i - 1]).delete()
                self.fillScroll()
            except:
                log.warning('delete failed')

    def doubleClick(self, *args):
        '''
        run the generic meta.getChildren call and select the results
        '''
        cmds.select(cl=True)
        nodes = []
        for i in cmds.textScrollList('slMetaNodeList', q=True, sii=True):
            nodes.extend(MetaClass(self.mNodes[i - 1]).getChildren(walk=True))
        if nodes:
            cmds.select(nodes)
        else:
            log.warning('no child nodes found from given metaNode')
        # cmds.select(self.mNodes[cmds.textScrollList('slMetaNodeList',q=True,sii=True)[0]-1].getChildren(walk=True))

    def __fillScrollEntries(self):
        '''
        consistant way to fill the text data displayed
        '''
        baseNames = []
        cmds.textScrollList('slMetaNodeList', edit=True, ra=True)
        width = len(self.mNodes[0])
        # figure out the width of the first cell
        for meta in self.mNodes:
            name = meta
            if self.stripNamespaces:
                name = meta.replace(':', '')
            if self.shortname:
                name = name.split('|')[-1].split(':')[-1]
            if len(name) > width:
                width = len(name)
            baseNames.append(name)
        width += 3
        entries = zip(self.mNodes, baseNames)
        # fill the scroll list
        for meta, name in entries:
            cmds.textScrollList('slMetaNodeList', edit=True,
                                    append=('{0:<%i}:{1:}' % width).format(name, getMClassDataFromNode(meta)),
                                    sc=lambda *args: self.selectCmd(),
                                    dcc=lambda *x: self.doubleClick())

    def __filterResults(self, *args):
        '''
        rebuild the list based on the filter typed in, Note that results are
        converted to upper before the match so it's case IN-sensitive
        '''
        self.shortname = False
        self.stripNamespaces = False
        filterby = cmds.textFieldGrp('filterByName', q=True, text=True)
        if filterby:
            self.mNodes = []
            if self.cachedforFilter:
                # fill the scroll list
                self.mNodes = r9Core.filterListByString(self.cachedforFilter, filterby, matchcase=False)

        if cmds.checkBox('cb_shortname', q=True, v=True):
            self.shortname = True
        if cmds.checkBox('cb_stripNS', q=True, v=True):
            self.stripNamespaces = True
        self.__fillScrollEntries()

    def __clearFilter(self, *args):
        cmds.textFieldGrp('filterByName', e=True, text='')
        self.fillScroll()

    def fillScroll(self, sortBy=None, *args):  # , mClassToShow=None, *args):
        states = cmds.radioCollection(self.uircbMetaUIShowStatus, q=True, select=True)
        cmds.textScrollList('slMetaNodeList', edit=True, ra=True)
        self.dataType = 'node'
        if states == 'metaUISatusinValids' or states == 'metaUISatusValids':
            self.dataType = 'mClass'

        # build the metaNode list up from the filters =====================

        if states == 'metaUISatusUnregistered':
            self.mNodes = getUnregisteredMetaNodes()

        elif cmds.rowColumnLayout('rc_useMetaFilterUI', q=True, en=True):
            mTypesFilter = cmds.checkBox('cb_filter_mTypes', q=True, v=True)
            mInstanceFilter = cmds.checkBox('cb_filter_mInstances', q=True, v=True)
            mCalssSelected = cmds.optionMenu('om_MetaUI_Filter', q=True, v=True)

            if mTypesFilter:
                self.mNodes = getMetaNodes(mTypes=mCalssSelected, mInstances=None, dataType=self.dataType)
                print('mTypeFilter : ', mCalssSelected)
            elif mInstanceFilter:
                self.mNodes = getMetaNodes(mTypes=None, mInstances=mCalssSelected, dataType=self.dataType)
                print('mInstanceFilter : ', mCalssSelected)
            else:
                self.mNodes = getMetaNodes(mTypes=self.mTypes, mInstances=self.mInstances, dataType=self.dataType)
        else:
            self.mNodes = getMetaNodes(mTypes=self.mTypes, mInstances=self.mInstances, dataType=self.dataType)
            print('none', self.mTypes, self.mInstances)

        if not self.mNodes:
            log.warning('no metaNodes found that match the filters')
            return

        if states == 'metaUISatusinValids':
            self.mNodes = [node.mNode for node in self.mNodes if not node.isValid()]
        if states == 'metaUISatusValids':
            self.mNodes = [node.mNode for node in self.mNodes if node.isValid()]

        # Sort the list ==================================================
        if not sortBy:
            sortBy = self.sortBy

        if sortBy == 'byClass':
            self.mNodes = sorted(self.mNodes, key=lambda x: getMClassDataFromNode(x).upper())
        elif sortBy == 'byName':
            self.mNodes = sorted(self.mNodes, key=lambda x: x.upper())

        # fill the textScroller =========================================
        if self.mNodes:
            self.cachedforFilter = list(self.mNodes)  # cache the results so that the filter by name is fast!
            self.__fillScrollEntries()

    def __uiCB_printInheritance(self, *args):
        '''
        show the inheritance of the given MClass
        '''
        indexes = cmds.textScrollList('slMetaNodeList', q=True, sii=True)
        if len(indexes) == 1:
            mNode = MetaClass(self.mNodes[indexes[0] - 1])
            for c in mNode.getInheritanceMap():
                print('Class Inheritance : ', c)

    def __uiCB_connectNode(self, *args):
        '''
        PRO PACK : Given a single selected mNode from the UI and a single selected MAYA node, run
        connectChild with the given promtString as the attr
        '''
        indexes = cmds.textScrollList('slMetaNodeList', q=True, sii=True)
        if len(indexes) == 1:
            mNode = MetaClass(self.mNodes[indexes[0] - 1])
        else:
            raise StandardError('Connect Call only works with a single selected mNode from the UI')

        r9Setup.PRO_PACK_STUBS().MetaDataUI.uiCB_connectNode(mNode)

    def __uiCB_disconnectNode(self, *args):
        '''
        PRO PACK : Given a single selected mNode from the UI and selected MAYA nodes, run
        disconnectChild to remove them from the metaData system
        '''
        indexes = cmds.textScrollList('slMetaNodeList', q=True, sii=True)
        if len(indexes) == 1:
            mNode = MetaClass(self.mNodes[indexes[0] - 1])
        else:
            raise StandardError('Connect Call only works with a single selected mNode from the UI')

        r9Setup.PRO_PACK_STUBS().MetaDataUI.uiCB_disconnectNode(mNode)

    def __uiCB_renameNode(self, *args):
        '''
        rename the selected mNode
        '''
        result = cmds.promptDialog(title=LANGUAGE_MAP._MetaNodeUI_.rename_mNode,
                                   message=LANGUAGE_MAP._Generic_.name,
                                   button=[LANGUAGE_MAP._Generic_.apply, LANGUAGE_MAP._Generic_.cancel],
                                   defaultButton=LANGUAGE_MAP._Generic_.apply,
                                   text=self.selected[0].shortName(),
                                   cancelButton='Cancel',
                                   dismissString='Cancel')
        if result == LANGUAGE_MAP._Generic_.apply:
            self.selected[0].rename(cmds.promptDialog(query=True, text=True))
            self.fillScroll()

    def __uiCB_connectChildMetaNode(self, mClass, *args):
        '''
        PRO PACK : Given a single selected mNode from the UI and selected MAYA nodes, run
        disconnectChild to remove them from the metaData system
        '''
        indexes = cmds.textScrollList('slMetaNodeList', q=True, sii=True)
        if len(indexes) == 1:
            mNode = MetaClass(self.mNodes[indexes[0] - 1])
        else:
            raise StandardError('Connect Call only works with a single selected mNode from the UI')
        r9Setup.PRO_PACK_STUBS().MetaDataUI.uiCB_addChildMetaNode(mNode, mClass)
        self.fillScroll()
        print('adding childMetaNode of mClass type : %s to %s' % (mClass, mNode.mNode))

    def printRegisteredNodeTypes(self, *args):
        print('\nRED9_META_NODETYPE_REGISTERY:\n=============================')
        print(getMClassNodeTypes())

    def printRegisteredMetaClasses(self, *args):
        data = getMClassMetaRegistry()
        print('\nRED9_META_REGISTERY:\n====================')
        for key, value in sorted(data.items()):
            print(key, ' : ', value)

    def printMetaNodeCache(self, *args):
        data = getMClassNodeCache()
        print('\nRED9_META_NODECACHE:\n====================')
        for key, value in sorted(data.items()):
            print(key, ' : ', value)


# ----------------------------------------------------------------------------
# --- Main Meta Class --- ------
# ----------------------------------------------------------------------------

class MetaInstanceError(Exception):
    '''
    exception thrown if the mClass object iunstance is no longer valid
    usually thrown if the class object is called after the Maya scene has been
    changed by loading or new
    '''
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)


class MetaClass(object):

    cached = None
    UNMANAGED = ['mNode',
                   'mNodeID',
                   '_MObject',
                   '_MObjectHandle',
                   '_MFnDependencyNode',
                   '_lockState',
                   'lockState',
                   '_forceAsMeta',
                   '_lastDagPath',
                   '_lastUUID']

    def __new__(cls, *args, **kws):

        # Idea here is if a MayaNode is passed in and has the mClass attr
        # we pass that into the super(__new__) such that an object of that class
        # is then instantiated and returned.

        mClass = None
        mNode = None
        MetaClass.cached = None

        if args:
            mNode = args[0]

            if mNode:
                cacheInstance = getMetaFromCache(mNode)  # Do Not run __new__ if the node is in the Cache
                # log.debug('### MetaClass.cached being set in the __new__ ###')
                if cacheInstance:
                    MetaClass.cached = True
                    return cacheInstance

            if issubclass(type(mNode), MetaClass):
                # log.debug('NodePassed is already an instanciated MetaNode!!')
                MetaClass.cached = True
                return mNode

            mClass = isMetaNode(mNode, checkInstance=False, returnMClass=True)

        if mClass:
            # log.debug("mClass derived from MayaNode Attr : %s" % mClass)
            if mClass in RED9_META_REGISTERY:
                _registeredMClass = RED9_META_REGISTERY[mClass]
                try:
                    if logging_is_debug():
                        log.debug('### Instantiating existing mClass : %s >> %s ###' % (mClass, _registeredMClass))
                    return super(cls.__class__, cls).__new__(_registeredMClass)  # , *args, **kws)
                except:
                    log.debug('Failed to initialize mClass : %s' % _registeredMClass)
                    pass
            else:
                raise StandardError('Node has an unRegistered mClass attr set')
        else:
            log.debug("mClass not found, given or registered")
            return super(cls.__class__, cls).__new__(cls)

    # @pymelHandler
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
        if logging_is_debug():
            log.debug('Meta__init__ main args :: node=%s, name=%s, nodeType=%s' % (node, name, nodeType))
        # data that will not get pushed to the Maya node
        object.__setattr__(self, '_MObject', '')
        object.__setattr__(self, '_MObjectHandle', '')
        object.__setattr__(self, '_MDagPath', '')
        object.__setattr__(self, '_lastDagPath', '')  # ...NEW...stored on mNode get
        object.__setattr__(self, '_lastUUID', '')  # . ..NEW...stored on caching of node
        object.__setattr__(self, '_lockState', False)  # by default all mNode's are unlocked, manage this in any subclass if needed
        object.__setattr__(self, '_forceAsMeta', False)  # force all getAttr calls to return mClass objects even for standard Maya nodes

        if not node:
#             if not name:
#                 name = self.__class__.__name__

            # no MayaNode passed in so make a fresh network node (default)
            if not nodeType == 'network' and nodeType not in RED9_META_NODETYPE_REGISTERY:
                # raise IOError('nodeType : "%s" : is NOT yet registered in the "RED9_META_NODETYPE_REGISTERY", please use r9Meta.registerMClassNodeMapping(nodeTypes=["%s"]) to do so before making this node' % (nodeType, nodeType))
                if logging_is_debug():
                    log.debug('nodeType : "%s" : is NOT yet registered in the "RED9_META_NODETYPE_REGISTERY", please use r9Meta.registerMClassNodeMapping(nodeTypes=["%s"]) to do so before making this node' % (nodeType, nodeType))
                if not name:
                    name = nodeType
            if not name:
                name = self.__class__.__name__

            # node = cmds.createNode(nodeType, name=name)
            # self.mNode = node
            self.mNode, _full_management = self.__createnode__(nodeType, name=name)

            if _full_management:
                # ! MAIN ATTR !: used to know what class to instantiate.
                self.addAttr('mClass', value=str(self.__class__.__name__), attrType='string')

                # ! MAIN NODE ID !: used by pose systems to ID the node.
                self.mNodeID = name

                # ! CLASS GRP  : this is used mainly by MetaRig and other complex systems
                # to denote a classes intended system base
                self.addAttr('mClassGrp', value='MetaClass', attrType='string', hidden=True)
                # ! SYSTEM ROOT : indicates that this node is the root of a system and
                # therefore halts the 'getConnectedMetaSystemRoot' call
                self.addAttr('mSystemRoot', value=False, attrType='bool', hidden=True)

                if r9Setup.mayaVersion() < 2016:
                    self.addAttr('UUID', value='')  # ! Cache UUID attr which the Cache itself is in control of

                cmds.setAttr('%s.%s' % (self.mNode, 'mClass'), e=True, l=True)  # lock it
                cmds.setAttr('%s.%s' % (self.mNode, 'mNodeID'), e=True, l=True)  # lock it

            log.debug('New Meta Node %s Created' % name)
            registerMClassNodeCache(self)

        else:
            self.mNode = node

            if isMetaNode(node):
                log.debug('Meta Node Passed in : %s' % node)
                registerMClassNodeCache(self)
            else:
                log.debug('Standard Maya Node being metaManaged')
                # do we register NON MClass standard wrapped Maya Nodes to the registry??
                # registerMClassNodeCache(self)

        # if not wrapped_node:
        self.lockState = False  # why set this on instantiation?

        # bind any default attrs up - note this should be overloaded where required
        self.__bindData__(*args, **kws)

        # This is useful! so we have a node with a lot of attrs, or just a simple node
        # this block if activated will auto-fill the object.__dict__ with all the available
        # Maya node attrs, so you get autocomplete on ALL attrs in the script editor!
        if autofill == 'all' or autofill == 'messageOnly':
            self.__fillAttrCache__(autofill)

    def __createnode__(self, nodeType, name):
        '''
        overloaded method to modify the base createNode call for specific types,
        added initially for the imagePlane support for ProPack

        :return [node, management]: where node is the name of the node created and management
            is a bool which controls the binding of the base attrs, if False we DON'T bind up
            the mNodeID, mClass attrs, instead we rely on the nodeType.lower() being a key in
            the Registery as a class (ie, ImagePlane in ProPack )

        :param nodeType: type of node to create
        :param name: name of the new node
        '''
        return cmds.createNode(nodeType, name=name), True

    def __bindData__(self, *args, **kws):
        '''
        This is intended as an entry point to allow you to bind whatever attrs or extras
        you need at a class level. It's called by the __init__ ...
        Intended to be overloaded as and when needed when inheriting from MetaClass

        .. note::
            When subclassing __bindData__ will run BEFORE your subclasses __init__

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
        try:
            if not self.isValidMObject():
                return False
            if self.hasAttr('mClass') and not cmds.listConnections(self.mNode):
                return False
        except MetaInstanceError, err:
            print('Bailing caught exception')
            return False
        return True

    def isValidMObject(self):
        '''
        validate the MObject, without this Maya will crash if the pointer is no longer valid

        TODO: thinking of storing the dagPath when we fill in the mNode to start with and
        if this test fails, ie the scene has been reloaded, then use the dagPath to refine
        and refill the mNode property back in.... maybe??
        '''
        try:
            mobjHandle = object.__getattribute__(self, "_MObjectHandle")
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

    # cast the mNode attr to the actual MObject so it's no longer limited by string dagpaths
    @property
    def mNode(self):
        '''
        mNode is the pointer to the Maya object itself, retrieved via the MObject
        under the hood so it's always in sync.
        '''
        mobjHandle = object.__getattribute__(self, "_MObjectHandle")
        if mobjHandle:
            try:
                if not mobjHandle.isValid():
                    # ...raise this error so that this stops calls on bad nodes as soon as possible. With just return, you get a series of errors
                    # raise ValueError,('MObject is no longer valid - Last good dag path was: "%s"' % object.__getattribute__(self, "_lastDagPath"))
                    raise MetaInstanceError, ('MObject is no longer valid - Last good dag path was: "%s"' % object.__getattribute__(self, "_lastDagPath"))
                # if we have an object thats a dagNode, ensure we return FULL Path
                mobj = object.__getattribute__(self, "_MObject")
                if OpenMaya.MObject.hasFn(mobj, OpenMaya.MFn.kDagNode):
                    dPath = OpenMaya.MDagPath()
                    OpenMaya.MDagPath.getAPathTo(mobj, dPath)
                    _result = dPath.fullPathName()
                else:
                    depNodeFunc = OpenMaya.MFnDependencyNode(mobj)
                    _result = depNodeFunc.name()
                # cache the dagpath on the object as a back-up for error reporting
                object.__setattr__(self, '_lastDagPath', _result)
                return _result
            except StandardError, error:
                raise StandardError(error)

    @mNode.setter
    def mNode(self, node):
        if node:
            try:
                mobj = OpenMaya.MObject()
                selList = OpenMaya.MSelectionList()
                selList.add(node)
                selList.getDependNode(0, mobj)
                object.__setattr__(self, '_MObject', mobj)
                object.__setattr__(self, '_MObjectHandle', OpenMaya.MObjectHandle(mobj))
                object.__setattr__(self, '_MFnDependencyNode', OpenMaya.MFnDependencyNode(mobj))
                # if we're a DAG object store off the MDagPath
#                if OpenMaya.MObject.hasFn(mobj, OpenMaya.MFn.kDagNode):
#                    dag = OpenMaya.MDagPath()
#                    selList.getDagPath(0,dag)
#                    object.__setattr__(self,'_MDagPath',dag)

            except StandardError, error:
                raise StandardError(error)

    @property
    def mNodeID(self):
        if not self.hasAttr('mNodeID'):
            # for casting None MetaData, standard Maya nodes into the api
            return self.mNode.split('|')[-1].split(':')[-1]
        else:
            return cmds.getAttr('%s.%s' % (self.mNode, 'mNodeID'))

    @mNodeID.setter
    @nodeLockManager
    def mNodeID(self, value):
        '''
        Why move this to a property? it's for speed when dealing with non meta /
        StandardWrapped Maya nodes in Meta. We used to set mNodeID during the initialization
        of the class regardless of whether we were creating the node or just instantiating it.
        This was slow and un-needed.
        '''
        if not self.hasAttr('mNodeID'):
            cmds.addAttr(self.mNode, longName='mNodeID', dt='string')
        cmds.setAttr('%s.%s' % (self.mNode, 'mNodeID'), e=True, l=False)
        cmds.setAttr('%s.%s' % (self.mNode, 'mNodeID'), value, type='string')
        cmds.setAttr('%s.%s' % (self.mNode, 'mNodeID'), e=True, l=True)  # lock it

    @property
    def mNodeMObject(self):
        '''
        exposed wrapper to return the MObject directly, this passes via the MObjectHandle
        to ensure that the MObject cached is still valid
        '''
        mobjHandle = object.__getattribute__(self, "_MObjectHandle")
        if mobjHandle:
            try:
                if not mobjHandle.isValid():
                    log.info('mNodes : MObject is no longer valid - %s - object may have been deleted or the scene reloaded?'
                              % object.__getattribute__(self, 'mNodeID'))
                    return
                # if we have an object thats a dagNode, ensure we return FULL Path
                return object.__getattribute__(self, "_MObject")
            except StandardError, error:
                raise StandardError(error)

    def getInheritanceMap(self):
        '''
        return the inheritance mapping of this class instance
        '''
        import inspect
        return inspect.getmro(self.__class__)

    @property
    def lockState(self):
        '''
        Lockstate is just that, the lockNode state of the Maya node
        '''
        return self._lockState

    @lockState.setter
    def lockState(self, state):
        try:
            cmds.lockNode(self.mNode, lock=state)
            self._lockState = state
        except:
            log.debug("can't set the nodeState for : %s" % self.mNode)

    def __repr__(self):
        try:
            if self.hasAttr('mClass'):
                return "%s(mClass: '%s', node: '%s')" % (self.__class__, self.mClass, self.mNode.split('|')[-1])
            else:
                return "%s(Wrapped Standard MayaNode, node: '%s')" % (self.__class__, self.mNode.split('|')[-1])
        except:
            # if this fails we have a dead node more than likely
            try:
                RED9_META_NODECACHE.pop(object.__getattribute__(self, "_lastUUID"))
                if logging_is_debug():
                    log.debug("Dead mNode %s removed from cache..." % object.__getattribute__(self, "_lastDagPath"))
            except:
                pass
            try:
                return ("Dead mNode : Last good dag path was: %s" % object.__getattribute__(self, "_lastDagPath"))
            except:
                return "THIS NODE BE DEAD BY THINE OWN HAND"

    def __eq__(self, obj):
        '''
        Equals calls are handled via the MObject cache
        '''
        # added this is mObject valid check as this was another place stuff breaks on a dead node...same cache clear ability
        if not self._MObjectHandle.isValid():
            try:
                RED9_META_NODECACHE.pop(object.__getattribute__(self, "_lastUUID"))
                if logging_is_debug():
                    log.debug("Dead mNode %s removed from cache..." % object.__getattribute__(self, "_lastDagPath"))
            except:
                pass
            return False
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

#     @r9General.Timer
    def __fillAttrCache__(self, level):
        '''
        go through all the attributes on the given node and cast each one of them into
        the main object.__dict__ this means they all show in the scriptEditor and autocomplete!
        This is ONLY for ease of use when dot complete in Maya, nothing more
        '''
        if level == 'messageOnly':
            attrs = self.listAttrsOfType(Type='message')
        else:
            attrs = cmds.listAttr(self.mNode)
            # attrs = self.listAttrsOfType(Type='none')
        for attr in attrs:
            try:
                # we only want to fill the __dict__ we don't want the overhead
                # of reading the attr data as thats done on demand.
                object.__setattr__(self, attr, None)
            except:
                log.debug('unable to bind attr : %s to initial python object' % attr)

    def setUUID(self):
        '''
        unique UUID used by the caching system
        '''
        if r9Setup.mayaVersion() >= 2016:
            mfn = OpenMaya.MFnDependencyNode(self._MObject)
            uuid = OpenMaya.MUuid()
            uuid.generate()
            mfn.setUuid(uuid)
            newUUID = uuid.asString()
            self.UUID = newUUID
        else:
            newUUID = generateUUID()
            self.UUID = newUUID

        if logging_is_debug():
            log.debug('setting new UUID : %s on %s' % (newUUID, self.mNode))
        return newUUID

    def getUUID(self):
        if r9Setup.mayaVersion() >= 2016:
            return cmds.ls(self.mNode, uuid=True)[0]
        return self.UUID

    # Attribute Management block
    # -----------------------------------------------------------------------------------

    def __setEnumAttr__(self, attr, value):
        '''
        Enums : I'm allowing you to set value by either the index or the display text
        '''
        if attributeDataType(value) in ['string', 'unicode']:
            log.debug('set enum attribute by string :  %s' % value)
            enums = cmds.attributeQuery(attr, node=self.mNode, listEnum=True)[0].split(':')
            try:
                value = enums.index(value)
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
        if cmds.attributeQuery(attr, node=self.mNode, multi=True) == False:
            if attributeDataType(value) == 'complex':
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

        if attr not in MetaClass.UNMANAGED and not attr == 'UNMANAGED':
            if self.hasAttr(attr):
                locked = False
                if self.attrIsLocked(attr) and force:
                    self.attrSetLocked(attr, False)
                    locked = True
                mnode = self.mNode
                attrType = self.attrType(attr)

                # enums Handling
                if attrType == 'enum':
                    self.__setEnumAttr__(attr, value)

                # message Link handling
                elif attrType == 'message':
                    self.__setMessageAttr__(attr, value, force)

                # standard Attribute
                else:
                    attrString = '%s.%s' % (mnode, attr)  # mayaNode.attribute for cmds.get/set calls
                    # attrType=cmds.getAttr(attrString, type=True)  # the MayaNode attribute valueType
                    valueType = attributeDataType(value)  # DataType passed in to be set as Value
                    # log.debug('setting attribute type : %s to value : %s' % (attrType,value))

                    if attrType == 'string':
                        if valueType == 'string' or valueType == 'unicode':
                            cmds.setAttr(attrString, value, type='string')
                            if logging_is_debug():
                                log.debug("setAttr : %s : type : 'string' to value : %s" % (attr, value))
                            # return  # why was this returned here, by-passing the attr lock handling?
                        elif valueType == 'complex':
                            if logging_is_debug():
                                log.debug("setAttr : %s : type : 'complex_string' to value : %s" % (attr, self.__serializeComplex(value)))
                            cmds.setAttr(attrString, self.__serializeComplex(value), type='string')
                            # return  # why was this returned here, by-passing the attr lock handling?

                    elif attrType in ['double3', 'float3'] and valueType == 'complex':
                        try:
                            cmds.setAttr(attrString, value[0], value[1], value[2])
                        except ValueError, error:
                            raise ValueError(error)
                    elif attrType == 'doubleArray':
                        cmds.setAttr(attrString, value, type='doubleArray')
                    elif attrType == 'matrix':
                        cmds.setAttr(attrString, value, type='matrix')

                    # elif attrType=='TdataCompound': #ie blendShape weights = multi data or joint.minRotLimitEnable
                    #    pass
                    else:
                        try:
                            cmds.setAttr(attrString, value)
                        except StandardError, error:
                            log.debug('failed to setAttr %s - might be connected' % attrString)
                            raise StandardError(error)
                    if logging_is_debug():
                        log.debug("setAttr : %s : type : '%s' to value : %s" % (attr, attrType, value))
                if locked:
                    self.attrSetLocked(attr, True)
            else:
                log.debug('attr : %s doesnt exist on MayaNode > class attr only' % attr)

    def __getMessageAttr__(self, attr):
        '''
        separated func as it's the kind of thing that other classes may want to overload
        the behaviour of the returns etc

        .. note::
            added the 'sh' flag to the listConnections 22/11/16!
        '''
        msgLinks = cmds.listConnections('%s.%s' % (self.mNode, attr), destination=True, source=True, sh=True)
        if msgLinks:
            msgLinks = cmds.ls(msgLinks, l=True)
            if not cmds.attributeQuery(attr, node=self.mNode, m=True):  # singular message
                if isMetaNode(msgLinks[0]):
                    return MetaClass(msgLinks[0])
            for i, link in enumerate(msgLinks):
                if isMetaNode(link) or self._forceAsMeta:
                    msgLinks[i] = MetaClass(link)
                    log.debug('%s :  Connected data is an mClass Object, returning the Class' % link)
#             if not cmds.attributeQuery(attr, node=self.mNode, m=True):  # singular message
#                 #log.debug('getattr for multi-message attr: connections =[%s]' % ','.join(msgLinks))
#                 if isMetaNode(msgLinks[0]):
#                     return msgLinks[0]  # MetaClass(msgLinks[0])
            return msgLinks
        else:
            if logging_is_debug():
                log.debug('nothing connected to msgLink %s.%s' % (self.mNode, attr))
            return []

    def __getattribute__(self, attr):
        '''
        Overload the method to always return the MayaNode
        attribute if it's been serialized to the MayaNode
        '''

        data = None  # base attr value
        objectattr = False  # is the attr on this object instance?

        try:
            data = object.__getattribute__(self, attr)
            objectattr = True
        except:
            if logging_is_debug():
                log.debug('%s : attr not yet seen - function call probably generated by Maya directly' % attr)

        if data:
            if type(data) == types.MethodType:
                # log.debug('this is a function call %s' % attr)
                return data

        try:
            # private class attr only
            if attr in MetaClass.UNMANAGED:
                return data
            # stops recursion, do not getAttr on mNode here
            mNode = object.__getattribute__(self, "mNode")
            if not mNode or not cmds.objExists(mNode):
                return data  # object.__getattribute__(self, attr)
            else:
                # MayaNode processing - retrieve attrVals on the MayaNode
                try:
                    attrType = cmds.getAttr('%s.%s' % (mNode, attr), type=True)

                    # Message Link handling
                    # =====================
                    if attrType == 'message':
                        return self.__getMessageAttr__(attr)

                    # Standard Maya Attr handling
                    # ===========================
                    attrVal = cmds.getAttr('%s.%s' % (mNode, attr), silent=True)
                    if attrType == 'string':
                        # for string data we pass it via the JSON decoder such that
                        # complex data can be managed and returned correctly
                        try:
                            attrVal = self.__deserializeComplex(attrVal)
                            if type(attrVal) == dict:
                                return attrVal
                                # log.debug('Making LinkedDict')
                                # return self.LinkedDict([self,attr],attrVal)
                        except:
                            log.debug('string is not JSON deserializable')
                        return attrVal

                    elif attrType == 'double3' or attrType == 'float3':
                        return attrVal[0]  # return (x,x,x) not [(x,x,x)] as standard Maya does
                    return attrVal
                except:
                    if objectattr:
                        return data
                    else:
                        raise AttributeError('object instance has no attribute : %s' % attr)
        except MetaInstanceError, error:
            raise MetaInstanceError, ('MObject is no longer valid - Last good dag path was: "%s"' %
                                     object.__getattribute__(self, "_lastDagPath"))
        except StandardError, error:
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
        if len(data) > 32700:
            log.debug('Warning >> Length of string is over 16bit Maya Attr Template limit - lock this after setting it!')
        return json.dumps(data)

    def __deserializeComplex(self, data):
        '''
        Deserialize data from a JSON string back to it's original complex data
        '''
        # log.debug('deserializing data via JSON')
        if type(data) == unicode:
            return json.loads(str(data))
        return json.loads(data)

    @nodeLockManager
    def __delattr__(self, attr):
        try:
            if logging_is_debug():
                log.debug('attribute delete  : %s , %s' % (self, attr))
            object.__delattr__(self, attr)
            if self.hasAttr(attr):
                cmds.setAttr('%s.%s' % (self.mNode, attr), l=False)
                cmds.deleteAttr('%s.%s' % (self.mNode, attr))

        except StandardError, error:
            raise StandardError(error)

    def attrType(self, attr):
        '''
        return the api attr type
        '''
        return cmds.getAttr('%s.%s' % (self.mNode, attr), type=True)

    def hasAttr(self, attr):
        '''
        simple wrapper check for attrs on the mNode itself.
        Note this is not run in some of the core internal calls in this baseClass
        '''
        if self.isValidMObject():
            try:
                return self._MFnDependencyNode.hasAttribute(attr)
                # return OpenMaya.MFnDependencyNode(self.mNodeMObject).hasAttribute(attr)
            except:
                # return cmds.attributeQuery(attr, exists=True, node=self.mNode)
                return cmds.objExists('%s.%s' % (self.mNode, attr))

    def attrIsLocked(self, attr):
        '''
        check the attribute on the mNode to see if it's locked

        :param attr: attribute to test. Note that this now takes a list and if passed it returns the
            overall state, ie, if any of the attrs in the list are locked then it will return True, only
            if they're all unlocked do we return False
        '''
#         if hasattr(attr, '__iter__'):
        if not r9General.is_basestring(attr):
            locked = False
            for a in attr:
                if cmds.getAttr('%s.%s' % (self.mNode, a), l=True):
                    locked = True
                    break
            return locked
        return cmds.getAttr('%s.%s' % (self.mNode, attr), l=True)

    @nodeLockManager
    def attrSetLocked(self, attr, state):
        '''
        set the lockState of a given attr on the mNode

        :param attr: the attr to lock, this now also takes a list of attrs
        :param state: lock state
        '''
        try:
#             if hasattr(attr, '__iter__'):
            if r9General.is_basestring(attr):
                attr = [attr]
            if not self.isReferenced():
                for a in attr:
                    cmds.setAttr('%s.%s' % (self.mNode, a), l=state)
        except StandardError, error:
            log.debug(error)

    def attrBreakConnections(self, attr, source=True, dest=False):
        '''
        break all current connections to the given attr on the mNode

        :param attr: the attr to break
        :param source: True by default, break connections on the source side
        :param dest: False by default, break connections on the destination side
        '''
        if source:
            for con in cmds.listConnections('%s.%s' % (self.mNode, attr), p=True, s=True, d=False) or []:
                cmds.disconnectAttr(con, '%s.%s' % (self.mNode, attr))
        if dest:
            for con in cmds.listConnections('%s.%s' % (self.mNode, attr), p=True, s=False, d=True) or []:
                cmds.disconnectAttr('%s.%s' % (self.mNode, attr), con)

    @nodeLockManager
    def renameAttr(self, currentAttr, newName):
        '''
        wrap over cmds.renameAttr
        '''
        cmds.renameAttr('%s.%s' % (self.mNode, currentAttr), newName)

    @nodeLockManager
    def delAttr(self, attr, force=False):
        '''
        delete a given attr
        '''
        if self.hasAttr(attr):
            try:
                if force:
                    cmds.setAttr('%s.%s' % (self.mNode, attr), l=False)
                cmds.deleteAttr(self.mNode, at=attr)
            except StandardError, err:
                raise StandardError('Failed to delete given attrs : %s : %s' % (attr, err))

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
        added = False
        if attrType and attrType == 'enum' and 'enumName' not in kws:
            raise ValueError('enum attrType must be passed with "enumName" keyword in args')

        DataTypeKws = {'string': {'longName': attr, 'dt': 'string'},
                        'unicode': {'longName': attr, 'dt': 'string'},
                        'int': {'longName': attr, 'at': 'long'},
                        'long': {'longName': attr, 'at': 'long'},
                        'bool': {'longName': attr, 'at': 'bool'},
                        'float': {'longName': attr, 'at': 'double'},
                        'float3': {'longName': attr, 'at': 'float3'},
                        'double': {'longName': attr, 'at': 'double'},
                        'double3': {'longName': attr, 'at': 'double3'},
                        'doubleArray': {'longName': attr, 'dt': 'doubleArray'},
                        'enum': {'longName': attr, 'at': 'enum'},
                        'complex': {'longName': attr, 'dt': 'string'},
                        'message': {'longName': attr, 'at': 'message', 'm': True, 'im': True},
                        'messageSimple': {'longName': attr, 'at': 'message', 'm': False}}

        keyable = ['int', 'float', 'bool', 'enum', 'double3']
        addCmdEditFlags = ['min', 'minValue', 'max', 'maxValue', 'defaultValue', 'dv',
                             'softMinValue', 'smn', 'softMaxValue', 'smx', 'enumName']
        setCmdEditFlags = ['keyable', 'k', 'lock', 'l', 'channelBox', 'cb']

        addkwsToEdit = {}
        setKwsToEdit = {}
        if kws:
            for kw, v in kws.items():
                if kw in addCmdEditFlags:
                    addkwsToEdit[kw] = v
                elif kw in setCmdEditFlags:
                    setKwsToEdit[kw] = v

        # ATTR EXSISTS - EDIT CURRENT
        # ---------------------------
        if self.hasAttr(attr):
            # if attr exists do we force the value here?? NOOOO as I'm using this only
            # to ensure that when we initialize certain classes base attrs exist with certain properties.
            log.debug('"%s" :  Attr already exists on the Node' % attr)
            try:
                # allow some of the standard edit flags to be run even if the attr exists
                if kws:
                    if addkwsToEdit:
                        cmds.addAttr('%s.%s' % (self.mNode, attr), e=True, **addkwsToEdit)
                        if logging_is_debug():
                            log.debug('addAttr Edit flags run : %s = %s' % (attr, addkwsToEdit))
                    if setKwsToEdit:
                        try:
                            if not self.isReferenced():
                                cmds.setAttr('%s.%s' % (self.mNode, attr), **setKwsToEdit)
                                if logging_is_debug():
                                    log.debug('setAttr Edit flags run : %s = %s' % (attr, setKwsToEdit))
                        except:
                            log.debug("mNode is referenced and the setEditFlags are therefore invalid (lock, keyable, channelBox)")
            except:
                if self.isReferenced():
                    log.debug('%s : Trying to modify an attr on a reference node' % attr)
            return

        # ATTR IS NEW, CREATE IT
        # ----------------------
        else:
            try:
                if not attrType:
                    attrType = attributeDataType(value)
                DataTypeKws[attrType].update(addkwsToEdit)  # merge in **kws, allows you to pass in all the standard addAttr kws
                if logging_is_debug():
                    log.debug('addAttr : %s : valueType : %s > dataType kws: %s' % (attr, attrType, DataTypeKws[attrType]))
                cmds.addAttr(self.mNode, **DataTypeKws[attrType])

                if attrType == 'double3' or attrType == 'float3':
                    if attrType == 'double3':
                        subtype = 'double'
                    else:
                        subtype = 'float'
                    attr1 = '%sX' % attr
                    attr2 = '%sY' % attr
                    attr3 = '%sZ' % attr
                    cmds.addAttr(self.mNode, longName=attr1, at=subtype, parent=attr, **kws)
                    cmds.addAttr(self.mNode, longName=attr2, at=subtype, parent=attr, **kws)
                    cmds.addAttr(self.mNode, longName=attr3, at=subtype, parent=attr, **kws)
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
                    if logging_is_debug():
                        log.debug('setAttr Edit flags run : %s = %s' % (attr, setKwsToEdit))

                added = True
            except StandardError, error:
                raise StandardError(error)
        return added

    def listAttrsOfType(self, Type='message'):
        '''
        this is a fast method to list all attrs of type on the mNode

        >>> [attr for attr in cmds.listAttr(self.mNode) if cmds.getAttr('%s.%s' % (self.mNode,attr),type=True)=='message']

        Simply using the above cmds calls is DOG SLOW upto this which goes via the Api.
        TODO: expand the Type support here
        '''
        depNodeFn = OpenMaya.MFnDependencyNode(self.mNodeMObject)
        attrCount = depNodeFn.attributeCount()
        ret = []
        for i in range(attrCount):
            attrObject = depNodeFn.attribute(i)
            if Type:
                if Type == 'message':
                    if not attrObject.hasFn(OpenMaya.MFn.kMessageAttribute):
                        continue
            mPlug = depNodeFn.findPlug(attrObject)
            ret.append(mPlug.name().split('.')[1])
        return ret

    # Utity Functions
    # -------------------------------------------------------------------------------------

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
        currentName = self.shortName()
        cmds.rename(self.mNode, name)
        # UNDER TEST
        if renameChildLinks:
            plugs = cmds.listConnections(self.mNode, s=True, d=True, p=True)
            for plug in plugs:
                split = plug.split('.')
                attr = split[-1].split('[')[0]
                child = split[0]
                # print 'attr : ', attr, ' child : ', child, ' plug : ', plug, ' curName : ', currentName
                if attr == currentName:
                    try:
                        child = MetaClass(child)
                        child.renameAttr(attr, name)
                        if logging_is_debug():
                            log.debug('Renamed Child attr to match new mNode name : %s.%s' % (child.mNode, attr))
                    except:
                        if logging_is_debug():
                            log.debug('Failed to rename attr : %s on node : %s' % (attr, child.mNode))

    def delete(self):
        '''
        delete the mNode and this class instance

        Note that if you delete a 'network' node then by default
        Maya will delete connected child nodes unless they're wired.
        To prevent this set the self.lockState=True in your classes __init__
        '''
        global RED9_META_NODECACHE

        if cmds.lockNode(self.mNode, q=True):
            cmds.lockNode(self.mNode, lock=False)

        # clear the node from the cache
        removeFromCache([self])

        cmds.delete(self.mNode)
        del(self)

    def gatherInfo(self, level=0, *args, **kws):
        '''
        a generic gather function designed to be overloaded at the class level and used to
        collect specific information on the given class in a generic way. This is used by the
        r9Aninm format in Pro to collect key info on the system being saved against

        :param level: added here for the more robust checking that the rigging systems need
        '''
        return self.gatherInfo_mNode()
#         data = {}
#         data['mNode'] = self.mNode
#         data['mNodeID'] = self.mNodeID
#         data['mClass'] = self.mClass
#         data['mClassGrp'] = self.mClassGrp
#         data['mSystemRoot'] = self.mSystemRoot
#         data['lockState'] = self.lockState
#         return data

    def gatherInfo_mNode(self):
        '''
        this is now split like this because some times, when sub-classing, we still want to get
        back to this very low level gather call. In ProPack we overload gatherInfo() repeatedly
        but in certain instances, we still want to return just this base info for the mNode.
        This now keeps the info here very dynamic for all child classes no matter how deep they are!
        '''
        data = {}
        data['mNode'] = self.mNode
        data['mNodeID'] = self.mNodeID
        data['mClass'] = self.mClass
        data['mClassInheritance'] = str(self.__class__)
        data['mClassGrp'] = self.mClassGrp
        data['mSystemRoot'] = self.mSystemRoot
        data['lockState'] = self.lockState
        data['nodeType'] = cmds.nodeType(self.mNode)

        # simple attr management for some of the mRig base classes
        # added here so that we don't have to subclass these simple additions
        # although really that needs doing in future
        if self.hasAttr('systemType'):
            data['systemType'] = self.systemType
        if self.hasAttr('mirrorSide'):
            data['mirrorSide'] = self.mirrorSide
        return data

    @property
    def userinfo(self):
        '''
        a simple node descriptor so that sub-classes can have tracking or just user info blocks that
        animators can use as notation
        '''
        if self.hasAttr('userinfo_attr'):
            return self.userinfo_attr
        return ''

    @userinfo.setter
    def userinfo(self, text):
        if text:
            self.addAttr('userinfo_attr', attrType='string')
            self.userinfo_attr = text

    # Reference / Namespace Management Block
    # ---------------------------------------------------------------------------------

    def isReferenced(self):
        '''
        is node.mNode referenced?
        '''
        return cmds.referenceQuery(self.mNode, inr=True)

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

    def referenceGroup(self):
        '''
        :return: string name of reference group
        '''
        grp = cmds.listConnections('%s.associatedNode' % self.referenceNode())
        if grp:
            return grp[0]

    def nameSpace(self):
        '''
        This flag has been modified to return just the direct namespace
        of the node, not all nested namespaces if found. Now returns a string
        '''
        if self.isReferenced():
            try:
                return cmds.referenceQuery(self.mNode, ns=True).split(':')[-1]
            except:
                return ''
        ns = self.mNode.split('|')[-1].split(':')
        if len(ns) > 1:
            return ns[:-1][-1]
        return ''

    def nameSpaceFull(self, asList=False):
        '''
        the namespace call has been modified to only return the single
        direct namespace of a node, not the nested. This new func will
        return the namespace in it's entirity either as a list or a
        catenated string

        :param asList: either return the namespaces in a list or as a catenated string (default)
        '''
        ns = self.mNode.split('|')[-1].split(':')
        if len(ns) > 1:
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
    # ---------------------------------------------------------------------------------

    def _getNextArrayIndex(self, node, attr):
        '''
        get the next available index in a multiMessage array
        '''
        ind = cmds.getAttr('%s.%s' % (node, attr), multiIndices=True)
        if not ind:
            return 0
        else:
            for i in ind:
                if not cmds.listConnections('%s.%s[%i]' % (node, attr, i)):
                    return i
            return ind[-1] + 1

    def _upliftMessage(self, node, attr):
        '''
        if attr is a single, non-muliti message attr and it's already connected to something
        then uplift it to a multi, non-indexed managed message attr and cast any current connections
        to the newly created attr

        :param node: node with the attr on it
        :param attr: attr to uplift
        :rtype bool: if the attr is a multi or not
        '''
        if not cmds.attributeQuery(attr, node=node, exists=True):
            log.debug('%s : message attr does not exist' % attr)
            return

        if cmds.attributeQuery(attr, node=node, multi=True):
            log.debug('%s : message attr is already multi - abort uplift' % attr)
            return True

        cons = cmds.listConnections('%s.%s' % (node, attr), s=True, d=False, p=True)  # attr is already connected?
        if cons:
            log.debug('%s : attr is already connected - uplift to multi-message - im=True' % attr)
            cmds.deleteAttr('%s.%s' % (node, attr))  # delete current attr
            cmds.addAttr(node, longName=attr, at='message', m=True, im=True)
            # recast previous attr connections
            for con in cons:
                cmds.connectAttr(con, '%s.%s[%i]' % (node, attr, self._getNextArrayIndex(node, attr)))  # na=True)
            return True

    def isChildNode(self, node, attr=None, srcAttr=None):
        '''
        test if a node is already connected to the mNode via a given attr link.
        Why the wrap? well this gets over the issue of array index's in the connections

        cmds.isConnected('node.attr[0]','other.attr[0]')
        fails if simply asked:
        cmds.isConnected('node.attr',other.attr')
        '''
        if issubclass(type(node), MetaClass):
            node = node.mNode
        if attr:
            cons = cmds.ls(cmds.listConnections('%s.%s' % (self.mNode, attr), s=False, d=True, p=True), l=True)
        else:
            cons = cmds.ls(cmds.listConnections(self.mNode, s=False, d=True, p=True), l=True)
        if cons:
            for con in cons:
                if srcAttr:
                    if '%s.%s' % (cmds.ls(node, l=True)[0], srcAttr) in con:
                        return True
                else:
                    if '%s.' % cmds.ls(node, l=True)[0] in con:
                        return True
        return False

    @nodeLockManager
    def connectChildren(self, nodes, attr, srcAttr=None, cleanCurrent=False, force=True, allowIncest=True, srcSimple=False, **kws):
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
        :param srcSimple: By default when we wire children we expect arrays so both plugs on the src and dest
            side of the connection are index managed. This flag stops the index and uses a single simple wire on the
            srcAttr side of the plug ( the child )

        TODO: check the attr type, if attr exists and is a non-multi message then don't run the indexBlock
        '''

        # make sure we have the attr on the mNode
        self.addAttr(attr, attrType='message')

        if not issubclass(type(nodes), list):
            nodes = [nodes]
        if cleanCurrent:
            self.__disconnectCurrentAttrPlugs(attr)  # disconnect/cleanup current plugs to this attr
        if not srcAttr:
            srcAttr = self.mNodeID  # attr on the nodes source side for the child connection
        if not nodes:
            # this allows 'None' to be passed into the set attr calls and in turn, allow
            # self.mymessagelink=None to clear all current connections
            return

        for node in nodes:
            ismeta = False
            if isMetaNode(node):
                ismeta = True
                if not issubclass(type(node), MetaClass):  # allows you to pass in an metaClass
                    MetaClass(node).addAttr(srcAttr, attrType='message')
                else:
                    node.addAttr(srcAttr, attrType='message')
                    node = node.mNode
            # elif not cmds.attributeQuery(srcAttr, exists=True, node=node):
            elif not cmds.objExists('%s.%s' % (node, srcAttr)):
                if allowIncest:
                    MetaClass(node).addAttr(srcAttr, attrType='message')
                else:
                    cmds.addAttr(node, longName=srcAttr, at='message', m=True, im=False)
            try:
                # also we need to add the self.allowIncest flag to trigger managed message links like this.
                if not self.isChildNode(node, attr, srcAttr):
                    try:
                        if ismeta or allowIncest:
                            if ismeta:
                                if logging_is_debug():
                                    log.debug('connecting MetaData nodes via indexes :  %s.%s >> %s.%s' % (self.mNode, attr, node, srcAttr))
                            elif allowIncest:
                                if logging_is_debug():
                                    log.debug('connecting Standard Maya nodes via indexes : %s.%s >> %s.%s' % (self.mNode, attr, node, srcAttr))
                            if not srcSimple:
                                cmds.connectAttr('%s.%s[%i]' % (self.mNode, attr, self._getNextArrayIndex(self.mNode, attr)),
                                         '%s.%s[%i]' % (node, srcAttr, self._getNextArrayIndex(node, srcAttr)), f=force)
                            else:
                                cmds.connectAttr('%s.%s[%i]' % (self.mNode, attr, self._getNextArrayIndex(self.mNode, attr)),
                                         '%s.%s' % (node, srcAttr), f=force)
                        else:
                            if logging_is_debug():
                                log.debug('connecting %s.%s >> %s.%s' % (self.mNode, attr, node, srcAttr))
                            cmds.connectAttr('%s.%s' % (self.mNode, attr), '%s.%s' % (node, srcAttr), f=force)
                    except:
                        # If the add was originally a messageSimple, then this exception is a
                        # back-up for the previous behaviour
                        cmds.connectAttr('%s.%s' % (self.mNode, attr), '%s.%s' % (node, srcAttr), f=force)
                else:
                    raise StandardError('"%s" is already connected to metaNode "%s"' % (node, self.mNode))
            except StandardError, error:
                log.warning(error)

#     @nodeLockManager
#     def connectChildren(self, nodes, attr, srcAttr=None, cleanCurrent=False, force=True, **kws):
#         '''
#         Thinking of depricating the original connectChildren call as the multi-message handling
#         was just getting too clumsy to manage
#         '''
#         if cleanCurrent:
#             self.__disconnectCurrentAttrPlugs(attr)  # disconnect/cleanup current plugs to this attr
#         for node in nodes:
#             self.connectChild(node, attr=attr, srcAttr=srcAttr, cleanCurrent=False, force=force, allow_multi=True, **kws)

    @nodeLockManager
    def connectChild(self, node, attr, srcAttr=None, cleanCurrent=True, force=True, allow_multi=False, **kws):
        '''
        Fast method of connecting a node to the mNode via a message attr link. This call
        generates a NONE-MULTI message on both sides of the connection and is designed
        for simple parent child relationships.

        .. note::
            this call by default manages the attr to only ONE CHILD to avoid this use cleanCurrent=False
        :param node: Maya node to connect to this mNode
        :param attr: Name for the message attribute
        :param srcAttr: If given this becomes the attr on the child node which connects it
                        to self.mNode. If NOT given this attr is set to self.mNodeID
        :param cleanCurrent: Disconnect and clean any currently connected nodes to the attr on self.
                        Note this is operating on the mNode side of the connection, removing
                        any currently connected nodes to this attr prior to making the new ones
        :param force: Maya's default connectAttr 'force' flag, if the srcAttr is already connected
                        to another node force the connection to the new attr
        :param allow_multi: allows the same node to connect back to this mNode under multiple wires
            default behaviour is to only let a single wire from an mNode to a child

        TODO: do we move the cleanCurrent to the end so that if the connect fails you're not left
        with a half run setup?
        '''
        # make sure we have the attr on the mNode, if we already have a MULIT-message
        # should we throw a warning here???
        self.addAttr(attr, attrType='messageSimple')
        src_is_multi = False
        try:
            if cleanCurrent:
                self.__disconnectCurrentAttrPlugs(attr)  # disconnect/cleanup current plugs to this attr
            if not srcAttr:
                srcAttr = self.mNodeID  # attr on the nodes source side for the child connection
            if not node:
                # this allows 'None' to be passed into the set attr calls and in turn, allow
                # self.mymessagelink=None to clear all current connections
                return

            # add and manage the attr on the child node
            if isMetaNode(node):
                if not issubclass(type(node), MetaClass):
                    MetaClass(node).addAttr(srcAttr, attrType='messageSimple')
                else:
                    node.addAttr(srcAttr, attrType='messageSimple')
                    node = node.mNode
            # elif not cmds.attributeQuery(srcAttr, exists=True, node=node):
            elif not cmds.objExists('%s.%s' % (node, srcAttr)):
                cmds.addAttr(node, longName=srcAttr, at='message', m=False)

            # uplift to multi-message index managed if needed
            if allow_multi:
                src_is_multi = self._upliftMessage(node, srcAttr)  # uplift the message to a multi if needed
            # else:
            #    src_is_multi=cmds.attributeQuery(srcAttr, node=node, multi=True)
            if not self.isChildNode(node, attr, srcAttr):
                try:
                    log.debug('connecting child via multi-message')
                    cmds.connectAttr('%s.%s' % (self.mNode, attr),
                                     '%s.%s[%i]' % (node, srcAttr, self._getNextArrayIndex(node, srcAttr)), f=force)
                except:
                    log.debug('connecting child via single-message')
                    cmds.connectAttr('%s.%s' % (self.mNode, attr), '%s.%s' % (node, srcAttr), f=force)
            else:
                raise StandardError('%s is already connected to metaNode' % node)
        except StandardError, error:
            log.warning(error)

    @nodeLockManager
    def connectParent(self, node, attr, srcAttr=None, cleanCurrent=True, **kws):
        '''
        Fast method of connecting message links to the mNode as parents
        :param nodes: Maya nodes to connect to this mNode
        :param attr: Name for the message attribute on the PARENT!
        :param srcAttr: If given this becomes the attr on the node which connects it
                        to the parent. If NOT given this attr is set to parents shortName
        :param cleanCurrent: Exposed from the connectChild code which is basically what this is running in reverse

        TODO: Modify so if a metaClass is passed in use it's addAttr cmd so the new
        attr is registered in the class given

        TODO: Manage connection Index like the connectChildren call does?
        '''
        if not issubclass(type(node), MetaClass):
            node = MetaClass(node)
        if not srcAttr:
            srcAttr = node.shortName()
        try:
            node.connectChild(self, attr, srcAttr, cleanCurrent=cleanCurrent)
        except StandardError, error:
                log.warning(error)

    @nodeLockManager
    def __disconnectCurrentAttrPlugs(self, attr, deleteSourcePlug=True, deleteDestPlug=False, *args, **kws):
        '''
        from a given attr on the mNode disconnect any current connections and
        clean up the plugs by deleting the existing attributes. Note the attr must be of type message
        '''
        currentConnects = self.__getattribute__(attr)
        if currentConnects:
            if not isinstance(currentConnects, list):
                currentConnects = [currentConnects]
            for connection in currentConnects:
                try:
                    if logging_is_debug():
                        log.debug('Disconnecting %s.%s >> from : %s' % (self.mNode, attr, connection))
                    self.disconnectChild(connection, attr=attr, deleteSourcePlug=deleteSourcePlug, deleteDestPlug=deleteDestPlug)
                except:
                    log.warning('Failed to disconnect current message link')

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
        sPlug = None
        dPlug = None
        sPlugMeta = None
        returnData = []
        searchConnection = '%s.' % self.mNode.split('|')[-1]
        if attr:
            searchConnection = '%s.%s' % (self.mNode.split('|')[-1], attr)
        if isMetaNode(node):  # and issubclass(type(node), MetaClass):
            sPlugMeta = node
            node = node.mNode
        cons = cmds.listConnections(node, s=True, d=False, p=True, c=True)

        if not cons:
            raise StandardError('%s is not connected to the mNode %s' % (node, self.mNode))

        for sPlug, dPlug in zip(cons[0::2], cons[1::2]):
            if logging_is_debug():
                log.debug('attr Connection inspected : %s << %s' % (sPlug, dPlug))
            # print 'searchCon : ', searchConnection
            # print 'dPlug : ', dPlug
            if (attr and searchConnection == dPlug.split('[')[0]) or (not attr and searchConnection in dPlug):
                if logging_is_debug():
                    log.debug('Disconnecting %s >> %s as %s found in dPlug' % (dPlug, sPlug, searchConnection))
                cmds.disconnectAttr(dPlug, sPlug)
                returnData.append((dPlug, sPlug))

        if deleteSourcePlug:  # child node
            try:
                allowDelete = True
                attr = sPlug.split('[')[0]  # split any multi-indexing from the plug ie node.attr[0]
                if cmds.listConnections(attr):
                    allowDelete = False
                    if logging_is_debug():
                        log.debug('sourceAttr connections remaining: %s' %
                                  ','.join(cmds.listConnections(attr)))
                if allowDelete:
                    log.debug('Deleting deleteSourcePlug Attr %s' % (attr))
                    if sPlugMeta:
                        delattr(sPlugMeta, attr.split('.')[-1])
                    else:
                        cmds.deleteAttr(attr)
                else:
                    log.debug('deleteSourcePlug attr aborted as node still has connections')
            except StandardError, error:
                log.warning('Failed to Remove mNode Connection Attr')
                log.debug(error)
        if deleteDestPlug:  # self
            try:
                allowDelete = True
                attr = dPlug.split('[')[0]  # split any multi-indexing from the plug ie node.attr[0]
                if cmds.listConnections(attr):
                    allowDelete = False
                    if logging_is_debug():
                        log.debug('sourceAttr connections remaining: %s' %
                                  ','.join(cmds.listConnections(attr)))
                if allowDelete:
                    if logging_is_debug():
                        log.debug('Deleting deleteDestPlug Attr %s' % (attr))
                    delattr(self, attr.split('.')[-1])
                    # cmds.deleteAttr(attr)
                else:
                    log.debug('deleteDestPlug attr aborted as node still has connections')
            except StandardError, error:
                log.warning('Failed to Remove Node Connection Attr')
                log.debug(error)

        return returnData

    # get Nodes Management Block
    # ---------------------------------------------------------------------------------

    def addChildMetaNode(self, mClass, attr, srcAttr=None, nodeName=None, **kws):
        '''
        Generic call to add a MetaNode as a Child of self

        :param mClass: mClass to generate, given as a valid key to the
            RED9_META_REGISTERY ie 'MetaRig' OR a class object, ie r9Meta.MetaRig
        :param attr: message attribute to wire the new node too
        :param name: optional name to give the new name
        '''
        key = mTypesToRegistryKey(mClass)[0]
        if key in RED9_META_REGISTERY:
            childClass = RED9_META_REGISTERY[key]
            mChild = childClass(name=nodeName, **kws)
            self.connectChild(mChild, attr, srcAttr=srcAttr, **kws)
            return mChild

    @r9General.Timer
    def getChildMetaNodes(self, walk=False, mAttrs=None, stepover=False, currentSystem=False, **kws):
        '''
        Find any connected Child MetaNodes to this mNode.

        :param walk: walk the connected network and return ALL children connected in the tree
        :param mAttrs: only return connected nodes that pass the given attribute filter
        :param stepover: if you're passing in 'mTypes' or 'mInstances' flags then this dictates if
            we continue to walk down a tree if it's parent didn't match the given type, default is False
            which will abort a tree who's parent didn't match. With stepover=True we simply stepover
            that node and continue down all child nodes
        :param currentSystem: if True we check for the mSystemRoot attr (bool) on mNodes and if set, we skip
            the node and all childnodes from that node. Why?? The mSystsmRoot attr is a marker to denote the
            root of a given mRig system, by respecting this we clamp searches to the current system and prevent
            walking into the connected child sub-system. Primarily used in ProPack to stop facial nodes being
            returned and processed as part of the connected body rig.

        .. note::
            mAttrs is only searching attrs on the mNodes themselves, not all children
            and although there is no mTypes flag, you can use mAttrs to get childnodes of type
            by going getChildMetaNodes(mAttrs='mClass=MetaRig')

        .. note::
            Because the **kws are passed directly to the getConnectedMetaNodes func, it will
            also take ALL of that functions **kws functionality in the initial search:
            mTypes=[], mInstances=[], mAttrs=None, dataType='mClass', skipTypes=[], skipInstances=[]
        '''
        if not walk:
            children = getConnectedMetaNodes(self.mNode, source=False, destination=True, mAttrs=mAttrs, dataType='mClass', **kws)
            if currentSystem:
                for child in children:
                    if child.hasAttr('mSystemRoot') and child.mSystemRoot:
                        print('skipping new Systems - preventing walking into child mRig systems : %s' % child)
                        children.remove(child)
            return children
        else:
            metaNodes = []
            if not any(['mTypes' in kws, 'mInstances' in kws, mAttrs]):
                # no flags passed so the stepover flag is redundant
                stepover = False
            if stepover:
                # if we're stepping over unmatched children then we remove the kws and deal with the match later
                children = getConnectedMetaNodes(self.mNode, source=False, destination=True, dataType='unicode')  # , **kws)
            else:
                children = getConnectedMetaNodes(self.mNode, source=False, destination=True, mAttrs=mAttrs, dataType='unicode', **kws)

            if children:
                runaways = 0
                depth = 0
                processed = []
                extendedChildren = []
                while children and runaways <= 1000:
                    for child in children:
                        if currentSystem:
                            if cmds.objExists('%s.mSystemRoot' % child) and cmds.getAttr('%s.mSystemRoot' % child):
                                log.debug('skipping new System - preventing walking into child mRig systems : %s' % child)
                                children.remove(child)
                                continue
                        mNode = child
                        if mNode not in processed:
                            metaNodes.append(child)
                        else:
                            # print('skipping as node already processed : %s' % mNode)
                            children.remove(child)
                            continue
                            # log.info('mNode added to metaNodes : %s' % mNode)
                        children.remove(child)
                        processed.append(mNode)
                        # log.info( 'connections too : %s' % mNode)
                        if stepover:
                            # if we're stepping over unmatched children then we remove the kws and deal with the match later
                            extendedChildren.extend(getConnectedMetaNodes(mNode, source=False, destination=True, dataType='unicode'))  # , **kws))
                        else:
                            extendedChildren.extend(getConnectedMetaNodes(mNode, source=False, destination=True, mAttrs=mAttrs, dataType='unicode', **kws))
                        # log.info('left to process : %s' % ','.join([c.mNode for c in children]))
                        if not children:
                            if extendedChildren:
                                log.debug('Child MetaNode depth extended %i' % depth)
                                # log.debug('Extended Depth child List: %s' % ','.join([c.mNode for c in extendedChildren]))
                                children.extend(extendedChildren)
                                extendedChildren = []
                                depth += 1
                        runaways += 1

                # at this point we're still dealing with unicode nodes
                childmNodes = [MetaClass(node) for node in metaNodes if not node == self.mNode]

                typematched = []
                if stepover:
                    for node in childmNodes:
                        if 'mTypes' in kws and node not in typematched:
                            if isMetaNode(node, kws['mTypes']):
                                log.debug('getChildMetaNodes : mTypes matched : %s' % node)
                                typematched.append(node)
                        if 'mInstances' in kws and node not in typematched:
                            if isMetaNodeInherited(node, kws['mInstances']):
                                log.debug('getChildMetaNodes : mInstances matched : %s' % node)
                                typematched.append(node)
                        if mAttrs and node not in typematched:
                            if r9Core.FilterNode().lsSearchAttributes(mAttrs, nodes=[node.mNode]):
                                log.debug('getChildMetaNodes : mAttrs matched : %s' % node)
                                typematched.append(node)
                    return typematched
                else:
                    return childmNodes
        return []

    def getChildSystemRoots(self):
        '''
        return all child MetaNodes that have the mSystemRoot checkbox set. This is used to denote a child
        MSystem in it's own right. Usually used in ProPack to denote a new child MetaRig, ie, facial system
        connected as a child of a mRig body system
        '''
        return self.getChildMetaNodes(walk=True, mAttrs=['mSystemRoot=True'])

    def getParentMetaNode(self, **kws):
        '''
        Find any connected Parent MetaNode to this mNode

        .. note::
            Because the **kws are passed directly to the getConnectedMetaNods func, it will
            also take ALL of that functions kws if passed as a kws dict
            mTypes=[], mInstances=[], mAttrs=None, dataType='mClass', nTypes=None, skipTypes=[], skipInstances=[]

        TODO: implement a walk here to go upstream
        '''
        mNodes = getConnectedMetaNodes(self.mNode, source=True, destination=False, **kws)
        if mNodes:
            return mNodes[0]

    @r9General.Timer
    def getChildren(self, walk=True, mAttrs=None, cAttrs=[], nAttrs=[], asMeta=False, asMap=False, plugsOnly=False, skip_cAttrs=[], **kws):
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
        :param plugsOnly: only with asMap flag, this truncates the return to [plugAttr, [nodes]]
        :param skip_cAttrs: if given these cAttrs will be ignored in the returned data

        .. note::
            mAttrs is only searching attrs on the mNodes themselves, not the children
            cAttrs is searching the connection attr names from the mNodes, uses the cmds.listAttr 'st' flag

        .. note::
            Because the **kws are passed directly to the getConnectedMetaNodes func via the getChildMetaNodes call,
            it will also take ALL of that functions **kws functionality in the initial search:
            mTypes=[], mInstances=[], mAttrs=None, dataType='mClass', skipTypes=[], skipInstances=[]
        '''
        childMetaNodes = [self]
        children = []
        attrMapData = {}
        if walk:
            childMetaNodes.extend([node for node in self.getChildMetaNodes(walk=True, mAttrs=mAttrs, **kws)])
        for node in childMetaNodes:
            if logging_is_debug():
                log.debug('MetaNode getChildren : %s >> %s' % (type(node), node.mNode))
            attrs = cmds.listAttr(node.mNode, ud=True, st=cAttrs)
            if attrs:
                for attr in attrs:
                    if skip_cAttrs and attr in skip_cAttrs:
                        continue
                    if cmds.getAttr('%s.%s' % (node.mNode, attr), type=True) == 'message':
                        msgLinked = cmds.listConnections('%s.%s' % (node.mNode, attr), destination=True, source=False)
                        if msgLinked:
                            if not nAttrs:
                                msgLinked = cmds.ls(msgLinked, l=True)  # cast to longNames!
                                if not asMap:
                                    children.extend(msgLinked)
                                else:
                                    if not plugsOnly:
                                        attrMapData['%s.%s' % (node.mNode, attr)] = msgLinked
                                    else:
                                        attrMapData[attr] = msgLinked
                                    # attrMapData['%s.%s' % (node.mNode, attr)] = msgLinked
                            else:
                                for linkedNode in msgLinked:
                                    for attr in nAttrs:
                                        # if cmds.attributeQuery(attr, exists=True, node=linkedNode):
                                        if cmds.objExists('%s.%s' % (linkedNode, attr)):
                                            linkedNode = cmds.ls(linkedNode, l=True)  # cast to longNames!
                                            # children.extend(linkedNode)
                                            if not asMap:
                                                children.extend(linkedNode)
                                            else:
                                                if not plugsOnly:
                                                    attrMapData['%s.%s' % (node.mNode, attr)] = linkedNode
                                                else:
                                                    if attr not in attrMapData:
                                                        attrMapData[attr] = []
                                                    attrMapData[attr].extend(linkedNode)
                                            break
                                            break
            else:
                if logging_is_debug():
                    log.debug('no matching attrs : %s found on node %s' % (cAttrs, node))
        if self._forceAsMeta or asMeta and not asMap:
            return [MetaClass(node) for node in children]
        if asMap:
            return attrMapData
        return children

    @staticmethod
    def getNodeConnectionMetaDataMap(node, mTypes=[]):  # toself=False, allplugs=False):
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
        if type(node) == list:
            raise StandardError("getNodeConnectionMetaDataMap: node must be a single node, not an list")
        mNodes = {}
        # why not use the r9Meta.getConnectedMetaNodes ?? > well here we're using
        # the c=True flag to get both plugs back in one go to process later
        connections = []
        for nType in getMClassNodeTypes():
            con = cmds.listConnections(node, type=nType, s=True, d=False, c=True, p=True)
            if con:
                connections.extend(con)
        if not connections:
            return connections

        if logging_is_debug():  # debug
            log.debug('%s : connectionMap : %s' % (node.split('|')[-1].split(':')[-1], connections[1::2]))

        for con in connections[1::2]:
            data = con.split('.')  # attr
            if isMetaNode(data[0], mTypes=mTypes):
                mNodes['metaAttr'] = data[1]
                try:
                    mNodes['metaNodeID'] = cmds.getAttr('%s.mNodeID' % data[0])
                except:
                    mNodes['metaNodeID'] = node.split(':')[-1].split('|')[-1]
                return mNodes
            elif mTypes:
                continue
            # if not mTypes:  # if not mTypes passed bail the loop and return the first connection
            #    return mNodes
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
        log.info('getNodeConnetionAttr will be depricated soon!!!!')
        for con in cmds.listConnections(node, s=True, d=False, p=True) or []:
            if self.mNode in con.split('.')[0]:
                return con.split('.')[1]

    def getNodeConnections(self, node, filters=[], bothplugs=False):
        '''
        really light wrapper, designed to return all connections
        between a given node and the mNode

        :param node: node to test connection attr for
        :param filters: filter string to match for the returns
        :param bothplugsL if True we return a list of tuples
        '''
        cons = []
        if not bothplugs:
            for attr in cmds.listConnections(node, s=True, d=False, p=True) or []:
                if self.mNode in attr.split('.')[0]:
                    if filters:
                        for flt in filters:
                            if flt in attr.split('.')[1]:
                                cons.append(attr.split('.')[1])
                    else:
                        cons.append(attr.split('.')[1])
        else:
            plugs = cmds.listConnections(node, s=True, d=False, c=True, p=True) or []
            if plugs:
                for srcattr, attr in zip(plugs[0::2], plugs[1::2]):
                    if self.mNode in attr.split('.')[0]:
                        if filters:
                            for flt in filters:
                                if flt in attr.split('.')[1]:
                                    cons.append([attr.split('.')[1], srcattr.split('.')[1]])
                        else:
                            cons.append([attr.split('.')[1], srcattr.split('.')[1]])
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
        searchNode = cmds.ls(sl=True)[0]
    mRig = getConnectedMetaSystemRoot(searchNode)
    if not mRig:
        raise StandardError('No root MetaData system node found from given searchNode')
    mNodes = []
    mNodes.append(mRig)
    mNodes.extend(mRig.getChildMetaNodes(walk=True))
    mNodes.reverse()

    for a in mNodes:
        print(a)

    for metaChild in mNodes:
        for child in metaChild.getChildren(walk=False):
            metaChild.disconnectChild(child)
            r9Anim.MirrorHierarchy().deleteMirrorIDs(child)
            # For the time being I'm adding the OLD mirror markers to this
            # call for the sake of cleanup on old rigs
            if cmds.attributeQuery('mirrorSide', exists=True, node=child):
                cmds.deleteAttr('%s.mirrorSide' % child)
            if cmds.attributeQuery('mirrorIndex', exists=True, node=child):
                cmds.deleteAttr('%s.mirrorIndex' % child)
            if cmds.attributeQuery('mirrorAxis', exists=True, node=child):
                cmds.deleteAttr('%s.mirrorAxis' % child)
        metaChild.delete()


class MetaRig(MetaClass):
    '''
    Sub-class of Meta used as the back-bone of our internal rigging
    systems. This is the core of how we hook all our tools to meta
    in a seamless manner and bind some core functionality.
    '''
    def __init__(self, *args, **kws):
        '''
        :param name: name of the node and in this case, the RigSystem itself
        '''
        super(MetaRig, self).__init__(*args, **kws)
        self._Timecode = None  # Timecode class handler

        if self.cached:
            log.debug('CACHE : Aborting __init__ on pre-cached %s Object' % self.__class__)
            return

        # note these are attrs on the mNode itself so we need to be careful when setting
        # them to locked if this node is referenced.
        self.mClassGrp = 'MetaRig'  # get the Grp code marking this as a SystemBase
        self.mSystemRoot = True  # set this node to be a system root if True

        # general management vars
        self.CTRL_Prefix = 'CTRL'  # prefix for all connected CTRL_ links added
        self.lockState = True  # now set in __bindData__ using the semi-private var self._lockState
        self.parentSwitchAttr = ['parent']  # attr used for parentSwitching
        self.MirrorClass = None  # capital as this binds to the MirrorClass directly
        # self.poseSkippedAttrs = []    # attributes which are to be IGNORED by the posesaver, set by you for your needs!
        self.filterSettings = None  # used in the settings func

    def __bindData__(self):
        # self._lockState=True        # set the internal lockstate
        self.addAttr('version', 1.0)  # internal version of the rig, used by pro and bound here as a generic version ID
        self.addAttr('rigType', '')   # type of the rig system 'biped', 'quad' etc
        self.addAttr('scaleSystem', attrType='messageSimple')
        self.addAttr('timecode_node', attrType='messageSimple')

        # Vital wires used by both StudioPack and Pro
        self.addAttr('renderMeshes', attrType='message')  # used to ID all meshes that are part of this rig system
        self.addAttr('exportSkeletonRoot', attrType='messageSimple')  # used to ID the skeleton root for exporters and code

    def gatherInfo(self, level=0, encode_objects=False, *args, **kws):
        '''
        gather key info on this system

        :param encode_objects: if True we should encode / stringify all objects for safe json conversion
        '''
        data = {}
        data['mClass'] = super(MetaRig, self).gatherInfo(level=level, encode_objects=encode_objects, *args, **kws)
        data['filepath'] = cmds.file(q=True, sn=True)
        if self.hasAttr('version'):
            data['version'] = self.version
        if self.hasAttr('rigType'):
            data['rigType'] = self.rigType
        if self.hasAttr('exportSkeletonRoot'):
            data['exportSkeletonRoot'] = self.exportSkeletonRoot
        if self.hasAttr('timecode_node'):
            data['timecode_node'] = self.timecode_node
        if self.isReferenced():
            data['namespace'] = self.nameSpace()
            data['namespace_full'] = self.nameSpaceFull()
            data['referenced_rigPath'] = self.referencePath()
            data['referenced_grp'] = self.referenceGroup()

        data['CTRL_Prefix'] = self.CTRL_Prefix
        try:
            data['Ctrl_Main'] = self.ctrl_main
        except:
            log.warning('"ctrl_main" : is NOT wired correctly!')
        return data

    def isValid(self):
        '''
        simple check to see if this definition is still valid and wired to
        controllers and not just to empty subSystems as is the case if you
        were to delete all the dag nodes in a rig, leaving the MetaRig
        structure in-tact but useless
        '''
        if not super(MetaRig, self).isValid():
            return False
        if not self.getChildren():
            return False
        return True

    def delete(self, full=True):
        '''
        full delete and clean of a rig system and network
        '''
        mNodes = []
        mNodes.append(self)

        childnodes = self.getChildMetaNodes(walk=True)
        if childnodes:
            mNodes.extend(childnodes)
            mNodes.reverse()

        for a in mNodes:
            print('nodes to delete : ', a)

        for mNode in mNodes:
            try:
                for child in mNode.getChildren(walk=False):
                    mNode.disconnectChild(child)
                    # print 'disconnecting child : ', child
                # print 'deleting mNode: ', mNode
                delete_mNode(mNode)
            except:
                # print 'deleting mNode failed - may have been removed: ', mNode
                pass

    @property
    def ctrl_main(self):
        '''
        why wrap, because when we subclass, IF we've modified the CRTL_Prefix then we
        can't rely on the default CTRL_Main[0] wire, so we wrap it with the current
        instances self.CTRL_Prefix
        '''
        if self.hasAttr('%s_Main' % self.CTRL_Prefix):
            try:
                return getattr(self, '%s_Main' % self.CTRL_Prefix)[0]
            except:
                log.warning('CTRL_Main was not connected')

        log.info('mRig has no "CTRL_Main" bound')

    @property
    def ctrl_locomotion(self):
        '''
        why wrap, because when we subclass, IF we've modified the CRTL_Prefix then we
        can't rely on the default CTRL_LocomotionRoot[0] wire, so we wrap it with the current
        instances self.CTRL_Prefix

        .. note::
            LocomotionRoot is a controller designated as the "locomotion root" node, for games this
            generally is the characters global motion pushed to a controller which directly controls
            the skeleton root / reference joint
        '''
        if self.hasAttr('%s_LocomotionRoot' % self.CTRL_Prefix):
            try:
                return getattr(self, '%s_LocomotionRoot' % self.CTRL_Prefix)[0]
            except:
                log.warning('CTRL_LocomotionRoot was not connected')

        log.info('mRig has no "CTRL_LocomotionRoot" bound')

    @property
    def characterSet(self):
        '''
        return the first connected characterSet found to children
        '''
        for node in self.getChildren(walk=True):
            chSet = cmds.listConnections(node, type='character')
            if chSet:
                return chSet[0]

    def addGenericCtrls(self, nodes):
        '''
        Pass in a list of objects to become generic, non specific
        controllers for a given setup. These are all connected to the same slot
        so don't have the search capability that the funct below gives
        '''
        self.connectChildren(nodes, 'RigCtrls')

    def addRigCtrl(self, node, ctrType=None, mirrorData=None, boundData=None, namereplace=[]):
        '''
        Add a single CTRL of managed type as a child of this mRig.

        :param node: Maya node to add
        :param ctrType: Attr name to assign this too, if not given we take the short nodename
        :param mirrorData: {side:'Left', slot:int, axis:'translateX,rotateY,rotateZ'..}
        :param boundData: {} any additional attrData, set on the given node as attrs
        :param namereplace: [] if given we apply node.replace(namereplace[0], namereplace[1]) before making the wire

        .. note::
            | mirrorData[slot] must NOT == 0 as it'll be handled as not set by the core.
            | ctrType >> 'Main' is the equivalent of the RootNode in the FilterNode calls.

        TODO: allow the mirror block to include an offset so that if you need to inverse AND offset
        by 180 to get left and right working you can still do so.
        '''
        # import Red9_AnimationUtils as r9Anim  # lazy load to avoid cyclic imports

        if isinstance(node, list):
            raise StandardError('node must be a single Maya Object')

        if not ctrType:
            ctrType = r9Core.nodeNameStrip(node)
        if namereplace:
            ctrType.replace(namereplace[0], namereplace[1])

        self.connectChild(node, '%s_%s' % (self.CTRL_Prefix, ctrType))
        if mirrorData:
            mirror = r9Anim.MirrorHierarchy()
            axis = None
            if 'axis' in mirrorData:
                axis = mirrorData['axis']
            mirror.setMirrorIDs(node,
                                side=mirrorData['side'],
                                slot=mirrorData['slot'],
                                axis=axis)
        if boundData:
            if issubclass(type(boundData), dict):
                for key, value in boundData.iteritems():
                    if logging_is_debug():
                        log.debug('Adding boundData to node : %s:%s' % (key, value))
                    MetaClass(node).addAttr(key, value=value)

    def getRigCtrls(self, walk=False, mAttrs=None):
        '''
        Depricated Code - use getChildren call now
        '''
        return self.getChildren(walk, mAttrs)

    def getChildren(self, walk=True, mAttrs=None, cAttrs=[], nAttrs=[], asMeta=False, asMap=False,
                    plugsOnly=False, incFacial=False, baseBehaviour=False, skip_cAttrs=[], **kws):
        '''
        Massively important bit of code, this is used by most bits of code
        to find the child controllers linked to this metaRig instance.

        :param walk: walk all subMeta connections and include all their children too
        :param mAttrs: only search connected mNodes that pass the given attribute filter (attr is at the metaSystems level)
        :param cAttrs: only pass connected children whos connection to the mNode matches the given attr (accepts wildcards)
        :param nAttrs: search returned MayaNodes for given set of attrs and only return matched nodes
        :param asMeta: return instantiated mNodes regardless of type
        :param asMap: return the data as a map such that {mNode.plugAttr:[nodes], mNode.plugAttr:[nodes]}
        :param plugsOnly: only with asMap flag, this truncates the return to {plugAttr:[nodes]}
        :param incFacial: if we have a facial system linked include it's children in the return (uses the getFacialSystem to id the facial node)
        :param baseBehaviour: if True we revert the CTRL_Prefix logic such that the return won't be clamped to just controllers
        :param skip_cAttrs: if given these connection attrs will be ignored in the returned data

        .. note::
            MetaRig getChildren has overloads adding the CTRL_Prefix to the cAttrs so that
            the return is just the controllers in the rig. It also now has additional logic
            to add any FacialCore system children by adding it's internal CTRL_Prefix to the list

        .. note::
            Because the **kws are passed directly to the getConnectedMetaNodes func via the getChildMetaNodes call,
            it will also take ALL of that functions **kws functionality in the initial search:
            source=True, destination=True, mTypes=[], mInstances=[], mAttrs=None, dataType='mClass', skipTypes=[], skipInstances=[]
        '''
        if not cAttrs and not baseBehaviour:
            cAttrs = ['RigCtrls', '%s_*' % self.CTRL_Prefix]
            if incFacial:
                facialSystem = self.getFacialSystem()
                if facialSystem:
                    cAttrs.append('%s_*' % facialSystem.CTRL_Prefix)

        return super(MetaRig, self).getChildren(walk=walk, mAttrs=mAttrs, cAttrs=cAttrs, nAttrs=nAttrs,
                                                asMeta=asMeta, asMap=asMap, plugsOnly=plugsOnly, skip_cAttrs=skip_cAttrs, **kws)

    def selectChildren(self, walk=True, mAttrs=None, cAttrs=[], nAttrs=[], add=False):
        '''
        light wrap over the getChildren so we can more carefully manage it in some of the pro proc bindings

        :param walk: walk all subMeta connections and include all their children too
        :param mAttrs: only search connected mNodes that pass the given attribute filter (attr is at the metaSystems level)
        :param cAttrs: only pass connected children whos connection to the mNode matches the given attr (accepts wildcards)
        :param nAttrs: search returned MayaNodes for given set of attrs and only return matched nodes
        :param add: if True add to the current selection (also works with the "shift" modifier

        .. note::
            the wrapper also accepts the 'Shift' modifier key, if pressed when this is called then we set the selection to 'add'
            else it's a fresh selection thats made
        '''
        nodes = self.getChildren(walk=walk, mAttrs=mAttrs, cAttrs=cAttrs, nAttrs=nAttrs, asMeta=False, asMap=False)
        if r9General.getModifier() == 'Shift' or add:
            cmds.select(nodes, add=True)
        else:
            cmds.select(nodes)

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
        if we have a FacialCore node return it. This allows you to modify how
        you wire up your facial system to metaData but gives us a consistent hook
        '''
        if self.hasAttr('FacialCore'):
            fcore = self.FacialCore
            if fcore and isMetaNode(fcore):
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

    # generic presets so we can be consistent, these are really only examples
    # ---------------------------------------------------------------------------------

    def addWristCtrl(self, node, side, axis=None):
        self.addRigCtrl(node, '%s_Wrist' % side[0],
                        mirrorData={'side': side, 'slot': 1, 'axis': axis})

    def addElbowCtrl(self, node, side, axis=None):
        self.addRigCtrl(node, '%s_Elbow' % side[0],
                        mirrorData={'side': side, 'slot': 2, 'axis': axis})

    def addClavCtrl(self, node, side, axis=None):
        self.addRigCtrl(node, '%s_Clav' % side[0],
                        mirrorData={'side': side, 'slot': 3, 'axis': axis})

    def addFootCtrl(self, node, side, axis=None):
        self.addRigCtrl(node, '%s_Foot' % side[0],
                        mirrorData={'side': side, 'slot': 4, 'axis': axis})

    def addKneeCtrl(self, node, side, axis=None):
        self.addRigCtrl(node, '%s_Knee' % side[0],
                        mirrorData={'side': side, 'slot': 5, 'axis': axis})

    def addPropCtrl(self, node, side, axis=None):
        self.addRigCtrl(node, '%s_Prop' % side[0],
                        mirrorData={'side': side, 'slot': 6, 'axis': axis})

    # NOTE: Main should be the Top World Space Control for the entire rig
    # ====================================================================
    def addMainCtrl(self, node, side='Centre', axis=None):
        self.addRigCtrl(node, 'Main',
                        mirrorData={'side': side, 'slot': 1, 'axis': axis})

    def addRootCtrl(self, node, side='Centre', axis=None):
        self.addRigCtrl(node, 'Root',
                        mirrorData={'side': side, 'slot': 2, 'axis': axis})

    def addHipCtrl(self, node, side='Centre', axis=None):
        self.addRigCtrl(node, 'Hips',
                        mirrorData={'side': side, 'slot': 3, 'axis': axis})

    def addChestCtrl(self, node, side='Cent re', axis=None):
        self.addRigCtrl(node, 'Chest',
                        mirrorData={'side': side, 'slot': 4, 'axis': axis})

    def addHeadCtrl(self, node, side='Centre', axis=None):
        self.addRigCtrl(node, 'Head',
                        mirrorData={'side': side, 'slot': 5, 'axis': axis})

    def addNeckCtrl(self, node, side='Centre', axis=None):
        self.addRigCtrl(node, 'Neck',
                        mirrorData={'side': side, 'slot': 6, 'axis': axis})

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
            nodeName = attr
        return self.addChildMetaNode(mClass, attr=attr, nodeName=nodeName, **kws)

    def addSupportNode(self, node, attr, boundData=None):
        '''
        Add a single MAYA node flagged as a SUPPORT node of managed type
        Really in the MetaRig design these should be wired to a MetaRigSupport node

        :param node: Maya node to add
        :param attr: Attr name to assign this too
        :param boundData: {} Data to set on the given node as attrs
        '''
        self.connectChild(node, 'SUP_%s' % attr)
        if boundData:
            if issubclass(type(boundData), dict):
                for key, value in boundData.iteritems():
                    if logging_is_debug():
                        log.debug('Adding boundData to node : %s:%s' % (key, value))
                    MetaClass(node).addAttr(key, value=value)

    def addMetaSubSystem(self, systemType, side, attr=None, nodeName=None, mClass='MetaRigSubSystem', buildflags={}):
        '''
        Basic design of a MetaRig is that you have sub-systems hanging off an mRig
        node, managing all controllers and data for a particular system, such as an
        Arm system.

        :param systemType: Attribute used in the message link. Note this is what you use
            to traverse the Dag tree so use something sensible!
        :param side: Side to designate the system. This is an enum: Centre,Left,Right
        :param attr: wire name to use in the connections, if not given wire will be side[0]_systemType_'System'
        :param nodeName: Name of the MetaClass network node created
        :param mClass: the class to be used for the support node - 'MetaRigSubSystem' by default
        '''
        r9Anim.MirrorHierarchy()._validateMirrorEnum(side)  # ??? do we just let the enum __setattr__ handle this?

        if not attr:
            attr = '%s_%s_System' % (side[0], systemType)
        if not nodeName:
            nodeName = attr
        subSystem = self.addChildMetaNode(mClass, attr=attr, nodeName=nodeName)

        # set the attrs on the newly created subSystem MetaNode
        subSystem.systemType = systemType
        subSystem.mirrorSide = side
        if buildflags:
            subSystem.buildFlags = buildflags
        return subSystem

    def getMetaSubSystems(self, walk=True, mAttrs=None, stepover=False, **kws):
        '''
        return all child MetaSubSystem nodes wired as to this rig

        :param walk: walk the connected network and return ALL children connected in the tree
        :param mAttrs: only return connected nodes that pass the given attribute filter
        :param stepover: if you're passing in 'mTypes' or 'mInstances' flags then this dictates if
            we continue to walk down a tree if it's parent didn't match the given type, default is False
            which will abort a tree who's parent didn't match. With stepover=True we simply stepover
            that node and continue down all child nodes
        '''
        return self.getChildMetaNodes(walk=walk, mInstances='MetaRigSubSystem', mAttrs=mAttrs, stepover=stepover)

    def set_ctrlColour(self, colourIndex=4):
        '''
        set the override colour of a given nodes shapes
        '''
        for ctrl in self.getChildren(walk=False):
            shapes = cmds.listRelatives(ctrl, type='shape', f=True)
            if shapes:
                for shape in shapes:
                    cmds.setAttr('%s.overrideEnabled' % shape, 1)
                    cmds.setAttr('%s.overrideColor' % shape, colourIndex)

    # mirror management
    # ---------------------------------------------------------------------------------

    def getMirrorData(self):
        '''
        Bind the MirrorObject to this instance of MetaRig.

        .. note::
            you must run this binding function before using any of
            the inbuilt mirror functions
        '''
        self.MirrorClass = r9Anim.MirrorHierarchy(nodes=self.getChildren(walk=True))
        try:
            self.MirrorClass.getMirrorSets()
            log.debug('Filling the MirrorClass attr on demand')
        except:
            log.warning('No Mirror Markers found on the rig')
        return self.MirrorClass

    def loadMirrorDataMap(self, mirrorMap):
        '''
        load a mirror setup onto this rig from a stored mirrorMap file

        :param mirrorMap: mirror file to load
        '''
        if not self.MirrorClass:
            self.MirrorClass = self.getMirrorData()
        if not os.path.exists(mirrorMap):
            raise IOError('Given MirrorMap file not found : %s' % mirrorMap)
        r9Anim.MirrorHierarchy(self.getChildren()).loadMirrorSetups(mirrorMap)

    def saveMirrorDataMap(self, filepath):
        '''
        save the current mirror setup for this rig to file

        :param filepath: filepath to store the mirrorMap too
        '''
        if not self.MirrorClass:
            self.MirrorClass = self.getMirrorData()

        r9Anim.MirrorHierarchy(self.getChildren()).saveMirrorSetups(filepath)

    def getMirror_opposites(self, nodes, forceRefresh=False):
        '''
        from the given nodes return a map of the opposite pairs of controllers
        so if you pass in a right controller of mirrorIndex 4 you get back the
        left[4] mirror node and visa versa. Centre controllers pass straight through

        :param nodes: nodes to get the opposites from
        :param forceRefresh: forces the mirrorDic (which is cached) to be updated
        '''
        if not self.MirrorClass or forceRefresh:
            self.MirrorClass = self.getMirrorData()
        oppositeNodes = []

        for node in nodes:
            side = self.MirrorClass.getMirrorSide(node)
            if not side:
                continue
            if side == 'Left':
                oppositeNodes.append(self.MirrorClass.mirrorDict['Right'][str(self.MirrorClass.getMirrorIndex(node))]['node'])
            if side == 'Right':
                oppositeNodes.append(self.MirrorClass.mirrorDict['Left'][str(self.MirrorClass.getMirrorIndex(node))]['node'])
            if side == 'Centre':
                oppositeNodes.append(node)
        return oppositeNodes

    def getMirror_ctrlSets(self, set='Centre', forceRefresh=False):
        '''
        from the metaNode grab all controllers and return sets of nodes
        based on their mirror side data

        :param set: which set/side to get, valid = 'Left' ,'Right', 'Centre'
        :param forceRefresh: forces the mirrorDic (which is cached) to be updated
        '''
#         submNodes=mRig.getChildMetaNodes(mAttrs=['mirrorSide=2'], walk=True)
#         ctrls=[]
#         for node in submNodes:
#             ctrls.extend(node.getChildren())
#         return ctrls
        ctrls = []
        if not self.MirrorClass or forceRefresh:
            self.MirrorClass = self.getMirrorData()
        for _, value in self.MirrorClass.mirrorDict[set].items():
            ctrls.append(value['node'])
        return ctrls

    def getMirror_lastIndexes(self, side, forceRefresh=False):
        '''
        get the last mirror index for a given side

        :param side: side to check, valid = 'Left' ,'Right', 'Centre'
        :param forceRefresh: forces the mirrorDic (which is cached) to be updated
        '''
        if not self.MirrorClass or forceRefresh:
            self.MirrorClass = self.getMirrorData()
        if side in self.MirrorClass.mirrorDict.keys() and self.MirrorClass.mirrorDict[side]:
            return max([int(m) for m in self.MirrorClass.mirrorDict[side].keys()])
        return 0

    def getMirror_nextSlot(self, side, forceRefresh=False):
        '''
        return the next available slot in the mirrorIndex list for a given side

        :param side: side to check, valid = 'Left' ,'Right', 'Centre'
        :param forceRefresh: forces the mirrorDic (which is cached) to be updated
        '''
        return self.getMirror_lastIndexes(side, forceRefresh) + 1

    def mirror(self, nodes=None, mode='Anim'):
        '''
        direct mapper call to the Mirror functions

        :param nodes: nodes to mirror, if None then we process the entire rig
        :param mode: either 'Anim' or 'Pose'
        '''
        if not self.MirrorClass:
            self.MirrorClass = self.getMirrorData()
        self.MirrorClass.mirrorData(nodes, mode)

    def mirror_delete_all_markers(self, nodes=[]):
        '''
        delete all mirror markers from the rig
        '''
        if not nodes:
            nodes = self.getChildren(walk=True)
        if nodes:
            if not self.MirrorClass:
                self.MirrorClass = self.getMirrorData()
            for node in nodes:
                self.MirrorClass.deleteMirrorIDs(node)

    # ---------------------------------------------------------------------------------
    # Utilities ----
    # ---------------------------------------------------------------------------------

    @nodeLockManager
    def poseCacheStore(self, attr=None, filepath=None, incRoots=True, storeThumbnail=False, *args, **kws):
        '''
        intended as a cached pose for this mRig, if an attr is given then
        the cached pose is stored internally on the node so it can be loaded
        back from the mNode internally. If not given then the pose is cached
        on this object instance only.

        :param attr: optional - attr to store the cached pose to
        :param filepath: optional - path to store the pose too
        :param incRoots: passed directly to the filterSettings object in the pose, do we process self.ctrl_main?
        :param storeThumbnail: do we save the thumbnail out or not?
        '''
        import Red9.core.Red9_PoseSaver as r9Pose  # lazy loaded
        self.poseCache = r9Pose.PoseData()
        self.poseCache.metaPose = True
        self.poseCache.settings.incRoots = incRoots
        self.poseCache.poseSave(self.mNode,
                                filepath=filepath,
                                useFilter=True,
                                storeThumbnail=storeThumbnail,
                                *args, **kws)  # no path so cache against this pose instance
        if attr:
            if not self.hasAttr(attr):
                self.addAttr(attr, value=self.poseCache.poseDict, hidden=True)
            else:
                setattr(self, attr, self.poseCache.poseDict)
            self.attrSetLocked(attr, True)

    def poseCacheLoad(self, nodes=None, attr=None, filepath=None, incRoots=True, relativePose=False, relativeRots='projected',
                      relativeTrans='projected', maintainSpaces=False, skipAttrs=[], *args, **kws):
        '''
        load a cached pose back to this mRig. If attr is given then its assumed
        that that attr is a cached poseDict on the mNode. If not given then it
        will load the cached pose from this objects instance, if there is one stored.

        :param nodes: if given load only the cached pose to the given nodes
        :param attr: optional - attr in which a pose has been stored internally on the mRig
        :param filepath: optional - posefile to load back
        :param incRoots: passed directly to the filterSettings object in the pose, do we process self.ctrl_main?
        :param relativePose: kick in the posePointCloud to align the loaded pose
            relatively to the selected node.
        :param relativeRots: 'projected' or 'absolute' - how to calculate the offset.
        :param relativeTrans: 'projected' or 'absolute' - how to calculate the offset.
        :param maintainSpaces: this preserves any parentSwitching mismatches between
            the stored pose and the current rig settings, current spaces are maintained.
            This only checks those nodes in the snapList and only runs under relative mode.
        :param skipAttrs: attrs to skip when loading the data
        '''
        import Red9.core.Red9_PoseSaver as r9Pose  # lazy loaded
        if attr or filepath:
            self.poseCache = r9Pose.PoseData(**kws)  # **kws so we can pass the filterSettings directly if needed
            if attr:
                self.poseCache.poseDict = getattr(self, attr)
        if self.poseCache:
            if not nodes:
                self.poseCache.metaPose = True  # force to metaPose
                self.poseCache.settings.incRoots = incRoots  # force an incRoot flag update

                # added June 2020, the priority was never getting turned on internally!!
                if self.settings.filterPriority:
                    self.poseCache.prioritySnapOnly = True
                if skipAttrs:
                    self.poseCache.skipAttrs = skipAttrs
                self.poseCache.poseLoad(self.mNode,
                                        filepath=filepath,
                                        useFilter=True,
                                        relativePose=relativePose,
                                        relativeRots=relativeRots,
                                        relativeTrans=relativeTrans,
                                        maintainSpaces=maintainSpaces, *args, **kws)
            else:
                # in non hierarchy / filter mode relative is NOT supported
                self.poseCache.poseLoad(nodes, filepath=filepath, useFilter=False, *args, **kws)

    def poseCompare(self, poseFile, supressWarning=False, compareDict='skeletonDict', filterMap=[], ignoreBlocks=[],
                    ignoreStrings=[], ignoreAttrs=[], longName=False, angularTolerance=0.1, linearTolerance=0.01, **kws):
        '''
        Integrated poseCompare, this checks the mRigs current pose against
        a given poseFile. This checks against the 'skeletonDict'

        :param poseFile: given .pose file with valid skeletonDict block
        :param supressWarning: if False raise the confirmDialogue
        :param angularTolerance: the tolerance used to check rotate attr float values
        :param linearTolerance: the tolerance used to check all other float attrs
        :param compareDict: the internal main dict in the pose file to compare the data with : base options : 'poseDict', 'skeletonDict'
        :param filterMap: if given this is used as a high level filter, only matching nodes get compared
            others get skipped. Good for passing in a master core skeleton to test whilst ignoring extra nodes
        :param ignoreBlocks: allows the given failure blocks to be ignored. We mainly use this for ['missingKeys']
        :param ignoreStrings: allows you to pass in a list of strings, if any of the keys in the data contain
             that string it will be skipped, note this is a partial match so you can pass in wildcard searches ['_','_end']
        :param ignoreAttrs: allows you to skip given attrs from the poseCompare calls
        :param longName: compare the longName DAG path stored against each node, note that the compare strips out any namespaces before compare

        :return: returns a 'PoseCompare' class object with all the compare data in it
        '''
        import Red9.core.Red9_PoseSaver as r9Pose  # lazy loaded
        self.poseCacheStore()
        compare = r9Pose.PoseCompare(self.poseCache,
                                   poseFile,
                                   compareDict=compareDict,
                                   linearTolerance=linearTolerance,
                                   angularTolerance=angularTolerance,
                                   filterMap=filterMap,
                                   ignoreBlocks=ignoreBlocks,
                                   ignoreStrings=ignoreStrings,
                                   ignoreAttrs=ignoreAttrs,
                                   longName=longName,
                                   **kws)
        if not compare.compare():
            info = 'Selected Pose is different to the rigs current pose\nsee script editor for debug details'
        else:
            info = 'Poses are the same'
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
        simple wrapper to hide all ctrls in the rig via their shapeNodes.lodVisibility
        so it doesn't interfer with any display layers etc

        :param state: bool to pass to the lodVisibility attr
        :param skip: [] child attrs on the mNode to skip during the process allowing certain controllers not to be effected
        '''
        ctrlMap = self.getChildren(walk=True, asMap=True)
        for plug, ctrl in ctrlMap.items():
            if not plug.split('.')[-1] in skip:
                shapes = cmds.listRelatives(ctrl, type='shape', f=True)
                for shape in shapes:
                    cmds.setAttr('%s.lodVisibility' % shape, state)
            else:
                print(plug, skip)

    def hideNodes(self):
        '''
        wrap over the nodeVisibility to set False for all Controllers
        with the exception of the Main_Ctrl
        '''
        self.nodeVisibility(state=0, skip=['%s_Main' % self.CTRL_Prefix])

    def unHideNodes(self):
        '''
        wrap over the nodeVisibility to set True for all Controllers
        with the exception of the Main_Ctrl
        '''
        self.nodeVisibility(state=1, skip=['%s_Main' % self.CTRL_Prefix])

    @nodeLockManager
    def saveAttrMap(self, *args):
        '''
        store AttrMap to the metaRig, saving the chBox state of ALL attrs for ALL nodes in the hierarchy
        '''
        import Red9_CoreUtils as r9Core  # lazy loaded
        chn = r9Core.LockChannels()
        chn.saveChannelMap(filepath=None,
                           nodes=getattr(self, '%s_Main' % self.CTRL_Prefix),
                           hierarchy=True,
                           serializeNode=self.mNode)

    def loadAttrMap(self, *args):
        '''
        load AttrMap from the metaRig, returning the chBox state of ALL attrs for ALL nodes in the hierarchy
        '''
        import Red9_CoreUtils as r9Core  # lazy loaded
        chn = r9Core.LockChannels()
        chn.loadChannelMap(filepath=None,
                           nodes=getattr(self, '%s_Main' % self.CTRL_Prefix),
                           hierarchy=True,
                           serializeNode=self.mNode)

    @nodeLockManager
    def saveZeroPose(self, *args):
        '''
        serialize the r9Pose file to the node itself
        '''
        self.poseCacheStore(attr='zeroPose')

    def loadZeroPose(self, nodes=None, skipAttrs=[], *args):
        '''
        load the zeroPose form the internal dict

        :param nodes: optional, load at subSystem level for given nodes
        :param skipAttrs: optional list of attrs to skip during the load
        '''
        self.poseCacheLoad(nodes=nodes, attr='zeroPose', skipAttrs=skipAttrs)

    def getAnimationRange(self, nodes=None, setTimeline=False, *args, **kws):
        '''
        return the extend of the animation range for this rig and / or the given controllers

        :param nodes: if given only return the extent of the animation data from the given nodes
        :param setTimeLine: if True set the playback timeranges also, default=False
        :param decimals: int -1 default, this is the number of decimal places in the return, -1 = no clamp
        :param transforms_only: if True we only test translate (animCurveTL) and rotate (animCurveTA) data, added for skeleton fbx baked tests
        :param skip_static: if True we ignore static curves and return [], else we return
            the key bounds for the static keys, ignoring the keyValues
        :param bounds_only: if True we only return the key bounds, first and last key times,
            else we look at the changing values to find the bounds
        '''
        if not nodes:
            nodes = self.getChildren(walk=True)
        return r9Anim.animRangeFromNodes(nodes, setTimeline=setTimeline, *args, **kws)

    def keyChildren(self, nodes=[], walk=True, mAttrs=None, cAttrs=[], nAttrs=[], shapes=False):
        '''
        setKey on the systems controllers with options to control what gets keyed
        via the standard getChildren *args which are passed in.

        :param nodes: nodes to check, if None process the entire rig via all the flags which are passed into the getChildren call
        :param walk: walk all subMeta connections and include all their children too
        :param mAttrs: only search connected mNodes that pass the given attribute filter (attr is at the metaSystems level)
        :param cAttrs: only pass connected children whos connection to the mNode matches the given attr (accepts wildcards)
        :param nAttrs: search returned MayaNodes for given set of attrs and only return matched nodes
        :param shapes: now set to false to avoid keying all exposed Arnold shape attributes! We do however respect the animators
            set key options and if they've specifically set shapes to key, we pick that up and respect it
        '''
        if not nodes:
            nodes = self.getChildren(walk=walk, mAttrs=mAttrs, cAttrs=cAttrs, nAttrs=nAttrs, asMeta=False, asMap=False)

        try:
            # respect the uses SetKey Options?
            if cmds.optionVar(q='setKeyframeWhich') == 1:  # 1 = all keyable attributes
                shapes = cmds.optionVar(q='keyShapes')
            # new shapes flag came in in 2017
            cmds.setKeyframe(nodes, shapes=shapes)
        except:
            cmds.setKeyframe(nodes)

    def hasKeys(self, nodes=[], walk=True, returnCtrls=False):
        '''
        return True if any of the rig's controllers have existing
        animation curve/key data

        :param nodes: nodes to check, if None process the entire rig
        '''
        if not nodes:
            nodes = self.getChildren(walk=walk)
        if not returnCtrls:
            return r9Core.FilterNode.lsAnimCurves(nodes, safe=True) or False
        else:
            failed = []
            for node in nodes:
                if r9Core.FilterNode.lsAnimCurves(node, safe=True):
                    failed.append(node)
            return failed

    def cutKeys(self, nodes=[], reset=True, walk=True, verbose=False):
        '''
        cut all animation keys from the rig and reset

        :param nodes: if passed in only cutKeys on given nodes
        :param reset: if true reset the rig after key removal
        '''
        if verbose:
            results = cmds.confirmDialog(title='CutKeys',
                               button=['Confirm', 'Abort'],
                               message='Confirm Key Deletion',
                               defaultButton='Close',
                               icon='question',
                               cancelButton='Close',
                               dismissString='Close')
            if results == 'Abort':
                return
        if not nodes:
            nodes = self.getChildren(walk=walk)
        if self.hasKeys(nodes):
            cmds.cutKey(r9Core.FilterNode.lsAnimCurves(nodes, safe=True))
        if reset:
            try:
                self.loadZeroPose(nodes)
            except:
                log.info('failed to load ZeroPose back to the rig - this may be an SRC system node')

    # -------------------------------------------------------------------------------------
    # PRO PACK : Supported Only ----
    # -------------------------------------------------------------------------------------

    '''
    All these commands are bound purely for those running the Red9 ProPack and are examples of
    the extensions being added. We bind them here to make it more transparent for you guys
    running Meta, save us sub-classing MetaRig for Pro and exposes some of the codebase wrapping
    '''

    def saveAnimation(self, filepath, incRoots=True, useFilter=True, timerange=(),
                      storeThumbnail=False, force=False, userInfoData='', **kws):
        '''
        : PRO_PACK :
            Binding of the animMap format for storing animation data out to file

        :param filepath: r9Anim file to load
        :param incRoots: do we include the root node in the load, in metaRig case this is ctrl_main
        :param useFilter: do we process all children of this rig or just selected
        :param timerange: specify a timerange to store, If no timerange is passed
            then it will use the current timeLine PlaybackRange, OR if you have a
            highlighted range of time selected (in red) it'll use this instead.
        :param storeThumbnail: this will be an avi but currently it's a pose thumbnail
        :param force: allow force write on a read only file
        :param userInfoData: user information used by the AnimStore UI only
        '''
        if r9Setup.has_pro_pack():
            from Red9.pro_pack import r9pro
            r9pro.r9import('r9panim')
            from r9panim import AnimMap

            self.animCache = AnimMap(**kws)
            self.animCache.userInfoData = userInfoData
            self.animCache.filepath = filepath
            self.animCache.metaPose = True
            self.animCache.settings.incRoots = incRoots
            self.animCache.saveAnim(self.mNode,
                                    useFilter=useFilter,
                                    timerange=timerange,
                                    storeThumbnail=storeThumbnail,
                                    force=force)

            log.info('AnimMap data saved to : %s' % self.animCache.filepath)

    def animMap_postprocess(self, feedback=None, *args, **kws):
        '''
        : PRO_PACK :
            Added to be Overloaded at the class level!

        Call passed into the animMap class and run AFTER the r9Anim file is loaded
        on the MetaRig, this allows you to add functionality to the base load call to
        extract extra data from the animMap and act upon it. This allows us to act on the
        animMap stored on the class object and rebuild data from the infoDict if required.
        We use this to rebuild audio links, exporter nodes and any other data that's required
        to be restored from the gathered info

        self.animCache.infoDict

        :param feedback: data passed back into the call by the main loadAnimation func

        .. note::
            see the following functions in the ProPack > metadata_pro.Pro_MetaRig_Base class for more detailed information

            * metadata_pro.Pro_MetaRig_Base.animMap_restore_export_data
            * metadata_pro.Pro_MetaRig_Base.animMap_restore_audio_data

            and all animMap_** functions as these expand
        '''
        pass

    def loadAnimation_postload_call(self, feedback=None, *args, **kws):
        '''
        # DEPRECATED FUNCTION - replaced with self.animMap_postprocess
        '''
        self.animMap_postprocess(feedback=None, *args, **kws)
        log.warning('DEPRECATED Warning: "mRig.loadAnimation_postload_call" - Please use "mRig.animMap_postload_call" instead')

    def loadAnimation(self, filepath, incRoots=True, useFilter=True, loadAsStored=True, loadFromFrm=0, loadFromTimecode=False,
                      timecodeBinding=[None, None], referenceNode=None, relativeRots='projected', relativeTrans='projected',
                      manageRanges=1, manageFileName=True, keyStatics=False, blendRange=None, merge=False, matchMethod='metaData',
                      smartbake=False, loadInternalRig=False, *args, **kws):
        '''
        : PRO_PACK :
            Binding of the animMap format for loading animation data from
            an r9Anim file. The base binding of the animation format is the DataMap object
            in the Red9_PoseSaver so many of the exposed flags come from there.

        :param filepath: r9Anim file to load
        :param incRoots: do we include the root node in the load, in metaRig case this is ctrl_main
        :param useFilter: do we process all children of this rig or just selected
        :param loadAsStored: load the data from the timerange stored
        :param loadFromFrm: load the data from a given frame, this requires the loadAsStored=False else is ignored
        :param loadFromTimecode: load against a given SMPTE timecode / frm binding, calculating the offset of
            the data to load against a given timecode reference. IF timecodeBinding isn't set then we gather the reference timecode from
            the mRig's internal data, else we use the timecode binding supplied
        :param timecodeBinding: (frm, str('00:00:00:00'))  Tuple where the first arg is the frame at which the second arg's SMPTE timecode
            has been set as reference, basically we're saying that the timecode at frm is x
        :param referenceNode: load relative to the given node
        :param relativeRots: 'projected' or 'absolute' - how to calculate the offset, default='projected'
        :param relativeTrans: 'projected' or 'absolute' - how to calculate the offset, default='projected'
        :param manageRanges: valid values : 0=leave,  1=extend, 2=set the timeranges according to the anim data loaded
        :param manageFileName: if True and the current Maya scene has no filename other than a blank scene (ie freshly loaded rig)
            then we take the r9Anim's filename and rename the Maya scene accordingly
        :param keyStatics: if True then we key everything in the data at startFrame & endFrame so that all non-keyed and static
            attrs that are stored internally as a pose are keyed.
        :param blendRange: None or int : None is default. If an int is passed then we use this as the hold range for the data, setting a key at
            time=[startFarme-blendRange, endFarme+blendRange] to hold the current data before we load the new keys. Note that this also turns
            on the keyStatics to ensure the data is preserved
        :param merge: if True we allow the data to be merged over any current keys, else we cut all keys in the load range first
        :param matchMethod: internal matching method used to match nodes to the stored data
        :param smartbake: only valid if we're loading with a referenceNode, this tries to respect current keys when doing the processing rather than frame baking
        :param loadInternalRig: If True and the r9Anim was created from a rig that was referenced then re-create that reference and load the r9Anim data onto
            the resulting nodes. This is used in the Direct Load calls as the prime way to import the rigs prior to loading

        : additional **KWS passed in and / or accepted in the ProPack codebase :

        :param manageExport: If running the Red9Pro Exporter systems this will rebuild the export Tag data directly
            from the r9Anim file's infoData block:

        * False : don't restore any exportData,
        * [] : if you pass in a list then we take that list and match internal exportloop names to it
        * 'byName' : restore only exportLoops who name matches the r9Anim's name
        * 'byRange': restore exportLoops that fall within the timerange of the imported r9Anim
        * 'byRange_start' : restore exportLoops that start after the timerange of the importer r9Anim (ignore end time data)
        * 'byRange_end' : restore exportLoops that end before the timerange of the importer r9Anim (ignore start time data)
        * 'byAll' : restore ALL exportLoops in the r9Anim infoData block

        :param manageAudio: If running the Red9Pro Exporter systems this will rebuild the Audio Node data directly, taking
            the same matching flags as the manageExport kws above
            from the r9Anim file's infoData block   (False, [], 'byName', 'byRange', 'byRange_start', 'byRange_end', 'byAll')

        .. note::
            After the anim load the animData is stored on this instance as self.animCache which then
            exposes all the data for further functions if needed.

            * self.animCache.infoDict = gatherInfo / general secondary data block on the file and pose.
            * self.animCache.poseDict = the animation and pose data dict.
            * self.animCache.skeletonDict = the pose data dict purely for the skeleton, used in compare functions.

        :param manageImagePlanes: if we're dealing with a sub-class of the Pro_MetaRig_FacialUI the restore the ImagePlane data,
            this is a simple bool. This creates the imageplane, binds it to the facial UI, offsets it, loads the imagedata, sets the
            width/height and frameoffset.

        .. note::
            because imagePlanes in Maya are so heavily bound to AETemplate callbacks you need to flick over to the attribute editor
            to correctly initialize any image sequence

        .. note::
            **kws are passed directly into BOTH the AnimMap class and the animMap_postprocess
            so that we can bounce additional **kws into these funcs without having to specify everything,
            this allows us to modify the behaviour on a case by case basis for clients
        '''
        if r9Setup.has_pro_pack():
            from Red9.pro_pack import r9pro
            r9pro.r9import('r9panim')
            from r9panim import AnimMap
            feedback = None
            if 'ANIMMAP' in kws:
                self.animCache = kws['ANIMMAP']
                self.animCache._read_mute = True  # stop DatMap reading the r9Anim file again and use the cached data
            else:
                self.animCache = AnimMap(**kws)  # **kws so we can pass back the filterSettings from the UI call in pro
                self.animCache.filepath = filepath  # no file so use the animcahe object data as given, this turns off the read call

            self.animCache.metaPose = True
            self.animCache.settings.incRoots = incRoots
            self.animCache.matchMethod = matchMethod
            if useFilter:
                rootNodes = self.mNode
            else:
                rootNodes = cmds.ls(sl=True, l=True)
            try:
                feedback = self.animCache.loadAnim(nodes=rootNodes,
                                               useFilter=useFilter,
                                               loadAsStored=loadAsStored,
                                               loadFromFrm=loadFromFrm,
                                               loadFromTimecode=loadFromTimecode,
                                               timecodeBinding=timecodeBinding,
                                               referenceNode=referenceNode,
                                               relativeRots=relativeRots,
                                               relativeTrans=relativeTrans,
                                               manageRanges=manageRanges,
                                               manageFileName=manageFileName,
                                               keyStatics=keyStatics,
                                               blendRange=blendRange,
                                               merge=merge,
                                               smartbake=smartbake,
                                               loadInternalRig=loadInternalRig,
                                               **kws)
                # =========================================================
                # pass the feedback to the postload code to handle, this is
                # responsible, at the client level for restoring things like audioNodes
                # and exportLoops
                self.animMap_postprocess(feedback, *args, **kws)
            except StandardError, err:
                log.warning(err)
            return feedback

    # --------------------------------------------------------------------------------------
    # PRO PACK : Timecode management ---
    # --------------------------------------------------------------------------------------

    @property
    def Timecode(self):
        '''
        : PRO_PACK : bind the Pro Timecode class to the node. The Timecode object is now cached
        to the instance rather than being instantiated on ach call.
        '''
        if r9Setup.has_pro_pack():
            try:
                import Red9.pro_pack.core.audio as r9paudio  # dev mode only ;)
            except:
                from Red9.pro_pack import r9pro
                r9pro.r9import('r9paudio')
                import r9paudio
            try:
                if not self._Timecode:
                    self._Timecode = r9paudio.Timecode(self.timecode_ctrlnode)
            except StandardError, err:
                log.error(err)
                # instantiate a blank Timecode class
                if not self._Timecode:
                    self._Timecode = r9paudio.Timecode(node=None)
            return self._Timecode

    @property
    def timecode_ctrlnode(self):
        '''
        : PRO_PACK : return the actual node that the timecode data is stamped onto in the rig
        '''
        if self.hasAttr('timecode_node') and self.timecode_node:
            return self.timecode_node[0]
        else:
            return self.ctrl_main

    def timecode_isValid(self):
        '''
        : PRO_PACK : check if the timecode is in a valid format, particularly the sample_rate attr
            which must NOT be set to Zero
        '''
        if r9Setup.has_pro_pack():
            if self.timecode_hasTimeCode():
                return self.Timecode.isValid()

    def timecode_get(self, atFrame=None):
        '''
        : PRO PACK : get the timecode back from the rig
        '''
        if r9Setup.has_pro_pack():
            return self.Timecode.getTimecode_from_node(time=atFrame)

    def timecode_addAttrs(self, tc='', propagate=False, timerange=()):
        '''
        : PRO PACK : add the timecode attributes and push the given timecode
        to the mRigs timecode node

        :param tc: timecode to set
        :param propagate: do we just set the attrs or push the counter keys
        :param timerange: If propagate then this is an optional timerange over which to set the data
        '''
        if r9Setup.has_pro_pack():
            self.Timecode.addTimecode_to_node(tc=tc, propagate=propagate, timerange=timerange)

    def timecode_setTimecode(self, tc='', propagate=False, ui=False, timerange=()):
        '''
        : PRO PACK : wrap over the timecode_addAttrs but exposes the enterTimecode ui

        :param tc: timecode to set
        :param propagate: do we just set the attrs or push the counter keys, if the UI is True then this is True by default
        :param ui: do we launch the Timecode UI to enter a specific timecode manually
        :param timerange: If propagate then this is an optional timerange over which to set the data
        '''
        if r9Setup.has_pro_pack():
            if ui:
                self.Timecode.enterTimecodeUI(buttonlabel='Set / Add Timecode', buttonfunc=None, default='01:00:00:00', propagate=True, timerange=timerange)
            else:
                self.timecode_addAttrs(tc=tc, propagate=propagate, timerange=timerange)

    def timecode_hasTimeCode(self):
        '''
        : PRO PACK : simple return to check if the system has the Pro Timecode
        systems bound to it
        '''
        if r9Setup.has_pro_pack():
            return self.Timecode.hasTimeCode() or False

    def timecode_remove(self):
        '''
        : PRO PACK : remove the Timecode attrs and system from this mRig
        '''
        if r9Setup.has_pro_pack():
            return self.Timecode.removedTimecode_from_node() or False


class MetaRigSubSystem(MetaRig):
    '''
    SubClass of the MRig, designed to organize Rig sub-systems (ie L_ArmSystem, L_LegSystem..)
    within a complex rig structure. This or MetaRig should have the Controllers wired to it
    '''
    def __init__(self, *args, **kws):
        super(MetaRigSubSystem, self).__init__(*args, **kws)
        self.mClassGrp = 'MetaClass'  # set the Grp removing the MetaRig systemBase Grp code
        self.mSystemRoot = False

    def __bindData__(self):
        self.addAttr('systemType', attrType='string')
        self.addAttr('mirrorSide', enumName='Centre:Left:Right', attrType='enum')
        self.addAttr('buildFlags', attrType='string', value={}, hidden=True)

    @property
    def SupportNode(self):
        '''
        return the connected Support mNode regardless of the wire used to connect it

        .. note::
            this is setup to use the Red9Pro Puppet wire conventions when multiple connected
            support nodes are found. The idea being that there is always 1 main support for a system
            and the naming convention of the mNodeID reflects that ie: L_ArmSystem and L_ArmSupport
        '''
        try:
            subsystems = getConnectedMetaNodes(self.mNode, source=False, destination=True, mInstances=MetaRigSupport, dataType='mClass')
            # print 'subsystems :', subsystems
            if len(subsystems) > 1:
                for s in subsystems:
                    if s.mNodeID == self.mNodeID.replace('System', 'Support'):
                        return s
            else:
                return subsystems[0]
        except:
            return []


class MetaRigSupport(MetaClass):
    '''
    SubClass of MetaClass, designed to organize support nodes, solvers and other internal
    nodes within a complex rig structure which you may need to ID at a later date.
    Controllers should NOT be wired to this node
    '''
    def __init__(self, *args, **kws):
        super(MetaRigSupport, self).__init__(*args, **kws)

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
        self.connectChild(node, 'SUP_%s' % attr)
        if boundData:
            if issubclass(type(boundData), dict):
                for key, value in boundData.iteritems():
                    if logging_is_debug():
                        log.debug('Adding boundData to node : %s:%s' % (key, value))
                    MetaClass(node).addAttr(key, value=value)


# ----------------------------------------------------------------------------
# --- Facial BaseClasses  --- -------------------
# ----------------------------------------------------------------------------

'''
Facial Base classes used and expanded upon by the Red9 Pro and client systems.
These are here so that we have consistant, open base classes that we can use as
a marker for the toolsets.
'''


class MetaFacialRig(MetaRig):
    '''
    SubClass of the MetaRig, designed to be manage Facial systems in the MetaData
    Dag tree for organizing Facial Controllers and support nodes
    '''
    def __init__(self, *args, **kws):
        super(MetaFacialRig, self).__init__(*args, **kws)
        self.mClassGrp = 'MetaFacialRig'
        self.CTRL_Prefix = 'FACE'

    def __bindData__(self):
        '''
        over-load and blank so that the MetaRig bindData doesn't get inherited
        '''
        pass

# Moved into ProPack
# class MetaFacialUI(MetaRig):
#     '''
#     SubClass of the MetaRig, designed to manage facial board style controls
#     for a facial system. Just an extract class to inherit from but it means that
#     all our facial logic will find custom class control boards based on being
#     subclassed from this consistent base.
#     '''
#     def __init__(self,*args,**kws):
#         super(MetaFacialUI, self).__init__(*args,**kws)
#         self.mClassGrp = 'MetaFacialRig'
#
#     def __bindData__(self):
#         '''
#         over-load and blank so that the MetaRig bindData doesn't get inherited
#         '''
#         pass

class MetaFacialRigSupport(MetaClass):
    '''
    SubClass of the MetaClass, designed to organize support nodes, solvers and other internal
    nodes within a complex rig structure which you may need to ID at a later date.
    Controllers should NOT be wired to this node
    '''
    def __init__(self, *args, **kws):
        super(MetaFacialRigSupport, self).__init__(*args, **kws)
        self.CTRL_Prefix = 'SUP'

    def addSupportNode(self, node, attr, boundData=None):
        '''
        Add a single MAYA node flagged as a SUPPORT node of managed type.

        :param node: Maya node to add
        :param attr: Attr name to assign this too
        :param boundData: {} Data to set on the given node as attrs
        '''
        self.connectChild(node, '%s_%s' % (self.CTRL_Prefix, attr))
        if boundData:
            if issubclass(type(boundData), dict):
                for key, value in boundData.iteritems():
                    if logging_is_debug():
                        log.debug('Adding boundData to node : %s:%s' % (key, value))
                    MetaClass(node).addAttr(key, value=value)


# ----------------------------------------------------------------------------
# --- HIK BaseClasses  --- -------------------
# ----------------------------------------------------------------------------

class MetaHIKCharacterNode(MetaRig):
    '''
    Casting HIK directly to a metaClass so it's treated as meta by default.
    Why the hell not, it's a complex character node that is default in Maya
    and useful for management in the systems
    '''
    def __init__(self, *args, **kws):
        kws.setdefault('autofill', 'messageOnly')
        super(MetaHIKCharacterNode, self).__init__(*args, **kws)

    def __bindData__(self):
        '''
        overload as we don't want the default MRig attrs bound to this nodeType
        '''
        pass

    def __repr__(self):
        return "%s(mClass: 'MetaHIKCharacterNode', node: '%s')" % (self.__class__, self.mNode.split('|')[-1])

    def __getMessageAttr__(self, attr):
        '''
        overloaded so that the main message wires return as single nodes
        '''
        data = super(MetaHIKCharacterNode, self).__getMessageAttr__(attr)
        if data:
            if type(data) == list:
                return data[0]
            return data

    def isValid(self):
        '''
        simple check to see if this definition is still wired to a skeleton,
        the the skeleton was deleted then the definition never gets cleaned up!!
        Messy Sodding Maya!
        '''
        if not cmds.listConnections(self.mNode, type='joint'):
            return False
        return True

    def getHIKPropertyStateNode(self):
        '''
        return the HIK Property node as a class for easy management
        '''
        properties = cmds.listConnections('%s.propertyState' % self.mNode)
        if properties:
            return MetaHIKPropertiesNode(properties[0])

    def getHIKControlSetNode(self):
        controlNode = cmds.listConnections(self.mNode, type='HIKControlSetNode')
        if controlNode:
            return controlNode[0]

    def delete(self):
        '''
        delete hik node and dependency nodes
        :return:
        '''
        # nodes connected to OutputCharacterDefinition
        OutputCharacterDefinition = cmds.listConnections('%s.OutputCharacterDefinition' % self.mNode)

        if OutputCharacterDefinition:
            cmds.delete(OutputCharacterDefinition)

        propertyState = cmds.listConnections('%s.propertyState' % self.mNode)

        if propertyState:
            cmds.delete(propertyState)

        if cmds.objExists(self.mNode):
            cmds.lockNode(self.mNode, lock=False)
            cmds.delete(self.mNode)

    @staticmethod
    def openui():
        '''
        Open hik UI
        '''
        if not r9Setup.mayaIsBatch():
            mel.eval('HIKCharacterControlsTool')
            mel.eval('hikSelectDefinitionTab')

    def lock(self):
        '''
        lock hik characterisation
        :return: True if lock False if not lock
        '''
        if self.InputCharacterizationLock:
            self.unLock()

        if self.checkcharacterization():
            mel.eval('hikCharacterLock("%s", 1, 1 )' % self.mNode)
            self.openui()
            return True

        self.openui()
        return False

    def unLock(self):
        '''
        unlock hik characterisation
        '''
        self.setascurrentcharacter()
        self.InputCharacterizationLock = False
        self.openui()

    @staticmethod
    def getCurrentCharacter():
        '''
        get current hik character
        :return: current hik charactre name
        '''
        return mel.eval('hikGetCurrentCharacter')

    def setascurrentcharacter(self):
        '''
        set current mNode as hikcurrentcharacter
        '''
        mel.eval('hikSetCurrentCharacter %s' % self.mNode)
        self.openui()

    def checkcharacterization(self):
        '''
        check that hikNode characterisation is valid
        :return: True if valid False if invalid
        '''
        self.setascurrentcharacter()
        self.openui()

        status = cmds.characterizationToolUICmd(query=True, curcharstatus=True)

        if status == 0:
            log.info('checkCharacterization for %s  : PASSED' % self.mNode)
            return True
        else:
            log.info('checkCharacterization for %s  : FAILED' % self.mNode)
            return False


class MetaHIKControlSetNode(MetaRig):
    '''
    Casting HIK directly to a metaClass so it's treated as meta by default.
    Why the hell not, it's a complex character node that is default in Maya
    and useful for management in the systems
    '''
    def __init__(self, *args, **kws):
        kws.setdefault('autofill', 'messageOnly')
        super(MetaHIKControlSetNode, self).__init__(*args, **kws)
        self.CTRL_Main = self.Reference

    def __repr__(self):
        return "%s(mClass: 'MetaHIKControlSetNode', node: '%s')" % (self.__class__, self.mNode.split('|')[-1])

    def __getMessageAttr__(self, attr):
        '''
        overloaded so that the main message wires return as single nodes
        '''
        data = super(MetaHIKControlSetNode, self).__getMessageAttr__(attr)
        if data:
            if type(data) == list:
                return data[0]
            return data

    def getHIKCharacterNode(self):
        return cmds.listConnections(self.mNode, type='HIKCharacterNode')[0]

    def getChildren(self, walk=False, mAttrs=None, cAttrs=None):
        '''
        Carefully over-loaded for HIK system
        '''
        children = []
        attrs = cmds.listAttr(self.mNode)
        if attrs:
            for attr in attrs:
                if cmds.getAttr('%s.%s' % (self.mNode, attr), type=True) == 'message':
                    effector = cmds.listConnections('%s.%s' % (self.mNode, attr), destination=False, source=True)
                    if effector:
                        for e in effector:
                            if cmds.nodeType(e) in ['hikIKEffector', 'hikFKJoint']:
                                children.extend(cmds.ls(e, l=True))
        return children


class MetaHIKPropertiesNode(MetaClass):
    '''
    Casting HIK Properties to a Meta class for easy managing

    ** PRO PACK BASED SETUP FOR THE REMAPPING HANDLERS **
    '''

    # these are all measurements specific to the skeleton when completed
    # if loading generic mapping data on different skeletons we need to skip these
    floor_contact = ['FootBottomToAnkle',
                      'FootBackToAnkle',
                      'FootMiddleToAnkle',
                      'FootFrontToMiddle',
                      'FootInToAnkle',
                      'FootOutToAnkle',
                      'HandBottomToWrist',
                      'HandBackToWrist',
                      'HandMiddleToWrist',
                      'HandFrontToMiddle',
                      'HandInToWrist',
                      'HandOutToWrist']

    tips_finger_toes = ['LeftHandThumbTip',
                        'LeftHandIndexTip',
                        'LeftHandMiddleTip',
                        'LeftHandRingTip',
                        'LeftHandPinkyTip',
                        'LeftHandExtraFingerTip',
                        'RightHandThumbTip',
                        'RightHandIndexTip',
                        'RightHandMiddleTip',
                        'RightHandRingTip',
                        'RightHandPinkyTip',
                        'RightHandExtraFingerTip',
                        'LeftFootThumbTip',
                        'LeftFootIndexTip',
                        'LeftFootMiddleTip',
                        'LeftFootRingTip',
                        'LeftFootPinkyTip',
                        'LeftFootExtraFingerTip',
                        'RightFootThumbTip',
                        'RightFootIndexTip',
                        'RightFootMiddleTip',
                        'RightFootRingTip',
                        'RightFootPinkyTip',
                        'RightFootExtraFingerTip']

    # roll pitch properties, think it might be better to just search for 'Roll' and 'Pitch' !!!!!!
    roll_pitch = ['RollExtractionMode',

                    # 2016 and previous HIK roll system
                    'LeftForeArmRollEx',
                    'LeftArmRollEx',
                    'RightForeArmRollEx',
                    'RightArmRollEx',
                    'rightShoulderRoll',
                    'LeftLegRollEx',
                    'LeftUpLegRollEx',
                    'RightLegRollEx',
                    'RightUpLegRollEx',

                    'LeftArmRoll', 'LeftArmRollMode',
                    'LeftForeArmRoll', 'LeftForeArmRollMode',
                    'LeftLegRoll', 'LeftLegRollMode',
                    'LeftUpLegRoll', 'LeftUpLegRollMode',
                    'RightArmRoll', 'RightArmRollMode',
                    'RightForeArmRoll', 'RightForeArmRollMode',
                    'RightLegRoll', 'RightLegRollMode',
                    'RightUpLegRoll', 'RightUpLegRollMode',

                    # 2017 onwards, new roll setup
                    'LeftLegFullRollExtraction', 'LeftLegFullRollExtractionMode',
                    'ParamLeafLeftUpLegRoll1', 'ParamLeafLeftUpLegRoll1Mode',
                    'ParamLeafLeftUpLegRoll2', 'ParamLeafLeftUpLegRoll2Mode',
                    'ParamLeafLeftUpLegRoll3', 'ParamLeafLeftUpLegRoll3Mode',
                    'ParamLeafLeftUpLegRoll4', 'ParamLeafLeftUpLegRoll4Mode',
                    'ParamLeafLeftUpLegRoll5', 'ParamLeafLeftUpLegRoll5Mode',
                    'leftHipRoll',
                    'ParamLeafLeftLegRoll1', 'ParamLeafLeftLegRoll1Mode',
                    'ParamLeafLeftLegRoll2', 'ParamLeafLeftLegRoll2Mode',
                    'ParamLeafLeftLegRoll3', 'ParamLeafLeftLegRoll3Mode',
                    'ParamLeafLeftLegRoll4', 'ParamLeafLeftLegRoll4Mode',
                    'ParamLeafLeftLegRoll5', 'ParamLeafLeftLegRoll5Mode',
                    'leftKneeRoll',
                    'LeftKneeKillPitch',

                    'RightLegFullRollExtraction', 'RightLegFullRollExtractionMode',
                    'ParamLeafRightUpLegRoll1', 'ParamLeafRightUpLegRoll1Mode',
                    'ParamLeafRightUpLegRoll2', 'ParamLeafRightUpLegRoll2Mode',
                    'ParamLeafRightUpLegRoll3', 'ParamLeafRightUpLegRoll3Mode',
                    'ParamLeafRightUpLegRoll4', 'ParamLeafRightUpLegRoll4Mode',
                    'ParamLeafRightUpLegRoll5', 'ParamLeafRightUpLegRoll5Mode',
                    'rightHipRoll',
                    'ParamLeafRightLegRoll1', 'ParamLeafRightLegRoll1Mode',
                    'ParamLeafRightLegRoll2', 'ParamLeafRightLegRoll2Mode',
                    'ParamLeafRightLegRoll3', 'ParamLeafRightLegRoll3Mode',
                    'ParamLeafRightLegRoll4', 'ParamLeafRightLegRoll4Mode',
                    'ParamLeafRightLegRoll5', 'ParamLeafRightLegRoll5Mode',
                    'rightKneeRoll',
                    'RightKneeKillPitch',

                    'LeftArmFullRollExtraction', 'LeftArmFullRollExtractionMode',
                    'ParamLeafLeftArmRoll1', 'ParamLeafLeftArmRoll1Mode',
                    'ParamLeafLeftArmRoll2', 'ParamLeafLeftArmRoll2Mode',
                    'ParamLeafLeftArmRoll3', 'ParamLeafLeftArmRoll3Mode',
                    'ParamLeafLeftArmRoll4', 'ParamLeafLeftArmRoll4Mode',
                    'ParamLeafLeftArmRoll5', 'ParamLeafLeftArmRoll5Mode',
                    'leftShoulderRoll',
                    'ParamLeafLeftForeArmRoll1', 'ParamLeafLeftForeArmRoll1Mode',
                    'ParamLeafLeftForeArmRoll2', 'ParamLeafLeftForeArmRoll2Mode',
                    'ParamLeafLeftForeArmRoll3', 'ParamLeafLeftForeArmRoll3Mode',
                    'ParamLeafLeftForeArmRoll4', 'ParamLeafLeftForeArmRoll4Mode',
                    'ParamLeafLeftForeArmRoll5', 'ParamLeafLeftForeArmRoll5Mode',
                    'leftElbowRoll',
                    'LeftElbowKillPitch',

                    'RightArmFullRollExtraction', 'RightArmFullRollExtractionMode',
                    'ParamLeafRightArmRoll1', 'ParamLeafRightArmRoll1Mode',
                    'ParamLeafRightArmRoll2', 'ParamLeafRightArmRoll2Mode',
                    'ParamLeafRightArmRoll3', 'ParamLeafRightArmRoll3Mode',
                    'ParamLeafRightArmRoll4', 'ParamLeafRightArmRoll4Mode',
                    'ParamLeafRightArmRoll5', 'ParamLeafRightArmRoll5Mode',
                    'rightShoulderRoll',
                    'ParamLeafRightForeArmRoll1', 'ParamLeafRightForeArmRoll1Mode',
                    'ParamLeafRightForeArmRoll2', 'ParamLeafRightForeArmRoll2Mode',
                    'ParamLeafRightForeArmRoll3', 'ParamLeafRightForeArmRoll3Mode',
                    'ParamLeafRightForeArmRoll4', 'ParamLeafRightForeArmRoll4Mode',
                    'ParamLeafRightForeArmRoll5', 'ParamLeafRightForeArmRoll5Mode',
                    'RightElbowKillPitch']

    measurements = floor_contact + tips_finger_toes

    def __init__(self, *args, **kws):
        super(MetaHIKPropertiesNode, self).__init__(*args, **kws)

        try:
            # try the pro_pack first as this is tested more
            from Red9 import pro_pack as r9pro
            self._resetfile = r9General.formatPath_join(r9pro.red9ProResourcePath(), 'hik_presets', 'HIK_default.hikproperties')
        except:
            # included in StudioPack for consistency of the codebase
            self._resetfile = r9General.formatPath_join(r9Setup.red9ModulePath(), 'presets', 'resource_files', 'HIK_default.hikproperties')

    def get_mapping(self):
        '''
        get the current mapping state and return a dict {attr:val, ...}
        '''
        data = {}
        for attr in sorted(cmds.listAttr(self.mNode)):
            if attr == 'message':  # skip the default message wire back to the HIK Character node
                continue
            data[attr] = getattr(self, attr)
        return data

    def get_non_default_values(self):
        '''
        return values that differ from the default values and have therefore been set by the user
        '''
        changes = {}
        defaults = r9General.readJson(self._resetfile)
        current = self.get_mapping()
        for key, val in current.items():
            try:
                if not val == defaults[key]:
                    changes[key] = [defaults[key], val]
            except:
                log.info('failed to compare key : %s' % key)
        return changes

    def reset_defaults(self):
        '''
        reset the default mapping property states
        '''
        if not os.path.exists(self._resetfile):
            log.warning('HIK_default.hikproperties : reset file not found in systems!')
            return
        self.load_mapping(self._resetfile, changes_only=True, verbose=True)

    def save_mapping(self, filepath, skip_measurements=True, skip_rolls=True):
        '''
        save the current mapping to file

        :param filepath: filepath to store the mapping out too
        :param skip_measurements: if true (defulat) we do not store those attrs that are skeleton specific
            only those which control the remapping
        '''
        filepath = os.path.splitext(filepath)[0] + '.hikproperties'
        try:
            data = self.get_mapping()
            if skip_measurements or skip_rolls:
                for key in data.keys():
                    if key in self.measurements:
                        data.pop(key)
                    if key in self.roll_pitch:
                        data.pop(key)

            r9General.writeJson(filepath, data)
        except:
            log.warning(traceback.format_exc())
        log.info('HIK Properties Saved: %s' % filepath)

    def load_mapping(self, filepath, changes_only=True, verbose=True, skip_measurements=True, skip_rolls=True):
        '''
        load a previous mapping back from file

        :param filepath: filepath to load the mapping from
        :param changes_only: only set those attrs that have changed (limits errors)
        :param verbose: report back all data set, changed or failed
        :param skip_measurements: if true (defulat) we do not store those attrs that are skeleton specific
            only those which control the remapping
        '''

        dataTypes = [float, int, bool]  # data types we're going to handle

        status = {'failed': {}, 'set': {}, 'changed': {}}
        if not os.path.exists(filepath):
            raise IOError('Filepath not found! %s' % filepath)

        for key, val in r9General.readJson(filepath).items():
            try:
                if type(val) in dataTypes:
                    if skip_measurements and key in self.measurements:
                        continue
                    if skip_rolls and key in self.roll_pitch:
                        continue

                    # only load data that's different from the default config
                    if changes_only:
                        current = getattr(self, key)
                        if not current == val:
                            setattr(self, key, val)
                            status['changed'][key] = (current, val)
                    else:
                        setattr(self, key, val)
                        status['set'][key] = val
            except:
                status['failed'][key] = (val, traceback.format_exc())
        if verbose:
            for attr, val in sorted(status['set'].items()):
                log.info('Set HIKProperty : %s : %s' % (attr, val))

            for attr, val in sorted(status['changed'].items()):
                log.info('Changed HIKProperty : %s : from %s >  %s' % (attr, val[0], val[1]))

            for attr, val in status['failed'].items():
                log.info('Failed to set HIKProperty : %s : %s' % (attr, val[0]))
                log.debug(val[1])

        return status


# EXPERIMENTAL CALLS ==========================================================

def monitorHUDaddCBAttrs():
    '''
    ChannelBox wrappers for the HUD :
    Adds selected attrs from the CB to a MetaHUD node for monitoring,
    if HUD node already exists this will simply add more attrs to it
    '''
    import Red9_CoreUtils as r9Core
    node = cmds.ls(sl=True, l=True)[0]
    attrs = cmds.channelBox('mainChannelBox', q=True, selectedMainAttributes=True)
    currentHUDs = getMetaNodes(mTypes=MetaHUDNode, mAttrs='mNodeID=CBMonitorHUD')
    if not currentHUDs:
        metaHUD = MetaHUDNode(name='CBMonitorHUD')
    else:
        metaHUD = currentHUDs[0]
    if attrs:
        for attr in attrs:
            log.info('connecting cbAttr to meta: %s' % attr)
            monitoredAttr = '%s_%s' % (r9Core.nodeNameStrip(node), attr)
            metaHUD.addMonitoredAttr(monitoredAttr,
                                     value=cmds.getAttr('%s.%s' % (node, attr)),
                                     refresh=False)
            cmds.connectAttr('%s.%s' % (node, attr), '%s.%s' % (metaHUD.mNode, monitoredAttr))
    metaHUD.refreshHud()
    cmds.select(node)

def monitorHUDManagement(func):
    '''
    ChannelBox wrappers for the HUD : kill any current MetaHUD headsUpDisplay blocks
    '''
    metaHUD = None
    currentHUDs = getMetaNodes(mTypes=MetaHUDNode, mAttrs='mNodeID=CBMonitorHUD')
    if currentHUDs:
        metaHUD = currentHUDs[0]

    if func == 'delete':
        if metaHUD:
            metaHUD.delete()
        else:
            # No metaData node, scene may have been deleted but the HUD
            # may still be up and active
            HUDS = cmds.headsUpDisplay(lh=True)
            for hud in HUDS:
                if 'MetaHUDConnector' in hud:
                    print('killing HUD : ', hud)
                    cmds.headsUpDisplay(hud, remove=True)
    if func == 'refreshHeadsUp':
        metaHUD.headsUpOnly = True
        metaHUD.refreshHud()
    if func == 'refreshSliders':
        metaHUD.headsUpOnly = False
        metaHUD.refreshHud()
    if func == 'kill':
        metaHUD.killHud()


def monitorHUDremoveCBAttrs():
    '''
    ChannelBox wrappers for the HUD : remove attrs from the MetaHUD
    '''
    import Red9_CoreUtils as r9Core
    currentHUDs = getMetaNodes(mTypes=MetaHUDNode, mAttrs='mNodeID=CBMonitorHUD')
    if currentHUDs:
        metaHUD = currentHUDs[0]
        node = cmds.ls(sl=True, l=True)[0]
        attrs = cmds.channelBox('mainChannelBox', q=True, selectedMainAttributes=True)
        if attrs:
            metaHUD.killHud()
            for attr in attrs:
                monitoredAttr = '%s_%s' % (r9Core.nodeNameStrip(node), attr)
                print('removing attr :', attr, monitoredAttr)
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
    huds = getMetaNodes(mInstances=MetaHUDNode)
    if huds:
        for hud in huds:
            try:
                hud.killHud()
            except:
                log.debug('failed to remove HUD metanode')
    HUDS = cmds.headsUpDisplay(lh=True)
    if HUDS:
        for hud in HUDS:
            if 'MetaHUDConnector' in hud:
                cmds.headsUpDisplay(hud, remove=True)

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
    def __init__(self, *args, **kws):
        super(MetaHUDNode, self).__init__(*args, **kws)

        if self.cached:
            log.debug('CACHE : Aborting __init__ on pre-cached %s Object' % self.__class__)
            return

        self.hudGroupActive = False
        self.eventTriggers = cmds.headsUpDisplay(le=True)
        self._blocksize = 'small'
        self.headsUpOnly = True

        self.addAttr('monitorAttrCache', value='[]', attrType='string')  # cache the HUD names so this runs between sessions
        self.monitorAttrs = self.monitorAttrCache
        self.addAttr('section', 1)
        self.addAttr('block', 1)
        self.addAttr('allowExpansion', True)  # if a section can't contain all elements then expand to the section below
        self.addAttr('eventTrigger', attrType='enum', value=0, enumName=':'.join(['attachToRefresh', 'timeChanged']))

        HUDS = cmds.headsUpDisplay(lh=True)
        for hud in HUDS:
            if 'MetaHUDConnector' in hud:
                self.hudGroupActive = True

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
        if attr not in self.monitorAttrs:
            self.addAttr(attr, value=value, attrType=attrType)
            self.monitorAttrs.append(attr)
            # serialize back to the node
            self.monitorAttrCache = self.monitorAttrs
            if self.hudGroupActive == True and refresh:
                try:
                    self.refreshHud()
                except:
                    log.debug('addMonitorAttr failed')
        else:
            log.info('Hud attr already exists on metaHud Node')

    def removeMonitoredAttr(self, attr):
        '''
        Remove an attr from the MetaNode and refresh the HUD to reflect the removal

        :param attr: attr to be removed from monitoring
        '''
        self.__delattr__(attr)

    # def getEventTrigger(self,*args):
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
        # Attributes:
        #        - Section 1, block 0, represents the top second slot of the view.
        #        - Set the _blocksize to "medium", instead of the default "small"
        #        - Assigned the HUD the label: "Position"
        #        - Defined the label font size to be large
        #        - Assigned the HUD a command to run on a SelectionChanged trigger
        #        - Attached the attributeChange node change to the SelectionChanged trigger
        #          to allow the update of the data on attribute changes.

        for i, attr in enumerate(self.monitorAttrs):
            section = self.section
            block = self.block + i
            if self.allowExpansion and i > 17:
                section = self.section + 5
                block = block - 17
                i = 0

            metaHudItem = 'MetaHUDConnector%s' % attr

            if self.headsUpOnly:
                if self.eventTrigger == 1:  # timeChanged
                    cmds.headsUpDisplay(metaHudItem,
                                        section=section,
                                        block=block,
                                        blockSize=self._blocksize,
                                        label=attr,
                                        labelFontSize=self._blocksize,
                                        allowOverlap=True,
                                        # command=partial(getattr,self,attr),
                                        command=partial(self.__compute__, attr),
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
                                        command=partial(self.__compute__, attr))
            else:
                print('node : ', self.mNode, ' attrs : ', attr)
                connectedData = cmds.listConnections('%s.%s' % (self.mNode, attr),
                                                   connections=True,
                                                   skipConversionNodes=True,
                                                   plugs=True)[-1].split('.')
                cmds.hudSliderButton(metaHudItem,
                                     section=section,
                                     block=block,
                                     vis=True,
                                     sliderLabel=attr,
                                     sliderDragCommand=partial(self.setSlidertoAttr, metaHudItem, '%s.%s' % (connectedData[0], connectedData[1])),
                                     value=0, type='float',
                                     sliderLabelWidth=150,
                                     valueWidth=60,
                                     sliderLength=150,
                                     bl='Reset',
                                     bw=60, bsh='rectangle',
                                     buttonReleaseCommand=partial(self.resetSlider, metaHudItem, '%s.%s' % (connectedData[0], connectedData[1])))
                try:
                    attrMin = cmds.attributeQuery(connectedData[1], node=connectedData[0], min=True)
                    if attrMin:
                        cmds.hudSliderButton(metaHudItem, e=True, min=attrMin[0])
                except:
                    cmds.hudSliderButton(metaHudItem, e=True, min=-1000)
                try:
                    attrMax = cmds.attributeQuery(connectedData[1], node=connectedData[0], max=True)
                    if attrMax:
                        cmds.hudSliderButton(metaHudItem, e=True, max=attrMax[0])
                except:
                    cmds.hudSliderButton(metaHudItem, e=True, max=1000)

        self.hudGroupActive = True

    def getConnectedAttr(self, attr):
        return cmds.listConnections('%s.%s' % (self.mNode, attr), c=True, p=True)[-1]

    def getConnectedNode(self, attr):
        return cmds.listConnections('%s.%s' % (self.mNode, attr))[0]

    def setSlidertoAttr(self, slider, attr):
        cmds.setAttr(attr, cmds.hudSliderButton(slider, query=True, v=True))

    def resetSlider(self, slider, attr):
        '''
        If the HUD is made up of sliders this resets them

        :param slider: slider to reset in the HUD
        :param attr: attr to reset on the mNode
        '''
        value = 0
        try:
            value = cmds.addAttr(q=True, dv=True)
        except:
            pass
        cmds.setAttr(attr, value)
        cmds.hudSliderButton(slider, e=True, v=value)

    def showHud(self, value):
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
            if cmds.headsUpDisplay(hud, exists=True):
                cmds.headsUpDisplay(hud, remove=True)
        self.hudGroupActive = False

    def refreshHud(self):
        '''
        Refresh the HUD by killing it and re-drawing it from scratch
        '''
        if self.hudGroupActive is True:
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
        wasActive = False
        if self.hudGroupActive is True:
            self.killHud()
            wasActive = True
        self.monitorAttrs.remove(attr)
        # serialize back to the node
        self.monitorAttrCache = self.monitorAttrs
        super(MetaHUDNode, self).__delattr__(attr)
        if wasActive is True:
            self.drawHUD()


'''
if we reload r9Meta on it's own then the registry used in construction of
the nodes will fall out of sync and invalidate the systems. This is a catch
to that.
'''
# registerMClassInheritanceMapping()

def metaData_sceneCleanups(*args):
    '''
    Registered on SceneOpen and SceneNew callbacks so that the MetaData Cache is cleared and
    any registered HUD is killed off
    '''
    if not r9Setup.mayaIsBatch():
        hardKillMetaHUD()
    resetCacheOnSceneNew()


# Setup the callbacks to clear the cache when required
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
