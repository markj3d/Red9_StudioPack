Red9_General
============

Red9 General is a module for general functions called and used throughout the codebase.
This includes most of the context managers and decorators.

.. note::
	Nothing inside this module should require any other part of Red9


.. automodule:: Red9.core.Red9_General

   .. rubric:: Key functions
   
   .. autosummary::
   
		getCurrentFPS
		getModifier
		forceToString
		itersubclasses
		inspectFunctionSource
		getScriptEditorSelection
		
		thumbNailScreen
		thumbnailFromPlayBlast
		thumbnailApiFromView
		
		os_OpenFileDirectory
		os_OpenFile
		formatPath
		formatPath_join
		sceneName
		
		writeJson
		readJson
    
   .. rubric:: Context Managers / decorators

   .. autosummary::
   	  
      AnimationContext
      undoContext
      ProgressBarContext
      HIKContext
      SceneRestoreContext
      Timer
      runProfile
    


   
   
   