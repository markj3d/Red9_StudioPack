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

from __future__ import print_function

import maya.cmds as cmds
import maya.OpenMaya as OpenMaya

from functools import partial
import re
import random
import math
import os

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

def logging_is_debug():
    if log.level == 10:
        return True

# Language map is used for all UI's as a text mapping for languages
LANGUAGE_MAP = r9Setup.LANGUAGE_MAP


# -------------------------------------------------------------------------------------
# Generic Functions -----
# -------------------------------------------------------------------------------------

def nodeNameStrip(node):
    '''
    Simple method to strip any |Path and :Namespaces: from
    a given object DagPath ie Ns:Rig|Ns:Leg|Ns:Foot == Foot
    '''
    return node.split('|')[-1].split(':')[-1]

@r9General.Timer
def prioritizeNodeList(inputlist, priorityList, regex=True, prioritysOnly=False):
    '''
    Simple function to force the order of a given nList such that nodes
    in the given priority list are moved to the front of the list.

    :param inputlist: main input list
    :param priorityList: list which is used to prioritize/order the main nList
    :param regex: Switches from regex search to simple exact node name
    :param prioritysOnly: return just the priorityList matches or the entire list sorted

    .. note::
        Known issue, if Regex=True and you have 2 similar str's in the priority list then there's
        a chance that matching may be erractic...

        >>> priorityList=['upperLip','l_upperLip']
        >>> nodes=['|my|dag|path|jaw',|my|dag|path|l_upperLip','|my|dag|path|upperLip','|my|dag|path|lowerLip']
        >>> returns: ['|my|dag|path|l_upperLip','|my|dag|path|upperLip',|my|dag|path|jaw,'|my|dag|path|lowerLip]

        as in regex 'l_upperLip'=='upperLip' as well as 'upperLip'=='upperLip'
        really in regex you'd need to be more specific:  priorityList=['^upperLip','l_upperLip']
    '''
    # stripped = [nodeNameStrip(node) for node in inputlist]  # stripped back to nodeName
    nList = list(inputlist)  # take a copy so we don't mutate the input list
    reordered = []

    if regex:
        # this will match all partial matches within the inputList
        # print 'pList : ',priorityList
        for pNode in priorityList:
            for node in inputlist:
                if re.search(pNode, nodeNameStrip(node)):
                    # print 'matched : ', nodeNameStrip(node), pNode, node
                    reordered.append(node)
                    try:
                        nList.remove(node)
                    except:
                        if logging_is_debug():
                            log.debug('node not in list or already removed: %s>> priority str : %s' % (nodeNameStrip(node), node))

    else:
        # this is setup to match exact only
        stripped = [nodeNameStrip(node) for node in inputlist]  # stripped back to nodeName
        for pNode in priorityList:
            if pNode in stripped:
                index = stripped.index(pNode)
                reordered.append(nList[index])
                nList.pop(index)
                stripped.pop(index)

    if not prioritysOnly:
        reordered.extend(nList)

    # [log.debug('Prioritized Index: %i = %s  <: ORIGINALLY :>  %s' % (i,nodeNameStrip(reordered[i]),n)) for i,n in enumerate(stripped)]

    return reordered


def sortNumerically(data):
    """
    Sort the given data in the way that humans expect.

    >>> data=['Joint_1','Joint_2','Joint_9','Joint_10','Joint_11','Joint_12']
    >>>
    >>> # standard gives us:
    >>> data.sort()
    >>> ['Joint_1', 'Joint_10', 'Joint_11', 'Joint_12', 'Joint_2', 'Joint_9']
    >>>
    >>> # sortNumerically gives us:
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

    :param replace_dict:
    '''
    rc = re.compile(r"[A-Za-z_]\w*")

    def translate(match):
        word = match.group(0)
        return replace_dict.get(word, word)
    return rc.sub(translate, text)

def removeNameSpace_fromDag(dagpath):
    '''
    from a given DagPath remove any namespaces - used in the poseCompare to only compare the native hierarchies

    such that:
        "|test:Reference|test:Hips|test:Spine|test:Spine1|test:Spine2|test:Spine3|test:Spine4|test:Neck|test:Neck1|test:Neck2|test:Head"
    will return:
        "|Reference|Hips|Spine|Spine1|Spine2|Spine3|Spine4|Neck|Neck1|Neck2|Head"
    '''
    clean = nodeNameStrip(dagpath)
    dirty = dagpath.split('|')[-1]
    if not clean == dirty:
        namespaces = dirty.split(clean)[0].split(':')
        namespaces.reverse()
        for ns in namespaces:
            if ns:
                dagpath = dagpath.replace('%s:' % ns, '')
        return dagpath
    return dagpath

def decodeString(val):
    '''
    From configObj the return is a string, we want to encode
    it back to it's original state so we pass it through this
    '''
    try:
        # configobj section handler to push back to native dict
        try:
            from Red9.packages.configobj import Section
            if issubclass(type(val), Section):
                return val.dict()
        except:
            log.debug('failed to convert configObj section %s' % val)

        if not issubclass(type(val), str) and not type(val) == unicode:
            # log.debug('Val : %s : is not a string / unicode' % val)
            # log.debug('ValType : %s > left undecoded' % type(val))
            return val
        if val == 'False' or val == 'True' or val == 'None':
            # log.debug('Decoded as type(bool)')
            return eval(val)
        elif val == '[]':
            # log.debug('Decoded as type(empty list)')
            return eval(val)
        elif val == '()':
            # log.debug('Decoded as type(empty tuple)')
            return eval(val)
        elif val == '{}':
            # log.debug('Decoded as type(empty dict)')
            return eval(val)
        elif (val[0] == '[' and val[-1] == ']'):
            # log.debug('Decoded as type(list)')
            return eval(val)
        elif (val[0] == '(' and val[-1] == ')'):
            # log.debug('Decoded as type(tuple)')
            return eval(val)
        elif (val[0] == '{' and val[-1] == '}'):
            # log.debug('Decoded as type(dict)')
            return eval(val)
        try:
            encoded = int(val)
            # log.debug('Decoded as type(int)')
            return encoded
        except:
            pass
        try:
            encoded = float(val)
            # log.debug('Decoded as type(float)')
            return encoded
        except:
            pass
    except:
        return
    # log.debug('Decoded as type(string)')
    return val


def validateString(strText, fix=False, illegals=['-', '#', '!', ' ', '@']):
    '''
    Function to validate that a string has no illegal characters

    :param strText: text to validate
    :param fix: if True then we replace illegals with '_'
    :param illegals: now allow you to pass in what you consider illegals, default=['-', '#', '!', ' ', '@']
    '''
    # numerics=['1','2','3','4','5','6','7','8','9','0']
    # illegals=['-', '#', '!', ' ']
    base = strText
    # if strText[0] in numerics:
    #    raise ValueError('Strings must NOT start with a numeric! >> %s' % strText)
    illegal = [i for i in illegals if i in strText]
    if illegal:
        if not fix:
            raise ValueError('String contains illegal characters "%s" <in> "%s"' % (','.join(illegal), strText))
        else:
            for i in illegal:
                strText = strText.replace(i, '_')
            log.info('%s : reformatted string to valid string : %s' % (base, strText))
    return strText


def filterListByString(input_list, filter_string, matchcase=False):
    '''
    Generic way to filter a list by a given string input. This is so that all
    the filtering used in the UI's is consistent. Used by the poseSaver, facialUI,
    MetaUI and many others.

    see : https://docs.python.org/3.3/howto/regex.html , http://www.pyregex.com , or search for Regex cheat sheets

    :param iniput_list: list of strings to be filtered
    :param filter_string: string to use in the filter, supports comma separated search strings
        eg : 'brows,smile,funnel'
    :param matchcase: whether to match or ignore case sensitivity

    .. note::
        this is a Regex search but it's managed under the hood.
        >> 'attack knife' would yield matches with 'attack and knife in the string, similar to 'attack*.*knife in windows, compiles to ('attack.*knife')
        >> 'attack..knife' would yield matches with 'attack12knife' 2 wildcards between the params (dots are wildcards in regex), compiles to ('attack..knife')
        >> 'attack.*knife' would yield matches with 'attack_big_massive_knife' because of the .* is multiple wildcards between the search params, compiles to ('attack.*knife')
        >> 'attack,knife' would yield matches with either 'attack' and 'knife' in the string, compiles to ('attack|knife') with the '|' or operator
        >> 'attack|knife' same as above
        >> 'attack$' would match 'we_attack' but not 'they_attacked' as the $ is used here as the end of the search string
        >> ^attack' would match 'attack_then' but not 'they_attack' as the ^ clamps to the front of the string
    '''

    if not matchcase:
        filter_string = filter_string.upper()
#     filterBy=[f for f in filter_string.replace(' ','').rstrip(',').split(',') if f]
    filteredList = []

    filterBy = [f for f in filter_string.rstrip(',').split(',') if f]
    pattern = []
    for n in filterBy:
        if ' ' in n:
            pattern.append('(%s)' % n.replace(' ', ')+.*('))
        else:
            pattern.append(n)
    filterPattern = '|'.join(n for n in pattern)
    log.debug('new : %s' % filterPattern)

    regexFilter = re.compile('(' + filterPattern + ')')  # convert into a regularExpression

    for item in input_list:
        data = item
        # filterPattern='|'.join(n for n in filterBy)
        # regexFilter=re.compile('('+filterPattern+')')  # convert into a regularExpression
        if not matchcase:
            data = item.upper()
        if regexFilter.search(data):
            # print data,item,filterPattern
            if item not in filteredList:
                filteredList.append(item)
    return filteredList

def nodes_in_hierarchy(rootNode, nodes=[], nodeType=None):
    '''
    check to see if a given set of nodes (shortname matched) are found in
    the given hierarchy and return the matches

    :param rootNode: rootNode of the hierarchy to search
    :param nodes: nodes to find from their shortName
    :param nodeType: nodeTypes within the hierarchy to search
    '''
    flt = FilterNode(rootNode)
    flt.settings.nodeTypes = nodeType
    found = []
    for node in nodes:
        _name = nodeNameStrip(node)
        flt.settings.searchPattern = '^%s' % _name
        matches = flt.processFilter()
        if matches:
            for m in matches:
                if nodeNameStrip(m) == _name:
                    found.append(m)
    return found

def nodes_are_constrained(src, target):
    '''
    :param src: the node that would be the driver of the constraint
    :param target: the node we think is being driven

    return any constraints between the source and target object if found.
    This checks the target for child constraints, then checks the target list
    for those constraints to see if the src is in the list, if so it's added to the return
    '''
    found = []
    src = cmds.ls(src, l=True)[0]
    cons = cmds.listRelatives(target, type='parentConstraint', f=True)
    if cons:
        for con in cons:
            if src in [cmds.ls(node, l=True)[0] for node in cmds.parentConstraint(con, q=True, tl=True)]:
                found.append(con)
    cons = cmds.listRelatives(target, type='orientConstraint', f=True)
    if cons:
        for con in cons:
            if src in [cmds.ls(node, l=True)[0] for node in cmds.orientConstraint(con, q=True, tl=True)]:
                found.append(con)
    cons = cmds.listRelatives(target, type='pointConstraint', f=True)
    if cons:
        for con in cons:
            if src in [cmds.ls(node, l=True)[0] for node in cmds.pointConstraint(con, q=True, tl=True)]:
                found.append(con)
    cons = cmds.listRelatives(target, type='scaleConstraint', f=True)
    if cons:
        for con in cons:
            if src in [cmds.ls(node, l=True)[0] for node in cmds.scaleConstraint(con, q=True, tl=True)]:
                found.append(con)
    return found

# -------------------------------------------------------------------------------------
# Filter Node Setups ------
# -------------------------------------------------------------------------------------

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
        activeFilters = []
        if self.metaRig:
            activeFilters.append('metaRig=%s' % self.metaRig)
        if self.nodeTypes:
            activeFilters.append('nodeTypes=%s' % self.nodeTypes)
        if self.searchAttrs:
            activeFilters.append('searchAttrs=%s' % self.searchAttrs)
        if self.searchPattern:
            activeFilters.append('searchPattern=%s' % self.searchPattern)
        # if self.hierarchy:
        activeFilters.append('hierarchy=%s' % self.hierarchy)
        if self.filterPriority:
            activeFilters.append('filterPriority=%s' % self.filterPriority)
        # if self.incRoots:
        activeFilters.append('incRoots=%s' % self.incRoots)
        # if self.transformClamp:
        activeFilters.append('transformClamp=%s' % self.transformClamp)
        return '%s(ActiveFilters: %s)' % (self.__class__.__name__, (', ').join(activeFilters))

    def __eq__(self, settingsdata):
        '''
        test if a given settings object filters matches this instance
        '''
        return all([self.transformClamp == settingsdata.transformClamp,
                    self.metaRig == settingsdata.metaRig,
                    self.hierarchy == settingsdata.hierarchy,
                    self.rigData == settingsdata.rigData,
                    self.incRoots == settingsdata.incRoots,
                    self.filterPriority == settingsdata.filterPriority,
                    self.nodeTypes == settingsdata.nodeTypes,
                    self.searchAttrs == settingsdata.searchAttrs,
                    self.searchPattern == settingsdata.searchPattern])

    def filterIsActive(self):
        '''
        the filter is deemed to be active if any of the filterSettings would
        produce a hierarchy search.
        '''
        if self.nodeTypes or self.searchAttrs or self.searchPattern or self.hierarchy or self.metaRig:
            return True
        return False

    def printSettings(self):
        '''
        pretty print the filterSettings data
        '''
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
        self.nodeTypes = []
        self.searchAttrs = []
        self.searchPattern = []
        self.hierarchy = False
        self.filterPriority = []
        self.incRoots = True
        self.metaRig = False
        self.transformClamp = True
        self.infoBlock = ""
        if rigData:
            self.rigData = {}

    def setByDict(self, data):
        '''
        set the filetrSettings via a dict correctly formatted, used
        to pull the data back from an MRig that has this data bound to it

        :param data: dict of data formatted as per the filterSettings keys.
            this is a new function allowing a dict of data to be passed into the
            object from a config file or mNode directly
        '''
        for key, val in data.items():
            try:
                self.__dict__[key] = decodeString(val)
            except:
                pass

    def write(self, filepath):
        '''
        write the filterSettings attribute out to a ConfigFile

        :param filepath: file path to write the configFile out to
        '''
        ConfigObj = configobj.ConfigObj(indent_type='\t')
        ConfigObj['filterNode_settings'] = self.__dict__
        ConfigObj.filename = filepath
        ConfigObj.write()

    def read(self, filepath):
        '''
        Read a given ConfigFile and fill this object instance with the data

        :param filepath: file path to write the configFile out to

        .. note::
            If filepath doesn't exists or you pass in just the short name of the config you
            want to load then we try and find a matching config in the default presets dir in Red9
        '''
        self.resetFilters()

        # have we passed in just the short name of an existing preset in the default dir?
        if not os.path.exists(filepath):
            if os.path.exists(os.path.join(r9Setup.red9Presets(), filepath)):
                filepath = os.path.join(r9Setup.red9Presets(), filepath)

        for key, val in configobj.ConfigObj(filepath)['filterNode_settings'].items():
            # because config is built from string data
            # we need to deal with specific types here
            try:
                self.__dict__[key] = decodeString(val)
            except:
                pass


# UI CALLS -----------------------------------------------------------------------

class FilterNode_UI(object):

    def __init__(self, settings=None):
        # Make a single filterNode instance
        self._filterNode = FilterNode()
        self._filterNode.settings.transformClamp = True
        self.win = 'NodeSearch'
        self.cbNodeTypes = []  # checkBox store for nodeTypes

    @classmethod
    def show(cls):
        cls()._showUI()

    def close(self):
        if cmds.window(self.win, exists=True):
            cmds.deleteUI(self.win, window=True)

    def _showUI(self):
        self.close()

        window = cmds.window(self.win, title=LANGUAGE_MAP._SearchNodeUI_.title)  # , widthHeight=(400, 400))
        cmds.menuBarLayout()
        cmds.menu(l=LANGUAGE_MAP._Generic_.vimeo_menu)
        cmds.menuItem(l=LANGUAGE_MAP._Generic_.vimeo_help,
                      c="import Red9.core.Red9_General as r9General;r9General.os_OpenFile('https://vimeo.com/56551684')")
        cmds.menuItem(divider=True)
        cmds.menuItem(l=LANGUAGE_MAP._Generic_.contactme, c=lambda *args: (r9Setup.red9ContactInfo()))
        self.MainLayout = cmds.columnLayout(adjustableColumn=True)
        cmds.frameLayout(label=LANGUAGE_MAP._SearchNodeUI_.complex_node_search, cll=True)  # , borderStyle='etchedOut')
        cmds.columnLayout(adjustableColumn=True)
        cmds.separator(h=15, style='none')

        # ====================
        # Intersector
        # ====================
        cmds.rowColumnLayout(ann=LANGUAGE_MAP._SearchNodeUI_.complex_node_search_ann, numberOfColumns=3, columnWidth=[(1, 130), (2, 130), (3, 130)], columnSpacing=[(1, 10)])
        cmds.checkBox(l=LANGUAGE_MAP._Generic_.nurbs_curve, v=False,
                        onc=lambda x: self.cbNodeTypes.append('nurbsCurve'),
                        ofc=lambda x: self.cbNodeTypes.remove('nurbsCurve'))
        cmds.checkBox(l=LANGUAGE_MAP._Generic_.meshes, v=False,
                        onc=lambda x: self.cbNodeTypes.append('mesh'),
                        ofc=lambda x: self.cbNodeTypes.remove('mesh'))
        cmds.checkBox(l=LANGUAGE_MAP._Generic_.joints, v=False,
                        onc=lambda x: self.cbNodeTypes.append('joint'),
                        ofc=lambda x: self.cbNodeTypes.remove('joint'))
        cmds.checkBox(l=LANGUAGE_MAP._Generic_.locators, v=False,
                        onc=lambda x: self.cbNodeTypes.append('locator'),
                        ofc=lambda x: self.cbNodeTypes.remove('locator'))
        cmds.checkBox(l=LANGUAGE_MAP._Generic_.cameras, v=False,
                        onc=lambda x: self.cbNodeTypes.append('camera'),
                        ofc=lambda x: self.cbNodeTypes.remove('camera'))
        cmds.checkBox(l=LANGUAGE_MAP._Generic_.audio, v=False,
                        onc=lambda x: self.cbNodeTypes.append('audio'),
                        ofc=lambda x: self.cbNodeTypes.remove('audio'))
        cmds.checkBox(l=LANGUAGE_MAP._Generic_.orient_constraint, v=False,
                        onc=lambda x: self.cbNodeTypes.append('orientConstraint'),
                        ofc=lambda x: self.cbNodeTypes.remove('orientConstraint'))
        cmds.checkBox(l=LANGUAGE_MAP._Generic_.point_constraint, v=False,
                        onc=lambda x: self.cbNodeTypes.append('pointConstraint'),
                        ofc=lambda x: self.cbNodeTypes.remove('pointConstraint'))
        cmds.checkBox(l=LANGUAGE_MAP._Generic_.parent_constraint, v=False,
                        onc=lambda x: self.cbNodeTypes.append('parentConstraint'),
                        ofc=lambda x: self.cbNodeTypes.remove('parentConstraint'))
        cmds.checkBox(l=LANGUAGE_MAP._Generic_.ik_handles, v=False,
                        onc=lambda x: self.cbNodeTypes.append('ikHandle'),
                        ofc=lambda x: self.cbNodeTypes.remove('ikHandle'))
        cmds.checkBox(l=LANGUAGE_MAP._Generic_.transforms, v=False,
                        onc=lambda x: self.cbNodeTypes.append('transform'),
                        ofc=lambda x: self.cbNodeTypes.remove('transform'))
        cmds.setParent('..')

        cmds.separator(h=20, st='in')
        self.uiSpecificNodeTypes = cmds.textFieldGrp(ann=LANGUAGE_MAP._SearchNodeUI_.search_nodetypes_ann,
                                            label=LANGUAGE_MAP._SearchNodeUI_.search_nodetypes, cw=[(1, 120)], text="")
        self.uiSpecificAttrs = cmds.textFieldGrp(ann=LANGUAGE_MAP._SearchNodeUI_.search_attributes_ann,
                                            label=LANGUAGE_MAP._SearchNodeUI_.search_attributes, cw=[(1, 120)], text="")
        self.uiSpecificPattern = cmds.textFieldGrp(label=LANGUAGE_MAP._SearchNodeUI_.search_pattern, cw=[(1, 120)], text="",
                                            ann=LANGUAGE_MAP._SearchNodeUI_.search_pattern_ann)
        cmds.separator(h=20, st='in')
        cmds.rowColumnLayout(numberOfColumns=2, columnWidth=[(1, 130), (2, 230)], columnSpacing=[(1, 10)])

        self.uiCbFromSelected = cmds.checkBox(ann=LANGUAGE_MAP._SearchNodeUI_.from_selected_ann,
                                            label=LANGUAGE_MAP._SearchNodeUI_.from_selected, al='left', v=True)
        self.uiCbKwsTransOnly = cmds.checkBox(ann=LANGUAGE_MAP._SearchNodeUI_.return_transforms_ann,
                        label=LANGUAGE_MAP._SearchNodeUI_.return_transforms, al='left',
                        v=self._filterNode.settings.transformClamp)
        cmds.separator(h=5, style='none')
        cmds.separator(h=5, style='none')
        self.uiCbKwsIncRoots = cmds.checkBox(ann=LANGUAGE_MAP._SearchNodeUI_.include_roots_ann,
                        label=LANGUAGE_MAP._SearchNodeUI_.include_roots, al='left',
                        v=self._filterNode.settings.incRoots)
        cmds.setParent('..')
        cmds.separator(h=10, style='none')
        cmds.button(label=LANGUAGE_MAP._SearchNodeUI_.intersection_search, bgc=r9Setup.red9ButtonBGC(1),
                     command=lambda *args: (self.__uiCall('intersection')))
        cmds.separator(h=20, st='in')
        cmds.button(label=LANGUAGE_MAP._SearchNodeUI_.simple_hierarchy, bgc=r9Setup.red9ButtonBGC(2),
                     command=lambda *args: (self.__uiCall('FullHierarchy')))
        cmds.setParent(self.MainLayout)
        cmds.separator(h=15, style='none')
        cmds.iconTextButton(style='iconOnly', bgc=(0.7, 0, 0), image1='Rocket9_buttonStrap2.bmp',
                             c=lambda *args: (r9Setup.red9ContactInfo()), h=22, w=200)
        cmds.separator(h=15, style='none')
        cmds.showWindow(window)
        # cmds.window(self.win, e=True, widthHeight=(400, 400))

    def __uiCall(self, mode):
        if mode == 'intersection':
            # Fill Main Settings Object filters =============

            # we use the reset on the filterSettings object for consistency across all calls
            self._filterNode.settings.resetFilters()

            # hierarchy flag
            self._filterNode.settings.incRoots = \
                        cmds.checkBox(self.uiCbKwsIncRoots, q=True, v=True)

            # transform flag
            self._filterNode.settings.transformClamp = \
                        cmds.checkBox(self.uiCbKwsTransOnly, q=True, v=True)

            # nodeType filter
            if cmds.textFieldGrp(self.uiSpecificNodeTypes, q=True, text=True):
                self._filterNode.settings.nodeTypes = \
                        cmds.textFieldGrp(self.uiSpecificNodeTypes, q=True, text=True).split(',')
            self._filterNode.settings.nodeTypes.extend(self.cbNodeTypes)
            # attribute filter
            if cmds.textFieldGrp(self.uiSpecificAttrs, q=True, text=True):
                self._filterNode.settings.searchAttrs = \
                        cmds.textFieldGrp(self.uiSpecificAttrs, q=True, text=True).split(',')
            # nodeName filter
            if cmds.textFieldGrp(self.uiSpecificPattern, q=True, text=True):
                self._filterNode.settings.searchPattern = \
                        cmds.textFieldGrp(self.uiSpecificPattern, q=True, text=True).split(',')

            # setup the root / processing mode
            if cmds.checkBox(self.uiCbFromSelected, q=True, v=True):
                self._filterNode.rootNodes = cmds.ls(sl=True, l=True)
                if not self._filterNode.rootNodes:
                    raise StandardError('No Root Nodes Given for Filtering')
            else:
                self._filterNode.rootNodes = None
                self._filterNode.processMode = 'Scene'

            # Main Call
            nodes = self._filterNode.processFilter()

        elif mode == 'FullHierarchy':
            self._filterNode.rootNodes = cmds.ls(sl=True, l=True)
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

    .. note::
        the searchPattern is a compiled Regex search but it's managed under the hood.
        >> 'attack knife' would yield matches with 'attack and knife in the string, similar to 'attack*.*knife in windows, compiles to ('attack.*knife')
        >> 'attack..knife' would yield matches with 'attack12knife' 2 wildcards between the params (dots are wildcards in regex), compiles to ('attack..knife')
        >> 'attack.*knife' would yield matches with 'attack_big_massive_knife' because of the .* is multiple wildcards between the search params, compiles to ('attack.*knife')
        >> 'attack,knife' would yield matches with either 'attack' and 'knife' in the string, compiles to ('attack|knife') with the '|' or operator
        >> 'attack|knife' same as above
        >> 'attack$' would match 'we_attack' but not 'they_attacked' as the $ is used here as the end of the search string
        >> ^attack' would match 'attack_then' but not 'they_attack' as the ^ clamps to the front of the string
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
                self.settings = filterSettings
            else:
                raise StandardError('filterSettings param requires an r9Core.FilterNode_Settings object')
        else:
            self.settings = FilterNode_Settings()

        self._processMode = 'Scene'  # Global processing mode - 'Selected' or 'Scene'
        self._rootNodes = []  # Main Roots used for all Hierarchy Filtering

        # Return Data
        self.hierarchy = []  # Data from the lsHierarchy call
        self.foundNodeTypes = []  # Matched Node list from lsSearchNodeTypes
        self.foundAttributes = []  # MatchAttribute list from lsSearchAttributes
        self.foundPattern = []  # Matched NodeName pattern list from lsSearchNamePattern
        self.intersectionData = []
        self.characterSetMembers = []  # Character Set member list from lsCharacterMembers
        # root objects to filter NOTE: This also switches Processing Mode to suit
        if roots:
            self.rootNodes = roots
        else:
            self.processMode = 'Scene'

    # Properties Block
    # ---------------------------------------------------------------------------------

    # Python2.5 compatible set/get property code for Maya2009

    def __get_rootNodes(self):
        if self._rootNodes:
            return self._rootNodes

    def __set_rootNodes(self, nodes):
        if nodes:
            if not isinstance(nodes, list):
                self._rootNodes = [nodes]
            else:
                self._rootNodes = nodes
            self.processMode = 'Selected'

            # New : MetaRig Update :
            # if we have a single rootNode and settings.metaRig=True then process that rig
            # to see if we have a bound settings object baked to it...if so we modify the
            # internal settings of this object to match
            self.__mrig_cast_settings()

        else:
            self.processMode = 'Scene'
            self._rootNodes = None

    rootNodes = property(__get_rootNodes, __set_rootNodes)

    def __mrig_cast_settings(self):
        '''
        get connected metaNodes relative to the rootNode then validate if we have an mRig to
        process, if we do then we look for the internal filterSettings data the new rigs carry
        and overload the filterSettings of this class with some of that data
        '''
        mrig = None
        if not self.settings.metaRig:
            return
        if len(self._rootNodes) == 1:
            if r9Meta.isMetaNode(self._rootNodes[0]) and issubclass(type(self._rootNodes[0]), r9Meta.MetaRig):
                mrig = r9Meta.MetaClass(self._rootNodes[0])
            else:
                mrig = r9Meta.getConnectedMetaSystemRoot(self._rootNodes[0], mInstances=r9Meta.MetaRig)
            if mrig:
                # PRO PACK ONLY:
                if mrig.hasAttr('filterSettings') and mrig.filterSettings:
                    try:
                        # log.info('==============================================================')
                        log.info('mRig : setting.filterPriority pulled directly from mNodes data')
                        # log.info('==============================================================')
                        self.settings.filterPriority = mrig.settings.filterPriority
                        if 'snapPriority' in mrig.settings.rigData:
                            self.settings.rigData['snapPriority'] = mrig.settings.rigData['snapPriority']
                        else:
                            self.settings.rigData['snapPriority'] = True
                        # self.settings.printSettings()
                        # log.info('==============================================================')
                    except StandardError, err:
                        log.info('mRig has FilterSettings data but is NOT a Pro_MetaRig - settings aborted')
                        log.info(err)
                else:
                    log.info('mRig : No specific filter data bound to this rig')
            return mrig

    def __get_processMode(self):
            return self._processMode

    def __set_processMode(self, mode):
        if mode == 'Selected':
            self._processMode = mode
            log.debug('Switching to SELECTED ROOTNODE HIERARCHY Processing Mode')
        elif mode == 'Scene':
            self._processMode = mode
            log.debug('Switching to SCENE or GIVEN NODE Processing Mode')

    processMode = property(__get_processMode, __set_processMode)

    @staticmethod
    def knownShapes():
        return ["baseLattice", "camera", "clusterHandle", "deformBend", "deformFlare", "deformSine",
        "deformSquash", "deformTwist", "deformWave", "angleDimension", "annotationShape",
        "distanceDimShape", "arcLengthDimension", "paramDimension", "dynHolder", "flexorShape",
        "clusterFlexo1rShape", "follicle1", "geoConnectable", "nurbsCurve", "lattice",
        "fluidShape", "fluidTexture2D", "fluidTexture3D", "heightField", "mesh", "nurbsSurface",
        "subdiv", "particle", "directedDisc", "environmentFog", "implicitBox", "renderBox",
        "implicitCone", "renderCone", "implicitSphere", "renderSphere", "locator",
        "dropoffLocator", "hikFloorContactMarker", "positionMarker", "orientationMarker",
        "sketchPlane", "renderRect", "snapshotShape", "hairConstraint", "hairSystem",
        "ambientLight", "areaLight", "directionalLight", "pointLight", "volumeLight",
        "spotLight", "lineModifier", "pfxGeometry", "pfxHair", "pfxToon", "stroke",
        "polyToolFeedbackShape", "rigidBody", "softModHandle", "spring"]

    # Hierarchy Block
    # ---------------------------------------------------------------------------------

    def getObjectSetMembers(self, objSet):
        '''
        return objectSet members in long form

        :param objSet: set to inspect and return the memebers from
        '''
        return cmds.ls(cmds.sets(objSet, q=True, nodesOnly=True), l=True, type='transform') or []

    def lsHierarchy(self, incRoots=False, transformClamp=False):
        '''
        Simple wrapper of the listRelatives, BUT with the option
        to include the rootNodes and select the results

        Also if a single rootNode is passed, and it's of type 'character'
        then the code will return the characterMembers instead

        :param incRoots: include the given rootNodes in the filter
        :param transformClamp: clamp all searches so that any shape style node returns it's parent transform

        TODO: objectSet modifications need testing!!!!!
        '''

        self.hierarchy = []
        if self.processMode == 'Selected':
            # check if we're dealing with a characterSet, if so return all its members
            for node in self.rootNodes:
                if cmds.nodeType(node) == 'character':
                    self.hierarchy.extend(self.lsCharacterMembers())
                elif cmds.nodeType(node) == 'objectSet':
                    self.hierarchy.extend(self.getObjectSetMembers(node))
                    childSets = cmds.listConnections(node, type='objectSet', s=True, d=False)  # need a walk here??
                    if childSets:
                        for childSet in childSets:
                            self.hierarchy.extend(self.getObjectSetMembers(childSet))
                else:
                    if incRoots:
                        self.hierarchy.append(node)
                    if not transformClamp:
                        self.hierarchy.extend(cmds.listRelatives(node, ad=True, f=True) or [])
                    else:
                        # Still not sure this is the right place for the transform clamp
                        self.hierarchy.extend(cmds.listRelatives(node, ad=True, f=True, type='transform') or [])
            return self.hierarchy
        else:
            raise StandardError('rootNodes not given to class - processing at SceneLevel Only - lsHierarchy is therefore invalid')

    # Node Management Block
    # ---------------------------------------------------------------------------------

    # @r9General.Timer
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

        TODO: Add the ability to use the NOT: operator in this, so for example, nodeTypes=transform
        would return all mesh nodes too, or rather the transform from a mesh, maybe you'd want to
        clamp that and prevent mesh transforms being returned? Is this even reasonable???
        '''

        self.foundNodeTypes = []
        typeMatched = []
        if logging_is_debug():
            log.debug('lsSearchNodeTypes : params : nodeTypes=%s, nodes=%s, incRoots=%i, transformClamp=%i'
                   % (nodeTypes, nodes, incRoots, transformClamp))

        if not isinstance(nodeTypes, list):
            nodeTypes = [nodeTypes]

        if self.processMode == 'Selected' and len(self.rootNodes) == 1:
            # PreProcess set selections and add all members to the test
            # TO DO: have this process multiple selected Sets
            if cmds.nodeType(self.rootNodes[0]) == 'character':
                nodes = self.lsCharacterMembers()
                log.debug('adding CharacterSetMembers to nodes for processing : %s', nodes)
            elif cmds.nodeType(self.rootNodes[0]) == 'objectSet':
                nodes = self.lsHierarchy(self.rootNodes[0])
                # nodes=cmds.sets(self.rootNodes[0],q=True,nodesOnly=True)
                log.debug('adding SelectionSetMember to nodes for processing : %s', nodes)

        if nodes:
            # This is going to run through the given objects and check if they of the given nodeType
            # However, this also will check if we're searching for given shapeNodeTypes and if so
            # question any transforms for child nodes of the correct shapeType
            shapeTypes = list(set(nodeTypes).intersection(set(self.knownShapes())))
            if not shapeTypes:
                typeMatched = [node for node in nodes if cmds.nodeType(node) in nodeTypes]
            else:
                for node in nodes:
                    if cmds.nodeType(node) in nodeTypes:
                        typeMatched.append(node)
                    else:
                        if 'transform' in cmds.nodeType(node, i=True):
                            shapeMatched = cmds.listRelatives(node, type=shapeTypes, f=True)
                            if shapeMatched:
                                typeMatched.extend(shapeMatched)
        else:
            # No Nodes passed in, do straight listRelatives Calls
            try:
                if self.processMode == 'Scene':
                    nodes = cmds.ls(type=nodeTypes, r=True, l=True)
                    if nodes:
                        typeMatched = nodes  # ensures we're always dealing with a list and not a null object
                elif self.processMode == 'Selected':
                    nodes = cmds.listRelatives(self.rootNodes, type=nodeTypes, ad=True, f=True)
                    if nodes:
                        typeMatched = nodes  # ensures we're always dealing with a list and not a null object

                    # Specific handler for blendShapes as these really need to be dealt with, and passed
                    # in the animation functions but don't show under a standard hierarchy search
                    if 'blendShape' in nodeTypes:
                        meshes = cmds.listRelatives(self.rootNodes, type='mesh', ad=True, f=True)
                        if meshes:
                            log.info('processing meshes for blendShapes')
                            for mesh in meshes:
                                blendShapes = [node for node in cmds.listHistory(mesh) if cmds.nodeType(node) == 'blendShape']
                                if blendShapes:
                                    typeMatched.extend(blendShapes)
            except StandardError, error:
                log.debug(error)
                log.warning('UnknownDataType Given in sublist : %s', nodeTypes)

        if typeMatched:
            if not transformClamp:
                self.foundNodeTypes = typeMatched
            else:
                for node in typeMatched:
                    # Check if the nodeType is inherited/subclass of 'shape', if so, return
                    # it's parent transform node. Note: if it is a shape node then we INSERT
                    # it at the front of the list, rather than appending to the end.
                    # This is due to the way Maya returns data from the listRelatives cmd
                    if 'shape' in cmds.nodeType(node, i=True):
                        parentTransform = cmds.listRelatives(node, f=True, p=True)[0]
                        if parentTransform not in self.foundNodeTypes:
                            self.foundNodeTypes.insert(0, parentTransform)
                    else:
                        if node not in self.foundNodeTypes:
                            self.foundNodeTypes.append(node)

            # test if the roots match the searchTypes if so add them to the end
            if self.processMode == 'Selected':
                if incRoots:
                    [self.foundNodeTypes.append(node) for node in self.rootNodes
                        if cmds.nodeType(node) in nodeTypes and node not in self.foundNodeTypes]
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
    # ---------------------------------------------------------------------------------

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
    # @r9General.Timer
    def lsAnimCurves(nodes=None, safe=False, allow_ref=False):
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
        :param allow_ref: if False and "safe" we remove all references animCurves, else we leave them in the return
        '''
        animCurves = []
        treeDepth = 2
        if not nodes:
            animCurves = cmds.ls(type='animCurve', r=True)
        else:
            try:
                # fucking AnimLayers!! if present then we up the depth of the history search
                # in-order to walk over the animBlendNodes to the actual animCurves.
                if r9Anim.getAnimLayersFromGivenNodes(nodes):
                    treeDepth = 3
                    log.debug('AnimLayers found, increasing search depth')

                    # Deal with curves linked to character sets or animation layer
                    animCurves = [curve for curve in cmds.listHistory(nodes, pdo=True, lf=False, lv=treeDepth)
                                               if cmds.nodeType(curve, i=True)[0] == 'animCurve']
                else:
                    # animCurves=cmds.listConnections(nodes,s=True,d=False,type='animCurve')
                    animCurves = [curve for curve in cmds.listHistory(nodes, pdo=True, lf=False, lv=treeDepth)
                                               if cmds.nodeType(curve, i=True)[0] == 'animCurve']
            except:
                pass
        if not animCurves:
            return []
        if not safe:
            return list(set(animCurves))
        else:
            safeCurves = list(animCurves)
            for animCurve in animCurves:
                # ignore referenced animCurves
                if not allow_ref and cmds.referenceQuery(animCurve, inr=True):
                    safeCurves.remove(animCurve)
                    continue
                # ignore setDrivens : animCurve have input connections
                if cmds.listConnections(animCurve, s=True, d=False):
                    safeCurves.remove(animCurve)
                    continue
                # ignore animClip curve data : animCurve is part of a TraxClip
                if cmds.nodeType(cmds.listConnections(animCurve)) == 'clipLibrary':
                    safeCurves.remove(animCurve)
                    continue
                # ignore curve if FUCKING animlayer it's a member of is locked!
                if cmds.getAttr("%s.ktv" % animCurve, l=True):
                    safeCurves.remove(animCurve)
                    continue

                # if curve.keyTimeValue.isLocked(): return False
            return safeCurves

    # Attribute Management Block
    # ---------------------------------------------------------------------------------

    # @r9General.Timer
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

        .. note::
            current Implementation DOES NOT allow multiple attr tests as only 1 val per key
            in the excludeAttrs and includeAttrs is currently supported!!
        '''

        self.foundAttributes = []
        attrDict = {}
        if logging_is_debug():
            log.debug('lsSearchAttributes : params : searchAttrs=%s, nodes=%s, incRoots=%i, returnValues=%i'
                   % (searchAttrs, nodes, incRoots, returnValues))

        # ensure we're passing a list
        if not isinstance(searchAttrs, list):
            searchAttrs = [searchAttrs]

        # Process and split the input list into 2 dicts
        includeAttrs = {}
        excludeAttrs = {}
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

        if logging_is_debug():
            log.debug('includes : %s' % includeAttrs.items())
            log.debug('excludes : %s' % excludeAttrs.items())

        # Node block
        if not nodes:
            if self.processMode == 'Scene':
                nodes = cmds.ls(dep=True, l=True)
            else:
                nodes = self.lsHierarchy(incRoots=incRoots)
            if not nodes:
                raise StandardError('No nodes found to process')

        # Search block
        for node in nodes:
            if includeAttrs:
                # we have attrs that we have to validate against so add=False is default
                add = False
            else:
                # we only have excluders so by default all nodes are added unless excluded
                add = True

            # Main test block, does the node get through the filter?
            for attr, val in includeAttrs.items():  # INCLUDE TESTS
                if cmds.attributeQuery(attr, exists=True, node=node):
                    if val[0]:  # value test
                        if not type(val[1]) == float:
                            if cmds.getAttr('%s.%s' % (node, attr)) == val[1]:
                                add = True
                                if logging_is_debug():
                                    log.debug('attr %s : value %s == %s : node %s > ADD = True' %
                                        (attr, val[1], cmds.getAttr('%s.%s' % (node, attr)), node))
                            else:
                                add = False
                                if logging_is_debug():
                                    log.debug('attr %s : value %s != %s : node %s > ADD = False' %
                                        (attr, val[1], cmds.getAttr('%s.%s' % (node, attr)), node))
                        else:
                            if floatIsEqual(cmds.getAttr('%s.%s' % (node, attr)), val[1]):
                                add = True
                                if logging_is_debug():
                                    log.debug('attr %s : Float value %f == %f : node %s > ADD = True' %
                                        (attr, val[1], cmds.getAttr('%s.%s' % (node, attr)), node))
                            else:
                                add = False
                                if logging_is_debug():
                                    log.debug('attr %s : Float value %f != %f : node %s > ADD = False' %
                                        (attr, val[1], cmds.getAttr('%s.%s' % (node, attr)), node))
                    else:
                        add = True
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
                                if logging_is_debug():
                                    log.debug('NOT: attr %s : Float value %s == %s : node %s > ADD = False' %
                                        (attr, val[1], cmds.getAttr('%s.%s' % (node, attr)), node))
                        else:
                            if floatIsEqual(cmds.getAttr('%s.%s' % (node, attr)), val[1]):
                                add = False
                                if logging_is_debug():
                                    log.debug('NOT: attr %s : Float value %f == %f : node %s > ADD = False' %
                                        (attr, val[1], cmds.getAttr('%s.%s' % (node, attr)), node))
                    else:
                        add = False
                        log.debug('NOT: attr %s : node %s > ADD = False' % (attr, node))
                    log.debug('NOT: attr Exclude : found : <BREAKOUT>')
                    break

            # Test Complete, ADD the node to the return list
            if add:
                if not returnValues:
                    if node not in self.foundAttributes:
                        self.foundAttributes.append(node)
                else:
                    try:
                        # WILL FAIL ON MESSAGE LINKS AS THEY HAVE NO VALUE
                        attrDict[node] = cmds.getAttr('%s.%s' % (node, attr))
                    except:
                        attrDict[node] = None
                        log.debug('Some Attribute Types such as Message attrs have no value')

        if returnValues:
            return attrDict
        else:
            return self.foundAttributes

    # Name Management Block
    # ---------------------------------------------------------------------------------

    # @r9General.Timer
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
        include = []
        exclude = []
        if not isinstance(searchPattern, list):
            searchPattern = [searchPattern]

        # Build the Regex funcs
        for pattern in searchPattern:
            pattern = pattern.replace(" ", "")  # strip whiteSpaces
            if 'NOT:' in pattern:
                exclude.append(pattern.split(':')[-1])
            else:
                include.append(pattern)

        includePattern = '|'.join(n for n in include)
        incRegex = re.compile('(' + includePattern + ')')  # convert into a regularExpression
        if exclude:
            excludePattern = '|'.join(n for n in exclude)
            excRegex = re.compile('(' + excludePattern + ')')  # convert into a regularExpression

        # Node block
        log.debug('lsSearchNamePattern : params : searchPattern=%s, nodes=%s, incRoots=%i'
               % (searchPattern, nodes, incRoots))
        if not nodes:
            if self.processMode == 'Scene':
                nodes = cmds.ls(dep=True, l=True)
            else:
                nodes = self.lsHierarchy(incRoots=incRoots)
            if not nodes:
                raise StandardError('No nodes found to process')

        # Actual Search calls
        if exclude:
            log.debug('Exclude SearchPattern found : %s' % exclude)
            for node in nodes:
                if incRegex.search(nodeNameStrip(node)) and not excRegex.search(nodeNameStrip(node)):
                    self.foundPattern.append(node)
        else:
            self.foundPattern = [node for node in nodes if incRegex.search(nodeNameStrip(node))]

        return self.foundPattern

    # Character Set Management Block
    # ---------------------------------------------------------------------------------

    def lsCharacterSets(self):
        '''
        Get any characterSets from the given rootNode (single only). If rootNode[0]
        is of type 'character' then it will just return itself. If not will test
        all children of the root for links to characterSets and return those found.
        '''
        cSets = []
        if self.processMode == 'Selected':
            # If any of the rootNodes are characterSet then return those
            if [cSets.append(node) for node in self.rootNodes if cmds.nodeType(node) == 'character']:
                for node in self.rootNodes:
                    # include subSets in this list
                    subSets = cmds.listConnections(node, type='character', s=True, d=False)
                    if subSets:
                        cSets.extend(subSets)
                return cSets
            else:
                # Test the full hierarchy for characterSet memberships
                hierarchy = self.lsHierarchy(incRoots=True)
                if not hierarchy:
                    raise StandardError('Roots have no children to process')
                for f in hierarchy:
                    linked = cmds.listConnections(f, type='character')
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
                for node in cmds.character(cset, query=True, nodesOnly=True):
                    if node not in self.characterSetMembers:
                        self.characterSetMembers.append(node)
                # self.characterSetMembers.extend(cmds.character(cset, query=True, nodesOnly=True))  # sure this used to work?
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
        rigCtrls = []
        metaNodes = []

        # First find all connected MetaData nodes
        for root in self.rootNodes:
            meta = None
            if r9Meta.isMetaNode(root):
                meta = r9Meta.MetaClass(root)
            else:
                mnodes = r9Meta.getConnectedMetaNodes(root)
                if mnodes:
                    for mnode in mnodes:
                        if issubclass(type(mnode), r9Meta.MetaRig):
                            meta = mnode
                            break
                    if not meta:
                        meta = mnodes[0]
            if meta and meta not in metaNodes:
                metaNodes.append(meta)

        # Find all controllers hanging off these given metaSystems
        if metaNodes:
            if logging_is_debug():
                log.debug('processing found MetaSystsem Nodes : %s' % ','.join([x.mNode for x in metaNodes]))
            for meta in metaNodes:
                ctrls = meta.getChildren(walk=walk)
                if ctrls and not incMain:
                    if meta.ctrl_main in ctrls:
                        ctrls.remove(meta.ctrl_main)
                rigCtrls.extend(ctrls)
        return rigCtrls

    # Main Search Call which uses the Settings Object
    # ---------------------------------------------------------------------------------

    def ProcessFilter(self):
        '''
        :Depricated Function:
        Replace the 'P' in the function call but not depricating it just yet
        as too much code both internally and externally relies on this method
        '''
        return self.processFilter()

    # @r9General.Timer
    def processFilter(self):
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
            self.intersectionData = []

            # wrap the intersector call
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

            # If FilterSettings have no effect then just return the rootNodes
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
                # run the main getChildren calls for hierarchy structure
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
                # note we reverse here as hierarchies are returned in reverse order
                # in Maya and the prioritize inserts at the beginning
                self.intersectionData.reverse()
                self.intersectionData = prioritizeNodeList(self.intersectionData, self.settings.filterPriority)
                self.intersectionData.reverse()
                # [log.debug('%i = %s' % (i, nodeNameStrip(n))) for i,n in enumerate(self.intersectionData)]

            return self.intersectionData

def getBlendTargetsFromMesh(node, asList=True, returnAll=False, levels=4, indexes=False):  # levels=1)
    '''
    quick func to return the blendshape targets found from a give mesh's connected blendshape's

    :param node: node to inspect for blendShapes, or the blendshape itself
    :param asList: return as a straight list of target names or a dict of data
    :param returnAll: if multiple blendshapes are found do we return all, or just the first
    :param levels: same as the 'levels' flag in listHistory as that's ultimately what grabs the blendShape nodes here
    :param indexes: return the data as a tuple (index, plug(weight[index]), blendtarget )
    '''
    if asList:
        targetData = []
    else:
        targetData = {}

    blendshapes = [b for b in cmds.listHistory(node, levels=levels) if cmds.nodeType(b) == 'blendShape']
    if blendshapes:
        for blend in blendshapes:
            weights = cmds.aliasAttr(blend, q=True)
            # print weights
            if weights:
                data = zip(weights[1::2], weights[0::2])
                weightKey = lambda x:int(x[0].replace('weight[', '').replace(']', ''))
                weightSorted = sorted(data, key=weightKey)
                if asList:
                    data = [t for i, t in weightSorted]
                    if indexes:
                        data = [(int(i.replace('weight[', '').replace(']', '')), i, t) for i, t in weightSorted]
                    if returnAll:
                        targetData.extend(data)
                    else:
                        # means we only return the first blend in the history
                        return data
                else:
                    targetData[blend] = weightSorted
    return targetData

def getBlendTargetIndex(blendNode, targetName):
    '''
    given a blendshape node return the weight index for a given targetName

    :param blendNode: blendShape node to inspect
    :param targetName: target Alias Name of the channel we're trying to find the index for
    '''
    weights = cmds.aliasAttr(blendNode, q=True)
    if weights:
        if targetName in weights:
            return int(weights[weights.index(targetName) + 1].replace('weight[', '').replace(']', ''))
    else:
        return 0

# -------------------------------------------------------------------------------------
# Node Matching ------
# -------------------------------------------------------------------------------------
@r9General.Timer
def matchNodeLists(nodeListA, nodeListB, matchMethod='stripPrefix', returnfails=False):
    '''
    Matches 2 given NODE LISTS by node name via various methods.

    :param nodeListA: list of nodes
    :param nodeListB: list of nodes
    :param returnfails: if True we return [matchedData, unmatched] so that we can pass the unmatched list for further processing
    :param matchMethod: default 'stripPrefix'

        | * matchMethod="index" : no intelligent matching, just purely zip the lists
            together in the order they were given
        | * matchMethod="indexReversed" : no intelligent matching, just purely zip
            the lists together in the reverse order they were given
        | * matchMethod="base" :  match each element by exact name (shortName) such
            that Spine==Spine or REF1:Spine==REF2:Spine
        | * matchMethod="stripPrefix" : match each element by a relaxed naming convention
            allowing for prefixes one side such that RigX_Spine == Spine
        | * matchMethod="mirrorIndex" : match via the nodes MirrorMarker
        | * matchMethod="metaData" : match the nodes based on their wiring connections to the MetaData framework

    :return: matched pairs of tuples for processing [(a1,b2),[(a2,b2)]
    '''
    infoPrint = ""
    matchedData = []
    unmatched = []
    # print 'MatchMethod : ', matchedData
    # take a copy of B as we modify the data here
    hierarchyB = list(nodeListB)
    if matchMethod == 'mirrorIndex':
        getMirrorID = r9Anim.MirrorHierarchy().getMirrorCompiledID
    if matchMethod == 'metaData':
        getMetaDict = r9Meta.MetaClass.getNodeConnectionMetaDataMap  # optimisation
        metaDictB = {}  # a cache of the connections so we don't re-process unless we have to

    if matchMethod == 'index':
        matchedData = zip(nodeListA, nodeListB)
    elif matchMethod == 'indexReversed':
        nodeListA.reverse()
        nodeListB.reverse()
        matchedData = zip(nodeListA, nodeListB)
    else:
        for nodeA in nodeListA:
            if matchMethod == 'mirrorIndex':
                indexA = getMirrorID(nodeA)
            if matchMethod == 'metaData':
                metaDictA = getMetaDict(nodeA)

            matched = False

            # BaseMatch is a direct compare ONLY
            # note that for 'stripPrefix' method we now FIRST do a base name
            # test to match like for like if we can if successful we don't
            # progress to the stripPrefix block itself
            if matchMethod == 'base' or matchMethod == 'stripPrefix':
                strippedA = nodeNameStrip(nodeA).upper()
                for nodeB in hierarchyB:
                    strippedB = nodeNameStrip(nodeB).upper()
                    if strippedA == strippedB:
                        if logging_is_debug():
                            infoPrint += '\nMatch Method : %s : %s == %s' % \
                                    (matchMethod, nodeA.split('|')[-1], nodeB.split('|')[-1])
                        matchedData.append((nodeA, nodeB))
                        hierarchyB.remove(nodeB)
                        matched = True
                        break

            if not matchMethod == 'base':
                for nodeB in hierarchyB:
                    strippedB = nodeNameStrip(nodeB).upper()
                    # Compare allowing for prefixing which is stripped off
                    if matchMethod == 'stripPrefix' and not matched:
                        if strippedA.endswith(strippedB) \
                            or strippedB.endswith(strippedA):
                            if logging_is_debug():
                                infoPrint += '\nMatch Method : %s : %s == %s' % \
                                         (matchMethod, nodeA.split('|')[-1], nodeB.split('|')[-1])
                            matchedData.append((nodeA, nodeB))
                            hierarchyB.remove(nodeB)
                            matched = True
                            break

                    # Compare using the nodes internal mirrorIndex if found
                    elif matchMethod == 'mirrorIndex':
                        if indexA and indexA == getMirrorID(nodeB):
                            if logging_is_debug():
                                infoPrint += '\nMatch Method : %s : %s == %s' % \
                                        (matchMethod, nodeA.split('|')[-1], nodeB.split('|')[-1])
                            matchedData.append((nodeA, nodeB))
                            hierarchyB.remove(nodeB)
                            matched = True
                            break

                    elif matchMethod == 'metaData':
                        if nodeB not in metaDictB.keys():
                            metaDictB[nodeB] = getMetaDict(nodeB)
                        if metaDictA and metaDictA == metaDictB[nodeB]:  # getMetaDict(nodeB):
                            if logging_is_debug():
                                infoPrint += '\nMatch Method : %s : %s == %s' % \
                                        (matchMethod, nodeA.split('|')[-1], nodeB.split('|')[-1])
                            matchedData.append((nodeA, nodeB))
                            hierarchyB.remove(nodeB)
                            matched = True
                            break
            if not matched:
                unmatched.append(nodeA)

        if unmatched and logging_is_debug():
            for node in unmatched:
                infoPrint += '\n!! Unresolved Matched Node !! : Match Method : %s : %s' % (matchMethod, node.split('|')[-1])

    log.debug('\nMatched Log : \n%s' % infoPrint)
    infoPrint = None
    if returnfails:
        return matchedData, unmatched
    else:
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
    # nodeList = None

    if nodes and issubclass(type(nodes), MatchedNodeInputs):
        log.debug('nodes are already of type MatchedNodeInputs')
        return nodes
    if not nodes:
        nodes = cmds.ls(sl=True, l=True)

    if filterSettings:
        log.debug('filterSettings Passed To MatchedNodeInputs : %s', filterSettings.__dict__)

    # make an instance of the MatchedNodeInputs object
    nodeList = MatchedNodeInputs(nodes, filterSettings=filterSettings, matchMethod=matchMethod, returnfails=True)

    if not toMany:
        nodeList.processMatchedPairs()
    else:
        # to Many - used for some of the anim functions
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

    def __init__(self, nodes=None, filterSettings=None, matchMethod='stripPrefix', returnfails=False):

        self.MatchedPairs = []  # Main Result Tuple of Pairs

        self.matchMethod = matchMethod
        self.returnfails = returnfails
        self.roots = nodes
        self.unmatched = []  # resultant list of unmatched nodes from the processing

        # make sure we have a settings object to process
        if filterSettings:
            if issubclass(type(filterSettings), FilterNode_Settings):
                self.settings = filterSettings
            else:
                raise StandardError('settings param requires an FilterNode_Settings object')
        else:
            self.settings = FilterNode_Settings()

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
            if not len(self.roots) == 2:
                raise StandardError('Please select ONLY 2 base objects for hierarchy comparison')

            # take a single instance of a FilterNode and process both root hierarchies
            filterNode = FilterNode(filterSettings=self.settings)
            filterNode.rootNodes = self.roots[0]
            nodesA = filterNode.processFilter()
            filterNode.rootNodes = self.roots[1]
            nodesB = filterNode.processFilter()

            # Match the 2 nodeLists by nodeName and return the MatcherPairs list
            self.MatchedPairs, self.unmatched = matchNodeLists(nodesA, nodesB, self.matchMethod, self.returnfails)

            # added 14/02/19: if the metaData mNodeID has been changed between rigs then the proper
            # metaData match will fail as it's based on mNodeID and mAttr matches for all nodes.
            # if this happens then regress the testing back to stripPrefix for all failed nodes
            if self.matchMethod == 'metaData' and self.unmatched:
                log.info('Regressing matchMethod from "metaData" to "stripPrefix" for failed matches within the mNode ConnectionMap')
                rematched = matchNodeLists(self.unmatched, nodesB, matchMethod='stripPrefix')
                if rematched:
                    self.MatchedPairs.extend(rematched)
                    self.unmatched = [node for node in rematched if node in self.unmatched]
        else:
            if not len(self.roots) >= 2:
                raise StandardError('Please select 2 or more matching base objects')
            if len(self.roots) == 2 and type(self.roots[0]) == list and type(self.roots[1]) == list:
                log.debug('<<2 lists passed in as roots - Assuming these are 2 hierarchies to process>>')
                self.MatchedPairs = matchNodeLists(self.roots[0], self.roots[1], self.matchMethod)
            else:
                # No matching, just take roots as selected and substring them with step
                # so that (roots[0],roots[1])(roots[2],roots[3])
                self.MatchedPairs = zip(self.roots[0::2], self.roots[1::2])
                for a, b in self.MatchedPairs:
                    log.debug('Blind Selection Matched  : %s == %s' % (a, b))

        return self.MatchedPairs


class LockChannels(object):
    '''
    Simple UI to manage the lock and key status of nodes
    '''
    def __init__(self):
        self.statusDict = {}

    class UI(object):

        def __init__(self):
            self.attrs = set()
            self.hierarchy = False
            self.userDefined = False
            self.win = 'LockChannels'

        @classmethod
        def show(cls):
            cls()._showUI()

        def close(self):
            if cmds.window(self.win, exists=True):
                cmds.deleteUI(self.win, window=True)

        def _showUI(self):
            self.close()
            window = cmds.window(self.win, title=LANGUAGE_MAP._LockChannelsUI_.title, s=False)  # widthHeight=(260, 410))
            cmds.menuBarLayout()
            cmds.menu(l=LANGUAGE_MAP._Generic_.vimeo_menu)
            cmds.menuItem(l=LANGUAGE_MAP._Generic_.vimeo_help,
                          c="import Red9.core.Red9_General as r9General;r9General.os_OpenFile('https://vimeo.com/58664502')")
            cmds.menuItem(divider=True)
            cmds.menuItem(l=LANGUAGE_MAP._Generic_.contactme, c=lambda *args: (r9Setup.red9ContactInfo()))
            cmds.columnLayout(adjustableColumn=True, columnAttach=('both', 5))
            cmds.separator(h=15, style='none')
            cmds.rowColumnLayout(ann=LANGUAGE_MAP._Generic_.attrs, numberOfColumns=4,
                                 columnWidth=[(1, 50), (2, 50), (3, 50)])

            cmds.checkBox('tx', l=LANGUAGE_MAP._Generic_.tx, v=False,
                          onc=lambda x: self.__uicheckboxCallbacksAttr('on', "tx"),
                          ofc=lambda x: self.__uicheckboxCallbacksAttr('off', "tx"))
            cmds.checkBox('ty', l=LANGUAGE_MAP._Generic_.ty, v=False,
                          onc=lambda x: self.__uicheckboxCallbacksAttr('on', "ty"),
                          ofc=lambda x: self.__uicheckboxCallbacksAttr('off', "ty"))
            cmds.checkBox('tz', l=LANGUAGE_MAP._Generic_.tz, v=False,
                          onc=lambda x: self.__uicheckboxCallbacksAttr('on', "tz"),
                          ofc=lambda x: self.__uicheckboxCallbacksAttr('off', "tz"))
            cmds.checkBox('translates', l=LANGUAGE_MAP._Generic_.translates, v=False,
                          onc=lambda x: self.__uicheckboxCallbacksAttr('on', ["tx", "ty", "tz"]),
                          ofc=lambda x: self.__uicheckboxCallbacksAttr('off', ["tx", "ty", "tz"]))

            cmds.checkBox('rx', l=LANGUAGE_MAP._Generic_.rx, v=False,
                          onc=lambda x: self.__uicheckboxCallbacksAttr('on', "rx"),
                          ofc=lambda x: self.__uicheckboxCallbacksAttr('off', "rx"))
            cmds.checkBox('ry', l=LANGUAGE_MAP._Generic_.ry, v=False,
                          onc=lambda x: self.__uicheckboxCallbacksAttr('on', "ry"),
                          ofc=lambda x: self.__uicheckboxCallbacksAttr('off', "ry"))
            cmds.checkBox('rz', l=LANGUAGE_MAP._Generic_.rz, v=False,
                          onc=lambda x: self.__uicheckboxCallbacksAttr('on', "rz"),
                          ofc=lambda x: self.__uicheckboxCallbacksAttr('off', "rz"))
            cmds.checkBox('rotates', l=LANGUAGE_MAP._Generic_.rotates, v=False,
                          onc=lambda x: self.__uicheckboxCallbacksAttr('on', ["rx", "ry", "rz"]),
                          ofc=lambda x: self.__uicheckboxCallbacksAttr('off', ["rx", "ry", "rz"]))

            cmds.checkBox('sx', l=LANGUAGE_MAP._Generic_.sx, v=False,
                          onc=lambda x: self.__uicheckboxCallbacksAttr('on', "sx"),
                          ofc=lambda x: self.__uicheckboxCallbacksAttr('off', "sx"))
            cmds.checkBox('sy', l=LANGUAGE_MAP._Generic_.sy, v=False,
                          onc=lambda x: self.__uicheckboxCallbacksAttr('on', "sy"),
                          ofc=lambda x: self.__uicheckboxCallbacksAttr('off', "sy"))
            cmds.checkBox('sz', l=LANGUAGE_MAP._Generic_.sz, v=False,
                          onc=lambda x: self.__uicheckboxCallbacksAttr('on', "sz"),
                          ofc=lambda x: self.__uicheckboxCallbacksAttr('off', "sz"))
            cmds.checkBox('scales', l=LANGUAGE_MAP._Generic_.scales, v=False,
                          onc=lambda x: self.__uicheckboxCallbacksAttr('on', ["sx", "sy", "sz"]),
                          ofc=lambda x: self.__uicheckboxCallbacksAttr('off', ["sx", "sy", "sz"]))

            cmds.checkBox('v', l=LANGUAGE_MAP._Generic_.vis, v=False,
                          onc=lambda x: self.__uicheckboxCallbacksAttr('on', "v"),
                          ofc=lambda x: self.__uicheckboxCallbacksAttr('off', "v"))

            cmds.setParent('..')
            cmds.rowColumnLayout(ann=LANGUAGE_MAP._Generic_.attrs, numberOfColumns=2,
                                 columnWidth=[(1, 150)])
            cmds.checkBox('userDefined', l=LANGUAGE_MAP._LockChannelsUI_.user_defined, v=False,
                          ann=LANGUAGE_MAP._LockChannelsUI_.user_defined_ann,
                          onc=lambda x: self.__setattr__('userDefined', True),
                          ofc=lambda x: self.__setattr__('userDefined', False))
            cmds.checkBox('ALL', l=LANGUAGE_MAP._LockChannelsUI_.all_attrs, v=False,
                          onc=lambda x: self.__uicheckboxCallbacksAttr('on', ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz", "v",
                                                                            "userDefined", "translates", "rotates", "scales"]),
                          ofc=lambda x: self.__uicheckboxCallbacksAttr('off', ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz", "v",
                                                                             "userDefined", "translates", "rotates", "scales"]))
            cmds.setParent('..')
            cmds.separator(h=20, style='in')
            cmds.checkBox('givenAttrs', l=LANGUAGE_MAP._LockChannelsUI_.specific_attrs,
                          onc=lambda x: cmds.textField('uitf_givenAttrs', e=True, en=True),
                          ofc=lambda x: cmds.textField('uitf_givenAttrs', e=True, en=False))
            cmds.textField('uitf_givenAttrs', text='', en=False,
                           ann=LANGUAGE_MAP._LockChannelsUI_.specific_attrs_ann)
            cmds.popupMenu()
            cmds.menuItem(label=LANGUAGE_MAP._Generic_.clear, command=partial(self.__uiTextFieldPopup, 'clear'))
            cmds.menuItem(label=LANGUAGE_MAP._LockChannelsUI_.add_chnbox_selection, command=partial(self.__uiTextFieldPopup, 'add'))

            cmds.separator(h=20, style='in')
            cmds.checkBox('Hierarchy', l=LANGUAGE_MAP._Generic_.hierarchy, al='left', v=False, ann=LANGUAGE_MAP._Generic_.hierarchy_ann,
                          onc=lambda x: self.__setattr__('hierarchy', True),
                          ofc=lambda x: self.__setattr__('hierarchy', False))
            cmds.rowColumnLayout(ann=LANGUAGE_MAP._Generic_.attrs, numberOfColumns=2, columnWidth=[(1, 125), (2, 125)])
            cmds.button(label=LANGUAGE_MAP._LockChannelsUI_.lock, bgc=r9Setup.red9ButtonBGC(1),
                         command=lambda *args: (self.__uiCall('lock')))
            cmds.button(label=LANGUAGE_MAP._LockChannelsUI_.unlock, bgc=r9Setup.red9ButtonBGC(2),
                         command=lambda *args: (self.__uiCall('unlock')))
            cmds.button(label=LANGUAGE_MAP._LockChannelsUI_.hide, bgc=r9Setup.red9ButtonBGC(1),
                         command=lambda *args: (self.__uiCall('hide')))
            cmds.button(label=LANGUAGE_MAP._LockChannelsUI_.unhide, bgc=r9Setup.red9ButtonBGC(2),
                         command=lambda *args: (self.__uiCall('unhide')))
            cmds.separator(h=20, style='in')
            cmds.separator(h=20, style='in')
            self.__uibtStore = cmds.button(label=LANGUAGE_MAP._LockChannelsUI_.store_attrmap, bgc=r9Setup.red9ButtonBGC(1),
                         ann=LANGUAGE_MAP._LockChannelsUI_.store_attrmap_ann,
                         command=lambda *args: (self.__uichannelMapFile('save')))
            self.__uibtLoad = cmds.button(label=LANGUAGE_MAP._LockChannelsUI_.load_attrmap, bgc=r9Setup.red9ButtonBGC(1),
                         ann=LANGUAGE_MAP._LockChannelsUI_.load_attrmap_ann,
                         command=lambda *args: (self.__uichannelMapFile('load')))
            cmds.setParent('..')
            cmds.separator(h=10, style='none')

            cmds.checkBox('serializeToNode', l=LANGUAGE_MAP._LockChannelsUI_.serialize_attrmap_to_node,
                          ann=LANGUAGE_MAP._LockChannelsUI_.serialize_attrmap_to_node_ann,
                          cc=lambda x: self.__uiAttrMapModeSwitch())

            cmds.textFieldButtonGrp('uitfbg_serializeNode',
                                    bl=LANGUAGE_MAP._Generic_.set,
                                    text='',
                                    en=False,
                                    ann=LANGUAGE_MAP._LockChannelsUI_.set_ann,
                                    bc=lambda *args: cmds.textFieldButtonGrp('uitfbg_serializeNode', e=True, text=cmds.ls(sl=True)[0]),
                                    cw=[(1, 220), (2, 60)])
            cmds.separator(h=15, style='none')
            cmds.iconTextButton(style='iconOnly', bgc=(0.7, 0, 0), image1='Rocket9_buttonStrap2.bmp',
                                 c=lambda *args: (r9Setup.red9ContactInfo()), h=22, w=200)
            cmds.separator(h=15, style='none')
            cmds.showWindow(window)
            # cmds.window(self.win, e=True, widthHeight=(260, 410))

        def __uicheckboxCallbacksAttr(self, mode, attrs):
            if not isinstance(attrs, list):
                attrs = [attrs]
            for attr in attrs:
                if mode == 'on':
                    try:
                        self.attrs.add(attr)
                        # manage the checkbox state in case the call was made
                        # from one of the list checkboxes.
                        cmds.checkBox(attr, edit=True, v=True)
                    except:
                        pass
                elif mode == 'off':
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
            hierarchy = cmds.checkBox('Hierarchy', q=True, v=True)
            nodes = cmds.ls(sl=True, l=True)

            if hierarchy and not nodes:
                raise StandardError('No Root of hierarchy selected to Process')
            if hierarchy and nodes and r9Meta.isMetaNode(nodes[0]):
                raise StandardError('MetaData node can not be the Root for hierarchy processing')
            if not hierarchy and not nodes:
                raise StandardError('No nodes selected to Process')

            if not cmds.checkBox('serializeToNode', q=True, v=True):
                if mode == 'load':
                    filePath = cmds.fileDialog2(fileFilter="attributeMap Files (*.attrMap *.attrMap);;", okc='Load')[0]
                    LockChannels().loadChannelMap(filepath=filePath, nodes=nodes, hierarchy=hierarchy)
                elif mode == 'save':
                    filePath = cmds.fileDialog2(fileFilter="attributeMap Files (*.attrMap *.attrMap);;", okc='Save')[0]
                    LockChannels().saveChannelMap(filepath=filePath, nodes=nodes, hierarchy=hierarchy)
            else:
                serializerNode = cmds.textFieldButtonGrp('uitfbg_serializeNode', q=True, text=True)
                if not cmds.objExists(serializerNode):
                    raise StandardError('No VALID MayaNode given to save/load the attrMaps to/From')
                if mode == 'load':
                    LockChannels().loadChannelMap(filepath=None, nodes=nodes, hierarchy=hierarchy, serializeNode=serializerNode)
                elif mode == 'save':
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
                    # print self.attrs
            LockChannels.processState(cmds.ls(sl=True, l=True), self.attrs, mode, self.hierarchy, self.userDefined)

    # MapFile calls
    # ----------------------------------
    def _buildAttrStateDict(self, nodes):
        '''
        build the internal dict thats stored and used by the save/load calls
        '''
        self.statusDict = {}
        for node in nodes:
            key = nodeNameStrip(node)
            self.statusDict[key] = {}
            self.statusDict[key]['keyable'] = cmds.listAttr(node, k=True, u=True)
            self.statusDict[key]['locked'] = cmds.listAttr(node, k=True, l=True)
            self.statusDict[key]['nonKeyable'] = cmds.listAttr(node, cb=True)

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

        self._buildAttrStateDict(nodes)
        if filepath:
            ConfigObj = configobj.ConfigObj(indent_type='\t')
            ConfigObj['channelMap'] = self.statusDict
            ConfigObj.filename = filepath
            ConfigObj.write()
        elif serializeNode:
            node = r9Meta.MetaClass(serializeNode)
            if not node.hasAttr('attrMap'):
                node.addAttr('attrMap', self.statusDict)
            else:
                node.attrSetLocked('attrMap', False)
                # cmds.setAttr('%s.attrMap' % serializeNode, l=False)
                node.attrMap = self.statusDict
            try:
                node.attrSetLocked('attrMap', True)
                # cmds.setAttr('%s.attrMap' % serializeNode, l=True)
            except StandardError, error:
                # referenced attrs, even though we've just added it, can't be locked!
                raise StandardError(error)
        log.info('<< AttrMap Processed >>')

    def loadChannelMap(self, filepath=None, nodes=None, hierarchy=True, serializeNode=None):
        '''
        From a given chnMap file restore the channelBox status for all attributes
        found that are in the map file. ie, keyable, hidden, locked

        :param filepath: filepath to the map to load
        :param nodes: nodes to load the data onto, if hierarcchy=True this is the rootNode
        :param hierarchy: process all child nodes of the nodes passed in
        :param serializeNode: if Meta then this is used to serialize the attrMap to the node itself

        .. note::
            Here we're dealing with 2 possible sets of data, either decoded by the
            ConfigObj decoder or a JSON deserializer and there's subtle differences in the dict
            thats returned hence the decodeString() calls

        '''
        if not nodes:
            nodes = cmds.ls(sl=True, l=True)
        if hierarchy:
            # Filter the selection for children including the selected roots
            nodes = FilterNode(nodes).lsHierarchy(incRoots=True, transformClamp=True)
        if filepath:
            self.statusDict = configobj.ConfigObj(filepath)['channelMap']
        elif serializeNode:
            serializeNode = r9Meta.MetaClass(serializeNode)
            if serializeNode.hasAttr('attrMap'):
                self.statusDict = serializeNode.attrMap
                # print type(self.statusDict), self.statusDict
            else:
                raise StandardError('attrMap not found on given node')

        for node in nodes:
            key = nodeNameStrip(node)
            if key in self.statusDict:

                # managed node so first hide and lock all current CBattrs
                currentAttrs = r9Anim.getChannelBoxAttrs(node, asDict=False)
                for attr in currentAttrs:
                    try:
                        # do not just blanket lock these!
                        if not attr in ['rotate', 'translate', 'scale']:
                            cmds.setAttr('%s.%s' % (node, attr), keyable=False, lock=True, channelBox=False)
                    except:
                        log.info('%s : failed to set initial state' % attr)

                # NOTE: this looks a slow way of processing but an Attr will
                # only ever appear in one of these lists so not really an overhead
                if not decodeString(self.statusDict[key]['keyable']) == None:
                    for attr in self.statusDict[key]['keyable']:
                        try:
#                             print 'keyable',attr
                            cmds.setAttr('%s.%s' % (node, attr), k=True, l=False)
                        except:
                            log.debug('%s : failed to set keyable attr status' % attr)
                if not decodeString(self.statusDict[key]['locked']) == None:
                    for attr in self.statusDict[key]['locked']:
                        try:
#                             print 'locked',attr
                            cmds.setAttr('%s.%s' % (node, attr), k=True, l=True)
                        except:
                            log.debug('%s : failed to set locked attr status' % attr)
                if not decodeString(self.statusDict[key]['nonKeyable']) == None:
                    for attr in self.statusDict[key]['nonKeyable']:
                        try:
#                             print 'nonKeyable',attr
                            cmds.setAttr('%s.%s' % (node, attr), cb=True)
                            cmds.setAttr('%s.%s' % (node, attr), l=False, k=False)
                        except:
                            log.debug('%s : failed to set nonKeyable attr status' % attr)
        log.info('<< AttrMap Processed >>')

    @staticmethod
    def processState(nodes, attrs=None, mode=None, hierarchy=False, userDefined=False, attrKws={}):
        '''
        Easy wrapper to manage channels that are keyable / locked
        in the channelBox.

        :param nodes: nodes to process
        :param attrs: set() of attrs, or 'all'
        :param mode: 'lock', 'unlock', 'hide', 'unhide', 'fullkey', 'lockall'
        :param hierarchy: process all child nodes, default is now False
        :param usedDefined: process all UserDefined attributes on all nodes
        :param attrKws: if mode=None then these are the flags passed to the setAttr
            command to control the node states, ie: {'keyable':True, 'lock':False, 'channelBox':True}

        >>> r9Core.LockChannels.processState(nodes, attrs=["sx", "sy", "sz", "v"], mode='lockall')
        >>>
        >>> # note: if attrs='all' we now set it to the following for ease:
        >>> ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz", "v", "radius"]
        '''
        userDefAttrs = set()
        if not nodes:
            nodes = cmds.ls(sl=True, l=True)
        else:
            if not type(nodes) == list:
                nodes = [nodes]
        if hierarchy:
            # Filter the selection for children including the selected roots
            nodes = FilterNode(nodes).lsHierarchy(incRoots=True)
        _attrs = attrs
        if attrs == 'all':
            _attrs = ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz", "v", "radius", "radi"]
        if attrs == 'transforms':
            _attrs = ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz"]

#         if not hasattr(_attrs, '__iter__'):
        if r9General.is_basestring(_attrs):
            _attrs = set([_attrs])
        if not type(_attrs) == set:
            _attrs = set(_attrs)

        if mode:
            attrKws = {}

        if mode == 'lock':
            attrKws['lock'] = True
        elif mode == 'unlock':
            attrKws['lock'] = False

        elif mode == 'hide':
            attrKws['keyable'] = False
        elif mode == 'unhide':
            attrKws['keyable'] = True

        elif mode == 'nonkeyable':
            attrKws['channelBox'] = True
        elif mode == 'keyable':
            attrKws['channelBox'] = False

        elif mode == 'fullkey':
            attrKws['keyable'] = True
            attrKws['lock'] = False
            # force unlock the compounds also?
            if attrs == 'all' or attrs == 'transforms':
                _attrs = _attrs | set(['translate', 'rotate', 'scale'])
        elif mode == 'lockall':
            attrKws['keyable'] = False
            attrKws['lock'] = True
            attrKws['channelBox'] = False  # 27/5/20 added

        for node in nodes:
            if userDefined:
                userDef = cmds.listAttr(node, ud=True, se=True)
                if userDef:
                    userDefAttrs = set(userDef)
            for attr in (_attrs | userDefAttrs):
                try:
                    log.debug('node: %s.%s' % (node, attr))
                    '''
                    If you pass in .tx but you've already locked the compound .translate then
                    the unlock will fail as it's parent compound is locked... do we fix this?
                    '''
                    if cmds.attributeQuery(attr, node=node, exists=True):
                        attrString = '%s.%s' % (node, attr)
                        if cmds.getAttr(attrString, type=True) in ['double3', 'float3']:
                            # why?? Maya fails to set the 'keyable' flag status for compound attrs!
                            childAttrs = cmds.listAttr(attrString, multi=True)
                            childAttrs.remove(attr)
                            log.debug('compoundAttr handler for node: %s.%s' % (node, attr))
                            cmds.setAttr(attrString, **attrKws)
                            for childattr in childAttrs:
                                cmds.setAttr('%s.%s' % (node, childattr), **attrKws)
                        else:
                            cmds.setAttr(attrString, **attrKws)
                except StandardError, error:
                    log.info(error)


def timeOffset_addPadding(pad=None, padfrom=None, scene=False, mRigs=False):
    '''
    simple wrap of the timeoffset class which will add padding into the
    animation curves on the selected object by shifting keys

    :param pad: amount of padding frames to add
    :param padfrom: frame to pad from
    :param scene: offset the entire scene
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
        TimeOffset.fromSelected(pad, nodes=nodes, timerange=(padfrom, 1000000), mRigs=mRigs)
    else:
        TimeOffset.fullScene(pad, timerange=(padfrom, 1000000))
    # TimeOffset.animCurves(pad, nodes=nodes, time=(padfrom, 1000000))

def timeOffset_collapse(scene=False, timerange=None, mRigs=False):
    '''
    Light wrap over the TimeOffset call to manage collapsing time

    :param scene: offset the entire scene or just selected
    :param timerange: specific timerange to collapse else we use the r9 timerange get call
    '''
    if not timerange:
        timerange = r9Anim.timeLineRangeGet(always=True)
    nodes = None
    if not timerange:
        raise StandardError('No timeRange selected to Compress')
    offset = -(timerange[1] - timerange[0])
    if not scene:
        nodes = cmds.ls(sl=True, l=True)
        TimeOffset.fromSelected(offset, nodes=nodes, timerange=(timerange[1], 10000000), mRigs=mRigs)
    else:
        TimeOffset.fullScene(offset, timerange=(timerange[1], 10000000))
    cmds.currentTime(timerange[0], e=True)

def timeOffset_collapseUI():
    '''
    collapse time confirmation UI
    '''
    def __uicb_run(scene, mrigs=False, *args):
        timeOffset_collapse(scene=scene,
                            timerange=(float(cmds.textField('start', q=True, tx=True)),
                                       float(cmds.textField('end', q=True, tx=True))),
                            mRigs=mrigs)

    timeRange = r9Anim.timeLineRangeGet(always=True)

    win = 'CollapseTime_UI'
    if cmds.window(win, exists=True):
        cmds.deleteUI(win, window=True)
    cmds.window(win, title=win)
    cmds.columnLayout(adjustableColumn=True)
    cmds.separator(h=10, style='none')
    cmds.text(label=LANGUAGE_MAP._MainMenus_.collapse_time)
    cmds.separator(h=15, style='in')
    cmds.rowColumnLayout(nc=4, cw=((1, 60), (2, 80), (3, 60), (4, 80)))
    cmds.text(label='Start Frm: ')
    cmds.textField('start', tx=timeRange[0], w=40)
    cmds.text(label='End Frm: ')
    cmds.textField('end', tx=timeRange[1], w=40)
    cmds.setParent('..')
    cmds.separator(h=10, style='none')
    cmds.rowColumnLayout(nc=2, cw=((1, 150), (2, 150)))
    cmds.button(label=LANGUAGE_MAP._MainMenus_.collapse_full,
                ann=LANGUAGE_MAP._MainMenus_.collapse_full_ann,
                command=partial(__uicb_run, True, False), bgc=r9Setup.red9ButtonBGC('green'))
    cmds.button(label=LANGUAGE_MAP._MainMenus_.collapse_selected,
                ann=LANGUAGE_MAP._MainMenus_.collapse_selected_ann,
                command=partial(__uicb_run, False, False), bgc=r9Setup.red9ButtonBGC('green'))
    cmds.setParent('..')
    cmds.separator(h=20, style='in')
    cmds.button(label=LANGUAGE_MAP._MainMenus_.collapse_mrig,
                ann=LANGUAGE_MAP._MainMenus_.collapse_mrig_ann,
                command=partial(__uicb_run, False, True), bgc=r9Setup.red9ButtonBGC('green'))

    cmds.separator(h=15, style='none')
    cmds.iconTextButton(style='iconOnly', bgc=(0.7, 0, 0), image1='Rocket9_buttonStrap2.bmp',
                                 c=lambda *args: (r9Setup.red9ContactInfo()), h=22, w=200)

    cmds.showWindow(win)


class TimeOffset(object):
    '''
    A class for dealing with time manipulation inside Maya.

    >>> offset=100
    >>>
    >>> #build a filterSettings object up, in this case we're loading a current one.
    >>> flt=r9Core.FilterNode_Settings()
    >>> flt.read(os.path.join(r9Setup.red9Presets(),'Red9_DevRig.cfg'))
    >>> flt.incRoots=True
    >>> flt.printSettings()
    >>>
    >>> r9Core.TimeOffset.fromSelected(offset, filterSettings=flt, flocking=False, randomize=False)

    '''

    # list of nodes processed by the systems so we no longer run the risk of offsetting a node twice!
    _processed = {'animcurves': [],
                  'sound': [],
                  'animclips': [],
                  'mnodes': [],
                  'image_planes': [],
                  'mnode_internals': []}

    def __init__(self, cache_object=None):
        if cache_object:
            self._processed = cache_object
            print('consuming current cached object')

    @classmethod
    def fullScene(cls, offset, timelines=False, timerange=None, ripple=True, startfrm=False):
        '''
        Process the entire scene and time offset all suitable nodes

        :param offset: number of frames to offset
        :param timelines: offset the playback timelines
        :param timerange: only offset times within a given timerange
        :param ripple: manage the upper range of data and ripple them with the offset
        :param startfrm: this turns the offset arg into a new target start frame for the animation,
            calculating the offset for you such that timerange[0] starts at the offset frm value, only works if timerange is passed in
        '''
        if timerange and startfrm:
            offset = offset - timerange[0]

        log.debug('TimeOffset Scene : offset=%s, timelines=%s' %
                  (offset, str(timelines)))
        cls._processed = {}  # clear the cache

#         with r9General.undoContext():
        with r9General.AnimationContext(eval_mode='anim', time=False, undo=True):
            cls._processed['mnodes'], cls._processed['mnode_internals'] = cls.metaNodes(offset, timerange=timerange, ripple=ripple)
            cls._processed['animcurves'] = cls.animCurves(offset, timerange=timerange, ripple=ripple)
            cls._processed['sound'] = cls.sound(offset, mode='Scene', timerange=timerange, ripple=ripple)
            cls._processed['animclips'] = cls.animClips(offset, mode='Scene', timerange=timerange, ripple=ripple)
            if timelines:
                cls.timelines(offset)

        print('Scene Offset Successfully')
        return cls._processed

    @classmethod
    def fromSelected(cls, offset, nodes=None, filterSettings=None, flocking=False,
                     randomize=False, timerange=None, ripple=True, mRigs=False, startfrm=False, currentSystem=False):
        '''
        Process the current selection list and offset as appropriate.

        :param offset: number of frames to offset
        :param nodes: nodes to offset (or root of the filterSettings)
        :param flocking: whether to successively increment nodes during offset
        :param randomize: whether to add a random factor to each successive nodes offset
        :param timerange: only offset times within a given timerange
        :param ripple: manage the upper range of data and ripple them with the offset
        :param mRigs: if True then the nodes to be used are resolved via mRig.getChildren but for all
            mRigs wired to the given nodes
        :param startfrm: this turns the offset arg into a new target start frame for the animation,
            calculating the offset for you such that timerange[0] starts at the offset frm value, only works if timerange is passed in
        :param filterSettings: this is a FilterSettings_Node object used to pass all
            the filter types into the FilterNode code. Internally the following is true:
        :param currentSystem: mRigs flag only: if True we check for the mSystemRoot attr (bool) on mNodes and if set,
            we skip the node and all childnodes from that node. Why?? The mSystsmRoot attr is a marker to denote the
            root of a given mRig system, by respecting this we clamp searches to the current system and prevent
            walking into the connected child sub-system. Primarily used in ProPack to stop facial nodes being
            returned and processed as part of the connected body rig.

            | settings.nodeTypes: list[] - search nodes of type
            | settings.searchAttrs: list[] - search nodes with Attrs of name
            | settings.searchPattern: list[] - search for a given nodeName searchPattern
            | settings.hierarchy: bool - process all children from the roots
            | settings.incRoots: bool - include the original root nodes in the filter
        '''
#         currentSystem = True
        if startfrm:
            if timerange:
                offset = offset - timerange[0]
                log.info('New Offset calculated based on given Start Frm and timerange : %s' % offset)
            else:
                log.warning('"startfrm" argument requires the "timeRange" argument to also be passed in, using offset as is was passed in! : %s' % offset)
        if logging_is_debug():
            log.debug('TimeOffset from Selected : offset=%s, flocking=%i, randomize=%i, timerange=%s, ripple:%s, startfrm=%s' %
                      (offset, flocking, randomize, str(timerange), ripple, startfrm))

        if not nodes:
            basenodes = cmds.ls(sl=True, l=True)
        else:
#             if not hasattr(nodes, '__iter__'):
            if r9General.is_basestring(nodes):
                basenodes = [nodes]
            else:
                basenodes = nodes
        cls._processed = {}  # clear the cache

        # deal with mNodes / mRigs
        # ======================================
        filtered = []
        mNodes = []  # all connected mNodes for the given rigs so we can timeOffset these correctly

        # New mrig section so that we can process rigs as entire entities for all the calls
        if mRigs:
            _mrigs = []
            for node in basenodes:
                # get directly connected mSystemRoots to the given node
                mrig = r9Meta.getConnectedMetaSystemRoot(node)
                if mrig and mrig not in _mrigs:
                    _mrigs.append(mrig)
                    if not currentSystem:
                        # PRO_PACK : extend those to child mRigs (facial connected to body as child)
                        _child_mrigs = mrig.getChildSystemRoots()
#                         _child_mrigs = mrig.getChildMetaNodes(walk=True, mInstances=['Pro_MetaRig','Pro_MetaRig_FacialUI'])
                        if _child_mrigs:
                            _mrigs.extend(_child_mrigs)

            # ensure a clean list
            _mrigs = list(set(_mrigs))

            if _mrigs:
                mNodes.extend(_mrigs)
                for rig in _mrigs:
                    _children = rig.getChildMetaNodes(walk=True, currentSystem=currentSystem)
                    for _child in _children:
                        if _child not in mNodes:
                            mNodes.append(_child)
                    filtered.extend(rig.getChildren())

        # process everything
        # ======================================
        elif filterSettings:
            filtered = FilterNode(basenodes, filterSettings).processFilter()
        else:
            filtered = basenodes

        if filtered:
#             with r9General.undoContext():
            with r9General.AnimationContext(eval_mode='anim', time=False, undo=True):
                if flocking or randomize:
                    cachedOffset = 0  # Cached last flocking value
                    increment = 0
                    for node in filtered:
                        if randomize and not flocking:
                            increment = random.uniform(0, offset)
                        if flocking and not randomize:
                            increment = cachedOffset + offset
                            cachedOffset += offset
                        if flocking and randomize:
                            rand = random.uniform(0, offset)
                            increment = cachedOffset + rand
                            cachedOffset += rand
                        cls._processed['animcurves'] = cls.animCurves(increment, node,
                                                                      timerange=timerange,
                                                                      ripple=ripple)
                        if logging_is_debug():
                            log.debug('animData randon/flock modified offset : %f on node: %s' % (increment, nodeNameStrip(node)))
                else:
                    cls._processed['mnodes'], cls._processed['mnode_internals'] = cls.metaNodes(offset, mNodes=mNodes,
                                                                                                timerange=timerange,
                                                                                                ripple=ripple)

                    cls._processed['animcurves'] = cls.animCurves(offset, nodes=filtered, timerange=timerange, ripple=ripple)

                    cls._processed['sound'] = cls.sound(offset, mode='Selected',
                                                        audioNodes=FilterNode().lsSearchNodeTypes('audio', filtered),
                                                        timerange=timerange,
                                                        ripple=ripple)

                    cls._processed['animclips'] = cls.animClips(offset, mode='Selected',
                                                                clips=FilterNode().lsSearchNodeTypes('animClip', filtered),
                                                                timerange=timerange,
                                                                ripple=ripple)
                log.info('Selected Nodes Offset Successfully')

                return cls._processed
        else:
            raise StandardError('Nothing selected or returned from the Hierarchy filter to offset')

    @classmethod
    def animCurves(cls, offset, nodes=None, timerange=None, ripple=True, safe=True, allow_ref=False):
        '''
        Shift Animation curves. If nodes are fed in to process then we do
        a number of aggressive searches to find all linked animation data.

        :param offset: amount to offset the curves
        :param nodes: nodes to offset if given
        :param timerange: if timerange given [start,end] then we cut the keys in that
            range before shifting associated keys. Now we could just use the
            keyframe(option='insert') BUT this has a MAJOR crash bug!
        :param ripple: manage the upper range of keys and ripple them with the offset
        :param safe: optional 'bool', only return animCurves which are safe to modify, this
            will strip out SetDrivens, Clips curves etc..
        :param allow_ref: if False and "safe" we remove all references animCurves, else we leave them in the return
        '''
        safeCurves = FilterNode.lsAnimCurves(nodes, safe=safe, allow_ref=allow_ref)
        curves_moved = []

        if safeCurves:
            log.debug('AnimCurve Offset = %s ============================' % offset)
            # log.debug(''.join([('offset: %s\n' % curve) for curve in safeCurves]))
            if timerange:
                rippleRange = (timerange[0], 1000000000)
                if offset > 0:
                    # if moving positive in time, cutchunk is from the upper timerange + offset
                    cutTimeBlock = (timerange[1] + 0.1, timerange[1] + offset)
                else:
                    # else it's from the lower timerange - offset
                    # cutTimeBlock=(timerange[0] + 0.1, timerange[0] - abs(offset + 1))
                    cutTimeBlock = (timerange[0] - 0.1, timerange[0] - abs(offset))  # corrections in the gap being created!!!
                log.debug('Cutting time range : %s>%s' % (cutTimeBlock[0], cutTimeBlock[1]))

            for curve in safeCurves:
                # bail if already processed
                if 'animcurves' in cls._processed and curve in cls._processed['animcurves']:
                    log.debug('skipping already processed animcurve : %s' % curve)
                    continue
                if 'mnode_internals' in cls._processed and curve in cls._processed['mnode_internals']:
                    log.debug('skipping already processed animcurve : %s' % curve)
                    continue
                try:
                    if timerange:
                        try:
                            if not ripple or offset < 0:
                                log.debug('cutting moveRange: %f > %f  : %s' % (cutTimeBlock[0], cutTimeBlock[1], curve))
                                cmds.cutKey(curve, time=cutTimeBlock)
                        except:
                            log.debug('unable to cut keys')
                        if ripple:
                            cmds.keyframe(curve, edit=True, r=True, timeChange=offset, time=rippleRange)
                        else:
                            cmds.keyframe(curve, edit=True, r=True, timeChange=offset, time=timerange)
                    else:
                        cmds.keyframe(curve, edit=True, r=True, timeChange=offset)
                    log.debug('offsetting: %s' % curve)
                    curves_moved.append(curve)
                except StandardError, err:
                    log.info('Failed to offset curves fully : %s' % curve)
                    log.debug(err)
            log.info('%i : AnimCurves were offset' % len(curves_moved))
        return curves_moved

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

    @classmethod
    def sound(cls, offset, mode='Scene', audioNodes=None, timerange=None, ripple=True):
        '''
        Offset Audio nodes.

        :param offset: amount to offset the sounds nodes by
        :param mode: either process entire scene or selected
        :param audioNodes: optional, given nodes to process
        :param timerange: optional timerange to process (outer bounds only)
        :param ripple: when shifting nodes ripple the offset to sounds after the range,
            if ripple=False we only shift audio that starts in the bounds of the timerange
        '''
        sounds_offset = []
        if mode == 'Scene':
            audioNodes = cmds.ls(type='audio')
        if audioNodes:
            log.debug('AudioNodes Offset ============================')
            for sound in audioNodes:
                try:
                    # bail if already processed
                    if 'sound' in cls._processed and sound in cls._processed['sound']:
                        log.debug('skipping already processed sound : %s' % sound)
                        continue
                    if 'mnode_internals' in cls._processed and sound in cls._processed['mnode_internals']:
                        log.debug('skipping already processed sound : %s' % sound)
                        continue

                    audioNode = r9Audio.AudioNode(sound)
                    if timerange:
                        if not audioNode.startFrame > timerange[0]:
                            log.info('Skipping Sound : %s > sound starts before the timerange begins' % sound)
                            continue
                        if audioNode.startFrame > timerange[1] and not ripple:
                            log.info('Skipping Sound : %s > sound starts after the timerange ends' % sound)
                            continue
                    audioNode.offsetTime(offset)
                    sounds_offset.append(sound)
                    log.debug('offset : %s' % sound)
                except:
                    log.debug('Failed to offset audio node %s' % sound)
            log.info('%i : SoundNodes were offset' % len(sounds_offset))
        return sounds_offset

    @classmethod
    def animClips(cls, offset, mode='Scene', clips=None, timerange=None, ripple=True):
        '''
        Offset Trax Clips

        :param offset: amount to offset the sounds nodes by
        :param mode: either process entire scene or selected
        :param clips: optional, given clips to offset
        :param timerange: optional timerange to process (outer bounds only)
        :param ripple: when shifting nodes ripple the offset to clips after the range,
            if ripple=False we only shift clips that starts in tghe bounds of the timerange
        '''
        clips_moved = []
        if mode == 'Scene':
            clips = cmds.ls(type='animClip')
        if clips:
            log.debug('Clips Offset ============================')
            for clip in clips:
                try:
                    # bail if already processed
                    if 'animclips' in cls._processed and clip in cls._processed['animclips']:
                        log.debug('skipping already processed animclip : %s' % clip)
                        continue
                    if 'mnode_internals' in cls._processed and clip in cls._processed['mnode_internals']:
                        log.debug('skipping already processed animclip : %s' % clip)
                        continue

                    startFrame = cmds.getAttr('%s.startFrame' % clip)
                    if timerange:
                        if not startFrame > timerange[0]:
                            log.info('Skipping Clip : %s > clip starts before the timerange begins' % clip)
                            continue
                        if startFrame > timerange[1] and not ripple:
                            log.info('Skipping Clip : %s > clip starts after the timerange begins' % clip)
                            continue
                    cmds.setAttr('%s.startFrame' % clip, startFrame + offset)
                    clips_moved.append(clip)
                    log.debug('offset : %s' % clip)
                except:
                    pass
            log.info('%i : AnimClips were offset' % len(clips_moved))
        return clips_moved

    @classmethod
    def metaNodes(cls, offset, timerange=None, ripple=True, mNodes=None):
        '''
        Offset special handling for MetaNodes. Inspect the metaNode and see if
        the 'timeOffset' method has been implemented and if so, call it.

        :param offset: amount to offset the sounds nodes by
        :param timerange: optional timerange to process (outer bounds only)
        :param ripple: when shifting nodes ripple the offset to clips after the range,
            if ripple=False we only shift clips that starts in the bounds of the timerange

        .. note::
            each timeOffset function implemented within a MetaClass must now return ALL Maya nodes (dag path)
            that were processed by it (other than itself) so that these can be flagged as processed and
            removed from the standard nodeType handlers in the TimeOffset class
        '''
        mNodes_offset = []
        mNodes_internal_offset = []  # nodes OTHER than the mNode itself that the function offset
        if not mNodes:
            mNodes = r9Meta.getMetaNodes()
        if mNodes:
            log.debug('MetaData Offset ============================')
            for mNode in set(mNodes):
                # bail if already processed
                if 'mnode' in cls._processed and mNode.mNode in cls._processed['mnode']:
                    log.debug('skipping already processed mNode : %s' % mNode)
                    continue

                if 'timeOffset' in dir(mNode) and r9General.is_callable(getattr(mNode, 'timeOffset')):
                    mNodes_internal_offset.extend(mNode.timeOffset(offset, timerange=timerange, ripple=ripple, cache_object=cls._processed) or [])
                    mNodes_offset.append(mNode.mNode)  # set to cache as dag path to make sure we cover duplicate systems
                log.debug('offset mnode : %s' % mNode)
            if mNodes_offset:
                log.info('================================')
                log.info('timeOffset generic mClass called')
                log.info('================================')
            for i, node in enumerate(mNodes_offset):
                log.info('%i : MetaData %s.timeOffset : called %s ' % (i, node.__class__.__name__, node))
        return mNodes_offset, mNodes_internal_offset

# -------------------------------------------------------------------------------------
# Math functions ----
# -------------------------------------------------------------------------------------

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
                if logging_is_debug():
                    log.debug('compare passed with gimbal : %f == %f : diff = %f' % (a, b, mod))
                return True
            elif abs(180.0 - mod) < tolerance:
                if logging_is_debug():
                    log.debug('compare passed with gimbal 180 : %f == %f : diff = %f' % (a, b, abs(180 - mod)))
                return True
            elif abs(90.0 - mod) < tolerance:
                if logging_is_debug():
                    log.debug('compare passed with gimbal 90 : %f == %f diff = %f' % (a, b, abs(90.0 - mod)))
                return True
            if logging_is_debug():
                log.debug('compare with gimbal failed against mod 180: best diff :%f' % (abs(180.0 - mod)))
                log.debug('compare with gimbal failed against mod 90: best diff :%f' % (abs(90.0 - mod)))
    if logging_is_debug():
        log.debug('float is out of tolerance : %f - %f == %f' % (a, b, abs(a - b)))
    return False

def valueToMappedRange(value, currentMin, currentMax, givenMin, givenMax):
    '''
    Acts like the setRange node but code side
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

# def ui_dpi_scaling_factors(width=False, height=False, factor=False):
#     '''
#     this is a bodge really, but needed to remap the UI scales to 4k setups in some of
#     the core StudioPack UI's. This basically uses a scaling factor based on the DPI of
#     the screen setups. This is also used in ProPack to control some of the widget sizes
#     so we can consistently scale icon widgets as expected.
#     '''
#     is_4k, _, _, ppi = r9Setup.maya_screen_mapping()
#
#     _factor = 1
#
#     if int(ppi) > 290: # 300% resolution scaling
#         _factor = 2.15
#     elif int(ppi) >= 240: # 250% resolution scaling
#         _factor = 2.05
#     elif int(ppi) >= 140:  # 150% resolution scaling
#         _factor = 1.5
#
#     if factor:
#         return _factor
#
#     _width = width * _factor
#     _height = height * _factor
#
#     if width and height:
#         return _width, _height
#     elif width:
#         return _width
#     elif height:
#         return _height
#
# #    if is_4k:
#         # base size mapping setups
# #        if width:
# #            _width = max(valueToMappedRange(width, 500, 7673, 333, 5115), 100)
# #        if height:
# #           _height = max(valueToMappedRange(height, 355, 2021, 65, 1175), 100)
#
# #        # now multiply by the dpi, based on 144.0dpi being default
# #        _width = _width * (144.0 / ppi)
# #        _height = _height * (144.0 / ppi)


def timeIsInRange(baseRange=(), testRange=(), start_inRange=True, end_inRange=True):
    '''
    test that a given testRange [start,end], falls within the bounds of a baseRange [start,end]
    Used to test if timeRanges fall within a baseRange

    :param baseRange: base time range to test against
    :param testRange: range to test against the baseRange, do these times fall within the baseRange?
    :param start_inRange: check is the testRange[0] value falls fully in the baseRange
    :param end_inRange: check is the testRange[1] value falls fully in the baseRange

    .. note::
        if you pass in baseRange as (None, 100) then we only validate against the end time regardless of the flags.
        if we pass in baseRange as (10, None) we only validate against the start time regardless of the flags.
        else we validate that testRange is fully within the baseRanges times
    '''

    if baseRange[1] is None:
        if testRange[0] >= baseRange[0]:
            return True
        else:
            return False
    if baseRange[0] is None:
        if testRange[1] <= baseRange[1]:
            return True
        else:
            return False
    start = False
    end = False
    if start_inRange:
        if testRange[0] >= baseRange[0] and testRange[0] <= baseRange[1]:
            start = True
        else:
            start = False
        if not end_inRange:
            return start
    if end_inRange:
        if testRange[1] <= baseRange[1] and testRange[1] >= baseRange[0]:
            end = True
        else:
            end = False
        if not start_inRange:
            return end
    return all([start, end])


def distanceBetween(nodeA, nodeB):
    '''
    simple calculation to return the distance between 2 objects
    '''
    x1, y1, z1, _, _, _ = cmds.xform(nodeA, q=True, ws=True, piv=True)
    x2, y2, z2, _, _, _ = cmds.xform(nodeB, q=True, ws=True, piv=True)
    return math.sqrt(math.pow((x1 - x2), 2) + math.pow((y1 - y2), 2) + math.pow((z1 - z2), 2))

def convertUnits_internalToUI(value, unit):
    '''
    convert units to Maya's internal 'cm' unit
    for the API to use when loading linear data
    '''
    if unit == 'centimeter':
        return value
    elif unit == 'meter':
        return value * 100.0000000
    elif unit == 'inch':
        return value * 2.540000000
    elif unit == 'foot':
        return value * 30.480000000
    elif unit == 'yard':
        return value * 91.440000000
    elif unit == 'millimeter':
        return value * 0.100000000
    elif unit == 'km':
        return value * 100000.000000000

def convertUnits_uiToInternal(value, unit):
    '''
    convert units from Maya's internal / base 'cm'
    to a given unit, multiplying up to suit
    '''
    if unit == 'centimeter':
        return value
    elif unit == 'meter':
        return value * 0.010000000
    elif unit == 'inch':
        return value * 0.393700787
    elif unit == 'foot':
        return value * 0.032808399
    elif unit == 'yard':
        return value * 0.010936133
    elif unit == 'millimeter':
        return value * 10.000000000
    elif unit == 'km':
        return value * 0.000010000

class MatrixOffset(object):

    '''
    Given 2 transforms calculate the difference as a Matrix and
    apply that as an offset matrix to a given list of nodes.

    >>> matrixOffset = MatrixOffset()
    >>> matrixOffset.setOffsetMatrix('inputA','inputB')
    >>> applyOffsetMatrixToNodes(nodesToOffset)
    '''

    def __init__(self):
        self.CachedData = []
        self.OffsetMatrix = OpenMaya.MMatrix

    @staticmethod
    def get_MDagPath(node):
        dagpath = OpenMaya.MDagPath()
        selList = OpenMaya.MSelectionList()
        selList.add(node)
        selList.getDagPath(0, dagpath)
        return dagpath

    def setOffsetMatrix(self, inputA, inputB):
        '''
        from 2 transform return an offsetMatrix between them

        :param inputA: MayaNode A
        :param inputB: MayaNode B
        '''
        DagNodeA = MatrixOffset.get_MDagPath(inputA)
        DagNodeB = MatrixOffset.get_MDagPath(inputB)

        initialMatrix = DagNodeA.inclusiveMatrix()
        newMatrix = DagNodeB.inclusiveMatrix()
        # get the difference, by inversing we put newMatrix in the same space
        self.OffsetMatrix = initialMatrix.inverse() * newMatrix
        return self.OffsetMatrix

    @classmethod
    def nodesAreEquivalent(cls, inputA, inputB):
        '''
        do the 2 nodes passed in have an equivalant inclusiveMatrix? ie, are they
        in the same worldSpace!

        :param inputA: nodeA
        :param inputB: nodeB
        '''
        DagNodeA = MatrixOffset.get_MDagPath(inputA)
        DagNodeB = MatrixOffset.get_MDagPath(inputB)

        initialMatrix = DagNodeA.inclusiveMatrix()
        newMatrix = DagNodeB.inclusiveMatrix()
        return initialMatrix.isEquivalent(newMatrix)

    def __cacheCurrentData(self, nodes):
        '''
        Return a list of tuples containing the cached state of the nodes
        [(node, MDagpath, worldMatrix, parentInverseMatrix)]
        '''
        self.CachedData = []
        for node in nodes:
            parentInverseMatrix = None
            dag = MatrixOffset.get_MDagPath(node)
            currentMatrix = dag.inclusiveMatrix()
            parents = cmds.listRelatives(node, p=True, f=True)
            scalePivot = cmds.getAttr('%s.scalePivot' % node)
            rotatePivot = cmds.getAttr('%s.rotatePivot' % node)
            if parents:
                parentNode = MatrixOffset.get_MDagPath(parents[0])
                parentInverseMatrix = parentNode.inclusiveMatrixInverse()
            self.CachedData.append((node, dag, currentMatrix, parentInverseMatrix, (rotatePivot, scalePivot)))
        return self.CachedData

    def applyOffsetTransformsToNodes(self, nodes, matrix=None, inversed=False):
        '''
        simple move function called to shift the given nodes against the offsetMatrix
        '''
        objs = cmds.ls(sl=True, l=True)
        cmds.select(nodes)
        offsetMatrix = self.OffsetMatrix
        if matrix:
            offsetMatrix = matrix
        if inversed:
            offsetMatrix = offsetMatrix.inverse()

        # simple apply offset via the standard move/rotate operators....
        cmds.move(offsetMatrix(3, 0), offsetMatrix(3, 1), offsetMatrix(3, 2), r=True)

#         mTransformMtx = OpenMaya.MTransformationMatrix(self.OffsetMatrix)
#         eulerRot = mTransformMtx.eulerRotation()  # MEulerRotation
#         angles = [math.degrees(angle) for angle in (eulerRot.x, eulerRot.y, eulerRot.z)]
#         cmds.rotate(angles[0], angles[1], angles[2], r=True)

        if objs:
            cmds.select(objs)

    def applyOffsetMatrixToNodes(self, nodes, matrix=None, inversed=False):
        '''
        offset all the given nodes by the given MMatrix object

        :param nodes: Nodes to apply the offset Matrix too
        :param matrix: Optional OpenMaya.MMatrix to transform the data by

        .. note::
            this doesn't deal with joints as for that we need to rotate by the inverse
            of the jointOrient matrix, after the rotation matrix
        '''
        offsetMatrix = self.OffsetMatrix
        if matrix:
            offsetMatrix = matrix
        if not type(nodes) == list:
            nodes = [nodes]
        if inversed:
            offsetMatrix = offsetMatrix.inverse()
        for node in nodes:
            if not cmds.objExists(node):
                log.warning('given node was not found! : %s' % node)
        for node, dag, initialMatrix, parentInverseMatrix, rotScal in self.__cacheCurrentData(nodes):
            try:
                if parentInverseMatrix:
                    if not initialMatrix.isEquivalent(dag.inclusiveMatrix()):
                        log.info('Dag has already been modified by previous parent node :  %s' % node)
                        continue
                    else:
                        # multiply the offset by the inverse ParentMatrix to put it into the correct space
                        OpenMaya.MFnTransform(dag).set(OpenMaya.MTransformationMatrix(initialMatrix * parentInverseMatrix * offsetMatrix.inverse()))
                        # cmds.setAttr('%s.rotatePivot' % node, rotScal[0][0][0], rotScal[0][0][1], rotScal[0][0][2])   ?? why were we doing this ??
                        # cmds.setAttr('%s.scalePivot' % node, rotScal[1][0][0], rotScal[1][0][1], rotScal[1][0][2])   ?? why were we doing this ??
                else:
                    OpenMaya.MFnTransform(dag).set(OpenMaya.MTransformationMatrix(initialMatrix * offsetMatrix.inverse()))
                    # cmds.setAttr('%s.rotatePivot' % node, rotScal[0][0][0], rotScal[0][0][1], rotScal[0][0][2])   ?? why were we doing this ??
                    # cmds.setAttr('%s.scalePivot' % node, rotScal[1][0][0], rotScal[1][0][1], rotScal[1][0][2])   ?? why were we doing this ??
            except:
                log.warning('Failed to apply offset Matrix too : %s' % node)
