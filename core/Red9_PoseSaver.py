'''
..
    Red9 Studio Pack: Maya Pipeline Solutions
    Author: Mark Jackson
    email: rednineinfo@gmail.com

    Red9 blog : http://red9-consultancy.blogspot.co.uk/
    MarkJ blog: http://markj3d.blogspot.co.uk


This is a new implementation of the PoseSaver core, same file format
and ConfigObj but now supports relative pose data handled via a
posePointCloud and the snapping core

.. note::

    I use the node short name as the key in the dictionary so
    ALL NODES must have unique names or you may get unexpected  results!

'''

from __future__ import print_function

import Red9.startup.setup as r9Setup
import Red9_CoreUtils as r9Core
import Red9_General as r9General
import Red9_AnimationUtils as r9Anim
import Red9_Meta as r9Meta
import maya.OpenMaya as OpenMaya


import maya.cmds as cmds
import os
import Red9.packages.configobj as configobj
import time
import getpass
import json


import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

LANGUAGE_MAP = r9Setup.LANGUAGE_MAP

def getFolderPoseHandler(posePath):
    '''
    Check if the given directory contains a poseHandler.py file
    if so return the filename. PoseHandlers are a way of extending or
    over-loading the standard behaviour of the poseSaver, see Vimeo for
    a more detailed explanation.

    TODO: have this also accept a pointer to a handler file rather than a direct
    poseHnadler.py file in each folder. This means we could point a folder to a generic handler
    inside our presets folder rather than having the code logic in each folder.
    '''
    poseHandler = None
    poseHandlers = [py for py in os.listdir(posePath) if py.endswith('poseHandler.py')]
    if poseHandlers:
        poseHandler = poseHandlers[0]
    return poseHandler


class DataMap(object):
    '''
    New base class for handling data storage and reloading with intelligence
    '''

    def __init__(self, filterSettings=None, *args, **kws):
        '''
        The idea of the DataMap is to make the node handling part of any system generic.
        This allows us to use this baseClass to build up things like poseSavers and all
        we have to worry about is the data save / extraction part, all the node handling
        and file handling is already done by this class ;)

        Note that we're not passing any data in terms of nodes here, We'll deal with
        those in the Save and Load calls.
        '''
        self.poseDict = {}
        self.infoDict = {}
        self.skeletonDict = {}
        self.settings_internal = None  # filterSettings object synced from the internal file block

        self.file_ext = ''  # extension the file will be saved as
        self.filepath = ''  # path to load / save
        self.__filepath = ''
        self.filename = ''  # short name of the pose
        self._read_mute = False  # a back-door to prevent the _readPose() call happening, allowing us to modify cached data safely

        self.dataformat = 'config'
        self._dataformat_resolved = None

        self.mayaUpAxis = r9Setup.mayaUpAxis()
        self.thumbnailRes = [128, 128]
        self.unitconversion = True  # convert linear units to correct for sceneUnit differences
        self.world_space = False

        self.__metaPose = False
        self.metaRig = None  # filled by the code as we process
        self.matchMethod = 'base'  # method used to match nodes internally in the poseDict
        self.useFilter = True
        self.prioritySnapOnly = False  # mainly used by any load relative calls, determines whether to use the internal filters priority list
        self.skipAttrs = []  # attrs to completely ignore in any pose handling

        self.nodesToStore = []  # built by the buildDataMap func
        self.nodesToLoad = []  # build in the processPoseFile func

        # make sure we have a settings object
        if filterSettings:
            if issubclass(type(filterSettings), r9Core.FilterNode_Settings):
                self.settings = filterSettings
                self.__metaPose = self.settings.metaRig
            else:
                raise StandardError('filterSettings param requires an r9Core.FilterNode_Settings object')
            self.settings.printSettings()
        else:
            self.settings = r9Core.FilterNode_Settings()
            self.__metaPose = self.settings.metaRig

    @property
    def metaPose(self):
        '''
        this flag adds in the additional MetaData block for all the matching code and info extraction.
        True if self.metaRig is filled, self.settings.metaRig=True or self.metaPose=True
        '''
        if self.metaRig:
            return True
        if self.settings.metaRig:
            return True
        return self.__metaPose

    @metaPose.setter
    def metaPose(self, val):
        self.__metaPose = val
        self.settings.metaRig = val

    @property
    def filepath(self):
        return self.__filepath

    @filepath.setter
    def filepath(self, path):
        if path and self.file_ext:
            self.__filepath = '%s%s' % (os.path.splitext(path)[0], self.file_ext)
        else:
            self.__filepath = path
        self.filename = os.path.splitext(os.path.basename(self.filepath))[0]

    def _pre_load(self, *args, **kws):
        '''
        called directly before the loadData call so you have access
        to manage the undoQueue etc if subclassing
        '''
        pass

    def _post_load(self, *args, **kws):
        '''
        called directly after the loadData call so you have access
        to manage the undoQueue etc if subclassing
        '''
        pass

    def setMetaRig(self, node):
        '''
        Master call to bind and set the mRig for the DataMap

        :param node: node to set the mRig from or instance of an mRig object
        '''
        log.debug('setting internal metaRig from given node : %s' % node)
        if r9Meta.isMetaNodeInherited(node, 'MetaRig'):
            self.metaRig = r9Meta.MetaClass(node)
        else:
            self.metaRig = r9Meta.getConnectedMetaSystemRoot(node)
        log.debug('setting internal metaRig : %s' % self.metaRig)
        return self.metaRig

    def hasFolderOverload(self):
        '''
        modified so you can now prefix the poseHandler.py file
        makes it easier to keep track of in a production environment
        '''
        self.poseHandler = None
        if self.filepath:
            self.poseHandler = getFolderPoseHandler(os.path.dirname(self.filepath))
        return self.poseHandler

    def getNodesFromFolderConfig(self, rootNode, mode):
        '''
        if the poseFolder has a poseHandler.py file use that to
        return the nodes to use for the pose instead

        :param rootNode: rootNode passed to the search poseHandlers
            poseGetNodesLoad or poseGetNodesSave functions
        :param mode: 'save' or 'load'
        '''
        import imp
        log.debug('getNodesFromFolderConfig - useFilter=True : custom poseHandler running')
        posedir = os.path.dirname(self.filepath)
        print('imp : ', self.poseHandler.split('.py')[0], '  :  ', os.path.join(posedir, self.poseHandler))
        tempPoseFuncs = imp.load_source(self.poseHandler.split('.py')[0], os.path.join(posedir, self.poseHandler))

        if mode == 'load':
            nodes = tempPoseFuncs.poseGetNodesLoad(self, rootNode)
        if mode == 'save':
            nodes = tempPoseFuncs.poseGetNodesSave(self, rootNode)
        del(tempPoseFuncs)

        return nodes

    def getNodes(self, nodes):
        '''
        get the nodes to process
        This is designed to allow for specific hooks to be used from user
        code stored in the pose folder itself.

        :param nodes: nodes passed to the filter calls

        .. note::
            Update : Aug 2016
            Because this calls FilterNode to get the data when useFilter=True it
            allows for any mRig with internal filterSettings bound to it to dynamically
            modify the settings on the fly to suit. This is a big update in handling
            for ProPack to integrate without having to massively restructure

        '''
        if not type(nodes) == list:
            nodes = [nodes]
        if self.useFilter:
            log.debug('getNodes - useFilter=True : filteActive=True  - no custom poseHandler')
            if self.settings.filterIsActive():
                return r9Core.FilterNode(nodes, self.settings).processFilter()  # main node filter
            else:
                log.debug('getNodes - useFilter=True : filteActive=False - no custom poseHandler')
                return nodes
        else:
            log.debug('getNodes - useFilter=False : no custom poseHandler')
            return nodes

    def getSkippedAttrs(self, rootNode=None):
        '''
        the returned list of attrs from this function will be
        COMPLETELY ignored by the pose system. They will not be saved
        or loaded.

        .. note::
            The collection of these attrs is currently only supported under MetaRig
            IF self.skipAttrs was passed into the object then we do NOT run this func, returning the currently setup list
        '''
        if self.skipAttrs:
            return self.skipAttrs
        if self.metaRig and self.metaRig.hasAttr('poseSkippedAttrs'):
            return self.metaRig.poseSkippedAttrs
        return []

    def getMaintainedAttrs(self, nodesToLoad, parentSpaceAttrs):
        '''
        Attrs returned here will be cached prior to pose load, then restored in-tact afterwards

        :param nodesToLoad: nodes that the pose is about to load the data too,
            this is the already processed nodeList
        :param parentSpaceAttrs: attributes we want to be ignored by the load system
        '''
        parentSwitches = []
        if not type(parentSpaceAttrs) == list:
            parentSpaceAttrs = [parentSpaceAttrs]
        for child in nodesToLoad:
            for attr in parentSpaceAttrs:
                if cmds.attributeQuery(attr, exists=True, node=child):
                    parentSwitches.append((child, attr, cmds.getAttr('%s.%s' % (child, attr))))
                    log.debug('parentAttrCache : %s > %s' % (child, attr))
        return parentSwitches

    # --------------------------------------------------------------------------------
    # Data Collection - Build ---
    # --------------------------------------------------------------------------------

    def _getTranforms(self, node, worldspace=True):
        '''
        get the transform data so we can pass it into the _collectNodeData_attrs
        as a new worldspace block (default)

        :param node: the node we're inspecting
        :param worldspace: bool, get the transforms back in either MSpace.kWorld or MSpace.kTransform
        '''
        import math
        euler = []

        # import maya.OpenMaya as OpenMaya
        dagpath = OpenMaya.MDagPath()
        selList = OpenMaya.MSelectionList()
        selList.add(node)
        selList.getDagPath(0, dagpath)
        _mFntrans = OpenMaya.MFnTransform(dagpath)

        if worldspace:
            _mSpace = OpenMaya.MSpace.kWorld
        else:
            _mSpace = OpenMaya.MSpace.kTransform

        trans = OpenMaya.MVector(_mFntrans.rotatePivot(_mSpace))
        rots = OpenMaya.MQuaternion()
        _mFntrans.getRotation(rots, _mSpace)

        # for some reason this can cause a hard Maya hang!!!!
        # trying to track it down but if you experience it comment this one line out!
#         euler = map(math.degrees, rots.asEulerRotation())

        _eulers = rots.asEulerRotation()
        euler = [math.degrees(_eulers[0]),
                 math.degrees(_eulers[1]),
                 math.degrees(_eulers[2])]

        return {'translation': [trans.x, trans.y, trans.z],
                'quaternion': [rots.x, rots.y, rots.z, rots.w],
                'euler': euler}

    def _collectNodeData_attrs(self, node, key):
        '''
        Capture and build attribute data from this node and fill the
        data to the datamap[key]
        '''
        channels = r9Anim.getSettableChannels(node, incStatics=True)
        if channels:
            self.poseDict[key]['attrs'] = {}
            self.poseDict[key]['attrs_kWorld'] = {}

            for attr in channels:
                if attr in self.skipAttrs:
                    log.debug('Skipping attr as requested : %s' % attr)
                    continue
                try:
                    if cmds.getAttr('%s.%s' % (node, attr), type=True) == 'TdataCompound':  # blendShape weights support
                        attrs = cmds.aliasAttr(node, q=True)[::2]  # extract the target channels from the multi
                        for attr in attrs:
                            self.poseDict[key]['attrs'][attr] = cmds.getAttr('%s.%s' % (node, attr))
                    else:
                        self.poseDict[key]['attrs'][attr] = cmds.getAttr('%s.%s' % (node, attr))
                except:
                    log.debug('%s : attr is invalid in this instance' % attr)

            if cmds.nodeType(node) in ['transform', 'joint']:
                self.poseDict[key]['attrs_kWorld'] = self._getTranforms(node, worldspace=True)

    def _collectNodeData(self, node, key):
        '''
        To Be Overloaded : what data to push into the main dataMap
        for each node found collected. This is the lowest level collect call
        for each node in the array.
        '''
        self._collectNodeData_attrs(node, key)

    def _buildBlock_info(self, nodes=None):
        '''
        Generic Info block for the data file, this could do with expanding
        '''
        self.infoDict['author'] = getpass.getuser()
        self.infoDict['date'] = time.ctime()
        self.infoDict['currentTime'] = cmds.currentTime(q=True)
        self.infoDict['timeUnit'] = cmds.currentUnit(q=True, fullName=True, time=True)
        self.infoDict['sceneUnits'] = cmds.currentUnit(q=True, fullName=True, linear=True)
        self.infoDict['upAxis'] = cmds.upAxis(q=True, axis=True)
        self.infoDict['metaPose'] = self.metaPose
        self.infoDict['filepath'] = cmds.file(q=True, sn=True)

        if self.metaRig:
            self.infoDict['metaRigNode'] = self.metaRig.mNode
            self.infoDict['metaRigNodeID'] = self.metaRig.mNodeID
            if self.metaRig.hasAttr('version'):
                self.infoDict['version'] = self.metaRig.version
            if self.metaRig.hasAttr('rigType'):
                self.infoDict['rigType'] = self.metaRig.rigType
            self.infoDict.update(self.metaRig.gatherInfo())

#         else:
#             # this is dealt with in the gatherInfo call from mRig
#             if cmds.referenceQuery(nodes[0], inr=True):
#                 _root = r9Meta.MetaClass(nodes[0])
#                 self.infoDict['namespace'] = _root.nameSpace()
#                 self.infoDict['namespace_full'] = _root.nameSpaceFull()
#                 self.infoDict['referenced_rigPath'] = _root.referencePath()
#                 self.infoDict['referenced_grp'] = _root.referenceGroup()
        if self.rootJnt:
            self.infoDict['skeletonRootJnt'] = self.rootJnt

    def _buildBlock_poseDict(self, nodes):
        '''
        Build the internal poseDict up from the given nodes. This is the
        core of the Pose System and the main dataMap used to store and retrieve data
        '''
        getMirrorID = r9Anim.MirrorHierarchy().getMirrorCompiledID
        if self.metaPose:
            getMetaDict = self.metaRig.getNodeConnectionMetaDataMap  # optimisation

        for i, node in enumerate(nodes):
            key = r9Core.nodeNameStrip(node)
            self.poseDict[key] = {}
            self.poseDict[key]['ID'] = i  # selection order index
            self.poseDict[key]['longName'] = node  # longNode name
            mirrorID = getMirrorID(node)
            if mirrorID:
                self.poseDict[key]['mirrorID'] = mirrorID  # add the mirrorIndex
            if self.metaPose:
                self.poseDict[key]['metaData'] = getMetaDict(node)  # metaSystem the node is wired too
            # the above blocks are the generic info used to map the data on load
            # this call is the specific collection of data for this node required by this map type
            self._collectNodeData(node, key)

    def buildBlocks_fill(self, nodes=None):
        '''
        To Be Overloaded : What capture routines to run in order to build the DataMap up.
        Note that the self._buildBlock_poseDict(nodes) calls the self._collectNodeData per node
        as a way of gathering what info to be stored against each node.
        '''
        if not nodes:
            nodes = self.nodesToStore
        self.poseDict = {}
        self._buildBlock_info(nodes)
        self._buildBlock_poseDict(nodes)

    def buildDataMap(self, nodes):
        '''
        build the internal dataMap dict, useful as a separate func so it
        can be used in the PoseCompare class easily. This is the main internal call
        for managing the actual pose data for save

        .. note::
            this replaces the original pose call self.buildInternalPoseData()
        '''
        self.nodesToStore = []

        self.metaRig = None
        self.rootJnt = None
        if not type(nodes) == list:
            nodes = [nodes]  # cast to list for consistency
        rootNode = nodes[0]

        if self.settings.filterIsActive() and self.useFilter:
            if self.metaPose:
                if self.setMetaRig(rootNode):
                    self.rootJnt = self.metaRig.getSkeletonRoots()
                    if self.rootJnt:
                        self.rootJnt = self.rootJnt[0]
            else:
                if cmds.attributeQuery('exportSkeletonRoot', node=rootNode, exists=True):
                    connectedSkel = cmds.listConnections('%s.%s' % (rootNode, 'exportSkeletonRoot'), destination=True, source=True)
                    if connectedSkel and cmds.nodeType(connectedSkel) == 'joint':
                        self.rootJnt = connectedSkel[0]
                    elif cmds.nodeType(rootNode) == 'joint':
                        self.rootJnt = rootNode
#                 elif cmds.attributeQuery('animSkeletonRoot',node=rootNode, exists=True):
#                     connectedSkel=cmds.listConnections('%s.%s' % (rootNode,'animSkeletonRoot'),destination=True,source=True)
#                     if connectedSkel and cmds.nodeType(connectedSkel)=='joint':
#                         self.rootJnt=connectedSkel[0]
#                     elif cmds.nodeType(rootNode)=='joint':
#                         self.rootJnt=rootNode
                elif self.settings.nodeTypes == ['joint']:
                    self.rootJnt = rootNode
        else:
            if self.metaPose:
                self.setMetaRig(rootNode)

        # fill the skip list, these attrs will be totally ignored by the code
        self.skipAttrs = self.getSkippedAttrs(rootNode)

        if self.hasFolderOverload():  # and self.useFilter:
            self.nodesToStore = self.getNodesFromFolderConfig(nodes, mode='save')
        else:
            self.nodesToStore = self.getNodes(nodes)

        if not self.nodesToStore:
            raise IOError('No Matching Nodes found to store the pose data from')

        return self.nodesToStore

    # --------------------------------------------------------------------------------
    # Data Mapping - Apply ---
    # --------------------------------------------------------------------------------

    @r9General.Timer
    def _applyData_attrs(self, *args, **kws):
        '''
        Load call for dealing with attrs :
        use self.matchedPairs for the process list of pre-matched
        tuples of (poseDict[key], node in scene)

        fix: 07/11/18: added the clamp=True to the set calls so we set values to max/min if the input value is out of range
        '''
        _attrs_linear = ['translateX', 'translateY', 'translateZ']

        # setup unit conversions for linear attrs
        _unitsfile = None
        _conversion_needed = False
        _sceneunits = cmds.currentUnit(q=True, fullName=True, linear=True)
        try:
            _unitsfile = self.infoDict['sceneUnits']
            if not _unitsfile == _sceneunits:
                _conversion_needed = True
        except:
            log.debug("This PoseFile doesn't not support scene unit conversion")

        for key, dest in self.matchedPairs:
            log.debug('Applying Key Block : %s' % key)
            try:
                if 'attrs' not in self.poseDict[key]:
                    continue
                for attr, val in self.poseDict[key]['attrs'].items():
                    if attr in self.skipAttrs:
                        log.debug('Skipping attr as requested : %s' % attr)
                        continue
                    try:
                        val = eval(val)
                    except:
                        pass
                    try:
                        # only unit convert linear attrs if the file supports it and it's needed!
                        if _conversion_needed and self.unitconversion and attr in _attrs_linear:
                            _converted = r9Core.convertUnits_uiToInternal(r9Core.convertUnits_internalToUI(val, _unitsfile), _sceneunits)
                            log.debug('node : %s : attr : %s : UnitConverted : val %s == %s' % (dest, attr, val, _converted))
                            cmds.setAttr('%s.%s' % (dest, attr), _converted, c=True)
                        else:
                            log.debug('node : %s : attr : %s : val %s' % (dest, attr, val))
                            cmds.setAttr('%s.%s' % (dest, attr), val, c=True)
                    except StandardError, err:
                        log.debug(err)
            except:
                log.debug('Pose Object Key : %s : has no Attr block data' % key)

    @r9General.Timer
    def _applyData_kWorld_attrs(self, worldspace=True, *args, **kws):
        '''
        added : 11/03/19 TESTING

        Load call for dealing with attrs in kWorld space. Still need to
        deal with hierarchy when we load now we're dealing in world space as
        parent / child behaviour will get screwed if not loaded in the correct order

        '''
        # setup unit conversions for linear attrs
        _unitsfile = None
        _conversion_needed = False
        _sceneunits = cmds.currentUnit(q=True, fullName=True, linear=True)
        try:
            _unitsfile = self.infoDict['sceneUnits']
            if not _unitsfile == _sceneunits:
                _conversion_needed = True
        except:
            log.debug("This PoseFile doesn't not support scene unit conversion")

        if worldspace:
            _mSpace = OpenMaya.MSpace.kWorld
        else:
            _mSpace = OpenMaya.MSpace.kTransform

        for key, dest in self.matchedPairs:
            log.debug('Applying Key Block : %s' % key)
            try:
                if 'attrs_kWorld' not in self.poseDict[key]:
                    continue
                try:
                    dagpath = OpenMaya.MDagPath()
                    selList = OpenMaya.MSelectionList()
                    selList.add(dest)
                    selList.getDagPath(0, dagpath)
                    _mFntrans = OpenMaya.MFnTransform(dagpath)

                    tran_data = []
                    rot_data = self.poseDict[key]['attrs_kWorld']['quaternion']
                    rot_data = [eval(rot_data[0]), eval(rot_data[1]), eval(rot_data[2]), eval(rot_data[3])]

                    for attr in self.poseDict[key]['attrs_kWorld']['translation']:
                        if _conversion_needed and self.unitconversion:
                            # only unit convert linear attrs if the file supports it and it's needed!
                            _converted = r9Core.convertUnits_uiToInternal(r9Core.convertUnits_internalToUI(attr, _unitsfile), _sceneunits)
                            log.debug('node : %s : UnitConverted : val %s == %s' % (dest, attr, _converted))
                            tran_data.append(eval(attr))
                        else:
                            log.debug('node : %s : val %s' % (dest, attr))
                            tran_data.append(eval(attr))

                    trans = OpenMaya.MVector(tran_data[0], tran_data[1], tran_data[2])
                    rots = OpenMaya.MQuaternion(rot_data[0], rot_data[1], rot_data[2], rot_data[3])

                    _mFntrans.setRotation(rots, _mSpace)
                    _mFntrans.setTranslation(trans, _mSpace)

                except StandardError, err:
                    log.debug(err)
            except:
                log.debug('Pose Object Key : %s : has no Attr block data' % key)

    def _applyData(self, *args, **kws):
        '''
        To Be Overloaded:
        Main apply block run after we've read the data and matched all nodes
        '''
        self._applyData_attrs()

    # --------------------------------------------------------------------------------
    # Process the data ---
    # --------------------------------------------------------------------------------

    def _writePose(self, filepath=None, force=False):
        '''
        Write the Pose ConfigObj to file
        '''
        if not filepath:
            filepath = self.filepath
        if not force:
            if os.path.exists(filepath) and not os.access(filepath, os.W_OK):
                raise IOError('File is Read-Only - write aborted : %s' % filepath)
        # =========================
        # write to ConfigObject
        # =========================
        if self.dataformat == 'config':
            ConfigObj = configobj.ConfigObj(indent_type='\t', encoding='utf-8')
            ConfigObj['info'] = self.infoDict
            ConfigObj['filterNode_settings'] = self.settings.__dict__
            ConfigObj['poseData'] = self.poseDict
            if self.skeletonDict:
                ConfigObj['skeletonDict'] = self.skeletonDict
            ConfigObj.filename = filepath
            ConfigObj.write()
            self._dataformat_resolved = 'config'
        # =========================
        # write to JSON format
        # =========================
        elif self.dataformat == 'json':
            data = {}
            data['info'] = self.infoDict
            data['filterNode_settings'] = self.settings.__dict__
            data['poseData'] = self.poseDict
            if self.skeletonDict:
                data['skeletonDict'] = self.skeletonDict
            with open(filepath, 'w') as f:
                f.write(json.dumps(data, sort_keys=True, indent=4))
                f.close()
            self._dataformat_resolved = 'json'

    @r9General.Timer
    def _readPose(self, filename=None, force=False):
        '''
        Read the pose file and build up the internal poseDict

        :param filename: path to the file to read
        :param force: fore the read, ignoring the internal _read_mute var
        '''
        if self._read_mute and not force:
            return
        if not filename:
            filename = self.filepath
        if filename:
            if os.path.exists(filename):
                # =========================
                # read JSON format
                # =========================
                if self.dataformat == 'json':
                    try:
                        with open(filename, 'r') as f:
                            data = json.load(f)
                        self.poseDict = data['poseData']
                        if 'info' in data.keys():
                            self.infoDict = data['info']
                        if 'skeletonDict' in data.keys():
                            self.skeletonDict = data['skeletonDict']
                        self._dataformat_resolved = 'json'
                    except IOError, err:
                        self._dataformat_resolved = 'config'
                        log.info('JSON : DataMap format failed to load, reverting to legacy ConfigObj')
                # =========================
                # read ConfigObject
                # =========================
                if self._dataformat_resolved == 'config' or self.dataformat == 'config':
                    # for key, val in configobj.ConfigObj(filename)['filterNode_settings'].items():
                    #    self.settings.__dict__[key]=decodeString(val)
                    data = configobj.ConfigObj(filename, encoding='utf-8')
                    self.poseDict = data['poseData']
                    if 'info' in data:
                        self.infoDict = data['info']
                    if 'skeletonDict' in data:
                        self.skeletonDict = data['skeletonDict']
                    if 'filterNode_settings' in data:
                        self.settings_internal = r9Core.FilterNode_Settings()
                        self.settings_internal.setByDict(data['filterNode_settings'])
                    self._dataformat_resolved = 'config'
            else:
                raise StandardError('Given filepath doesnt not exist : %s' % filename)
        else:
            raise StandardError('No FilePath given to read the pose from')

    def processPoseFile(self, nodes):
        '''
        pre-loader function that processes all the nodes and data prior to
        actually calling the load... why? this is for the poseMixer for speed.
        This reads the file, matches the nodes to the internal file data and fills
        up the self.matchedPairs data [(src,dest),(src,dest)]

        .. note::
            this replaced the original call self._poseLoad_buildcache()
        '''
        self.nodesToLoad = []

        if not type(nodes) == list:
            nodes = [nodes]  # cast to list for consistency

        if self.filepath and not os.path.exists(self.filepath):
            raise StandardError('Given Path does not Exist')

        if self.metaPose:
            # set the mRig in a consistent manner
            self.setMetaRig(nodes[0])
            if 'metaPose' in self.infoDict and self.metaRig:
                try:
                    if eval(self.infoDict['metaPose']):
                        self.matchMethod = 'metaData'
                except:
                    self.matchMethod = 'metaData'
            else:
                log.debug('Warning, trying to load a NON metaPose to a MRig - switching to NameMatching')

        if self.filepath and self.hasFolderOverload():  # and useFilter:
            self.nodesToLoad = self.getNodesFromFolderConfig(nodes, mode='load')
        else:
            self.nodesToLoad = self.getNodes(nodes)
        if not self.nodesToLoad:
            raise StandardError('Nothing selected or returned by the filter to load the pose onto')

        if self.filepath:
            self._readPose(self.filepath)
            log.debug('Pose Read Successfully from : %s' % self.filepath)

        # fill the skip list, these attrs will be totally ignored by the code
        self.skipAttrs = self.getSkippedAttrs(nodes[0])

        # build the master list of matched nodes that we're going to apply data to
        # Note: this is built up from matching keys in the poseDict to the given nodes
        self.matchedPairs, unmatched = self._matchNodesToPoseData(self.nodesToLoad, returnfails=True)

        # added 14/02/19: if the metaData mNodeID has been changed between rigs then the proper
        # metaData match will fail as it's based on mNodeID and mAttr matches for all nodes.
        # if this happens then regress the testing back to stripPrefix for all failed nodes
        if self.matchMethod == 'metaData' and unmatched:
            log.info('Regressing matchMethod from "metaData" to "stripPrefix" for failed matches within the mNode ConnectionMap')
            rematched = self._matchNodesToPoseData(unmatched, matchMethod='stripPrefix')
            if rematched:
                self.matchedPairs.extend(rematched)

        return self.nodesToLoad

    @r9General.Timer
    def _matchNodesToPoseData(self, nodes, matchMethod=None, returnfails=False):
        '''
        Main filter to extract matching data pairs prior to processing
        return : tuple such that :  (poseDict[key], destinationNode)
        NOTE: I've changed this so that matchMethod is now an internal PoseData attr

        :param nodes: nodes to try and match from the poseDict
        :param matchMethod: if given this over-rides self.matchMethod so you can do additional checks without mutating the class var
        :param returnfails: if True we return [matchedData, unmatched] so that we can pass the unmatched list for further processing
        '''
        matchedPairs = []
        unmatched = []
        log.debug('using matchMethod : %s' % self.matchMethod)

        if not matchMethod:
            matchMethod = self.matchMethod

        # standard match method logic
        if matchMethod == 'stripPrefix' or matchMethod == 'base':
            log.debug('matchMethodStandard : %s' % matchMethod)
            matchedPairs = r9Core.matchNodeLists([key for key in self.poseDict.keys()], nodes, matchMethod=matchMethod)

        # pose data specific logic
        if matchMethod == 'index':
            for i, node in enumerate(nodes):
                matched = False
                for key in self.poseDict.keys():
                    if int(self.poseDict[key]['ID']) == i:
                        matchedPairs.append((key, node))
                        log.debug('poseKey : %s %s >> matchedSource : %s %i' % (key, self.poseDict[key]['ID'], node, i))
                        matched = True
                        break
                if not matched:
                    unmatched.append(node)

        if matchMethod == 'mirrorIndex':
            getMirrorID = r9Anim.MirrorHierarchy().getMirrorCompiledID
            for node in nodes:
                matched = False
                mirrorID = getMirrorID(node)
                if not mirrorID:
                    continue
                for key in self.poseDict.keys():
                    if 'mirrorID' in self.poseDict[key] and self.poseDict[key]['mirrorID']:
                        poseID = self.poseDict[key]['mirrorID']
                        if poseID == mirrorID:
                            matchedPairs.append((key, node))
                            log.debug('poseKey : %s %s >> matched MirrorIndex : %s' % (key, node, self.poseDict[key]['mirrorID']))
                            matched = True
                            break
                if not matched:
                    unmatched.append(node)

        # unlike 'mirrorIndex' this matches JUST the ID's, the above matches SIDE_ID
        if matchMethod == 'mirrorIndex_ID':
            getMirrorID = r9Anim.MirrorHierarchy().getMirrorIndex
            for node in nodes:
                matched = False
                mirrorID = getMirrorID(node)
                if not mirrorID:
                    continue
                for key in self.poseDict.keys():
                    if 'mirrorID' in self.poseDict[key] and self.poseDict[key]['mirrorID']:
                        poseID = self.poseDict[key]['mirrorID'].split('_')[-1]
                        if not poseID == 'None':
                            if int(poseID) == mirrorID:
                                matchedPairs.append((key, node))
                                log.debug('poseKey : %s %s >> matched MirrorIndex : %s' % (key, node, self.poseDict[key]['mirrorID']))
                                matched = True
                                break
                        else:
                            log.debug('poseKey SKIPPED : %s:%s : as incorrect MirrorIDs' % (key, self.poseDict[key]['mirrorID']))
                if not matched:
                        unmatched.append(node)

        if matchMethod == 'metaData':
            if not self.metaRig:
                self.setMetaRig(nodes[0])
            getMetaDict = self.metaRig.getNodeConnectionMetaDataMap  # optimisation

            poseKeys = dict(self.poseDict)  # optimisation
            for node in nodes:
                matched = False
                try:
                    metaDict = getMetaDict(node)
                    for key in poseKeys:
                        if poseKeys[key]['metaData'] == metaDict:
                            matchedPairs.append((key, node))
                            log.debug('poseKey : %s %s >> matched MetaData : %s' % (key, node, poseKeys[key]['metaData']))
                            poseKeys.pop(key)
                            matched = True
                            break
                except:
                    log.info('FAILURE to load MetaData pose blocks - Reverting to Name')
                    matchedPairs = r9Core.matchNodeLists([key for key in self.poseDict.keys()], nodes)
                if not matched:
                        unmatched.append(node)
        if returnfails:
            return matchedPairs, unmatched
        else:
            return matchedPairs

    def matchInternalPoseObjects(self, nodes=None, fromFilter=True):
        '''
        This is a throw-away and only used in the UI to select for debugging!
        from a given poseFile return or select the internal stored objects
        '''
        InternalNodes = []
        if not fromFilter:
            # no filter, we just pass in the longName thats stored
            for key in self.poseDict.keys():
                if cmds.objExists(self.poseDict[key]['longName']):
                    InternalNodes.append(self.poseDict[key]['longName'])
                elif cmds.objExists(key):
                    InternalNodes.append(key)
                elif cmds.objExists(r9Core.nodeNameStrip(key)):
                    InternalNodes.append(r9Core.nodeNameStrip(key))
        else:
            # use the internal Poses filter and then Match against scene nodes
            if self.settings.filterIsActive():
                filterData = r9Core.FilterNode(nodes, self.settings).processFilter()
                matchedPairs = self._matchNodesToPoseData(filterData)
                if matchedPairs:
                    InternalNodes = [node for _, node in matchedPairs]
        if not InternalNodes:
            raise StandardError('No Matching Nodes found!!')
        return InternalNodes

    # --------------------------------------------------------------------------------
    # Main Calls ----
    # --------------------------------------------------------------------------------

    # @r9General.Timer
    def saveData(self, nodes, filepath=None, useFilter=True, storeThumbnail=True, force=False):
        '''
        Generic entry point for the Data Save.

        :param nodes: nodes to store the data against OR the rootNode if the
            filter is active.
        :param filepath: posefile to save - if not given the pose is cached on this
            class instance.
        :param useFilter: use the filterSettings or not.
        :param storeThumbnail: save a thumbnail or not
        :param force: force write the data even if the file is read-only
        '''
        # push args to object - means that any poseHandler.py file has access to them
        if filepath:
            self.filepath = filepath

        self.useFilter = useFilter
        if self.filepath:
            log.debug('PosePath given : %s' % self.filepath)

        self.buildDataMap(nodes)  # generate the main node mapping
        self.buildBlocks_fill(self.nodesToStore)  # fill in all the data to collect

        if self.filepath:
            self._writePose(self.filepath, force=force)

            if storeThumbnail:
                sel = cmds.ls(sl=True, l=True)
                cmds.select(cl=True)
                r9General.thumbNailScreen(filepath, self.thumbnailRes[0], self.thumbnailRes[1])
                if sel:
                    cmds.select(sel)
        log.info('Data Saved Successfully to : %s' % self.filepath)

    # @r9General.Timer
    def loadData(self, nodes, filepath=None, useFilter=True, *args, **kws):
        '''
        Generic entry point for the Data Load.

        :param nodes:  if given load the data to only these. If given and filter=True
            this is the rootNode for the filter.
        :param filepath: file to load - if not given the pose is loaded from a
            cached instance on this class.
        :param useFilter: If the pose has an active Filter_Settings block and this
            is True then use the filter on the destination hierarchy.
        '''

        # push args to object - means that any poseHandler.py file has access to them
        if filepath:
            self.filepath = filepath
        if not type(nodes) == list:
            nodes = [nodes]  # cast to list for consistency
        self.useFilter = useFilter  # used in the getNodes call

        try:
            self._pre_load()
            # main process to match and build up the data
            self.processPoseFile(nodes)

            if not self.matchedPairs:
                raise StandardError('No Matching Nodes found in the PoseFile!')
            else:
                if self.prioritySnapOnly:
                    # we've already filtered the hierarchy, may as well just filter the results for speed
                    self.nodesToLoad = r9Core.prioritizeNodeList(self.nodesToLoad, self.settings.filterPriority, regex=True, prioritysOnly=True)
                    self.nodesToLoad.reverse()

                # nodes now matched, apply the data in the dataMap
                self._applyData()
        except StandardError, err:
            log.info('Pose Load Failed! : , %s' % err)
        finally:
            self._post_load()


class PoseData(DataMap):
    '''
    The PoseData is stored per node inside an internal dict as follows:

    >>> node = '|group|Rig|Body|TestCtr'
    >>> poseDict['TestCtr']
    >>> poseDict['TestCtr']['ID'] = 0   index in the Hierarchy used to build the data up
    >>> poseDict['TestCtr']['longName'] = '|group|Rig|Body|TestCtr'
    >>> poseDict['TestCtr']['attrs']['translateX'] = 0.5
    >>> poseDict['TestCtr']['attrs']['translateY'] = 1.0
    >>> poseDict['TestCtr']['attrs']['translateZ'] = 22
    >>>
    >>> # if we're storing as MetaData we also include:
    >>> poseDict['TestCtr']['metaData']['metaAttr'] = CTRL_L_Thing    = the attr that wires this node to the MetaSubsystem
    >>> poseDict['TestCtr']['metaData']['metaNodeID'] = L_Arm_System  = the metaNode this node is wired to via the above attr

    Matching of nodes against this dict is via either the nodeName, nodeIndex (ID) or
    the metaData block.

    New functionality allows you to use the main calls to cache a pose and reload it
    from this class instance, wraps things up nicely for you:

        >>> pose=r9Pose.PoseData()
        >>> pose.metaPose=True
        >>>
        >>> # cache the pose (just don't pass in a filePath)
        >>> pose.poseSave(cmds.ls(sl=True))
        >>> # reload the cache you just stored
        >>> pose.poseLoad(cmds.ls(sl=True))

    We can also load in a percentage of a pose by running the PoseData._applyData(percent) as follows:

        >>> pose=r9Pose.PoseData()
        >>> pose.metaPose=True
        >>> pose.filepath='C:/mypose.pose'
        >>>
        >>> # processPoseFile does just that, processes and build up the list of data but doesn't apply it
        >>> pose.processPoseFile(nodes='myRootNode')
        >>>
        >>> # now we can dial in a percentage of the pose, we bind this to a floatSlider in the UI
        >>> pose._applyData(percent=20)

    .. note::
        If the root node of the hierarchy passed into the poseSave() has a message attr
        'exportSkeletonRoot' or 'animSkeletonRoot' and that message is connected to a
        skeleton then the pose will also include an internal 'skeleton' pose, storing all
        child joints into a separate block in the poseFile that can be used by the
        PoseCompare class/function.

        For metaData based rigs this calls a function on the metaRig class getSkeletonRoots()
        which wraps the 'exportSkeletonRoot' attr, allowing you to overload this behaviour
        in your own MetaRig subclasses.
    '''

    def __init__(self, filterSettings=None, *args, **kws):
        '''
        I'm not passing any data in terms of nodes here, We'll deal with
        those in the PoseSave and PoseLoad calls. Leaves this open for
        expansion
        '''
        super(PoseData, self).__init__(filterSettings=filterSettings, *args, **kws)

        self.file_ext = '.pose'
        self.poseDict = {}
        self.infoDict = {}
        self.skeletonDict = {}
        self.posePointCloudNodes = []
        self.poseCurrentCache = {}  # cached dict storing the current state of the objects prior to applying the pose
        self.relativePose = False
        self.relativeRots = 'projected'
        self.relativeTrans = 'projected'

        self.mirrorInverse = False  # when loading do we inverse the attrs values being loaded (PRO-PACK finger systems)

    def _collectNodeData(self, node, key):
        '''
        collect the attr data from the node and add it to the poseDict[key]
        '''
        self._collectNodeData_attrs(node, key)

    def _buildBlock_skeletonData(self, rootJnt):
        '''
        :param rootNode: root of the skeleton to process

        TODO : strip the longname from the root joint upwards and remove namespaces on all
        '''
        self.skeletonDict = {}
        if not rootJnt:
            log.info('skeleton rootJnt joint was not found - [skeletonDict] pose section will not be propagated')
            return

        fn = r9Core.FilterNode(rootJnt)
        fn.settings.nodeTypes = 'joint'
        fn.settings.incRoots = True
        skeleton = fn.processFilter()
        parentNode = cmds.listRelatives(rootJnt, p=True, f=True)

        for jnt in skeleton:
            key = r9Core.nodeNameStrip(jnt)
            self.skeletonDict[key] = {}
            self.skeletonDict[key]['attrs'] = {}
            self.skeletonDict[key]['attrs_kWorld'] = {}
            if parentNode:
                self.skeletonDict[key]['longName'] = jnt.replace(parentNode[0], '')
            else:
                self.skeletonDict[key]['longName'] = jnt
            for attr in ['translateX', 'translateY', 'translateZ', 'rotateX', 'rotateY', 'rotateZ', 'jointOrientX', 'jointOrientY', 'jointOrientZ']:
                try:
                    self.skeletonDict[key]['attrs'][attr] = cmds.getAttr('%s.%s' % (jnt, attr))
                except:
                    log.debug('%s : attr is invalid in this instance' % attr)
            self.skeletonDict[key]['attrs_kWorld'] = self._getTranforms(jnt, worldspace=True)

    def buildBlocks_fill(self, nodes=None):
        '''
        What capture routines to run in order to build the poseDict data
        '''
        if not nodes:
            nodes = self.nodesToStore
        self.poseDict = {}
        self._buildBlock_info(nodes)
        self._buildBlock_poseDict(nodes)
        self._buildBlock_skeletonData(self.rootJnt)

    def _cacheCurrentNodeStates(self):
        '''
        this is purely for the _applyPose with percent and optimization for the UI's
        '''
        log.info('updating the currentCache')
        self.poseCurrentCache = {}
        for key, dest in self.matchedPairs:
            log.debug('caching current node data : %s' % key)
            self.poseCurrentCache[key] = {}
            if 'attrs' not in self.poseDict[key]:
                continue
            for attr, _ in self.poseDict[key]['attrs'].items():
                try:
                    self.poseCurrentCache[key][attr] = cmds.getAttr('%s.%s' % (dest, attr))
                except:
                    log.debug('Attr mismatch on destination : %s.%s' % (dest, attr))

    @r9General.Timer
    def _applyData_attrs_complex(self, percent=None):
        '''
        :param percent: percent of the pose to load

        This is only now used IF we're dealing with PoseBlending or
        manipulating the data via the mirrorIndex, else we divert to
        running the default _applyData_attrs from the DataMap!!

        Limitations are that the DataMap call deals with unitConversion
        for linear attrs, this doesn't for speed

        '''
        mix_percent = False  # gets over float values of zero from failing
        if percent is not None or type(percent) == float:
            mix_percent = True
            if not self.poseCurrentCache:
                self._cacheCurrentNodeStates()

        for key, dest in self.matchedPairs:
            log.debug('Applying Key Block : %s' % key)
            try:
                if 'attrs' not in self.poseDict[key]:
                    continue
                for attr, val in self.poseDict[key]['attrs'].items():
                    if attr in self.skipAttrs:
                        log.debug('Skipping attr as requested : %s' % attr)
                        continue
                    try:
                        val = eval(val)
                        # =====================================================================
                        # inverse the correct mirror attrs if the mirrorInverse flag was thrown
                        # =====================================================================
                        # this is mainly for the ProPack finger systems support hooks
                        if self.mirrorInverse and 'mirrorID' in self.poseDict[key] and self.poseDict[key]['mirrorID']:
                            axis = r9Anim.MirrorHierarchy().getMirrorAxis(dest)
                            side = r9Anim.MirrorHierarchy().getMirrorSide(dest)
                            if attr in axis:
                                poseSide = self.poseDict[key]['mirrorID'].split('_')[0]
                                if not poseSide == side:
                                    val = 0 - val
                                    log.debug('Inversing Pose Values for Axis: %s, stored side: %s, nodes side: %s, node: %s' % (attr,
                                                                                                                                  poseSide,
                                                                                                                                  side,
                                                                                                                                  r9Core.nodeNameStrip(dest)))
                    except:
                        pass
                    log.debug('node : %s : attr : %s : val %s' % (dest, attr, val))
                    try:
                        if not mix_percent:
                            cmds.setAttr('%s.%s' % (dest, attr), val)
                        else:
                            current = self.poseCurrentCache[key][attr]
                            blendVal = ((val - current) / 100) * percent
                            # print 'loading at percent : %s (current=%s , stored=%s' % (percent,current,current+blendVal)
                            cmds.setAttr('%s.%s' % (dest, attr), current + blendVal)
                    except StandardError, err:
                        log.debug(err)
            except:
                log.debug('Pose Object Key : %s : has no Attr block data' % key)

    @r9General.Timer
    def _applyData(self, percent=None):
        '''
        apply the attrs for the pose.

        .. note:
            when dealing with pose blending or mirrorInverse handling we BY-PASS the
            sceneUnit conversions done in the main attr handler. This is for speed as generally
            complex adjustments such as blending in poses wouldn't be done between scenes in different Maya sceneUnits.
        '''
        if self.mirrorInverse or percent is not None:
            self._applyData_attrs_complex(percent)
        else:
            self._applyData_attrs()

        if self.world_space:
            self._applyData_kWorld_attrs(worldspace=True)

    # Main Calls ----------------------------------------

    # @r9General.Timer
    def poseSave(self, nodes, filepath=None, useFilter=True, storeThumbnail=True, modelPanel=None):  # 'modelPanel4'):
        '''
        Entry point for the generic PoseSave.

        :param nodes: nodes to store the data against OR the rootNode if the
            filter is active.
        :param filepath: posefile to save - if not given the pose is cached on this
            class instance.
        :param useFilter: use the filterSettings or not.
        :param storeThumbnail: generate and store a thubmbnail from the screen to go alongside the pose
        '''
        # push args to object - means that any poseHandler.py file has access to them
        if filepath:
            self.filepath = filepath
        self.useFilter = useFilter
        if self.filepath:
            log.debug('PosePath given : %s' % self.filepath)

        self.buildDataMap(nodes)  # generate the main node mapping
        self.buildBlocks_fill(self.nodesToStore)  # fill in all the data to collect

        if self.filepath:
            self._writePose(self.filepath)

            if storeThumbnail:
                sel = cmds.ls(sl=True, l=True)
                cmds.select(cl=True)
                r9General.thumbNailScreen(self.filepath, self.thumbnailRes[0], self.thumbnailRes[1], modelPanel=modelPanel)
                if sel:
                    cmds.select(sel)
            log.info('Pose Saved Successfully to : %s' % self.filepath)

    # @r9General.Timer
    @r9General.evalManager_idleAction
    def poseLoad(self, nodes, filepath=None, useFilter=True, relativePose=False, relativeRots='projected',
                 relativeTrans='projected', maintainSpaces=False, percent=None):
        '''
        Entry point for the generic PoseLoad.

        :param nodes:  if given load the data to only these. If given and filter=True
            this is the rootNode for the filter.
        :param filepath: posefile to load - if not given the pose is loaded from a
            cached instance on this class.
        :param useFilter: If the pose has an active Filter_Settings block and this
            is True then use the filter on the destination hierarchy.
        :param relativePose: kick in the posePointCloud to align the loaded pose
            relatively to the selected node.
        :param relativeRots: 'projected' or 'absolute' - how to calculate the offset.
        :param relativeTrans: 'projected' or 'absolute' - how to calculate the offset.
        :param maintainSpaces: this preserves any parentSwitching mismatches between
            the stored pose and the current rig settings, current spaces are maintained.
            This only checks those nodes in the snapList and only runs under relative mode.
        :param percent: percentage of the pose to apply, used by the poseBlender in the UIs

        .. note::
            Relative mode currently relies on the controller / reference node thats passed in to be Y-up in it's native state,
            thats to say the Y axis pointing upwards. We'll be patching this moving forwards
        '''

        objs = cmds.ls(sl=True, l=True)
        if relativePose and not objs:
            raise StandardError('Nothing selected to align Relative Pose too')
        if not type(nodes) == list:
            nodes = [nodes]  # cast to list for consistency

        # push args to object - means that any poseHandler.py file has access to them
        self.relativePose = relativePose
        self.relativeRots = relativeRots
        self.relativeTrans = relativeTrans
        self.PosePointCloud = None

        if filepath:
            self.filepath = filepath

        self.useFilter = useFilter  # used in the getNodes call
        self.maintainSpaces = maintainSpaces
        # self.mayaUpAxis = r9Setup.mayaUpAxis()  # already at the root level of the DataMap

        try:
            self._pre_load()
            # main process to match and build up the data
            self.processPoseFile(nodes)

            if not self.matchedPairs:
                raise StandardError('No Matching Nodes found in the PoseFile!')
            else:
                if self.relativePose:
                    if self.prioritySnapOnly:
                        if not self.settings.filterPriority:
                            log.warning('Internal filterPriority list is empty, switching "SnapPriority" flag OFF!')
                        else:
                            # we've already filtered the hierarchy, may as well just filter the results for speed
                            self.nodesToLoad = r9Core.prioritizeNodeList(self.nodesToLoad, self.settings.filterPriority, regex=True, prioritysOnly=True)
                            self.nodesToLoad.reverse()

                    # setup the PosePointCloud -------------------------------------------------
                    reference = objs[0]
                    self.PosePointCloud = PosePointCloud(self.nodesToLoad)
                    self.PosePointCloud.buildOffsetCloud(reference, raw=True)
#                     resetCache = [cmds.getAttr('%s.translate' % self.PosePointCloud.posePointRoot),
#                                 cmds.getAttr('%s.rotate' % self.PosePointCloud.posePointRoot)]
                    pptRoot = r9Meta.MetaClass(self.PosePointCloud.posePointRoot)
                    resetCache = [pptRoot.translate, pptRoot.rotate]

                    if self.maintainSpaces:
                        if self.metaRig:
                            parentSpaceCache = self.getMaintainedAttrs(self.nodesToLoad, self.metaRig.parentSwitchAttr)
                        elif 'parentSpaces' in self.settings.rigData:
                            parentSpaceCache = self.getMaintainedAttrs(self.nodesToLoad, self.settings.rigData['parentSpaces'])

                self._applyData(percent)

                if self.relativePose:
                    # snap the poseCloud to the new xform of the referenced node, snap the cloud
                    # to the pose, reset the clouds parent to the cached xform and then snap the
                    # nodes back to the cloud
                    r9Anim.AnimFunctions.snap([reference, self.PosePointCloud.posePointRoot])

                    if self.relativeRots == 'projected':
                        if self.mayaUpAxis == 'y':
                            pptRoot.rx = 0
                            pptRoot.rz = 0
                        elif self.mayaUpAxis == 'z':
                            pptRoot.rx = 0
                            pptRoot.ry = 0

                    # push data to the cloud
                    # ======================
                    self.PosePointCloud.snapPosePntstoNodes()

                    # absolute relative
                    if not self.relativeTrans == 'projected':
                        pptRoot.translate = resetCache[0]
                    if not self.relativeRots == 'projected':
                        pptRoot.rotate = resetCache[1]

                    # projected relative
                    if self.relativeRots == 'projected':
                        if self.mayaUpAxis == 'y':
                            pptRoot.ry = resetCache[1][1]
                        elif self.mayaUpAxis == 'z':
                            pptRoot.rz = resetCache[1][2]
                    if self.relativeTrans == 'projected':
                        if self.mayaUpAxis == 'y':
                            pptRoot.tx = resetCache[0][0]
                            pptRoot.tz = resetCache[0][2]
                        elif self.mayaUpAxis == 'z':
                            pptRoot.tx = resetCache[0][0]
                            pptRoot.ty = resetCache[0][1]

                    # if maintainSpaces then restore the original parentSwitch attr values
                    # BEFORE pushing the point cloud data back to the rig
                    if self.maintainSpaces and parentSpaceCache:  # and self.metaRig:
                        for child, attr, value in parentSpaceCache:
                            log.debug('Resetting parentSwitches : %s.%s = %f' % (r9Core.nodeNameStrip(child), attr, value))
                            cmds.setAttr('%s.%s' % (child, attr), value)

                    # pull data back from the cloud
                    # =============================
                    self.PosePointCloud.snapNodestoPosePnts()
                    self.PosePointCloud.delete()
                    cmds.select(reference)
                else:
                    if objs:
                        cmds.select(objs)
        except StandardError, err:
            log.info('Pose Load Failed! : , %s' % err)
        finally:
            self._post_load()

class PoseBlender(object):
    '''
    simple wrap over the PoseLoad code to control the loading of the r9Pose through a poseBlender UI
    or a simple percent args passed into the applyPercent call. This is called by the AnimUI and is really
    only meant as an internal binding
    '''
    def __init__(self, filepaths, nodes=None, filterSettings=None, useFilter=True, matchMethod='stripPrefix'):

        self.nodes = nodes
        self.filepaths = filepaths
        self._poseBlendUndoChunkOpen = False
        self._poseSliderActive = None
        self._poseSliders = []

        # build the pose object up
        self.poseNode = PoseData(filterSettings)
        self.poseNode.useFilter = useFilter
        self.poseNode.matchMethod = matchMethod
        self.poseNode.filepath = filepaths[0]  # first path as default

    def _blendPose(self, filepath, slider, *args):
        '''
        this has been expanded to possibly support multiple floatSliders blending
        multiple poses at once, managing the cache accordingly
        '''
        if not self._poseBlendUndoChunkOpen or not slider == self._poseSliderActive:
            log.debug('Opening Undo Chunk for PoseBlender')
            cmds.undoInfo(openChunk=True)
            self._poseBlendUndoChunkOpen = True

            if not slider == self._poseSliderActive:
                self.poseNode.filepath = filepath
                self.poseNode.processPoseFile(self.nodes)
                self.poseNode._cacheCurrentNodeStates()
                self._poseSliderActive = slider

                # zero all other sliders for the cache to be consistent
                for _slider in self._poseSliders:
                    if not _slider == slider:
                        cmds.floatSliderGrp(_slider, e=True, value=0)

        # actual slider drag call
        self.poseNode._applyData(percent=cmds.floatSliderGrp(slider, q=True, v=True))

    def _closeChunk(self, *args):
        cmds.undoInfo(closeChunk=True)
        self._poseBlendUndoChunkOpen = False
        log.debug('Closing Undo Chunk for PoseBlender')

    def keyMembers(self, *args):
        '''
        key the members of the pose data
        '''
        cmds.setKeyframe([node for _, node in self.poseNode.matchedPairs])

    def selectMembers(self, *args):
        cmds.select([node for _, node in self.poseNode.matchedPairs])

    def applyPercent(self, percent):
        '''
        direct call to load a percentage of the given pose in this instance
        '''
        self.poseNode.processPoseFile(self.nodes)
        self.poseNode._applyData(percent=percent)

    def show(self):
        '''
        main blender UI, simple but generic and allows us to dial in a percentage
        of the given pose. This is basically a wrap for the other UI's and functions
        that call this method so we have a single class managing the UI and functionality.
        '''
        # self.poseNode.processPoseFile(self.nodes)

        from functools import partial
        if cmds.window('poseBlender', exists=True):
            cmds.deleteUI('poseBlender')

        cmds.window('poseBlender')
        cmds.columnLayout()
        # cmds.text('    Blending Pose :  "%s"' % self.poseNode.filename, fn='boldLabelFont', h=20)
        cmds.separator(h=10, style='in')
        cmds.rowColumnLayout(numberOfColumns=3,
                             columnWidth=[(1, 460), (2, 110), (3, 110)],
                             columnSpacing=[(2, 5), (3, 5)])

        for filepath in self.filepaths:

            name = os.path.splitext(os.path.basename(filepath))[0]
            self._poseSliders.append(name)
            cmds.floatSliderGrp(name,
                                label='Percentage: "%s" : ' % name,
                                field=True,
                                minValue=0.0,
                                maxValue=100.0,
                                value=0,
                                columnWidth3=[200, 60, 200],
                                dc=partial(self._blendPose, filepath, name),
                                cc=partial(self._closeChunk))

            cmds.button(label=LANGUAGE_MAP._AnimationUI_.pose_blend_key_members,
                        ann=LANGUAGE_MAP._AnimationUI_.pose_blend_key_members,
                        command=self.keyMembers)
            cmds.button(label=LANGUAGE_MAP._AnimationUI_.pose_blend_select_members,
                        ann=LANGUAGE_MAP._AnimationUI_.pose_blend_select_members,
                        command=self.selectMembers)

        cmds.setParent('..')
        cmds.showWindow()


class PosePointCloud(object):
    '''
    PosePointCloud is the technique inside the PoseSaver used to snap the pose into
    relative space. It's been added as a tool in it's own right as it's sometimes
    useful to be able to shift poses in global space.

    >>> # heres an mRig example, it will also work with any other rigs by just setting up
    >>> # the filter settings object in the same way for any of the Red9 tools
    >>> import Red9.core.Red9_PoseSaver as r9Pose
    >>> import Red9.core.Red9_Meta as r9Meta
    >>>
    >>> # grab our mRig node
    >>> mrig=r9Meta.getMetaRigs()[0]
    >>>
    >>> ppc=r9Pose.PosePointCloud(nodes=mrig.ctrl_main)
    >>> ppc.settings.metaRig=True
    >>> ppc.prioritySnapOnly=True  # for rigs you can turn this on so that ONLY those nodes in the filterPriority list get built and used
    >>>
    >>> # build the cloud system
    >>> ppc.buildOffsetCloud()   # you can also pass a root point in, used as the base pivot ( rootReference='pSphere1')
    >>>
    >>> # to apply the cloud, snapping the rig into the clouds pose
    >>> ppc.applyPosePointCloud()
    >>>
    >>> # to sync the cloud to the rigs current frame, allowing you to update the clouds internal pose
    >>> ppc.updatePosePointCloud()
    >>>
    >>> # delete the ppc node
    >>> ppc.delete()
    '''
    def __init__(self, nodes, filterSettings=None, meshes=[], prioritySnapOnly=False, *args, **kws):
        '''
        :param nodes: feed the nodes to process in as a list, if a filter is given
                      then these are the rootNodes for it
        :param filterSettings: pass in a filterSettings object to filter the given hierarchy
        :param meshes: this is really for reference, rather than make a locator, pass in a reference geo
                     which is then shapeSwapped for the PPC root node giving great reference!
        :param prioritySnapOnly: ONLY make ppc points for the filterPriority nodes
        '''

        self.meshes = meshes
        if self.meshes and not isinstance(self.meshes, list):
            self.meshes = [meshes]

        self.refMesh = 'posePointCloudGeoRef'  # name for the duplicate meshes used
        self.mayaUpAxis = r9Setup.mayaUpAxis()
        self.inputNodes = nodes  # inputNodes for processing
        self.posePointCloudNodes = []  # generated ppc nodes
        self.posePointRoot = None  # generated rootnode of the ppc
        self.settings = None
        self.prioritySnapOnly = prioritySnapOnly  # ONLY make ppc points for the filterPriority nodes

        self.rootReference = None  # root node used as the main pivot for the cloud
        self.isVisible = True  # Do we build the visual reference setup or not?
        self.mRig = None
        self.ppcMeta = None  # MetaNode to cache the data

        if filterSettings:
            if not issubclass(type(filterSettings), r9Core.FilterNode_Settings):
                raise StandardError('filterSettings param requires an r9Core.FilterNode_Settings object')
            elif filterSettings.filterIsActive():
                self.settings = filterSettings
        else:
            self.settings = r9Core.FilterNode_Settings()

        if self.getCurrentInstances():
            self.syncdatafromCurrentInstance()

    def __connectdataToMeta__(self):
        '''
        on build push the data to a metaNode so it's cached in the scene incase we need to
        reconstruct anything at a later date. This is used extensively in the AnimReDirect calls
        '''
        self.ppcMeta.connectChild(self.posePointRoot, 'posePointRoot')
        self.ppcMeta.addAttr('posePointCloudNodes', self.posePointCloudNodes)
        self.ppcMeta.addAttr('baseClass', self.__class__.__name__, attrType='string')

    def syncdatafromCurrentInstance(self):
        '''
        pull existing data back from the metaNode
        '''
        if self.getCurrentInstances():
            self.ppcMeta = self.getCurrentInstances()[0]
            self.posePointCloudNodes = self.ppcMeta.posePointCloudNodes
            self.posePointRoot = self.ppcMeta.posePointRoot[0]
            self.baseClass = self.ppcMeta.baseClass

    def getInputNodes(self):
        '''
        handler to build up the list of nodes to generate the cloud against.
        This uses the filterSettings and the inputNodes variables to process the
        hierarchy and is designed for overloading if required.
        '''
        if self.settings.filterIsActive():
            __searchPattern_cached = self.settings.searchPattern
#             if self.prioritySnapOnly:
#                 self.settings.searchPattern=self.settings.filterPriority
#            self.inputNodes=r9Core.FilterNode(self.inputNodes, self.settings).processFilter()

            flt = r9Core.FilterNode(self.inputNodes, self.settings)
            if self.prioritySnapOnly:
                # take from the flt instance as that now manages metaRig specific settings internally
                self.settings.searchPattern = flt.settings.filterPriority
            self.inputNodes = flt.processFilter()

            self.settings.searchPattern = __searchPattern_cached  # restore the settings back!!

        # auto logic for MetaRig - go find the renderMeshes wired to the systems
        if self.settings.metaRig:
            if not self.meshes:
                self.mRig = r9Meta.getConnectedMetaSystemRoot(self.inputNodes)
            else:
                self.mRig = r9Meta.getMetaRigs()[0]
            self.meshes = self.mRig.renderMeshes

        if self.inputNodes:
            self.inputNodes.reverse()  # for the snapping operations
        return self.inputNodes

    def getPPCNodes(self):
        '''
        return a list of the PPC nodes
        '''
        return [ppc for ppc, _ in self.posePointCloudNodes]

    def getTargetNodes(self):
        '''
        return a list of the target controllers
        '''
        return [target for _, target in self.posePointCloudNodes]

    @staticmethod
    def getCurrentInstances():
        '''
        get any current PPC nodes in the scene
        '''
        return r9Meta.getMetaNodes(mClassGrps=['PPCROOT'])

    def snapPosePntstoNodes(self):
        '''
        snap each pntCloud point to their respective Maya nodes
        '''
        for pnt, node in self.posePointCloudNodes:
            try:
                log.debug('snapping PPT : %s' % pnt)
                r9Anim.AnimFunctions.snap([node, pnt])
            except:
                log.debug('FAILED : snapping PPT : %s' % pnt)

    def snapNodestoPosePnts(self):
        '''
        snap each MAYA node to it's respective pntCloud point
        '''
        for pnt, node in self.posePointCloudNodes:
            try:
                log.debug('snapping Ctrl : %s > %s : %s' % (r9Core.nodeNameStrip(node), pnt, node))
                r9Anim.AnimFunctions.snap([pnt, node])
            except:
                log.debug('FAILED : snapping PPT : %s' % pnt)

    def generateVisualReference(self):
        '''
        Generic call that's used to overload the visual handling
        of the PPC is other instances such as the AnimationPPC
        '''
        if self.meshes and self.isVisible:
            self.shapeSwapMeshes()

    def buildOffsetCloud(self, rootReference=None, raw=False, projectedRots=False, projectedTrans=False):
        '''
        Build a point cloud up for each node in nodes

        :param nodes: list of objects to be in the cloud
        :param rootReference: the node used for the initial pivot location
        :param raw: build the cloud but DON'T snap the nodes into place - an optimisation for the PoseLoad sequence
        :param projectedRots: project the rotates of the root node of the cloud
        :param projectedTrans: project the translates of the root node of the cloud
        '''

        self.deleteCurrentInstances()

        # moved the mNode generation earlier so the rest of the code can bind to it during build
        self.ppcMeta = r9Meta.MetaClass(name='PPC_Root')
        self.ppcMeta.mClassGrp = 'PPCROOT'

        self.posePointRoot = cmds.ls(cmds.spaceLocator(name='posePointCloud'), sl=True, l=True)[0]
        cmds.setAttr('%s.visibility' % self.posePointRoot, self.isVisible)

        ppcShape = cmds.listRelatives(self.posePointRoot, type='shape', f=True)[0]
        cmds.setAttr("%s.localScaleZ" % ppcShape, 30)
        cmds.setAttr("%s.localScaleX" % ppcShape, 30)
        cmds.setAttr("%s.localScaleY" % ppcShape, 30)

        if rootReference:
            self.rootReference = rootReference

        # run the filterCode based on the settings object
        self.getInputNodes()

        if self.mayaUpAxis == 'y':
            cmds.setAttr('%s.rotateOrder' % self.posePointRoot, 2)  # to prevent as much gimal as possible
        if self.rootReference:  # and not mesh:
            r9Anim.AnimFunctions.snap([self.rootReference, self.posePointRoot])

            # reset the PPTCloudRoot to projected ground plane
            if projectedRots:
                if self.mayaUpAxis == 'y':
                    cmds.setAttr('%s.rx' % self.posePointRoot, 0)
                    cmds.setAttr('%s.rz' % self.posePointRoot, 0)
                elif self.mayaUpAxis == 'z':  # maya Z up
                    cmds.setAttr('%s.rx' % self.posePointRoot, 0)
                    cmds.setAttr('%s.ry' % self.posePointRoot, 0)
            if projectedTrans:
                if self.mayaUpAxis == 'y':
                    cmds.setAttr('%s.ty' % self.posePointRoot, 0)
                elif self.mayaUpAxis == 'z':  # maya Z up
                    cmds.setAttr('%s.tz' % self.posePointRoot, 0)

        for node in self.inputNodes:
            pnt = cmds.spaceLocator(name='pp_%s' % r9Core.nodeNameStrip(node))[0]
            if not raw:
                r9Anim.AnimFunctions.snap([node, pnt])
            cmds.parent(pnt, self.posePointRoot)
            self.posePointCloudNodes.append((pnt, node))
        cmds.select(self.posePointRoot)

        # generate the mesh references if required
        self.generateVisualReference()

        self.__connectdataToMeta__()
        return self.posePointCloudNodes

    def shapeSwapMeshes(self, selectable=True):
        '''
        Swap the mesh Geo so it's a shape under the PPC transform root
        '''
        currentCount = len(cmds.listRelatives(self.posePointRoot, type='shape'))
        for i, mesh in enumerate(self.meshes):
            dupMesh = cmds.duplicate(mesh, rc=True, n=self.refMesh + str(i + currentCount))[0]
            dupShape = cmds.listRelatives(dupMesh, type='shape')[0]
            r9Core.LockChannels().processState(dupMesh, 'all', mode='fullkey', hierarchy=False)
            try:
                if selectable:
                    # turn on the overrides so the duplicate geo can be selected
                    cmds.setAttr("%s.overrideDisplayType" % dupShape, 0)
                    cmds.setAttr("%s.overrideEnabled" % dupShape, 1)
                    cmds.setAttr("%s.overrideLevelOfDetail" % dupShape, 0)
                else:
                    cmds.setAttr("%s.overrideDisplayType" % dupShape, 2)
                    cmds.setAttr("%s.overrideEnabled" % dupShape, 1)
            except:
                log.debug('Couldnt set the draw overrides for the refGeo')
            cmds.parent(dupMesh, self.posePointRoot)
            cmds.makeIdentity(dupMesh, apply=True, t=True, r=True)
            cmds.parent(dupShape, self.posePointRoot, r=True, s=True)
            cmds.delete(dupMesh)

    def applyPosePointCloud(self):
        self.snapNodestoPosePnts()

    def updatePosePointCloud(self):
        self.snapPosePntstoNodes()
        if self.meshes:
            cmds.delete(cmds.listRelatives(self.posePointRoot, type=['mesh', 'nurbsCurve']))
            self.generateVisualReference()
            cmds.refresh()

    def delete(self):
        root = self.posePointRoot
        if not root:
            root = self.ppcMeta.posePointRoot[0]
        self.ppcMeta.delete()
        cmds.delete(root)

    def deleteCurrentInstances(self):
        '''
        delete any current instances of PPC clouds
        '''
        PPCNodes = self.getCurrentInstances()
        if PPCNodes:
            log.info('Deleting current PPC nodes in the scene')
            for ppc in PPCNodes:
                cmds.delete(ppc.posePointRoot)
                try:
                    ppc.delete()
                except:
                    pass  # metaNode should be cleared by default when it's only connection is deleted

class PoseCompare(object):
    '''
    This is aimed at comparing a rigs current pose with a given one, be that a
    pose file on disc, a pose class object, or even a poseObject against another.
    It will compare either the main [poseData].keys or the ['skeletonDict'].keys
    and for key in keys compare, with tolerance, the [attrs] block.

    >>> # lets do simple skeleton comparison giving it 2 rootjnts
    >>> import Red9.core.Red9_PoseSaver as r9Pose
    >>> # root jnts of skeletons to test
    >>> test_root='root_of_skl_to_test'
    >>> master_root='root_of_correct_skl'
    >>>
    >>> mPoseA=r9Pose.PoseData()
    >>> mPoseA.settings.nodeTypes=['joint']
    >>> mPoseA.buildDataMap(test_root)
    >>> mPoseA.buildBlocks_fill()
    >>>
    >>> mPoseB=r9Pose.PoseData()
    >>> mPoseB.settings.nodeTypes=['joint']
    >>> mPoseB.buildDataMap(master_root)
    >>> mPoseB.buildBlocks_fill()
    >>>
    >>> compare=r9Pose.PoseCompare(mPoseA,mPoseB)
    >>> compare.compare() #>> bool, True = same

    >>> ----------------------------------------------------
    >>> # mRig manual pose testing - note that mRig has
    >>> # poseCompare wrapped as an internal function also!
    >>> ----------------------------------------------------
    >>> # build an mPose object and fill the internal poseDict
    >>> mPoseA=r9Pose.PoseData()
    >>> mPoseA.metaPose=True
    >>> mPoseA.buildDataMap(cmds.ls(sl=True))
    >>> mPoseA.buildBlocks_fill()
    >>>
    >>> mPoseB=r9Pose.PoseData()
    >>> mPoseB.metaPose=True
    >>> mPoseB.buildDataMap(cmds.ls(sl=True))
    >>> mPoseB.buildBlocks_fill()
    >>>
    >>> compare=r9Pose.PoseCompare(mPoseA,mPoseB)
    >>>
    >>> #.... or ....
    >>> compare=r9Pose.PoseCompare(mPoseA,'H:/Red9PoseTests/thisPose.pose')
    >>> #.... or ....
    >>> compare=r9Pose.PoseCompare('H:/Red9PoseTests/thisPose.pose','H:/Red9PoseTests/thatPose.pose')
    >>>
    >>> compare.compare() #>> bool, True = same
    >>> compare.fails['failedAttrs']
    '''
    def __init__(self, currentPose, referencePose, angularTolerance=0.1, linearTolerance=0.01,
                 compareDict='poseDict', filterMap=[], ignoreBlocks=[], ignoreStrings=[], ignoreAttrs=[], longName=False):
        '''
        Make sure we have 2 PoseData objects to compare
        :param currentPose: either a PoseData object or a valid pose file
        :param referencePose: either a PoseData object or a valid pose file
        :param angularTolerance: the tolerance used to check rotate attr float values
        :param linearTolerance: the tolerance used to check all other float attrs
        :param compareDict: the internal main dict in the pose file to compare the data with : base options : 'poseDict', 'skeletonDict'
        :param filterMap: if given this is used as a high level filter, only matching nodes get compared
            others get skipped. Good for passing in a master core skeleton to test whilst ignoring extra nodes
        :param ignoreBlocks: allows the given failure blocks to be ignored. We mainly use this for ['missingKeys']
        :param ignoreStrings: allows you to pass in a list of strings, if any of the keys in the data contain
             that string it will be skipped, note this is a partial match so you can pass in wildcard searches ['_','_end']
        :param ignoreAttrs: allows you to skip given attrs from the poseCompare calls
        :param longName: compare the longName DAG path stores against each node, note that the compare strips out any namespaces before compare

        .. note::
            In the new setup if the pose being generated had it's settings.nodeTypes=['joint'] or we found the
            exportSkeletonRoot jnt (mrig) then we add a whole new dict to serialize the current skeleton data to the pose,
            this means that we can then compare a pose on a rig via the internal skeleton transforms as well
            as the actual rig controllers... makes validation a lot more accurate for export
                * 'poseDict'     = [poseData] main controller data
                * 'skeletonDict' = [skeletonDict] block generated if exportSkeletonRoot is connected
                * 'infoDict'     = [info] block
        '''
        self.status = False
        self.compareDict = compareDict
        self.angularTolerance = angularTolerance
        self.angularAttrs = ['rotateX', 'rotateY', 'rotateZ', 'jointOrientX', 'jointOrientY', 'jointOrientZ']

        self.linearTolerance = linearTolerance
        self.linearAttrs = ['translateX', 'translateY', 'translateZ']

        self.filterMap = filterMap
        self.ignoreBlocks = ignoreBlocks
        self.ignoreStrings = ignoreStrings
        self.ignoreAttrs = ignoreAttrs
        self.longName = longName

        if isinstance(currentPose, PoseData):
            self.currentPose = currentPose
        elif os.path.exists(currentPose):
            self.currentPose = PoseData()
            self.currentPose._readPose(currentPose)
        elif not os.path.exists(referencePose):
            raise IOError('Given CurrentPose Path is invalid!')

        if isinstance(referencePose, PoseData):
            self.referencePose = referencePose
        elif os.path.exists(referencePose):
            self.referencePose = PoseData()
            self.referencePose._readPose(referencePose)
        elif not os.path.exists(referencePose):
            raise IOError('Given ReferencePose Path is invalid!')

    def __addFailedAttr(self, key, attr):
        '''
        add failed attrs data to the dict
        '''
        if 'failedAttrs' not in self.fails:
            self.fails['failedAttrs'] = {}
        if key not in self.fails['failedAttrs']:
            self.fails['failedAttrs'][key] = {}
        if 'attrMismatch' not in self.fails['failedAttrs'][key]:
            self.fails['failedAttrs'][key]['attrMismatch'] = []
        self.fails['failedAttrs'][key]['attrMismatch'].append(attr)

    def compare(self):
        '''
        Compare the 2 PoseData objects via their internal [key][attrs] blocks
        return a bool. After processing self.fails is a dict holding all the fails
        for processing later if required
        '''
        self.fails = {}
        logprint_keymismacth = ''
        logprint_dagpath = ''
        logprint_missingattr = ''
        logprint_missingfail = ''

        currentDic = getattr(self.currentPose, self.compareDict)
        referenceDic = getattr(self.referencePose, self.compareDict)

        if not currentDic or not referenceDic:
            raise StandardError('missing pose section <<%s>> compare aborted' % self.compareDict)

        for key, attrBlock in currentDic.items():
            if self.filterMap and key not in self.filterMap:
                log.debug('node not in filterMap - skipping key %s' % key)
                continue
            skip = False

            # --------------------------------------------
            # check that the key isn't in the ignoreStrings
            # --------------------------------------------
            if self.ignoreStrings:
                for istr in self.ignoreStrings:
                    if istr in key:
                        skip = True
                        break
            if skip:
                continue

            # ---------------------------------------------
            # "missingKeys" block - check that the key exists
            # ---------------------------------------------

            if key in referenceDic:
                referenceAttrBlock = referenceDic[key]
            else:
                if 'missingKeys' not in self.ignoreBlocks:
                    logprint_keymismacth += 'ERROR: Key Mismatch : %s\n' % key
                    if 'missingKeys' not in self.fails:
                        self.fails['missingKeys'] = []
                    self.fails['missingKeys'].append(key)
                else:
                    log.debug('missingKeys in ignoreblock : node is missing from data but being skipped "%s"' % key)
                continue

            # ---------------------------------------------
            # "hierarchyMismatch" block - check full dagPaths
            # ---------------------------------------------
            try:
                expectedDag = r9Core.removeNameSpace_fromDag(referenceAttrBlock['longName'])
                currentDag = r9Core.removeNameSpace_fromDag(attrBlock['longName'])

                if self.longName and not expectedDag == currentDag:
                    if 'dagMismatch' not in self.ignoreBlocks:
                        logprint_dagpath += 'ERROR: hierarchy Mismatch : \n\t\tcurrentValue=\t"%s" >> \n\t\texpectedValue=\t"%s"\n' % (currentDag, expectedDag)
                        if 'dagMismatch' not in self.fails:
                            self.fails['dagMismatch'] = []
                        self.fails['dagMismatch'].append(key)
                    else:
                        log.debug('dagMismatch in ignoreblock : DagPath compare being skipped "%s"' % key)
            except:
                log.debug('Skipping DAGPATH compare as "longName" was not found in the reference pose : "%s"' % key)

            # ---------------------------------------------
            # "failedAttrs" block - compare attr values
            # ---------------------------------------------

            # check that this object actually has attr data in the pose
            if 'attrs' not in attrBlock:
                log.debug('%s node has no attrs block in the pose' % key)
                continue
            else:
                if 'failedAttrs' in self.ignoreBlocks:
                    log.debug('failedAttrs in ignoreblock : attr compare being skipped "%s"' % key)
                    continue
                # main compare block for attr values
                for attr, value in attrBlock['attrs'].items():
                    if attr in self.ignoreAttrs:
                        continue
                    # attr missing completely from the key
                    if attr not in referenceAttrBlock['attrs']:
                        if 'failedAttrs' not in self.fails:
                            self.fails['failedAttrs'] = {}
                        if key not in self.fails['failedAttrs']:
                            self.fails['failedAttrs'][key] = {}
                        if 'missingAttrs' not in self.fails['failedAttrs'][key]:
                            self.fails['failedAttrs'][key]['missingAttrs'] = []
                        self.fails['failedAttrs'][key]['missingAttrs'].append(attr)
                        logprint_missingattr += 'ERROR: Missing attribute in data : "%s.%s"\n' % (key, attr)
                        continue

                    # test the attrs value matches
                    value = r9Core.decodeString(value)  # decode as this may be a configObj
                    refValue = r9Core.decodeString(referenceAttrBlock['attrs'][attr])  # decode as this may be a configObj

                    if type(value) == float:
                        matched = False
                        if attr in self.angularAttrs:
                            matched = r9Core.floatIsEqual(value, refValue, self.angularTolerance, allowGimbal=True)
                        else:
                            matched = r9Core.floatIsEqual(value, refValue, self.linearTolerance, allowGimbal=False)
                        if not matched:
                            self.__addFailedAttr(key, attr)
                            logprint_missingfail += 'ERROR: AttrValue float mismatch : "%s.%s" currentValue=%s >> expectedValue=%s\n' % (key, attr, value, refValue)
                            continue
                    elif not value == refValue:
                        self.__addFailedAttr(key, attr)
                        logprint_missingfail += 'ERROR: AttrValue mismatch : "%s.%s" currentValue=%s >> expectedValue=%s\n' % (key, attr, value, refValue)
                        continue

        if any(['missingKeys' in self.fails, 'failedAttrs' in self.fails, 'dagMismatch' in self.fails]):
            print('PoseCompare returns : "%s" ========================================\n' % self.compareDict)
            if logprint_keymismacth:
                print(logprint_keymismacth)
            if logprint_dagpath:
                print(logprint_dagpath)
            if logprint_missingattr:
                print(logprint_missingattr)
            if logprint_missingfail:
                print(logprint_missingfail)
            print('PoseCompare returns : ========================================')
            return False
        self.status = True
        return True


def batchPatchPoses(posedir, config, poseroot, load=True, save=True, patchfunc=None,
                    relativePose=False, relativeRots=False, relativeTrans=False):
    '''
    whats this?? a fast method to run through all the poses in a given dictionary and update
    or patch them. If patchfunc isn't given it'll just run through and resave the pose - updating
    the systems if needed. If it is then it gets run between the load and save calls.
    :param posedir: directory of poses to process
    :param config: hierarchy settings cfg to use to ID the nodes (hierarchy tab preset = filterSettings object)
    :param poseroot: root node to the filters - poseTab rootNode/MetaRig root
    :param patchfunc: optional function to run between the load and save call in processing, great for
            fixing issues on mass with poses. Note we now pass pose file back into this func as an arg
    :param load: should the batch load the pose
    :param save: should the batch resave the pose
    '''

    filterObj = r9Core.FilterNode_Settings()
    filterObj.read(os.path.join(r9Setup.red9ModulePath(), 'presets', config))
    mPose = PoseData(filterObj)
    mPose.setMetaRig(poseroot)
    files = os.listdir(posedir)
    files.sort()
    for f in files:
        if f.lower().endswith('.pose'):
            if load:
                print('Loading Pose : %s' % os.path.join(posedir, f))
                mPose.poseLoad(nodes=poseroot,
                               filepath=os.path.join(posedir, f),
                               useFilter=True,
                               relativePose=relativePose,
                               relativeRots=relativeRots,
                               relativeTrans=relativeTrans)
            if patchfunc:
                print('Applying patch')
                patchfunc(f)
            if save:
                print('Saving Pose : %s' % os.path.join(posedir, f))
                mPose.poseSave(nodes=poseroot,
                               filepath=os.path.join(posedir, f),
                               useFilter=True,
                               storeThumbnail=False)
            log.info('Processed Pose File :  %s' % f)
