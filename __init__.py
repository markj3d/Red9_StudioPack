'''
    ===============================================================================
    Red9 StudioPack:
    author : Mark Jackson
    email : rednineinfo@gmail.com

    This is the main entry point for initilizing the Red9 StudioPack. 
    Unlike previous releases I've removed the ability to install this via the
    Maya Module systems. Instead I've made it more of a standard Python site-package
    which has many benefits in the way the systems are managed.
    Simply running the following will initialize and install the setups
    
    You need to modify the path to point to the folder containing this file and
    add it to the system path UNLESS the Red9 folder is already on a Maya script path.
    
    import sys
    sys.path.append('P:\Red9_Pipeline\Red9_Release1.28')
    
    import Red9
    Red9.start()
    
    ===============================================================================
    
    
    License::
    ===============================================================================
    Red9 StudioPack is released under a BSD style license
    
    Copyright (c) 2013, Mark Jackson
    All rights reserved.
    
    Redistribution and use in source and binary forms, with or without modification, are 
    permitted provided that the following conditions are met:
    
    * Redistributions of source code must retain the above copyright notice, 
        this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright notice, 
        this list of conditions and the following disclaimer in the documentation 
        and/or other materials provided with the distribution.
    * Neither the name of the Red9 nor the names of its contributors may be used 
        to endorse or promote products derived from this software without specific 
        prior written permission.
        
    THIS SOFTWARE IS PROVIDED BY MARK JACKSON "AS IS" AND ANY EXPRESS OR IMPLIED 
    WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY 
    AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL MARK JACKSON
    BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL 
    DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; 
    LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED 
    AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT 
    (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, 
    EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
    ===============================================================================
    
'''


#Initialize the RED9_META_REGISTRY which is used by the MetaClass baseclass to
#know what subclasses there are, and what to consider in it's __new__ statement
#for initialization. If you're using the MetaClass as a base for your own modules
#you'll probably need to run the Red9.core.Red9_Meta.registerMClassInheritanceMapping()
#to update this dictionary
#global RED9_META_REGISTERY
#RED9_META_REGISTERY=[]

import maya.cmds as cmds
import startup.setup as setup

def start(Menu=True, MayaUIHooks=True, MayaOverloads=True, parentMenu='MayaWindow'):
  
    #Run the main setups. If you DON'T want the Red9Menu set 'Menu=False'
    #cmds.evalDeferred("Red9.setup.start(Menu=%s)" % Menu)
    cmds.evalDeferred("import Red9;Red9.setup.start(Menu=%s,MayaUIHooks=%s,MayaOverloads=%s,parentMenu='%s')" % (Menu,MayaUIHooks,MayaOverloads,parentMenu))
    #Import the core, not this is on LowPriority to make sure it
    #happens after the main setups have finished above
    cmds.evalDeferred("import Red9.core", lp=True)



