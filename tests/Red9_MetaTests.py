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

import maya.cmds as cmds
import pymel.core as pm
import os
import time
import Red9.core.Red9_Meta as r9Meta
from Red9.core.Red9_CoreUtils import floatIsEqual

import Red9.startup.setup as r9Setup
#r9Setup.start(Menu=False)

# force the upAxis, just in case
r9Setup.mayaUpAxis('y')

class Test_MetaRegistryCalls():

    def teardown(self):
        cmds.file(new=True, f=True)
        r9Meta.registerMClassNodeMapping()  # reset the nodeTypes registry

    def test_registerMClassNodeMapping(self):
        '''
        test the registry functions for nodeTypes
        '''
        cmds.file(new=True, f=True)
        r9Meta.MetaClass(name='standardNetworkMetaNode')
        assert [cmds.nodeType(n.mNode) for n in r9Meta.getMetaNodes()] == ['network']

        # register transforms to the NodeTypes
        r9Meta.registerMClassNodeMapping(nodeTypes='transform')
        print r9Meta.getMClassNodeTypes()
        assert r9Meta.getMClassNodeTypes() == sorted(['network', 'objectSet', 'transform'])
        new = r9Meta.MetaClass(name='newTransformMetaNode', nodeType='transform')
        assert [cmds.nodeType(n.mNode) for n in r9Meta.getMetaNodes()] == ['network', 'transform']

        # reset the NodeTypes
        r9Meta.resetMClassNodeTypes()
        print r9Meta.getMClassNodeTypes()
        assert r9Meta.getMClassNodeTypes() == ['network', 'objectSet']  # ,'HIKCharacterNode']
        assert [cmds.nodeType(n.mNode) for n in r9Meta.getMetaNodes()] == ['network']

    def test_getMClassInstances(self):
        for mNode in r9Meta.getMClassInstances(r9Meta.MetaHUDNode):
            assert issubclass(mNode, r9Meta.MetaHUDNode)
        for mNode in r9Meta.getMClassInstances(r9Meta.MetaRig):
            assert issubclass(mNode, r9Meta.MetaRig)

    def test_getMClassDataFromNode(self):
        a = r9Meta.MetaRig(name='rig')
        b = r9Meta.MetaRigSubSystem(name='subSub')
        assert r9Meta.getMClassDataFromNode(a) == 'MetaRig'
        assert r9Meta.getMClassDataFromNode(a.mNode) == 'MetaRig'
        assert r9Meta.getMClassDataFromNode(b) == 'MetaRigSubSystem'
        assert r9Meta.getMClassDataFromNode(b.mNode) == 'MetaRigSubSystem'


class Test_MetaCache():

    def teardown(self):
        cmds.file(new=True, f=True)

    def test_MetaCache(self):
        a = r9Meta.MetaRig(name='rig')
        dagpath = str(a.mNode)
        assert r9Meta.getMetaFromCache(a.mNode) == a
        assert r9Meta.getMetaFromCache(dagpath) == a
        assert r9Meta.MetaClass(a.mNode) == a
        r9Meta.resetCache()
        assert not r9Meta.getMetaFromCache(a.mNode)
        r9Meta.MetaClass(a.mNode)
        assert r9Meta.getMetaFromCache(a.mNode) == a
        dagpath = str(a.mNode)
        a.delete()
        assert not r9Meta.RED9_META_NODECACHE

    def test_uuid(self):
        a = r9Meta.MetaRig(name='rig')
        UUID = a.getUUID()  # a.UUID
        assert UUID in r9Meta.RED9_META_NODECACHE

        # test the duplicate handler
        dup = cmds.duplicate(a.mNode)
        assert not dup == a.mNode
        nodes = r9Meta.getMetaNodes()
        assert len(nodes) == 2
        assert len(r9Meta.RED9_META_NODECACHE.keys()) == 2
        assert r9Meta.RED9_META_NODECACHE[UUID] == a
        assert r9Meta.MetaClass(a.mNode).getUUID() == UUID

    def test_wrappedMayaNodes(self):
        '''
        test how the cache handles non mClass nodes
        '''
        cmds.polyCube(name='cube1')
        n1 = r9Meta.MetaClass('|cube1')
        r9Meta.registerMClassNodeCache(n1)
        # from 2016 the UUID is the key for all nodes in the Cache
        if r9Setup.mayaVersion() >= 2016:
            UUID = cmds.ls(n1.mNode, uuid=True)[0]
            assert r9Meta.RED9_META_NODECACHE[UUID] == n1
        else:
            assert r9Meta.RED9_META_NODECACHE['|cube1'] == n1
        n1.rename('renamedCube1')
        assert n1.mNode == '|renamedCube1'

        # because in this case we have no UUID's we only store the
        # cache against the node name. Theres now a test against
        # the MOBject to ensure that things are still correct in the pull
        cmds.polyCube(name='cube1')
        n2 = r9Meta.MetaClass('|cube1')

        assert n2.mNode == '|cube1'
        assert not n2.mNode == 'renamedCube1'
        r9Meta.registerMClassNodeCache(n2)
        if r9Setup.mayaVersion() >= 2016:
            UUID = cmds.ls(n2.mNode, uuid=True)[0]
            assert r9Meta.RED9_META_NODECACHE[UUID] == n2
        else:
            assert r9Meta.RED9_META_NODECACHE['|cube1'] == n2


    def test_joshs_bastard_error(self):
        '''
        make mnode
        delete node manually (YOU SHOULD NOT DO THIS!!!) 
        call anything from the cache ---- boom
        '''
        pass




class Test_MetaClass():

    def setup(self):
        cmds.file(new=True, f=True)
        self.MClass = r9Meta.MetaClass(name='MetaClass_Test')

    def teardown(self):
        self.setup()

    def test_initNew(self):
        assert isinstance(self.MClass, r9Meta.MetaClass)
        assert self.MClass.mClass == 'MetaClass'
        assert self.MClass.mNode == 'MetaClass_Test'
        assert cmds.nodeType(self.MClass.mNode) == 'network'

    def test_unregisteredNodeType(self):
        # new handler will bail if you try and create with an unRegistered nodeType
        try:
            r9Meta.MetaClass(name='new', nodeType='transform')
            print 'Failed - generated new node with unregistered nodeType!'
            assert False
        except:
            assert True

    def test_functionCalls(self):

        # select
        cmds.select(cl=True)
        self.MClass.select()
        assert cmds.ls(sl=True)[0] == 'MetaClass_Test'

        # rename
        self.MClass.rename('FooBar')
        assert self.MClass.mNode == 'FooBar'
        self.MClass.select()
        assert cmds.ls(sl=True)[0] == 'FooBar'

        # convert
        new = r9Meta.convertMClassType(self.MClass, 'MetaRig')
        assert isinstance(new, r9Meta.MetaRig)
        assert self.MClass.mClass == 'MetaRig'

        # isReferenced
        assert not self.MClass.isReferenced()

        # delete
        self.MClass.delete()
        assert not cmds.objExists('MetaClass_Test')


    def test_isValid(self):
        assert not self.MClass.isValid()  # strange one, isValid fails if the mNode has no connections.... is this a good decision?
        cube1 = cmds.ls(cmds.polyCube()[0], l=True)[0]
        newMeta = r9Meta.MetaClass(cube1)
        assert newMeta.isValid()
        cmds.delete(newMeta.mNode)
        assert not self.MClass.isValid()

    def test_mNodeID(self):
        assert self.MClass.mNodeID == 'MetaClass_Test'
        assert cmds.attributeQuery('mNodeID', node=self.MClass.mNode, exists=True)
        assert self.MClass.hasAttr('mNodeID')

        # lets test standard wrapped handling
        cube1 = cmds.ls(cmds.polyCube()[0], l=True)[0]
        cube2 = cmds.ls(cmds.polyCube()[0], l=True)[0]
        cube3 = cmds.ls(cmds.polyCube()[0], l=True)[0]
        cubeMeta = r9Meta.MetaClass(cube1)
        assert cubeMeta.mNodeID == 'pCube1'
        # nest the dag path
        cmds.parent(cube1, cube2)
        cmds.parent(cube2, cube3)
        assert cubeMeta.mNode == '|pCube3|pCube2|pCube1'
        cubeMeta = r9Meta.MetaClass('|pCube3|pCube2')
        assert cubeMeta.mNodeID == 'pCube2'

    def test_MObject_Handling(self):
        # mNode is now handled via an MObject
        assert self.MClass.mNode == 'MetaClass_Test'
        cmds.rename('MetaClass_Test', 'FooBar')
        assert self.MClass.mNode == 'FooBar'

    def test_addChildMetaNode(self):
        '''
        add a new MetaNode as a child of self
        '''
        newMFacial = self.MClass.addChildMetaNode('MetaFacialRig', attr='Facial', nodeName='FacialNode')
        assert isinstance(newMFacial, r9Meta.MetaFacialRig)
        assert newMFacial.mNode == 'FacialNode'
        assert cmds.listConnections('%s.Facial' % self.MClass.mNode, c=True, p=True) == ['MetaClass_Test.Facial',
                                                                                     'FacialNode.MetaClass_Test']
        assert isinstance(self.MClass.Facial, r9Meta.MetaFacialRig)
        assert self.MClass.Facial.mNode == 'FacialNode'

    def test_addChildMetaNode_ClassAttr(self):
        '''
        add a new MetaNode as a child of self, passing in class rather than a string
        '''
        newMFacial = self.MClass.addChildMetaNode(r9Meta.MetaFacialRig, attr='Facial', nodeName='FacialNode')
        assert isinstance(newMFacial, r9Meta.MetaFacialRig)
        assert newMFacial.mNode == 'FacialNode'
        assert cmds.listConnections('%s.Facial' % self.MClass.mNode, c=True, p=True) == ['MetaClass_Test.Facial',
                                                                                     'FacialNode.MetaClass_Test']
        assert isinstance(self.MClass.Facial, r9Meta.MetaFacialRig)
        assert self.MClass.Facial.mNode == 'FacialNode'

    def test_connectionsTo_MetaNodes_child(self):
        '''
        Test how the code handles connections to other MetaNodes
        '''
        facialNode = r9Meta.MetaFacialRig(name='FacialNode')
        self.MClass.connectChild(facialNode, 'Facial')

        assert self.MClass.Facial.mNode == 'FacialNode'
        assert isinstance(self.MClass.Facial, r9Meta.MetaFacialRig)
        assert self.MClass.hasAttr('Facial')
        assert not facialNode.hasAttr('Facial')
        assert facialNode.hasAttr('MetaClass_Test')
        assert cmds.listConnections('%s.Facial' % self.MClass.mNode, c=True, p=True) == ['MetaClass_Test.Facial',
                                                                                     'FacialNode.MetaClass_Test']
        # test disconnect call
        self.MClass.disconnectChild(self.MClass.Facial, deleteSourcePlug=True, deleteDestPlug=True)
        assert not self.MClass.hasAttr('Facial')
        assert not facialNode.hasAttr('MetaClass_Test')

        # test the additional attr flag
        self.MClass.connectChild(facialNode, 'parentAttr', 'childAttr')
        assert cmds.listConnections('%s.parentAttr' % self.MClass.mNode, c=True, p=True) == ['MetaClass_Test.parentAttr',
                                                                                     'FacialNode.childAttr']
        self.MClass.disconnectChild(self.MClass.parentAttr, deleteSourcePlug=True, deleteDestPlug=True)
        assert not self.MClass.hasAttr('parentAttr')
        assert not facialNode.hasAttr('childAttr')

    def test_connectionsTo_MetaNodes_children(self):
        '''
        COMPLEX! Test how the code handles connections to other MetaNodes via
        connectChildren. Note that currently if the connections are between
        MetaNodes then the messageAttr is INDEX managed
        '''
        master1 = r9Meta.MetaClass(name='master1')
        master2 = r9Meta.MetaClass(name='master2')
        child1 = r9Meta.MetaClass(name='child1')
        child2 = r9Meta.MetaClass(name='child2')
        cube = cmds.ls(cmds.polyCube()[0], l=True)[0]

        # note mClass instance being passed in
        master1.connectChildren([child1, child2, cube], 'modules', 'puppet')
        assert cmds.attributeQuery('modules', node=master1.mNode, m=True)
        assert cmds.attributeQuery('modules', node=master1.mNode, im=True)
        assert sorted(master1.modules) == sorted(['|pCube1', child1, child2])
        assert child1.puppet == [master1]
        assert child2.puppet == [master1]
        assert cmds.attributeQuery('puppet', node=cube, m=True)
        # assert not cmds.attributeQuery('puppet', node=cube, im=True)  # If we switch to 'allow_incest' as default then this is no longer valid!
        assert cmds.listConnections('%s.puppet' % cube) == ['master1']

        # mClass mNode being passed in
        master2.connectChildren([child1.mNode, child2.mNode, cube], 'time', 'master', force=True)
        assert sorted(master2.time) == sorted(['|pCube1', child1, child2])
        assert child1.master == [master2]
        assert child2.master == [master2]
        assert cmds.listConnections('%s.master' % cube) == ['master2']
        # check previous
        assert sorted(master1.modules) == sorted(['|pCube1', child1, child2])
        assert child1.puppet == [master1]
        assert child2.puppet == [master1]
        assert cmds.listConnections('%s.puppet' % cube) == ['master1']

        master1.connectChildren([child1, child2], 'time', 'master', cleanCurrent=True)
        assert master1.time == [child1, child2]
        assert sorted(child1.master, key=lambda x:x.mNode) == [master1, master2]
        assert sorted(child2.master, key=lambda x:x.mNode) == [master1, master2]
        # check previous
        assert sorted(master2.time) == sorted(['|pCube1', child1, child2])
        assert cmds.listConnections('%s.master' % cube) == ['master2']
        assert sorted(master1.modules) == sorted(['|pCube1', child1, child2])
        assert child1.puppet == [master1]
        assert child2.puppet == [master1]
        assert cmds.listConnections('%s.puppet' % cube) == ['master1']

        try:
            master1.connectChildren([child1], 'time', 'master')
            assert False, 'Shouldnt be able to connect the same node multi-times via the same attrs'
        except:
            assert True

        master1.disconnectChild(child2, 'time')
        assert master1.time == [child1]
        assert child2.master == [master2]
        # check previous
        assert sorted(master1.modules) == sorted(['|pCube1', child1, child2])
        assert sorted(master2.time) == sorted(['|pCube1', child1, child2])

        master1.disconnectChild(child1)
        assert sorted(master1.modules) == sorted(['|pCube1', child2])
        assert not master1.hasAttr('time')  # cleaned the plug
        assert child1.master == [master2]
        assert child1.hasAttr('puppet')  # ???? FIXME: this is wrong, it should have been cleaned as it's now empty!
        # assert not child1.puppet

        # check previous
        assert sorted(master2.time) == sorted(['|pCube1', child1, child2])

        # isChildNode test calls
        assert master1.isChildNode(child2.mNode)
        assert master1.isChildNode(child2.mNode, 'modules', 'puppet')
        assert master1.isChildNode(child2)
        assert not master1.isChildNode(child1)

    def test_connectionsTo_MayaNodes_Basic(self):
        '''
        Test how the code handles connections to standard MayaNodes
        '''
        cube1 = cmds.ls(cmds.polyCube()[0], l=True)[0]
        cube2 = cmds.ls(cmds.polyCube()[0], l=True)[0]
        cube3 = cmds.ls(cmds.polyCube()[0], l=True)[0]
        cube4 = cmds.ls(cmds.polyCube()[0], l=True)[0]

        # add singular Child
        self.MClass.connectChild(cube1, 'Singluar')
        assert self.MClass.Singluar == [cube1]
        # add multiple Children
        self.MClass.connectChildren([cube2, cube3], 'Multiple')
        assert sorted(self.MClass.Multiple) == [cube2, cube3]

        # get the MetaNode back from the cube1 connection and retest
        found = r9Meta.getConnectedMetaNodes(cube1)[0]
        assert isinstance(found, r9Meta.MetaClass)
        assert found.mNode == 'MetaClass_Test'
        assert found.mClass == 'MetaClass'
        assert sorted(found.Multiple) == [cube2, cube3]

        # connect something else to Singluar - cleanCurrent=True by default so unhook cube1
        self.MClass.connectChild(cube2, 'Singluar')
        print self.MClass.Singluar, '  : mclass.Singular'
        assert self.MClass.Singluar == [cube2]
        assert not cmds.attributeQuery('MetaClassTest', node=cube1, exists=True)  # cleaned up after ourselves?
        self.MClass.connectChildren([cube3, cube4], 'Singluar')
        print sorted(self.MClass.Singluar), [cube2, cube3, cube4]
        assert sorted(self.MClass.Singluar) == sorted([cube2, cube3, cube4])

        # setAttr has cleanCurrent and force set to true so remove all current connections to this attr
        self.MClass.Singluar = cube1
        assert self.MClass.Singluar == [cube1]
        try:
            # still thinking about this....if the attr isn't a multi then
            # the __setattr__ will fail if you pass in a lots of nodes
            self.MClass.Singluar = [cube1, cube2, cube3]
        except:
            assert True

        self.MClass.Multiple = [cube1, cube4]
        assert sorted(self.MClass.Multiple) == sorted([cube1, cube4])

    def test_connections_called_from_wrappedMClass(self):
        '''
        lets try connects again and see how it behaves when the mClass calling
        the code is just a wrapped standard Maya node
        '''
        loc1 = cmds.spaceLocator(name="boom")[0]
        loc2 = cmds.spaceLocator(name="blah")[0]
        loc3 = cmds.spaceLocator(name="weeh")[0]
        boom = r9Meta.MetaClass("boom")

        assert r9Meta.isMetaNode(boom)
        boom.connectChild(loc2, "child", "parent")
        assert boom.child == ['|blah']
        boom.connectChild(loc3, "child", "parent")
        assert boom.child == ['|weeh']
        assert not cmds.attributeQuery('parent', node=loc2, exists=True)

    def test_connectionsTo_MayaNodes_Complex(self):
        '''
        This is more to sanity check the connection management, when and how nodes get
        removed from current connections, when multiples are allowed etc. Also check the
        flags 'srcAttr' & 'force'
        '''
        cube1 = cmds.ls(cmds.polyCube()[0], l=True)[0]
        cube2 = cmds.ls(cmds.polyCube()[0], l=True)[0]
        cube3 = cmds.ls(cmds.polyCube()[0], l=True)[0]
        cube4 = cmds.ls(cmds.polyCube()[0], l=True)[0]
        cube5 = cmds.ls(cmds.polyCube()[0], l=True)[0]
        cube6 = cmds.ls(cmds.polyCube()[0], l=True)[0]

        # test the fact that connectChildren allows multiples, cleanCurrent=False
        self.MClass.connectChildren([cube1, cube2, cube3], 'con1')
        assert sorted(self.MClass.con1) == [cube1, cube2, cube3]
        self.MClass.connectChildren([cube4, cube5], 'con1')
        assert sorted(self.MClass.con1) == [cube1, cube2, cube3, cube4, cube5]
        # test the cleanCurrent flag, deletes all current connections before  doing the hookup
        self.MClass.connectChildren([cube6, cube2], 'con1', cleanCurrent=True)
        assert sorted(self.MClass.con1) == [cube2, cube6]

        # unhook manager for cleanCurrent, no 'srcAttr' flag given so the attr on the node
        # used to connect to mNode is the same default for all, mNode.mNodeID. This means
        # the node can't be connected to the same mNode more than once by default
        self.MClass.connectChild(cube1, 'singleAttr1')
        assert self.MClass.singleAttr1 == [cube1]
        self.MClass.connectChild(cube1, 'singleAttr2')
        assert self.MClass.singleAttr2 == [cube1]
        assert not self.MClass.singleAttr1 == [cube1]

        # test multiple connections to the same mNode by specifying the srcAttr used on the
        # node itself, stops the node getting mNode.mNodeID attr which is the default
        self.MClass.connectChild(cube1, 'singleAttr1', srcAttr='newScrAttr')
        assert self.MClass.singleAttr1 == [cube1]
        assert self.MClass.singleAttr2 == [cube1]  # is still connected
        assert cmds.listConnections('%s.singleAttr1' % self.MClass.mNode, c=True, p=True) == ['MetaClass_Test.singleAttr1',
                                                                                          'pCube1.newScrAttr']
        # force Flag test
        try:
            # should fail as cube2 is still connected to the mNode via the 'con1' attr
            self.MClass.connectChild(cube2, 'singleAttr', force=False)
            assert False
        except:
            assert True
        # force cube2's removal from previous attr
        self.MClass.connectChild(cube2, 'singleAttr', force=True)
        assert self.MClass.singleAttr == [cube2]
        # addAttr failure hook. cube2 already connected so addAttr now hard coded to fail with warning
        try:
            self.MClass.addAttr('newAttr', attrType='message', value=cube2)
            assert False
        except:
            assert True

    def test_forceFlagReturns(self):
        '''
        test the _forceAsMeta flag, modifying all returns to be instantiated metaClass objects
        This is deep integration and needs careful testing
        '''
        cube1 = cmds.ls(cmds.polyCube()[0], l=True)[0]
        cube2 = cmds.ls(cmds.polyCube()[0], l=True)[0]
        cube3 = cmds.ls(cmds.polyCube()[0], l=True)[0]
        self.MClass.connectChild(cube1, 'singleAttr1')
        self.MClass.connectChild(cube2, 'singleAttr2')
        assert self.MClass.getChildren() == [cube1, cube2]

        # throw the flag to force returns
        self.MClass._forceAsMeta = True

        assert issubclass(type(self.MClass.singleAttr1[0]), r9Meta.MetaClass)
        assert self.MClass.singleAttr1[0].mNode == cube1
        assert r9Meta.isMetaNode(self.MClass.singleAttr1[0])
        nodes = self.MClass.getChildren()
        for node in nodes:
            assert r9Meta.isMetaNode(node)
            assert node.getParentMetaNode() == self.MClass
            assert cmds.nodeType(node.mNode) == 'transform'

        # connection handler
        self.MClass.connectChild(r9Meta.MetaClass(cube3), 'newConnect')
        assert self.MClass.newConnect[0].mNode == cube3
        assert self.MClass.isChildNode(cube3)
        assert self.MClass.isChildNode(cube3, 'newConnect')


    def test_connectParent(self):

        parent = r9Meta.MetaFacialRig(name='Facial')
        self.MClass.connectParent(parent, 'FacialNode')

        assert parent.getChildMetaNodes()[0] == self.MClass
        assert self.MClass.getParentMetaNode() == parent
        assert parent.FacialNode == self.MClass


    def test_attrLocking(self):
        '''
        deals with locking and managing locked attrs
        '''
        self.MClass.addAttr('newTest', 1.0)
        assert not self.MClass.attrIsLocked('newTest')
        cmds.setAttr('%s.newTest' % self.MClass.mNode, l=True)
        assert self.MClass.attrIsLocked('newTest')
        self.MClass.attrSetLocked('newTest', False)
        assert not self.MClass.attrIsLocked('newTest')
        self.MClass.attrSetLocked('newTest', True)
        assert self.MClass.attrIsLocked('newTest')

        # setAttr also uses this handler to force set locked attrs
        self.MClass.newTest = 4
        assert self.MClass.newTest == 4

    def test_lockState(self):
        assert not self.MClass.lockState
        assert not cmds.lockNode(self.MClass.mNode, query=True)[0]
        self.MClass.lockState = True
        assert cmds.lockNode(self.MClass.mNode, query=True)[0]

    def test_addAttrHandling(self):
        self.MClass.addAttr('floatAttr', 1, l=True)
        assert self.MClass.attrIsLocked('floatAttr')
        self.MClass.addAttr('max', 1, max=10)
        assert self.MClass.max == 1
        try:
            self.MClass.max = 30
        except:
            assert True
        assert cmds.addAttr('%s.max' % self.MClass.mNode, q=True, max=True) == 10

        # check that adding attrs back onto an mNode through cmds still gets picked up
        mObj1 = r9Meta.MetaClass(name='testr9')
        cmds.addAttr(mObj1.mNode, ln='stringTest', dt='string')
        cmds.setAttr('%s.stringTest' % mObj1.mNode, 'maya_added_attr', type='string')
        assert cmds.getAttr('%s.stringTest' % mObj1.mNode) == 'maya_added_attr'
        assert mObj1.stringTest == 'maya_added_attr'



    def test_attributeHandling(self):
        '''
        This tests the standard attribute handing in the MetaClass.__setattr__
        '''
        node = self.MClass

        # standard attribute handling
        node.addAttr('stringTest', "this_is_a_string")  # create a string attribute
        node.addAttr('fltTest', 1.333)  # create a float attribute
        node.addAttr('fltTest2', 10.5, min=0, max=15)  # create a float attribute with min/max
        node.addAttr('intTest', 3)  # create a int attribute
        node.addAttr('boolTest', False)  # create a bool attribute
        node.addAttr('enum', attrType='enum', enumName='A:B:D:E:F')  # create an enum attribute
        node.addAttr('doubleTest', attrType='double3', value=(1.12, 2.55, 5.0))
        node.addAttr('floatTest', attrType='float3', value=(2.33, 2.55, 1.52))
        node.addAttr('doubleTest2', attrType='double3', value=(1.0, 2.0, 10.0), min=1, max=15)
        node.addAttr('doubleArray', attrType='doubleArray', value=(1.0, 2.0, 10.0))
        node.addAttr('doubleArray2', attrType='doubleArray')

        # create a string attr with JSON serialized data
        testDict = {'jsonFloat':1.05, 'jsonInt':3, 'jsonString':'string says hello', 'jsonBool':True}
        node.addAttr('jsonTest', testDict)

        # test the hasAttr call in the baseClass
        assert node.hasAttr('stringTest')
        assert node.hasAttr('fltTest')
        assert node.hasAttr('fltTest2')
        assert node.hasAttr('intTest')
        assert node.hasAttr('boolTest')
        assert node.hasAttr('enum')
        assert node.hasAttr('jsonTest')
        assert node.hasAttr('doubleTest')  # compound3 so it adds 3 child attrs
        assert node.hasAttr('floatTest')  # compound3 so it adds 3 child attrs
        assert node.hasAttr('doubleTestX')
        assert node.hasAttr('doubleTestY')
        assert node.hasAttr('doubleTestZ')
        assert node.hasAttr('doubleTest2')
        assert node.hasAttr('doubleArray')
        assert node.hasAttr('doubleArray2')

        # test the actual Maya node attributes
        #------------------------------------
        assert cmds.getAttr('%s.stringTest' % node.mNode, type=True) == 'string'
        assert cmds.getAttr('%s.fltTest' % node.mNode, type=True) == 'double'
        assert cmds.getAttr('%s.fltTest2' % node.mNode, type=True) == 'double'
        assert cmds.getAttr('%s.intTest' % node.mNode, type=True) == 'long'
        assert cmds.getAttr('%s.boolTest' % node.mNode, type=True) == 'bool'
        assert cmds.getAttr('%s.enum' % node.mNode, type=True) == 'enum'
        assert cmds.getAttr('%s.jsonTest' % node.mNode, type=True) == 'string'
        assert cmds.getAttr('%s.doubleTest' % node.mNode, type=True) == 'double3'
        assert cmds.getAttr('%s.floatTest' % node.mNode, type=True) == 'float3'
        assert cmds.getAttr('%s.doubleTestX' % node.mNode, type=True) == 'double'
        assert cmds.getAttr('%s.doubleTestY' % node.mNode, type=True) == 'double'
        assert cmds.getAttr('%s.doubleTestZ' % node.mNode, type=True) == 'double'
        assert cmds.getAttr('%s.doubleArray' % node.mNode, type=True) == 'doubleArray'
        assert cmds.getAttr('%s.doubleArray2' % node.mNode, type=True) == 'doubleArray'

        assert cmds.getAttr('%s.stringTest' % node.mNode) == 'this_is_a_string'
        assert cmds.getAttr('%s.fltTest' % node.mNode) == 1.333
        assert cmds.getAttr('%s.fltTest2' % node.mNode) == 10.5
        assert cmds.getAttr('%s.intTest' % node.mNode) == 3
        assert cmds.getAttr('%s.boolTest' % node.mNode) == False
        assert cmds.getAttr('%s.enum' % node.mNode) == 0
        assert cmds.getAttr('%s.jsonTest' % node.mNode) == '{"jsonFloat": 1.05, "jsonBool": true, "jsonString": "string says hello", "jsonInt": 3}'
        assert cmds.getAttr('%s.doubleTest' % node.mNode) == [(1.12, 2.55, 5.0)]
        #assert cmds.getAttr('%s.floatTest' % node.mNode) == [(2.33, 2.55, 1.52)]
        assert cmds.getAttr('%s.doubleTestX' % node.mNode) == 1.12
        assert cmds.getAttr('%s.doubleTestY' % node.mNode) == 2.55
        assert cmds.getAttr('%s.doubleTestZ' % node.mNode) == 5.0
        assert cmds.getAttr('%s.doubleArray' % node.mNode) == [1.0, 2.0, 10.0]
        assert not cmds.getAttr('%s.doubleArray2' % node.mNode)  # added with no initial value

        assert cmds.attributeQuery('fltTest2', node=node.mNode, max=True) == [15.0]
        assert cmds.attributeQuery('doubleTest2X', node=node.mNode, min=True) == [1.0]
        assert cmds.attributeQuery('doubleTest2Y', node=node.mNode, max=True) == [15.0]


        # now check the MetaClass __getattribute__ and __setattr__ calls
        #--------------------------------------------------------------
        assert node.intTest == 3
        node.intTest = 10  # set back to the MayaNode
        assert node.intTest == 10

        #float ========================
        assert node.fltTest == 1.333
        node.fltTest = 3.55  # set the float attr
        assert node.fltTest == 3.55
        # float with min, max kws passed
        try:
            # try setting the value past it's max
            node.fltTest2 = 22
            assert False
        except:
            assert True
        try:
            # try setting the value past it's min
            node.fltTest2 = -5
            assert False
        except:
            assert True

        #string =======================
        assert node.stringTest == 'this_is_a_string'
        node.stringTest = "change the text"  # set the string attr
        assert node.stringTest == 'change the text'

        #bool =========================
        assert node.boolTest == False
        node.boolTest = True  # set bool
        assert node.boolTest == True

        #enum =========================
        assert node.enum == 0
        node.enum = 'B'
        assert node.enum == 1
        node.enum = 2
        assert node.enum == 2

        #json string handlers =========
        assert type(node.jsonTest) == dict
        assert node.jsonTest == {'jsonFloat':1.05, 'jsonInt':3, 'jsonString':'string says hello', 'jsonBool':True}
        assert node.jsonTest['jsonFloat'] == 1.05
        assert node.jsonTest['jsonInt'] == 3
        assert node.jsonTest['jsonString'] == 'string says hello'
        assert node.jsonTest['jsonBool'] == True

        #double3 ======================
        assert node.doubleTest == (1.12, 2.55, 5.0)
        assert node.doubleTestX == 1.12
        assert node.doubleTestY == 2.55
        assert node.doubleTestZ == 5.0
        node.doubleTest = (2.0, 44.2, 22.0)
        assert node.doubleTest == (2.0, 44.2, 22.0)
        try:
            # try setting the value past it's max
            node.doubleTest2 = (0, 1, 22)
            assert False
        except:
            assert True
        try:
            # try setting the value past it's max
            node.doubleTest2X = -10
            assert False
        except:
            assert True

        #float3 ======================
        #assert node.floatTest == (2.33, 2.55, 1.52)
        assert floatIsEqual(node.floatTestX, 2.33)
        assert floatIsEqual(node.floatTestY, 2.55)
        assert floatIsEqual(node.floatTestZ, 1.52)
        node.floatTest = (2.0, 44.2, 22.0)
        assert floatIsEqual(node.floatTestX, 2.0)
        assert floatIsEqual(node.floatTestY, 44.2)
        assert floatIsEqual(node.floatTestZ, 22.0)
        #assert node.floatTest == (2.0, 44.2, 22.0)

        #doubleArray ======================
        assert node.doubleArray == [1.0, 2.0, 10.0]
        node.doubleArray = [20, 5.5, 3.1]
        assert node.doubleArray == [20, 5.5, 3.1]
        node.doubleArray = []
        assert not node.doubleArray
        assert not node.doubleArray2
        node.doubleArray2 = [1.1, 5, 6, 7, 1.1]
        assert node.doubleArray2 == [1.1, 5, 6, 7, 1.1]

        del(node.boolTest)
        assert cmds.objExists(node.mNode)
        assert not node.hasAttr('boolTest')
        assert not cmds.attributeQuery('boolTest', node=node.mNode, exists=True)


    def test_attributeHandlingMath(self):
        '''
        This tests the python attr handling with math args
        '''
        node = self.MClass

        node.addAttr('fltTest', 1.5)
        node.fltTest += 1
        assert node.fltTest == 2.5
        node.fltTest -= 1
        assert node.fltTest == 1.5
        node.fltTest *= 2
        assert node.fltTest == 3.0


    def test_attributeHandling_MessageAttr(self):
        '''
        test the messageLink handling in the __setattr__ block and addAttr
        this doesn't do any connectChild/children testing
        '''
        node = self.MClass

        # make sure we collect LONG names for these as all wrappers deal with longName
        cube1 = cmds.ls(cmds.polyCube()[0], l=True)[0]
        cube2 = cmds.ls(cmds.polyCube()[0], l=True)[0]
        cube3 = cmds.ls(cmds.polyCube()[0], l=True)[0]
        cube4 = cmds.ls(cmds.polyCube()[0], l=True)[0]
        cube5 = cmds.ls(cmds.polyCube()[0], l=True)[0]
        cube6 = cmds.ls(cmds.polyCube()[0], l=True)[0]

        node.addAttr('msgMultiTest', value=[cube1, cube2], attrType='message')  # multi Message attr
        node.addAttr('msgSingleTest', value=cube3, attrType='messageSimple')  # non-multi message attr

        assert node.hasAttr('msgMultiTest')
        assert node.hasAttr('msgSingleTest')

        assert cmds.getAttr('%s.msgMultiTest' % node.mNode, type=True) == 'message'
        assert cmds.getAttr('%s.msgSingleTest' % node.mNode, type=True) == 'message'
        assert cmds.attributeQuery('msgMultiTest', node=node.mNode, multi=True) == True
        assert cmds.attributeQuery('msgSingleTest', node=node.mNode, multi=True) == False

        # NOTE : cmds returns shortName, but all MetaClass attrs are always longName
        assert cmds.listConnections('%s.msgMultiTest' % node.mNode, c=True, p=True) == ['MetaClass_Test.msgMultiTest[0]',
                                                                 'pCube1.MetaClass_Test[0]',
                                                                 'MetaClass_Test.msgMultiTest[1]',
                                                                 'pCube2.MetaClass_Test[0]']
        assert cmds.listConnections('%s.msgSingleTest' % node.mNode, c=True, p=True) == ['MetaClass_Test.msgSingleTest',
                                                                                     'pCube3.MetaClass_Test']

        assert sorted(node.msgMultiTest) == [cube1, cube2]
        assert node.msgSingleTest == [cube3]

        # test the reconnect handler via the setAttr
        node.msgMultiTest = [cube5, cube6]
        assert sorted(node.msgMultiTest) == [cube5, cube6]
        assert not cmds.attributeQuery('MetaClass_Test', node=cube1, exists=True)  # disconnect should delete the old connection attr
        print cmds.listConnections('%s.msgMultiTest' % node.mNode, c=True, p=True)
        assert cmds.listConnections('%s.msgMultiTest' % node.mNode, c=True, p=True) == ['MetaClass_Test.msgMultiTest[0]',
                                                                 'pCube5.MetaClass_Test[0]',
                                                                 'MetaClass_Test.msgMultiTest[1]',
                                                                 'pCube6.MetaClass_Test[0]']
        node.msgMultiTest = [cube1, cube2, cube4, cube6]
        assert sorted(node.msgMultiTest) == [cube1, cube2, cube4, cube6]
        assert sorted(cmds.listConnections('%s.msgMultiTest' % node.mNode)) == ['pCube1', 'pCube2', 'pCube4', 'pCube6']

        node.msgSingleTest = cube4
        assert node.msgSingleTest == [cube4]
        assert cmds.listConnections('%s.msgSingleTest' % node.mNode) == ['pCube4']  # cmds returns a list
        node.msgSingleTest = cube3
        assert node.msgSingleTest == [cube3]
        assert cmds.listConnections('%s.msgSingleTest' % node.mNode) == ['pCube3']  # cmds returns a list

    def test_longJsonDumps(self):
        '''
        Test the handling of LONG serialized Json data - testing the 16bit string attrTemplate handling
        NOTE: if you set a string to over 32,767 chars and don't lock the attr once made, selecting
        the textField in the AttributeEditor will truncate the data, hence this test!
        '''
        data = "x" * 40000
        self.MClass.addAttr('json_test', data)
        assert len(self.MClass.json_test) == 40000

        # save the file and reload to ensure the attr is consistent
        cmds.file(rename=os.path.join(r9Setup.red9ModulePath(), 'tests', 'testFiles', 'deleteMe.ma'))
        cmds.file(save=True, type='mayaAscii')
        cmds.file(new=True, f=True)
        cmds.file(os.path.join(r9Setup.red9ModulePath(), 'tests', 'testFiles', 'deleteMe.ma'), open=True, f=True)

        mClass = r9Meta.getMetaNodes()[0]
        assert len(mClass.json_test)

    def test_castingStandardNode(self):
        mLambert = r9Meta.MetaClass('lambert1')
        # mLambert is just a Python MetaNode and doesn't exist as a MayaNode
        mLambert.diffuse = 0.5
        assert '%0.2f' % cmds.getAttr('lambert1.diffuse') == '0.50'
        mLambert.diffuse = 0.77
        assert '%0.2f' % cmds.getAttr('lambert1.diffuse') == '0.77'

        mLambert.color = (0.5, 0.5, 0.5)
        assert mLambert.color == (0.5, 0.5, 0.5)
        assert cmds.getAttr('lambert1.color') == [(0.5, 0.5, 0.5)]
        mLambert.color = (1.0, 0.0, 0.5)
        print mLambert.color
        assert mLambert.color == (1.0, 0.0, 0.5)
        assert cmds.getAttr('lambert1.color') == [(1.0, 0.0, 0.5)]

    def test_convertMClassType(self):
        '''
        test the class convert call, designed to mutate a given
        metaClass to another and re-instantiate it
        '''
        # MClass Mutation
        assert type(self.MClass) == r9Meta.MetaClass
        converted = r9Meta.convertMClassType(self.MClass, 'MetaRig')
        assert type(converted) == r9Meta.MetaRig
        assert converted.mClass == 'MetaRig'
        mNodes = r9Meta.getMetaNodes()
        assert len(mNodes) == 1


    def test_referenceHandler(self):
        # TODO: Fill Test
        # referenceNode
        # referencePath
        # nameSpace
        # nameSpaceFull
        # nameSpaceFull(asList=True)
        pass

    def test_isSystemRoot(self):
        # TODO: Fill Test
        pass

    def test_renameChildLinks(self):
        # TODO: Fill Test
        pass



class Test_Generic_SearchCalls():
    '''
    Basic Generic search calls at scene level
    '''
    def setup(self):
        cmds.file(new=True, f=True)
        self.metaA = r9Meta.MetaClass(name='MetaClass_Test')
        self.metaB = r9Meta.MetaRig(name='MetaRig_Test')
        self.metaC = r9Meta.MetaRigSupport(name='MetaRigSupport_Test')
        self.metaD = r9Meta.MetaFacialRig(name='MetaFacialRig_Test')
        self.metaE = r9Meta.MetaFacialRigSupport(name='MetaFacialRigSupport_Test')

    def teardown(self):
        self.setup()

    def test_isMetaNode(self):
        assert r9Meta.isMetaNode('MetaRig_Test')
        assert r9Meta.isMetaNode(self.metaA)
        assert r9Meta.isMetaNode('MetaRig_Test', mTypes=['MetaRig'])
        assert r9Meta.isMetaNode('MetaRig_Test', mTypes='MetaRig')
        assert not r9Meta.isMetaNode('MetaRig_Test', mTypes='MonkeyBollox')
        assert not r9Meta.isMetaNode('MetaRig_Test', mTypes='MetaFacialRigSupport_Test')
        assert r9Meta.isMetaNode('MetaRig_Test', mTypes=[r9Meta.MetaRig])
        assert r9Meta.isMetaNode('MetaRig_Test', mTypes=r9Meta.MetaRig)
        assert r9Meta.isMetaNode(self.metaB, mTypes=r9Meta.MetaRig)
        assert not r9Meta.isMetaNode(self.metaB, mTypes=r9Meta.MetaRigSupport)
        cube1 = cmds.ls(cmds.polyCube()[0], l=True)[0]
        assert not r9Meta.isMetaNode(cube1)

    def test_isMetaNodeInherited(self):
        assert r9Meta.isMetaNodeInherited('MetaFacialRig_Test', 'MetaRig')
        assert r9Meta.isMetaNodeInherited(self.metaD, 'MetaRig')
        assert r9Meta.isMetaNodeInherited('MetaFacialRig_Test', 'MetaClass')
        assert not r9Meta.isMetaNodeInherited('MetaFacialRig_Test', 'MetaRigSubSystem')
        assert r9Meta.isMetaNodeInherited('MetaFacialRig_Test', r9Meta.MetaRig)
        assert r9Meta.isMetaNodeInherited(self.metaD, r9Meta.MetaRig)
        assert r9Meta.isMetaNodeInherited('MetaFacialRig_Test', r9Meta.MetaClass)
        assert not r9Meta.isMetaNodeInherited('MetaFacialRig_Test', r9Meta.MetaRigSubSystem)

    def test_getMetaNodes(self):
        nodes = sorted(r9Meta.getMetaNodes(), key=lambda x: x.mClass.upper())
        assert [n.mClass for n in nodes] == ['MetaClass', 'MetaFacialRig', 'MetaFacialRigSupport', 'MetaRig', 'MetaRigSupport']

    def test_getMetaNodes_mTypes(self):
        # mTypes test
        nodes = sorted(r9Meta.getMetaNodes(mTypes=['MetaRig', 'MetaFacialRig']), key=lambda x: x.mClass.upper())
        assert [n.mClass for n in nodes] == ['MetaFacialRig', 'MetaRig']

        nodes = r9Meta.getMetaNodes(dataType=None, mTypes=['MetaRig'])
        assert nodes == ['MetaRig_Test']

    def test_getMetaNodes_mTypesAsClass(self):
        # mTypes test passing in Class rather than string
        nodes = sorted(r9Meta.getMetaNodes(mTypes=[r9Meta.MetaRig, r9Meta.MetaFacialRig]), key=lambda x: x.mClass.upper())
        assert [n.mClass for n in nodes] == ['MetaFacialRig', 'MetaRig']

        nodes = r9Meta.getMetaNodes(dataType=None, mTypes=[r9Meta.MetaRig])
        assert nodes == ['MetaRig_Test']

    def test_getMetaNodes_mInstances(self):
        # mInstances tests
        nodes = r9Meta.getMetaNodes(dataType=None, mInstances=['MetaRig'])
        assert nodes == ['MetaFacialRig_Test', 'MetaRig_Test']
        nodes = r9Meta.getMetaNodes(mInstances=['MetaRig'])
        assert [n.mNodeID for n in nodes] == ['MetaFacialRig_Test', 'MetaRig_Test']
        nodes = r9Meta.getMetaNodes(mInstances=['MetaClass'])
        assert sorted([n.mNode for n in nodes]) == ['MetaClass_Test',
                                                  'MetaFacialRigSupport_Test',
                                                  'MetaFacialRig_Test',
                                                  'MetaRigSupport_Test',
                                                  'MetaRig_Test']
    def test_getMetaNodes_mInstancesAsClass(self):
        # mInstances tests passing in Class rather than string
        nodes = r9Meta.getMetaNodes(dataType=None, mInstances=[r9Meta.MetaRig])
        assert nodes == ['MetaFacialRig_Test', 'MetaRig_Test']
        nodes = r9Meta.getMetaNodes(mInstances=[r9Meta.MetaRig])
        assert [n.mNodeID for n in nodes] == ['MetaFacialRig_Test', 'MetaRig_Test']
        nodes = r9Meta.getMetaNodes(mInstances=[r9Meta.MetaClass])
        assert sorted([n.mNode for n in nodes]) == ['MetaClass_Test',
                                                  'MetaFacialRigSupport_Test',
                                                  'MetaFacialRig_Test',
                                                  'MetaRigSupport_Test',
                                                  'MetaRig_Test']

    def test_getMetaNodes_mAttrs(self):
        assert r9Meta.getMetaNodes(mAttrs='version=1')[0].mNodeID == 'MetaRig_Test'

    def test_getMetaNodes_mGrps(self):
        # TODO: Fill Test
        pass

class Test_MetaRig():

    def setup(self):
        cmds.file(os.path.join(r9Setup.red9ModulePath(), 'tests', 'testFiles', 'MetaRig_baseTests.ma'), open=True, f=True)
        self.mRig = self.addMetaRig()

    def teardown(self):
        self.setup()

    def addMetaRig(self):
        '''
        Add a basic MetaRig network to the file including MetaSubSystems and MetaSupport
        '''
        mRig = r9Meta.MetaRig(name='RED_Rig')

        # Link the MainCtrl , this is used as Root for some of the functions
        mRig.addRigCtrl('World_Ctrl', 'Main', mirrorData={'side':'Centre', 'slot':1})

        #Left Arm SubMeta Systems --------------------------
        lArm = mRig.addMetaSubSystem('Arm', 'Left', nodeName='L_ArmSystem', attr='L_ArmSystem')
        lArm.addRigCtrl('L_Wrist_Ctrl', 'L_Wrist', mirrorData={'side':'Left', 'slot':1})
        lArm.addRigCtrl('L_Elbow_Ctrl', 'L_Elbow', mirrorData={'side':'Left', 'slot':2})
        lArm.addRigCtrl('L_Clav_Ctrl', 'L_Clav', mirrorData={'side':'Left', 'slot':3})
        #Left Arm Fingers ---------------------------------
        lArm.addMetaSubSystem('Fingers', 'Left')
        lArm.L_Fingers_System.addRigCtrl('Character1_LeftHandThumb1', 'ThumbRoot')
        lArm.L_Fingers_System.addRigCtrl('Character1_LeftHandIndex1', 'IndexRoot')
        lArm.L_Fingers_System.addRigCtrl('Character1_LeftHandMiddle1', 'MiddleRoot')
        lArm.L_Fingers_System.addRigCtrl('Character1_LeftHandRing1', 'RingRoot')
        lArm.L_Fingers_System.addRigCtrl('Character1_LeftHandPinky1', 'PinkyRoot')

        #Left Leg SubMeta Systems --------------------------
        lLeg = mRig.addMetaSubSystem('Leg', 'Left', nodeName='L_LegSystem')
        lLeg.addRigCtrl('L_Foot_Ctrl', 'L_Foot', mirrorData={'side':'Left', 'slot':4})
        lLeg.addRigCtrl('L_Knee_Ctrl', 'L_Knee', mirrorData={'side':'Left', 'slot':5})

        #Right Arm SubMeta Systems --------------------------
        rArm = mRig.addMetaSubSystem('Arm', 'Right', nodeName='R_ArmSystem', attr='R_ArmSystem')
        rArm.addRigCtrl('R_Wrist_Ctrl', 'R_Wrist', mirrorData={'side':'Right', 'slot':1})
        rArm.addRigCtrl('R_Elbow_Ctrl', 'R_Elbow', mirrorData={'side':'Right', 'slot':2})
        rArm.addRigCtrl('R_Clav_Ctrl', 'R_Clav', mirrorData={'side':'Right', 'slot':3})
        #Right Arm Fingers ----------------------------------
        rArm.addMetaSubSystem('Fingers', 'Right')
        rArm.R_Fingers_System.addRigCtrl('Character1_RightHandThumb1', 'ThumbRoot')
        rArm.R_Fingers_System.addRigCtrl('Character1_RightHandIndex1', 'IndexRoot')
        rArm.R_Fingers_System.addRigCtrl('Character1_RightHandMiddle1', 'MiddleRoot')
        rArm.R_Fingers_System.addRigCtrl('Character1_RightHandRing1', 'RingRoot')
        rArm.R_Fingers_System.addRigCtrl('Character1_RightHandPinky1', 'PinkyRoot')

        #Right Leg SubMeta System --------------------------
        rLeg = mRig.addMetaSubSystem('Leg', 'Right', nodeName='R_LegSystem', attr='R_LegSystem')
        rLeg.addRigCtrl('R_Foot_Ctrl', 'R_Foot', mirrorData={'side':'Right', 'slot':4})
        rLeg.addRigCtrl('R_Knee_Ctrl', 'R_Knee', mirrorData={'side':'Right', 'slot':5})

        #Spine SubMeta System -------------------------------
        spine = mRig.addMetaSubSystem('Spine', 'Centre', nodeName='SpineSystem', attr='SpineSystem')
        spine.addRigCtrl('COG__Ctrl', 'Root', mirrorData={'side':'Centre', 'slot':2})
        spine.addRigCtrl('Hips_Ctrl', 'Hips', mirrorData={'side':'Centre', 'slot':3})
        spine.addRigCtrl('Chest_Ctrl', 'Chest', mirrorData={'side':'Centre', 'slot':4})
        spine.addRigCtrl('Head_Ctrl', 'Head', mirrorData={'side':'Centre', 'slot':5})


        #add SupportMeta Nodes ------------------------------
        # this is a really basic demo, for the sake of this you could
        # just wire all the support nodes to one MetaSupport, but this
        # shows what you could do for really complex setups
        lArm.addSupportMetaNode('L_ArmSupport')
        lArm.L_ArmSupport.addSupportNode('ikHandle1', 'IKHandle')
        rArm.addSupportMetaNode('R_ArmSupport')
        rArm.R_ArmSupport.addSupportNode('ikHandle2', 'IKHandle')
        lLeg.addSupportMetaNode('L_LegSupport')
        lLeg.L_LegSupport.addSupportNode('ikHandle5', 'IKHandle')
        rLeg.addSupportMetaNode('R_LegSupport')
        rLeg.R_LegSupport.addSupportNode('ikHandle6', 'IKHandle')
        spine.addSupportMetaNode('SpineSupport')
        spine.SpineSupport.addSupportNode('ikHandle3', 'NeckIK')
        spine.SpineSupport.addSupportNode('ikHandle4', 'SpineIK')

        return mRig

    def test_basicRigStructure(self):

        mRig = r9Meta.getConnectedMetaSystemRoot('L_Wrist_Ctrl')

        assert type(mRig) == r9Meta.MetaRig
        assert mRig.mNode == 'RED_Rig'
        assert mRig.CTRL_Main[0] == '|World_Ctrl'

        # test the Left Arm wires
        assert type(mRig.L_ArmSystem) == r9Meta.MetaRigSubSystem
        assert mRig.L_ArmSystem.mNode == 'L_ArmSystem'
        assert mRig.L_ArmSystem.systemType == 'Arm'
        assert mRig.L_ArmSystem.mirrorSide == 1
        assert mRig.L_ArmSystem.CTRL_L_Wrist[0] == '|World_Ctrl|L_Wrist_Ctrl'
        assert mRig.L_ArmSystem.CTRL_L_Elbow[0] == '|World_Ctrl|COG__Ctrl|L_Elbow_Ctrl'
        ctrl = r9Meta.MetaClass(mRig.L_ArmSystem.CTRL_L_Wrist[0])
        assert ctrl.mirrorSide == 1  # ?????? consistency of attrs on node and metaSubsystems!!!!!!!
        assert ctrl.mirrorIndex == 1

        # test the Right Leg wires
        assert type(mRig.R_LegSystem) == r9Meta.MetaRigSubSystem
        assert r9Meta.isMetaNode('R_LegSystem')
        assert mRig.R_LegSystem.mNode == 'R_LegSystem'
        assert mRig.R_LegSystem.systemType == 'Leg'
        assert mRig.R_LegSystem.mirrorSide == 2
        assert mRig.R_LegSystem.CTRL_R_Foot[0] == '|World_Ctrl|R_Foot_grp|R_Foot_Ctrl'
        assert mRig.R_LegSystem.CTRL_R_Knee[0] == '|World_Ctrl|R_Knee_Ctrl'
        ctrl = r9Meta.MetaClass(mRig.R_LegSystem.CTRL_R_Foot[0])
        assert ctrl.mirrorSide == 2  # ?????? consistency of attrs on node and metaSubsystems!!!!!!!
        assert ctrl.mirrorIndex == 4

        # test the Left Leg wires
        # :NOTE slight difference in the naming as we didn't pass in the attr when making the subSystem
        assert type(mRig.L_Leg_System) == r9Meta.MetaRigSubSystem
        assert r9Meta.isMetaNode('L_LegSystem')
        assert mRig.L_Leg_System.mNode == 'L_LegSystem'
        assert mRig.L_Leg_System.systemType == 'Leg'
        assert mRig.L_Leg_System.mirrorSide == 1

        # test the Spine wires
        assert type(mRig.SpineSystem) == r9Meta.MetaRigSubSystem
        assert mRig.SpineSystem.mNode == 'SpineSystem'
        assert mRig.SpineSystem.systemType == 'Spine'
        assert mRig.SpineSystem.mirrorSide == 0
        assert mRig.SpineSystem.CTRL_Hips[0] == '|World_Ctrl|COG__Ctrl|Hips_Ctrl'
        assert mRig.SpineSystem.CTRL_Chest[0] == '|World_Ctrl|COG__Ctrl|Chest_Ctrl'
        ctrl = r9Meta.MetaClass(mRig.SpineSystem.CTRL_Chest[0])
        assert ctrl.mirrorSide == 0  # ?????? consistency of attrs on node and metaSubsystems!!!!!!!
        assert ctrl.mirrorIndex == 4

        # test the MetaRigSupport nodes
        assert type(mRig.L_ArmSystem.L_ArmSupport) == r9Meta.MetaRigSupport
        assert mRig.L_ArmSystem.L_ArmSupport.mNode == 'L_ArmSupport'
        assert mRig.L_ArmSystem.L_ArmSupport.SUP_IKHandle[0] == '|World_Ctrl|L_Wrist_Ctrl|ikHandle1'
        assert mRig.SpineSystem.SpineSupport.SUP_NeckIK[0] == '|World_Ctrl|COG__Ctrl|Chest_Ctrl|Head_grp|Head_Ctrl|ikHandle3'
        assert mRig.SpineSystem.SpineSupport.SUP_SpineIK[0] == '|World_Ctrl|COG__Ctrl|Chest_Ctrl|ikHandle4'

    def test_getRigCtrls(self):

        assert self.mRig.getRigCtrls() == ['|World_Ctrl']

        assert self.mRig.getRigCtrls(walk=True) == ['|World_Ctrl',
                                    '|World_Ctrl|R_Foot_grp|R_Foot_Ctrl',
                                    '|World_Ctrl|R_Knee_Ctrl',
                                    '|World_Ctrl|L_Wrist_Ctrl',
                                    '|World_Ctrl|COG__Ctrl|L_Elbow_Ctrl',
                                    '|World_Ctrl|COG__Ctrl|Chest_Ctrl|L_Clav_Ctrl',
                                    '|World_Ctrl|R_Wrist_Ctrl',
                                    '|World_Ctrl|COG__Ctrl|R_Elbow_Ctrl',
                                    '|World_Ctrl|COG__Ctrl|Chest_Ctrl|R_Clav_Ctrl',
                                    '|World_Ctrl|COG__Ctrl',
                                    '|World_Ctrl|COG__Ctrl|Hips_Ctrl',
                                    '|World_Ctrl|COG__Ctrl|Chest_Ctrl',
                                    '|World_Ctrl|COG__Ctrl|Chest_Ctrl|Head_grp|Head_Ctrl',
                                    '|World_Ctrl|L_Foot_grp|L_Foot_Ctrl',
                                    '|World_Ctrl|L_Knee_Ctrl',
                                    '|Character1_Pelvis|Character1_Spine|Character1_Spine2|Character1_RightShoulder|Character1_RightArm|Character1_RightForeArm|Character1_RightHand|Character1_RightHandThumb1',
                                    '|Character1_Pelvis|Character1_Spine|Character1_Spine2|Character1_RightShoulder|Character1_RightArm|Character1_RightForeArm|Character1_RightHand|Character1_RightHandIndex1',
                                    '|Character1_Pelvis|Character1_Spine|Character1_Spine2|Character1_RightShoulder|Character1_RightArm|Character1_RightForeArm|Character1_RightHand|Character1_RightHandMiddle1',
                                    '|Character1_Pelvis|Character1_Spine|Character1_Spine2|Character1_RightShoulder|Character1_RightArm|Character1_RightForeArm|Character1_RightHand|Character1_RightHandRing1',
                                    '|Character1_Pelvis|Character1_Spine|Character1_Spine2|Character1_RightShoulder|Character1_RightArm|Character1_RightForeArm|Character1_RightHand|Character1_RightHandPinky1',
                                    '|Character1_Pelvis|Character1_Spine|Character1_Spine2|Character1_LeftShoulder|Character1_LeftArm|Character1_LeftForeArm|Character1_LeftHand|Character1_LeftHandThumb1',
                                    '|Character1_Pelvis|Character1_Spine|Character1_Spine2|Character1_LeftShoulder|Character1_LeftArm|Character1_LeftForeArm|Character1_LeftHand|Character1_LeftHandIndex1',
                                    '|Character1_Pelvis|Character1_Spine|Character1_Spine2|Character1_LeftShoulder|Character1_LeftArm|Character1_LeftForeArm|Character1_LeftHand|Character1_LeftHandMiddle1',
                                    '|Character1_Pelvis|Character1_Spine|Character1_Spine2|Character1_LeftShoulder|Character1_LeftArm|Character1_LeftForeArm|Character1_LeftHand|Character1_LeftHandRing1',
                                    '|Character1_Pelvis|Character1_Spine|Character1_Spine2|Character1_LeftShoulder|Character1_LeftArm|Character1_LeftForeArm|Character1_LeftHand|Character1_LeftHandPinky1']

        assert self.mRig.R_ArmSystem.getRigCtrls() == ['|World_Ctrl|R_Wrist_Ctrl',
                                                     '|World_Ctrl|COG__Ctrl|R_Elbow_Ctrl',
                                                     '|World_Ctrl|COG__Ctrl|Chest_Ctrl|R_Clav_Ctrl']

        assert self.mRig.R_ArmSystem.getRigCtrls(walk=True) == ['|World_Ctrl|R_Wrist_Ctrl',
                                                 '|World_Ctrl|COG__Ctrl|R_Elbow_Ctrl',
                                                 '|World_Ctrl|COG__Ctrl|Chest_Ctrl|R_Clav_Ctrl',
                                                 '|Character1_Pelvis|Character1_Spine|Character1_Spine2|Character1_RightShoulder|Character1_RightArm|Character1_RightForeArm|Character1_RightHand|Character1_RightHandThumb1',
                                                 '|Character1_Pelvis|Character1_Spine|Character1_Spine2|Character1_RightShoulder|Character1_RightArm|Character1_RightForeArm|Character1_RightHand|Character1_RightHandIndex1',
                                                 '|Character1_Pelvis|Character1_Spine|Character1_Spine2|Character1_RightShoulder|Character1_RightArm|Character1_RightForeArm|Character1_RightHand|Character1_RightHandMiddle1',
                                                 '|Character1_Pelvis|Character1_Spine|Character1_Spine2|Character1_RightShoulder|Character1_RightArm|Character1_RightForeArm|Character1_RightHand|Character1_RightHandRing1',
                                                 '|Character1_Pelvis|Character1_Spine|Character1_Spine2|Character1_RightShoulder|Character1_RightArm|Character1_RightForeArm|Character1_RightHand|Character1_RightHandPinky1']

        assert self.mRig.R_ArmSystem.getChildren(walk=False) == ['|World_Ctrl|R_Wrist_Ctrl',
                                                     '|World_Ctrl|COG__Ctrl|R_Elbow_Ctrl',
                                                     '|World_Ctrl|COG__Ctrl|Chest_Ctrl|R_Clav_Ctrl']

    def test_getNodeConnectionMetaDataMap(self):
        assert self.mRig.getNodeConnectionMetaDataMap('|World_Ctrl|L_Foot_grp|L_Foot_Ctrl') == {'metaAttr': u'CTRL_L_Foot', 'metaNodeID': u'L_LegSystem'}

    def test_getNodeConnectionMetaDataMap_mTypes(self):
        # TODO: Fill Test
        # assert self.mRig.getNodeConnectionMetaDataMap(mTypes=??)
        pass

    def test_getNodeConnections(self):
        assert self.mRig.L_Leg_System.getNodeConnections('|World_Ctrl|L_Foot_grp|L_Foot_Ctrl') == ['CTRL_L_Foot']

    def test_getChildMetaNodes(self):
        # test that the new flags in the get calls are running
        assert sorted([n.mNode for n in self.mRig.getChildMetaNodes(walk=False, mAttrs=['systemType=Arm'], stepover=False)]) == ['L_ArmSystem',
                                                                                                                                 'R_ArmSystem']
        # stepover non matched test
        assert self.mRig.getChildMetaNodes(walk=True, mAttrs=['systemType=Fingers'], stepover=False) == []
        assert sorted([n.mNode for n in self.mRig.getChildMetaNodes(walk=True, mAttrs=['systemType=Fingers'], stepover=True)]) == ['L_Fingers_System',
                                                                                                                                   'R_Fingers_System']

        assert sorted([n.mNode for n in self.mRig.getChildMetaNodes(walk=True, mTypes=['MetaRigSupport'], stepover=True)]) == ['L_ArmSupport',
                                                                                                                             'L_LegSupport',
                                                                                                                             'R_ArmSupport',
                                                                                                                             'R_LegSupport',
                                                                                                                             'SpineSupport']

        assert sorted([n.mNode for n in self.mRig.getChildMetaNodes(walk=True, mInstances=['MetaRig'], stepover=True)]) == [  'L_ArmSystem',
                                                                                                                            'L_Fingers_System',
                                                                                                                            'L_LegSystem',
                                                                                                                            'R_ArmSystem',
                                                                                                                            'R_Fingers_System',
                                                                                                                            'R_LegSystem',
                                                                                                                            'SpineSystem']

        assert sorted([n.mNode for n in self.mRig.getChildMetaNodes(walk=True, mInstances=['MetaClass'], stepover=True)]) == ['L_ArmSupport',
                                                                                                                            'L_ArmSystem',
                                                                                                                            'L_Fingers_System',
                                                                                                                            'L_LegSupport',
                                                                                                                            'L_LegSystem',
                                                                                                                            'R_ArmSupport',
                                                                                                                            'R_ArmSystem',
                                                                                                                            'R_Fingers_System',
                                                                                                                            'R_LegSupport',
                                                                                                                            'R_LegSystem',
                                                                                                                            'SpineSupport',
                                                                                                                            'SpineSystem']
        assert self.mRig.getChildMetaNodes(walk=True, mInstances=['MetaRigSupport'], stepover=False) == []
        assert [n.mNode for n in self.mRig.L_ArmSystem.getChildMetaNodes(walk=True, mInstances=['MetaRigSupport'], stepover=False)] == ['L_ArmSupport']

#    def test_getChildren_mAttrs(self):
#        #TODO: Fill Test
#        pass
#
#    def test_getChildren_asMap(self):
#        #TODO: Fill Test
#        pass
#
#    def test_getConnectedMetaNodes(self):
#        #TODO: Fill Test
#        pass
#
#    def test_getConnectedMetaNodes_mTypes(self):
#        #TODO: Fill Test
#        pass
#
#    def test_getConnectedMetaNodes_mInstances(self):
#        #TODO: Fill Test
#        pass
#
#    def test_getConnectedMetaNodes_mAttrs(self):
#        #TODO: Fill Test
#        pass
#
#    def test_getSkeletonRoots(self):
#        #TODO: Fill Test
#        pass
#
#    def test_addSupportNode(self):
#        #TODO: Fill Test
#        pass
#
#    def test_set_ctrlColour(self):
#        #TODO: Fill Test
#        pass
#
#    def test_mirrorDataHandling(self):
#        #TODO: Fill Test
#        #loadMirrorDataMap
#        #getMirrorData
#        #getMirror_opposites
#        #getMirror_ctrlSets
#        #mirror
#        pass
#
#    def test_poseCache(self):
#        #poseCacheStore
#        #poseCacheLoad
#        #poseCompare
#        pass
#
#    def test_nodeVisibility(self):
#        #nodeVisibility
#        #hideNodes
#        #unHideNodes
#        pass
#
#    def test_attrMap(self):
#        #loadAttrMap
#        #saveAttrMap
#        pass

class Test_SpeedTesting():
    '''
    These are all set to fail so that we get the capture output that we can bracktrack
    '''
    def setup(self):
        cmds.file(new=True, f=True)

    def test_standardNodes(self):
        cubes = []
        for i in range(1, 10000):
            cubes.append(cmds.polyCube(name='a%s' % i)[0])



        now = time.clock()
        c = [r9Meta.MetaClass(p, autofill=False) for p in cubes]
        print 'SPEED: Standard Wrapped Nodes : autofill=False: %s' % str(time.clock() - now)
        print 'Timer 05/01/17 should be around 2.48 secs on the Beast'
        print 'Timer should be around 2.28 secs on the Beast'

        # verify against pymel, I know we're still a lot slower
        now = time.clock()
        c = pm.ls(cubes)
        print 'Timer Pymel Reference : ', time.clock() - now
        print '\n'
        r9Meta.resetCache()

        now = time.clock()
        c = [r9Meta.MetaClass(p, autofill='all') for p in cubes]
        print 'SPEED: Standard Wrapped Nodes : autofill=all : %s' % str(time.clock() - now)
        print 'Timer 05/01/17 should be around 5.27 secs on the Beast'
        print 'Timer should be around 9.04 secs on the Beast'

        assert False

    def test_MetaNodes(self):
        nodes = []
        for i in range(1, 10000):
            nodes.append(r9Meta.MetaClass(name='a%s' % i).mNode)
        r9Meta.resetCache()
        now = time.clock()
        c = [r9Meta.MetaClass(p, autofill='all') for p in nodes]
        print 'SPEED: Meta Nodes : autofill=all : %s' % str(time.clock() - now)
        print 'Timer 05/01/17 should be around 6.25 secs on the Beast'
        print 'Timer should be around 8.5 secs on the Beast'
        print '\n'

        now = time.clock()
        c = [r9Meta.MetaClass(p, autofill='all') for p in nodes]
        print 'SPEED: Meta Nodes from Cache :  %s' % str(time.clock() - now)
        print 'Timer 05/01/17 should be around 2.93 secs on the Beast'
        print 'Timer should be around 3.25 secs on the Beast'
        print '\n'

        r9Meta.resetCache()

        c = [r9Meta.MetaClass(p, autofill=False) for p in nodes]
        print 'SPEED: Meta Nodes : autofill=False : %s' % str(time.clock() - now)
        print 'Timer 05/01/17 should be around 7.39 secs on the Beast'
        print 'Timer should be around 8.5 secs on the Beast'
        assert False





class Test_MetaNetworks():
    '''
    Test the network walking and get commands on a larger network
    '''
    def setup(self):
        cmds.file(os.path.join(r9Setup.red9ModulePath(), 'tests', 'testFiles', 'Meta_Network_WalkTest.ma'), open=True, f=True)
        self.mRig = r9Meta.getMetaNodes(mTypes='MetaRig')[0]

    def teardown(self):
        self.setup()

    def buildNetwork(self):
        '''
        code that built the test scene above
        '''
        mRig = r9Meta.MetaRig()
        mRig.addMetaSubSystem('Spine', 'Centre')
        mRig.C_Spine_System.addMetaSubSystem('Arm', 'Left')
        mRig.C_Spine_System.L_Arm_System.addMetaSubSystem('other', 'Left')
        mRig.C_Spine_System.L_Arm_System.addSupportMetaNode('L_Arm_Support')
        mRig.C_Spine_System.L_Arm_System.L_other_System.addMetaSubSystem('Fingers', 'Left')

        mRig.C_Spine_System.addMetaSubSystem('Arm', 'Right')
        mRig.C_Spine_System.R_Arm_System.addMetaSubSystem('other', 'Right')
        mRig.C_Spine_System.R_Arm_System.addSupportMetaNode('R_Arm_Support')
        mRig.C_Spine_System.R_Arm_System.R_other_System.addMetaSubSystem('Fingers', 'Right')

        mRig.addMetaSubSystem('Leg', 'Right')
        mRig.R_Leg_System.addMetaSubSystem('Toes', 'Right')
        mRig.addMetaSubSystem('Leg', 'Left')
        mRig.R_Leg_System.addMetaSubSystem('Toes', 'Left')

    def test_getChildMetaNodes(self):
        '''
        note that the order of this is important as the return is
        managed by the depth of the connections
        '''
        nodes = self.mRig.getChildMetaNodes(walk=True)
        assert [node.mNodeID for node in nodes] == ['R_Leg_System',
                                                 'L_Leg_System',
                                                 'C_Spine_System',
                                                 'L_Toes_System',
                                                 'L_Arm_System',
                                                 'R_Toes_System',
                                                 'R_Arm_System',
                                                 'L_other_System',
                                                 'R_other_System',
                                                 'L_Arm_Support',
                                                 'R_Arm_Support',
                                                 'R_Fingers_System',
                                                 'L_Fingers_System']

        nodes = self.mRig.C_Spine_System.getChildMetaNodes(walk=True)
        assert [node.mNodeID for node in nodes] == ['R_Arm_System',
                                                 'L_Arm_System',
                                                 'R_other_System',
                                                 'L_other_System',
                                                 'R_Arm_Support',
                                                 'L_Arm_Support',
                                                 'L_Fingers_System',
                                                 'R_Fingers_System']

        nodes = self.mRig.C_Spine_System.getChildMetaNodes(walk=False)
        assert [node.mNodeID for node in nodes] == ['R_Arm_System', 'L_Arm_System']


    def test_getParentSystems(self):
        assert r9Meta.getConnectedMetaSystemRoot('L_Fingers_System').mNode == 'MetaRig'
        assert r9Meta.getConnectedMetaSystemRoot('L_Toes_System').mNode == 'MetaRig'

        assert self.mRig.C_Spine_System.L_Arm_System.getParentMetaNode().mNodeID == 'C_Spine_System'
        assert self.mRig.C_Spine_System.L_Arm_System.L_Arm_Support.getParentMetaNode().mNodeID == 'L_Arm_System'

    def test_getConnectedMetaSystemRoot_args(self):
        # add in a few additional systemRoots and check the filter args
        assert r9Meta.getConnectedMetaSystemRoot('L_Fingers_System').mNode == 'MetaRig'
        r_legSys = r9Meta.getConnectedMetaNodes('MetaRig')[0]
        l_legSys = r9Meta.getConnectedMetaNodes('MetaRig')[2]

        # add 2 new mNodes that are effectively now BOTH additional parents to the system
        newparent1 = r9Meta.MetaClass(name='exportNode')
        newparent2 = r9Meta.MetaFacialRig(name='facial')
        r_legSys.connectParent(newparent1, attr='ExportRoot')
        l_legSys.connectParent(newparent2, attr='Facial')

        assert r9Meta.getConnectedMetaSystemRoot('L_Leg_System').mClass == 'MetaRig'
        assert r9Meta.getConnectedMetaSystemRoot('L_Leg_System', mTypes=['MetaFacialRig']).mClass == 'MetaFacialRig'

        assert r9Meta.getConnectedMetaSystemRoot('R_Fingers_System').mClass == 'MetaRig'
        assert not r9Meta.getConnectedMetaSystemRoot('R_Fingers_System', ignoreTypes='MetaRig')

        assert r9Meta.getConnectedMetaSystemRoot('R_Toes_System').mClass == 'MetaClass'
        assert r9Meta.getConnectedMetaSystemRoot('R_Toes_System', ignoreTypes=['MetaClass']).mClass == 'MetaRig'

    def test_getMetaNodes_mAttrs(self):
        mNodes = r9Meta.getMetaNodes(mAttrs='mirrorSide=1')
        assert sorted([node.mNodeID for node in mNodes]) == ['L_Arm_System',
                                                 'L_Fingers_System',
                                                 'L_Leg_System',
                                                 'L_Toes_System',
                                                 'L_other_System']
        mNodes = r9Meta.getMetaNodes(mAttrs=['mirrorSide=1', 'systemType=Arm'])
        assert sorted([node.mNodeID for node in mNodes]) == ['L_Arm_System']

        mNodes = r9Meta.getMetaNodes(mAttrs=['systemType=Leg'])
        assert sorted([node.mNodeID for node in mNodes]) == ['L_Leg_System', 'R_Leg_System']



