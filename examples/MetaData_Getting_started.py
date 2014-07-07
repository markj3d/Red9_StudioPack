
#===============================================================
# Basic MetaClass Use:
#===============================================================

import Red9.core.Red9_Meta as r9Meta
import maya.cmds as cmds

#make a new blank mClass MayaNode
node=r9Meta.MetaClass()
node.select()

'''
If a Maya node is passed in and it has the mClass attribute of a class
thats known then the following call with return the correct class object.

NOTE: there's a global RED9_META_REGISTERY which holds registered mClasses
found at start using itersubclasses, called in the r9Meta.registerMClassInheritanceMapping()
'''
new=r9Meta.MetaClass(cmds.ls(sl=True)[0])
type(new)
#// <class 'Red9_Meta.MetaClass'> 

'''
Attribute Handling
===============================================================
Attribute management for the node. If no type flag is passed in
then the code automatically figures what attrType to add from the
given value. Note that the attribute is serialized to the Maya
Node AND the class object. All attributes are managed
'''
#standard attribute handling
node.addAttr('stringTest', "this_is_a_string")  #create a string attribute
node.addAttr('fltTest', 1.333)        #create a float attribute
node.addAttr('fltTest2', 2.0, hidden=False, min=0, max=10) #create a float attribute with additional flags
node.addAttr('intTest', 3)            #create a int attribute
node.addAttr('boolTest', False)       #create a bool attribute

node.intTest    #>>3       
node.intTest=10 #set back to the MayaNode
node.intTest    #>>10

node.fltTest    #>>1.333
node.fltTest=3.55
node.fltTest    #>>3.55

node.stringTest #>>'this_is_a_string'
node.stringTest="change the text"
node.stringTest #>>change the text

node.boolTest   #>>False
node.boolTest=True #set back to the MayaNode
node.boolTest   #>>True


#enum handling, settable via the string or the index
#note that we need to specifically pass the type in here
node.addAttr('enum', enumName='A:B:D:E:F', attrType='enum')
node.enum='A'
node.enum   #>>0 always returns the actual index
node.enum=2
node.enum   #>>2


#JSON handling
#make a new test dict for this demo
testDict={'jsonFloat':1.05,'Int':3,'jsonString':'string says hello','jsonBool':True}
node.addAttr('jsonTest', testDict)  #create a string attr with JSON serialized data
node.jsonTest['jsonString']     #will deserialize the MayaNode jsonTest attr back to a dict and return its key['stringTest']

#double handling
#adds a double3 attr with subAttrs 'doubleTestX,doubleTestY,doubleTesZ', sets them as doubles with min/max vaules, 
#sets their values to 1,2,10, then exposes them to the channelBox!
node.addAttr('doubleTest', attrType='double3', value=(1.0,2.0,10.0), min=1, max=15, hidden=False)


#message attribute handling:
#----------------------------

cmds.ls(cmds.polyCube()[0],l=True)[0]
cmds.ls(cmds.polyCube()[0],l=True)[0]
cmds.ls(cmds.polyCube()[0],l=True)[0]
cmds.ls(cmds.polyCube()[0],l=True)[0]

#create a non multi-message attr and wire pCube1 to it     
node.addAttr('msgSingleTest', value='pCube1', attrType='messageSimple')
node.msgSingleTest  #>> ['pCube1']   
node.msgSingleTest='pCube2'
node.msgSingleTest  #>> ['pCube2'] # NOTE pCube1 had now been disconnected and the msg connected to Cube2

#create a multi-message attr and wire pCube1 to it, indexMatters=False
node.addAttr('msgMultiTest', value=['pCube1','pCube2','pCube3'], attrType='message')  
node.msgMultiTest   #>> ['pCube1','pCube2','pCube3'] 
node.msgMultiTest='pCube1'
node.msgMultiTest   #>> ['pCube1'] #pCube2 and pCube3 have now been disconnected
node.msgMultiTest=['pCube2','pCube3']
node.msgMultiTest   #>>['pCube2','pCube3']

#connect the cube up using the main connectChild call
node.connectChild('pCube4','myChild')
node.myChild 

#deleting an attribute is the same as standard Python
delattr(node,'attr_to_delete')

'''
Blind Usage for any Maya Node
===============================================================
Lets do the same thing on a standard Maya node without the MetaClass. Here we're
going to simply use the MetaClass wrapping to manage a standard lambert Node.
NOTE: the scriptEditor autoComplete will automatically pickup ALL attributes
on the node once cast to the MetaClass. Very useful for managing large nodes.
'''
mLambert=r9Meta.MetaClass('lambert1')
#mLambert is just a Python MetaNode and doesn't exist as a MayaNode
mLambert.diffuse     #>>0.5
mLambert.color       #>>(0.5, 0.5, 0.5)
mLambert.color=(1,0.2,0.2) #sets the compound float3 attr

mLambert.diffuse=0.7 #sets the diffuse directly
mLambert.diffuse     #>>0.7


'''
General
===============================================================
Generic call to find all mClass nodes in the scene. This also takes
a type argument so you can return only nodes of a given class type
NOTE: 'type' the given class type must exist as a key in the RED9_META_REGISTRY 
'''
mClass = r9Meta.getMetaNodes()
mClass = r9Meta.getMetaNodes(dataType='mClass',mTypes='MetaRig')
#Return only MetaRig class objects. If the dataType isn't 'mClass' then we
#return the standard MayaNodes, else we return the mClass initialized to the class object

#Connect the selected Maya Nodes to the mClass node under a Multi-Message attr 'mirrorLeft'
node.connectChildren(cmds.ls(sl=True),'mirrorLeft')
node.mirrorLeft    #will now return all connected nodes to the message attr

#Connect the selected Maya Node to the mClass node under a NON Multi-Message attr 'simpleChild'
#this is what most of the MRig calls use as a single connection describes a single MayaNode
node.connectChild(cmds.ls(sl=True)[0],'simpleChild')
node.simpleChild    #will now return all connected nodes to the message attr

r9Meta.getConnectedMetaNodes(nodes, source=True, destination=True, dataType='mClass')



'''
MetaRigging!
===============================================================
NOTE: For more detailed examples of the MetaRig see the MetaRig_Morpheus.py 
example in this folder.
This class is a wrapper of the main class aimed at managing complex
rigs and finding controllers. Simple concept, you make a blank mRig
node and just hook the controllers up to it.
'''
mRig=r9Meta.MetaRig()
mRig.addGenericCtrls(cmds.ls(sl=True))  #add all given nodes to the 'RigCtrl' msgLink
mRig.getRigCtrls()                      #return all RigCtrls from above

#note that the default mClass connect will allow you to still add
#a list of nodes to a specific msg attr.
mRig.connectChildren(cmds.ls(sl=True),'mirrorLeft')

#From a given Maya node return all connected mNodes as mClass objects
#note that this call can clamp to source or destination and has the same 
#dataType flag as the getMetaNodes call
mNode=r9Meta.getConnectedMetaNodes(cmds.ls(sl=True))[0]

'''
The above is the most basic use. Wiring all given nodes to a single attr
the issue here is how do you find a specific controller from the list? 
So we have a singular Add function which binds the given node to a single
message attr, suffixed with 'CTRL_' 
'''

mRig.addRigCtrl('MyMaya_Ctrl_Hips', 'Hips')
mRig.CTRL_Hips  #>>MyMaya_Ctrl_Hips

'''
Note that because of the autofill on the object, once you have a mClass Rig
object you'll get a list of all the hooked Controllers (added by this method)
on completion in the scriptEditor. Whats more mRig.getRigCtrls() will still
give you a full list of them back.
'''

