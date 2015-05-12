.. Red9 documentation master file, created by
   sphinx-quickstart on Mon Jun 24 21:20:48 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Red9's documentation!
================================

Author : Mark Jackson 

Red9 Consultancy Limited 
http://red9consultancy.com 

Red9 was born out of frustration for the lack of this kind of in-depth support
that there is in the general Maya community. I wanted to create full production
ready tools suite which integrated seemlessly within Maya, giving users the 
kind of pipeline support normally limited to larger studios. 

The Red9 core is coded in such a way as to allow most of the functions to be 
expanded upon, and used by any tech artists / programmer out there, solving many
common issues you find when coding in Maya. 

The core modules are expanding rapidly so keep up to date. Red9 main repository can 
now be found on GitHub and I'll be branching on there every release:

https://github.com/markj3d/Red9_StudioPack

* Red9_AnimationUtils : all animation functions for dealing with data flow, key management, mirroring and time 
* Red9_Audio	: Audio tools for managing sound nodes, includes a full audio compiler for mixing multiple wav together
* Red9_CoreUtils : backbone of the systems, filtering, processing and managing nodes on mass
* Red9_General : general system calls
* Red9_Meta : MetaData api - huge library for data flow management around complex Maya rigs.
* Red9_PoseSaver : generic poseSaver for any rig
* Red9_Tools	: generic tools for Maya


Red9 Modules
============

core
----

    .. toctree::
        :glob:
        

        red9templates/*
        
Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`