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

import Red9.startup.setup as r9Setup
import Red9_CoreUtils as r9Core
import Red9_General as r9General
import Red9_AnimationUtils as r9Anim
import Red9_Meta as r9Meta

import maya.cmds as cmds
import os
import Red9.packages.configobj as configobj
import time
import getpass


import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


def getFolderPoseHandler(posePath):
    '''
    Check if the given directory contains a poseHandler.py file
    if so return the filename. PoseHandlers are a way of extending or
    over-loading the standard behaviour of the poseSaver, see Vimeo for
    a more detailed explanation.
    '''
    poseHandler=None
    poseHandlers=[py for py in os.listdir(posePath) if py.endswith('poseHandler.py')]
    if poseHandlers:
        poseHandler=poseHandlers[0]
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
        self.poseDict={}
        self.infoDict={}
        self.skeletonDict={}
        self.file_ext = ''  # extension the file will be saved as
        self.filepath=''    # path to load / save
        self.__filepath = ''
        self.mayaUpAxis = r9Setup.mayaUpAxis()
        self.thumbnailRes=[128,128]
        
        self.__metaPose=False
        self.metaRig=None  # filled by the code as we process
        self.matchMethod='base'  # method used to match nodes internally in the poseDict
        self.useFilter=True
        self.prioritySnapOnly=False  # mainly used by any load relative calls, determines whether to use the internal filters priority list
        self.skipAttrs=[]  # attrs to completely ignore in any pose handling
        
        # make sure we have a settings object
        if filterSettings:
            if issubclass(type(filterSettings), r9Core.FilterNode_Settings):
                self.settings=filterSettings
                self.__metaPose=self.settings.metaRig
            else:
                raise StandardError('filterSettings param requires an r9Core.FilterNode_Settings object')
            self.settings.printSettings()
        else:
            self.settings=r9Core.FilterNode_Settings()
            self.__metaPose=self.settings.metaRig
    
    @property
    def metaPose(self):
        return self.__metaPose
    
    @metaPose.setter
    def metaPose(self, val):
        self.__metaPose=val
        self.settings.metaRig=val
    
    @property
    def filepath(self):
        return self.__filepath
    
    @filepath.setter
    def filepath(self, path):
        if path and self.file_ext:
            self.__filepath='%s%s' % (os.path.splitext(path)[0], self.file_ext)
        else:
            self.__filepath=path
    
    def _pre_load(self):
        '''
        called directly before the loadData call so you have access
        to manage the undoQueue etc if subclassing
        '''
        pass
    
    def _post_load(self):
        '''
        called directly after the loadData call so you have access
        to manage the undoQueue etc if subclassing
        '''
        pass
           
    def setMetaRig(self, node):
        log.debug('setting internal metaRig from given node : %s' % node)
        if r9Meta.isMetaNodeInherited(node,'MetaRig'):
            self.metaRig=r9Meta.MetaClass(node)
        else:
            self.metaRig=r9Meta.getConnectedMetaSystemRoot(node)
        log.debug('setting internal metaRig : %s' % self.metaRig)
        return self.metaRig
    
    def hasFolderOverload(self):
        '''
        modified so you can now prefix the poseHandler.py file
        makes it easier to keep track of in a production environment
        '''
        self.poseHandler=None
        if self.filepath:
            self.poseHandler = getFolderPoseHandler(os.path.dirname(self.filepath))
        return self.poseHandler
    
    def getNodesFromFolderConfig(self, rootNode, mode):
        '''
        if the poseFolder has a poseHandler.py file use that to
        return the nodes to use for the pose instead
        '''
        import imp
        log.debug('getNodesFromFolderConfig - useFilter=True : custom poseHandler running')
        posedir=os.path.dirname(self.filepath)
        print 'imp : ', self.poseHandler.split('.py')[0], '  :  ', os.path.join(posedir, self.poseHandler)
        tempPoseFuncs = imp.load_source(self.poseHandler.split('.py')[0], os.path.join(posedir, self.poseHandler))
        
        if mode=='load':
            nodes=tempPoseFuncs.poseGetNodesLoad(self,rootNode)
        if mode=='save':
            nodes=tempPoseFuncs.poseGetNodesSave(self,rootNode)
        del(tempPoseFuncs)

        return nodes
                    
    def getNodes(self, nodes):
        '''
        get the nodes to process
        This is designed to allow for specific hooks to be used from user
        code stored in the pose folder itself.
        '''
        if not type(nodes)==list:
            nodes=[nodes]
        if self.useFilter:
            log.debug('getNodes - useFilter=True : filteActive=True  - no custom poseHandler')
            if self.settings.filterIsActive():
                return r9Core.FilterNode(nodes,self.settings).ProcessFilter()  # main node filter
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
        or loaded. Currently only supported under MetaRig
        '''
        if self.metaRig and self.metaRig.hasAttr('poseSkippedAttrs'):
            return self.metaRig.poseSkippedAttrs
        return []
    
    def getMaintainedAttrs(self, nodesToLoad, parentSpaceAttrs):
        '''
        Attrs returned here will be cached prior to pose load, then restored in-tact afterwards
        '''
        parentSwitches=[]
        if not type(parentSpaceAttrs)==list:
            parentSpaceAttrs=[parentSpaceAttrs]
        for child in nodesToLoad:
            for attr in parentSpaceAttrs:
                if cmds.attributeQuery(attr, exists=True, node=child):
                    parentSwitches.append((child, attr, cmds.getAttr('%s.%s' % (child,attr))))
                    log.debug('parentAttrCache : %s > %s' % (child,attr))
        return parentSwitches
                 
    # Data Collection - Build the dataMap ---------------------------------------------
             
    def _collectNodeData_attrs(self, node, key):
        '''
        Capture and build attribute data from this node and fill the
        data to the datamap[key]
        '''
        channels=r9Anim.getSettableChannels(node,incStatics=True)
        if channels:
            self.poseDict[key]['attrs']={}
            for attr in channels:
                if attr in self.skipAttrs:
                    log.debug('Skipping attr as requested : %s' % attr)
                    continue
                try:
                    if cmds.getAttr('%s.%s' % (node,attr),type=True)=='TdataCompound':  # blendShape weights support
                        attrs=cmds.aliasAttr(node, q=True)[::2]  # extract the target channels from the multi
                        for attr in attrs:
                            self.poseDict[key]['attrs'][attr]=cmds.getAttr('%s.%s' % (node,attr))
                    else:
                        self.poseDict[key]['attrs'][attr]=cmds.getAttr('%s.%s' % (node,attr))
                except:
                    log.debug('%s : attr is invalid in this instance' % attr)
                     
    def _collectNodeData(self, node, key):
        '''
        To Be Overloaded : what data to push into the main dataMap 
        for each node found collected. This is the lowest level collect call
        for each node in the array.
        '''
        self._collectNodeData_attrs(node, key)
    
    def _buildBlock_info(self):
        '''
        Generic Info block for the data file, this could do with expanding
        '''
        self.infoDict['author']=getpass.getuser()
        self.infoDict['date']=time.ctime()
        self.infoDict['metaPose']=self.metaPose
        if self.metaRig:
            self.infoDict['metaRigNode']=self.metaRig.mNode
            self.infoDict['metaRigNodeID']=self.metaRig.mNodeID
            if self.metaRig.hasAttr('version'):
                self.infoDict['version'] = self.metaRig.version
            if self.metaRig.hasAttr('rigType'):
                self.infoDict['rigType'] = self.metaRig.rigType
        if self.rootJnt:
            self.infoDict['skeletonRootJnt']=self.rootJnt
                
    def _buildBlock_poseDict(self, nodes):
        '''
        Build the internal poseDict up from the given nodes. This is the
        core of the Pose System and the main dataMap used to store and retrieve data
        '''
        getMirrorID=r9Anim.MirrorHierarchy().getMirrorCompiledID
        if self.metaPose:
            getMetaDict=self.metaRig.getNodeConnectionMetaDataMap  # optimisation

        for i,node in enumerate(nodes):
            key=r9Core.nodeNameStrip(node)
            self.poseDict[key]={}
            self.poseDict[key]['ID']=i           # selection order index
            self.poseDict[key]['longName']=node  # longNode name
            
            mirrorID=getMirrorID(node)
            if mirrorID:
                self.poseDict[key]['mirrorID']=mirrorID  # add the mirrorIndex
            if self.metaPose:
                self.poseDict[key]['metaData']=getMetaDict(node)  # metaSystem the node is wired too
            
            # the above blocks are the generic info used to map the data on load
            # this call is the specific collection of data for this node required by this map type
            self._collectNodeData(node, key)

    def _buildBlocks_to_run(self, nodes):
        '''
        To Be Overloaded : What capture routines to run in order to build the DataMap up.
        Note that the self._buildBlock_poseDict(nodes) calls the self._collectNodeData per node
        as a way of gathering what info to be stored against each node.
        '''
        self.poseDict={}
        self._buildBlock_info()
        self._buildBlock_poseDict(nodes)

    def buildDataMap(self, nodes):
        '''
        build the internal dataMap dict, useful as a separate func so it
        can be used in the PoseCompare class easily. This is the main internal call
        for managing the actual pose data for save
        
        ..note:
            this replaces the original pose call self.buildInternalPoseData()
        '''
        self.metaRig=None
        self.rootJnt=None
        if not type(nodes)==list:
            nodes=[nodes]  # cast to list for consistency
        rootNode=nodes[0]

        if self.settings.filterIsActive() and self.useFilter:
            if self.metaPose:
                if self.setMetaRig(rootNode):
                    self.rootJnt=self.metaRig.getSkeletonRoots()
                    if self.rootJnt:
                        self.rootJnt=self.rootJnt[0]
            else:
                if cmds.attributeQuery('exportSkeletonRoot',node=rootNode,exists=True):
                    connectedSkel=cmds.listConnections('%s.%s' % (rootNode,'exportSkeletonRoot'),destination=True,source=True)
                    if connectedSkel and cmds.nodeType(connectedSkel)=='joint':
                        self.rootJnt=connectedSkel[0]
                    elif cmds.nodeType(rootNode)=='joint':
                        self.rootJnt=rootNode
                if cmds.attributeQuery('animSkeletonRoot',node=rootNode,exists=True):
                    connectedSkel=cmds.listConnections('%s.%s' % (rootNode,'animSkeletonRoot'),destination=True,source=True)
                    if connectedSkel and cmds.nodeType(connectedSkel)=='joint':
                        self.rootJnt=connectedSkel[0]
                    elif cmds.nodeType(rootNode)=='joint':
                        self.rootJnt=rootNode
        else:
            if self.metaPose:
                self.setMetaRig(rootNode)
                
        #fill the skip list, these attrs will be totally ignored by the code
        self.skipAttrs=self.getSkippedAttrs(rootNode)
        
        if self.hasFolderOverload():  # and self.useFilter:
            nodesToStore=self.getNodesFromFolderConfig(nodes,mode='save')
        else:
            nodesToStore=self.getNodes(nodes)
            
        if not nodesToStore:
            raise IOError('No Matching Nodes found to store the pose data from')
        
        self._buildBlocks_to_run(nodesToStore)
        
    
    # Data Mapping - Apply the dataMap ------------------------------------------------


    @r9General.Timer
    def _applyData_attrs(self, *args, **kws):
        '''
        Load Example for attrs : 
        use self.matchedPairs for the process list of pre-matched 
        tuples of (poseDict[key], node in scene)
        '''
        for key, dest in self.matchedPairs:
            log.debug('Applying Key Block : %s' % key)
            try:
                if not 'attrs' in self.poseDict[key]:
                    continue
                for attr, val in self.poseDict[key]['attrs'].items():
                    try:
                        val = eval(val)
                    except:
                        pass
                    log.debug('node : %s : attr : %s : val %s' % (dest, attr, val))
                    try:
                        cmds.setAttr('%s.%s' % (dest, attr), val)
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
                  
    # Process the data -------------------------------------------------
                                              
    def _writePose(self, filepath):
        '''
        Write the Pose ConfigObj to file
        '''
        ConfigObj = configobj.ConfigObj(indent_type='\t')
        ConfigObj['filterNode_settings']=self.settings.__dict__
        ConfigObj['poseData']=self.poseDict
        ConfigObj['info']=self.infoDict
        if self.skeletonDict:
            ConfigObj['skeletonDict']=self.skeletonDict
        ConfigObj.filename = filepath
        ConfigObj.write()

    @r9General.Timer
    def _readPose(self, filename):
        '''
        Read the pose file and build up the internal poseDict
        TODO: do we allow the data to be filled from the pose filter thats stored???????
        '''
        if filename:
            if os.path.exists(filename):
                #for key, val in configobj.ConfigObj(filename)['filterNode_settings'].items():
                #    self.settings.__dict__[key]=decodeString(val)
                self.poseDict=configobj.ConfigObj(filename)['poseData']
                if 'info' in configobj.ConfigObj(filename):
                    self.infoDict=configobj.ConfigObj(filename)['info']
                if 'skeletonDict' in configobj.ConfigObj(filename):
                    self.skeletonDict=configobj.ConfigObj(filename)['skeletonDict']
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
        
        ..note:
            this replaced the original call self._poseLoad_buildcache()
        '''
        if not type(nodes)==list:
            nodes=[nodes]  # cast to list for consistency
            
        if self.metaPose:
            self.setMetaRig(nodes[0])
            
        if self.filepath and not os.path.exists(self.filepath):
            raise StandardError('Given Path does not Exist')
                
        if self.filepath and self.hasFolderOverload():  # and useFilter:
            nodesToLoad = self.getNodesFromFolderConfig(nodes, mode='load')
        else:
            nodesToLoad=self.getNodes(nodes)
        if not nodesToLoad:
            raise StandardError('Nothing selected or returned by the filter to load the pose onto')
        
        if self.filepath:
            self._readPose(self.filepath)
            log.info('Pose Read Successfully from : %s' % self.filepath)

        if self.metaPose:
            print 'infoDict : ', self.infoDict
            print 'metaRig : ', self.metaRig
            if 'metaPose' in self.infoDict and self.metaRig:
                try:
                    if eval(self.infoDict['metaPose']):
                        self.matchMethod = 'metaData'
                except:
                    self.matchMethod = 'metaData'
            else:
                log.debug('Warning, trying to load a NON metaPose to a MRig - switching to NameMatching')
        
        #fill the skip list, these attrs will be totally ignored by the code
        self.skipAttrs=self.getSkippedAttrs(nodes[0])
                 
        #Build the master list of matched nodes that we're going to apply data to
        #Note: this is built up from matching keys in the poseDict to the given nodes
        self.matchedPairs = self._matchNodesToPoseData(nodesToLoad)
        
        return nodesToLoad
                    
    @r9General.Timer
    def _matchNodesToPoseData(self, nodes):
        '''
        Main filter to extract matching data pairs prior to processing
        return : tuple such that :  (poseDict[key], destinationNode)
        NOTE: I've changed this so that matchMethod is now an internal PoseData attr
        
        :param nodes: nodes to try and match from the poseDict
        '''
        matchedPairs=[]
        log.info('using matchMethod : %s' % self.matchMethod)
        if self.matchMethod=='stripPrefix' or self.matchMethod=='base':
            log.info('matchMethodStandard : %s' % self.matchMethod)
            matchedPairs=r9Core.matchNodeLists([key for key in self.poseDict.keys()], nodes, matchMethod=self.matchMethod)
        if self.matchMethod=='index':
            for i, node in enumerate(nodes):
                for key in self.poseDict.keys():
                    if int(self.poseDict[key]['ID'])==i:
                        matchedPairs.append((key,node))
                        log.debug('poseKey : %s %s >> matchedSource : %s %i' % (key, self.poseDict[key]['ID'], node, i))
                        break
        if self.matchMethod=='mirrorIndex':
            getMirrorID=r9Anim.MirrorHierarchy().getMirrorCompiledID
            for node in nodes:
                mirrorID=getMirrorID(node)
                if not mirrorID:
                    continue
                for key in self.poseDict.keys():
                    if self.poseDict[key]['mirrorID'] and self.poseDict[key]['mirrorID']==mirrorID:
                        matchedPairs.append((key,node))
                        log.debug('poseKey : %s %s >> matched MirrorIndex : %s' % (key, node, self.poseDict[key]['mirrorID']))
                        break
        if self.matchMethod=='metaData':
            getMetaDict=self.metaRig.getNodeConnectionMetaDataMap  # optimisation
            poseKeys=dict(self.poseDict)  # optimisation
            for node in nodes:
                try:
                    metaDict=getMetaDict(node)
                    for key in poseKeys:
                        if poseKeys[key]['metaData']==metaDict:
                            matchedPairs.append((key,node))
                            log.debug('poseKey : %s %s >> matched MetaData : %s' % (key, node, poseKeys[key]['metaData']))
                            poseKeys.pop(key)
                            break
                except:
                    log.info('FAILURE to load MetaData pose blocks - Reverting to Name')
                    matchedPairs=r9Core.matchNodeLists([key for key in self.poseDict.keys()], nodes)
        return matchedPairs
                             
    def matchInternalPoseObjects(self, nodes=None, fromFilter=True):
        '''
        This is a throw-away and only used in the UI to select for debugging!
        from a given poseFile return or select the internal stored objects
        '''
        InternalNodes=[]
        if not fromFilter:
            #no filter, we just pass in the longName thats stored
            for key in self.poseDict.keys():
                if cmds.objExists(self.poseDict[key]['longName']):
                    InternalNodes.append(self.poseDict[key]['longName'])
                elif cmds.objExists(key):
                    InternalNodes.append(key)
                elif cmds.objExists(r9Core.nodeNameStrip(key)):
                    InternalNodes.append(r9Core.nodeNameStrip(key))
        else:
            #use the internal Poses filter and then Match against scene nodes
            if self.settings.filterIsActive():
                filterData=r9Core.FilterNode(nodes,self.settings).ProcessFilter()
                matchedPairs=self._matchNodesToPoseData(filterData)
                if matchedPairs:
                    InternalNodes=[node for _,node in matchedPairs]
        if not InternalNodes:
            raise StandardError('No Matching Nodes found!!')
        return InternalNodes

    #Main Calls ----------------------------------------
  
    @r9General.Timer
    def saveData(self, nodes, filepath=None, useFilter=True, storeThumbnail=True):
        '''
        Generic entry point for the Data Save.
        
        :param nodes: nodes to store the data against OR the rootNode if the 
            filter is active.
        :param filepath: posefile to save - if not given the pose is cached on this 
            class instance.
        :param useFilter: use the filterSettings or not.
        '''
        #push args to object - means that any poseHandler.py file has access to them
        if filepath:
            self.filepath=filepath
            
        self.useFilter=useFilter
        if self.filepath:
            log.debug('PosePath given : %s' % self.filepath)
            
        self.buildDataMap(nodes)
        
        if self.filepath:
            self._writePose(self.filepath)
            
            if storeThumbnail:
                sel=cmds.ls(sl=True,l=True)
                cmds.select(cl=True)
                r9General.thumbNailScreen(filepath,self.thumbnailRes[0],self.thumbnailRes[1])
                if sel:
                    cmds.select(sel)
        log.info('Data Saved Successfully to : %s' % self.filepath)
        
        
    @r9General.Timer
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
        if not type(nodes)==list:
            nodes=[nodes]  # cast to list for consistency
        self.useFilter = useFilter  # used in the getNodes call
                     
        try:
            self._pre_load()
            
            nodesToLoad = self.processPoseFile(nodes)
            
            if not self.matchedPairs:
                raise StandardError('No Matching Nodes found in the PoseFile!')
            else:
                if self.prioritySnapOnly:
                    #we've already filtered the hierarchy, may as well just filter the results for speed
                    nodesToLoad=r9Core.prioritizeNodeList(nodesToLoad, self.settings.filterPriority, regex=True, prioritysOnly=True)
                    nodesToLoad.reverse()
                
                # nodes now matched, apply the data in the dataMap
                self._applyData()
        except StandardError,err:
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
    >>> #if we're storing as MetaData we also include:
    >>> poseDict['TestCtr']['metaData']['metaAttr'] = CTRL_L_Thing    = the attr that wires this node to the MetaSubsystem
    >>> poseDict['TestCtr']['metaData']['metaNodeID'] = L_Arm_System  = the metaNode this node is wired to via the above attr
    
    Matching of nodes against this dict is via either the nodeName, nodeIndex (ID) or
    the metaData block.
    
    New functionality allows you to use the main calls to cache a pose and reload it
    from this class instance, wraps things up nicely for you:
    
        >>> pose=r9Pose.PoseData()
        >>> pose.metaPose=True
        >>>
        >>> #cache the pose (just don't pass in a filePath)
        >>> pose.poseSave(cmds.ls(sl=True))
        >>> #reload the cache you just stored
        >>> pose.poseLoad(cmds.ls(sl=True))
    
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
        super(PoseData, self).__init__(filterSettings=filterSettings, *args,**kws)
        
        self.file_ext = '.pose'
        self.poseDict={}
        self.infoDict={}
        self.skeletonDict={}
        self.posePointCloudNodes=[]
        self.poseCurrentCache={}  # cached dict storing the current state of the objects prior to applying the pose
        self.relativePose=False
        self.relativeRots='projected'
        self.relativeTrans='projected'

    def _collectNodeData(self, node, key):
        '''
        collect the attr data from the node and add it to the poseDict[key]
        '''
        self._collectNodeData_attrs(node, key)

    def _buildBlock_skeletonData(self, rootJnt):
        '''
        :param rootNode: root of the skeleton to process
        '''
        self.skeletonDict={}
        if not rootJnt:
            log.info('skeleton rootJnt joint was not found')
            return
        
        fn=r9Core.FilterNode(rootJnt)
        fn.settings.nodeTypes='joint'
        fn.settings.incRoots=False
        skeleton=fn.ProcessFilter()

        for jnt in skeleton:
            key=r9Core.nodeNameStrip(jnt)
            self.skeletonDict[key]={}
            self.skeletonDict[key]['attrs']={}
            for attr in ['translateX','translateY','translateZ', 'rotateX','rotateY','rotateZ']:
                try:
                    self.skeletonDict[key]['attrs'][attr]=cmds.getAttr('%s.%s' % (jnt,attr))
                except:
                    log.debug('%s : attr is invalid in this instance' % attr)

    def _buildBlocks_to_run(self, nodes):
        '''
        What capture routines to run in order to build the poseDict data
        '''
        self.poseDict={}
        self._buildBlock_info()
        self._buildBlock_poseDict(nodes)
        self._buildBlock_skeletonData(self.rootJnt)

    def _cacheCurrentNodeStates(self):
        '''
        this is purely for the _applyPose with percent and optimization for the UI's
        '''
        log.info('updating the currentCache')
        self.poseCurrentCache={}
        for key, dest in self.matchedPairs:
            log.debug('caching current node data : %s' % key)
            self.poseCurrentCache[key]={}
            if not 'attrs' in self.poseDict[key]:
                continue
            for attr, _ in self.poseDict[key]['attrs'].items():
                try:
                    self.poseCurrentCache[key][attr]=cmds.getAttr('%s.%s' % (dest, attr))
                except:
                    log.debug('Attr mismatch on destination : %s.%s' % (dest, attr))
                
    @r9General.Timer
    def _applyData(self, percent=None):
        '''
        :param percent: percent of the pose to load
        '''
        mix_percent=False  # gets over float values of zero from failing
        if percent or type(percent)==float:
            mix_percent=True
            if not self.poseCurrentCache:
                self._cacheCurrentNodeStates()
            
        for key, dest in self.matchedPairs:
            log.debug('Applying Key Block : %s' % key)
            try:
                if not 'attrs' in self.poseDict[key]:
                    continue
                for attr, val in self.poseDict[key]['attrs'].items():
                    if attr in self.skipAttrs:
                        log.debug('Skipping attr as requested : %s' % attr)
                        continue
                    try:
                        val = eval(val)
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
                  

    #Main Calls ----------------------------------------
  
    @r9General.Timer
    def poseSave(self, nodes, filepath=None, useFilter=True, storeThumbnail=True):
        '''
        Entry point for the generic PoseSave.
        
        :param nodes: nodes to store the data against OR the rootNode if the 
            filter is active.
        :param filepath: posefile to save - if not given the pose is cached on this 
            class instance.
        :param useFilter: use the filterSettings or not.
        :param storeThumbnail: generate and store a thu8mbnail from the screen to go alongside the pose
        '''
        #push args to object - means that any poseHandler.py file has access to them
        if filepath:
            self.filepath=filepath
            
        self.useFilter=useFilter
        if self.filepath:
            log.debug('PosePath given : %s' % self.filepath)
            
        self.buildDataMap(nodes)
        
        if self.filepath:
            self._writePose(self.filepath)
            
            if storeThumbnail:
                sel=cmds.ls(sl=True,l=True)
                cmds.select(cl=True)
                r9General.thumbNailScreen(self.filepath, self.thumbnailRes[0], self.thumbnailRes[1])
                if sel:
                    cmds.select(sel)
        log.info('Pose Saved Successfully to : %s' % self.filepath)
        
    @r9General.Timer
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
        '''
        
        if relativePose and not cmds.ls(sl=True):
            raise StandardError('Nothing selected to align Relative Pose too')
        if not type(nodes)==list:
            nodes=[nodes]  # cast to list for consistency
        
        #push args to object - means that any poseHandler.py file has access to them
        self.relativePose = relativePose
        self.relativeRots = relativeRots
        self.relativeTrans = relativeTrans
        self.PosePointCloud = None
        
        if filepath:
            self.filepath=filepath
            
        self.useFilter = useFilter  # used in the getNodes call
        self.maintainSpaces = maintainSpaces
        self.mayaUpAxis = r9Setup.mayaUpAxis()
        
        nodesToLoad = self.processPoseFile(nodes)
        
        if not self.matchedPairs:
            raise StandardError('No Matching Nodes found in the PoseFile!')
        else:
            if self.relativePose:
                if self.prioritySnapOnly:
                    #we've already filtered the hierarchy, may as well just filter the results for speed
                    nodesToLoad=r9Core.prioritizeNodeList(nodesToLoad, self.settings.filterPriority, regex=True, prioritysOnly=True)
                    nodesToLoad.reverse()
                    
                #setup the PosePointCloud -------------------------------------------------
                reference=cmds.ls(sl=True,l=True)[0]
                self.PosePointCloud=PosePointCloud(nodesToLoad)
                self.PosePointCloud.buildOffsetCloud(reference, raw=True)
                resetCache=[cmds.getAttr('%s.translate' % self.PosePointCloud.posePointRoot),
                            cmds.getAttr('%s.rotate' % self.PosePointCloud.posePointRoot)]
                
                if self.maintainSpaces:
                    if self.metaRig:
                        parentSpaceCache=self.getMaintainedAttrs(nodesToLoad, self.metaRig.parentSwitchAttr)
                    elif 'parentSpaces' in self.settings.rigData:
                        parentSpaceCache=self.getMaintainedAttrs(nodesToLoad, self.settings.rigData['parentSpaces'])
    
            self._applyData(percent)

            if self.relativePose:
                #snap the poseCloud to the new xform of the referenced node, snap the cloud
                #to the pose, reset the clouds parent to the cached xform and then snap the
                #nodes back to the cloud
                r9Anim.AnimFunctions.snap([reference,self.PosePointCloud.posePointRoot])
                 
                if self.relativeRots=='projected':
                    if self.mayaUpAxis=='y':
                        cmds.setAttr('%s.rx' % self.PosePointCloud.posePointRoot,0)
                        cmds.setAttr('%s.rz' % self.PosePointCloud.posePointRoot,0)
                    elif self.mayaUpAxis=='z':  # fucking Z!!!!!!
                        cmds.setAttr('%s.rx' % self.PosePointCloud.posePointRoot,0)
                        cmds.setAttr('%s.ry' % self.PosePointCloud.posePointRoot,0)
                    
                self.PosePointCloud.snapPosePntstoNodes()
                
                if not self.relativeTrans=='projected':
                    cmds.setAttr('%s.translate' % self.PosePointCloud.posePointRoot,
                                 resetCache[0][0][0],
                                 resetCache[0][0][1],
                                 resetCache[0][0][2])
                if not self.relativeRots=='projected':
                    cmds.setAttr('%s.rotate' % self.PosePointCloud.posePointRoot,
                                 resetCache[1][0][0],
                                 resetCache[1][0][1],
                                 resetCache[1][0][2])
               
                if self.relativeRots=='projected':
                    if self.mayaUpAxis=='y':
                        cmds.setAttr('%s.ry' % self.PosePointCloud.posePointRoot,resetCache[1][0][1])
                    elif self.mayaUpAxis=='z':  # fucking Z!!!!!!
                        cmds.setAttr('%s.rz' % self.PosePointCloud.posePointRoot,resetCache[1][0][2])
                if self.relativeTrans=='projected':
                    if self.mayaUpAxis=='y':
                        cmds.setAttr('%s.tx' % self.PosePointCloud.posePointRoot,resetCache[0][0][0])
                        cmds.setAttr('%s.tz' % self.PosePointCloud.posePointRoot,resetCache[0][0][2])
                    elif self.mayaUpAxis=='z':  # fucking Z!!!!!!
                        cmds.setAttr('%s.tx' % self.PosePointCloud.posePointRoot,resetCache[0][0][0])
                        cmds.setAttr('%s.ty' % self.PosePointCloud.posePointRoot,resetCache[0][0][1])
                
                #if maintainSpaces then restore the original parentSwitch attr values
                #BEFORE pushing the point cloud data back to the rig
                if self.maintainSpaces and parentSpaceCache:  # and self.metaRig:
                    for child,attr,value in parentSpaceCache:
                        log.debug('Resetting parentSwitches : %s.%s = %f' % (r9Core.nodeNameStrip(child),attr,value))
                        cmds.setAttr('%s.%s' % (child,attr), value)
                            
                self.PosePointCloud.snapNodestoPosePnts()
                self.PosePointCloud.delete()
                cmds.select(reference)


class PosePointCloud(object):
    '''
    PosePointCloud is the technique inside the PoseSaver used to snap the pose into
    relative space. It's been added as a tool in it's own right as it's sometimes
    useful to be able to shift poses in global space.
    '''
    def __init__(self, nodes, filterSettings=None, meshes=[], *args, **kws):
        '''
        :param rootReference: the object to be used as the PPT's pivot reference
        :param nodes: feed the nodes to process in as a list, if a filter is given
                      then these are the rootNodes for it
        :param filterSettings: pass in a filterSettings object to filter the given hierarchy
        :param meshes: this is really for reference, rather than make a locator, pass in a reference geo
                     which is then shapeSwapped for the PPC root node giving great reference!
        '''
           
        self.meshes = meshes
        if self.meshes and not isinstance(self.meshes, list):
            self.meshes=[meshes]

        self.refMesh = 'posePointCloudGeoRef'  # name for the duplicate meshes used
        self.mayaUpAxis = r9Setup.mayaUpAxis()
        self.inputNodes = nodes         # inputNodes for processing
        self.posePointCloudNodes = []   # generated ppc nodes
        self.posePointRoot = None       # generated rootnode of the ppc
        self.settings = None
        self.prioritySnapOnly=False     # ONLY make ppc points for the filterPriority nodes
        
        self.rootReference = None   # root node used as the main pivot for the cloud
        self.isVisible = True       # Do we build the visual reference setup or not?
        
        self.ppcMeta=None  # MetaNode to cache the data
        
        if filterSettings:
            if not issubclass(type(filterSettings), r9Core.FilterNode_Settings):
                raise StandardError('filterSettings param requires an r9Core.FilterNode_Settings object')
            elif filterSettings.filterIsActive():
                self.settings=filterSettings
        else:
            self.settings=r9Core.FilterNode_Settings()

    def __connectdataToMeta__(self):
        '''
        on build push the data to a metaNode so it's cached in the scene incase we need to 
        reconstruct anything at a later date. This is used extensivly in the AnimReDirect calls
        '''
        self.ppcMeta = r9Meta.MetaClass(name='PPC_Root')
        self.ppcMeta.mClassGrp='PPCROOT'
        self.ppcMeta.connectChild(self.posePointRoot, 'posePointRoot')
        self.ppcMeta.addAttr('posePointCloudNodes', self.posePointCloudNodes)
         
    def syncdatafromCurrentInstance(self):
        '''
        pull existing data back from the metaNode
        '''
        self.ppcMeta=self.getCurrentInstances()
        if self.ppcMeta:
            self.ppcMeta=self.ppcMeta[0]
            self.posePointCloudNodes=self.ppcMeta.posePointCloudNodes
            self.posePointRoot=self.ppcMeta.posePointRoot[0]
              
    def getPPCNodes(self):
        '''
        return a list of the PPC nodes
        '''
        return [ppc for ppc,_ in self.posePointCloudNodes]

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
        for pnt,node in self.posePointCloudNodes:
            log.debug('snapping PPT : %s' % pnt)
            r9Anim.AnimFunctions.snap([node,pnt])

    def snapNodestoPosePnts(self):
        '''
        snap each MAYA node to it's respective pntCloud point
        '''
        for pnt, node in self.posePointCloudNodes:
            log.debug('snapping Ctrl : %s > %s : %s' % (r9Core.nodeNameStrip(node), pnt, node))
            r9Anim.AnimFunctions.snap([pnt,node])

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
        '''
        
        self.deleteCurrentInstances()

        self.posePointRoot=cmds.ls(cmds.spaceLocator(name='posePointCloud'),l=True)[0]
        cmds.setAttr('%s.visibility' % self.posePointRoot, self.isVisible)
       
        ppcShape=cmds.listRelatives(self.posePointRoot,type='shape')[0]
        cmds.setAttr("%s.localScaleZ" % ppcShape, 30)
        cmds.setAttr("%s.localScaleX" % ppcShape, 30)
        cmds.setAttr("%s.localScaleY" % ppcShape, 30)
        if rootReference:
            self.rootReference=rootReference
        if self.settings.filterIsActive():
            if self.prioritySnapOnly:
                self.settings.searchPattern=self.settings.filterPriority
            self.inputNodes=r9Core.FilterNode(self.inputNodes, self.settings).ProcessFilter()
        if self.inputNodes:
            self.inputNodes.reverse()  # for the snapping operations
        
        if self.mayaUpAxis=='y':
            cmds.setAttr('%s.rotateOrder' % self.posePointRoot, 2)
        if self.rootReference:  # and not mesh:
            r9Anim.AnimFunctions.snap([self.rootReference,self.posePointRoot])
            
            #reset the PPTCloudRoot to projected ground plane
            if projectedRots:
                cmds.setAttr('%s.rx' % self.posePointRoot, 0)
                cmds.setAttr('%s.rz' % self.posePointRoot, 0)
            if projectedTrans:
                cmds.setAttr('%s.ty' % self.posePointRoot, 0)
                
        for node in self.inputNodes:
            pnt=cmds.spaceLocator(name='pp_%s' % r9Core.nodeNameStrip(node))[0]
            if not raw:
                r9Anim.AnimFunctions.snap([node,pnt])
            cmds.parent(pnt,self.posePointRoot)
            self.posePointCloudNodes.append((pnt,node))
        cmds.select(self.posePointRoot)
        
        # generate the mesh references if required
        self.generateVisualReference()
            
        self.__connectdataToMeta__()
        return self.posePointCloudNodes
    
    def shapeSwapMeshes(self, selectable=True):
        '''
        Swap the mesh Geo so it's a shape under the PPC transform root
        TODO: Make sure that the duplicate message link bug is covered!!
        '''
        currentCount = len(cmds.listRelatives(self.posePointRoot, type='shape'))
        for i,mesh in enumerate(self.meshes):
            dupMesh = cmds.duplicate(mesh, rc=True, n=self.refMesh+str(i + currentCount))[0]
            dupShape = cmds.listRelatives(dupMesh, type='shape')[0]
            r9Core.LockChannels().processState(dupMesh,['tx','ty','tz','rx','ry','rz','sx','sy','sz'],\
                                               mode='fullkey',hierarchy=False)
            try:
                if selectable:
                    #turn on the overrides so the duplicate geo can be selected
                    cmds.setAttr("%s.overrideDisplayType" % dupShape, 0)
                    cmds.setAttr("%s.overrideEnabled" % dupShape, 1)
                    cmds.setAttr("%s.overrideLevelOfDetail" % dupShape, 0)
                else:
                    cmds.setAttr("%s.overrideDisplayType" % dupShape, 2)
                    cmds.setAttr("%s.overrideEnabled" % dupShape, 1)
            except:
                log.debug('Couldnt set the draw overrides for the refGeo')
            cmds.parent(dupMesh,self.posePointRoot)
            cmds.makeIdentity(dupMesh,apply=True,t=True,r=True)
            cmds.parent(dupShape,self.posePointRoot,r=True,s=True)
            cmds.delete(dupMesh)

    def applyPosePointCloud(self):
        self.snapNodestoPosePnts()

    def updatePosePointCloud(self):
        self.snapPosePntstoNodes()
        if self.meshes:
            cmds.delete(cmds.listRelatives(self.posePointRoot, type=['mesh','nurbsCurve']))
            self.generateVisualReference()
            cmds.refresh()

    def delete(self):
        root=self.posePointRoot
        if not root:
            root=self.ppcMeta.posePointRoot[0]
        self.ppcMeta.delete()
        cmds.delete(root)
        
    def deleteCurrentInstances(self):
        '''
        delete any current instances of PPC clouds
        '''
        PPCNodes=self.getCurrentInstances()
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
    
    >>> #build an mPose object and fill the internal poseDict
    >>> mPoseA=r9Pose.PoseData()
    >>> mPoseA.metaPose=True
    >>> mPoseA.buildInternalPoseData(cmds.ls(sl=True))
    >>> 
    >>> mPoseB=r9Pose.PoseData()
    >>> mPoseB.metaPose=True
    >>> mPoseB.buildInternalPoseData(cmds.ls(sl=True))
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
                 compareDict='poseDict', filterMap=[], ignoreBlocks=[]):
        '''
        Make sure we have 2 PoseData objects to compare
        :param currentPose: either a PoseData object or a valid pose file
        :param referencePose: either a PoseData object or a valid pose file
        :param tolerance: tolerance by which floats are matched
        :param angularTolerance: the tolerance used to check rotate attr float values
        :param linearTolerance: the tolerance used to check all other float attrs
        :param compareDict: the internal main dict in the pose file to compare the data with
        :param filterMap: if given this is used as a high level filter, only matching nodes get compared
            others get skipped. Good for passing in a mater core skeleton to test whilst ignoring extra nodes
        :param ignoreBlocks: allows the given failure blocks to be ignored. We mainly use this for ['missingKeys']
        
        .. note::
            In the new setup if the skeletonRoot jnt is found we add a whole
            new dict to serialize the current skeleton data to the pose, this means that
            we can compare a pose on a rig via the internal skeleton transforms as well
            as the actual rig controllers...makes validation a lot more accurate for export
                * 'poseDict'     = [poseData] main controller data
                * 'skeletonDict' = [skeletonDict] block generated if exportSkeletonRoot is connected
                * 'infoDict'     = [info] block
        '''
        self.status = False
        self.compareDict = compareDict
        self.angularTolerance = angularTolerance
        self.angularAttrs = ['rotateX', 'rotateY', 'rotateZ']
        
        self.linearTolerance = linearTolerance
        self.linearAttrs = ['translateX', 'translateY', 'translateZ']
        
        self.filterMap = filterMap
        self.ignoreBlocks = ignoreBlocks
        
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
        if not 'failedAttrs' in self.fails:
            self.fails['failedAttrs'] = {}
        if not key in self.fails['failedAttrs']:
            self.fails['failedAttrs'][key] = {}
        if not 'attrMismatch' in self.fails['failedAttrs'][key]:
            self.fails['failedAttrs'][key]['attrMismatch'] = []
        self.fails['failedAttrs'][key]['attrMismatch'].append(attr)
       
    def compare(self):
        '''
        Compare the 2 PoseData objects via their internal [key][attrs] blocks
        return a bool. After processing self.fails is a dict holding all the fails
        for processing later if required
        '''
        self.fails = {}
        logprint = 'PoseCompare returns : %s ========================================\n' % self.compareDict
        currentDic = getattr(self.currentPose, self.compareDict)
        referenceDic = getattr(self.referencePose, self.compareDict)
        
        if not currentDic or not referenceDic:
            raise StandardError('missing pose section <<%s>> compare aborted' % self.compareDict)
        
        for key, attrBlock in currentDic.items():
            if self.filterMap and not key in self.filterMap:
                log.debug('node not in filterMap - skipping key %s' % key)
                continue
            if key in referenceDic:
                referenceAttrBlock = referenceDic[key]
            else:
                if not 'missingKeys' in self.ignoreBlocks:
                    logprint += 'ERROR: Key Mismatch : %s\n' % key
                    if not 'missingKeys' in self.fails:
                        self.fails['missingKeys'] = []
                    self.fails['missingKeys'].append(key)
                else:
                    log.debug('missingKeys in ignoreblock : node is missing from data but being skipped "%s"' % key)
                continue

            if not 'attrs' in attrBlock:
                log.debug('%s node has no attrs block in the pose' % key)
                continue
            for attr, value in attrBlock['attrs'].items():
                # attr missing completely from the key
                if not attr in referenceAttrBlock['attrs']:
                    if not 'failedAttrs' in self.fails:
                        self.fails['failedAttrs'] = {}
                    if not key in self.fails['failedAttrs']:
                        self.fails['failedAttrs'][key] = {}
                    if not 'missingAttrs' in self.fails['failedAttrs'][key]:
                        self.fails['failedAttrs'][key]['missingAttrs'] = []
                    self.fails['failedAttrs'][key]['missingAttrs'].append(attr)
                    # log.info('missing attribute in data : "%s.%s"' % (key,attr))
                    logprint += 'ERROR: Missing attribute in data : "%s.%s"\n' % (key, attr)
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
                        # log.info('AttrValue float mismatch : "%s.%s" currentValue=%s >> expectedValue=%s' % (key,attr,value,refValue))
                        logprint += 'ERROR: AttrValue float mismatch : "%s.%s" currentValue=%s >> expectedValue=%s\n' % (key, attr, value, refValue)
                        continue
                elif not value == refValue:
                    self.__addFailedAttr(key, attr)
                    # log.info('AttrValue mismatch : "%s.%s" currentValue=%s >> expectedValue=%s' % (key,attr,value,refValue))
                    logprint += 'ERROR: AttrValue mismatch : "%s.%s" currentValue=%s >> expectedValue=%s\n' % (key, attr, value, refValue)
                    continue
                
        if 'missingKeys' in self.fails or 'failedAttrs' in self.fails:
            logprint += 'PoseCompare returns : ========================================'
            print logprint
            return False
        self.status = True
        return True

         

def batchPatchPoses(posedir, config, poseroot, load=True, save=True, patchfunc=None,\
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

    filterObj=r9Core.FilterNode_Settings()
    filterObj.read(os.path.join(r9Setup.red9ModulePath(), 'presets', config))  # 'Crytek_New_Meta.cfg'))
    mPose=PoseData(filterObj)
    
    files=os.listdir(posedir)
    files.sort()
    for f in files:
        if f.lower().endswith('.pose'):
            if load:
                mPose.poseLoad(poseroot, os.path.join(posedir,f),
                               useFilter=True,
                               relativePose=relativePose,
                               relativeRots=relativeRots,
                               relativeTrans=relativeTrans)
            if patchfunc:
                patchfunc(f)
            if save:
                mPose.poseSave(poseroot, os.path.join(posedir,f), useFilter=True, storeThumbnail=False)
            log.info('Processed Pose File :  %s' % f)

