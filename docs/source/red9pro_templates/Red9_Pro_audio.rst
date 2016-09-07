Pro_Pack : Audio
======================

ProPack audio module manages BWav formats, Timecode and the more advanced aspects of dealing with Audio within Maya.
All the BWav handling in the StudioPack ultimately calls this codebase but most of the actual handling in ProPack still uses the AudioNode and AudioHandler
from the StudioPack API.

	>>> # import statement for the module via the r9pro decompiler
	>>> from Red9.pro_pack import r9pro 
	>>> r9pro.r9import('r9paudio')
	>>> import r9paudio
	
.. automodule:: Red9.pro_pack.core.audio

   .. rubric:: Core Functions

   .. autosummary::
   
      milliseconds_to_Timecode
      milliseconds_to_frame
      timecode_to_milliseconds
      timecode_to_frame
      frame_to_timecode
      frame_to_milliseconds
      validate_timecodeString
       
   .. rubric:: Main Classes

   .. autosummary::
   	  
      Timecode
      BWav_Handler
      AudioGRP_Manager



    


   
   
   