Red9_PoseSaver
==============

Red9_PoseSaver is designed as a generic module for storing and dealing
with poses inside Maya. The PoseData object is the base for all of this
and is what's wrapped by the AnimUI and the MetaData.poseCacheLoad() calls.

There's also a powerful setup for testing a rigs current pose against a 
previously stored pose file, or you can test poseObjectA==poseObjectB
or even poseFileA==poseFileB


.. automodule:: Red9.core.Red9_PoseSaver
   
   .. rubric:: Core Pose Classes

   .. autosummary::
   
      DataMap
      PoseData
      PosePointCloud
      PoseBlender
      PoseCompare

   
   

   
   
   