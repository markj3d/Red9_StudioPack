'''
------------------------------------------
Red9 Consultancy : Maya Pipeline Solutions
email: rednineinfo@gmail.com
------------------------------------------


##################################################################
#                        MORPHEUS TEST                           #
##################################################################

This is a demo file to show you in code how to add MetaRig data to
a standard downloadable rig. There are 3 methods below to give you 
an idea of how the API calls work. This will tag up most of the
main controllers on Morpheus, not everything as it's only a demo

Once done you can switch to using the MetaRig checkbox in the
AnimationUI's Hierarchy Tab. The code below also adds the Mirror 
data so that pose and anim data will mirror correctly for Morpheus.

NOTE: Also see the Red9_MetaTest module for the unittests for MetaRig 
as there's a full rig and sub-system test that bolt onto a very 
basic test rig that I now ship with the pack.
\Red9\tests\Red9_MetaTest.py >> Test_MetaRig

There's also now the resulting markered rig in the tests\testFiles folder!
'''

#base imports
import Red9.core.Red9_Meta as r9Meta
import maya.cmds as cmds
#reload(r9Meta)



'''
####################################################################
#  METHOD 1:  ADDING CONTROLS : using the mRig Presets
####################################################################

Easy method, these basic types are defined for speed, but really the
method below is the one for more experienced people as it's completely
expandable and flexible. Saying that if you want these presets expanding
just let me know. They certainly stop you having to mess with the mirrorData!
'''

#make the base MRig
mRig=r9Meta.MetaRig(name='MORPHEUS')

#Left / Right Pairs
mRig.addFootCtrl('morpheusRig_v01_00:m_leg_IKleg_Cntrl_l_anim','Left')
mRig.addFootCtrl('morpheusRig_v01_00:m_leg_IKleg_Cntrl_r_anim','Right')
mRig.addKneeCtrl('morpheusRig_v01_00:m_leg_PV_Cntrl_l_anim','Left')
mRig.addKneeCtrl('morpheusRig_v01_00:m_leg_PV_Cntrl_r_anim','Right')
#note here we're supplying axis that determine which axis are managed in the mirror code
#without these the default axis set is used and inverted during mirror
mRig.addWristCtrl('morpheusRig_v01_00:m_arm_IK_Cntrl_l_anim','Left', axis='translateX,translateY,translateZ')
mRig.addWristCtrl('morpheusRig_v01_00:m_arm_IK_Cntrl_r_anim','Right',axis='translateX,translateY,translateZ')
mRig.addElbowCtrl('morpheusRig_v01_00:m_arm_PV_Cntrl_l_anim','Left')
mRig.addElbowCtrl('morpheusRig_v01_00:m_arm_PV_Cntrl_r_anim','Right')
mRig.addClavCtrl('morpheusRig_v01_00:rig_clavicle_l_skin_IK_anim','Left')
mRig.addClavCtrl('morpheusRig_v01_00:rig_clavicle_r_skin_IK_anim','Right')

#Centre Controllers
mRig.addMainCtrl('morpheusRig_v01_00:all_anim')
mRig.addRootCtrl('morpheusRig_v01_00:m_spine_Root_anim')
mRig.addHipCtrl('morpheusRig_v01_00:rig_spine_0_skin_Hips_anim')
mRig.addChestCtrl('morpheusRig_v01_00:rig_spine_0_skin_Shoulders_anim')
mRig.addNeckCtrl('morpheusRig_v01_00:m_neck_IK_anim')
mRig.addHeadCtrl('morpheusRig_v01_00:head_mover_ctrl')


#In this instance all the Ctrls are bound directly to the mRig itself
mRig.L_Wrist #>>morpheusRig_v01_00:m_arm_IK_Cntrl_l_anim




'''
####################################################################
#  METHOD 2:  ADDING CONTROLS : using the mRig.addRigCtrl() call 
####################################################################

This is the preferred method as it gives you all the freedom you need.
Difference is you have to specify the mirrorData dict { side, slot, axis}
The actual slot index makes no difference, as long as left and right controllers 
have the same ID to denote they are a pair. 
You also have to give the MetaRig attr that'll be used to ID the controller on 
the mRig object, this will be prefixed with CTRL_xxx
'''

#make the base MRig
mRig=r9Meta.MetaRig(name='MORPHEUS')

#Left Right Pairs
mRig.addRigCtrl('morpheusRig_v01_00:m_leg_IKleg_Cntrl_l_anim','L_Foot', mirrorData={'side':'Left', 'slot':4})
mRig.addRigCtrl('morpheusRig_v01_00:m_leg_IKleg_Cntrl_r_anim','R_Foot', mirrorData={'side':'Right','slot':4})
mRig.addRigCtrl('morpheusRig_v01_00:m_leg_PV_Cntrl_l_anim','L_Knee',    mirrorData={'side':'Left', 'slot':5})
mRig.addRigCtrl('morpheusRig_v01_00:m_leg_PV_Cntrl_r_anim','R_Knee',    mirrorData={'side':'Right','slot':5})
#note here we're supplying axis that determine which axis are managed in the mirror code
#without these the default axis set is used and inverted during mirror
mRig.addRigCtrl('morpheusRig_v01_00:m_arm_IK_Cntrl_l_anim','L_Wrist',  mirrorData={'side':'Left', 'slot':1,'axis':'translateX,translateY,translateZ'})
mRig.addRigCtrl('morpheusRig_v01_00:m_arm_IK_Cntrl_r_anim','R_Wrist',  mirrorData={'side':'Right','slot':1,'axis':'translateX,translateY,translateZ'})
mRig.addRigCtrl('morpheusRig_v01_00:m_arm_PV_Cntrl_l_anim','L_Elbow',  mirrorData={'side':'Left', 'slot':2})
mRig.addRigCtrl('morpheusRig_v01_00:m_arm_PV_Cntrl_r_anim','R_Elbow',  mirrorData={'side':'Right','slot':2})
mRig.addRigCtrl('morpheusRig_v01_00:rig_clavicle_l_skin_IK_anim','L_Clav', mirrorData={'side':'Left', 'slot':3})
mRig.addRigCtrl('morpheusRig_v01_00:rig_clavicle_r_skin_IK_anim','R_Clav', mirrorData={'side':'Right','slot':3})

#Centre Controllers
mRig.addRigCtrl('morpheusRig_v01_00:all_anim','Main', mirrorData={'side':'Centre', 'slot':1})
mRig.addRigCtrl('morpheusRig_v01_00:m_spine_Root_anim','Root', mirrorData={'side':'Centre', 'slot':2})
mRig.addRigCtrl('morpheusRig_v01_00:rig_spine_0_skin_Hips_anim','Hips',  mirrorData={'side':'Centre', 'slot':3})  
mRig.addRigCtrl('morpheusRig_v01_00:rig_spine_0_skin_Shoulders_anim','Chest', mirrorData={'side':'Centre', 'slot':4})
mRig.addRigCtrl('morpheusRig_v01_00:m_neck_IK_anim','Neck',  mirrorData={'side':'Centre', 'slot':5})
mRig.addRigCtrl('morpheusRig_v01_00:head_mover_ctrl','Head', mirrorData={'side':'Centre', 'slot':6})
mRig.select()


#In this instance all the Ctrls are bound directly to the mRig itself
mRig.L_Wrist #>>morpheusRig_v01_00:m_arm_IK_Cntrl_l_anim




'''
####################################################################
#  METHOD 3:  ADDING CONTROLS : Using Subsystem MetaNodes!
####################################################################

The above 2 methods use the same connection setups BUT crucially only connect 
the nodes to the mRig MetaNode itself. In production it's actually better to have 
subMeta Node systems that hold all controllers and / or data describing a 
particular rig sub system, ie, the system=Arm, side=Left

This example is more production ready and wires the subSystems for you as an example
of what a production network may look like under the hood.
'''

#make the base MRig
mRig=r9Meta.MetaRig(name='MORPHEUS')

#Link the MainCtrl , this is used as Root for some of the functions
mRig.addRigCtrl('morpheusRig_v01_00:all_anim','Main', mirrorData={'side':'Centre', 'slot':1})

#Left Arm SubMeta Systems --------------------------
lArm= mRig.addMetaSubSystem('Arm', 'Left', nodeName='L_ArmSystem', attr='L_ArmSystem')
lArm.addRigCtrl('morpheusRig_v01_00:m_arm_IK_Cntrl_l_anim','L_Wrist', mirrorData={'side':'Left','slot':1,'axis':'translateX,translateY,translateZ'})
lArm.addRigCtrl('morpheusRig_v01_00:m_arm_PV_Cntrl_l_anim','L_Elbow', mirrorData={'side':'Left','slot':2})
lArm.addRigCtrl('morpheusRig_v01_00:rig_clavicle_l_skin_IK_anim','L_Clav', mirrorData={'side':'Left','slot':3})
#Left Leg SubMeta Systems --------------------------
lLeg= mRig.addMetaSubSystem('Leg', 'Left', nodeName='L_LegSystem', attr='L_LegSystem')
lLeg.addRigCtrl('morpheusRig_v01_00:m_leg_IKleg_Cntrl_l_anim','L_Foot', mirrorData={'side':'Left','slot':4})
lLeg.addRigCtrl('morpheusRig_v01_00:m_leg_PV_Cntrl_l_anim', 'L_Knee',   mirrorData={'side':'Left','slot':5})

#Right Arm SubMeta Systems --------------------------
rArm= mRig.addMetaSubSystem('Arm', 'Right', nodeName='R_ArmSystem', attr='R_ArmSystem')
rArm.addRigCtrl('morpheusRig_v01_00:m_arm_IK_Cntrl_r_anim','R_Wrist', mirrorData={'side':'Right','slot':1,'axis':'translateX,translateY,translateZ'})
rArm.addRigCtrl('morpheusRig_v01_00:m_arm_PV_Cntrl_r_anim','R_Elbow', mirrorData={'side':'Right','slot':2})
rArm.addRigCtrl('morpheusRig_v01_00:rig_clavicle_r_skin_IK_anim','R_Clav', mirrorData={'side':'Right', 'slot':3})
#Right Leg SubMeta System --------------------------
rLeg= mRig.addMetaSubSystem('Leg', 'Right', nodeName='R_LegSystem', attr='R_LegSystem')
rLeg.addRigCtrl('morpheusRig_v01_00:m_leg_IKleg_Cntrl_r_anim','R_Foot', mirrorData={'side':'Right','slot':4})
rLeg.addRigCtrl('morpheusRig_v01_00:m_leg_PV_Cntrl_r_anim', 'R_Knee',   mirrorData={'side':'Right','slot':5})

#Spine SubMeta System -------------------------------
spine= mRig.addMetaSubSystem('Spine', 'Centre', nodeName='SpineSystem', attr='SpineSystem')
spine.addRigCtrl('morpheusRig_v01_00:m_spine_Root_anim','Root',  mirrorData={'side':'Centre','slot':2})
spine.addRigCtrl('morpheusRig_v01_00:rig_spine_0_skin_Hips_anim','Hips', mirrorData={'side':'Centre','slot':3})  
spine.addRigCtrl('morpheusRig_v01_00:rig_spine_0_skin_Shoulders_anim','Chest', mirrorData={'side':'Centre','slot':4})
spine.addRigCtrl('morpheusRig_v01_00:m_neck_IK_anim','Neck', mirrorData={'side':'Centre','slot':5})
spine.addRigCtrl('morpheusRig_v01_00:head_mover_ctrl','Head',  mirrorData={'side':'Centre','slot':6})


#In this instance the Ctls are bound to their respective subSystems
#yet getting data back is as simple as just .dot walk :)
mRig.L_LegSystem.CTRL_L_Foot #>> morpheusRig_v01_00:m_leg_IKleg_Cntrl_l_anim




'''
##############################################################################
#   EXTRAS - lets have some fun and add some Facial
##############################################################################
'''
#hook a support subMetaNode to wire facial too, note the msg attr will be "Facial"
facial=mRig.addChildMetaNode('MetaFacialRig',attr='Facial',nodeName='FACIAL') #NEW generic method in BaseClass

#note: If you supply mirrorData to this arg then the facial will also mirror as required ;)
facial.addRigCtrl('morpheusRig_v01_00:jaw_anim','Jaw')
facial.addRigCtrl('morpheusRig_v01_00:mouthEmote_left_anim','L_Smile',
            mirrorData={'side':'Left', 'slot':10})
facial.addRigCtrl('morpheusRig_v01_00:mouthEmote_right_anim','R_Smile',
            mirrorData={'side':'Right', 'slot':10})

'''
Now if we have the mRig object we can just walk the Meta structure! 
Note that any controller added has it's attr prefixed by "CTRL_". 
There is scope in the code to add and modify this "type" in the subMetaNode and 
there's an example in the Red9_Meta.py of the MetaRigFacialSupport who's 
controllers are prefixed with "FACE" to help ID and manage the type more easily
'''
#Find the Jaw controller from the mRig
mRig.Facial.FACE_Jaw

#Get all controllers wired to the MetaRigNode
#NOTE this currently has no walk function so will only return direct wired controllers
#so in this example from the mRig it will not return the Facial Controllers
mRig.getRigCtrls()

#or facial controllers
mRig.Facial.getRigCtrls()

#finally to get the mRig node back from any of the Controllers
#Note that this command has source,destination args to clamp 
#the direction of the search
r9Meta.getConnectedMetaNodes(cmds.ls(sl=True))[0]



'''
##############################################################################
#   CONCLUSION : why is this good???
##############################################################################

So you now have a basically setup MetaRig. If you open the AnimationUI
and go to the Hierarchy Tab switch the MetaRig checkbox on, this will switch all
the back-end code to filter for the MetaNode systems. The hierarchy filters for
most of the setups still require you to select a node to act on, in case you have 
multiple characters in the scene, but as long as its a member of the mRig then 
hierarchy functions will all work on the mRig as root.

HINT: For this example if you use any of the functions with a hierarchy checkbox on,
and select a main controller, say the L_Foot, then the code will act only on those 
Controllers wired directly to the main mRig node.
If you select one of the nodes wired to the Facial mRig (a sub MetaNode, then it'll 
act on those instead. Means that you can copy,pose,mirror Facial by just changing 
your initial selection.

Any bugs mail me!

have fun playing

Red

'''

