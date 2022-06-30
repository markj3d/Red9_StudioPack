Pro_Pack : anim_map
=====================

ProPack anim_map module if the core of the r9Anim animation format. Recently
moved to become a separate module in it's own right rather than just part of the 
base animation module.

	>>> # import statement for the module via the r9pro decompiler
	>>> from Red9.pro_pack import r9pro 
	>>> r9panim = r9pro.r9import('r9panim_map')
	
In the latest drop (May 2022) we've finally added in a frame sampler to extend
the functionality, and to speed up saving animations which are part of an animLayer in Maya.
Previously we used Maya's internal animLayer merge code but that was just too slow so we've 
written the new frame sampler to speed saving scenes with lots of layer. This has also opened up a new set 
of features in that the code now deals with attributes that are constrained, driven, connected
or part of a layer. If an attr is found to be driven then we sample the animation on save. If an 
attr isn't flagged as driven we take the original code path and just grab the animCurve data direct 
from the plugged animCurve node.

Because of this new support we've also added a wrapper in r9Anim module to merge animLayers
via the new mechanism. In a client file test Maya was taking 45 seconds to merge and delete
all the animLayer data, ours took 8 seconds. 

.. automodule:: Red9.pro_pack.core.anim_map
   
   .. rubric:: Main Classes

   .. autosummary::
   	  
      AnimationStore
      AnimMap


    


   
   
   