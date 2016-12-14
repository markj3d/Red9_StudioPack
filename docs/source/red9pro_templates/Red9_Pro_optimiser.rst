Pro_Pack : Optimiser
=======================

ProPack optimiser module manages the health of assets and your
Maya scene via a complex Health object system. The HealthValidation class runs
tests that are bound to it, formatted such that each test returns a HealthTestObject.
These objects contain both the results of the test, what failed, what passed and 
where ever possible they also have a fix method bound to them.

This is a crucial part of the ProPack systems for clients, dealing not just with
overall optimisation methods and cleanups, but also a complex health runner setup.

The key to all of the testing systems are HealthTestObjects formatted in a specific manner
and passed into the HealthValidation class to run and collate.

Each test makes and returns an instance of a HealthTestObject and is self contained, they can be
run standalone without the HealthValidation class to test specific things, or grouped into a bigger
set of tests, for example to health check a rig prior to releasing to an animator.

	>>> # import statement for the module via the r9pro decompiler
	>>> from Red9.pro_pack import r9pro 
	>>> r9pro.r9import('r9popt')
	>>> import r9popt


	>>> def simple_example_test(expected=False):
	...     '''
	...     This is an example of how to write correctly formatted Health tests 
	...     for the Validation systems based on simply matching a predictable input result.
	...     This is how all the Maya environment tests are built in the ProPack
	...     
	...     In simple tests like this we can just compare the results with the expected data
	...     such that HealthObject.results_returned==HealthObject.results_expected
	...    
	...     :param expected: status of the test expected
	...     '''
	...     # we make a fresh instance of a HealthTestObject, this is crucial
	...     HealthObject = r9popt.HealthTestObject(name='simple_example_test')
	...     
	...     # set the internal results_expected to that arg passed in
	...     HealthObject.results_expected = expected
	...     
	...     # bind a fix method if you have one written
	...     # HealthObject.fix_method=maya_timeUnits_fix
	...     
	...     # run the actual test and push it's result to the HealthObject
	...     HealthObject.results_returned = cmds.about(q=True, batch=True)
	...     
	...     # do the simple compare by calling the set_byCompare func
	...     # this sets the status internally and sets the test as having been run
	...    HealthObject.set_byCompare()
	...    
	...    # we ALWAYS have to return the HealthObject
	...    return HealthObject
    
    
	>>> def custom_example_test(expected):
	...	    '''
	...	    more complex test, most of the time we don't know what exactly
	...	    is in the scene before we run the test so the above example is useless.
	...	    In this example we're constructing the test and managing the results
	...	    directly
	...	    
	...	    :param expected: a list of nodes we expect to be present
	...	    '''
	...	    # as above, take an instance of the HealthObject and set the initial vars
	...	    HealthObject=r9popt.HealthTestObject(name='custom_example')
	...	    HealthObject.results_expected=expected
	...	
	...	    for node in expected:
	...	        # run our test
	...	        if not cmds.objExists(node):
	...	            # test failed so we add the failed nodes to the results_failed list
	...	            HealthObject.results_failed_nodes.append(node)
	...	            # we can also set the log info, displayed when we get the overall status
	...	            HealthObject.log_message+='failed node :  "%s" : Missing in Scene' % node
	...	        else:
	...	            # test passed so add the passed nodes to the results
	...	            HealthObject.results_passed_nodes.append(node)
	...	    # if we have failed nodes then the test failed and we need to set it's status as such
	...	    # by default the HealthObject is set as failed
	...	    if not HealthObject.results_failed_nodes:
	...	        HealthObject.set_passed()
	...	    # return the HealthObject
	...	    return HealthObject


	When we put this together with the HealValidation system we get a very powerful way of checking data inside Maya.
	In Pro for clients this is also bound to the fileOpen callback, allowing us to test the scene after load against a given project template.
	
	>>> class Client_SceneOpen_HealthValidation(r9popt.HealthValidation):
 	>>>     def __init__(self, *args, **kwargs):
	...         # Tests to run, note this is a list of tuples where the second
	...         # arg is the expected result if specified
	...         self.tests=[(r9popt.maya_sceneUnits_test, {'expected':'centimeter'}), # Maya environment units
	...                     (r9popt.maya_timeUnits_test, {'expected':'ntsc'}),  # Maya environment fps 'ntsc' 30fps
	...                     (r9popt.maya_upAxis_test, {'expected':'y'})]  # Maya environment world axis Y-up
	>>> 
	>>> test=Client_SceneOpen_HealthValidation()
	>>> test.run_health()
	>>> 
	>>> test.getStatus()  # pass or fail?
	>>> print test.prettyPrintStatus()  # note this is formatted as a string for output to file
	>>> test.writeStatus(filepath)  # output the test results to file 
	>>> 
	>>> # fix anything that failed
	>>> test.run_fix_methods() 
    
    You could of course just take an instance of the default HealthValidataion object and fill up
    the internal tests list but it's often easier to have a bespoke class to test a specific set of data
    
    >>> test=r9popt.HealthValidation()
    >>> test.tests=[(r9popt.maya_sceneUnits_test, {'expected':'centimeter'}), 
    ...                     (r9popt.maya_timeUnits_test, {'expected':'ntsc'}),
    ...                     (r9popt.maya_upAxis_test, {'expected':'y'})]
    >>> test.run_health()



.. automodule:: Red9.pro_pack.core.optimiser

   .. rubric:: Main Classes

   .. autosummary::
   	  
      OptimizerUI
      OptimizeScene
      HealthTestObject
      HealthValidation




    


   
   
   