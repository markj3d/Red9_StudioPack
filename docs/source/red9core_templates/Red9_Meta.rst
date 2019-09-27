Red9_Meta
=========

Red9 Meta is a full metaData API that deals with Maya nodes in a more seamless manor. I've
tried to do as much documentation as I can both in terms of commenting the code and doing
examples and Vimeo demos. 

This is a big concept and I'll be expanding these docs accordingly when I get more time.

Vimeo Demos:
------------

* Develop Conference 2014 - MetaData in a Production Pipeline Video1 <https://vimeo.com/100882408>
* Develop Conference 2014 - MetaData in a Production Pipeline Video2 <https://vimeo.com/100883383>
* Develop Conference 2014 - MetaData in a Production Pipeline Video3 <https://vimeo.com/102463373>

* MetaData part1 <https://vimeo.com/61841345> 
* MetaData part2 <https://vimeo.com/62546103> 
* MetaData Part3 <https://vimeo.com/64258996> 
* MetaData part4 <https://vimeo.com/72006183> 
* MetaData MetaHUD <https://vimeo.com/65006622>
 
There are also some basic examples in the Red9 Package itself found under the examples folder.


.. automodule:: Red9.core.Red9_Meta

   .. rubric:: Key Functions

   .. autosummary::
   	  
   	  registerMClassInheritanceMapping
   	  registerMClassNodeMapping
   	  isMetaNode
   	  isMetaNodeInherited
      getMetaNodes
      getMetaRigs
      getMetaRigs_fromSelected
      getConnectedMetaNodes
      getConnectedMetaSystemRoot

   
   .. rubric:: Main Classes

   .. autosummary::
   	  
      MetaClass
      MetaRig
      MetaRigSubSystem
      MetaRigSupport
      MetaFacialRig
      MetaFacialRigSupport
      MetaHIKCharacterNode
      MetaHIKControlSetNode
      MetaHIKPropertiesNode
      MetaHUDNode
      MetaTimeCodeHUD
    


   
   
   