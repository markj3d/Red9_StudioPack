Red9_CoreUtils
==============

Red9_CoreUtils is the backbone of much of the systems, used to filter, find and process nodes
on mass withing Maya as well as containing a lot of core functions for dealing with data.

The FilterNode and FilterSettings classes are used throughout the pack, in fact any
time the tools process a hierarchy it's these classes that deal with it.


.. automodule:: Red9.core.Red9_CoreUtils

   .. rubric:: Core Functions

   .. autosummary::
   
      nodeNameStrip
      prioritizeNodeList
      sortNumerically
      stringReplace
      matchNodeLists
      getBlendTargetsFromMesh
      processMatchedNodes
      matchNodeLists
      timeOffset_addPadding
      timeOffset_collapse
      
      decodeString
      floatIsEqual
      valueToMappedRange
      distanceBetween

    
   .. rubric:: Core Classes

   .. autosummary::
   
      FilterNode_Settings
      FilterNode
      MatchedNodeInputs
      LockChannels
      TimeOffset
      MatrixOffset
   
   

   
   
   