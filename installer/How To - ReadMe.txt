Red Nine Studio Pack:
=====================

Contact : Mark Jackson
Technical Animation Director
 
email: rednineinfo@gmail.com

Firstly thanks for your interest, if you'd like to get more involved mail me!

This Maya Python module is an ongoing project to bring extensive support for those 
studios without the luxury of their own R&D department. Maya out of the box is 
sadly lacking in a lot of the love that large studios show it through their own 
toolsets, this StudioPack is aimed at correcting that balance.

For suggestions and info please feel free to contact me.


Installation: 
======================================

	The system is designed to be booted as a standard Python site-package.
	You can do one of 2 things here, either copy the Red9 folder to your Maya
	scripts directory or any directory on the Maya Python path, 
	OR move it to any folder of your choice and make sure you set the 
	sys.path.append() correctly

	Note: the main folder containing all the Red9 subfolders must be called 'Red9',
	if you've downloaded a versioned zip file make sure to rename the folder correctly



	To Boot for a Maya session:
	===========================
	Open up a Python Tab in	the Script Editor and run the following:

	Note: You don't need to set the path if you dropped the "Red9" folder
	into the Maya scripts directory in your prefs, or any directory already 
	on a Python path.
	

	#Set the Python path
	#--------------------
	import sys
	sys.path.append('C:/ExtraSitePackages/RedNine_v1.42')

	
	#Launch the pack
	#--------------------
	import Red9
	Red9.start()

	
	This will boot the pack only for this Maya session.

	If you do need to set the path then point to folder that contains 
	the "Red9" folder NOT to the Red9 folder itself.

	if the pack was located : c:\markj\pythonModules\Red9_release141\Red
	set the path to:          c:\markj\pythonModules\Red9_release141\


	
	To Boot when Maya launches:
	===========================

	Copy the userSetup.py file into your Maya scripts folder found here:
	
	C:\user\xxxxx\Documents\maya\2012\scripts
	
	Then edit the folder path as per instructions in the userSetup file

	NOTE: if you have spaces in your path ie:
	-----------------------------------------

	sys.path.append('D:\My Documents\Maya\2012-x64\Red9_release\')

	then do so like the following (making the string a raw sting stops the escapes)
	
	sys.path.append(r'D:\My Documents\Maya\2012-x64\Red9_release\')

	
	
