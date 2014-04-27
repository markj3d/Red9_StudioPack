'''
..
    Red9 Studio Pack: Maya Pipeline Solutions
    Author: Mark Jackson
    email: rednineinfo@gmail.com
    
    Red9 blog : http://red9-consultancy.blogspot.co.uk/
    MarkJ blog: http://markj3d.blogspot.co.uk
    
    This is the Core library of utils used throughout the modules
    
    Setup : Follow the Install instructions in the Modules package
'''

from __future__ import with_statement  # required only for Maya2009/8
import maya.cmds as cmds
import maya.OpenMaya as OpenMaya

from functools import partial
import re
import random
import math

import Red9.packages.configobj as configobj
import Red9.startup.setup as r9Setup

import Red9_General as r9General
import Red9_Audio as r9Audio
import Red9_AnimationUtils as r9Anim
import Red9_Meta as r9Meta

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)



# Generic  Functions
#---------------------------------------------------------------------------------

def nodeNameStrip(node):
    '''
    Simple method to strip any |Path and :Namespaces: from
    a given object DagPath ie Ns:Rig|Ns:Leg|Ns:Foot == Foot
    '''
    return node.split('|')[-1].split(':')[-1]


def prioritizeNodeList(nList, priorityList, regex=True, prioritysOnly=False):
    '''
    Simple function to force the order of a given nList such that nodes
    in the given priority list are moved to the front of the list.
    
    :param nList: main input list
    :param priorityList: list which is used to prioritize/order the main nList
    '''
    stripped = [nodeNameStrip(node) for node in nList]  # stripped back to nodeName
    reordered = []
    
    if regex:
        for pNode in priorityList:
            for index, node in enumerate(stripped):
                if re.search(pNode, node):
                    reordered.append(nList[index])
                    nList.pop(index)
                    stripped.remove(node)
    else:
        for pNode in priorityList:
            if pNode in stripped:
                index = stripped.index(pNode)
                reordered.append(nList[index])
                nList.pop(index)
                stripped.pop(index)
    if not prioritysOnly:
        reordered.extend(nList)
    # [log.debug('Prioritized Index: %i = %s  <: ORIGINALLY :>  %s' % (i,nodeNameStrip(reordered[i]),n))\
    #     for i,n in enumerate(stripped)]
    return reordered

     
def sortNumerically(data):
    """
    Sort the given data in the way that humans expect.
    
    >>> data=['Joint_1','Joint_2','Joint_9','Joint_10','Joint_11','Joint_12']
    >>>
    >>> #standard gives us:
    >>> data.sort()
    >>> ['Joint_1', 'Joint_10', 'Joint_11', 'Joint_12', 'Joint_2', 'Joint_9']
    >>> 
    >>> #sortNumerically gives us:
    >>> sortNumerically(data)
    >>> ['Joint_1', 'Joint_2', 'Joint_9', 'Joint_10', 'Joint_11', 'Joint_12']
    """
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
    return sorted(data, key=alphanum_key)


def stringReplace(text, replace_dict):
    '''
    Replace words in a text that match a key in replace_dict
    with the associated value, return the modified text.
    Only whole words are replaced.
    Note that replacement is case sensitive, but attached
    quotes and punctuation marks are neutral.
    '''
    rc = re.compile(r"[A-Za-z_]\w*")
    def translate(match):
        word = match.group(0)
        return replace_dict.get(word, word)
    return rc.sub(translate, text)


def decodeString(val):
    '''
    From configObj the return is a string, we want to encode
    it back to it's original state so we pass it through this
    '''
    if not issubclass(type(val), str) and not type(val)==unicode:
        #log.debug('Val : %s : is not a string / unicode' % val)
        #log.debug('ValType : %s > left undecoded' % type(val))
        return val
    if val=='False' or val=='True' or val=='None':
        #log.debug('Decoded as type(bool)')
        return eval(val)
    elif val=='[]':
        #log.debug('Decoded as type(empty list)')
        return eval(val)
    elif val=='()':
        #log.debug('Decoded as type(empty tuple)')
        return eval(val)
    elif val=='{}':
        #log.debug('Decoded as type(empty dict)')
        return eval(val)
    elif (val[0]=='[' and val[-1] ==']'):
        #log.debug('Decoded as type(list)')
        return eval(val)
    elif (val[0] =='(' and val[-1]==')'):
        #log.debug('Decoded as type(tuple)')
        return eval(val)
    elif (val[0] =='{' and val[-1]=='}'):
        #log.debug('Decoded as type(dict)')
        return eval(val)
    try:
        encoded=int(val)
        #log.debug('Decoded as type(int)')
        return encoded
    except:
        pass
    try:
        encoded=float(val)
        #log.debug('Decoded as type(float)')
        return encoded
    except:
        pass
    #log.debug('Decoded as type(string)')
    return val

def floatIsEqual(a, b, tolerance=0.01, allowGimbal=True):
    '''
    compare 2 floats with tolerance.
    
    :param a: value 1 
    :param b: value 2 
    :param tolerance: compare with this tolerance default=0.001 
    :param allowGimbal: allow values differences to be divisible by 180 compensate for gimbal flips 
    
    '''
    if abs(a - b) < tolerance:
        return True
    else:
        if allowGimbal:
            mod = abs(a - b) % 180.0
            if mod < tolerance:
                log.debug('compare passed with gimbal : %f == %f : diff = %f' % (a, b, mod))
                return True
            elif abs(180.0 - mod) < tolerance:
                log.debug('compare passed with gimbal 180 : %f == %f : diff = %f' % (a, b, abs(180 - mod)))
                return True
            elif abs(90.0 - mod) < tolerance:
                log.debug('compare passed with gimbal 90 : %f == %f diff = %f' % (a, b, abs(90.0 - mod)))
                return True
            log.debug('compare with gimbal failed against mod 180: best diff :%f' % (abs(180.0-mod)))
            log.debug('compare with gimbal failed against mod 90: best diff :%f' % (abs(90.0-mod)))
    log.debug('float is out of tolerance : %f - %f == %f' % (a, b, abs(a - b)))
    return False

def valueToMappedRange(value, currentMin, currentMax, givenMin, givenMax):
    '''
    we have a min max range, lets say 0.5 - 15 and we want to map the
    range to a new range say 0-1 and return where the value given is
    in that new range
    '''
    # Figure out how 'wide' each range is
    currentSpan = currentMax - currentMin
    givenSpan = givenMax - givenMin
    # Convert the left range into a 0-1 range (float)
    valueScaled = float(value - currentMin) / float(currentSpan)
    # Convert the 0-1 range into a value in the right range.
    return givenMin + (valueScaled * givenSpan)
    
def validateString(strText):
    '''
    Function to validate that a string has no illegal characters
    '''
    #numerics=['1','2','3','4','5','6','7','8','9','0']
    illegals=['-', '#', '!', ' ']
    #if strText[0] in numerics:
    #    raise ValueError('Strings must NOT start with a numeric! >> %s' % strText)
    illegal=[i for i in illegals if i in strText]
    if illegal:
        raise ValueError('String contains illegal characters "%s" <in> "%s"' % (','.join(illegal), strText))
    else:
        return strText
    
    
#Filter Node Setups ----------------------------------------------------------------------

class FilterNode_Settings(object):
    '''
    Simple concept, this settings object is passed into the filterNode Calls
    and is used to setup how hierarchies are processed and filtered. This is
    class is used through out Red in conjunction with the filterNode class. 
    
    Default settings bound:
        * nodeTypes: []  - search for given Maya nodeTypes'
        * searchAttrs: [] - search for given attributes on nodes
        * searchPattern: [] - search for nodeName patterns
        * hierarchy: False - full hierarchy process
        * metaRig: False - ??Do we do this here?? {'MetaClass','functCall'}
        * filterPriority: [] - A way of re-ordering the hierarchy lists
        * incRoots: True - process rootNodes in the filters
        * transformClamp: True - clamp any nodes found to their transforms
        * infoBlock: ''
        * rigData: {}
    '''
    def __init__(self):
        self.__dict__ = {'nodeTypes': [],  # search for given Maya nodeTypes
                       'searchAttrs': [],  # search for given attributes on nodes
                       'searchPattern': [],  # search for nodeName patterns
                       'hierarchy': False,  # full hierarchy process
                       'metaRig': False,  # ??Do we do this here?? {'MetaClass','functCall'}
                       'filterPriority': [],  # A way of re-ordering the hierarchy lists
                       'incRoots': True,  # process rootNodes in the filters
                       'transformClamp': True,  # clamp any nodes found to their transforms
                       'infoBlock': '',
                       'rigData': {}}
        self.resetFilters()  # Just in case I screw up below
        
    def __repr__(self):
        '''
        print back ONLY the active filters when the object is inspected
        '''
        activeFilters=[]
        if self.metaRig:
            activeFilters.append('metaRig=%s' % self.metaRig)
        if self.nodeTypes:
            activeFilters.append('nodeTypes=%s' % self.nodeTypes)
        if self.searchAttrs:
            activeFilters.append('searchAttrs=%s' % self.searchAttrs)
        if self.searchPattern:
            activeFilters.append('searchPattern=%s' % self.searchPattern)
        if self.hierarchy:
            activeFilters.append('hierarchy=%s' % self.hierarchy)
        if self.filterPriority:
            activeFilters.append('filterPriority=%s' % self.filterPriority)
        if self.incRoots:
            activeFilters.append('incRoots=%s' % self.incRoots)
        if self.transformClamp:
            activeFilters.append('transformClamp=%s' % self.transformClamp)
        return '%s(ActiveFilters: %s)' % (self.__class__.__name__, (',').join(activeFilters))
    
    def filterIsActive(self):
        if self.nodeTypes or self.searchAttrs or self.searchPattern or self.hierarchy or self.metaRig:
            return True
        return False
    
    def printSettings(self):
        log.info('FilterNode Settings : nodeTypes : %s :   %s' %
                 (self.nodeTypes, type(self.nodeTypes)))
        log.info('FilterNode Settings : searchAttrs : %s :   %s' %
                 (self.searchAttrs, type(self.searchAttrs)))
        log.info('FilterNode Settings : searchPattern : %s :   %s' %
                 (self.searchPattern, type(self.searchPattern)))
        log.info('FilterNode Settings : hierarchy : %s :   %s' %
                 (self.hierarchy, type(self.hierarchy)))
        log.info('FilterNode Settings : incRoots : %s :   %s' %
                 (self.incRoots, type(self.incRoots)))
        log.info('FilterNode Settings : metaRig : %s :   %s' %
                 (self.metaRig, type(self.metaRig)))
        log.info('FilterNode Settings : transformClamp : %s :   %s' %
                 (self.transformClamp, type(self.transformClamp)))
        log.info('FilterNode Settings : filterPriority : %s :   %s' %
                 (self.filterPriority, type(self.filterPriority)))
        log.info('FilterNode Settings : rigData : %s :   %s' %
                 (self.rigData, type(self.rigData)))
        
    def resetFilters(self, rigData=True):
        '''
        reset the MAIN filter args only
        :param rigData: this is a cached attr and not fully handled 
        by the UI hence the option NOT to reset, used by the UI presetFill calls
        '''
        self.nodeTypes=[]
        self.searchAttrs=[]
        self.searchPattern=[]
        self.hierarchy=False
        self.filterPriority=[]
        self.incRoots=True
        self.metaRig=False
        self.transformClamp=True
        self.infoBlock=""
        if rigData:
            self.rigData={}
        
#    def write(self,filepath):
#        '''
#        write the filterSettings attribute out to a ConfigFile
#        @param filepath: file path to write the configFile out to
#        '''
#        config = ConfigParser.RawConfigParser()
#        config.optionxform=str #prevent options being converted to lowerCase
#        config.add_section('filterNode_settings')
#        for key, val in self.__dict__.items():
#            config.set('filterNode_settings', key, val)
#
#        # Writing our configuration file to 'example.cfg'
#        with open(filepath, 'wb') as configfile:
#            config.write(configfile)

#    def read(self,filepath):
#        '''
#        Read a given ConfigFile and fill this object instance with the data
#        @param filepath: file path to write the configFile out to
#        '''
#        config = ConfigParser.RawConfigParser()
#        config.optionxform=str #prevent options being converted to lowerCase
#        config.read(filepath)
#
#        self.resetFilters()
#
#        settings=dict(config.items("filterNode_settings"))
#        for key,val in settings.items():
#            #because config is built from string data
#            #we need to deal with specific types here
#            try:
#                self.__dict__[key]=decodeString(val)
#            except:
#                pass
                  
    def write(self, filepath):
        '''
        write the filterSettings attribute out to a ConfigFile
        :param filepath: file path to write the configFile out to
        '''
        ConfigObj = configobj.ConfigObj(indent_type='\t')
        ConfigObj['filterNode_settings']=self.__dict__
        ConfigObj.filename = filepath
        ConfigObj.write()
        
           
    def read(self, filepath):
        '''
        Read a given ConfigFile and fill this object instance with the data
        :param filepath: file path to write the configFile out to
        '''
        self.resetFilters()
        for key, val in configobj.ConfigObj(filepath)['filterNode_settings'].items():
            #because config is built from string data
            #we need to deal with specific types here
            try:
                self.__dict__[key]=decodeString(val)
            except:
                pass

  
# UI CALLS :
#---------------------------------------------------------------------------------
    
class FilterNode_UI(object):

    def __init__(self, settings=None):
        #Make a single filterNode instance
        self._filterNode=FilterNode()
        self._filterNode.settings.transformClamp=True
        
    @classmethod
    def show(cls):
        cls()._showUI()
               
    def _showUI(self):
        self.win = 'NodeSearch'
        self.cbNodeTypes=[]  # checkBox store for nodeTypes
        
        if cmds.window(self.win, exists=True):
            cmds.deleteUI(self.win, window=True)
        window = cmds.window(self.win, title="Node Searcher", widthHeight=(400, 400))
        cmds.menuBarLayout()
        cmds.menu(l="VimeoHelp")
        cmds.menuItem(l="Open Vimeo Help File",\
                      c="import Red9.core.Red9_General as r9General;r9General.os_OpenFile('https://vimeo.com/56551684')")
        cmds.menuItem(divider=True)
        cmds.menuItem(l="Contact Me", c=lambda *args: (r9Setup.red9ContactInfo()))
        self.MainLayout=cmds.columnLayout(adjustableColumn=True)
        cmds.frameLayout(label='Complex Node Search', cll=True, borderStyle='etchedOut')
        cmds.columnLayout(adjustableColumn=True)
        cmds.separator(h=15, style='none')
        
        #====================
        # Intersector
        #====================
        cmds.rowColumnLayout(ann='nodeTypeSelectors', numberOfColumns=3, columnWidth=[(1, 130), (2, 130), (3, 130)], columnSpacing=[(1, 10)])
        cmds.checkBox(l='Meshes', v=False,
                        onc=lambda x: self.cbNodeTypes.append('mesh'),
                        ofc=lambda x: self.cbNodeTypes.remove('mesh'))
        cmds.checkBox(l='Locators', v=False,
                        onc=lambda x: self.cbNodeTypes.append('locator'),
                        ofc=lambda x: self.cbNodeTypes.remove('locator'))
        cmds.checkBox(l='Joints', v=False,
                        onc=lambda x: self.cbNodeTypes.append('joint'),
                        ofc=lambda x: self.cbNodeTypes.remove('joint'))
        cmds.checkBox(l='NurbsCurve', v=False,
                        onc=lambda x: self.cbNodeTypes.append('nurbsCurve'),
                        ofc=lambda x: self.cbNodeTypes.remove('nurbsCurve'))
        cmds.checkBox(l='OrientConstraint', v=False,
                        onc=lambda x: self.cbNodeTypes.append('orientConstraint'),
                        ofc=lambda x: self.cbNodeTypes.remove('orientConstraint'))
        cmds.checkBox(l='PointConstraint', v=False,
                        onc=lambda x: self.cbNodeTypes.append('pointConstraint'),
                        ofc=lambda x: self.cbNodeTypes.remove('pointConstraint'))
        cmds.checkBox(l='ParentConstraint', v=False,
                        onc=lambda x: self.cbNodeTypes.append('parentConstraint'),
                        ofc=lambda x: self.cbNodeTypes.remove('parentConstraint'))
        cmds.checkBox(l='ikHandle', v=False,
                        onc=lambda x: self.cbNodeTypes.append('ikHandle'),
                        ofc=lambda x: self.cbNodeTypes.remove('ikHandle'))
        cmds.checkBox(l='Transforms', v=False,
                        onc=lambda x: self.cbNodeTypes.append('transform'),
                        ofc=lambda x: self.cbNodeTypes.remove('transform'))
        cmds.setParent('..')

        cmds.separator(h=20, st='in')
        self.uiSpecificNodeTypes = cmds.textFieldGrp(ann='Specific NodeTypes to look for - separated by ,',
                                            label='Specific NodeTypes', cw=[(1, 120)], text="")
        self.uiSpecificAttrs = cmds.textFieldGrp(ann='Search for specific Attributes on nodes, list separated by ","',
                                            label='Search Attributes', cw=[(1, 120)], text="")
        self.uiSpecificPattern = cmds.textFieldGrp(label='Search Name Pattern', cw=[(1, 120)], text="",
                                            ann='Search for specific nodeName Patterns, list separated by "," - Note this is a Python.regularExpression - ^ clamps to the start, $ clamps to the end')
        cmds.separator(h=20, st='in')
        cmds.rowColumnLayout(numberOfColumns=2, columnWidth=[(1, 130), (2, 230)], columnSpacing=[(1, 10)])
       
        self.uiCbFromSelected = cmds.checkBox(ann='Process Selected Hierarchies or all Scene Nodes',
                                            label='From Selected', al='left', v=True)
        self.uiCbKwsTransOnly = cmds.checkBox(ann='Clamp the filter to only return the Transform Nodes, by-passes any shapes or nodeTypes with Transforms as parents',
                        label='Return Transforms were applicable', al='left',
                        v=self._filterNode.settings.transformClamp)
        cmds.separator(h=5, style='none')
        cmds.separator(h=5, style='none')
        self.uiCbKwsIncRoots = cmds.checkBox(ann='Include the originalRoots in the selection',
                        label='Include Roots', al='left',
                        v=self._filterNode.settings.incRoots)
        cmds.setParent('..')
        cmds.separator(h=10, style='none')
        cmds.button(label='Intersection Search - All Above Fields', bgc=r9Setup.red9ButtonBGC(1),
                     command=lambda *args: (self.__uiCall('intersection')))
        cmds.separator(h=20, st='in')
        cmds.button(label='Simple Hierarchy', bgc=r9Setup.red9ButtonBGC(2),
                     command=lambda *args: (self.__uiCall('FullHierarchy')))
        cmds.setParent(self.MainLayout)
        cmds.separator(h=15, style='none')
        cmds.iconTextButton(style='iconOnly', bgc=(0.7, 0, 0), image1='Rocket9_buttonStrap2.bmp',
                             c=lambda *args: (r9Setup.red9ContactInfo()), h=22, w=200)
        cmds.showWindow(window)
        cmds.window(self.win, e=True, widthHeight=(400, 380))
        
        
    def __uiCall(self, mode):
        if mode == 'intersection':
            # Fill Main Settings Object filters =============
            
            #we use the reset on the filterSettings object for consistency across all calls
            self._filterNode.settings.resetFilters()
            
            #hierarchy flag
            self._filterNode.settings.incRoots=\
                        cmds.checkBox(self.uiCbKwsIncRoots, q=True, v=True)
            
            #transform flag
            self._filterNode.settings.transformClamp=\
                        cmds.checkBox(self.uiCbKwsTransOnly, q=True, v=True)
            
            #nodeType filter
            if cmds.textFieldGrp(self.uiSpecificNodeTypes, q=True, text=True):
                self._filterNode.settings.nodeTypes=\
                        cmds.textFieldGrp(self.uiSpecificNodeTypes, q=True, text=True).split(',')
            self._filterNode.settings.nodeTypes.extend(self.cbNodeTypes)
            #attribute filter
            if cmds.textFieldGrp(self.uiSpecificAttrs, q=True, text=True):
                self._filterNode.settings.searchAttrs=\
                        cmds.textFieldGrp(self.uiSpecificAttrs, q=True, text=True).split(',')
            #nodeName filter
            if cmds.textFieldGrp(self.uiSpecificPattern, q=True, text=True):
                self._filterNode.settings.searchPattern=\
                        cmds.textFieldGrp(self.uiSpecificPattern, q=True, text=True).split(',')
            
            #setup the root / processing mode
            if cmds.checkBox(self.uiCbFromSelected, q=True, v=True):
                self._filterNode.rootNodes = cmds.ls(sl=True, l=True)
                if not self._filterNode.rootNodes:
                    raise StandardError('No Root Nodes Given for Filtering')
            else:
                self._filterNode.rootNodes=None
                self._filterNode.processMode='Scene'
        
            #Main Call
            nodes = self._filterNode.ProcessFilter()
  
        elif mode == 'FullHierarchy':
            self._filterNode.rootNodes=cmds.ls(sl=True, l=True)
            if not self._filterNode.rootNodes:
                raise StandardError('No Root Objects selected to process')
            nodes = self._filterNode.lsHierarchy(self._filterNode.settings.incRoots)
        
        log.info('RootNodes : %s', self._filterNode.rootNodes)
        log.info('ProcessMode : %s', self._filterNode.processMode)
        log.info('Search Returned %i nodes' % len(nodes))
        if(nodes):
            cmds.select(nodes)
            
        
        
class FilterNode(object):
    '''
    FilterNode is a class for managing, searching and filtering nodes with the scene.
    If the arg roots[] is given then the code filters the hierarchy's of these roots.
    If roots is not given then the functions will search globally at a scene level.
    
    Note that the main call, ProcessFilter() is only part of this class, there are 
    many other specific filtering functions for finding nodes in your Maya scene.
    
    This is a crucial class and used extensively in Red9 where ever hierarchies
    are in need of filtering. Used in conjunction with a FilterNode_Settings object 
    which,if not given, gets bound to self.settings. 
    
    >>> flt = FilterNode(rootNode)
    >>> flt.settings.nodeTypes=['nurbsCurve']
    >>> filt.settings.searchPattern=['Ctrl']
    >>> filt.ProcessFilter()
    
    The above makes a filterNode class, we pass in our hierarchies rootNode (string), 
    then set the internal settings to filter the hierarchy for all child nurbsCurves 
    who's name includes 'Ctrl'. Finally the ProcessFilter runs the main call.
    '''
    def __init__(self, roots=None, filterSettings=None):
        '''
        :param roots: Given root nodes in the Maya scene to search from.
            If a root is NOT given then the filter codes default to scanning all scene nodes.
        :param filterSettings: This expects a FilterNode_Settings Object to be passed in. This
            in turn holds all the filtering parameters used by the main lsIntersector call
            all other calls use given params so can be called directly.
        '''
        # make sure we have a settings object
        if filterSettings:
            if issubclass(type(filterSettings), FilterNode_Settings):
                self.settings=filterSettings
            else:
                raise StandardError('filterSettings param requires an r9Core.FilterNode_Settings object')
        else:
            self.settings=FilterNode_Settings()
        
        self._processMode='Scene'   # Global processing mode - 'Selected' or 'Scene'
        self._rootNodes = []        # Main Roots used for all Hierarchy Filtering
         
        #Return Data
        self.hierarchy=[]        # Data from the lsHierarchy call
        self.foundNodeTypes=[]   # Matched Node list from lsSearchNodeTypes
        self.foundAttributes=[]  # MatchAttribute list from lsSearchAttributes
        self.foundPattern=[]     # Matched NodeName pattern list from lsSearchNamePattern
        self.intersectionData=[]
        self.characterSetMembers=[]  # Character Set member list from lsCharacterMembers
        
        #root objects to filter NOTE: This also switches Processing Mode to suit
        if roots:
            self.rootNodes = roots
        else:
            self.processMode='Scene'
          


    # Properties Block
    #---------------------------------------------------------------------------------
    
    # Python2.5 compatible set/get property code for Maya2009
    
    def __get_rootNodes(self):
        if self._rootNodes:
            return self._rootNodes

    def __set_rootNodes(self, nodes):
        if nodes:
            if not isinstance(nodes, list):
                self._rootNodes=[nodes]
            else:
                self._rootNodes=nodes
            self.processMode='Selected'
        else:
            self.processMode='Scene'
            self._rootNodes=None
            #raise StandardError('no nodes Given')
              
    rootNodes = property(__get_rootNodes, __set_rootNodes)
    

    def __get_processMode(self):
            return self._processMode

    def __set_processMode(self, mode):
        if mode=='Selected':
            self._processMode=mode
            log.debug('Switching to SELECTED ROOTNODE HIERARCHY Processing Mode')
        elif mode=='Scene':
            self._processMode=mode
            log.debug('Switching to SCENE or GIVEN NODE Processing Mode')
            
    processMode = property(__get_processMode, __set_processMode)

    @staticmethod
    def knownShapes():
        return ["baseLattice", "camera", "clusterHandle", "deformBend", "deformFlare", "deformSine", \
        "deformSquash", "deformTwist", "deformWave", "angleDimension", "annotationShape", \
        "distanceDimShape", "arcLengthDimension", "paramDimension", "dynHolder", "flexorShape", \
        "clusterFlexo1rShape", "follicle1", "geoConnectable", "nurbsCurve", "lattice", \
        "fluidShape", "fluidTexture2D", "fluidTexture3D", "heightField", "mesh", "nurbsSurface", \
        "subdiv", "particle", "directedDisc", "environmentFog", "implicitBox", "renderBox", \
        "implicitCone", "renderCone", "implicitSphere", "renderSphere", "locator", \
        "dropoffLocator", "hikFloorContactMarker", "positionMarker", "orientationMarker", \
        "sketchPlane", "renderRect", "snapshotShape", "hairConstraint", "hairSystem", \
        "ambientLight", "areaLight", "directionalLight", "pointLight", "volumeLight", \
        "spotLight", "lineModifier", "pfxGeometry", "pfxHair", "pfxToon", "stroke", \
        "polyToolFeedbackShape", "rigidBody", "softModHandle", "spring"]
        

    # Hierarchy Block
    #---------------------------------------------------------------------------------
    
    def getObjectSetMembers(self, objSet):
        '''
        return objectSet members in long form
        '''
        return cmds.ls(cmds.sets(objSet, q=True, nodesOnly=True), l=True, type='transform') or []
        
    def lsHierarchy(self, incRoots=False, transformClamp=False):
        
        '''
        Simple wrapper of the listRelatives, BUT with the option
        to include the rootNodes and select the results

        Also if a single rootNode is passed, and it's of type 'character'
        then the code will return the characterMembers instead
        :param incRoots: include the given rootNodes in the filter
        TODO: objectSet modifications need testing!!!!!
        '''

        self.hierarchy=[]
        if self.processMode=='Selected':
            #check if we're dealing with a characterSet, if so return all its members
            for node in self.rootNodes:
                if cmds.nodeType(node)=='character':
                    self.hierarchy.extend(self.lsCharacterMembers())
                elif cmds.nodeType(node)=='objectSet':
                    #print 'objectSets - here'
                    self.hierarchy.extend(self.getObjectSetMembers(node))
                    childSets=cmds.listConnections(node, type='objectSet', s=True, d=False)  # need a walk here??
                    if childSets:
                        #print 'childSet : ', childSets
                        for childSet in childSets:
                            self.hierarchy.extend(self.getObjectSetMembers(childSet))
                else:
                    if incRoots:
                        self.hierarchy.append(node)
                    if not transformClamp:
                        self.hierarchy.extend(cmds.listRelatives(node, ad=True, f=True))
                    else:
                        #Still not sure this is the right place for the transform clamp
                        self.hierarchy.extend(cmds.listRelatives(node, ad=True, f=True,
                                                                 type='transform'))
            return self.hierarchy
        else:
            raise StandardError('rootNodes not given to class - processing at SceneLevel Only - lsHierarchy is therefore invalid')
    
    

    # Node Management Block
    #---------------------------------------------------------------------------------
    
    #@r9General.Timer
    def lsSearchNodeTypes(self, nodeTypes, nodes=None, incRoots=True, transformClamp=False):
        '''
        Main filter function wraps the cmds.listRelatives but replicates
        the mel listTransforms function in that it's capable of just returning
        the transform nodes of the given nodeTypes
        for example, when filtered for meshes, we might not want the shape node
        This now has complex handling for dealing with CharcterSets and SelectionSets
        
        :param nodeTypes: Maya NodeTypes passed into the listRelatives wrapper
        :param nodes: optional - allows you to pass in a list to process if required
        :param incRoots: Include the given root nodes in the search, default=True
            Valid only if the Class is in 'Selected' processMode only.
        :param transformClamp: Clamp the return to the Transform nodes. Ie, mesh normally
            would return the shape node, this clamps the return to it's Transform node, default=False

        :return: a list of nodes who type match the given search list
        '''
      
        self.foundNodeTypes = []
        typeMatched=[]

        log.debug('lsSearchNodeTypes : params : nodeTypes=%s, nodes=%s, incRoots=%i, transformClamp=%i'\
               % (nodeTypes, nodes, incRoots, transformClamp))
      
        if not isinstance(nodeTypes, list):
            nodeTypes = [nodeTypes]
        
        if self.processMode=='Selected' and len(self.rootNodes)==1:
            #PreProcess Set selections and add all members to the test
            #TO DO: have this process multiple selected Sets
            if cmds.nodeType(self.rootNodes[0])=='character':
                nodes = self.lsCharacterMembers()
                log.debug('adding CharacterSetMembers to nodes for processing : %s', nodes)
            elif cmds.nodeType(self.rootNodes[0])=='objectSet':
                nodes=self.lsHierarchy(self.rootNodes[0])
                #nodes=cmds.sets(self.rootNodes[0],q=True,nodesOnly=True)
                log.debug('adding SelectionSetMember to nodes for processing : %s', nodes)
       
        if nodes:
            #This is going to run through the given objects and check if they of the given nodeType
            #However, this also will check if we're searching for given shapeNodeTypes and if so
            #question any transforms for child nodes of the correct shapeType
            shapeTypes=list(set(nodeTypes).intersection(set(self.knownShapes())))
            if not shapeTypes:
                typeMatched = [node for node in nodes if cmds.nodeType(node) in nodeTypes]
            else:
                for node in nodes:
                    if cmds.nodeType(node) in nodeTypes:
                        typeMatched.append(node)
                    else:
                        if 'transform' in cmds.nodeType(node, i=True):
                            shapeMatched=cmds.listRelatives(node, type=shapeTypes, f=True)
                            if shapeMatched:
                                typeMatched.extend(shapeMatched)
        else:
            #No Nodes passed in, do straight listRelatives Calls
            try:
                if self.processMode=='Scene':
                    nodes = cmds.ls(type=nodeTypes, r=True, l=True)
                    if nodes:
                        typeMatched=nodes  # ensures we're always dealing with a list and not a null object
                elif self.processMode=='Selected':
                    nodes = cmds.listRelatives(self.rootNodes, type=nodeTypes, ad=True, f=True)
                    if nodes:
                        typeMatched=nodes  # ensures we're always dealing with a list and not a null object
                        
                    #Specific handler for blendShapes as these really need to be dealt with, and passed
                    #in the animation functions but don't show under a standard hierarchy search
                    if 'blendShape' in nodeTypes:
                        meshes=cmds.listRelatives(self.rootNodes, type='mesh', ad=True, f=True)
                        if meshes:
                            log.info('processing meshes for blendShapes')
                            for mesh in meshes:
                                blendShapes=[node for node in cmds.listHistory(mesh) if cmds.nodeType(node)=='blendShape']
                                if blendShapes:
                                    typeMatched.extend(blendShapes)
            except StandardError, error:
                log.debug(error)
                log.warning('UnknownDataType Given in sublist : %s', nodeTypes)

        if typeMatched:
            if not transformClamp:
                self.foundNodeTypes=typeMatched
            else:
                for node in typeMatched:
                    #Check if the nodeType is inherited/subclass of 'shape', if so, return
                    #it's parent transform node. Note: if it is a shape node then we INSERT
                    #it at the front of the list, rather than appending to the end.
                    #This is due to the way Maya returns data from the listRelatives cmd
                    if 'shape' in cmds.nodeType(node, i=True):
                        parentTransform = cmds.listRelatives(node, f=True, p=True)[0]
                        if parentTransform not in self.foundNodeTypes:
                            self.foundNodeTypes.insert(0, parentTransform)
                    else:
                        self.foundNodeTypes.append(node)
            
            #test if the roots match the searchTypes if so add them to the end
            if self.processMode=='Selected':
                if incRoots:
                    [self.foundNodeTypes.append(node) for node in self.rootNodes if cmds.nodeType(node) in nodeTypes]
                    log.debug('RootNode Matched by incRoots : %s', self.foundNodeTypes)
                else:
                    try:
                        for node in self.rootNodes:
                            self.foundNodeTypes.remove(node)
                    except:
                        pass
        else:
            log.info('lsSearchNodeTypes matched no nodes')
            
        log.debug('NodeTypes Found: %s', self.foundNodeTypes)
        return self.foundNodeTypes
    
    
    # Easy wrappers for .completion if an instance is taken
    #---------------------------------------------------------------------------------
    
    def lsMeshes(self):
        '''
        Filter for Meshes : from a start node find all mesh nodes in the hierarchy
        '''
        return self.lsSearchNodeTypes('mesh')
    def lsTransforms(self):
        '''
        Filter for Transforms : from a start node find all transform nodes in the hierarchy
        '''
        return self.lsSearchNodeTypes('transform')
    def lsJoints(self):
        '''
        Filter for Joints : from a start node find all Joints nodes in the hierarchy
        '''
        return self.lsSearchNodeTypes('joint')
    def lsLocators(self):
        '''
        Filter for Locators : from a start node find all Locators nodes in the hierarchy
        '''
        return self.lsSearchNodeTypes('locator')
    def lsIkData(self):
        '''
        Filter for IKData : from a start node find all ikHandle & ikEffector nodes in the hierarchy
        '''
        return self.lsSearchNodeTypes(['ikHandle', 'ikEffector'])
    def lsNurbsCurve(self):
        '''
        Filter for NurbsCurve : from a start node find all NurbsCurve nodes in the hierarchy
        '''
        return self.lsSearchNodeTypes('nurbsCurve')
    def lsConstraintsAll(self):
        '''
        Filter for All Constraint Nodes : from a start node find all Constraint nodes in the hierarchy
        '''
        return self.lsSearchNodeTypes(['orientConstraint', 'pointConstraint', 'parentConstraint'])
    def lsOrientConstraint(self):
        '''
        Filter for OrientConstraint : from a start node find all OrientConstraint nodes in the hierarchy
        '''
        return self.lsSearchNodeTypes('orientConstraint')
    def lsPointConstraint(self):
        '''
        Filter for PointConstraint : from a start node find all PointConstraint nodes in the hierarchy
        '''
        return self.lsSearchNodeTypes('pointConstraint')
    def lsParentConstraint(self):
        '''
        Filter for ParentConstraint : from a start node find all ParentConstraint nodes in the hierarchy
        '''
        return self.lsSearchNodeTypes('parentConstraint')
      
    @staticmethod
    @r9General.Timer
    def lsAnimCurves(nodes=None, safe=False):
        '''
        Search for animationCurves. If no nodes are passed in to process then this
        is a simple one liner, BUT if you pass in a selection of nodes to process
        then it's a lot harder. This code has to traverse the history and connection
        lists to find any animCurves that are in the nodes graph. This passes over
        character sets and animLayers to find all animCurve data.
        Note that this has no filter for excluding curves of type
        eg: setDrivens etc will need post filtering from the returns in many cases
        
        :param nodes: optional given node list, return animData in the nodes history
        :param safe: optional 'bool', only return animCurves which are safe to modify, this
                     will strip out SetDrivens, Clips curves etc..
        '''
        animCurves=[]
        treeDepth=2
        if not nodes:
            animCurves=cmds.ls(type='animCurve', r=True)
        else:
            try:
                #fucking AnimLayers!! if present then we up the depth of the history search
                #in-order to walk over the animBlendNodes to the actual animCurves.
                if r9Anim.getAnimLayersFromGivenNodes(nodes):
                    treeDepth=3
                    log.debug('AnimLayers found, increasing search depth')
                
                    #Deal with curves linked to character sets or animation layer
                    animCurves = [curve for curve in cmds.listHistory(nodes, pdo=True, lf=False, lv=treeDepth) \
                                               if cmds.nodeType(curve, i=True)[0] == 'animCurve']
                else:
                    # animCurves=cmds.listConnections(nodes,s=True,d=False,type='animCurve')
                    animCurves = [curve for curve in cmds.listHistory(nodes, pdo=True, lf=False, lv=treeDepth) \
                                               if cmds.nodeType(curve, i=True)[0] == 'animCurve']
            except:
                pass
        if not animCurves:
            return []
        if not safe:
            return list(set(animCurves))
        else:
            safeCurves=list(animCurves)
            for animCurve in animCurves:
                #ignore referenced animCurves
                if cmds.referenceQuery(animCurve, inr=True):
                    safeCurves.remove(animCurve)
                    continue
                #ignore setDrivens : animCurve have input connections
                if cmds.listConnections(animCurve, s=True, d=False):
                    safeCurves.remove(animCurve)
                    continue
                #ignore animClip curve data : animCurve is part of a TraxClip
                if cmds.nodeType(cmds.listConnections(animCurve))=='clipLibrary':
                    safeCurves.remove(animCurve)
                    continue
                #ignore curve if FUCKING animlayer it's a member of is locked!
                if cmds.getAttr("%s.ktv" % animCurve, l=True):
                    safeCurves.remove(animCurve)
                    continue
                
                #if curve.keyTimeValue.isLocked(): return False
            return safeCurves
                
            
            
    # Attribute Management Block
    #---------------------------------------------------------------------------------

    #@r9General.Timer
    def lsSearchAttributes(self, searchAttrs, nodes=None, incRoots=True, returnValues=False):
        '''
        Search for nodes that have a given attr or any attrs from a given list[]
        
        :param searchAttrs: list or string of attributes to search for on all child nodes
            NOTE: new operators 'NOT:' and '='
        :param nodes: optional - allows you to pass in a list to process if required
        :param returnValues: If found return the Value of the Attrs
            along with the node - switches return type to tuple. default=False
        :param incRoots: Include the given root nodes in the search, default=True
            Valid only if the Class is in 'Selected' processMode only.
         
        :rtype: list[] or dict{} of nodes whos attributes include any of the given attrs[]
        :return: Nodes that have the search attr/attrs. If returnValue is given as a
            keyword then it will return a dict in the form {node,attrValue}
        
        .. note::
            If the searchAttrs has an entry in the form NOT:searchAttr then this will be forcibly
            excluded from the filter. Also you can now do 'myAttr=2.33' to only pass if the attr is equal
            similarly 'NOT:myAttr=2.33' will exclude if the value is equal
            see the ..\Red9\tests\Red9_CoreUtilTests.py for live unittest examples
        
        TODO: current Implementation DOES NOT allow multiple attr tests as only 1 val per key 
            in the excludeAttrs and includeAttrs is currently supported!!!!!!
        '''
        
        self.foundAttributes = []
        attrDict = {}

        log.debug('lsSearchAttributes : params : searchAttrs=%s, nodes=%s, incRoots=%i, returnValues=%i'\
               % (searchAttrs, nodes, incRoots, returnValues))
      
        #ensure we're passing a list
        if not isinstance(searchAttrs, list):
            searchAttrs=[searchAttrs]
        
        #Process and split the input list into 2 dicts
        includeAttrs={}
        excludeAttrs={}
        for pattern in searchAttrs:
            val = [None, None]  # why?? so that a value of False or 0 is still a value and not ignored!
            pattern = pattern.replace(" ", "")  # strip whiteSpaces
            attr = pattern
            if '=' in pattern:
                # print 'pattern has ='
                val = [True, decodeString(pattern.split('=')[-1])]
                attr = pattern.split('=')[0]
            if 'NOT:' in pattern:
                # print 'pattern NOT ='
                excludeAttrs[(attr.split('NOT:')[-1])] = val
            else:
                includeAttrs[attr] = val
        log.debug('includes : %s' % includeAttrs.items())
        log.debug('excludes : %s' % excludeAttrs.items())
                 
        #Node block
        if not nodes:
            if self.processMode=='Scene':
                nodes = cmds.ls(dep=True, l=True)
            else:
                nodes = self.lsHierarchy(incRoots=incRoots)
            if not nodes:
                raise StandardError('No nodes found to process')
               
        #Search block
        for node in nodes:
            if includeAttrs:
                #we have attrs that we have to validate against so add=False is default
                add=False
            else:
                #we only have excluders so by default all nodes are added unless excluded
                add=True
                
            #Main test block, does the node get through the filter?
            for attr, val in includeAttrs.items():  # INCLUDE TESTS
                if cmds.attributeQuery(attr, exists=True, node=node):
                    if val[0]:  # value test
                        if not type(val[1]) == float:
                            if cmds.getAttr('%s.%s' % (node, attr)) == val[1]:
                                add = True
                                log.debug('attr %s : value %s == %s : node %s > ADD = True' % \
                                    (attr, val[1], cmds.getAttr('%s.%s' % (node, attr)), node))
                            else:
                                add = False
                                log.debug('attr %s : value %s != %s : node %s > ADD = False' % \
                                    (attr, val[1], cmds.getAttr('%s.%s' % (node, attr)), node))
                        else:
                            if floatIsEqual(cmds.getAttr('%s.%s' % (node, attr)), val[1]):
                                add = True
                                log.debug('attr %s : Float value %f == %f : node %s > ADD = True' % \
                                    (attr, val[1], cmds.getAttr('%s.%s' % (node, attr)), node))
                            else:
                                add = False
                                log.debug('attr %s : Float value %f != %f : node %s > ADD = False' % \
                                    (attr, val[1], cmds.getAttr('%s.%s' % (node, attr)), node))
                    else:
                        add=True
                        log.debug('attr %s : node %s > ADD = True' % (attr, node))
                    if not add:
                        log.debug('attr Include : Value Mismatch found : <BREAKOUT>')
                        break
                    
            for attr, val in excludeAttrs.items():  # EXCLUDE TESTS ('NOT:' operator)
                if cmds.attributeQuery(attr, exists=True, node=node):
                    if val[0]:  # value Test
                        if not type(val[1]) == float:
                            if cmds.getAttr('%s.%s' % (node, attr)) == val[1]:
                                add = False
                                log.debug('NOT: attr %s : Float value %s == %s : node %s > ADD = False' % \
                                    (attr, val[1], cmds.getAttr('%s.%s' % (node, attr)), node))
                        else:
                            if floatIsEqual(cmds.getAttr('%s.%s' % (node, attr)), val[1]):
                                add = False
                                log.debug('NOT: attr %s : Float value %f == %f : node %s > ADD = False' % \
                                    (attr, val[1], cmds.getAttr('%s.%s' % (node, attr)), node))
                    else:
                        add = False
                        log.debug('NOT: attr %s : node %s > ADD = False' % (attr, node))
                    log.debug('NOT: attr Exclude : found : <BREAKOUT>')
                    break
              
            #Test Complete, ADD the node to the return list
            if add:
                if not returnValues:
                    if node not in self.foundAttributes:
                        self.foundAttributes.append(node)
                else:
                    try:
                        #WILL FAIL ON MESSAGE LINKS AS THEY HAVE NO VALUE
                        attrDict[node] = cmds.getAttr('%s.%s' % (node, attr))
                    except:
                        attrDict[node] = None
                        log.debug('Some Attribute Types such as Message attrs have no value')
                        
        if returnValues:
            return attrDict
        else:
            return self.foundAttributes
        

    # Name Management Block
    #---------------------------------------------------------------------------------
    
    #@r9General.Timer
    def lsSearchNamePattern(self, searchPattern, nodes=None, incRoots=True):
        '''
        Search for nodes who's name match the given search patterns
        
        :param searchPattern: string/list patterns to match node names against (includes a 'NOT:' operator)
        :param nodes: optional - allows you to pass in a list to process if required
        :param incRoots: Include the given root nodes in the search, default=True
            Valid only if the Class is in 'Selected' processMode only.
            
        .. note:: 
            If the searchPattern has an entry in the form NOT:searchtext then this will be forcibly
            excluded from the filter. ie, My_L_Foot_Ctrl will be excluded with the following pattern
            ['Ctrl','NOT:My'] where Ctrl finds it, but the 'NOT:My' tells the filter to skip it if found
        '''
        self.foundPattern = []
        include=[]
        exclude=[]
        if not isinstance(searchPattern, list):
            searchPattern=[searchPattern]
        
        #Build the Regex funcs
        for pattern in searchPattern:
            pattern = pattern.replace(" ", "")  # strip whiteSpaces
            if 'NOT:' in pattern:
                exclude.append(pattern.split(':')[-1])
            else:
                include.append(pattern)
        
        includePattern='|'.join(n for n in include)
        incRegex=re.compile('('+includePattern+')')  # convert into a regularExpression
        if exclude:
            excludePattern='|'.join(n for n in exclude)
            excRegex=re.compile('('+excludePattern+')')  # convert into a regularExpression

        #Node block
        log.debug('lsSearchNamePattern : params : searchPattern=%s, nodes=%s, incRoots=%i'\
               % (searchPattern, nodes, incRoots))
        if not nodes:
            if self.processMode=='Scene':
                nodes = cmds.ls(dep=True, l=True)
            else:
                nodes = self.lsHierarchy(incRoots=incRoots)
            if not nodes:
                raise StandardError('No nodes found to process')
            
        #Actual Search calls
        if exclude:
            log.debug('Exclude SearchPattern found : %s' % exclude)
            for node in nodes:
                if incRegex.search(nodeNameStrip(node)) and not excRegex.search(nodeNameStrip(node)):
                    self.foundPattern.append(node)
        else:
            self.foundPattern=[node for node in nodes if incRegex.search(nodeNameStrip(node))]
                   
        return self.foundPattern
    

    # Character Set Management Block
    #---------------------------------------------------------------------------------
    
    def lsCharacterSets(self):
        '''
        Get any characterSets from the given rootNode (single only). If rootNode[0]
        is of type 'character' then it will just return itself. If not will test
        all children of the root for links to characterSets and return those found.
        '''
        cSets=[]
        if self.processMode=='Selected':
            #If any of the rootNodes are characterSet then return those
            if [cSets.append(node) for node in self.rootNodes if cmds.nodeType(node) =='character']:
                for node in self.rootNodes:
                    #include subSets in this list
                    subSets=cmds.listConnections(node, type='character', s=True, d=False)
                    if subSets:
                        cSets.extend(subSets)
                return cSets
            else:
                #Test the full hierarchy for characterSet memberships
                hierarchy = self.lsHierarchy(incRoots=True)
                if not hierarchy:
                    raise StandardError('Roots have no children to process')
                for f in hierarchy:
                    linked=cmds.listConnections(f, type='character')
                    if linked:
                        [cSets.append(cSet) for cSet in linked if cSet not in cSets]
        else:
            raise StandardError('rootNodes not given to class - processing at SceneLevel Only')
        return cSets
    
    
    def lsCharacterMembers(self):
        '''
        From self.characterSets return all it's node members. If characterSets attr
        hasn't been set then it will invoke a test on the RootNode down through
        it's hierarchy to find all characterSet links. Not that this now processes
        subCharacterSets too
        
        ##### THIS NEEDS WORK TO RETURN THE MEMBERS IN THE CORRECT ORDER #####
        '''
        self.characterSetMembers = []
        cSets = self.lsCharacterSets()
        if cSets:
            for cset in cSets:
                log.debug('cSet : %s', cset)
                self.characterSetMembers.extend(cmds.character(cset, query=True, nodesOnly=True))
            # make sure the cSets are not part of the return
            [self.characterSetMembers.remove(cset) for cset in cSets if cset in self.characterSetMembers]
                    
            return cmds.ls(self.characterSetMembers, l=True)

    def lsMetaRigControllers(self, walk=True, incMain=True):
        '''
        very light wrapper to handle MetaData in the FilterSystems. This is hard coded
        to find CTRL markered attrs and give back the attached nodes
        :param walk: walk the found systems for subSystems and process those too
        :param incMain: Like the other filters we allow the given top
            node in the hierarchy to be removed from processing. In a MetaRig
            this is the CTRL_Main controller which should be Top World Space
        '''
        rigCtrls=[]
        metaNodes=[]
        
        #First find and connected MetaData nodes
        for root in self.rootNodes:
            meta=None
            if r9Meta.isMetaNode(root):
                meta=r9Meta.MetaClass(root)
            else:
                mnodes=r9Meta.getConnectedMetaNodes(root)
                if mnodes:
                    for mnode in mnodes:
                        if issubclass(type(mnode), r9Meta.MetaRig):
                            meta=mnode
                            break
                    if not meta:
                        meta=mnodes[0]
            if meta and meta not in metaNodes:
                metaNodes.append(meta)
                
        #Find all controllers hanging off these given metaSystems
        if metaNodes:
            log.debug('processing found MetaSystsem Nodes : %s' % ','.join([x.mNode for x in metaNodes]))
            for meta in metaNodes:
                ctrls=meta.getChildren(walk=walk)
                if ctrls and not incMain and meta.hasAttr(meta.rigGlobalCtrlAttr):
                    ctrl_main=meta.__getattribute__(meta.rigGlobalCtrlAttr)[0]
                    if ctrl_main in ctrls:
                        ctrls.remove(ctrl_main)
                rigCtrls.extend(ctrls)
        return rigCtrls
            

    # Main Search Call which uses the Settings Object
    #---------------------------------------------------------------------------------
    
    #@r9General.Timer
    def ProcessFilter(self):
            '''
            Uses intersection to allow you to process multiple search flags for
            more accurate filtering.
            Uses the FilterNode_Settings object for all args such that:
                
            :param settings.nodeTypes: nodetypes to search for on child nodes
            :param settings.searchAttrs: attribute to search for on child nodes
            :param settings.searchPattern: name pattern to match on child nodes
            :param settings.transformClamp: Clamp the return to the Transform nodes.
            :param settings.incRoots: Include the given root nodes in the search.
            
            :return: all nodes which match ALL the given keyword filter searches
            '''
            log.debug(self.settings.__dict__)
            self.intersectionData=[]
            
            #wrap the intersector call
            def addToIntersection(nodes):
                if nodes:
                    if self.intersectionData:
                        # NOTE : Whilst set.intersection may be a faster and better solution
                        # it doesn't retain the lists order, for some Hierarchy functions this
                        # is crucial so switching this over to looping through in order
                        self.intersectionData = [node for node in nodes if node in self.intersectionData]
                    else:
                        self.intersectionData = nodes
                else:
                    self.intersectionData = []
            
            #If FilterSettings have no effect then just return the rootNodes
            if not self.settings.filterIsActive:
                return self.rootNodes
            
            # Straight Hierarchy Filter ----------------------
            if self.settings.hierarchy:
                nodes = self.lsHierarchy(incRoots=self.settings.incRoots,
                                         transformClamp=self.settings.transformClamp)
                addToIntersection(nodes)
                if not nodes:
                    return []
            
            # MetaClass Filter ------------------------------
            if self.settings.metaRig:
                nodes = self.lsMetaRigControllers(incMain=self.settings.incRoots)
                addToIntersection(nodes)
                if not nodes:
                    return []
                
            # NodeTypes Filter -------------------------------
            if self.settings.nodeTypes:
                nodes = self.lsSearchNodeTypes(self.settings.nodeTypes,
                                               nodes=self.intersectionData,
                                               incRoots=self.settings.incRoots,
                                               transformClamp=self.settings.transformClamp)
                addToIntersection(nodes)
                if not nodes:
                    return []
               
            # Attribute Filter -------------------------------
            if self.settings.searchAttrs:
                nodes = self.lsSearchAttributes(self.settings.searchAttrs,
                                                nodes=self.intersectionData,
                                                incRoots=self.settings.incRoots)
                addToIntersection(nodes)
                if not nodes:
                    return []
                  
            # NodeName Filter --------------------------------
            if self.settings.searchPattern:
                nodes = self.lsSearchNamePattern(self.settings.searchPattern,
                                                 nodes=self.intersectionData,
                                                 incRoots=self.settings.incRoots)
                addToIntersection(nodes)
                if not nodes:
                    return []
                
            # use the prioritizeNodeList call to order the list based on a given set of priority's
            if self.settings.filterPriority:
                #note we reverse here as hierarchies are returned in reverse order
                #in Maya and the prioritize inserts at the beginning
                self.intersectionData.reverse()
                self.intersectionData=prioritizeNodeList(self.intersectionData, self.settings.filterPriority)
                self.intersectionData.reverse()
                #[log.debug('%i = %s' % (i, nodeNameStrip(n))) for i,n in enumerate(self.intersectionData)]
                  
            return self.intersectionData


#Node Matching -------------------------------------------------------------------------
            
def matchNodeLists(nodeListA, nodeListB, matchMethod='stripPrefix'):
    '''
    Matches 2 given NODE LISTS by node name via various methods.
    
    :param matchMethod: default 'stripPrefix' 
        *base*:  Match each element by exact name (shortName)
        such that Spine==Spine or REF1:Spine==REF2:Spine
        
        *stripPrefix*: Match each element by a relaxed naming convention
        allowing for prefixes such that RigX_Spine == Spine
    :return: matched pairs of tuples for processing [(a1,b2),[(a2,b2)]
    '''

    infoPrint = ""
    matchedData = []
    
    #take a copy of B as we modify the data here
    hierarchyB=list(nodeListB)
    
    for nodeA in nodeListA:
        strippedA = nodeNameStrip(nodeA)
        for nodeB in hierarchyB:
            #strip the path off for the compare
            #strippedA = nodeNameStrip(nodeA)
            strippedB = nodeNameStrip(nodeB)
            
            #BaseMatch is a direct compare ONLY
            if matchMethod == 'base':
                if strippedA.upper() == strippedB.upper():
                    infoPrint += '\nMatch Method : %s : %s == %s' % \
                            (matchMethod, nodeA.split('|')[-1], nodeB.split('|')[-1])
                    matchedData.append((nodeA, nodeB))
                    hierarchyB.remove(nodeB)
                    break
                
            #Compare allowing for prefixing which is stripped off
            elif matchMethod == 'stripPrefix':
                if strippedA.upper().endswith(strippedB.upper()) \
                    or strippedB.upper().endswith(strippedA.upper()):
                    infoPrint += '\nMatch Method : %s : %s == %s' % \
                            (matchMethod, nodeA.split('|')[-1], nodeB.split('|')[-1])
                    matchedData.append((nodeA, nodeB))
                    hierarchyB.remove(nodeB)
                    break
                
    log.debug('\nMatched Log : \n%s' % infoPrint)
    infoPrint = None
    return matchedData


def processMatchedNodes(nodes=None, filterSettings=None, toMany=False, matchMethod='stripPrefix'):
    '''
    HUGELY IMPORTANT CALL FOR ALL ANIMATION FUNCTIONS
    
    PreProcess the given 'nodes' and 'filterSettings'(optional)
    via a MatchedNodeInput OBJECT that has an attribute self.MatchedPairs
    We're going to use this throughout the code such that:
    nodeList.MatchedPairs = [(ObjA,ObjB),(ObjC,ObjD) .....]
    
    :param nodes: Given Nodes for processing
    :param filterSettings: as all other functions, this is the main hierarchy filter
    :param toMany: Return a MatchedPairs where the first node in each
        tuple is the first selected node, ie, used to cast data from the first
        node to all subsequent nodes [(ObjA,ObjB),(ObjA,ObjC),(ObjA,ObjD) ....
    :param matchMethod: method used in the name matchProcess
    :return: MatchNodeInputs class object
    '''
    #nodeList = None

    if nodes and issubclass(type(nodes), MatchedNodeInputs):
        log.debug('nodes are already of type MatchedNodeInputs')
        return nodes
    if not nodes:
        nodes = cmds.ls(sl=True, l=True)

    if filterSettings:
        log.debug('filterSettings Passed To MatchedNodeInputs : %s', filterSettings.__dict__)
    
    #make an instance of the MatchedNodeInputs object
    nodeList = MatchedNodeInputs(nodes, filterSettings=filterSettings, matchMethod=matchMethod)
    
    if not toMany:
        nodeList.processMatchedPairs()
    else:
        #to Many - used for some of the anim functions
        nodeList.MatchedPairs = [(nodes[0], node) for node in nodes]
        
    if not nodeList.MatchedPairs:
        raise StandardError('ProcessNodes returned no Nodes to process')
    
    return nodeList

    
class MatchedNodeInputs(object):
    '''
    Class to process and match input nodes for most of the Hierarchy/Anim
    functions that work on carefully managed matched pairs of nodes.
    
    :param nodes: root nodes to start the filtering process from
    :param matchMethod: Method of matching each nodePair based on nodeName
    :param filterSettings: This is a FilterSettings_Node object used to pass all 
        the filter types into the FilterNode code within. Internally the following 
        is true:
        
        | settings.nodeTypes: list[] - search nodes of type
        | settings.searchAttrs: list[] - search nodes with Attrs of name
        | settings.searchPattern: list[] - search for a given nodeName searchPattern
        | settings.hierarchy: bool - process all children from the roots
        | settings.incRoots: bool - include the original root nodes in the filter
        
    :return: list of matched pairs [(a1,b2),[(a2,b2)]   
            
    .. note:: 
        with all the search and hierarchy keywords OFF the code performs
        a Dumb zip, no matching and no Hierarchy filtering, just zip the given nodes
        into selected pairs obj[0]>obj[1], obj[2]>obj[3] etc
    '''
    
    def __init__(self, nodes=None, filterSettings=None, matchMethod='stripPrefix'):
           
        self.MatchedPairs=[]  # Main Result Tuple of Pairs
        
        self.matchMethod=matchMethod
        self.roots=nodes
        
        # make sure we have a settings object to process
        if filterSettings:
            if issubclass(type(filterSettings), FilterNode_Settings):
                self.settings=filterSettings
            else:
                raise StandardError('settings param requires an FilterNode_Settings object')
        else:
            self.settings=FilterNode_Settings()
            
    def processMatchedPairs(self):
        '''
        Filter selected roots for hierarchy matching using a FilterNode and it's
        settings object if one was passed in to the main class.
        This uses the ProcessFilter() method for powerful pre-filtering before
        passing the results into the matchNodeLists func.
        :rtype: tuple
        :return: a matched pair list of nodes
        '''
        if self.settings.filterIsActive():
            if not len(self.roots)==2:
                raise StandardError('Please select ONLY 2 base objects for hierarchy comparison')
           
            #take a single instance of a FilterNode and process both root hierarchies
            filterNode=FilterNode(filterSettings=self.settings)
            filterNode.rootNodes=self.roots[0]
            nodesA=filterNode.ProcessFilter()
            filterNode.rootNodes=self.roots[1]
            nodesB=filterNode.ProcessFilter()

            #Match the 2 nodeLists by nodeName and return the MatcherPairs list
            self.MatchedPairs=matchNodeLists(nodesA, nodesB, self.matchMethod)
             
        else:
            if not len(self.roots)>=2:
                raise StandardError('Please select 2 or more matching base objects')
            if len(self.roots)==2 and type(self.roots[0])==list and type(self.roots[1])==list:
                log.debug('<<2 lists passed in as roots - Assuming these are 2 hierarchies to process>>')
                self.MatchedPairs=matchNodeLists(self.roots[0], self.roots[1], self.matchMethod)
            else:
                #No matching, just take roots as selected and substring them with step
                #so that (roots[0],roots[1])(roots[2],roots[3])
                self.MatchedPairs=zip(self.roots[0::2], self.roots[1::2])
                for a, b in self.MatchedPairs:
                    log.debug('Blind Selection Matched  : %s == %s' % (a, b))
          
        return self.MatchedPairs


class LockChannels(object):
    
    '''
    Simple UI to manage the lock and key status of nodes
    '''
    def __init__(self):
        self.statusDict={}
        
    class UI(object):
        
        def __init__(self):
            self.attrs=set()
            self.hierarchy=False
            self.userDefined=False
            self.win = 'LockChannels'
            
        @classmethod
        def show(cls):
            cls()._showUI()
        
        def _showUI(self):
            if cmds.window(self.win, exists=True):
                cmds.deleteUI(self.win, window=True)
            window = cmds.window(self.win, title="LockChannels", s=False, widthHeight=(260, 410))
            cmds.menuBarLayout()
            cmds.menu(l="VimeoHelp")
            cmds.menuItem(l="Open Vimeo Help File", \
                          c="import Red9.core.Red9_General as r9General;r9General.os_OpenFile('https://vimeo.com/58664502')")
            cmds.menuItem(divider=True)
            cmds.menuItem(l="Contact Me", c=lambda *args: (r9Setup.red9ContactInfo()))
            cmds.columnLayout(adjustableColumn=True, columnAttach=('both', 5))
            cmds.separator(h=15, style='none')
            cmds.rowColumnLayout(ann='attrs', numberOfColumns=4,
                                 columnWidth=[(1, 50), (2, 50), (3, 50)])
           
            cmds.checkBox('tx', l='Tx', v=False,
                          onc=lambda x: self.__uicheckboxCallbacksAttr('on', "tx"),
                          ofc=lambda x: self.__uicheckboxCallbacksAttr('off', "tx"))
            cmds.checkBox('ty', l='Ty', v=False,
                          onc=lambda x: self.__uicheckboxCallbacksAttr('on', "ty"),
                          ofc=lambda x: self.__uicheckboxCallbacksAttr('off', "ty"))
            cmds.checkBox('tz', l='Tz', v=False,
                          onc=lambda x: self.__uicheckboxCallbacksAttr('on', "tz"),
                          ofc=lambda x: self.__uicheckboxCallbacksAttr('off', "tz"))
            cmds.checkBox('translates', l='Translates', v=False,
                          onc=lambda x: self.__uicheckboxCallbacksAttr('on', ["tx", "ty", "tz"]),
                          ofc=lambda x: self.__uicheckboxCallbacksAttr('off', ["tx", "ty", "tz"]))
            
            cmds.checkBox('rx', l='Rx', v=False,
                          onc=lambda x: self.__uicheckboxCallbacksAttr('on', "rx"),
                          ofc=lambda x: self.__uicheckboxCallbacksAttr('off', "rx"))
            cmds.checkBox('ry', l='Ry', v=False,
                          onc=lambda x: self.__uicheckboxCallbacksAttr('on', "ry"),
                          ofc=lambda x: self.__uicheckboxCallbacksAttr('off', "ry"))
            cmds.checkBox('rz', l='Rz', v=False,
                          onc=lambda x: self.__uicheckboxCallbacksAttr('on', "rz"),
                          ofc=lambda x: self.__uicheckboxCallbacksAttr('off', "rz"))
            cmds.checkBox('rotates', l='Rotates', v=False,
                          onc=lambda x: self.__uicheckboxCallbacksAttr('on', ["rx", "ry", "rz"]),
                          ofc=lambda x: self.__uicheckboxCallbacksAttr('off', ["rx", "ry", "rz"]))
           
            cmds.checkBox('sx', l='Sx', v=False,
                          onc=lambda x: self.__uicheckboxCallbacksAttr('on', "sx"),
                          ofc=lambda x: self.__uicheckboxCallbacksAttr('off', "sx"))
            cmds.checkBox('sy', l='Sy', v=False,
                          onc=lambda x: self.__uicheckboxCallbacksAttr('on', "sy"),
                          ofc=lambda x: self.__uicheckboxCallbacksAttr('off', "sy"))
            cmds.checkBox('sz', l='Sz', v=False,
                          onc=lambda x: self.__uicheckboxCallbacksAttr('on', "sz"),
                          ofc=lambda x: self.__uicheckboxCallbacksAttr('off', "sz"))
            cmds.checkBox('scales', l='Scales', v=False,
                          onc=lambda x: self.__uicheckboxCallbacksAttr('on', ["sx", "sy", "sz"]),
                          ofc=lambda x: self.__uicheckboxCallbacksAttr('off', ["sx", "sy", "sz"]))
            
            cmds.checkBox('v', l='Vis', v=False,
                          onc=lambda x: self.__uicheckboxCallbacksAttr('on', "v"),
                          ofc=lambda x: self.__uicheckboxCallbacksAttr('off', "v"))
            
            cmds.setParent('..')
            cmds.rowColumnLayout(ann='attrs', numberOfColumns=2,
                                 columnWidth=[(1, 150)])
            cmds.checkBox('userDefined', l='All User Defined Attrs', v=False,
                          ann='These are non-standard attributes added to the nodes. These are considered per node',
                          onc=lambda x: self.__setattr__('userDefined', True),
                          ofc=lambda x: self.__setattr__('userDefined', False))
            cmds.checkBox('ALL', l='ALL Attrs', v=False,
                          onc=lambda x: self.__uicheckboxCallbacksAttr('on', ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz", "v", \
                                                                            "userDefined", "translates", "rotates", "scales"]),
                          ofc=lambda x: self.__uicheckboxCallbacksAttr('off', ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz", "v", \
                                                                             "userDefined", "translates", "rotates", "scales"]))
            cmds.setParent('..')
            cmds.separator(h=20, style='in')
            cmds.checkBox('givenAttrs', l='Specific Attrs',
                          onc=lambda x: cmds.textField('uitf_givenAttrs', e=True, en=True),
                          ofc=lambda x: cmds.textField('uitf_givenAttrs', e=True, en=False))
            cmds.textField('uitf_givenAttrs', text='', en=False,
                           ann='list of specific attributes to lock, comma separated: note : RMB Menu')
            cmds.popupMenu()
            cmds.menuItem(label='Clear', command=partial(self.__uiTextFieldPopup, 'clear'))
            cmds.menuItem(label='Add ChnBox Selection', command=partial(self.__uiTextFieldPopup, 'add'))
      
            cmds.separator(h=20, style='in')
            cmds.checkBox('Hierarchy', l='Hierarchy', al='left', v=False, ann='Full Hierarchy',
                          onc=lambda x: self.__setattr__('hierarchy', True),
                          ofc=lambda x: self.__setattr__('hierarchy', False))
            cmds.rowColumnLayout(ann='attrs', numberOfColumns=2, columnWidth=[(1, 125), (2, 125)])
            cmds.button(label='Lock', bgc=r9Setup.red9ButtonBGC(1),
                         command=lambda *args: (self.__uiCall('lock')))
            cmds.button(label='unLock', bgc=r9Setup.red9ButtonBGC(2),
                         command=lambda *args: (self.__uiCall('unlock')))
            cmds.button(label='Hide', bgc=r9Setup.red9ButtonBGC(1),
                         command=lambda *args: (self.__uiCall('hide')))
            cmds.button(label='unHide', bgc=r9Setup.red9ButtonBGC(2),
                         command=lambda *args: (self.__uiCall('unhide')))
            cmds.separator(h=20, style='in')
            cmds.separator(h=20, style='in')
            self.__uibtStore = cmds.button(label='Store attrMap', bgc=r9Setup.red9ButtonBGC(1),
                         ann='This saves the current "lock,keyable,hidden" status of all attributes in the channelBox to an attrMap file',
                         command=lambda *args: (self.__uichannelMapFile('save')))
            self.__uibtLoad = cmds.button(label='Load from attrMap', bgc=r9Setup.red9ButtonBGC(1),
                         ann='This restores the "lock,keyable,hidden" status of all attributes from the attrMap file',
                         command=lambda *args: (self.__uichannelMapFile('load')))
            cmds.setParent('..')
            cmds.separator(h=10, style='none')
            
            
            cmds.checkBox('serializeToNode', l='Serialized attrMap to node',
                          ann='rather than saving the data to a file, serialize it to a given node so its stored internally in your systems',
                          cc=lambda x: self.__uiAttrMapModeSwitch())

            cmds.textFieldButtonGrp('uitfbg_serializeNode',
                                    bl='set',
                                    text='',
                                    en=False,
                                    ann='Node for serializing the attrMap directly onto',
                                    bc=lambda *args: cmds.textFieldButtonGrp('uitfbg_serializeNode', e=True, text=cmds.ls(sl=True)[0]),
                                    cw=[(1, 220), (2, 60)])
            cmds.separator(h=15, style='none')
            cmds.iconTextButton(style='iconOnly', bgc=(0.7, 0, 0), image1='Rocket9_buttonStrap2.bmp',
                                 c=lambda *args: (r9Setup.red9ContactInfo()), h=22, w=200)
      
            cmds.showWindow(window)
            
        def __uicheckboxCallbacksAttr(self, mode, attrs):
            if not isinstance(attrs, list):
                attrs=[attrs]
            for attr in attrs:
                if mode=='on':
                    try:
                        self.attrs.add(attr)
                        #manage the checkbox state in case the call was made
                        #from one of the list checkboxes.
                        cmds.checkBox(attr, edit=True, v=True)
                    except:
                        pass
                elif mode=='off':
                    try:
                        cmds.checkBox(attr, edit=True, v=False)
                        self.attrs.remove(attr)
                    except:
                        pass
        
        def __uiTextFieldPopup(self, mode, *args):
            '''
            add attributes to the TextField from those selected in the channelBox
            '''
            current = []
            if cmds.textField('uitf_givenAttrs', q=True, text=True):
                current = cmds.textField('uitf_givenAttrs', q=True, text=True).split(',')
            if mode == 'clear':
                current = cmds.textField('uitf_givenAttrs', e=True, text='')
            if mode == 'add':
                selectedCB = r9Anim.getChannelBoxSelection()
                if selectedCB:
                    for attr in selectedCB:
                        if attr not in current:
                            current.append(attr)
                cmds.textField('uitf_givenAttrs', e=True, text=','.join(current))
       
        def __uichannelMapFile(self, mode):
            '''
            Manage the load/save of attrMap files
            '''
            hierarchy=cmds.checkBox('Hierarchy', q=True, v=True)
            nodes=cmds.ls(sl=True, l=True)
            
            if hierarchy and not nodes:
                raise StandardError('No Root of hierarchy selected to Process')
            if hierarchy and nodes and r9Meta.isMetaNode(nodes[0]):
                raise StandardError('MetaData node can not be the Root for hierarchy processing')
            if not hierarchy and not nodes:
                raise StandardError('No nodes selected to Process')
            
            if not cmds.checkBox('serializeToNode', q=True, v=True):
                if mode=='load':
                    filePath=cmds.fileDialog2(fileFilter="attributeMap Files (*.attrMap *.attrMap);;", okc='Load')[0]
                    LockChannels().loadChannelMap(filepath=filePath, nodes=nodes, hierarchy=hierarchy)
                elif mode=='save':
                    filePath=cmds.fileDialog2(fileFilter="attributeMap Files (*.attrMap *.attrMap);;", okc='Save')[0]
                    LockChannels().saveChannelMap(filepath=filePath, nodes=nodes, hierarchy=hierarchy)
            else:
                serializerNode=cmds.textFieldButtonGrp('uitfbg_serializeNode', q=True, text=True)
                if not cmds.objExists(serializerNode):
                    raise StandardError('No VALID MayaNode given to save/load the attrMaps to/From')
                if mode=='load':
                    LockChannels().loadChannelMap(filepath=None, nodes=nodes, hierarchy=hierarchy, serializeNode=serializerNode)
                elif mode=='save':
                    LockChannels().saveChannelMap(filepath=None, nodes=nodes, hierarchy=hierarchy, serializeNode=serializerNode)
        
        def __uiAttrMapModeSwitch(self):
            if cmds.checkBox('serializeToNode', q=True, v=True):
                cmds.textFieldButtonGrp('uitfbg_serializeNode', e=True, en=True)
                cmds.button(self.__uibtStore, e=True, l='Save attrMap Internal')
                cmds.button(self.__uibtLoad, e=True, l='Load attrMap Internal')
            else:
                cmds.textFieldButtonGrp('uitfbg_serializeNode', e=True, en=False)
                cmds.button(self.__uibtStore, e=True, l='Store attrMap')
                cmds.button(self.__uibtLoad, e=True, l='Load attrMap')
                            
        def __uiCall(self, mode):
            if cmds.textField('uitf_givenAttrs', q=True, en=True):
                newAttrs = cmds.textField('uitf_givenAttrs', q=True, text=True)
                if newAttrs:
                    for a in newAttrs.split(','):
                        self.attrs.add(a)
                    #print self.attrs
            LockChannels.processState(cmds.ls(sl=True, l=True), self.attrs, mode, self.hierarchy, self.userDefined)
            
            
    # MapFile calls
    #-----------------------------------
    def __buildAttrStateDict(self, nodes):
        '''
        build the internal dict thats stored and used by the save/load calls
        '''
        self.statusDict={}
        for node in nodes:
            key=nodeNameStrip(node)
            self.statusDict[key]={}
            self.statusDict[key]['keyable']=cmds.listAttr(node, k=True, u=True)
            self.statusDict[key]['locked'] =cmds.listAttr(node, k=True, l=True)
            self.statusDict[key]['nonKeyable'] =cmds.listAttr(node, cb=True)
    
    def saveChannelMap(self, filepath=None, nodes=None, hierarchy=True, serializeNode=None):
        '''
        WE HAVE TO LOCK THE ATTRIBUTE!! why, 32k Maya string character Limits kick in and
        truncates the data unless the attr is locked out
        '''
        if not nodes:
            nodes = cmds.ls(sl=True, l=True)
        if hierarchy:
            # Filter the selection for children including the selected roots
            nodes = FilterNode(nodes).lsHierarchy(incRoots=True, transformClamp=True)

        self.__buildAttrStateDict(nodes)
        if filepath:
            ConfigObj = configobj.ConfigObj(indent_type='\t')
            ConfigObj['channelMap']=self.statusDict
            ConfigObj.filename = filepath
            ConfigObj.write()
        elif serializeNode:
            node=r9Meta.MetaClass(serializeNode)
            if not node.hasAttr('attrMap'):
                node.addAttr('attrMap', self.statusDict)
            else:
                node.attrSetLocked('attrMap', False)
                #cmds.setAttr('%s.attrMap' % serializeNode, l=False)
                node.attrMap=self.statusDict
            try:
                node.attrSetLocked('attrMap', True)
                #cmds.setAttr('%s.attrMap' % serializeNode, l=True)
            except StandardError, error:
                #referenced attrs, even though we've just added it, can't be locked!
                raise StandardError(error)
        log.info('<< AttrMap Processed >>')
        
    def loadChannelMap(self, filepath=None, nodes=None, hierarchy=True, serializeNode=None):
        '''
        From a given chnMap file restore the channelBox status for all attributes
        found that are in the map file. ie, keyable, hidden, locked
        
        .. note:: 
            Here we're dealing with 2 possible sets of data, either decoded by the
            ConfigObj decoder or a JSON deserializer and there's subtle differences in the dict
            thats returned hence the decodeString() calls
        TODO: Add progress bar?
        '''
        if not nodes:
            nodes = cmds.ls(sl=True, l=True)
        if hierarchy:
            # Filter the selection for children including the selected roots
            nodes = FilterNode(nodes).lsHierarchy(incRoots=True, transformClamp=True)
        if filepath:
            self.statusDict=configobj.ConfigObj(filepath)['channelMap']
        elif serializeNode:
            serializeNode=r9Meta.MetaClass(serializeNode)
            if serializeNode.hasAttr('attrMap'):
                self.statusDict=serializeNode.attrMap
                #print type(self.statusDict), self.statusDict
            else:
                raise StandardError('attrMap not found on given node')
            
        for node in nodes:
            key=nodeNameStrip(node)
            if key in self.statusDict:
                
                #managed node so first hide and lock all current CBattrs
                currentAttrs=r9Anim.getChannelBoxAttrs(node, asDict=False)
                for attr in currentAttrs:
                    try:
                        cmds.setAttr('%s.%s' %(node, attr), keyable=False, lock=True, channelBox=False)
                    except:
                        log.info('%s : failed to set initial state' % attr)
                        
                #NOTE: this looks a slow way of processing but an Attr will
                #only ever appear in one of these lists so not really an overhead
                if not decodeString(self.statusDict[key]['keyable'])==None:
                    for attr in self.statusDict[key]['keyable']:
                        try:
                            #print 'keyable',attr
                            cmds.setAttr('%s.%s' %(node, attr), k=True, l=False)
                        except:
                            log.debug('%s : failed to set keyable attr status' % attr)
                if not decodeString(self.statusDict[key]['locked'])==None:
                    for attr in self.statusDict[key]['locked']:
                        try:
                            #print 'locked',attr
                            cmds.setAttr('%s.%s' %(node, attr), k=True, l=True)
                        except:
                            log.debug('%s : failed to set locked attr status' % attr)
                if not decodeString(self.statusDict[key]['nonKeyable'])==None:
                    for attr in self.statusDict[key]['nonKeyable']:
                        try:
                            #print 'nonKeyable',attr
                            cmds.setAttr('%s.%s' %(node, attr), cb=True)
                            cmds.setAttr('%s.%s' %(node, attr), l=False, k=False)
                        except:
                            log.debug('%s : failed to set nonKeyable attr status' % attr)
        log.info('<< AttrMap Processed >>')
        
    @staticmethod
    def processState(nodes, attrs, mode, hierarchy=False, userDefined=False):
        '''
        Easy wrapper to manage channels that are keyable / locked
        in the channelBox.
        
        :param nodes: nodes to process
        :param attrs: set() of attrs
        :param mode: 'lock', 'unlock', 'hide', 'unhide', 'fullkey', 'lockall'
        :param hierarchy: process all child nodes, default is now False
        :param usedDefined: process all UserDefined attributes on all nodes
        '''
        userDefAttrs=set()
        if not nodes:
            nodes = cmds.ls(sl=True, l=True)
        else:
            if not type(nodes)==list:
                nodes=[nodes]
        if hierarchy:
            #Filter the selection for children including the selected roots
            nodes=FilterNode(nodes).lsHierarchy(incRoots=True)
        
        if not hasattr(attrs,'__iter__'):
            attrs=set([attrs])
        if not type(attrs)==set:
            attrs=set(attrs)
            
        #print('Base attrs : ',attrs)
        attrKws={}
        
        if mode=='lock':
            attrKws['lock']=True
        elif mode=='unlock':
            attrKws['lock']=False
        elif mode=='hide':
            attrKws['keyable']=False
        elif mode=='unhide':
            attrKws['keyable']=True
        elif mode=='fullkey':
            attrKws['keyable']=True
            attrKws['lock']=False
        elif mode=='lockall':
            attrKws['keyable']=False
            attrKws['lock']=True
            
        for node in nodes:
            if userDefined:
                userDef=cmds.listAttr(node, ud=True, se=True)
                if userDef:
                    userDefAttrs=set(userDef)
            for attr in (attrs | userDefAttrs):
                try:
                    #log.debug('node: %s.%s' % (node,attr))
                    if cmds.attributeQuery(attr, node=node, exists=True):
                        attrString='%s.%s' % (node, attr)
                        if cmds.getAttr(attrString, type=True) in ['double3','float3']:
                            #why?? Maya fails to set the 'keyable' flag staus for compound attrs!
                            childAttrs=cmds.listAttr(attrString, multi=True)
                            childAttrs.remove(attr)
                            log.debug('compoundAttr handler for node: %s.%s' % (node,attr))
                            for childattr in childAttrs:
                                cmds.setAttr('%s.%s' % (node, childattr), **attrKws)
                        else:
                            cmds.setAttr(attrString, **attrKws)
                except StandardError, error:
                    log.info(error)
                

def timeOffset_addPadding(pad=None, padfrom=None, scene=False):
    '''
    simple wrap of the timeoffset class which will add padding into the
    animation curves on the selected object by shifting keys
    :param pad: amount of padding frames to add
    :param padfrom: frame to pad from
    '''
    nodes = None
    if not pad:
        result = cmds.promptDialog(
                    title='Add Padding Frames',
                    message='Padding:',
                    button=['OK', 'Cancel'],
                    defaultButton='OK',
                    cancelButton='Cancel',
                    dismissString='Cancel')
        if result == 'OK':
            pad = float(cmds.promptDialog(query=True, text=True))
    if not padfrom:
        padfrom = cmds.currentTime(q=True)
    if not scene:
        nodes = cmds.ls(sl=True, l=True)
        TimeOffset.fromSelected(pad, nodes=nodes, timerange=(padfrom, 1000000))
    else:
        TimeOffset.fullScene(pad, timerange=(padfrom, 1000000))
    # TimeOffset.animCurves(pad, nodes=nodes, time=(padfrom, 1000000))
   
def timeOffset_collapse(scene=False):
    '''
    simple wrap of the timeoffset that given a selected range in the timeline will
    collapse the keys within that range and shift forward keys back to close the gap
    :param scene: whether to process the entire scene or selected nodes
    '''
    nodes = None
    timeRange = r9Anim.timeLineRangeGet(always=False)
    if not timeRange:
        raise StandardError('No timeRange selected to Compress')
    offset = -(timeRange[1] - timeRange[0])
    if not scene:
        nodes = cmds.ls(sl=True, l=True)
        TimeOffset.fromSelected(offset, nodes=nodes, timerange=(timeRange[1], 10000000))
    else:
        TimeOffset.fullScene(offset, timerange=(timeRange[1], 10000000))
    # TimeOffset.animCurves(-(timeRange[1]-timeRange[0]), nodes=nodes, time=(timeRange[1], 10000000))
    
    cmds.currentTime(timeRange[0], e=True)
   
class TimeOffset(object):
    '''
    A class for dealing with time manipulation inside Maya.
    
    >>> offset=100
    >>> 
    >>> #build a filterSettings object up, in this case we're loading a current one.
    >>> flt=r9Core.FilterNode_Settings()
    >>> flt.read(os.path.join(r9Setup.red9Presets(),'Crytek_New_Meta.cfg'))
    >>> flt.incRoots=True
    >>> flt.printSettings()
    >>> 
    >>> r9Core.TimeOffset().fromSelected(offset, filterSettings=flt, flocking=False, randomize=False)

    '''
    @classmethod
    def fullScene(cls, offset, timelines=False, timerange=None):
        '''
        Process the entire scene and time offset all suitable nodes
        '''
        log.debug('TimeOffset Scene : offset=%s, timelines=%s' % \
                  (offset, str(timelines)))
        cls.animCurves(offset, timerange=timerange)
        cls.sound(offset, mode='Scene', timerange=timerange)
        cls.animClips(offset, mode='Scene', timerange=timerange)
        if timelines:
            cls.timelines(offset)
        print('Scene Offset Successfully')
        
    @classmethod
    def fromSelected(cls, offset, nodes=None, filterSettings=None, flocking=False,
                     randomize=False, timerange=None):
        '''
        Process the current selection list and offset as appropriate.
        
        :param offset: number of frames to offset
        :param nodes: nodes to offset (or root of the filterSettings)
        :param flocking: wether to sucessively increment nodes during offset
        :param randomize: whether to add a ramdon factor to each succesive nodes offset
        :param timerange: only offset times within a given timerange
        :param filterSettings: this is a FilterSettings_Node object used to pass all 
            the filter types into the FilterNode code. Internally the following is true:

            | settings.nodeTypes: list[] - search nodes of type
            | settings.searchAttrs: list[] - search nodes with Attrs of name
            | settings.searchPattern: list[] - search for a given nodeName searchPattern
            | settings.hierarchy: bool - process all children from the roots
            | settings.incRoots: bool - include the original root nodes in the filter
        '''
        log.debug('TimeOffset from Selected : offset=%s, flocking=%i, randomize=%i, timerange=%s' % \
                  (offset, flocking, randomize, str(timerange)))
        if not nodes:
            nodes=cmds.ls(sl=True, l=True)

        if filterSettings:
            nodes = FilterNode(nodes, filterSettings).ProcessFilter()
            # selectedNodes.extend(FilterNode(selectedNodes,filterSettings).ProcessFilter())
            # selectedNodes=sortNumerically(selectedNodes)
        if nodes:
            if flocking or randomize:
                cachedOffset = 0  # Cached last flocking value
                increment = 0
                for node in nodes:
                    if randomize and not flocking:
                        increment = random.uniform(0, offset)
                    if flocking and not randomize:
                        increment = cachedOffset + offset
                        cachedOffset += offset
                    if flocking and randomize:
                        rand = random.uniform(0, offset)
                        increment = cachedOffset + rand
                        cachedOffset += rand
                    cls.animCurves(increment, node)
                    log.debug('animData randon/flock modified offset : %f on node: %s' % (increment, nodeNameStrip(node)))
            else:
                cls.animCurves(offset, nodes=nodes, timerange=timerange)
                cls.sound(offset, mode='Selected',
                          audioNodes=FilterNode().lsSearchNodeTypes('audio', nodes),
                          timerange=timerange)
                cls.animClips(offset, mode='Selected',
                              clips=FilterNode().lsSearchNodeTypes('animClip', nodes),
                              timerange=timerange)
            log.info('Selected Nodes Offset Successfully')
        else:
            raise StandardError('Nothing selected or returned from the Hierarchy filter to offset')

    @staticmethod
    @r9General.Timer
    def animCurves(offset, nodes=None, timerange=None):
        '''
        Shift Animation curves. If nodes are fed in to process then we do
        a number of aggressive searches to find all linked animation data.
        
        :param offset: amount to offset the curves
        :param nodes: nodes to offset if given
        :param timerange: if timerange given [start,end] then we cut the keys in that 
            range before shifting associated keys. Now we could just use the 
            keyframe(option='insert') BUT this has a MAJOR crash bug!
        '''
        safeCurves=FilterNode.lsAnimCurves(nodes, safe=True)
        
        if safeCurves:
            log.debug('AnimCurve Offset = %s ============================' % offset)
            #log.debug(''.join([('offset: %s\n' % curve) for curve in safeCurves]))
            moved=0
            if timerange:
                if offset>0:
                    #if moving positive in time, cutchunk is from the upper timerange + offset
                    cutTimeBlock=(timerange[1] + 0.1, timerange[1] + offset)
                else:
                    #else it's from the lower timerange - offset
                    cutTimeBlock=(timerange[0] + 0.1, timerange[0] - abs(offset + 1))
            for curve in safeCurves:
                try:
                    if timerange:
                        try:
                            log.debug('cutting moveRange: %f > %f  : %s' % (cutTimeBlock[0], cutTimeBlock[1], curve))
                            cmds.cutKey(curve, time=cutTimeBlock)
                        except:
                            log.debug('unable to cut keys')
                        cmds.keyframe(curve, edit=True, r=True, timeChange=offset, time=timerange)
                    else:
                        cmds.keyframe(curve, edit=True, r=True, timeChange=offset)
                    log.debug('offsetting: %s' % curve)
                    moved += 1
                except:
                    log.info('Failed to offset curves fully : %s' % curve)
            log.info('%i : AnimCurves were offset' % moved)
            
    @staticmethod
    def timelines(offset):
        '''
        Shift the main playback timelines and CurrentFrame
        '''
        cmds.currentTime(cmds.currentTime(q=True) + offset, e=True)
        cmds.playbackOptions(ast=cmds.playbackOptions(q=True, ast=True) + offset,
                             aet=cmds.playbackOptions(q=True, aet=True) + offset,
                             min=cmds.playbackOptions(q=True, min=True) + offset,
                             max=cmds.playbackOptions(q=True, max=True) + offset)
        
    @staticmethod
    def sound(offset, mode='Scene', audioNodes=None, timerange=None):
        '''
        Offset Audio nodes.
        
        :param offset: amount to offset the sounds nodes by
        :param mode: either process entire scene or selected
        :param audioNodes: optional, given nodes to process
        :param timerange: optional timerange to process (outer bounds only)
        '''
        if mode=='Scene':
            audioNodes=cmds.ls(type='audio')
        if audioNodes:
            nodesOffset=0
            log.debug('AudioNodes Offset ============================')
            for sound in audioNodes:
                try:
                    audioNode=r9Audio.AudioNode(sound)
                    if timerange and not audioNode.startFrame>timerange[0]:
                        log.info('Skipping Sound : %s > sound starts before the timerange begins' % sound)
                        continue
                    audioNode.offsetTime(offset)
                    nodesOffset+=1
                    log.debug('offset : %s' % sound)
                except:
                    pass
            log.info('%i : SoundNodes were offset' % nodesOffset)
                
    @staticmethod
    def animClips(offset, mode='Scene', clips=None, timerange=None):
        '''
        Offset Trax Clips
        
        :param offset: amount to offset the sounds nodes by
        :param mode: either process entire scene or selected
        :param clips: optional, given clips to offset
        :param timerange: optional timerange to process (outer bounds only)
        '''
        if mode=='Scene':
            clips=cmds.ls(type='animClip')
        if clips:
            log.debug('Clips Offset ============================')
            for clip in clips:
                try:
                    startFrame = cmds.getAttr('%s.startFrame' % clip)
                    if timerange and not startFrame>timerange[0]:
                        log.info('Skipping Clip : %s > clip starts before the timerange begins' % clip)
                        continue
                    cmds.setAttr('%s.startFrame' % clip, startFrame + offset)
                    log.debug('offset : %s' % clip)
                except:
                    pass
            log.info('%i : AnimClips were offset' % len(clips))
 
 
def distanceBetween(nodeA, nodeB):
    '''
    simple calculation to return the distance between 2 objects
    '''
    x1, y1, z1, _,_,_ = cmds.xform(nodeA,q=True,ws=True,piv=True)
    x2, y2, z2, _,_,_ = cmds.xform(nodeB,q=True,ws=True,piv=True)
    return math.sqrt(math.pow((x1-x2),2) + math.pow((y1-y2),2) + math.pow((z1-z2),2))


class MatrixOffset(object):
    
    '''
    Given 2 transforms calculate the difference as a Matrix and
    apply that as an offset matrix to a given list of nodes.
        
    >>> matrixOffset = MatrixOffset()
    >>> matrixOffset.setOffsetMatrix('inputA','inputB')
    >>> applyOffsetMatrixToNodes(nodesToOffset)
    '''
    
    def __init__(self):
        self.CachedData=[]
        self.OffsetMatrix=OpenMaya.MMatrix
        
    @staticmethod
    def get_MDagPath(node):
        dagpath=OpenMaya.MDagPath()
        selList=OpenMaya.MSelectionList()
        selList.add(node)
        selList.getDagPath(0, dagpath)
        return dagpath
        
    def setOffsetMatrix(self, inputA, inputB):
        '''
        from 2 transform return an offsetMatrix between them 
        
        :param inputA: MayaNode A
        :param inputB: MayaNode B
        '''
        DagNodeA=MatrixOffset.get_MDagPath(inputA)
        DagNodeB=MatrixOffset.get_MDagPath(inputB)
        
        initialMatrix=DagNodeA.inclusiveMatrix()
        newMatrix=DagNodeB.inclusiveMatrix()
        #get the difference, by inversing we put newMatrix in the same space
        self.OffsetMatrix=initialMatrix.inverse()*newMatrix
        return self.OffsetMatrix
        
    def __cacheCurrentData(self, nodes):
        '''
        Return a list of tuples containing the cached state of the nodes
        [(node, MDagpath, worldMatrix, parentInverseMatrix)]
        '''
        self.CachedData=[]
        for node in nodes:
            if not cmds.objExists(node):
                continue
            parentInverseMatrix=None
            dag=MatrixOffset.get_MDagPath(node)
            currentMatrix=dag.inclusiveMatrix()
            parents=cmds.listRelatives(node, p=True, f=True)
            scalePivot=cmds.getAttr('%s.scalePivot' % node)
            rotatePivot=cmds.getAttr('%s.rotatePivot' % node)
            if parents:
                parentNode=MatrixOffset.get_MDagPath(parents[0])
                parentInverseMatrix=parentNode.inclusiveMatrixInverse()
            self.CachedData.append((node, dag, currentMatrix, parentInverseMatrix, (rotatePivot, scalePivot)))
        return self.CachedData
    
    
    def applyOffsetMatrixToNodes(self, nodes, matrix=None):
        '''
        offset all the given nodes by the given MMatrix object
        
        :param nodes: Nodes to apply the offset Matrix too
        :param matrix: Optional OpenMaya.MMatrix to transform the data by
        '''
        offsetMatrix=self.OffsetMatrix
        if matrix:
            offsetMatrix=matrix
        if not type(nodes)==list:
            nodes=[nodes]
        for node, dag, initialMatrix, parentInverseMatrix, rotScal in self.__cacheCurrentData(nodes):
            if parentInverseMatrix:
                if not initialMatrix.isEquivalent(dag.inclusiveMatrix()):
                    print 'Dag has already been modified by previous parent node', node
                    continue
                else:
                #multiply the offset by the inverse ParentMatrix to put it into the correct space
                    OpenMaya.MFnTransform(dag).set(OpenMaya.MTransformationMatrix(initialMatrix*parentInverseMatrix*offsetMatrix.inverse()))
                    print 'node offset : ', node
                    cmds.setAttr('%s.rotatePivot' % node, rotScal[0][0][0],rotScal[0][0][1],rotScal[0][0][2])
                    cmds.setAttr('%s.scalePivot' % node, rotScal[1][0][0],rotScal[1][0][1],rotScal[1][0][2])
            else:
                OpenMaya.MFnTransform(dag).set(OpenMaya.MTransformationMatrix(initialMatrix*offsetMatrix.inverse()))
                cmds.setAttr('%s.rotatePivot' % node, rotScal[0][0][0],rotScal[0][0][1],rotScal[0][0][2])
                cmds.setAttr('%s.scalePivot' % node, rotScal[1][0][0],rotScal[1][0][1],rotScal[1][0][2])

       

