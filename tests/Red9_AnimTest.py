'''
------------------------------------------
Red9 Studio Pack: Maya Pipeline Solutions
Author: Mark Jackson
email: rednineinfo@gmail.com

Red9 blog : http://red9-consultancy.blogspot.co.uk/
MarkJ blog: http://markj3d.blogspot.co.uk
------------------------------------------

This is the main unittest for the Red9_Meta module and a good
example of what's expected and what the systems can do on simple data
================================================================

'''


# import pymel.core as pm
import maya.standalone
maya.standalone.initialize(name='python')

import Red9.core.Red9_AnimationUtils as r9Anim
import Red9.startup.setup as r9Setup
import maya.cmds as cmds
import os
# r9Setup.start(Menu=False)

# force the upAxis, just in case
r9Setup.mayaUpAxis('y')

class Test_MirrorSetups(object):
    def setup(self):

        self.leftWrist = 'leftWrist'
        self.leftFoot = 'leftFoot'
        self.rightWrist = 'rightWrist'
        self.rightFoot = 'rightFoot'
        self.root = 'root'

        cmds.polyCube(n=self.leftWrist)[0]
        cmds.polyCube(n=self.leftFoot)[0]
        cmds.polyCube(n=self.rightWrist)[0]
        cmds.polyCube(n=self.rightFoot)[0]
        cmds.polyCube(n=self.root)[0]
        self.rig = cmds.group([self.leftWrist, self.leftFoot, self.rightWrist, self.rightFoot, self.root], name='rigRoot')

        self.MirrorClass = r9Anim.MirrorHierarchy(self.rig)
        self.MirrorClass.settings.hierarchy = True
        self.filePath = os.path.join(r9Setup.red9ModulePath(), 'tests', 'testFiles', 'mirrorData.mirrorMap')

    def teardown(self):
        cmds.file(new=True, f=True)

    def checkData(self):
        assert self.MirrorClass.getMirrorSide(self.leftWrist) == 'Left'
        assert self.MirrorClass.getMirrorIndex(self.leftWrist) == 1
        assert self.MirrorClass.getMirrorAxis(self.leftWrist) == ['translateX', 'rotateY', 'rotateZ']  # defaults

        assert self.MirrorClass.getMirrorSide(self.leftFoot) == 'Left'
        assert self.MirrorClass.getMirrorIndex(self.leftFoot) == 2
        assert self.MirrorClass.getMirrorAxis(self.leftFoot) == []

        assert self.MirrorClass.getMirrorSide(self.rightWrist) == 'Right'
        assert self.MirrorClass.getMirrorIndex(self.rightWrist) == 1
        assert self.MirrorClass.getMirrorAxis(self.rightWrist) == ['translateZ', 'rotateX', 'rotateY']

        assert self.MirrorClass.getMirrorSide(self.rightFoot) == 'Right'
        assert self.MirrorClass.getMirrorIndex(self.rightFoot) == 2
        assert self.MirrorClass.getMirrorAxis(self.rightFoot) == ['translateX', 'rotateY', 'rotateZ']  # defaults

        assert self.MirrorClass.getMirrorSide(self.root) == 'Centre'
        assert self.MirrorClass.getMirrorIndex(self.root) == 2
        assert self.MirrorClass.getMirrorAxis(self.root) == ['rotateY']
        return True

    def setMarkers(self):
        self.MirrorClass.setMirrorIDs(self.leftWrist, 'Left', 1)
        self.MirrorClass.setMirrorIDs(self.leftFoot, 'Left', 2, axis='None')
        self.MirrorClass.setMirrorIDs(self.rightWrist, 'Right', 1, axis='translateZ,rotateX,rotateY')
        self.MirrorClass.setMirrorIDs(self.rightFoot, 'Right', 2)
        self.MirrorClass.setMirrorIDs(self.root, 'Centre', 2, axis='rotateY')

    def test_mirrorLoader(self):

        self.setMarkers()
        assert cmds.attributeQuery('mirrorSide', node=self.leftWrist, exists=True)
        assert cmds.attributeQuery('mirrorIndex', node=self.leftWrist, exists=True)
        assert not cmds.attributeQuery('mirrorAxis', node=self.leftWrist, exists=True)
        assert cmds.attributeQuery('mirrorAxis', node=self.leftFoot, exists=True)

        assert cmds.getAttr('%s.mirrorIndex' % self.leftWrist) == 1
        assert cmds.getAttr('%s.mirrorSide' % self.leftWrist, asString=True) == 'Left'
        assert cmds.getAttr('%s.mirrorIndex' % self.leftFoot) == 2
        assert cmds.getAttr('%s.mirrorSide' % self.leftFoot, asString=True) == 'Left'
        assert cmds.getAttr('%s.mirrorAxis' % self.leftFoot) == ''
        assert cmds.getAttr('%s.mirrorAxis' % self.rightWrist) == 'translateZ,rotateX,rotateY'
        assert cmds.getAttr('%s.mirrorAxis' % self.root) == 'rotateY'

        assert self.checkData()

    def test_mirrorSave(self):
        self.setMarkers()
        self.MirrorClass.saveMirrorSetups(self.filePath)
        assert os.path.exists(self.filePath)
        self.MirrorClass.deleteMirrorIDs(self.leftFoot)
        assert not self.MirrorClass.getMirrorIndex(self.leftFoot)

    def test_mirrorLoad(self):
        assert not self.MirrorClass.getMirrorIndex(self.leftFoot)
        self.MirrorClass.loadMirrorSetups(self.filePath,
                                          [self.leftWrist, self.leftFoot, self.rightWrist, self.rightFoot, self.root],
                                          clearCurrent=True)
        assert self.checkData()


