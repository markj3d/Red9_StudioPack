'''
------------------------------------------
Red9 Studio Pack : Maya Pipeline Solutions
email: rednineinfo@gmail.com
-------------------------------------------

This is the main unittest for the Red9_Meta module and a good
example of what's expected and what the systems can do on simple data
================================================================

'''


# import pymel.core as pm
import maya.standalone
maya.standalone.initialize(name='python')

import maya.cmds as cmds
import os

# import Red9_Meta as r9Meta
import Red9.core.Red9_Meta as r9Meta
import Red9.core.Red9_CoreUtils as r9Core
import Red9.core.Red9_PoseSaver as r9Pose

import Red9.startup.setup as r9Setup
# r9Setup.start(Menu=False, loadclients=['Testing'])  # this gets called by the Maya boot sequence anyway!!!!

# force the units, just in case
r9Setup.mayaUpAxis('y')
cmds.currentUnit(time='ntscf')

red9MetaRigConfig = os.path.join(r9Setup.red9Presets(), 'Red9_MetaRig_unitTest.cfg')

def getPoseFolder():
    return os.path.join(r9Setup.red9ModulePath(), 'tests', 'testFiles', 'MetaRig_Poses')

class Test_MetaRig():
    '''
    these are wrapped calls on MetaRig itself, note that compare goes via
    the skeletonDict in the internal metaRig compare calls
    '''
    def setup(self):
        cmds.file(os.path.join(r9Setup.red9ModulePath(), 'tests', 'testFiles', 'MetaRig_anim_jump.mb'), open=True, f=True)
        self.mRig = r9Meta.getMetaNodes(mTypes=r9Meta.MetaRig)[0]
        self.poseFolder = getPoseFolder()
        cmds.currentUnit(time='ntscf')

    def teardown(self):
        pass
        # self.setup()

    def test_poseCacheLoadFile(self):
        '''
        test the poseCache handlers in metaRig
        '''
        self.mRig.poseCacheLoad(filepath=os.path.join(self.poseFolder, 'jump_f218.pose'))

        assert self.mRig.poseCompare(os.path.join(self.poseFolder, 'jump_f218.pose'),
                                     supressWarning=True,
                                     ignoreAttrs=['jointOrientX', 'jointOrientY', 'jointOrientZ']).status
        cmds.setAttr('%s.ty' % self.mRig.L_ArmSystem.CTRL_L_Elbow[0], 0)
        compareData = self.mRig.poseCompare(os.path.join(self.poseFolder, 'jump_f218.pose'),
                                          supressWarning=True,
                                          compareDict='skeletonDict',
                                          ignoreAttrs=['jointOrientX', 'jointOrientY', 'jointOrientZ'])
        assert not compareData.status
        assert compareData.fails['failedAttrs'].keys() == ['Character1_LeftArm', 'Character1_LeftHand']
        assert str(compareData.fails['failedAttrs']) == "{u'Character1_LeftArm': {'attrMismatch': ['rotateX', 'rotateY', 'rotateZ']}, u'Character1_LeftHand': {'attrMismatch': ['rotateX', 'rotateY', 'rotateZ']}}"

    def test_poseCacheStoreAttr(self):
        cmds.currentTime(9)
        self.mRig.poseCacheStore(attr='poseAttr')  # cache against an attr
        assert self.mRig.hasAttr('poseAttr')
        assert self.mRig.poseAttr == self.mRig.poseCache.poseDict

        cmds.currentTime(0)
        self.mRig.poseCacheLoad(attr='poseAttr')
        compareData = self.mRig.poseCompare(os.path.join(self.poseFolder, 'jump_f9.pose'),
                                          supressWarning=True,
                                          compareDict='skeletonDict',
                                          ignoreAttrs=['jointOrientX', 'jointOrientY', 'jointOrientZ'])
        assert compareData.status

    def test_poseCacheStoreFile(self):
        # store a new posefile out from the MetaRig wrappers
        filepath = os.path.join(self.poseFolder, 'jump_f218UnitTest.pose')
        cmds.currentTime(9)
        self.mRig.poseCacheStore(filepath=filepath, storeThumbnail=False)  # cache against an attr
        assert os.path.exists(filepath)

        # validate the new file
        cmds.currentTime(0)
        self.mRig.poseCacheLoad(filepath=filepath)
        compareData = self.mRig.poseCompare(os.path.join(self.poseFolder, 'jump_f9.pose'),
                                          compareDict='skeletonDict',
                                          supressWarning=True,
                                          ignoreAttrs=['jointOrientX', 'jointOrientY', 'jointOrientZ'])
        assert compareData.status
        # validate the compare actually ran as expected
        compareData = self.mRig.poseCompare(os.path.join(self.poseFolder, 'jump_f218.pose'),
                                          compareDict='skeletonDict',
                                          supressWarning=True,
                                          ignoreAttrs=['jointOrientX', 'jointOrientY', 'jointOrientZ'])
        assert not compareData.status
        os.remove(filepath)

    def test_poseCacheInternal(self):
        cmds.currentTime(218)
        assert not hasattr(self.mRig, 'poseCache')
        self.mRig.poseCacheStore()
        assert self.mRig.poseCache
        cmds.currentTime(9)
        self.mRig.poseCacheLoad()
        compareData = self.mRig.poseCompare(os.path.join(self.poseFolder, 'jump_f218.pose'),
                                          compareDict='skeletonDict',
                                          supressWarning=True,
                                          ignoreAttrs=['jointOrientX', 'jointOrientY', 'jointOrientZ'])
        assert compareData.status


class Test_PoseDataMeta():

    def setup(self):
        cmds.file(os.path.join(r9Setup.red9ModulePath(), 'tests', 'testFiles', 'MetaRig_anim_jump.mb'), open=True, f=True)
        self.mRig = r9Meta.getMetaNodes(mTypes=r9Meta.MetaRig)[0]
        self.poseFolder = getPoseFolder()

        # make our PoseData object with the unitTest config loaded
        filterNode = r9Core.FilterNode_Settings()
        filterNode.read(red9MetaRigConfig)
        self.poseData = r9Pose.PoseData(filterNode)
        cmds.currentUnit(time='ntscf')

    def test_metaRigHandlers(self):
        '''
        main metaRig handlers in the pose setups
        '''
        self.poseData.metaPose = False
        assert not self.poseData.metaRig
        self.poseData.setMetaRig('L_Wrist_Ctrl')
        assert r9Meta.isMetaNode(self.poseData.metaRig)
        assert self.poseData.metaPose == True  # this is now part of the metaPose property,
        self.poseData.metaPose = True
        assert self.poseData.settings.metaRig == True

    def test_poseLoadMeta(self):
        cmds.currentTime(0)
        filepath = os.path.join(self.poseFolder, 'jump_f218.pose')
        self.poseData.poseLoad(self.mRig.mNode, filepath=filepath, useFilter=True)
        assert r9Pose.PoseCompare(self.poseData, filepath)

    def test_poseLoadMeta_relativeProjected(self):
        '''
        load the pose with relative and check against the store 'projected' posefile
        '''
        cmds.currentTime(0)
        requiredPose = os.path.join(self.poseFolder, 'jump_f218_projected.pose')

        filepath = os.path.join(self.poseFolder, 'jump_f218.pose')
        cmds.select('L_Foot_Ctrl')
        self.poseData.poseLoad(self.mRig.mNode, filepath=filepath, useFilter=True,
                               relativePose=True,
                               relativeRots='projected',
                               relativeTrans='projected')
        print '\n\n\n##########   MAYA UP AXIS : ###################', r9Setup.mayaUpAxis()
        print 'status : ', self.mRig.poseCompare(requiredPose, compareDict='poseDict', supressWarning=False).status
        assert self.mRig.poseCompare(requiredPose, compareDict='poseDict', supressWarning=False).status  # using the mRig internal wrap

        self.mRig.poseCacheStore()  # build an internal poseObj on the mRig now that we've loaded in relative space
        assert not r9Pose.PoseCompare(self.mRig.poseCache, filepath, compareDict='poseDict').compare()
        assert r9Pose.PoseCompare(self.mRig.poseCache, requiredPose, compareDict='poseDict').compare()

    def test_poseLoadMeta_relativeAbsolute(self):
        '''
        load the pose with relative and check against the store 'absolute' posefile
        '''
        cmds.currentTime(29)
        filepath = os.path.join(self.poseFolder, 'jump_f9.pose')
        cmds.select('R_Foot_Ctrl')
        self.poseData.poseLoad(self.mRig.mNode, filepath=filepath, useFilter=True,
                               relativePose=True,
                               relativeRots='projected',
                               relativeTrans='absolute')

        self.mRig.poseCacheStore()  # build an internal poseObj on the mRig now that we've loaded in relative space
        assert not r9Pose.PoseCompare(self.mRig.poseCache, filepath, compareDict='poseDict').compare()
        assert r9Pose.PoseCompare(self.mRig.poseCache, os.path.join(self.poseFolder, 'jump_f9_absolute29.pose'),
                                  compareDict='poseDict').compare()

    def test_poseLoad_maintainParentSwitches(self):
        pass

    def test_matchNodesOnIndex(self):
        pass

    def test_getNodesFromFolderConfig(self):
        pass

    def test_getMaintainedAttrs(self):
        pass

    def test_blendShapeSupport(self):
        pass

    def test_buildInternalPoseData_nonMetaSkeleton(self):
        pass


class Test_PoseData_loaders():
    '''
    same set of tests as the meta but going through the nodeType filters and 
    matchMethods stripPrefix/mirrorIndex/index etc
    '''
    def setup(self):
        cmds.file(os.path.join(r9Setup.red9ModulePath(), 'tests', 'testFiles', 'MetaRig_anim_jump.mb'), open=True, f=True)
        self.rootNode = '|World_Ctrl'
        self.poseFolder = getPoseFolder()
        cmds.currentUnit(time='ntscf')

        # make our PoseData object with the unitTest config loaded
        filterNode = r9Core.FilterNode_Settings()
        filterNode.nodeTypes = 'nurbsCurve'
        filterNode.incRoots = False
        filterNode.filterPriority = ['COG__Ctrl', 'Hips_Ctrl', 'Chest_Ctrl', 'R_Wrist_Ctrl', 'L_Wrist_Ctrl', 'L_Foot_Ctrl', 'R_Foot_Ctrl', 'L_Knee_Ctrl', 'R_Knee_Ctrl']
        self.poseData = r9Pose.PoseData(filterNode)

    def test_poseLoad_stripPrefix(self):
        self.poseData.matchMethod = 'stripPrefix'
        cmds.currentTime(0)
        filepath = os.path.join(self.poseFolder, 'jump_f218.pose')
        self.poseData.poseLoad(self.rootNode, filepath=filepath, useFilter=True)
        assert r9Pose.PoseCompare(self.poseData, filepath).compare()

#    def test_poseLoad_index(self):
#        self.poseData.matchMethod='index'
#        cmds.currentTime(0)
#        filepath=os.path.join(self.poseFolder,'jump_f218.pose')
#        self.poseData.poseLoad(self.rootNode, filepath=filepath, useFilter=True)
#        assert r9Pose.PoseCompare(self.poseData,filepath).compare()
#
    def test_poseLoad_mirrorIndex(self):
        self.poseData.matchMethod = 'mirrorIndex'
        cmds.currentTime(0)
        filepath = os.path.join(self.poseFolder, 'jump_f218.pose')
        self.poseData.poseLoad(self.rootNode, filepath=filepath, useFilter=True)
        assert r9Pose.PoseCompare(self.poseData, filepath).compare()

    def test_poseLoad_relativeProjected_stripPrefix(self):
        '''
        load the pose with relative and check against the store 'projected' posefile
        '''
        # stripPrefix Match -------------------------------------------------
        self.poseData.matchMethod = 'stripPrefix'
        cmds.currentTime(0)
        requiredPose = os.path.join(self.poseFolder, 'jump_f218_projected.pose')

        filepath = os.path.join(self.poseFolder, 'jump_f218.pose')
        cmds.select('L_Foot_Ctrl')
        self.poseData.poseLoad(self.rootNode, filepath=filepath, useFilter=True,
                               relativePose=True,
                               relativeRots='projected',
                               relativeTrans='projected')
        print '\n\n\n##########   MAYA UP AXIS : ###################', r9Setup.mayaUpAxis()

        # the pose is no longer in the same space due to the relative code,
        # we need up update the internal pose before comparing
        nodes = self.poseData.buildDataMap(self.rootNode)
        self.poseData.buildBlocks_fill(nodes)
        assert r9Pose.PoseCompare(self.poseData, requiredPose).compare()

    def test_poseLoad_relativeProjected_mirrorIndex(self):
        '''
        load the pose with relative and check against the store 'projected' posefile
        '''
        # mirrorIndex Match -------------------------------------------------
        self.poseData.matchMethod = 'mirrorIndex'
        cmds.currentTime(0)
        requiredPose = os.path.join(self.poseFolder, 'jump_f218_projected.pose')

        filepath = os.path.join(self.poseFolder, 'jump_f218.pose')
        cmds.select('L_Foot_Ctrl')
        self.poseData.poseLoad(self.rootNode, filepath=filepath, useFilter=True,
                               relativePose=True,
                               relativeRots='projected',
                               relativeTrans='projected')
        print '\n\n\n##########   MAYA UP AXIS : ###################', r9Setup.mayaUpAxis()

        # the pose is no longer in the same space due to the relative code,
        # we need up update the internal pose before comparing
        nodes = self.poseData.buildDataMap(self.rootNode)
        self.poseData.buildBlocks_fill(nodes)
        assert r9Pose.PoseCompare(self.poseData, requiredPose).compare()

    def test_poseLoad_relativeAbsolute_stripPrefix(self):
        '''
        load the pose with relative and check against the store 'absolute' posefile
        '''
        # stripPrefix Match -------------------------------------------------
        self.poseData.matchMethod = 'stripPrefix'
        cmds.currentTime(29)
        filepath = os.path.join(self.poseFolder, 'jump_f9.pose')
        cmds.select('R_Foot_Ctrl')
        self.poseData.poseLoad(self.rootNode, filepath=filepath, useFilter=True,
                               relativePose=True,
                               relativeRots='projected',
                               relativeTrans='absolute')

        # the pose is no longer in the same space due to the relative code,
        # we need up update the internal pose before comparing
        nodes = self.poseData.buildDataMap(self.rootNode)
        self.poseData.buildBlocks_fill(nodes)
        assert not r9Pose.PoseCompare(self.poseData,
                                      filepath,
                                      compareDict='poseDict').compare()
        assert r9Pose.PoseCompare(self.poseData, os.path.join(self.poseFolder, 'jump_f9_absolute29.pose'), compareDict='poseDict').compare()

    def test_poseLoad_relativeAbsolute_mirrorIndex(self):
        '''
        load the pose with relative and check against the store 'absolute' posefile
        '''
        # mirrorIndex Match -------------------------------------------------
        self.poseData.matchMethod = 'mirrorIndex'
        cmds.currentTime(29)
        filepath = os.path.join(self.poseFolder, 'jump_f9.pose')
        cmds.select('R_Foot_Ctrl')
        self.poseData.poseLoad(self.rootNode, filepath=filepath, useFilter=True,
                               relativePose=True,
                               relativeRots='projected',
                               relativeTrans='absolute')

        # the pose is no longer in the same space due to the relative code,
        # we need up update the internal pose before comparing
        nodes = self.poseData.buildDataMap(self.rootNode)
        self.poseData.buildBlocks_fill(nodes)
        assert not r9Pose.PoseCompare(self.poseData,
                                      filepath,
                                      compareDict='poseDict').compare()
        assert r9Pose.PoseCompare(self.poseData, os.path.join(self.poseFolder, 'jump_f9_absolute29.pose'), compareDict='poseDict').compare()


