Red9_Audio
==========

Red9 Audio is the module for all audio handling within the Red9 pack.
 
This includes the wrapper to the new audio compile tools for mixing multiple wavs 
inside Maya to a single merged track, allowing you to finally playblast multiple 
separate audio nodes! Why the hell Autodesk haven't done this I have no idea
as it's a major issue when you're dealing with facial sequences. There's is 
a 'compile' flag in the playblast command but it's never worked.


.. automodule:: Red9.core.Red9_Audio

   .. rubric:: Core Functions

   .. autosummary::
   
      milliseconds_to_Timecode
      milliseconds_to_frame
      timecode_to_milliseconds
      timecode_to_frame
      frame_to_timecode
      frame_to_milliseconds
      combineAudio
      inspect_wav
      audioPathLoaded
      
   .. rubric:: Main Classes

   .. autosummary::
   	  
      AudioHandler
      AudioNode

    


   
   
   