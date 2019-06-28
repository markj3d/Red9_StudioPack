Pro_Pack : MetaData
======================

ProPack metadata module contains all the specifically built nodes for the 
extended pipelines running under ProPack. These include our Red9Puppet and
the exporter and audio management systems. This is the very core of all the Red9 
pipeline when running the Red9 Puppet rig.

	>>> # import statement for the module via the r9pro decompiler
	>>> from Red9.pro_pack import r9pro 
	>>> r9pro.r9import('r9pmeta')
	>>> import r9pmeta
	
.. automodule:: Red9.pro_pack.core.metadata_pro
   
   .. rubric:: Main Classes

   .. autosummary::
   	  
      Pro_MetaRig_Base
      Pro_MetaRig
      Pro_MetaRig_SRC
      Pro_MetaRig_Prop
	  Pro_MetaRig_External
      Pro_MetaRig_FacialUI
      ExportTag_Base
      ExportTag_Character
      ExportTag_Facial
      ExportTag_Prop
      ExportTag_Environment
      ExportLoopNode
	  ImagePlane
      SceneMover
      AudioGroup
	  MetaTimeCodeHUD
      

    


   
   
   