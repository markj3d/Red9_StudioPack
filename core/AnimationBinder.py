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
    
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    I'll probably put this file and any updates to it on my blog in the
    near future.
    
    Thanks for trying the workflows, all comments more than welcomed

    PLEASE NOTE: this code is in the process of being re-built for the 
    Red9 ProPack where we intend to bind HIK to the remapping by default
    
    
########################################################################
'''



#import maya.cmds as cmds
#import maya.mel as mel
import maya.cmds as cmds
import pymel.core as pm
#import Red9_AnimationUtils as r9Anim
import Red9.startup.setup as r9Setup

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
#log.setLevel(logging.DEBUG)
########################################################################


BAKE_MARKER='BoundCtr'
BNDNODE_MARKER='BindNode'

class BindSettings(object):
    
    def __init__(self):
        '''
        Settings object that we pass to the Binder Classes directly, keeps the code clean
        '''
        self.BindTrans = True
        self.BindRots = True
        self.ResetTranslates = True
        self.ResetRotates = False
        self.BaseScale = 1
        self.BakeDebug = False
        self.__alignToControlTrans = True
        self.__alignToControlRots = True
        self.__alignToSourceTrans = False
        self.__alignToSourceRots = False
        
    @property
    def AlignToControlTrans(self):
        return self.__alignToControlTrans
    @AlignToControlTrans.setter
    def AlignToControlTrans(self, value):
        if value:
            self.__alignToSourceTrans = False
            self.__alignToControlTrans = True
            log.info('AlignToControlTrans=True, Switching AlignToSourceTrans=False')
        else:
            self.__alignToControlTrans = False
      
    @property
    def AlignToSourceTrans(self):
        return self.__alignToSourceTrans
    @AlignToSourceTrans.setter
    def AlignToSourceTrans(self, value):
        if value:
            self.__alignToControlTrans = False
            self.__alignToSourceTrans = True
            log.info('AlignToSourceTrans=True, Switching AlignToControlTrans=False')
        else:
            self.__alignToSourceTrans = False

    @property
    def AlignToControlRots(self):
        return self.__alignToControlRots
    @AlignToControlRots.setter
    def AlignToControlRots(self, value):
        if value:
            self.__alignToSourceRots = False
            self.__alignToControlRots = True
            log.info('AlignToControlRots=True, Switching AlignToSourceRots=False')
        else:
            self.__alignToControlRots = False

    @property
    def AlignToSourceRots(self):
        return self.__alignToSourceRots
    @AlignToSourceRots.setter
    def AlignToSourceRots(self, value):
        if value:
            self.__alignToControlRots = False
            self.__alignToSourceRots = True
            log.info('AlignToSourceRots=True, Switching AlignToControlRots=False')
        else:
            self.__alignToSourceRots = False

    def Print(self):
        #for key,value in self.__dict__.items():print key,value
        log.info(self.__dict__)


class BindNodeBase(object):

    def __init__(self, source, destination, settings=None):
        '''
        *arg source : Driver Joint
        *arg destination : Rig Controller to be Bound
        *arg settings : a BindSettings object
        '''
        self.__sourceNode = None
        self.__destinationNode = None
        self.BindNode = {}

        if settings:
            if not issubclass(type(settings), BindSettings):
                raise StandardError('settingsObj arg must be a BindSettings Object')
            else:
                self.Settings = settings
        else:
            #take a default instance of the Settings Object
            log.info('Taking Default SettingsObject')
            self.Settings = BindSettings()
            
        log.info(self.Settings.Print())
        self.SourceNode = source
        self.DestinationNode = destination

    @property
    def SourceNode(self):
        return self.__sourceNode
    @SourceNode.setter
    def SourceNode(self, value):
        if value:
            self.__sourceNode = pm.PyNode(value)
        else:
            raise StandardError('Source Node Not Found')
        
    @property
    def DestinationNode(self):
        return self.__destinationNode
    @DestinationNode.setter
    def DestinationNode(self, value):
        if value:
            self.__destinationNode = pm.PyNode(value)
        else:
            raise StandardError('Destination Node Not Found')

    def MakeBaseGeo(self, GeoType, Name):
        '''
        Make the Base BindGeo Type
        '''
        node = None
        size = 3 * self.Settings.BaseScale
        if GeoType == 'Diamond':
            node = pm.curve(d=1, name=Name, p=[(size, 0, -size), (size, 0, size), (-size, 0, size), \
                                           (-size, 0, -size), (size, 0, -size), (0, size, 0), \
                                           (-size, 0, size), (0, -size, 0), (size, 0, -size), \
                                           (size, 0, size), (0, size, 0), (-size, 0, -size), \
                                           (0, -size, 0), (size, 0, size)])
        if GeoType == 'Locator':
            node = pm.spaceLocator(name=Name)
            node.getShape().localScaleX.set(size * 2)
            node.getShape().localScaleY.set(size * 2)
            node.getShape().localScaleZ.set(size * 2)
            
        #Set the overRides to Yellow
        node.overrideEnabled.set(1)
        node.overrideColor.set(17)
        return node

    @staticmethod
    def AddBindMarkers(Ctr, BndNode=None):
        #message link this to the controller for the BakeCode to find
        if Ctr:
            print 'Ctrl'
            if not Ctr.hasAttr(BAKE_MARKER):
                print 'addAttr'
                Ctr.addAttr(BAKE_MARKER, attributeType='message', multi=True, im=False)
        if BndNode:
            if not BndNode.hasAttr(BNDNODE_MARKER):
                BndNode.addAttr(BNDNODE_MARKER, attributeType='message', multi=True, im=False)
        if Ctr and BndNode:
            Ctr.BoundCtr>>BndNode.BindNode
        
        
    def MakeBindBase(self, Name, GeoType='Diamond'):
        '''
        Make the unaligned BindGeo setup, this proc is overwritten for more complex binds
        Note: the BindNode is returned as a dic where ['Main'] is always the node that
        ultimately the constraints get made too, and ['Root'] is the root of the BindGroup
        *arg Name :  BaseName of the matchNode
        '''
        self.BindNode['Main'] = self.MakeBaseGeo(GeoType, '%s_BND' % Name)
        self.BindNode['Root'] = self.BindNode['Main']
        pm.select(self.BindNode['Root'])


    def AlignBindNode(self):
        '''
        Align the newly made BindNode as required
        '''
        #Parent the BindNode to the Source Driver NOde
        pm.parent(self.BindNode['Main'], self.SourceNode)
    
        #Positional Alignment
        if self.Settings.AlignToControlTrans:
            pm.delete(pm.pointConstraint(self.DestinationNode, self.BindNode['Root']))
        if self.Settings.AlignToSourceTrans:
            pm.delete(pm.pointConstraint(self.SourceNode, self.BindNode['Root']))

        #Rotation Alignment
        if self.Settings.AlignToControlRots:
            pm.delete(pm.orientConstraint(self.DestinationNode, self.BindNode['Root']))
        if self.Settings.AlignToSourceRots:
            pm.delete(pm.orientConstraint(self.SourceNode, self.BindNode['Root']))


    def LinkBindNode(self):
        '''
        Make the actual driving connections between the Bind and Destination Nodes
        '''
        maintainOffsets = False
        # Make the Bind Between the Object
    #       if BindTrans and BindRots:
    #           try:
    #               con=pm.parentConstraint(self.BindNode['Main'], self.DestinationNode, mo=maintainOffsets)
    #               con.interpType.set(2)
    #           except:
    #               raise StandardError('ParentConstraint Bind could not be made')

        if self.Settings.BindTrans:
            try:
                pm.pointConstraint(self.BindNode['Main'], self.DestinationNode, mo=maintainOffsets)
            except:
                pass
        if self.Settings.BindRots:
            try:
                con = pm.orientConstraint(self.BindNode['Main'], self.DestinationNode, mo=maintainOffsets)
                con.interpType.set(2)
            except:
                pass

        #Add the BindMarkers so that we can ID these nodes and connections later
        self.AddBindMarkers(self.DestinationNode, self.BindNode['Root'])


    def AddBinderNode(self):
        '''
        Main Wrapper to make the AnimBind setup between Source and Destination nodes
        '''
        print ('The current Driving Object (source) is : %s' % self.SourceNode.stripNamespace())
        print ('The current Slave Object (destination) is : %s' % self.DestinationNode.stripNamespace())

        self.MakeBindBase(self.DestinationNode.nodeName())  # Make the MatchObject and parent to the source
        self.AlignBindNode()            # Align the new node to the Desitation Ctr
        self.LinkBindNode()             # Constrain or Link the Ctrl to the New MatchNode
        
        if self.Settings.ResetTranslates:
            log.info('resetting binders translates : %s', self.BindNode['Root'])
            self.BindNode['Root'].translate.set([0, 0, 0])
        if self.Settings.ResetRotates:
            log.info('resetting binders rotates : %s', self.BindNode['Main'])
            self.BindNode['Main'].rotate.set([0, 0, 0])
    


class BindNodeTwin(BindNodeBase):
    '''
    Second more complex Bind type used for the Wrists, Feet and any chain where you may
    need to isolate the rotate and translates. This allows you to easily extend the limb
    lengths whilst maintaining easily editable data.
    *arg source : Driver Joint
    *arg destination : Rig Controller to be Bound
    *arg settings : a BindSettings object
    '''
    
    def __init__(self, source, destination, settings):
        super(BindNodeTwin, self).__init__(source, destination, settings)

    def MakeBindBase(self, Name):
        '''
        Make the unaligned BindGeo and group/parent it up to the driver Source Joint
        Note: the BindNode is returns as a dic where ['Main'] is always the node that
        ultimately the constraints get made too, and ['Root'] is the root of the BindGroup
        *arg Name :  BaseName of the matchNode
        '''
        #Used for complex setups to separate the Trans/Rot Channels, good when over-keying
        self.BindNode['Main'] = self.MakeBaseGeo('Diamond', '%s_Rots_BND' % Name)
        self.BindNode['Root'] = self.MakeBaseGeo('Locator', '%s_Trans_BND' % Name)
        pm.parent(self.BindNode['Main'], self.BindNode['Root'])
        pm.select(self.BindNode['Root'])


    def AlignBindNode(self, **kws):
        '''
        Overwrite the default behaviour: Align the newly made BindNode as required for this bind
        '''

        parentNode = self.SourceNode.listRelatives(p=True)[0]

        if parentNode:
            #Parent the BindNode to the Source Driver Node
            pm.parent(self.BindNode['Root'], self.SourceNode.listRelatives(p=True)[0])
        else:
            pm.parent(self.BindNode['Root'], self.SourceNode)

        self.BindNode['Main'].rotateOrder.set(self.SourceNode.rotateOrder.get())
        self.BindNode['Root'].rotateOrder.set(self.DestinationNode.rotateOrder.get())

        #Positional Alignment
        if self.Settings.AlignToControlTrans:
            pm.delete(pm.pointConstraint(self.SourceNode, self.BindNode['Root']))
            pm.makeIdentity(self.BindNode['Root'], apply=True, t=1, r=0, s=0)
            pm.delete(pm.pointConstraint(self.DestinationNode, self.BindNode['Root']))
        if self.Settings.AlignToSourceTrans:
            pm.delete(pm.pointConstraint(self.SourceNode, self.BindNode['Root']))
            pm.makeIdentity(self.BindNode['Root'], apply=True, t=1, r=0, s=0)

        #Rotation Alignment
        if parentNode:
            pm.orientConstraint(self.SourceNode, self.BindNode['Root'])

        if self.Settings.AlignToControlRots:
            pm.delete(pm.orientConstraint(self.DestinationNode, self.BindNode['Main']))
        if self.Settings.AlignToSourceRots:
            pm.delete(pm.orientConstraint(self.SourceNode, self.BindNode['Main']))


class BindNodeAim(BindNodeBase):
    '''
    Third more complex Bind type used for complex Spine issues. Unlike the other
    methods this uses an AimConstraint to point the controller towards a target
    node to extract a rotation vector. This gets over issues with complex spline
    setups where the previous 2 methods would send in incorrect rotation data.
    *arg source : Driver Aim Node
    *arg destination : Rig Controller to be Bound
    *arg upVector : UpVector and Parent node for the AimConstraint
    *arg settings : a BindSettings object
    '''
    
    def __init__(self, source, destination, upVector, settings=None):
        super(BindNodeAim, self).__init__(source, destination, settings)
        #Extra arg passed into the Aim BND. This becomes the parent for the
        #BND nodes as well as the location for the UpVector locator fed into
        #the AimConstraint. The Source in this instance becomes the AimObject
        self.upVectorParent = upVector
        if self.Settings.AlignToSourceTrans or self.Settings.AlignToSourceRots:
            raise UserWarning('AlignToSource settings are NOT VALID for the AimBnd setups')
        
    def MakeBindBase(self, Name):
        '''
        Make the unaligned BindGeo and group/parent it up to the driver Source Joint
        Note: the BindNode is returns as a dic where ['Main'] is always the node that
        ultimately the constraints get made too, and ['Root'] is the root of the BindGroup
        *arg Name :  BaseName of the matchNode
        '''
        #Used for complex setups to separate the Trans/Rot Channels, good when over-keying
        #tempScale=self.Settings.BaseScale
        self.BindNode['Main'] = self.MakeBaseGeo('Diamond', '%s_Rots_BND' % Name)
        self.BindNode['Root'] = self.MakeBaseGeo('Locator', '%s_Trans_BND' % Name)
        self.BindNode['Up'] = self.MakeBaseGeo('Locator', '%s_UpVector_BND' % Name)
        self.BindNode['AimOffset'] = self.MakeBaseGeo('Locator', '%s_AimOffset_BND' % Name)
           
        #self.Settings.BaseScale=tempScale*0.25
        pm.parent(self.BindNode['Main'], self.BindNode['Root'])
        #self.Settings.BaseScale=tempScale
        pm.select(self.BindNode['Root'])


    def AlignBindNode(self, **kws):
        '''
        Overwrite the default behaviour: Align the newly made BindNode as required for this bind
        '''

        #Parent the BindNode/UpVector Object to the upVectorParent Node
        #Parent the AimLocator Object to the Source node -used to modify the AimPoint
        pm.parent(self.BindNode['Root'], self.upVectorParent)
        pm.parent(self.BindNode['Up'], self.upVectorParent)
        pm.parent(self.BindNode['AimOffset'], self.SourceNode)

        #self.BindNode['Root'].scale.set(self.Settings.BaseScale,self.Settings.BaseScale,self.Settings.BaseScale)
        self.BindNode['Main'].rotateOrder.set(self.SourceNode.rotateOrder.get())
        self.BindNode['Root'].rotateOrder.set(self.DestinationNode.rotateOrder.get())

        #Aim Alignment
        pm.aimConstraint(self.BindNode['AimOffset'], self.BindNode['Root'], aimVector=(0,1,0),upVector=(0,0,1),\
                             worldUpType="object",worldUpObject=self.BindNode['Up'])

        #Positional Alignment
        pm.delete(pm.pointConstraint(self.SourceNode, self.BindNode['AimOffset']))
        pm.makeIdentity(self.BindNode['AimOffset'], apply=True, t=1, r=1, s=0)
        pm.delete(pm.pointConstraint(self.upVectorParent, self.BindNode['Root']))
        pm.makeIdentity(self.BindNode['Root'], apply=True, t=1, r=0, s=0)
        pm.delete(pm.pointConstraint(self.upVectorParent, self.BindNode['Up']))
        pm.makeIdentity(self.BindNode['Up'], apply=True, t=1, r=0, s=0)
        pm.delete(pm.pointConstraint(self.DestinationNode, self.BindNode['Root']))
        
        #Rotate Alignment
        pm.delete(pm.orientConstraint(self.DestinationNode, self.BindNode['Main']))


class AnimBinderUI(object):
    def __init__(self):
        self.win = 'AnimBinder'
        self.settings = BindSettings()
    
    @staticmethod
    def _contactDetails(opentype='email'):
        if opentype=='email':
            cmds.confirmDialog(title='Contact', \
                           message=("Autodesk MasterClass - Live Animation Binding\n" +
                                    "Mark Jackson\n" +
                                    "____________________________________________\n\n" +
                                    "Contact: markj3d@gmail.com"), \
                           button='thankyou', messageAlign='center')
        elif opentype=='blog':
            import webbrowser
            webbrowser.open_new("http://markj3d.blogspot.com/")
        elif opentype=='vimeo':
            import webbrowser
            webbrowser.open_new("https://vimeo.com/31046583")
 
    def _UI(self):
        if cmds.window(self.win, exists=True):
            cmds.deleteUI(self.win, window=True)
        cmds.window(self.win, title=self.win, menuBar=True, sizeable=False, widthHeight=(300,380))
        
        cmds.menu(label='Help')
        cmds.menuItem(label='Watch MasterClass Video', c=lambda x:self._contactDetails(opentype='vimeo'))
        cmds.menuItem(label='Contact', c=r9Setup.red9ContactInfo)
        #cmds.menuItem(label='Contact', c=lambda x:self._contactDetails(opentype='email'))
        cmds.menuItem(label='Blog', c=r9Setup.red9_blog)
        cmds.menuItem(label='Red9HomePage', c=r9Setup.red9_website_home)


        cmds.columnLayout(adjustableColumn=True)
        cmds.text(fn="boldLabelFont", label="Advanced Bind Options")
        cmds.separator(h=15, style="none")
        cmds.rowColumnLayout(numberOfColumns=2, cw=((1,150),(2,150)),cs=((1,10)))
        cmds.checkBox(value=self.settings.BindRots, label="BindRots", ann="Bind only the Rotates of the given Controller", al="left", \
                      onc=lambda x:self.settings.__setattr__('BindRots', True), \
                      ofc=lambda x:self.settings.__setattr__('BindRots', False))
        cmds.checkBox(value=self.settings.BindTrans, label="BindTrans", ann="Bind only the Translates of the given Controller", al="left", \
                      onc=lambda x:self.settings.__setattr__('BindTrans', True), \
                      ofc=lambda x:self.settings.__setattr__('BindTrans', False))
        cmds.checkBox(value=1, label="AlignRots CtrSpace", ann="Force the BindLocator to the position of the Controller", al="left", \
                      onc=lambda x:self.settings.__setattr__('AlignToControlRots', True), \
                      ofc=lambda x:self.settings.__setattr__('AlignToSourceRots', True))
        cmds.checkBox(value=1, label="AlignTrans CtrSpace", ann="Force the BindLocator to the position of the Controller", al="left", \
                      onc=lambda x:self.settings.__setattr__('AlignToControlTrans', True), \
                      ofc=lambda x:self.settings.__setattr__('AlignToSourceTrans', True))
        cmds.checkBox(value=self.settings.ResetRotates, label="Reset Rots Offsets", ann="Reset any Offset during bind, snapping the systems together", al="left", \
                      onc=lambda x:self.settings.__setattr__('ResetRotates', True), \
                      ofc=lambda x:self.settings.__setattr__('ResetRotates', False))
        cmds.checkBox(value=self.settings.ResetTranslates, label="Reset Trans Offsets", ann="Reset any Offset during bind, snapping the systems together", al="left", \
                      onc=lambda x:self.settings.__setattr__('ResetTranslates', True), \
                      ofc=lambda x:self.settings.__setattr__('ResetTranslates', False))
   
        cmds.setParent('..')
        cmds.separator(h=10, style="none")
        cmds.button(label="BasicBind", al="center",\
                    ann="Select the Joint on the driving Skeleton then the Controller to be driven", \
                    c=lambda x:BindNodeBase(pm.selected()[0], pm.selected()[1], settings=self.settings).AddBinderNode())
        cmds.button(label="ComplexBind", al="center",\
                    ann="Select the Joint on the driving Skeleton then the Controller to be driven", \
                    c=lambda x:BindNodeTwin(pm.selected()[0], pm.selected()[1], settings=self.settings).AddBinderNode())
        cmds.button(label="AimerBind", al="center",\
                    ann="Select the Joint on the driving Skeleton to AIM at, then the Controller to be driven, finally a node on the driven skeleton to use as UpVector", \
                    c=lambda x:BindNodeAim(pm.selected()[0], pm.selected()[1], pm.selected()[2], settings=self.settings).AddBinderNode())
        cmds.separator(h=15, style="none")
        cmds.rowColumnLayout(numberOfColumns=2,columnWidth=[(1,147),(2,147)])
        
        cmds.button(label="Add BakeMarker", al="center", \
                    ann="Add the BoundCtrl / Bake Marker to the selected nodes", \
                    c=lambda x:addBindMarkers(cmds.ls(sl=True,l=True)))
        cmds.button(label="remove BakeMarker", al="center", \
                    ann="Remove the BoundCtrl / Bake Marker from the selected nodes", \
                    c=lambda x:removeBindMarker(cmds.ls(sl=True,l=True)))
        
        cmds.button(label="Select BindNodes", al="center", \
                    ann="Select Top Group Node of the Source Binder", \
                    c=lambda x:pm.select(GetBindNodes(cmds.ls(sl=True,l=True))))
        cmds.button(label="Select BoundControls", al="center", \
                    ann="Select Top Group Node of the Bound Rig", \
                    c=lambda x:pm.select(GetBoundControls(cmds.ls(sl=True,l=True))))
        cmds.setParent('..')
        cmds.rowColumnLayout(numberOfColumns=2,columnWidth=[(1,200),(2,74)], columnSpacing=[(2,5)])
        cmds.button(label="Bake Binder", al="center", \
                    ann="Select Top Group Node of the Bound Rig", \
                    c=lambda x:BakeBinderData(cmds.ls(sl=True,l=True), self.settings.BakeDebug))
        cmds.checkBox(value=self.settings.BakeDebug, label="Debug View", ann="Keep viewport active to observe the baking process", al="left", \
                      onc=lambda x:self.settings.__setattr__('BakeDebug', True), \
                      ofc=lambda x:self.settings.__setattr__('BakeDebug', False))
        cmds.setParent('..')
        cmds.separator(h=10, style="none")
        cmds.button(label="Link Skeleton Hierarchies - Direct Connect", al="center", \
                    ann="Select Root joints of the source and destination skeletons to be connected - connect via attrs", \
                    c=lambda x:BindSkeletons(cmds.ls(sl=True)[0], cmds.ls(sl=True)[1], method='connect'))
        cmds.button(label="Link Skeleton Hierarchies - Constraints", al="center", \
                    ann="Select Root joints of the source and destination skeletons to be connected - connect via parentConstraints", \
                    c=lambda x:BindSkeletons(cmds.ls(sl=True)[0], cmds.ls(sl=True)[1], method='constrain'))
        cmds.separator(h=10, style="none")
        cmds.button(label="MakeStabilizer", al="center", \
                    ann="Select the nodes you want to extract the motion data from", \
                    c=lambda x:MakeStabilizedNode())

        cmds.separator(h=20, style="none")
        cmds.iconTextButton(style='iconOnly', bgc=(0.7,0,0), image1='Rocket9_buttonStrap2.bmp',
                                 c=lambda *args:(r9Setup.red9ContactInfo()),h=22,w=200)
        cmds.showWindow(self.win)
        cmds.window(self.win,e=True,h=400)
        
    @classmethod
    def Show(cls):
        cls()._UI()
        

def GetBindNodes(rootNode=None):
    '''
    From selected root find all BindNodes via the marker attribute 'BindNode'
    Note we're not casting to PyNodes here for speed here
    '''
    if not rootNode:
        raise StandardError('Please Select a node to search from:')
    return [node for node in cmds.listRelatives(rootNode, ad=True, f=True) \
            if cmds.attributeQuery(BNDNODE_MARKER, exists=True, node=node)]

def GetBoundControls(rootNode=None):
    '''
    From selected root find all BoundControllers via the marker attribute 'BoundCtr'
    Note we're not casting to PyNodes here for speed here
    '''
    if not rootNode:
        raise StandardError('Please Select a node to search from:')
    return [node for node in cmds.listRelatives(rootNode, ad=True, f=True)\
             if cmds.attributeQuery(BAKE_MARKER, exists=True, node=node)]

def BakeBinderData(rootNode=None, debugView=False, ignoreInFilter=[]):
    '''
    From a given Root Node search all children for the 'BoundCtr' attr marker. If none
    were found then search for the BindNode attr and use the message links to walk to
    the matching Controller.
    Those found are then baked out and the marker attribute is deleted
    '''
    BoundCtrls = GetBoundControls(rootNode)
    
    #Found no Ctrls, try and walk the message from the BndNodes
    if not BoundCtrls:
        BndNodes = GetBindNodes()
        for node in BndNodes:
            cons=cmds.listConnections('%s.%s' % (node,BNDNODE_MARKER))
            if cons:
                BoundCtrls.append(cmds.ls(cons[0],l=True)[0])
            else:
                log.info('Nothing connected to %s.%s' % (node,BNDNODE_MARKER))
            
    if BoundCtrls:
        try:
            if not debugView:
                cmds.refresh(su=True)
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
                #Remove the BindMarker from the baked node
                try:
                    cmds.deleteAttr('%s.%s' % (node,BAKE_MARKER))
                except StandardError,error:
                    log.info(error)
            if ignoreInFilter:
                BoundCtrls = [node for node in BoundCtrls if node.split('|')[-1].split(':')[-1] not in ignoreInFilter]
            cmds.filterCurve(BoundCtrls)
            cmds.delete(BoundCtrls, sc=True)  # static channels
        except StandardError,error:
            raise StandardError(error)
        finally:
            cmds.refresh(su=False)
            cmds.refresh(f=True)
    else:
        raise StandardError("Couldn't find any BinderMarkers in given hierarchy")
    return True

    
def MatchGivenHierarchys(source, dest):
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
            
            
def BindSkeletons(source, dest, method='connect'):
    '''
    From 2 given root joints search through each hierarchy for child joints, match
    them based on node name, then connect their trans/rots directly, or
    parentConstrain them. Again cmds for speed
    '''
    sourceJoints = cmds.listRelatives(source, ad=True, f=True, type='joint')
    destJoints = cmds.listRelatives(dest, ad=True, f=True, type='joint')
 
    if cmds.nodeType(source) == 'joint':
        sourceJoints.append(source)
    if cmds.nodeType(dest) == 'joint':
        destJoints.append(dest)
        
    attrs = ['rotateX', 'rotateY', 'rotateZ', 'translateX', 'translateY', 'translateZ']
     
    for sJnt, dJnt in MatchGivenHierarchys(sourceJoints, destJoints):
        if method == 'connect':
            for attr in attrs:
                try:
                    cmds.connectAttr('%s.%s' % (sJnt, attr), '%s.%s' % (dJnt, attr), f=True)
                except:
                    pass
        elif method == 'constrain':
            try:
                cmds.parentConstraint(sJnt, dJnt, mo=True)
            except:
                pass
    

def MakeStabilizedNode(nodeName=None, centered=True):
    '''
    Very simple proc to generate a Stabilized node for
    raw MoCap tracking purposes... First selected node
    is used as the Aim axis, second selected is used as this
    aim's worldUp
    '''
    RequiredMarkers = pm.ls(sl=True, l=True)
    #pos = pm.xform(WorldUpObj, q=True, ws=True, t=True)
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
        
    #Snap a curveKnot to the pivot of all referenceMarkers
    for node in RequiredMarkers:
        pm.curve(curve, a=True, ws=True, p=(pm.xform(node, q=True, ws=True, t=True)))
    pm.curve(curve, a=True, ws=True, p=(pm.xform(AimAt, q=True, ws=True, t=True)))
    
    return curve


def addBindMarkers(ctrls=None, *args):
    '''
    add the bind markers to nodes, these dictate what gets baked
    '''
    if not ctrls:
        ctrls=cmds.ls(sl=True,l=True)
    for ctr in ctrls:
        print pm.PyNode(ctr)
        BindNodeBase.AddBindMarkers(pm.PyNode(ctr))
        
def removeBindMarker(ctrls=None, *args):
    '''
    remove the bind markers from nodes, these dictate what gets baked
    '''
    if not ctrls:
        ctrls=cmds.ls(sl=True,l=True)
    for ctr in ctrls:
        cmds.deleteAttr('%s.%s' % (ctr, BAKE_MARKER))
    
        