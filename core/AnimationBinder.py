'''
########################################################################

    Autodesk MasterClass 2011 - Live Animation Binding
    --------------------------------------------------
    Author : Mark Jackson :
    Email  : markj3d@gmail.com
    Blog   : http://markj3d.blogspot.com

    This is designed to run on Maya2011 / 2012 with native PyMel support
    If you're interested in running this under previous versions of Maya
    drop me a line and I'll point you in the right direction.

    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Install: just drop this file into your scripts folder or one any path
    that's on a python path. then in a Python ScriptEditor Tab :

    import AnimationBinder as AB
    AB.AnimBinderUI.Show()

    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    I'll probably put this file and any updates to it on my blog in the
    near future.

    Thanks for trying the workflows, all comments more than welcomed

    PLEASE NOTE: this code is in the process of being re-built for the
    Red9 ProPack where we intend to bind HIK to the remapping by default


########################################################################
'''

from __future__ import print_function

import maya.cmds as cmds
import pymel.core as pm
import Red9_AnimationUtils as r9Anim
import Red9_CoreUtils as r9Core
import Red9.startup.setup as r9Setup
import Red9.core.Red9_General as r9General


import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
# log.setLevel(logging.DEBUG)
########################################################################


BAKE_MARKER = 'BoundCtr'
BNDNODE_MARKER = 'BindNode'

class Bindsettings(object):

    def __init__(self):
        '''
        settings object that we pass to the Binder Classes directly, keeps the code clean
        '''
        self.bind_trans = True
        self.bind_rots = True
        self.reset_trans = True
        self.reset_rots = False
        self.base_scale = 1
        self.bake_debug = False
        self.__align_to_control_trans = True
        self.__align_to_control_rots = True
        self.__align_to_source_trans = False
        self.__align_to_source_rots = False

    @property
    def align_to_control_trans(self):
        return self.__align_to_control_trans

    @align_to_control_trans.setter
    def align_to_control_trans(self, value):
        if value:
            self.__align_to_source_trans = False
            self.__align_to_control_trans = True
            log.info('align_to_control_trans=True, Switching align_to_source_trans=False')
        else:
            self.__align_to_control_trans = False

    @property
    def align_to_source_trans(self):
        return self.__align_to_source_trans

    @align_to_source_trans.setter
    def align_to_source_trans(self, value):
        if value:
            self.__align_to_control_trans = False
            self.__align_to_source_trans = True
            log.info('align_to_source_trans=True, Switching align_to_control_trans=False')
        else:
            self.__align_to_source_trans = False

    @property
    def align_to_control_rots(self):
        return self.__align_to_control_rots

    @align_to_control_rots.setter
    def align_to_control_rots(self, value):
        if value:
            self.__align_to_source_rots = False
            self.__align_to_control_rots = True
            log.info('align_to_control_rots=True, Switching align_to_source_rots=False')
        else:
            self.__align_to_control_rots = False

    @property
    def align_to_source_rots(self):
        return self.__align_to_source_rots

    @align_to_source_rots.setter
    def align_to_source_rots(self, value):
        if value:
            self.__align_to_control_rots = False
            self.__align_to_source_rots = True
            log.info('align_to_source_rots=True, Switching align_to_control_rots=False')
        else:
            self.__align_to_source_rots = False

    def print_settings(self):
        log.info(self.__dict__)


class BindNodeBase(object):

    def __init__(self, source=None, destination=None, settings=None):
        '''
        *arg source : Driver Joint
        *arg destination : Rig Controller to be Bound
        *arg settings : a Bindsettings object
        '''
        self.BindNode = {}

        self.__source = None
        self.__dest = None
        if source:
            self.sourceNode = source
        if destination:
            self.destinationNode = destination

        if settings:
            if not issubclass(type(settings), Bindsettings):
                raise StandardError('settingsObj arg must be a Bindsettings Object')
            else:
                self.settings = settings
        else:
            # take a default instance of the settings Object
            log.info('Taking Default settingsObject')
            self.settings = Bindsettings()

        log.info(self.settings.print_settings())

    @property
    def sourceNode(self):
        return self.__source

    @sourceNode.setter
    def sourceNode(self, node):
        if not cmds.objExists(node):
            raise IOError('source node not valid')
        else:
            self.__source = pm.PyNode(node)

    @property
    def destinationNode(self):
        return self.__dest

    @destinationNode.setter
    def destinationNode(self, node):
        if not cmds.objExists(node):
            raise IOError('destination node not valid')
        else:
            self.__dest = pm.PyNode(node)

    def make_base_geo(self, GeoType, Name):
        '''
        Make the Base BindGeo Type
        '''
        node = None
        size = 3 * self.settings.base_scale
        if GeoType == 'Diamond':
            node = pm.curve(d=1, name=Name, p=[(size, 0, -size), (size, 0, size), (-size, 0, size),
                                           (-size, 0, -size), (size, 0, -size), (0, size, 0),
                                           (-size, 0, size), (0, -size, 0), (size, 0, -size),
                                           (size, 0, size), (0, size, 0), (-size, 0, -size),
                                           (0, -size, 0), (size, 0, size)])
        if GeoType == 'Locator':
            node = pm.spaceLocator(name=Name)
            node.getShape().localScaleX.set(size * 2)
            node.getShape().localScaleY.set(size * 2)
            node.getShape().localScaleZ.set(size * 2)

        # Set the overRides to Yellow
        node.overrideEnabled.set(1)
        node.overrideColor.set(17)
        return node

    @staticmethod
    def add_bind_markers(Ctr, BndNode=None):
        # message link this to the controller for the BakeCode to find
        if Ctr:
            if not Ctr.hasAttr(BAKE_MARKER):
                Ctr.addAttr(BAKE_MARKER, attributeType='message', multi=True, im=False)
        if BndNode:
            if not BndNode.hasAttr(BNDNODE_MARKER):
                BndNode.addAttr(BNDNODE_MARKER, attributeType='message', multi=True, im=False)
        if Ctr and BndNode:
            Ctr.BoundCtr >> BndNode.BindNode

    def make_bind_base(self, Name=None, GeoType='Diamond'):
        '''
        Make the unaligned BindGeo setup, this proc is overwritten for more complex binds
        Note: the BindNode is returned as a dic where ['Main'] is always the node that
        ultimately the constraints get made too, and ['Root'] is the root of the BindGroup
        *arg Name :  BaseName of the matchNode
        '''
        if not Name:
            Name = self.destinationNode.nodeName()
        self.BindNode['Main'] = self.make_base_geo(GeoType, '%s_BND' % Name)
        self.BindNode['Root'] = self.BindNode['Main']
        pm.select(self.BindNode['Root'])

    def align_bind_node(self):
        '''
        Align the newly made BindNode as required
        '''
        # Parent the BindNode to the Source Driver Node
        pm.parent(self.BindNode['Main'], self.sourceNode)

        # Positional Alignment
        if self.settings.align_to_control_trans:
            pm.delete(pm.pointConstraint(self.destinationNode, self.BindNode['Root']))
        if self.settings.align_to_source_trans:
            pm.delete(pm.pointConstraint(self.sourceNode, self.BindNode['Root']))

        # Rotation Alignment
        if self.settings.align_to_control_rots:
            pm.delete(pm.orientConstraint(self.destinationNode, self.BindNode['Root']))
        if self.settings.align_to_source_rots:
            pm.delete(pm.orientConstraint(self.sourceNode, self.BindNode['Root']))

    def link_bind_node(self):
        '''
        Make the actual driving connections between the Bind and Destination Nodes
        '''
        maintainOffsets = False
        # Make the Bind Between the Object
    #       if bind_trans and bind_rots:
    #           try:
    #               con=pm.parentConstraint(self.BindNode['Main'], self.destinationNode, mo=maintainOffsets)
    #               con.interpType.set(2)
    #           except:
    #               raise StandardError('ParentConstraint Bind could not be made')

        if self.settings.bind_trans:
            try:
                pm.pointConstraint(self.BindNode['Main'], self.destinationNode, mo=maintainOffsets)
            except:
                pass
        if self.settings.bind_rots:
            try:
                con = pm.orientConstraint(self.BindNode['Main'], self.destinationNode, mo=maintainOffsets)
                con.interpType.set(2)
            except:
                pass

        # Add the BindMarkers so that we can ID these nodes and connections later
        self.add_bind_markers(self.destinationNode, self.BindNode['Root'])

    def add_binder_node(self):
        '''
        Main Wrapper to make the AnimBind setup between Source and Destination nodes
        '''
        print('The current Driving Object (source) is : %s' % self.sourceNode.stripNamespace())
        print('The current Slave Object (destination) is : %s' % self.destinationNode.stripNamespace())

        self.make_bind_base(self.destinationNode.nodeName())  # Make the MatchObject and parent to the source
        self.align_bind_node()  # Align the new node to the Desitation Ctr
        self.link_bind_node()  # Constrain or Link the Ctrl to the New MatchNode

        if self.settings.reset_trans:
            log.info('resetting binders translates : %s', self.BindNode['Root'])
            self.BindNode['Root'].translate.set([0, 0, 0])
        if self.settings.reset_rots:
            log.info('resetting binders rotates : %s', self.BindNode['Main'])
            self.BindNode['Main'].rotate.set([0, 0, 0])


class BindNodeTwin(BindNodeBase):
    '''
    Second more complex Bind type used for the Wrists, Feet and any chain where you may
    need to isolate the rotate and translates. This allows you to easily extend the limb
    lengths whilst maintaining easily editable data.
    *arg source : Driver Joint
    *arg destination : Rig Controller to be Bound
    *arg settings : a Bindsettings object
    '''

    def __init__(self, source=None, destination=None, settings=None):
        super(BindNodeTwin, self).__init__(source, destination, settings)

    def make_bind_base(self, Name):
        '''
        Make the unaligned BindGeo and group/parent it up to the driver Source Joint
        Note: the BindNode is returns as a dic where ['Main'] is always the node that
        ultimately the constraints get made too, and ['Root'] is the root of the BindGroup
        *arg Name :  BaseName of the matchNode
        '''
        # Used for complex setups to separate the Trans/Rot Channels, good when over-keying
        self.BindNode['Main'] = self.make_base_geo('Diamond', '%s_Rots_BND' % Name)
        self.BindNode['Root'] = self.make_base_geo('Locator', '%s_Trans_BND' % Name)
        pm.parent(self.BindNode['Main'], self.BindNode['Root'])
        pm.select(self.BindNode['Root'])

    def align_bind_node(self, **kws):
        '''
        Overwrite the default behaviour: Align the newly made BindNode as required for this bind
        '''

        parentNode = self.sourceNode.listRelatives(p=True)[0]

        if parentNode:
            # Parent the BindNode to the Source Driver Node
            pm.parent(self.BindNode['Root'], self.sourceNode.listRelatives(p=True)[0])
        else:
            pm.parent(self.BindNode['Root'], self.sourceNode)

        self.BindNode['Main'].rotateOrder.set(self.sourceNode.rotateOrder.get())
        self.BindNode['Root'].rotateOrder.set(self.destinationNode.rotateOrder.get())

        # Positional Alignment
        if self.settings.align_to_control_trans:
            pm.delete(pm.pointConstraint(self.sourceNode, self.BindNode['Root']))
            pm.makeIdentity(self.BindNode['Root'], apply=True, t=1, r=0, s=0)
            pm.delete(pm.pointConstraint(self.destinationNode, self.BindNode['Root']))
        if self.settings.align_to_source_trans:
            pm.delete(pm.pointConstraint(self.sourceNode, self.BindNode['Root']))
            pm.makeIdentity(self.BindNode['Root'], apply=True, t=1, r=0, s=0)

        # Rotation Alignment
        if parentNode:
            pm.orientConstraint(self.sourceNode, self.BindNode['Root'])

        if self.settings.align_to_control_rots:
            pm.delete(pm.orientConstraint(self.destinationNode, self.BindNode['Main']))
        if self.settings.align_to_source_rots:
            pm.delete(pm.orientConstraint(self.sourceNode, self.BindNode['Main']))


class BindNodeAim(BindNodeBase):
    '''
    Third more complex Bind type used for complex Spine issues. Unlike the other
    methods this uses an AimConstraint to point the controller towards a target
    node to extract a rotation vector. This gets over issues with complex spline
    setups where the previous 2 methods would send in incorrect rotation data.
    *arg source : Driver Aim Node
    *arg destination : Rig Controller to be Bound
    *arg upVector : UpVector and Parent node for the AimConstraint
    *arg settings : a Bindsettings object
    '''

    def __init__(self, source=None, destination=None, upVector=None, settings=None):
        super(BindNodeAim, self).__init__(source, destination, settings)
        # Extra arg passed into the Aim BND. This becomes the parent for the
        # BND nodes as well as the location for the UpVector locator fed into
        # the AimConstraint. The Source in this instance becomes the AimObject
        self.upVectorParent = upVector
        if self.settings.align_to_source_trans or self.settings.align_to_source_rots:
            raise UserWarning('AlignToSource settings are NOT VALID for the AimBnd setups')

    def make_bind_base(self, Name):
        '''
        Make the unaligned BindGeo and group/parent it up to the driver Source Joint
        Note: the BindNode is returns as a dic where ['Main'] is always the node that
        ultimately the constraints get made too, and ['Root'] is the root of the BindGroup
        *arg Name :  BaseName of the matchNode
        '''
        # Used for complex setups to separate the Trans/Rot Channels, good when over-keying
        # tempScale=self.settings.base_scale
        self.BindNode['Main'] = self.make_base_geo('Diamond', '%s_Rots_BND' % Name)
        self.BindNode['Root'] = self.make_base_geo('Locator', '%s_Trans_BND' % Name)
        self.BindNode['Up'] = self.make_base_geo('Locator', '%s_UpVector_BND' % Name)
        self.BindNode['AimOffset'] = self.make_base_geo('Locator', '%s_AimOffset_BND' % Name)

        # self.settings.base_scale=tempScale*0.25
        pm.parent(self.BindNode['Main'], self.BindNode['Root'])
        # self.settings.base_scale=tempScale
        pm.select(self.BindNode['Root'])

    def align_bind_node(self, **kws):
        '''
        Overwrite the default behaviour: Align the newly made BindNode as required for this bind
        '''

        # Parent the BindNode/UpVector Object to the upVectorParent Node
        # Parent the AimLocator Object to the Source node -used to modify the AimPoint
        pm.parent(self.BindNode['Root'], self.upVectorParent)
        pm.parent(self.BindNode['Up'], self.upVectorParent)
        pm.parent(self.BindNode['AimOffset'], self.sourceNode)

        # self.BindNode['Root'].scale.set(self.settings.base_scale,self.settings.base_scale,self.settings.base_scale)
        self.BindNode['Main'].rotateOrder.set(self.sourceNode.rotateOrder.get())
        self.BindNode['Root'].rotateOrder.set(self.destinationNode.rotateOrder.get())

        # Aim Alignment
        pm.aimConstraint(self.BindNode['AimOffset'], self.BindNode['Root'], aimVector=(0, 1, 0), upVector=(0, 0, 1),
                             worldUpType="object", worldUpObject=self.BindNode['Up'])

        # Positional Alignment
        pm.delete(pm.pointConstraint(self.sourceNode, self.BindNode['AimOffset']))
        pm.makeIdentity(self.BindNode['AimOffset'], apply=True, t=1, r=1, s=0)
        pm.delete(pm.pointConstraint(self.upVectorParent, self.BindNode['Root']))
        pm.makeIdentity(self.BindNode['Root'], apply=True, t=1, r=0, s=0)
        pm.delete(pm.pointConstraint(self.upVectorParent, self.BindNode['Up']))
        pm.makeIdentity(self.BindNode['Up'], apply=True, t=1, r=0, s=0)
        pm.delete(pm.pointConstraint(self.destinationNode, self.BindNode['Root']))

        # Rotate Alignment
        pm.delete(pm.orientConstraint(self.destinationNode, self.BindNode['Main']))


class AnimBinderUI(object):
    def __init__(self):
        self.win = 'AnimBinder'
        self.settings = Bindsettings()

    @staticmethod
    def _contactDetails(opentype='email'):
        if opentype == 'email':
            cmds.confirmDialog(title='Contact',
                           message=("Autodesk MasterClass - Live Animation Binding\n" +
                                    "Mark Jackson\n" +
                                    "____________________________________________\n\n" +
                                    "Contact: markj3d@gmail.com"), \
                           button='thankyou', messageAlign='center')
        elif opentype == 'blog':
            import webbrowser
            webbrowser.open_new("http://markj3d.blogspot.com/")
        elif opentype == 'vimeo':
            import webbrowser
            webbrowser.open_new("https://vimeo.com/31046583")

    def _UI(self):
        if cmds.window(self.win, exists=True):
            cmds.deleteUI(self.win, window=True)
        cmds.window(self.win, title=self.win, menuBar=True, sizeable=True, widthHeight=(300, 380))

        cmds.menu(label='Help')
        cmds.menuItem(label='Watch MasterClass Video', c=lambda x: self._contactDetails(opentype='vimeo'))
        cmds.menuItem(label='Contact', c=r9Setup.red9ContactInfo)
        # cmds.menuItem(label='Contact', c=lambda x:self._contactDetails(opentype='email'))
        cmds.menuItem(label='Blog', c=r9Setup.red9_blog)
        cmds.menuItem(label='Red9HomePage', c=r9Setup.red9_website_home)

        cmds.columnLayout(adjustableColumn=True)
        cmds.text(fn="boldLabelFont", label="Advanced Bind Options")
        cmds.separator(h=15, style="none")
        cmds.rowColumnLayout(numberOfColumns=2, cw=((1, 150), (2, 150)), cs=((1, 10)))
        cmds.checkBox(value=self.settings.bind_rots, label="bind_rots", ann="Bind only the Rotates of the given Controller", al="left",
                      onc=lambda x: self.settings.__setattr__('bind_rots', True),
                      ofc=lambda x: self.settings.__setattr__('bind_rots', False))
        cmds.checkBox(value=self.settings.bind_trans, label="bind_trans", ann="Bind only the Translates of the given Controller", al="left",
                      onc=lambda x: self.settings.__setattr__('bind_trans', True),
                      ofc=lambda x: self.settings.__setattr__('bind_trans', False))
        cmds.checkBox(value=1, label="AlignRots CtrSpace", ann="Force the BindLocator to the position of the Controller", al="left",
                      onc=lambda x: self.settings.__setattr__('align_to_control_rots', True),
                      ofc=lambda x: self.settings.__setattr__('align_to_source_rots', True))
        cmds.checkBox(value=1, label="AlignTrans CtrSpace", ann="Force the BindLocator to the position of the Controller", al="left",
                      onc=lambda x: self.settings.__setattr__('align_to_control_trans', True),
                      ofc=lambda x: self.settings.__setattr__('align_to_source_trans', True))
        cmds.checkBox(value=self.settings.reset_rots, label="Reset Rots Offsets", ann="Reset any Offset during bind, snapping the systems together", al="left",
                      onc=lambda x: self.settings.__setattr__('reset_rots', True),
                      ofc=lambda x: self.settings.__setattr__('reset_rots', False))
        cmds.checkBox(value=self.settings.reset_trans, label="Reset Trans Offsets", ann="Reset any Offset during bind, snapping the systems together", al="left",
                      onc=lambda x: self.settings.__setattr__('reset_trans', True),
                      ofc=lambda x: self.settings.__setattr__('reset_trans', False))

        cmds.setParent('..')
        cmds.separator(h=10, style="none")
        cmds.button(label="BasicBind", al="center",
                    ann="Select the Joint on the driving Skeleton then the Controller to be driven",
                    c=lambda x: BindNodeBase(cmds.ls(sl=True, l=True)[0], cmds.ls(sl=True, l=True)[1], settings=self.settings).add_binder_node())
        cmds.button(label="ComplexBind", al="center",
                    ann="Select the Joint on the driving Skeleton then the Controller to be driven",
                    c=lambda x: BindNodeTwin(cmds.ls(sl=True, l=True)[0], cmds.ls(sl=True, l=True)[1], settings=self.settings).add_binder_node())
        cmds.button(label="AimerBind", al="center",
                    ann="Select the Joint on the driving Skeleton to AIM at, then the Controller to be driven, finally a node on the driven skeleton to use as UpVector",
                    c=lambda x: BindNodeAim(cmds.ls(sl=True, l=True)[0], cmds.ls(sl=True, l=True)[1], cmds.ls(sl=True, l=True)[2], settings=self.settings).add_binder_node())
        cmds.separator(h=15, style="none")
        cmds.rowColumnLayout(numberOfColumns=2, columnWidth=[(1, 147), (2, 147)])

        cmds.button(label="Add BakeMarker", al="center",
                    ann="Add the BoundCtrl / Bake Marker to the selected nodes",
                    c=lambda x: add_bind_markers(cmds.ls(sl=True, l=True)))
        cmds.button(label="remove BakeMarker", al="center",
                    ann="Remove the BoundCtrl / Bake Marker from the selected nodes",
                    c=lambda x: removeBindMarker(cmds.ls(sl=True, l=True)))

        cmds.button(label="Select BindNodes", al="center",
                    ann="Select Top Group Node of the Source Binder",
                    c=lambda x: pm.select(get_bind_nodes(cmds.ls(sl=True, l=True))))
        cmds.button(label="Select BoundControls", al="center",
                    ann="Select Top Group Node of the Bound Rig",
                    c=lambda x: pm.select(get_bound_controls(cmds.ls(sl=True, l=True))))
        cmds.setParent('..')
        cmds.rowColumnLayout(numberOfColumns=2, columnWidth=[(1, 200), (2, 74)], columnSpacing=[(2, 5)])
        cmds.button(label="Bake Binder", al="center",
                    ann="Select Top Group Node of the Bound Rig",
                    c=lambda x: bake_binder_data(cmds.ls(sl=True, l=True), self.settings.bake_debug))
        cmds.checkBox(value=self.settings.bake_debug, label="Debug View",
                      ann="Keep viewport active to observe the baking process", al="left",
                      onc=lambda x: self.settings.__setattr__('bake_debug', True),
                      ofc=lambda x: self.settings.__setattr__('bake_debug', False))
        cmds.setParent('..')
        cmds.separator(h=10, style="none")
        cmds.button(label="Link Skeleton Hierarchies - Direct Connect", al="center",
                    ann="Select Root joints of the source and destination skeletons to be connected - connect via attrs",
                    c=lambda x: bind_skeletons(cmds.ls(sl=True)[0], cmds.ls(sl=True)[1], method='connect', verbose=True))
        cmds.button(label="Link Skeleton Hierarchies - Constraints", al="center",
                    ann="Select Root joints of the source and destination skeletons to be connected - connect via parentConstraints",
                    c=lambda x: bind_skeletons(cmds.ls(sl=True)[0], cmds.ls(sl=True)[1], method='constrain', verbose=True))
        cmds.separator(h=10, style="none")
        cmds.button(label="MakeStabilizer", al="center",
                    ann="Select the nodes you want to extract the motion data from",
                    c=lambda x: make_stabilized_node())

        cmds.separator(h=20, style="none")
        cmds.iconTextButton(style='iconOnly', bgc=(0.7, 0, 0), image1='Rocket9_buttonStrap2.bmp',
                                 c=lambda *args: (r9Setup.red9ContactInfo()), h=22, w=200)
        cmds.showWindow(self.win)
        cmds.window(self.win, e=True, h=400)

    @classmethod
    def Show(cls):
        if r9Setup.has_pro_pack():
            cmds.confirmDialog(title='UI Deprecated',
                               message=('This version of the AnimationBinder has been superseded by '
                                        'the new build in Red9 ProPack and is here for legacy purposes.\n'
                                        '\nIf making a fresh Binder we recommend using the version in ProPack!'),
                               icon='information',
                               button='thankyou', messageAlign='center')
        cls()._UI()


def get_bind_nodes(rootNode=None):
    '''
    From selected root find all BindNodes via the marker attribute 'BindNode'
    Note we're not casting to PyNodes here for speed here
    '''
    if not rootNode:
        raise StandardError('Please Select a node to search from:')
    return [node for node in cmds.listRelatives(rootNode, ad=True, f=True)
            if cmds.attributeQuery(BNDNODE_MARKER, exists=True, node=node)]

def get_bound_controls(rootNode=None):
    '''
    From selected root find all BoundControllers via the marker attribute 'BoundCtr'
    Note we're not casting to PyNodes here for speed here
    '''
    if not rootNode:
        raise StandardError('Please Select a node to search from:')
    return [node for node in cmds.listRelatives(rootNode, ad=True, f=True)
             if cmds.attributeQuery(BAKE_MARKER, exists=True, node=node)]

def bake_binder_data(rootNode=None, debugView=False, runFilter=True, ignoreInFilter=[]):
    '''
    From a given Root Node search all children for the 'BoundCtr' attr marker. If none
    were found then search for the BindNode attr and use the message links to walk to
    the matching Controller.
    Those found are then baked out and the marker attribute is deleted
    '''
    BoundCtrls = get_bound_controls(rootNode)

    # Found no Ctrls, try and walk the message from the BndNodes
    if not BoundCtrls:
        BndNodes = get_bind_nodes()
        for node in BndNodes:
            cons = cmds.listConnections('%s.%s' % (node, BNDNODE_MARKER))
            if cons:
                BoundCtrls.append(cmds.ls(cons[0], l=True)[0])
            else:
                log.info('Nothing connected to %s.%s' % (node, BNDNODE_MARKER))

    if BoundCtrls:
        try:
            if not debugView:
                cmds.refresh(su=True)
            with r9General.AnimationContext():
                cmds.bakeResults(BoundCtrls, simulation=True,
                             sampleBy=1,
                             time=(cmds.playbackOptions(q=True, min=True), cmds.playbackOptions(q=True, max=True)),
                             disableImplicitControl=True,
                             preserveOutsideKeys=True,
                             sparseAnimCurveBake=True,
                             removeBakedAttributeFromLayer=False,
                             controlPoints=False,
                             shape=False)

            for node in BoundCtrls:
                # Remove the BindMarker from the baked node
                try:
                    cmds.deleteAttr('%s.%s' % (node, BAKE_MARKER))
                except StandardError, error:
                    log.info(error)
            if ignoreInFilter:
                BoundCtrls = [node for node in BoundCtrls if node.split('|')[-1].split(':')[-1] not in ignoreInFilter]
            if runFilter:
                cmds.filterCurve(BoundCtrls)
            cmds.delete(BoundCtrls, sc=True)  # static channels
        except StandardError, error:
            raise StandardError(error)
        finally:
            cmds.refresh(su=False)
            cmds.refresh(f=True)
    else:
        raise StandardError("Couldn't find any BinderMarkers in given hierarchy")
    return True

def match_given_hierarchys(source, dest):
    '''
    Simple node name matching that strips any DAG path and namespaces prior to matching
    '''
    nameMatched = []
    if not isinstance(source, list):
        source = [source]
    if not isinstance(dest, list):
        dest = [dest]

    for sJnt in source:
        for dJnt in dest:
            if sJnt.split('|')[-1].split(':')[-1] == dJnt.split('|')[-1].split(':')[-1]:
                nameMatched.append((sJnt, dJnt))
                break
    return nameMatched

def bind_skeletons(source, dest, method='connect', scales=False, verbose=False, unlock=False):
    '''
    From 2 given root joints search through each hierarchy for child joints, match
    them based on node name, then connect their trans/rots directly, or
    parentConstrain them. Again cmds for speed

    :param source: the root node of the driving skeleton
    :param dest: the root node of the driven skeleton
    :param method: the method used for the connection, either 'connect' or 'constrain'
    :param scale: do we bind the scales of the destination skel to the source??
    :param unlock: if True force unlock the required transform attrs on the destination skeleton first
    '''

    sourceJoints = cmds.listRelatives(source, ad=True, f=True, type='joint')
    destJoints = cmds.listRelatives(dest, ad=True, f=True, type='joint')

    if verbose:
        result = cmds.confirmDialog(title='Bind Skeletons SCALES',
                            message=("Would you also like to process the SCALE channels within the bind?"),
                            button=['Yes', 'No'],
                            messageAlign='center', icon='question',
                            dismissString='Cancel')
        if result == 'Yes':
            scales = True
        else:
            scales = False

    # parent constrain the root nodes regardless of bindType, fixes issues where
    # we have additional rotated parent groups on the source
    cmds.parentConstraint(source, dest)
    if scales:
        cmds.scaleConstraint(source, dest, mo=True)

    # attrs to 'connect' and also to ensure are unlocked
    attrs = ['rotateX', 'rotateY', 'rotateZ', 'translateX', 'translateY', 'translateZ']
    if scales:
        attrs = attrs + ['scaleX', 'scaleY', 'scaleZ', 'inverseScale']
    if unlock:
        r9Core.LockChannels().processState(dest, attrs=attrs, mode='fullkey', hierarchy=True)

    for sJnt, dJnt in match_given_hierarchys(sourceJoints, destJoints):
        if method == 'connect':
            for attr in attrs:
                try:
                    cmds.connectAttr('%s.%s' % (sJnt, attr), '%s.%s' % (dJnt, attr), f=True)
                except:
                    pass
        elif method == 'constrain':
            # need to see if the channels are open if not, change this binding code
            try:
                cmds.parentConstraint(sJnt, dJnt, mo=True)
            except:
                chns = r9Anim.getSettableChannels(dJnt)
                if all(['translateX' in chns, 'translateY' in chns, 'translateZ' in chns]):
                    cmds.pointConstraint(sJnt, dJnt, mo=True)
                elif all(['rotateX' in chns, 'rotateY' in chns, 'rotateZ' in chns]):
                    cmds.orientConstraint(sJnt, dJnt, mo=True)
                else:
                    log.info('Failed to Bind joints: %s >> %s' % (sJnt, dJnt))

            # if we have incoming scale connections then run the scaleConstraint
            if scales:  # and cmds.listConnections('%s.sx' % sJnt):
                try:
                    cmds.scaleConstraint(sJnt, dJnt, mo=True)
                    # turn off the compensation so that the rig can still be scaled correctly by the MasterNode
                    # cmds.setAttr('%s.segmentScaleCompensate' % dJnt, 0)
                except:
                    print('failed : scales ', dJnt)


def make_stabilized_node(nodeName=None, centered=True):
    '''
    Very simple proc to generate a Stabilized node for
    raw MoCap tracking purposes... First selected node
    is used as the Aim axis, second selected is used as this
    aim's worldUp
    '''
    RequiredMarkers = pm.ls(sl=True, l=True)
    # pos = pm.xform(WorldUpObj, q=True, ws=True, t=True)
    curve = pm.curve(ws=True, d=1, p=(0, 0, 0), k=0)

    if centered:
        AimAt = RequiredMarkers[0]
        WorldUpObj = RequiredMarkers[1]
        pm.pointConstraint(RequiredMarkers, curve)
    else:
        AimAt = RequiredMarkers[1]
        WorldUpObj = RequiredMarkers[2]
        pm.pointConstraint(RequiredMarkers[0], curve)

    pm.aimConstraint((AimAt, curve),
                     weight=1,
                     aimVector=(0, 0, 1),
                     upVector=(0, 1, 0),
                     worldUpType="object",
                     worldUpObject=WorldUpObj)

    # Snap a curveKnot to the pivot of all referenceMarkers
    for node in RequiredMarkers:
        pm.curve(curve, a=True, ws=True, p=(pm.xform(node, q=True, ws=True, t=True)))
    pm.curve(curve, a=True, ws=True, p=(pm.xform(AimAt, q=True, ws=True, t=True)))

    return curve

def add_bind_markers(ctrls=None, *args):
    '''
    add the bind markers to nodes, these dictate what gets baked
    '''
    if not ctrls:
        ctrls = cmds.ls(sl=True, l=True)
    for ctr in ctrls:
        print(pm.PyNode(ctr))
        BindNodeBase.add_bind_markers(pm.PyNode(ctr))

def removeBindMarker(ctrls=None, *args):
    '''
    remove the bind markers from nodes, these dictate what gets baked
    '''
    if not ctrls:
        ctrls = cmds.ls(sl=True, l=True)
    for ctr in ctrls:
        cmds.deleteAttr('%s.%s' % (ctr, BAKE_MARKER))
