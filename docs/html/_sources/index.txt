.. Red9 documentation master file, created by
   sphinx-quickstart on Mon Jun 24 21:20:48 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Red9's documentation!
================================

Author : Mark Jackson 

| Red9 Consultancy Limited 
| http://red9consultancy.com 

https://vimeo.com/user9491246


| Red9 was born out of frustration for the lack of this kind of in-depth support that there is in the general Maya community. 
| We wanted to create full production ready tools suite which integrated seemlessly within Maya, giving users the 
| kind of pipeline support normally limited to larger studios. 

| The base of all our toolsets is the Red9 StudioPack, it's open source and has been in full production with a huge number of major studios since around 2011. 
| It's production battered, tested in anger and always growing.

| In 2013 we setup Red9Consultancy, allowing us to expand and tailor the pipelines around a larger, more complex studio based environment. 
| Supplying Rigs, Facial systems and bespoke pipelines to studios wanting a more dedicated solution. 

| To this end we now also have the Red9 ProPack, being designed alongside a number of AAA studios and including the kind of tools and workflows 
| that you can't get in a totally generic setup. To this end we extended our MetaData systems and now offer our own Red9 Puppet system.



Red9 StudioPack Modules
=======================

| The Red9 StudioPack core is coded in such a way as to allow most of the functions to be expanded upon, and used by any tech artists / programmer out there, 
| solving many common issues you find when coding in Maya. The core modules are expanding rapidly so keep up to date. Red9 main repository can 
| now be found on GitHub and I'll be branching on there every release:

https://github.com/markj3d/Red9_StudioPack

* Red9_Setup	: Red9 main setup manager
* Red9_AnimationUtils : all animation functions for dealing with data flow, key management, mirroring and time 
* Red9_Audio	: Audio tools for managing sound nodes, includes a full audio compiler for mixing multiple wav together
* Red9_CoreUtils : backbone of the systems, filtering, processing and managing nodes on mass
* Red9_General : general system calls
* Red9_Meta : MetaData api - huge library for data flow management around complex Maya rigs.
* Red9_PoseSaver : generic poseSaver for any rig
* Red9_Tools	: generic tools for Maya


StudioPack core
---------------

    .. toctree::
        :glob:
        

        red9core_templates/*

Red9 ProPack Modules
====================

| The ProPack is a far more complex in-depth set of tools, designed for mid / large studios that want that extra level service and the stress taking out of production. 
| We've developed the ProPack around the needs of production, including new file management systems, our own animation format, animation re-direction systems,
| metaData based export setups, extensive HealthManagement and testing and lots more. 

For more details contact us
. 


ProPack core
------------

    .. toctree::
        :glob:
        

        red9pro_templates/*
  
Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`