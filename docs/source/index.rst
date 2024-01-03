.. Red9 documentation master file, created by
   sphinx-quickstart on Mon Jun 24 21:20:48 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.


.. image:: Red9_ProPack_splash.png

| 
**Welcome to Red9 Pipeline Documentation**
=============================================
Authors : Mark Jackson / Franco Bresciani

| **Red9 Consultancy Limited**

| * **web** : http://red9consultancy.com
| * **email** : info@red9consultancy.com
| * **Vimeo** : http://vimeo.com/user9491246
| * **Twitter** : @red9_anim
| * **Facebook** : http://www.facebook.com/Red9Anim


Red9 was born out of frustration for the lack of this kind of in-depth support that there is in the general Maya community. 
We wanted to create full production ready tools suite which integrated seemlessly within Maya, giving users the kind 
of pipeline support normally limited to larger studios. 

The base of all our toolsets is the Red9 StudioPack, it's open source and has been in full production with a huge number 
of major studios since around 2011. It's production battered, tested in anger and always growing.

In 2013 we setup Red9Consultancy, allowing us to expand and tailor the pipelines around a larger, more complex studio 
based environment. Supplying Rigs, Facial systems and bespoke pipelines to studios wanting a more dedicated solution. 

To this end we now also have the Red9 ProPack, available on our new wedsite on a Subscription basis. This has been designed 
alongside numerous AAA studios and includes the kind of tools and workflows that you can't get in a totally generic setup. 

.. image:: Red9_ProPack_strap1.png

**Red9 StudioPack Modules**
============================

The Red9 StudioPack core is coded in such a way as to allow most of the functions to be expanded upon, and used by any 
tech artists / programmer out there, solving many common issues you find when coding in Maya. These core modules are 
updated on a daily basis as they form the core of the Red9 ProPack so make sure to keep up to date. 

Red9 main repository can now be found on GitHub in 2 repositories, one for Python2 covering upto Maya 2020, and one for Python3 covering Maya 2022+.

| http://github.com/markj3d/Red9_StudioPack
| http://github.com/markj3d/Red9_StudioPack_Python3

StudioPack core
---------------

    .. toctree::
        :glob:

        red9core_templates/*

.. image:: Red9_ProPack_strap2.png

**Red9 ProPack Modules**
=========================

The ProPack is a far more complex in-depth set of tools, designed for mid / large studios that want that extra level service 
and the stress taking out of production. We've developed the ProPack around the needs of production, 
including new file management systems, project management codebase, our own animation format, animation re-direction systems, 
metaData based export setups, extensive HealthManagement and testing and lots, lots more. 

**Red9/pro_pack/devkit/completion** 

Red9 ProPack is closed code however we have included predef stub code in the devkit above
which you can use in your Python editor to gain full autocompletion and doc strings

Red9 ProPack on boot consumes a "ProjectObject" which allows you to manage paths and system variables dynamically, switching them 
between different projects live in Maya, including Perforce mounts and workspaces. For more details please see the projects module docs.
We also support a number of Maya.env variables that can be modified to control the systems more carefully depending on your studio setups.

| **RED9_PROJECT_RESOURCES=path**  : custom folder containing x.project files, these are mounted by the ProjectManager
| **RED9_CLIENTCORE=path**  : custom path that allows you to direct the ClientCore path to suiot your company structures
| **RED9_PERFORCE_FORCE_ABORT=1**  : 0 or 1 hard abort for any Perforce binding & handling
| **RED9_LICENSE_LOCATION=path**  : custom path to find the R9USER license file
| **RED9_AIR_GAPPED=1**  : 0 or 1 designed for nodelocked based licenses where machines have no physical intrnal connection

For more details please visit our website or contact us: info@red9consultancy.com


ProPack core
------------

    .. toctree::
        :glob:

        red9pro_templates/*
		

ProPack tools
-------------

	These modules are generally the tool & UI wrapping over the main code in the core

    .. toctree::
        :glob:

        red9pro_templates/tools/*
 

ProPack puppet
-------------

	These modules are specific to puppet rig and tooling around that, this will expand over the next few years

    .. toctree::
        :glob:

        red9pro_templates/puppet/*
		
**Indices and tables**
=======================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. image:: Red9_ProPack_strap_pro.png
	:target: http://red9consultancy.com/propack