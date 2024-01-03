Pro_Pack : puppet : ikfk_match
================================

ProPack core IK>FK matching codebase used to configure, connect and match limb
between IK and FK modes. These work at a sub-system level so all controllers need
to be wired to a consistent system node. For example, mrig.L_ArmSystem for 
matching the left arm. If you try and add wires to a rig thats a flat structure
the matching will be a one shot full rig based process so not ideal.

	>>> # import statement for the module via the r9pro decompiler
	>>> from Red9.pro_pack import r9pro 
	>>> r9puppet_ikfk_utils = r9pro.r9import('r9puppet_ikfk_utils')
	
.. automodule:: Red9.pro_pack.puppet.ikfk_match
   
   .. rubric:: Main Classes

   .. autosummary::
   	  



    


   
   
   