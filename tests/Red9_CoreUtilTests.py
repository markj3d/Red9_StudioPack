'''
------------------------------------------
Red9 Studio Pack: Maya Pipeline Solutions
Author: Mark Jackson
email: rednineinfo@gmail.com

Red9 blog : http://red9-consultancy.blogspot.co.uk/
MarkJ blog: http://markj3d.blogspot.co.uk
------------------------------------------

This is the main unittest for the Red9_CoreUtils module and a good
example of what's expected and what the systems can do on simple data
================================================================

'''


import maya.standalone
maya.standalone.initialize(name='python')

import maya.cmds as cmds
import os

import Red9.core.Red9_CoreUtils as r9Core
import Red9.startup.setup as r9Setup
# r9Setup.boot_client_projects(batchclients=['Testing'])

# force the upAxis, just in case
r9Setup.mayaUpAxis('y')

class Test_FilterSettings():
    def setup(self):
        self.filter = r9Core.FilterNode_Settings()

    def teardown(self):
        self.filter.resetFilters()

    def test_filterSettings(self):

        assert not self.filter.filterIsActive()
        assert self.filter.nodeTypes == []
        assert self.filter.searchAttrs == []
        assert self.filter.searchPattern == []
        assert self.filter.hierarchy == False
        assert self.filter.filterPriority == []
        assert self.filter.incRoots == True
        assert self.filter.metaRig == False
        assert self.filter.transformClamp == True

        self.filter.nodeTypes = ['nurbsCurves', 'joint']
        assert self.filter.filterIsActive()
        self.filter.resetFilters()
        assert not self.filter.filterIsActive()

        self.filter.searchAttrs = ['new', 'attr']
        assert self.filter.filterIsActive()
        self.filter.resetFilters()
        assert not self.filter.filterIsActive()

        self.filter.searchPattern = ['CTRL', 'TEST']
        assert self.filter.filterIsActive()
        self.filter.resetFilters()
        assert not self.filter.filterIsActive()

        self.filter.hierarchy = True
        assert self.filter.filterIsActive()
        self.filter.resetFilters()
        assert not self.filter.filterIsActive()

        self.filter.metaRig = True
        assert self.filter.filterIsActive()
        self.filter.resetFilters()
        assert not self.filter.filterIsActive()

    def test_readWrite(self):
        '''
        Test the read / write calls
        '''
        filterFile = os.path.join(os.path.dirname(__file__), 'testFiles', 'filterTest.cfg')
        if os.path.exists(filterFile):
            os.remove(filterFile)
        self.filter.nodeTypes = ['nurbsCurves']
        self.filter.searchAttrs = ['myAttr']
        self.filter.searchPattern = 'anim$'
        self.filter.hierarchy = False
        self.filter.filterPriority = ['m_spine_Root_anim$', 'rig_spine_0_skin_Hips_anim$', 'rig_spine_0_skin_Shoulders_anim$']
        self.filter.incRoots = True
        self.filter.metaRig = True
        self.filter.transformClamp = True

        self.filter.write(filterFile)
        assert os.path.exists(filterFile)
        self.filter.resetFilters()
        assert not self.filter.filterIsActive()

        self.filter.read(filterFile)
        assert self.filter.filterIsActive()
        assert self.filter.nodeTypes == ['nurbsCurves']
        assert self.filter.searchAttrs == ['myAttr']
        assert self.filter.searchPattern == 'anim$'
        assert self.filter.hierarchy == False
        assert self.filter.filterPriority == ['m_spine_Root_anim$', 'rig_spine_0_skin_Hips_anim$', 'rig_spine_0_skin_Shoulders_anim$']
        assert self.filter.incRoots == True
        assert self.filter.metaRig == True
        assert self.filter.transformClamp == True

        self.filter.resetFilters()
        assert not self.filter.filterIsActive()
        assert not self.filter.metaRig
        # read by only giving the short config name, no path
        self.filter.read('Red9_DevRig.cfg')
        assert self.filter.filterIsActive()
        assert self.filter.metaRig


class Test_FilterNode():

    def setup(self):
        cmds.file(os.path.join(r9Setup.red9ModulePath(), 'tests', 'testFiles', 'FilterNode_baseTests.ma'), open=True, f=True)
        self.filterNode = r9Core.FilterNode(['World_Root'])
        assert self.filterNode.rootNodes == ['World_Root']

    def teardown(self):
        self.filterNode.settings.resetFilters()

    def test_SearchNodeTypes(self):
        self.filterNode.settings.nodeTypes = ['joint']
        assert self.filterNode.ProcessFilter() == ['|World_Root|joint1|joint2_Ctrl|joint3_AttrMarked',
                                            '|World_Root|joint1|joint2_Ctrl',
                                            '|World_Root|joint1',
                                            '|World_Root|joint4|joint5_AttrMarked|joint6_Ctrl|joint7_AttrMarked|joint8|joint9',
                                            '|World_Root|joint4|joint5_AttrMarked|joint6_Ctrl|joint7_AttrMarked|joint8',
                                            '|World_Root|joint4|joint5_AttrMarked|joint6_Ctrl|joint7_AttrMarked',
                                            '|World_Root|joint4|joint5_AttrMarked|joint6_Ctrl',
                                            '|World_Root|joint4|joint5_AttrMarked',
                                            '|World_Root|joint4']

        self.filterNode.settings.nodeTypes = ['nurbsCurve']
        assert self.filterNode.ProcessFilter() == ['|World_Root|Spine_Ctrl|R_Wrist_Ctrl',
                                            '|World_Root|Spine_Ctrl|L_Wrist_Ctrl',
                                            '|World_Root|Spine_Ctrl|L_Foot_MarkerAttr_Ctrl',
                                            '|World_Root|Spine_Ctrl',
                                            '|World_Root|nurbsCircle1']

        self.filterNode.settings.nodeTypes = ['nurbsCurve', 'locator']
        assert self.filterNode.ProcessFilter() == ['|World_Root|IK_Ctrl',
                                            '|World_Root|Spine_Ctrl|L_Pole_Ctrl',
                                            '|World_Root|Spine_Ctrl|R_Pole_Ctrl',
                                            '|World_Root|Spine_Ctrl|R_Wrist_Ctrl|R_Pole_AttrMarked_Ctrl',
                                            '|World_Root|Spine_Ctrl|R_Wrist_Ctrl',
                                            '|World_Root|Spine_Ctrl|L_Wrist_Ctrl|L_Pole_thingy',
                                            '|World_Root|Spine_Ctrl|L_Wrist_Ctrl',
                                            '|World_Root|Spine_Ctrl|L_Foot_MarkerAttr_Ctrl',
                                            '|World_Root|Spine_Ctrl',
                                            '|World_Root|nurbsCircle1']

        self.filterNode.settings.nodeTypes = ['blendShape']
        assert self.filterNode.ProcessFilter() == ['ffff']

    def test_SearchPattern(self):
        self.filterNode.settings.nodeTypes = ['nurbsCurve', 'locator']
        self.filterNode.settings.searchPattern = 'Ctrl'
        assert self.filterNode.ProcessFilter() == ['|World_Root|IK_Ctrl',
                                             '|World_Root|Spine_Ctrl|L_Pole_Ctrl',
                                             '|World_Root|Spine_Ctrl|R_Pole_Ctrl',
                                             '|World_Root|Spine_Ctrl|R_Wrist_Ctrl|R_Pole_AttrMarked_Ctrl',
                                             '|World_Root|Spine_Ctrl|R_Wrist_Ctrl',
                                             '|World_Root|Spine_Ctrl|L_Wrist_Ctrl',
                                             '|World_Root|Spine_Ctrl|L_Foot_MarkerAttr_Ctrl',
                                             '|World_Root|Spine_Ctrl']

        # test the 'NOT:' operator
        self.filterNode.settings.searchPattern = ['Ctrl', 'NOT:Pole']
        assert self.filterNode.ProcessFilter() == ['|World_Root|IK_Ctrl',
                                             '|World_Root|Spine_Ctrl|R_Wrist_Ctrl',
                                             '|World_Root|Spine_Ctrl|L_Wrist_Ctrl',
                                             '|World_Root|Spine_Ctrl|L_Foot_MarkerAttr_Ctrl',
                                             '|World_Root|Spine_Ctrl']
        # test the whiteSpace handler
        self.filterNode.settings.searchPattern = ['Ctrl ', ' NOT:Pole ']
        assert self.filterNode.ProcessFilter() == ['|World_Root|IK_Ctrl',
                                             '|World_Root|Spine_Ctrl|R_Wrist_Ctrl',
                                             '|World_Root|Spine_Ctrl|L_Wrist_Ctrl',
                                             '|World_Root|Spine_Ctrl|L_Foot_MarkerAttr_Ctrl',
                                             '|World_Root|Spine_Ctrl']

        # test just using NOT: as an excluder
        self.filterNode.settings.searchPattern = ['NOT:Pole']
        assert self.filterNode.ProcessFilter() == ['|World_Root|IK_Ctrl',
                                             '|World_Root|Spine_Ctrl|R_Wrist_Ctrl',
                                             '|World_Root|Spine_Ctrl|L_Wrist_Ctrl',
                                             '|World_Root|Spine_Ctrl|L_Foot_MarkerAttr_Ctrl',
                                             '|World_Root|Spine_Ctrl',
                                             '|World_Root|nurbsCircle1']

    def test_SearchAttrs(self):
        # basic hasAttr
        self.filterNode.settings.searchAttrs = ['MarkerAttr']
        assert self.filterNode.ProcessFilter() == ['|World_Root|joint1|joint2_Ctrl|joint3_AttrMarked',
                                             '|World_Root|joint4|joint5_AttrMarked|joint6_Ctrl|joint7_AttrMarked',
                                             '|World_Root|joint4|joint5_AttrMarked',
                                             '|World_Root|Spine_Ctrl|L_Foot_MarkerAttr_Ctrl',
                                             '|World_Root|Spine_Ctrl|R_Wrist_Ctrl|R_Pole_AttrMarked_Ctrl',
                                             '|World_Root|pCube4_AttrMarked']
        # has attr with matching value (STR test)
        self.filterNode.settings.searchAttrs = ['MarkerAttr=right']
        assert self.filterNode.ProcessFilter() == ['|World_Root|Spine_Ctrl|R_Wrist_Ctrl|R_Pole_AttrMarked_Ctrl',
                                                  '|World_Root|pCube4_AttrMarked']
        # test whiteSpace Handler
        self.filterNode.settings.searchAttrs = ['MarkerAttr = right']
        assert self.filterNode.ProcessFilter() == ['|World_Root|Spine_Ctrl|R_Wrist_Ctrl|R_Pole_AttrMarked_Ctrl',
                                                  '|World_Root|pCube4_AttrMarked']
        self.filterNode.settings.searchAttrs = [' MarkerAttr =right ']
        assert self.filterNode.ProcessFilter() == ['|World_Root|Spine_Ctrl|R_Wrist_Ctrl|R_Pole_AttrMarked_Ctrl',
                                                  '|World_Root|pCube4_AttrMarked']
        # has attr but exclude is attr if value equals
        self.filterNode.settings.searchAttrs = ['MarkerAttr', 'NOT:MarkerAttr=left']
        assert self.filterNode.ProcessFilter() == ['|World_Root|joint4|joint5_AttrMarked',
                                            '|World_Root|Spine_Ctrl|L_Foot_MarkerAttr_Ctrl',
                                            '|World_Root|Spine_Ctrl|R_Wrist_Ctrl|R_Pole_AttrMarked_Ctrl',
                                            '|World_Root|pCube4_AttrMarked']

        # BOOLS  ---------------------------
        self.filterNode.settings.searchAttrs = ['export']
        assert self.filterNode.ProcessFilter() == ['|World_Root|camera1',
                                                 '|World_Root|camera2']
        # has attr with matching Value (BOOL test)
        self.filterNode.settings.searchAttrs = ['export=True']
        assert self.filterNode.ProcessFilter() == ['|World_Root|camera2']
        # exclude if hasAttr and attr value equals
        self.filterNode.settings.searchAttrs = ['NOT:export=True']
        self.filterNode.settings.nodeTypes = ['camera']  # not so I only want a few test nodes
        assert self.filterNode.ProcessFilter() == ['|World_Root|camera1']
        self.filterNode.settings.nodeTypes = []

        # FLOATS  ----------------------------
        self.filterNode.settings.searchAttrs = ['floatAttr']
        assert self.filterNode.ProcessFilter() == ['|World_Root|Spine_Ctrl|R_Pole_Ctrl',
                                                 '|World_Root|Spine_Ctrl|L_Pole_Ctrl']
        # has attr with matching Value (FLOAT test) tolerance internally is 0.01
        self.filterNode.settings.searchAttrs = ['floatAttr=2.533']
        assert self.filterNode.ProcessFilter() == ['|World_Root|Spine_Ctrl|R_Pole_Ctrl']
        # has attr with matching Value (FLOAT test) out of tolerance
        self.filterNode.settings.searchAttrs = ['floatAttr=2.5']
        assert not self.filterNode.ProcessFilter()

        self.filterNode.settings.searchAttrs = ['NOT:floatAttr=2.533', 'floatAttr']
        assert self.filterNode.ProcessFilter() == ['|World_Root|Spine_Ctrl|L_Pole_Ctrl']

        # COMPLEX ----------------------------
        self.filterNode.settings.searchAttrs = ['MarkerAttr', 'NOT:MarkerAttr=left', 'export=True']
        assert self.filterNode.ProcessFilter() == ['|World_Root|joint4|joint5_AttrMarked',
                                                 '|World_Root|Spine_Ctrl|L_Foot_MarkerAttr_Ctrl',
                                                 '|World_Root|Spine_Ctrl|R_Wrist_Ctrl|R_Pole_AttrMarked_Ctrl',
                                                 '|World_Root|camera2', u'|World_Root|pCube4_AttrMarked']


    def test_ComplexMixedFilter(self):

        # nodetype + searchAttr
        self.filterNode.settings.nodeTypes = ['locator']
        self.filterNode.settings.searchAttrs = ['MarkerAttr']
        assert self.filterNode.ProcessFilter() == ['|World_Root|Spine_Ctrl|R_Wrist_Ctrl|R_Pole_AttrMarked_Ctrl']

        # build a full intersection
        self.filterNode.settings.resetFilters()
        self.filterNode.settings.nodeTypes = ['joint', 'locator', 'mesh']
        assert self.filterNode.ProcessFilter() == ['|World_Root|IK_Ctrl',
                                               '|World_Root|pCube4_AttrMarked|pCube5',
                                               '|World_Root|pCube4_AttrMarked',
                                               '|World_Root|Spine_Ctrl|L_Pole_Ctrl',
                                               '|World_Root|Spine_Ctrl|R_Pole_Ctrl',
                                               '|World_Root|Spine_Ctrl|R_Wrist_Ctrl|R_Pole_AttrMarked_Ctrl|pCube1',
                                               '|World_Root|Spine_Ctrl|R_Wrist_Ctrl|R_Pole_AttrMarked_Ctrl',
                                               '|World_Root|Spine_Ctrl|L_Wrist_Ctrl|L_Pole_thingy',
                                               '|World_Root|Spine_Ctrl|L_Foot_MarkerAttr_Ctrl|pCube2',
                                               '|World_Root|joint4|joint5_AttrMarked|joint6_Ctrl|pCube3',
                                               '|World_Root|joint1|joint2_Ctrl|joint3_AttrMarked',
                                               '|World_Root|joint1|joint2_Ctrl',
                                               '|World_Root|joint1',
                                               '|World_Root|joint4|joint5_AttrMarked|joint6_Ctrl|joint7_AttrMarked|joint8|joint9',
                                               '|World_Root|joint4|joint5_AttrMarked|joint6_Ctrl|joint7_AttrMarked|joint8',
                                               '|World_Root|joint4|joint5_AttrMarked|joint6_Ctrl|joint7_AttrMarked',
                                               '|World_Root|joint4|joint5_AttrMarked|joint6_Ctrl',
                                               '|World_Root|joint4|joint5_AttrMarked',
                                               '|World_Root|joint4']
        # add searchAttr and intersect
        self.filterNode.settings.searchAttrs = ['MarkerAttr']
        assert self.filterNode.ProcessFilter() == ['|World_Root|pCube4_AttrMarked',
                                                 '|World_Root|Spine_Ctrl|R_Wrist_Ctrl|R_Pole_AttrMarked_Ctrl',
                                                 '|World_Root|joint1|joint2_Ctrl|joint3_AttrMarked',
                                                 '|World_Root|joint4|joint5_AttrMarked|joint6_Ctrl|joint7_AttrMarked',
                                                 '|World_Root|joint4|joint5_AttrMarked']
        # add searchPattern and intersect
        self.filterNode.settings.searchPattern = ['Cube']
        assert self.filterNode.ProcessFilter() == ['|World_Root|pCube4_AttrMarked']

    def test_WorldFilter(self):
        '''
        No rootNode so processing at World/Scene level
        '''
        self.filterNode.rootNodes = []

        self.filterNode.settings.nodeTypes = ['blendShape']
        assert self.filterNode.ProcessFilter() == ['NewBlend', 'ffff']

        self.filterNode.settings.nodeTypes = ['mesh']
        assert self.filterNode.ProcessFilter() == ['|World_Root|pCube4_AttrMarked|pCube5',
                                                '|World_Root2_chSet|pCube4_AttrMarked_Bingo|pCube5',
                                                '|World_Root|joint4|joint5_AttrMarked|joint6_Ctrl|pCube3',
                                                '|World_Root2_chSet|joint4|joint5_AttrMarked|joint6_Ctrl|pCube3',
                                                '|World_Root|Spine_Ctrl|L_Foot_MarkerAttr_Ctrl|pCube2',
                                                '|World_Root2_chSet|Spine_Ctrl|L_Foot_MarkerAttr_Ctrl|pCube2',
                                                '|World_Root2_chSet|pCube6',
                                                '|World_Root|Spine_Ctrl|R_Wrist_Ctrl|R_Pole_AttrMarked_Ctrl|pCube1',
                                                '|World_Root2_chSet|Spine_Ctrl|R_Wrist_Ctrl|R_Pole_AttrMarked_Ctrl|pCube1',
                                                '|World_Root2_chSet|pCube4_AttrMarked_Bingo',
                                                '|World_Root|pCube4_AttrMarked']

        self.filterNode.settings.searchAttrs = ['MarkerAttr']
        assert self.filterNode.ProcessFilter() == ['|World_Root2_chSet|pCube4_AttrMarked_Bingo',
                                                 '|World_Root|pCube4_AttrMarked']
        self.filterNode.settings.searchPattern = ['Bingo']
        assert self.filterNode.ProcessFilter() == ['|World_Root2_chSet|pCube4_AttrMarked_Bingo']


    def test_CharacterSetHandler(self):
        # reset the rootNode to be the chSet and test the chSet hierarchy handler
        self.filterNode.settings.resetFilters()
        self.filterNode.rootNodes = ['TestChSet']
        self.filterNode.settings.hierarchy = True

        # FAILS: as the lsCharacterMembers when run in the tests doesn't return a consistent
        # order, yet in practice in Maya it does????
        for n in self.filterNode.ProcessFilter():
            print n
        assert sorted(self.filterNode.ProcessFilter()) == sorted(['|World_Root2_chSet|nurbsCircle1',
                                                 '|World_Root2_chSet|Spine_Ctrl',
                                                  '|World_Root2_chSet|Spine_Ctrl|L_Foot_MarkerAttr_Ctrl',
                                                  '|World_Root2_chSet|Spine_Ctrl|L_Wrist_Ctrl',
                                                  '|World_Root2_chSet|Spine_Ctrl|R_Wrist_Ctrl',
                                                  '|World_Root2_chSet|Spine_Ctrl|R_Pole_Ctrl',
                                                  '|World_Root2_chSet|Spine_Ctrl|L_Pole_Ctrl',
                                                  '|World_Root2_chSet|pCube4_AttrMarked_Bingo',
                                                  '|World_Root2_chSet|joint1|joint2_Ctrl',
                                                  '|World_Root2_chSet|joint4|joint5_AttrMarked'])

        self.filterNode.settings.resetFilters()
        self.filterNode.settings.searchAttrs = ['MarkerAttr']
        assert sorted(self.filterNode.ProcessFilter()) == sorted(['|World_Root2_chSet|Spine_Ctrl|L_Foot_MarkerAttr_Ctrl',
                                            '|World_Root2_chSet|pCube4_AttrMarked_Bingo',
                                            '|World_Root2_chSet|joint4|joint5_AttrMarked'])

    def test_CharacterSubSetTest(self):
        # TODO: Fill Test
        pass

    def test_SelectionSetHandler(self):
        # TODO: Fill Test
        pass

    def test_AnimCurveHandler(self):
        # TODO: Fill Test
        pass

    def test_MetaRig(self):
        # TODO: Fill Test
        pass

    def test_FilterPriority(self):
        # assert the unprioritized list
        self.filterNode.settings.nodeTypes = ['joint', 'locator', 'mesh']
        self.filterNode.settings.searchAttrs = ['MarkerAttr']
        assert self.filterNode.ProcessFilter() == ['|World_Root|pCube4_AttrMarked',
                                            '|World_Root|Spine_Ctrl|R_Wrist_Ctrl|R_Pole_AttrMarked_Ctrl',
                                            '|World_Root|joint1|joint2_Ctrl|joint3_AttrMarked',
                                            '|World_Root|joint4|joint5_AttrMarked|joint6_Ctrl|joint7_AttrMarked',
                                            '|World_Root|joint4|joint5_AttrMarked']
        # now add the priority filter in and test
        self.filterNode.settings.resetFilters()
        self.filterNode.settings.nodeTypes = ['joint', 'locator', 'mesh']
        self.filterNode.settings.searchAttrs = ['MarkerAttr']
        self.filterNode.settings.filterPriority = ['R_Pole_AttrMarked_Ctrl', 'joint5_AttrMarked']
        assert self.filterNode.ProcessFilter() == ['|World_Root|pCube4_AttrMarked',
                                            '|World_Root|joint1|joint2_Ctrl|joint3_AttrMarked',
                                            '|World_Root|joint4|joint5_AttrMarked|joint6_Ctrl|joint7_AttrMarked',
                                            '|World_Root|joint4|joint5_AttrMarked',
                                            '|World_Root|Spine_Ctrl|R_Wrist_Ctrl|R_Pole_AttrMarked_Ctrl']


class Test_baseFunctions():
    def test_nodeNameStrip(self):
        assert r9Core.nodeNameStrip('|root|of|systems|ctrl') == 'ctrl'
        assert r9Core.nodeNameStrip('|AA:root|AA:of|AA:systems|AA:ctrl') == 'ctrl'
        assert r9Core.nodeNameStrip('|BBBB:ctrl') == 'ctrl'

    def test_validateString(self):
        # simple string tester for invalid chrs
        try:
            assert not r9Core.validateString('hello!')
        except ValueError:
            assert True
        try:
            assert not r9Core.validateString('#hello')
        except ValueError:
            assert True
        try:
            assert not r9Core.validateString('hello-test')
        except ValueError:
            assert True
        try:
            assert not r9Core.validateString('hello test')
        except ValueError:
            assert True
        assert r9Core.validateString('hellotest')


    def test_stringReplace(self):
        a = 'this is a test of String replacement PPP'
        assert r9Core.stringReplace(a, {'String':'rhubarb'}) == 'this is a test of rhubarb replacement PPP'
        assert r9Core.stringReplace(a, {'PPP':'P.P.P'}) == 'this is a test of String replacement P.P.P'
        assert r9Core.stringReplace(a, {}) == 'this is a test of String replacement PPP'

    def test_prioritizeList(self):
        inputList = ['aa', 'vv', 'gg', 'ee', 'yy', 'ab', 'ac']
        priority = ['ac', 'vv']
        assert r9Core.prioritizeNodeList(inputList, priority) == ['ac', 'vv', 'aa', 'gg', 'ee', 'yy', 'ab']

        inputList = ['|dd|aa', 'vv', 'gg', 'ee', 'dd:yy', '|ss|ab', '|zz|xx|cc|ac']
        priority = ['ac', 'vv']
        assert r9Core.prioritizeNodeList(inputList, priority) == ['|zz|xx|cc|ac', 'vv', '|dd|aa', 'gg', 'ee', 'dd:yy', '|ss|ab']

        inputList = ['|dd|aa', 'vv', 'gg', 'ee', 'dd:yy', '|ss|ab', '|zz|xx|cc|ac']
        priority = ['ac', 'vv']
        assert r9Core.prioritizeNodeList(inputList, priority, prioritysOnly=True) == ['|zz|xx|cc|ac', 'vv']

        inputList = ['AA', 'SS', 'FF', 'GGG', '|shoulders|Head', 'CTRL_M_Head', 'CTRL_M_HeadPlate', 'CTRL_Mid_MiddleSpine', 'CTRL_Mid_MiddleSpine_01', 'CTRL_Mid_MiddleSpine_02', 'Mid_Middle', 'ccc', 'vvvv']
        priority = ['Head', 'CTRL_Mid_MiddleSpine']
        assert r9Core.prioritizeNodeList(inputList, priority, prioritysOnly=True) == ['|shoulders|Head', 'CTRL_M_Head', 'CTRL_M_HeadPlate', 'CTRL_Mid_MiddleSpine', 'CTRL_Mid_MiddleSpine_01', 'CTRL_Mid_MiddleSpine_02']

        # inputList=['|dd|aa','vv','gg','ee','dd:yy','|ss|ab','|zz|xx|cc|ac']
        # priority=['ac','vv']
        # assert r9Core.prioritizeNodeList(inputList, priority, prioritysOnly=True)==['|zz|xx|cc|ac','vv']

    def test_decodeString(self):
        assert isinstance(r9Core.decodeString('{"ssss":30}'), dict)
        assert isinstance(r9Core.decodeString('["ssss",30]'), list)
        assert isinstance(r9Core.decodeString('(1,2,3)'), tuple)
        assert isinstance(r9Core.decodeString('True'), bool)
        assert not r9Core.decodeString('None')
        assert isinstance(r9Core.decodeString('ehhehhehe'), str)
        assert isinstance(r9Core.decodeString('5.0'), float)
        assert isinstance(r9Core.decodeString('5'), int)

    def test_filterListByString(self):
        testlist = ['big', 'fat', 'round', 'fluffy', 'redbigfat', 'flufgrub']
        assert r9Core.filterListByString(testlist, 'Ff', matchcase=False) == ['fluffy']
        assert r9Core.filterListByString(testlist, 'Ff', matchcase=True) == []
        assert r9Core.filterListByString(testlist, 'big,ff', matchcase=False) == ['big', 'fluffy', 'redbigfat']
        assert r9Core.filterListByString(testlist, 'Big,ff', matchcase=True) == ['fluffy']

    def test_floatIsEqual(self):
        assert not r9Core.floatIsEqual(1, 0.5, tolerance=0.5, allowGimbal=True)
        assert  r9Core.floatIsEqual(1, 0.51, tolerance=0.5, allowGimbal=True)
        assert r9Core.floatIsEqual(0.1, 0.091, tolerance=0.01, allowGimbal=True)

        assert r9Core.floatIsEqual(1, 181, tolerance=0.01, allowGimbal=True)
        assert r9Core.floatIsEqual(1, 91, tolerance=0.01, allowGimbal=True)
        assert not r9Core.floatIsEqual(1, 91, tolerance=0.01, allowGimbal=False)
        assert not r9Core.floatIsEqual(1, -89, tolerance=0.01, allowGimbal=False)
        assert r9Core.floatIsEqual(0.05, 90, tolerance=1, allowGimbal=True)

    def test_timeIsInRange(self):

        assert r9Core.timeIsInRange((0, 100), (9, 80))
        assert not r9Core.timeIsInRange((10, 100), (9, 80))
        assert not r9Core.timeIsInRange((-100, 10), (9, 80))
        assert r9Core.timeIsInRange((-100, 10), (-100, 0))

        assert r9Core.timeIsInRange((-100, None), (9, 80))
        assert r9Core.timeIsInRange((0, None), (9, 80))
        assert not r9Core.timeIsInRange((0, None), (-5, 80))

        assert r9Core.timeIsInRange((None, 100), (9, 80))
        assert not r9Core.timeIsInRange((None, 100), (9, 101))
        assert r9Core.timeIsInRange((None, 100), (-5, 0))

        assert r9Core.timeIsInRange((40, 100), (40, 100), start_inRange=True, end_inRange=True)
        assert r9Core.timeIsInRange((40, 100), (50, 99), start_inRange=True, end_inRange=True)
        assert not r9Core.timeIsInRange((40, 100), (40, 101), start_inRange=True, end_inRange=True)
        assert r9Core.timeIsInRange((40, 100), (50, 101), start_inRange=True, end_inRange=False)
        assert r9Core.timeIsInRange((40, 100), (20, 50), start_inRange=False, end_inRange=True)
        assert not r9Core.timeIsInRange((40, 100), (20, 101), start_inRange=False, end_inRange=True)


class Test_LockNodes(object):
    def setup(self):
        cmds.file(new=True, f=True)
        self.cube = cmds.ls(cmds.polyCube()[0], l=True)[0]

    def test_processState(self):
        assert cmds.listAttr(self.cube, k=True, u=True) == ['visibility',
                                                            'translateX', 'translateY', 'translateZ',
                                                            'rotateX', 'rotateY', 'rotateZ',
                                                            'scaleX', 'scaleY', 'scaleZ']
        r9Core.LockChannels.processState(self.cube, 'visibility', 'lock', hierarchy=False, userDefined=False)
        assert cmds.getAttr('%s.visibility' % self.cube, lock=True)
        assert cmds.listAttr(self.cube, k=True, u=True) == ['translateX', 'translateY', 'translateZ',
                                                            'rotateX', 'rotateY', 'rotateZ',
                                                            'scaleX', 'scaleY', 'scaleZ']
        r9Core.LockChannels.processState(self.cube, 'visibility', 'unlock', hierarchy=False, userDefined=False)
        assert cmds.listAttr(self.cube, k=True, u=True) == ['visibility',
                                                            'translateX', 'translateY', 'translateZ',
                                                            'rotateX', 'rotateY', 'rotateZ',
                                                            'scaleX', 'scaleY', 'scaleZ']

class Test_Matching_CoreFuncs(object):

#    def setup(self):
#        cmds.file(os.path.join(r9Setup.red9ModulePath(),'tests','testFiles','FilterNode_baseTests.ma'),open=True,f=True)
#        self.filterNode=r9Core.FilterNode(['World_Root'])
#        assert self.filterNode.rootNodes==['World_Root']
#
#    def teardown(self):
#        self.filterNode.settings.resetFilters()

    def test_processMatchedNodes(self):
        # TODO: Fill Test
        pass
    def test_matchNodeLists(self):
        # TODO: Fill Test
        pass  #
    def test_MatchedNodeInputs(self):
        # TODO: Fill Test
        pass  #

