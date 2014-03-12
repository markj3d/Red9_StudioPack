//Maya ASCII 2012 scene
//Name: FilterNode_baseTests.ma
//Last modified: Mon, Apr 15, 2013 12:01:12 PM
//Codeset: 1252
requires maya "2012";
requires "stereoCamera" "10.0";
currentUnit -l centimeter -a degree -t film;
fileInfo "application" "maya";
fileInfo "product" "Maya 2012";
fileInfo "version" "2012 x64";
fileInfo "cutIdentifier" "001200000000-796618";
fileInfo "osv" "Microsoft Windows 7 Business Edition, 64-bit Windows 7 Service Pack 1 (Build 7601)\n";
createNode transform -s -n "persp";
	setAttr ".v" no;
	setAttr ".t" -type "double3" 1.5391764635881025 21.611392374624081 116.8152367953667 ;
	setAttr ".r" -type "double3" -2.7383527296031844 -2.1999999999997844 6.2166030182999049e-018 ;
createNode camera -s -n "perspShape" -p "persp";
	setAttr -k off ".v" no;
	setAttr ".fl" 34.999999999999993;
	setAttr ".coi" 119.57797361665536;
	setAttr ".imn" -type "string" "persp";
	setAttr ".den" -type "string" "persp_depth";
	setAttr ".man" -type "string" "persp_mask";
	setAttr ".hc" -type "string" "viewSet -p %camera";
createNode transform -s -n "top";
	setAttr ".v" no;
	setAttr ".t" -type "double3" 0 100.1 0 ;
	setAttr ".r" -type "double3" -89.999999999999986 0 0 ;
createNode camera -s -n "topShape" -p "top";
	setAttr -k off ".v" no;
	setAttr ".rnd" no;
	setAttr ".coi" 100.1;
	setAttr ".ow" 30;
	setAttr ".imn" -type "string" "top";
	setAttr ".den" -type "string" "top_depth";
	setAttr ".man" -type "string" "top_mask";
	setAttr ".hc" -type "string" "viewSet -t %camera";
	setAttr ".o" yes;
createNode transform -s -n "front";
	setAttr ".v" no;
	setAttr ".t" -type "double3" 0 0 100.1 ;
createNode camera -s -n "frontShape" -p "front";
	setAttr -k off ".v" no;
	setAttr ".rnd" no;
	setAttr ".coi" 100.1;
	setAttr ".ow" 106.19317566267516;
	setAttr ".imn" -type "string" "front";
	setAttr ".den" -type "string" "front_depth";
	setAttr ".man" -type "string" "front_mask";
	setAttr ".hc" -type "string" "viewSet -f %camera";
	setAttr ".o" yes;
createNode transform -s -n "side";
	setAttr ".v" no;
	setAttr ".t" -type "double3" 100.1 0 0 ;
	setAttr ".r" -type "double3" 0 89.999999999999986 0 ;
createNode camera -s -n "sideShape" -p "side";
	setAttr -k off ".v" no;
	setAttr ".rnd" no;
	setAttr ".coi" 100.1;
	setAttr ".ow" 30;
	setAttr ".imn" -type "string" "side";
	setAttr ".den" -type "string" "side_depth";
	setAttr ".man" -type "string" "side_mask";
	setAttr ".hc" -type "string" "viewSet -s %camera";
	setAttr ".o" yes;
createNode transform -n "locator1";
createNode locator -n "locatorShape1" -p "locator1";
	setAttr -k off ".v";
createNode transform -n "locator3";
	setAttr ".t" -type "double3" 0 6.6427928089323434 0 ;
createNode locator -n "locatorShape3" -p "locator3";
	setAttr -k off ".v";
createNode transform -n "camera3";
	setAttr ".t" -type "double3" 19.151003247046212 8.7991095999942033 0 ;
createNode camera -n "cameraShape3" -p "camera3";
	setAttr -k off ".v";
	setAttr ".rnd" no;
	setAttr ".cap" -type "double2" 1.41732 0.94488 ;
	setAttr ".ff" 0;
	setAttr ".ow" 30;
	setAttr ".imn" -type "string" "camera1";
	setAttr ".den" -type "string" "camera1_depth";
	setAttr ".man" -type "string" "camera1_mask";
createNode transform -n "pointLight3";
	setAttr ".t" -type "double3" 25.275873654885309 8.6265780392100027 0 ;
createNode pointLight -n "pointLightShape3" -p "pointLight3";
	setAttr -k off ".v";
createNode transform -n "pointLight4";
	setAttr ".t" -type "double3" 25.275873654885309 13.543727521559706 0 ;
createNode pointLight -n "pointLightShape4" -p "pointLight4";
	setAttr -k off ".v";
createNode transform -n "World_Root";
createNode joint -n "joint1" -p "World_Root";
	setAttr ".t" -type "double3" -3.6433793663688054 -0.012185215272137159 0 ;
	setAttr ".r" -type "double3" -4.2665598936896257e-007 -16.49501341721647 1.7309582018143121 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" 0 0 89.999999999999986 ;
	setAttr ".radi" 0.61844869604190589;
createNode joint -n "joint2_Ctrl" -p "|World_Root|joint1";
	setAttr ".t" -type "double3" 3.2900081234768472 7.3052855397756017e-016 0 ;
	setAttr ".r" -type "double3" 1.0439685387335194e-014 42.983836676891784 3.7109899871756524e-013 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".pa" -type "double3" 0 89.999999897160009 0 ;
	setAttr ".radi" 0.63448438061649026;
createNode joint -n "joint3_AttrMarked" -p "|World_Root|joint1|joint2_Ctrl";
	addAttr -ci true -sn "MarkerAttr" -ln "MarkerAttr" -dt "string";
	setAttr ".t" -type "double3" 3.6000313585854782 7.9936754073483622e-016 0 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" 0 0 -89.999999999999986 ;
	setAttr ".radi" 0.63448438061649026;
	setAttr -k on ".MarkerAttr" -type "string" "left";
createNode ikEffector -n "effector1" -p "|World_Root|joint1|joint2_Ctrl";
	setAttr ".v" no;
	setAttr ".hd" yes;
createNode joint -n "joint4" -p "World_Root";
	setAttr ".t" -type "double3" 4.0107393733741361 -0.080536935208317006 0 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" 0 0 89.999999999999986 ;
	setAttr ".radi" 0.63323309947840856;
createNode joint -n "joint5_AttrMarked" -p "|World_Root|joint4";
	addAttr -ci true -sn "MarkerAttr" -ln "MarkerAttr" -dt "string";
	setAttr ".t" -type "double3" 3.5758399232492319 7.9399596303302988e-016 0 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.63823194373271785;
	setAttr -k on ".MarkerAttr";
createNode joint -n "joint6_Ctrl" -p "|World_Root|joint4|joint5_AttrMarked";
	setAttr ".t" -type "double3" 3.672484245499211 8.15455313385274e-016 0 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" 0 0 -60.688103539485006 ;
	setAttr ".radi" 0.67751490982158769;
createNode joint -n "joint7_AttrMarked" -p "|World_Root|joint4|joint5_AttrMarked|joint6_Ctrl";
	addAttr -ci true -sn "MarkerAttr" -ln "MarkerAttr" -dt "string";
	setAttr ".t" -type "double3" 4.4319549232173605 6.6613381477509392e-016 0 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" 0 0 -54.952902284820269 ;
	setAttr ".radi" 0.74790222180931787;
	setAttr -k on ".MarkerAttr" -type "string" "left";
createNode joint -n "joint8" -p "|World_Root|joint4|joint5_AttrMarked|joint6_Ctrl|joint7_AttrMarked";
	setAttr ".t" -type "double3" 5.7927762883134761 -1.7763568394002505e-015 0 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" 180 0 -65.283039528467512 ;
	setAttr ".radi" 0.58227284371501231;
createNode joint -n "joint9" -p "|World_Root|joint4|joint5_AttrMarked|joint6_Ctrl|joint7_AttrMarked|joint8";
	setAttr ".t" -type "double3" 2.590608311823571 -2.3175905639050143e-015 -2.8349688781380121e-031 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" 0 180 89.075954647227121 ;
	setAttr ".radi" 0.58227284371501231;
createNode transform -n "pCube3" -p "|World_Root|joint4|joint5_AttrMarked|joint6_Ctrl";
	setAttr ".t" -type "double3" -12.191867470387797 5.0737014995313521 0.11357408139026504 ;
	setAttr ".r" -type "double3" 0 0 -29.31189646051498 ;
	setAttr ".s" -type "double3" 0.99999999999999989 0.99999999999999989 1 ;
createNode mesh -n "pCubeShape3" -p "|World_Root|joint4|joint5_AttrMarked|joint6_Ctrl|pCube3";
	setAttr -k off ".v";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 14 ".uvst[0].uvsp[0:13]" -type "float2" 0.375 0 0.625 0 0.375
		 0.25 0.625 0.25 0.375 0.5 0.625 0.5 0.375 0.75 0.625 0.75 0.375 1 0.625 1 0.875 0
		 0.875 0.25 0.125 0 0.125 0.25;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".covm[0]"  0 1 1;
	setAttr ".cdvm[0]"  0 1 1;
createNode transform -n "nurbsCircle1" -p "World_Root";
	setAttr ".t" -type "double3" -15.607020480148948 2.1516474836710167 0 ;
createNode nurbsCurve -n "nurbsCircleShape1" -p "|World_Root|nurbsCircle1";
	setAttr -k off ".v";
	setAttr ".tw" yes;
createNode transform -n "Spine_Ctrl" -p "World_Root";
	setAttr ".t" -type "double3" -15.607020480148948 32.295623993885428 0 ;
createNode nurbsCurve -n "Spine_CtrlShape" -p "|World_Root|Spine_Ctrl";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		3 8 2 no 3
		13 -2 -1 0 1 2 3 4 5 6 7 8 9 10
		11
		1.739234036768567 1.7392340367685644 0
		-2.8061646809873577e-016 2.4596483629390118 0
		-1.7392340367685657 1.7392340367685657 0
		-2.4596483629390118 7.1274456003626816e-016 0
		-1.7392340367685659 -1.7392340367685648 0
		-7.411400545420654e-016 -2.4596483629390118 0
		1.7392340367685644 -1.7392340367685657 0
		2.4596483629390118 -1.3210819338553792e-015 0
		1.739234036768567 1.7392340367685644 0
		-2.8061646809873577e-016 2.4596483629390118 0
		-1.7392340367685657 1.7392340367685657 0
		;
createNode transform -n "L_Foot_MarkerAttr_Ctrl" -p "|World_Root|Spine_Ctrl";
	addAttr -ci true -sn "MarkerAttr" -ln "MarkerAttr" -dt "string";
	setAttr ".t" -type "double3" 0 -8.0639764503451907 0 ;
	setAttr -k on ".MarkerAttr";
createNode nurbsCurve -n "L_Foot_MarkerAttr_CtrlShape" -p "|World_Root|Spine_Ctrl|L_Foot_MarkerAttr_Ctrl";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		3 8 2 no 3
		13 -2 -1 0 1 2 3 4 5 6 7 8 9 10
		11
		1.739234036768567 1.7392340367685644 0
		-2.8061646809873577e-016 2.4596483629390118 0
		-1.7392340367685657 1.7392340367685657 0
		-2.4596483629390118 7.1274456003626816e-016 0
		-1.7392340367685659 -1.7392340367685648 0
		-7.411400545420654e-016 -2.4596483629390118 0
		1.7392340367685644 -1.7392340367685657 0
		2.4596483629390118 -1.3210819338553792e-015 0
		1.739234036768567 1.7392340367685644 0
		-2.8061646809873577e-016 2.4596483629390118 0
		-1.7392340367685657 1.7392340367685657 0
		;
createNode transform -n "pCube2" -p "|World_Root|Spine_Ctrl|L_Foot_MarkerAttr_Ctrl";
	setAttr ".t" -type "double3" 6.5029468039693565 -21.132228282434319 0.11357408139026504 ;
createNode mesh -n "pCubeShape2" -p "|World_Root|Spine_Ctrl|L_Foot_MarkerAttr_Ctrl|pCube2";
	setAttr -k off ".v";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 14 ".uvst[0].uvsp[0:13]" -type "float2" 0.375 0 0.625 0 0.375
		 0.25 0.625 0.25 0.375 0.5 0.625 0.5 0.375 0.75 0.625 0.75 0.375 1 0.625 1 0.875 0
		 0.875 0.25 0.125 0 0.125 0.25;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".covm[0]"  0 1 1;
	setAttr ".cdvm[0]"  0 1 1;
createNode transform -n "L_Wrist_Ctrl" -p "|World_Root|Spine_Ctrl";
	setAttr ".t" -type "double3" 1.7763568394002505e-015 -23.188486453180353 0 ;
createNode nurbsCurve -n "L_Wrist_CtrlShape" -p "|World_Root|Spine_Ctrl|L_Wrist_Ctrl";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		3 8 2 no 3
		13 -2 -1 0 1 2 3 4 5 6 7 8 9 10
		11
		1.739234036768567 1.7392340367685644 0
		-2.8061646809873577e-016 2.4596483629390118 0
		-1.7392340367685657 1.7392340367685657 0
		-2.4596483629390118 7.1274456003626816e-016 0
		-1.7392340367685659 -1.7392340367685648 0
		-7.411400545420654e-016 -2.4596483629390118 0
		1.7392340367685644 -1.7392340367685657 0
		2.4596483629390118 -1.3210819338553792e-015 0
		1.739234036768567 1.7392340367685644 0
		-2.8061646809873577e-016 2.4596483629390118 0
		-1.7392340367685657 1.7392340367685657 0
		;
createNode transform -n "L_Pole_thingy" -p "|World_Root|Spine_Ctrl|L_Wrist_Ctrl";
	setAttr ".t" -type "double3" 15.607020480148948 0.71082667375467778 0 ;
createNode locator -n "L_Pole_thingyShape" -p "|World_Root|Spine_Ctrl|L_Wrist_Ctrl|L_Pole_thingy";
	setAttr -k off ".v";
createNode transform -n "R_Wrist_Ctrl" -p "|World_Root|Spine_Ctrl";
	setAttr ".t" -type "double3" 1.7763568394002505e-015 -15.986256374452974 0 ;
createNode nurbsCurve -n "R_Wrist_CtrlShape" -p "|World_Root|Spine_Ctrl|R_Wrist_Ctrl";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		3 8 2 no 3
		13 -2 -1 0 1 2 3 4 5 6 7 8 9 10
		11
		1.739234036768567 1.7392340367685644 0
		-2.8061646809873577e-016 2.4596483629390118 0
		-1.7392340367685657 1.7392340367685657 0
		-2.4596483629390118 7.1274456003626816e-016 0
		-1.7392340367685659 -1.7392340367685648 0
		-7.411400545420654e-016 -2.4596483629390118 0
		1.7392340367685644 -1.7392340367685657 0
		2.4596483629390118 -1.3210819338553792e-015 0
		1.739234036768567 1.7392340367685644 0
		-2.8061646809873577e-016 2.4596483629390118 0
		-1.7392340367685657 1.7392340367685657 0
		;
createNode transform -n "R_Pole_AttrMarked_Ctrl" -p "|World_Root|Spine_Ctrl|R_Wrist_Ctrl";
	addAttr -ci true -sn "MarkerAttr" -ln "MarkerAttr" -dt "string";
	setAttr ".t" -type "double3" 15.607020480148948 -6.4914034049727007 0 ;
	setAttr -k on ".MarkerAttr" -type "string" "right";
createNode locator -n "R_Pole_AttrMarked_CtrlShape" -p "|World_Root|Spine_Ctrl|R_Wrist_Ctrl|R_Pole_AttrMarked_Ctrl";
	setAttr -k off ".v";
createNode transform -n "pCube1" -p "|World_Root|Spine_Ctrl|R_Wrist_Ctrl|R_Pole_AttrMarked_Ctrl";
	setAttr ".t" -type "double3" -9.104073676179592 -9.2356576381542048 0.11357408139026504 ;
createNode mesh -n "pCubeShape1" -p "|World_Root|Spine_Ctrl|R_Wrist_Ctrl|R_Pole_AttrMarked_Ctrl|pCube1";
	addAttr -ci true -sn "mso" -ln "miShadingSamplesOverride" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "msh" -ln "miShadingSamples" -min 0 -smx 8 -at "float";
	addAttr -ci true -sn "mdo" -ln "miMaxDisplaceOverride" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "mmd" -ln "miMaxDisplace" -min 0 -smx 1 -at "float";
	setAttr -k off ".v";
	setAttr -s 4 ".iog[0].og";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".covm[0]"  0 1 1;
	setAttr ".cdvm[0]"  0 1 1;
createNode mesh -n "pCubeShape1Orig" -p "|World_Root|Spine_Ctrl|R_Wrist_Ctrl|R_Pole_AttrMarked_Ctrl|pCube1";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".covm[0]"  0 1 1;
	setAttr ".cdvm[0]"  0 1 1;
createNode transform -n "R_Pole_Ctrl" -p "|World_Root|Spine_Ctrl";
	addAttr -ci true -sn "floatAttr" -ln "floatAttr" -at "double";
	setAttr ".t" -type "double3" 15.607020480148948 -22.477659779425675 0 ;
	setAttr -k on ".floatAttr" 2.53333;
createNode locator -n "R_Pole_CtrlShape" -p "|World_Root|Spine_Ctrl|R_Pole_Ctrl";
	setAttr -k off ".v";
createNode transform -n "L_Pole_Ctrl" -p "|World_Root|Spine_Ctrl";
	addAttr -ci true -sn "floatAttr" -ln "floatAttr" -at "double";
	setAttr ".t" -type "double3" 15.607020480148948 -19.204731212714822 0 ;
	setAttr -k on ".floatAttr";
createNode locator -n "L_Pole_CtrlShape" -p "|World_Root|Spine_Ctrl|L_Pole_Ctrl";
	setAttr -k off ".v";
createNode transform -n "camera1" -p "World_Root";
	addAttr -ci true -sn "export" -ln "export" -min 0 -max 1 -at "bool";
	setAttr ".t" -type "double3" 19.151003247046212 0 0 ;
	setAttr -k on ".export";
createNode camera -n "cameraShape1" -p "|World_Root|camera1";
	setAttr -k off ".v";
	setAttr ".rnd" no;
	setAttr ".cap" -type "double2" 1.41732 0.94488 ;
	setAttr ".ff" 0;
	setAttr ".ow" 30;
	setAttr ".imn" -type "string" "camera1";
	setAttr ".den" -type "string" "camera1_depth";
	setAttr ".man" -type "string" "camera1_mask";
createNode transform -n "camera2" -p "World_Root";
	addAttr -ci true -sn "export" -ln "export" -min 0 -max 1 -at "bool";
	setAttr ".t" -type "double3" 19.151003247046212 4.0544916784287022 0 ;
	setAttr -k on ".export" yes;
createNode camera -n "cameraShape2" -p "|World_Root|camera2";
	setAttr -k off ".v";
	setAttr ".rnd" no;
	setAttr ".cap" -type "double2" 1.41732 0.94488 ;
	setAttr ".ff" 0;
	setAttr ".ow" 30;
	setAttr ".imn" -type "string" "camera1";
	setAttr ".den" -type "string" "camera1_depth";
	setAttr ".man" -type "string" "camera1_mask";
createNode transform -n "pointLight1" -p "World_Root";
	setAttr ".t" -type "double3" 25.275873654885309 0 0 ;
createNode pointLight -n "pointLightShape1" -p "|World_Root|pointLight1";
	setAttr -k off ".v";
createNode transform -n "pointLight2" -p "World_Root";
	setAttr ".t" -type "double3" 25.275873654885309 4.0544916784287022 0 ;
createNode pointLight -n "pointLightShape2" -p "|World_Root|pointLight2";
	setAttr -k off ".v";
createNode transform -n "nurbsSphere1" -p "World_Root";
	setAttr ".t" -type "double3" -24.092390838288175 1.6667691774916349 0 ;
createNode nurbsSurface -n "nurbsSphereShape1" -p "|World_Root|nurbsSphere1";
	setAttr -k off ".v";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".tw" yes;
	setAttr ".covm[0]"  0 1 1;
	setAttr ".cdvm[0]"  0 1 1;
	setAttr ".dvu" 0;
	setAttr ".dvv" 0;
	setAttr ".cpr" 4;
	setAttr ".cps" 4;
	setAttr ".nufa" 4.5;
	setAttr ".nvfa" 4.5;
createNode transform -n "pCube4_AttrMarked" -p "World_Root";
	addAttr -ci true -sn "MarkerAttr" -ln "MarkerAttr" -dt "string";
	setAttr ".t" -type "double3" -9.104073676179592 8.2801814611384703 0.11357408139026504 ;
	setAttr -k on ".MarkerAttr" -type "string" "right";
createNode mesh -n "pCube4_AttrMarkedShape" -p "pCube4_AttrMarked";
	setAttr -k off ".v";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 14 ".uvst[0].uvsp[0:13]" -type "float2" 0.375 0 0.625 0 0.375
		 0.25 0.625 0.25 0.375 0.5 0.625 0.5 0.375 0.75 0.625 0.75 0.375 1 0.625 1 0.875 0
		 0.875 0.25 0.125 0 0.125 0.25;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".covm[0]"  0 1 1;
	setAttr ".cdvm[0]"  0 1 1;
createNode transform -n "pCube5" -p "pCube4_AttrMarked";
	setAttr ".t" -type "double3" 0 2.9181213705469879 0 ;
createNode mesh -n "pCubeShape5" -p "|World_Root|pCube4_AttrMarked|pCube5";
	setAttr -k off ".v";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 14 ".uvst[0].uvsp[0:13]" -type "float2" 0.375 0 0.625 0 0.375
		 0.25 0.625 0.25 0.375 0.5 0.625 0.5 0.375 0.75 0.625 0.75 0.375 1 0.625 1 0.875 0
		 0.875 0.25 0.125 0 0.125 0.25;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".covm[0]"  0 1 1;
	setAttr ".cdvm[0]"  0 1 1;
createNode transform -n "IK_Ctrl" -p "World_Root";
	setAttr ".t" -type "double3" -3.8359970113906416 6.361637895492386 -0.67156166760067837 ;
createNode locator -n "IK_CtrlShape" -p "|World_Root|IK_Ctrl";
	setAttr -k off ".v";
createNode ikHandle -n "ikHandle1" -p "|World_Root|IK_Ctrl";
	setAttr ".t" -type "double3" 0 8.8817841970012523e-016 0 ;
	setAttr ".r" -type "double3" 0 0 89.999999999999986 ;
	setAttr ".roc" yes;
createNode transform -n "World_Root2_chSet";
createNode joint -n "joint1" -p "World_Root2_chSet";
	setAttr ".t" -type "double3" -3.6433793663688054 -0.012185215272137159 0 ;
	setAttr ".r" -type "double3" -4.2665688995361545e-007 -16.495013417216473 1.7309582018146501 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" 0 0 89.999999999999986 ;
	setAttr ".radi" 0.61844869604190589;
createNode joint -n "joint2_Ctrl" -p "|World_Root2_chSet|joint1";
	setAttr ".r" -type "double3" 1.0439685387335298e-014 42.983836676891734 3.7109899896632391e-013 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".pa" -type "double3" 0 89.999999897160009 0 ;
	setAttr ".radi" 0.63448438061649026;
createNode joint -n "joint3_AttrMarked" -p "|World_Root2_chSet|joint1|joint2_Ctrl";
	addAttr -ci true -sn "MarkerAttr" -ln "MarkerAttr" -dt "string";
	setAttr ".t" -type "double3" 3.6000313585854782 7.9936754073483622e-016 0 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" 0 0 -89.999999999999986 ;
	setAttr ".radi" 0.63448438061649026;
	setAttr -k on ".MarkerAttr";
createNode ikEffector -n "effector1" -p "|World_Root2_chSet|joint1|joint2_Ctrl";
	setAttr ".v" no;
	setAttr ".t" -type "double3" 3.6000313585854782 7.9936754073483622e-016 0 ;
	setAttr ".hd" yes;
createNode joint -n "joint4" -p "World_Root2_chSet";
	setAttr ".t" -type "double3" 4.0107393733741361 -0.080536935208317006 0 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" 0 0 89.999999999999986 ;
	setAttr ".radi" 0.63323309947840856;
createNode joint -n "joint5_AttrMarked" -p "|World_Root2_chSet|joint4";
	addAttr -ci true -sn "MarkerAttr" -ln "MarkerAttr" -dt "string";
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.63823194373271785;
	setAttr -k on ".MarkerAttr";
createNode joint -n "joint6_Ctrl" -p "|World_Root2_chSet|joint4|joint5_AttrMarked";
	setAttr ".t" -type "double3" 3.672484245499211 8.15455313385274e-016 0 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" 0 0 -60.688103539485006 ;
	setAttr ".radi" 0.67751490982158769;
createNode joint -n "joint7_AttrMarked" -p "|World_Root2_chSet|joint4|joint5_AttrMarked|joint6_Ctrl";
	addAttr -ci true -sn "MarkerAttr" -ln "MarkerAttr" -dt "string";
	setAttr ".t" -type "double3" 4.4319549232173605 6.6613381477509392e-016 0 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" 0 0 -54.952902284820269 ;
	setAttr ".radi" 0.74790222180931787;
	setAttr -k on ".MarkerAttr";
createNode joint -n "joint8" -p "|World_Root2_chSet|joint4|joint5_AttrMarked|joint6_Ctrl|joint7_AttrMarked";
	setAttr ".t" -type "double3" 5.7927762883134761 -1.7763568394002505e-015 0 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" 180 0 -65.283039528467512 ;
	setAttr ".radi" 0.58227284371501231;
createNode joint -n "joint9" -p "|World_Root2_chSet|joint4|joint5_AttrMarked|joint6_Ctrl|joint7_AttrMarked|joint8";
	setAttr ".t" -type "double3" 2.590608311823571 -2.3175905639050143e-015 -2.8349688781380121e-031 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" 0 180 89.075954647227121 ;
	setAttr ".radi" 0.58227284371501231;
createNode transform -n "pCube3" -p "|World_Root2_chSet|joint4|joint5_AttrMarked|joint6_Ctrl";
	setAttr ".t" -type "double3" -12.191867470387797 5.0737014995313521 0.11357408139026504 ;
	setAttr ".r" -type "double3" 0 0 -29.31189646051498 ;
	setAttr ".s" -type "double3" 0.99999999999999989 0.99999999999999989 1 ;
createNode mesh -n "pCubeShape3" -p "|World_Root2_chSet|joint4|joint5_AttrMarked|joint6_Ctrl|pCube3";
	setAttr -k off ".v";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 14 ".uvst[0].uvsp[0:13]" -type "float2" 0.375 0 0.625 0 0.375
		 0.25 0.625 0.25 0.375 0.5 0.625 0.5 0.375 0.75 0.625 0.75 0.375 1 0.625 1 0.875 0
		 0.875 0.25 0.125 0 0.125 0.25;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".covm[0]"  0 1 1;
	setAttr ".cdvm[0]"  0 1 1;
createNode transform -n "nurbsCircle1" -p "World_Root2_chSet";
createNode nurbsCurve -n "nurbsCircleShape1" -p "|World_Root2_chSet|nurbsCircle1";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		3 8 2 no 3
		13 -2 -1 0 1 2 3 4 5 6 7 8 9 10
		11
		1.739234036768567 1.7392340367685644 0
		-2.8061646809873577e-016 2.4596483629390118 0
		-1.7392340367685657 1.7392340367685657 0
		-2.4596483629390118 7.1274456003626816e-016 0
		-1.7392340367685659 -1.7392340367685648 0
		-7.411400545420654e-016 -2.4596483629390118 0
		1.7392340367685644 -1.7392340367685657 0
		2.4596483629390118 -1.3210819338553792e-015 0
		1.739234036768567 1.7392340367685644 0
		-2.8061646809873577e-016 2.4596483629390118 0
		-1.7392340367685657 1.7392340367685657 0
		;
createNode transform -n "Spine_Ctrl" -p "World_Root2_chSet";
createNode nurbsCurve -n "Spine_CtrlShape" -p "|World_Root2_chSet|Spine_Ctrl";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		3 8 2 no 3
		13 -2 -1 0 1 2 3 4 5 6 7 8 9 10
		11
		1.739234036768567 1.7392340367685644 0
		-2.8061646809873577e-016 2.4596483629390118 0
		-1.7392340367685657 1.7392340367685657 0
		-2.4596483629390118 7.1274456003626816e-016 0
		-1.7392340367685659 -1.7392340367685648 0
		-7.411400545420654e-016 -2.4596483629390118 0
		1.7392340367685644 -1.7392340367685657 0
		2.4596483629390118 -1.3210819338553792e-015 0
		1.739234036768567 1.7392340367685644 0
		-2.8061646809873577e-016 2.4596483629390118 0
		-1.7392340367685657 1.7392340367685657 0
		;
createNode transform -n "L_Foot_MarkerAttr_Ctrl" -p "|World_Root2_chSet|Spine_Ctrl";
	addAttr -ci true -sn "MarkerAttr" -ln "MarkerAttr" -dt "string";
	setAttr -k on ".MarkerAttr" -type "string" "right";
createNode nurbsCurve -n "L_Foot_MarkerAttr_CtrlShape" -p "|World_Root2_chSet|Spine_Ctrl|L_Foot_MarkerAttr_Ctrl";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		3 8 2 no 3
		13 -2 -1 0 1 2 3 4 5 6 7 8 9 10
		11
		1.739234036768567 1.7392340367685644 0
		-2.8061646809873577e-016 2.4596483629390118 0
		-1.7392340367685657 1.7392340367685657 0
		-2.4596483629390118 7.1274456003626816e-016 0
		-1.7392340367685659 -1.7392340367685648 0
		-7.411400545420654e-016 -2.4596483629390118 0
		1.7392340367685644 -1.7392340367685657 0
		2.4596483629390118 -1.3210819338553792e-015 0
		1.739234036768567 1.7392340367685644 0
		-2.8061646809873577e-016 2.4596483629390118 0
		-1.7392340367685657 1.7392340367685657 0
		;
createNode transform -n "pCube2" -p "|World_Root2_chSet|Spine_Ctrl|L_Foot_MarkerAttr_Ctrl";
	setAttr ".t" -type "double3" 6.5029468039693565 -21.132228282434319 0.11357408139026504 ;
createNode mesh -n "pCubeShape2" -p "|World_Root2_chSet|Spine_Ctrl|L_Foot_MarkerAttr_Ctrl|pCube2";
	setAttr -k off ".v";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 14 ".uvst[0].uvsp[0:13]" -type "float2" 0.375 0 0.625 0 0.375
		 0.25 0.625 0.25 0.375 0.5 0.625 0.5 0.375 0.75 0.625 0.75 0.375 1 0.625 1 0.875 0
		 0.875 0.25 0.125 0 0.125 0.25;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".covm[0]"  0 1 1;
	setAttr ".cdvm[0]"  0 1 1;
createNode transform -n "L_Wrist_Ctrl" -p "|World_Root2_chSet|Spine_Ctrl";
createNode nurbsCurve -n "L_Wrist_CtrlShape" -p "|World_Root2_chSet|Spine_Ctrl|L_Wrist_Ctrl";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		3 8 2 no 3
		13 -2 -1 0 1 2 3 4 5 6 7 8 9 10
		11
		1.739234036768567 1.7392340367685644 0
		-2.8061646809873577e-016 2.4596483629390118 0
		-1.7392340367685657 1.7392340367685657 0
		-2.4596483629390118 7.1274456003626816e-016 0
		-1.7392340367685659 -1.7392340367685648 0
		-7.411400545420654e-016 -2.4596483629390118 0
		1.7392340367685644 -1.7392340367685657 0
		2.4596483629390118 -1.3210819338553792e-015 0
		1.739234036768567 1.7392340367685644 0
		-2.8061646809873577e-016 2.4596483629390118 0
		-1.7392340367685657 1.7392340367685657 0
		;
createNode transform -n "L_Pole_thingy" -p "|World_Root2_chSet|Spine_Ctrl|L_Wrist_Ctrl";
	setAttr ".t" -type "double3" 15.607020480148948 0.71082667375467778 0 ;
createNode locator -n "L_Pole_thingyShape" -p "|World_Root2_chSet|Spine_Ctrl|L_Wrist_Ctrl|L_Pole_thingy";
	setAttr -k off ".v";
createNode transform -n "R_Wrist_Ctrl" -p "|World_Root2_chSet|Spine_Ctrl";
createNode nurbsCurve -n "R_Wrist_CtrlShape" -p "|World_Root2_chSet|Spine_Ctrl|R_Wrist_Ctrl";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		3 8 2 no 3
		13 -2 -1 0 1 2 3 4 5 6 7 8 9 10
		11
		1.739234036768567 1.7392340367685644 0
		-2.8061646809873577e-016 2.4596483629390118 0
		-1.7392340367685657 1.7392340367685657 0
		-2.4596483629390118 7.1274456003626816e-016 0
		-1.7392340367685659 -1.7392340367685648 0
		-7.411400545420654e-016 -2.4596483629390118 0
		1.7392340367685644 -1.7392340367685657 0
		2.4596483629390118 -1.3210819338553792e-015 0
		1.739234036768567 1.7392340367685644 0
		-2.8061646809873577e-016 2.4596483629390118 0
		-1.7392340367685657 1.7392340367685657 0
		;
createNode transform -n "R_Pole_AttrMarked_Ctrl" -p "|World_Root2_chSet|Spine_Ctrl|R_Wrist_Ctrl";
	addAttr -ci true -sn "MarkerAttr" -ln "MarkerAttr" -dt "string";
	setAttr ".t" -type "double3" 15.607020480148948 -6.4914034049727007 0 ;
	setAttr -k on ".MarkerAttr";
createNode locator -n "R_Pole_AttrMarked_CtrlShape" -p "|World_Root2_chSet|Spine_Ctrl|R_Wrist_Ctrl|R_Pole_AttrMarked_Ctrl";
	setAttr -k off ".v";
createNode transform -n "pCube1" -p "|World_Root2_chSet|Spine_Ctrl|R_Wrist_Ctrl|R_Pole_AttrMarked_Ctrl";
	setAttr ".t" -type "double3" -9.104073676179592 -9.2356576381542048 0.11357408139026504 ;
createNode mesh -n "pCubeShape1" -p "|World_Root2_chSet|Spine_Ctrl|R_Wrist_Ctrl|R_Pole_AttrMarked_Ctrl|pCube1";
	setAttr -k off ".v";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 14 ".uvst[0].uvsp[0:13]" -type "float2" 0.375 0 0.625 0 0.375
		 0.25 0.625 0.25 0.375 0.5 0.625 0.5 0.375 0.75 0.625 0.75 0.375 1 0.625 1 0.875 0
		 0.875 0.25 0.125 0 0.125 0.25;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".covm[0]"  0 1 1;
	setAttr ".cdvm[0]"  0 1 1;
createNode transform -n "R_Pole_Ctrl" -p "|World_Root2_chSet|Spine_Ctrl";
createNode locator -n "R_Pole_CtrlShape" -p "|World_Root2_chSet|Spine_Ctrl|R_Pole_Ctrl";
	setAttr -k off ".v";
createNode transform -n "L_Pole_Ctrl" -p "|World_Root2_chSet|Spine_Ctrl";
createNode locator -n "L_Pole_CtrlShape" -p "|World_Root2_chSet|Spine_Ctrl|L_Pole_Ctrl";
	setAttr -k off ".v";
createNode transform -n "camera1" -p "World_Root2_chSet";
	setAttr ".t" -type "double3" 19.151003247046212 0 0 ;
createNode camera -n "cameraShape1" -p "|World_Root2_chSet|camera1";
	setAttr -k off ".v";
	setAttr ".rnd" no;
	setAttr ".cap" -type "double2" 1.41732 0.94488 ;
	setAttr ".ff" 0;
	setAttr ".ow" 30;
	setAttr ".imn" -type "string" "camera1";
	setAttr ".den" -type "string" "camera1_depth";
	setAttr ".man" -type "string" "camera1_mask";
createNode transform -n "camera2" -p "World_Root2_chSet";
	setAttr ".t" -type "double3" 19.151003247046212 4.0544916784287022 0 ;
createNode camera -n "cameraShape2" -p "|World_Root2_chSet|camera2";
	setAttr -k off ".v";
	setAttr ".rnd" no;
	setAttr ".cap" -type "double2" 1.41732 0.94488 ;
	setAttr ".ff" 0;
	setAttr ".ow" 30;
	setAttr ".imn" -type "string" "camera1";
	setAttr ".den" -type "string" "camera1_depth";
	setAttr ".man" -type "string" "camera1_mask";
createNode transform -n "pCube6" -p "World_Root2_chSet";
	setAttr ".t" -type "double3" -9.1040736761795902 0.58230657630554816 0.11357408139026504 ;
createNode mesh -n "pCubeShape6" -p "pCube6";
	setAttr -k off ".v";
	setAttr -s 4 ".iog[0].og";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".covm[0]"  0 1 1;
	setAttr ".cdvm[0]"  0 1 1;
createNode mesh -n "pCubeShape1Orig6" -p "pCube6";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 14 ".uvst[0].uvsp[0:13]" -type "float2" 0.375 0 0.625 0 0.375
		 0.25 0.625 0.25 0.375 0.5 0.625 0.5 0.375 0.75 0.625 0.75 0.375 1 0.625 1 0.875 0
		 0.875 0.25 0.125 0 0.125 0.25;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".covm[0]"  0 1 1;
	setAttr ".cdvm[0]"  0 1 1;
createNode mesh -n "pCubeShape6Orig" -p "pCube6";
	setAttr -k off ".v";
	setAttr ".io" yes;
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 14 ".uvst[0].uvsp[0:13]" -type "float2" 0.375 0 0.625 0 0.375
		 0.25 0.625 0.25 0.375 0.5 0.625 0.5 0.375 0.75 0.625 0.75 0.375 1 0.625 1 0.875 0
		 0.875 0.25 0.125 0 0.125 0.25;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".covm[0]"  0 1 1;
	setAttr ".cdvm[0]"  0 1 1;
createNode transform -n "pointLight1" -p "World_Root2_chSet";
	setAttr ".t" -type "double3" 25.275873654885309 0 0 ;
createNode pointLight -n "pointLightShape1" -p "|World_Root2_chSet|pointLight1";
	setAttr -k off ".v";
createNode transform -n "pointLight2" -p "World_Root2_chSet";
	setAttr ".t" -type "double3" 25.275873654885309 4.0544916784287022 0 ;
createNode pointLight -n "pointLightShape2" -p "|World_Root2_chSet|pointLight2";
	setAttr -k off ".v";
createNode transform -n "nurbsSphere1" -p "World_Root2_chSet";
	setAttr ".t" -type "double3" -24.092390838288175 1.6667691774916349 0 ;
createNode nurbsSurface -n "nurbsSphereShape1" -p "|World_Root2_chSet|nurbsSphere1";
	setAttr -k off ".v";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".covm[0]"  0 1 1;
	setAttr ".cdvm[0]"  0 1 1;
	setAttr ".dvu" 0;
	setAttr ".dvv" 0;
	setAttr ".cpr" 4;
	setAttr ".cps" 4;
	setAttr ".cc" -type "nurbsSurface" 
		3 3 0 2 no 
		9 0 0 0 1 2 3 4 4 4
		13 -2 -1 0 1 2 3 4 5 6 7 8 9 10
		
		77
		2.0257455296216898e-016 4.0514910592433874e-016 -2.1109267692085179
		2.0257455296216898e-016 4.0514910592433874e-016 -2.1109267692085179
		2.0257455296216898e-016 4.0514910592433874e-016 -2.1109267692085179
		2.0257455296216898e-016 4.0514910592433874e-016 -2.1109267692085179
		2.0257455296216898e-016 4.0514910592433874e-016 -2.1109267692085179
		2.0257455296216898e-016 4.0514910592433874e-016 -2.1109267692085179
		2.0257455296216898e-016 4.0514910592433874e-016 -2.1109267692085179
		2.0257455296216898e-016 4.0514910592433874e-016 -2.1109267692085179
		2.0257455296216898e-016 4.0514910592433874e-016 -2.1109267692085179
		2.0257455296216898e-016 4.0514910592433874e-016 -2.1109267692085179
		2.0257455296216898e-016 4.0514910592433874e-016 -2.1109267692085179
		0.42200970539075888 0.42200970539075966 -2.1109267692085179
		0.59681184881668603 2.0643722135865716e-018 -2.1109267692085179
		0.42200970539075927 -0.42200970539075922 -2.1109267692085179
		2.4309461079423687e-016 -0.59681184881668603 -2.1109267692085179
		-0.42200970539075905 -0.42200970539075944 -2.1109267692085179
		-0.59681184881668614 -2.4998452555986587e-016 -2.1109267692085179
		-0.42200970539075938 0.42200970539075888 -2.1109267692085179
		-3.9070227628161173e-016 0.59681184881668603 -2.1109267692085179
		0.42200970539075888 0.42200970539075966 -2.1109267692085179
		0.59681184881668603 2.0643722135865716e-018 -2.1109267692085179
		0.42200970539075927 -0.42200970539075922 -2.1109267692085179
		1.3012385454715274 1.3012385454715294 -1.6541467556458691
		1.8402291988884747 -3.2306525664204904e-016 -1.6541467556458691
		1.3012385454715281 -1.3012385454715281 -1.6541467556458691
		4.2013527419628378e-016 -1.8402291988884747 -1.6541467556458691
		-1.3012385454715278 -1.3012385454715285 -1.6541467556458691
		-1.8402291988884747 -4.4137986301385242e-016 -1.6541467556458691
		-1.3012385454715285 1.3012385454715274 -1.6541467556458691
		-8.7527358377944893e-016 1.8402291988884747 -1.6541467556458691
		1.3012385454715274 1.3012385454715294 -1.6541467556458691
		1.8402291988884747 -3.2306525664204904e-016 -1.6541467556458691
		1.3012385454715281 -1.3012385454715281 -1.6541467556458691
		1.8306008607330384 1.8306008607330413 2.5865343080019434e-017
		2.5888605645405263 -6.1240201568640807e-016 2.5865343080019434e-017
		1.8306008607330393 -1.8306008607330395 2.5865343080019434e-017
		4.3314304304600151e-016 -2.5888605645405263 2.5865343080019434e-017
		-1.8306008607330393 -1.8306008607330395 2.5865343080019434e-017
		-2.5888605645405267 -4.6303023222488329e-016 2.5865343080019434e-017
		-1.8306008607330395 1.8306008607330384 2.5865343080019434e-017
		-1.0734380790139113e-015 2.5888605645405263 2.5865343080019434e-017
		1.8306008607330384 1.8306008607330413 2.5865343080019434e-017
		2.5888605645405263 -6.1240201568640807e-016 2.5865343080019434e-017
		1.8306008607330393 -1.8306008607330395 2.5865343080019434e-017
		1.3012385454715281 1.3012385454715294 1.6541467556458695
		1.8402291988884751 -5.4755719878115377e-016 1.6541467556458695
		1.3012385454715285 -1.3012385454715287 1.6541467556458695
		1.9564333205717944e-016 -1.8402291988884751 1.6541467556458695
		-1.3012385454715285 -1.3012385454715287 1.6541467556458695
		-1.8402291988884751 -2.1688792087474788e-016 1.6541467556458695
		-1.3012385454715285 1.3012385454715281 1.6541467556458695
		-6.5078164164034464e-016 1.8402291988884751 1.6541467556458695
		1.3012385454715281 1.3012385454715294 1.6541467556458695
		1.8402291988884751 -5.4755719878115377e-016 1.6541467556458695
		1.3012385454715285 -1.3012385454715287 1.6541467556458695
		0.42200970539075938 0.42200970539075966 2.1109267692085174
		0.59681184881668625 -2.8441930797718016e-016 2.1109267692085174
		0.42200970539075927 -0.4220097053907596 2.1109267692085174
		-4.3389069396529736e-017 -0.59681184881668625 2.1109267692085174
		-0.42200970539075949 -0.42200970539075938 2.1109267692085174
		-0.59681184881668636 3.6499154630900733e-017 2.1109267692085174
		-0.42200970539075938 0.42200970539075938 2.1109267692085174
		-1.0421859609084527e-016 0.59681184881668625 2.1109267692085174
		0.42200970539075938 0.42200970539075966 2.1109267692085174
		0.59681184881668625 -2.8441930797718016e-016 2.1109267692085174
		0.42200970539075927 -0.4220097053907596 2.1109267692085174
		3.6729436284540931e-016 1.6471980988324028e-016 2.1109267692085179
		3.6729436284540931e-016 1.6471980988324028e-016 2.1109267692085179
		3.6729436284540931e-016 1.6471980988324028e-016 2.1109267692085179
		3.6729436284540931e-016 1.6471980988324028e-016 2.1109267692085179
		3.6729436284540931e-016 1.6471980988324028e-016 2.1109267692085179
		3.6729436284540931e-016 1.6471980988324028e-016 2.1109267692085179
		3.6729436284540931e-016 1.6471980988324028e-016 2.1109267692085179
		3.6729436284540931e-016 1.6471980988324028e-016 2.1109267692085179
		3.6729436284540931e-016 1.6471980988324028e-016 2.1109267692085179
		3.6729436284540931e-016 1.6471980988324028e-016 2.1109267692085179
		3.6729436284540931e-016 1.6471980988324028e-016 2.1109267692085179
		
		;
	setAttr ".nufa" 4.5;
	setAttr ".nvfa" 4.5;
createNode transform -n "pCube4_AttrMarked_Bingo" -p "World_Root2_chSet";
	addAttr -ci true -sn "MarkerAttr" -ln "MarkerAttr" -dt "string";
	setAttr -k on ".MarkerAttr" -type "string" "right";
createNode mesh -n "pCube4_AttrMarked_BingoShape" -p "pCube4_AttrMarked_Bingo";
	setAttr -k off ".v";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 14 ".uvst[0].uvsp[0:13]" -type "float2" 0.375 0 0.625 0 0.375
		 0.25 0.625 0.25 0.375 0.5 0.625 0.5 0.375 0.75 0.625 0.75 0.375 1 0.625 1 0.875 0
		 0.875 0.25 0.125 0 0.125 0.25;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".covm[0]"  0 1 1;
	setAttr ".cdvm[0]"  0 1 1;
createNode transform -n "pCube5" -p "pCube4_AttrMarked_Bingo";
	setAttr ".t" -type "double3" 0 2.9181213705469879 0 ;
createNode mesh -n "pCubeShape5" -p "|World_Root2_chSet|pCube4_AttrMarked_Bingo|pCube5";
	setAttr -k off ".v";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 14 ".uvst[0].uvsp[0:13]" -type "float2" 0.375 0 0.625 0 0.375
		 0.25 0.625 0.25 0.375 0.5 0.625 0.5 0.375 0.75 0.625 0.75 0.375 1 0.625 1 0.875 0
		 0.875 0.25 0.125 0 0.125 0.25;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".covm[0]"  0 1 1;
	setAttr ".cdvm[0]"  0 1 1;
createNode transform -n "IK_Ctrl" -p "World_Root2_chSet";
	setAttr ".t" -type "double3" -3.8359970113906416 6.361637895492386 -0.67156166760067837 ;
createNode locator -n "IK_CtrlShape" -p "|World_Root2_chSet|IK_Ctrl";
	setAttr -k off ".v";
createNode ikHandle -n "ikHandle1" -p "|World_Root2_chSet|IK_Ctrl";
	setAttr ".t" -type "double3" 0 8.8817841970012523e-016 0 ;
	setAttr ".r" -type "double3" 0 0 89.999999999999986 ;
	setAttr ".roc" yes;
createNode lightLinker -s -n "lightLinker1";
	setAttr -s 2 ".lnk";
	setAttr -s 2 ".slnk";
createNode displayLayerManager -n "layerManager";
createNode displayLayer -n "defaultLayer";
createNode renderLayerManager -n "renderLayerManager";
createNode renderLayer -n "defaultRenderLayer";
	setAttr ".g" yes;
createNode ikRPsolver -n "ikRPsolver";
createNode makeNurbSphere -n "makeNurbSphere1";
	setAttr ".ax" -type "double3" 0 0 1 ;
	setAttr ".r" 2.1109267692085179;
createNode makeNurbCircle -n "makeNurbCircle1";
	setAttr ".r" 2.2195102542155296;
createNode polyCube -n "polyCube1";
	setAttr ".w" 1.6934999976697931;
	setAttr ".h" 1.1646131526110912;
	setAttr ".d" 3.5094196260200547;
	setAttr ".cuv" 4;
createNode script -n "sceneConfigurationScriptNode";
	setAttr ".b" -type "string" "playbackOptions -min 1 -max 24 -ast 1 -aet 48 ";
	setAttr ".st" 6;
createNode character -n "TestChSet";
	addAttr -ci true -h true -sn "aal" -ln "attributeAliasList" -dt "attributeAlias";
	setAttr -s 30 ".dnsm";
	setAttr -s 30 ".lv[2:30]"  -19.204731212714822 15.607020480148948 0 
		-22.477659779425675 15.607020480148948 0 -15.986256374452974 1.7763568394002505e-015 
		0 -23.188486453180353 1.7763568394002505e-015 0 -8.0639764503451907 0 0 7.3052855397756017e-016 
		3.2900081234768472 0 7.9399596303302988e-016 3.5758399232492319 0.11357408139026504 
		8.2801814611384703 -9.104073676179592 0 32.295623993885428 -15.607020480148948 0 
		2.1516474836710167 -15.607020480148948;
	setAttr -s 30 ".lv";
	setAttr ".am" -type "characterMapping" 30 "World_Root2_chSet|Spine_Ctrl|L_Pole_Ctrl.translateZ" 
		1 1 "World_Root2_chSet|Spine_Ctrl|L_Pole_Ctrl.translateY" 1 2 "World_Root2_chSet|Spine_Ctrl|L_Pole_Ctrl.translateX" 
		1 3 "World_Root2_chSet|Spine_Ctrl|R_Pole_Ctrl.translateZ" 1 4 "World_Root2_chSet|Spine_Ctrl|R_Pole_Ctrl.translateY" 
		1 5 "World_Root2_chSet|Spine_Ctrl|R_Pole_Ctrl.translateX" 1 6 "World_Root2_chSet|Spine_Ctrl|R_Wrist_Ctrl.translateZ" 
		1 7 "World_Root2_chSet|Spine_Ctrl|R_Wrist_Ctrl.translateY" 1 8 "World_Root2_chSet|Spine_Ctrl|R_Wrist_Ctrl.translateX" 
		1 9 "World_Root2_chSet|Spine_Ctrl|L_Wrist_Ctrl.translateZ" 1 10 "World_Root2_chSet|Spine_Ctrl|L_Wrist_Ctrl.translateY" 
		1 11 "World_Root2_chSet|Spine_Ctrl|L_Wrist_Ctrl.translateX" 1 12 "World_Root2_chSet|Spine_Ctrl|L_Foot_MarkerAttr_Ctrl.translateZ" 
		1 13 "World_Root2_chSet|Spine_Ctrl|L_Foot_MarkerAttr_Ctrl.translateY" 1 
		14 "World_Root2_chSet|Spine_Ctrl|L_Foot_MarkerAttr_Ctrl.translateX" 1 15 "World_Root2_chSet|joint1|joint2_Ctrl.translateZ" 
		1 16 "World_Root2_chSet|joint1|joint2_Ctrl.translateY" 1 17 "World_Root2_chSet|joint1|joint2_Ctrl.translateX" 
		1 18 "World_Root2_chSet|joint4|joint5_AttrMarked.translateZ" 1 19 "World_Root2_chSet|joint4|joint5_AttrMarked.translateY" 
		1 20 "World_Root2_chSet|joint4|joint5_AttrMarked.translateX" 1 21 "pCube4_AttrMarked_Bingo.translateZ" 
		1 22 "pCube4_AttrMarked_Bingo.translateY" 1 23 "pCube4_AttrMarked_Bingo.translateX" 
		1 24 "World_Root2_chSet|Spine_Ctrl.translateZ" 1 25 "World_Root2_chSet|Spine_Ctrl.translateY" 
		1 26 "World_Root2_chSet|Spine_Ctrl.translateX" 1 27 "World_Root2_chSet|nurbsCircle1.translateZ" 
		1 28 "World_Root2_chSet|nurbsCircle1.translateY" 1 29 "World_Root2_chSet|nurbsCircle1.translateX" 
		1 30  ;
	setAttr ".aal" -type "attributeAlias" {"L_Wrist_Ctrl_translateZ","linearValues[10]"
		,"L_Wrist_Ctrl_translateY","linearValues[11]","L_Wrist_Ctrl_translateX","linearValues[12]"
		,"L_Foot_MarkerAttr_Ctrl_translateZ","linearValues[13]","L_Foot_MarkerAttr_Ctrl_translateY"
		,"linearValues[14]","L_Foot_MarkerAttr_Ctrl_translateX","linearValues[15]","joint2_Ctrl_translateZ"
		,"linearValues[16]","joint2_Ctrl_translateY","linearValues[17]","joint2_Ctrl_translateX"
		,"linearValues[18]","joint5_AttrMarked_translateZ","linearValues[19]","L_Pole_Ctrl_translateZ"
		,"linearValues[1]","joint5_AttrMarked_translateY","linearValues[20]","joint5_AttrMarked_translateX"
		,"linearValues[21]","pCube4_AttrMarked_Bingo_translateZ","linearValues[22]","pCube4_AttrMarked_Bingo_translateY"
		,"linearValues[23]","pCube4_AttrMarked_Bingo_translateX","linearValues[24]","Spine_Ctrl_translateZ"
		,"linearValues[25]","Spine_Ctrl_translateY","linearValues[26]","Spine_Ctrl_translateX"
		,"linearValues[27]","nurbsCircle1_translateZ","linearValues[28]","nurbsCircle1_translateY"
		,"linearValues[29]","L_Pole_Ctrl_translateY","linearValues[2]","nurbsCircle1_translateX"
		,"linearValues[30]","L_Pole_Ctrl_translateX","linearValues[3]","R_Pole_Ctrl_translateZ"
		,"linearValues[4]","R_Pole_Ctrl_translateY","linearValues[5]","R_Pole_Ctrl_translateX"
		,"linearValues[6]","R_Wrist_Ctrl_translateZ","linearValues[7]","R_Wrist_Ctrl_translateY"
		,"linearValues[8]","R_Wrist_Ctrl_translateX","linearValues[9]"} ;
createNode script -n "sceneReviewData";
	setAttr ".b" -type "string" "try:\r\timport Red9.core.Red9_Tools as r9Tools;\r\tr9Tools.SceneReviewerUI.show();\rexcept:\r\tpass";
	setAttr ".st" 1;
	setAttr ".stp" 1;
createNode blendShape -n "ffff";
	addAttr -ci true -h true -sn "aal" -ln "attributeAliasList" -dt "attributeAlias";
	setAttr -s 2 ".w[0:1]"  0 0;
	setAttr -s 2 ".it[0].itg";
	setAttr ".it[0].itg[0].iti[6000].ipt" -type "pointArray" 8 -0.65353929996490479
		 2.5209781527519226 0.22950732707977295 1 0.65353929996490479 2.5209781527519226 0.22950732707977295
		 1 -0.65353929996490479 1.6646788716316223 0.22950732707977295 1 0.65353929996490479
		 1.6646788716316223 0.22950732707977295 1 -0.65353929996490479 1.6646788716316223
		 -0.22950732707977295 1 0.65353929996490479 1.6646788716316223 -0.22950732707977295
		 1 -0.65353929996490479 2.5209781527519226 -0.22950732707977295 1 0.65353929996490479
		 2.5209781527519226 -0.22950732707977295 1 ;
	setAttr ".it[0].itg[0].iti[6000].ict" -type "componentList" 1 "vtx[0:7]";
	setAttr ".it[0].itg[1].iti[6000].ipt" -type "pointArray" 8 0.19809514284133911
		 -0.24309754371643066 -0.41051018238067627 1 -0.19809514284133911 -0.24309754371643066
		 -0.41051018238067627 1 0.19809514284133911 0.24309754371643066 -0.41051018238067627
		 1 -0.19809514284133911 0.24309754371643066 -0.41051018238067627 1 0.19809514284133911
		 0.24309754371643066 0.41051018238067627 1 -0.19809514284133911 0.24309754371643066
		 0.41051018238067627 1 0.19809514284133911 -0.24309754371643066 0.41051018238067627
		 1 -0.19809514284133911 -0.24309754371643066 0.41051018238067627 1 ;
	setAttr ".it[0].itg[1].iti[6000].ict" -type "componentList" 1 "vtx[0:7]";
	setAttr ".aal" -type "attributeAlias" {"pCube7","weight[0]","pCube6","weight[1]"
		} ;
createNode tweak -n "tweak1";
createNode objectSet -n "ffffSet";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "ffffGroupId";
	setAttr ".ihi" 0;
createNode groupParts -n "ffffGroupParts";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode objectSet -n "tweakSet1";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "groupId2";
	setAttr ".ihi" 0;
createNode groupParts -n "groupParts2";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode blendShape -n "NewBlend";
	addAttr -ci true -h true -sn "aal" -ln "attributeAliasList" -dt "attributeAlias";
	setAttr -s 2 ".w[0:1]"  0 0;
	setAttr -s 2 ".it[0].itg";
	setAttr ".it[0].itg[0].iti[6000].ipt" -type "pointArray" 8 0 -4.5868766903877258
		 0 1 0 -4.5868766903877258 0 1 0 -4.5868770480155945 0 1 0 -4.5868770480155945 0 1 0
		 -4.5868770480155945 0 1 0 -4.5868770480155945 0 1 0 -4.5868766903877258 0 1 0 -4.5868766903877258
		 0 1 ;
	setAttr ".it[0].itg[0].iti[6000].ict" -type "componentList" 1 "vtx[0:7]";
	setAttr ".it[0].itg[1].iti[6000].ipt" -type "pointArray" 8 0 6.0720793604850769
		 0 1 0 6.0720793604850769 0 1 0 6.0720790028572083 0 1 0 6.0720790028572083 0 1 0
		 6.0720790028572083 0 1 0 6.0720790028572083 0 1 0 6.0720793604850769 0 1 0 6.0720793604850769
		 0 1 ;
	setAttr ".it[0].itg[1].iti[6000].ict" -type "componentList" 1 "vtx[0:7]";
	setAttr ".aal" -type "attributeAlias" {"pCube8","weight[0]","pCube7","weight[1]"
		} ;
createNode tweak -n "tweak2";
createNode objectSet -n "NewBlendSet";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "NewBlendGroupId";
	setAttr ".ihi" 0;
createNode groupParts -n "NewBlendGroupParts";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
createNode objectSet -n "tweakSet2";
	setAttr ".ihi" 0;
	setAttr ".vo" yes;
createNode groupId -n "groupId4";
	setAttr ".ihi" 0;
createNode groupParts -n "groupParts4";
	setAttr ".ihi" 0;
	setAttr ".ic" -type "componentList" 1 "vtx[*]";
select -ne :time1;
	addAttr -ci true -sn "sceneReport" -ln "sceneReport" -dt "string";
	setAttr ".o" 1;
	setAttr ".unw" 1;
	setAttr ".sceneReport" -type "string" "{\"date\": \"Sun Nov 25 20:41:21 2012\", \"comment\": \"UnitTest support file:\\n======================\\nThis is designed to run the Red9_CoreUtilTests.py\\ntests that validate the r9Core.FilterNode() class\", \"history\": \"\", \"author\": \"Red\"}";
select -ne :renderPartition;
	setAttr -s 2 ".st";
select -ne :initialShadingGroup;
	setAttr -s 13 ".dsm";
	setAttr ".ro" yes;
select -ne :initialParticleSE;
	setAttr ".ro" yes;
select -ne :defaultShaderList1;
	setAttr -s 2 ".s";
select -ne :lightList1;
	setAttr -s 6 ".l";
select -ne :postProcessList1;
	setAttr -s 2 ".p";
select -ne :defaultRenderingList1;
select -ne :renderGlobalsList1;
select -ne :defaultLightSet;
	setAttr -s 6 ".dsm";
select -ne :hardwareRenderGlobals;
	setAttr ".ctrs" 256;
	setAttr ".btrs" 512;
select -ne :defaultHardwareRenderGlobals;
	setAttr ".fn" -type "string" "im";
	setAttr ".res" -type "string" "ntsc_4d 646 485 1.333";
select -ne :characterPartition;
select -ne :ikSystem;
connectAttr "|World_Root|joint1.s" "|World_Root|joint1|joint2_Ctrl.is";
connectAttr "|World_Root|joint1|joint2_Ctrl.s" "|World_Root|joint1|joint2_Ctrl|joint3_AttrMarked.is"
		;
connectAttr "|World_Root|joint1|joint2_Ctrl|joint3_AttrMarked.tx" "|World_Root|joint1|joint2_Ctrl|effector1.tx"
		;
connectAttr "|World_Root|joint1|joint2_Ctrl|joint3_AttrMarked.ty" "|World_Root|joint1|joint2_Ctrl|effector1.ty"
		;
connectAttr "|World_Root|joint1|joint2_Ctrl|joint3_AttrMarked.tz" "|World_Root|joint1|joint2_Ctrl|effector1.tz"
		;
connectAttr "|World_Root|joint4.s" "|World_Root|joint4|joint5_AttrMarked.is";
connectAttr "|World_Root|joint4|joint5_AttrMarked.s" "|World_Root|joint4|joint5_AttrMarked|joint6_Ctrl.is"
		;
connectAttr "|World_Root|joint4|joint5_AttrMarked|joint6_Ctrl.s" "|World_Root|joint4|joint5_AttrMarked|joint6_Ctrl|joint7_AttrMarked.is"
		;
connectAttr "|World_Root|joint4|joint5_AttrMarked|joint6_Ctrl|joint7_AttrMarked.s" "|World_Root|joint4|joint5_AttrMarked|joint6_Ctrl|joint7_AttrMarked|joint8.is"
		;
connectAttr "|World_Root|joint4|joint5_AttrMarked|joint6_Ctrl|joint7_AttrMarked|joint8.s" "|World_Root|joint4|joint5_AttrMarked|joint6_Ctrl|joint7_AttrMarked|joint8|joint9.is"
		;
connectAttr "makeNurbCircle1.oc" "|World_Root|nurbsCircle1|nurbsCircleShape1.cr"
		;
connectAttr "ffff.og[0]" "|World_Root|Spine_Ctrl|R_Wrist_Ctrl|R_Pole_AttrMarked_Ctrl|pCube1|pCubeShape1.i"
		;
connectAttr "ffffGroupId.id" "|World_Root|Spine_Ctrl|R_Wrist_Ctrl|R_Pole_AttrMarked_Ctrl|pCube1|pCubeShape1.iog.og[0].gid"
		;
connectAttr "ffffSet.mwc" "|World_Root|Spine_Ctrl|R_Wrist_Ctrl|R_Pole_AttrMarked_Ctrl|pCube1|pCubeShape1.iog.og[0].gco"
		;
connectAttr "groupId2.id" "|World_Root|Spine_Ctrl|R_Wrist_Ctrl|R_Pole_AttrMarked_Ctrl|pCube1|pCubeShape1.iog.og[1].gid"
		;
connectAttr "tweakSet1.mwc" "|World_Root|Spine_Ctrl|R_Wrist_Ctrl|R_Pole_AttrMarked_Ctrl|pCube1|pCubeShape1.iog.og[1].gco"
		;
connectAttr "tweak1.vl[0].vt[0]" "|World_Root|Spine_Ctrl|R_Wrist_Ctrl|R_Pole_AttrMarked_Ctrl|pCube1|pCubeShape1.twl"
		;
connectAttr "polyCube1.out" "pCubeShape1Orig.i";
connectAttr "makeNurbSphere1.os" "|World_Root|nurbsSphere1|nurbsSphereShape1.cr"
		;
connectAttr "|World_Root|joint1.msg" "|World_Root|IK_Ctrl|ikHandle1.hsj";
connectAttr "|World_Root|joint1|joint2_Ctrl|effector1.hp" "|World_Root|IK_Ctrl|ikHandle1.hee"
		;
connectAttr "ikRPsolver.msg" "|World_Root|IK_Ctrl|ikHandle1.hsv";
connectAttr "|World_Root2_chSet|joint1.s" "|World_Root2_chSet|joint1|joint2_Ctrl.is"
		;
connectAttr "TestChSet.lv[16]" "|World_Root2_chSet|joint1|joint2_Ctrl.tz";
connectAttr "TestChSet.lv[17]" "|World_Root2_chSet|joint1|joint2_Ctrl.ty";
connectAttr "TestChSet.lv[18]" "|World_Root2_chSet|joint1|joint2_Ctrl.tx";
connectAttr "|World_Root2_chSet|joint1|joint2_Ctrl.s" "|World_Root2_chSet|joint1|joint2_Ctrl|joint3_AttrMarked.is"
		;
connectAttr "|World_Root2_chSet|joint4.s" "|World_Root2_chSet|joint4|joint5_AttrMarked.is"
		;
connectAttr "TestChSet.lv[19]" "|World_Root2_chSet|joint4|joint5_AttrMarked.tz";
connectAttr "TestChSet.lv[20]" "|World_Root2_chSet|joint4|joint5_AttrMarked.ty";
connectAttr "TestChSet.lv[21]" "|World_Root2_chSet|joint4|joint5_AttrMarked.tx";
connectAttr "|World_Root2_chSet|joint4|joint5_AttrMarked.s" "|World_Root2_chSet|joint4|joint5_AttrMarked|joint6_Ctrl.is"
		;
connectAttr "|World_Root2_chSet|joint4|joint5_AttrMarked|joint6_Ctrl.s" "|World_Root2_chSet|joint4|joint5_AttrMarked|joint6_Ctrl|joint7_AttrMarked.is"
		;
connectAttr "|World_Root2_chSet|joint4|joint5_AttrMarked|joint6_Ctrl|joint7_AttrMarked.s" "|World_Root2_chSet|joint4|joint5_AttrMarked|joint6_Ctrl|joint7_AttrMarked|joint8.is"
		;
connectAttr "|World_Root2_chSet|joint4|joint5_AttrMarked|joint6_Ctrl|joint7_AttrMarked|joint8.s" "|World_Root2_chSet|joint4|joint5_AttrMarked|joint6_Ctrl|joint7_AttrMarked|joint8|joint9.is"
		;
connectAttr "TestChSet.lv[28]" "|World_Root2_chSet|nurbsCircle1.tz";
connectAttr "TestChSet.lv[29]" "|World_Root2_chSet|nurbsCircle1.ty";
connectAttr "TestChSet.lv[30]" "|World_Root2_chSet|nurbsCircle1.tx";
connectAttr "TestChSet.lv[25]" "|World_Root2_chSet|Spine_Ctrl.tz";
connectAttr "TestChSet.lv[26]" "|World_Root2_chSet|Spine_Ctrl.ty";
connectAttr "TestChSet.lv[27]" "|World_Root2_chSet|Spine_Ctrl.tx";
connectAttr "TestChSet.lv[13]" "|World_Root2_chSet|Spine_Ctrl|L_Foot_MarkerAttr_Ctrl.tz"
		;
connectAttr "TestChSet.lv[14]" "|World_Root2_chSet|Spine_Ctrl|L_Foot_MarkerAttr_Ctrl.ty"
		;
connectAttr "TestChSet.lv[15]" "|World_Root2_chSet|Spine_Ctrl|L_Foot_MarkerAttr_Ctrl.tx"
		;
connectAttr "TestChSet.lv[10]" "|World_Root2_chSet|Spine_Ctrl|L_Wrist_Ctrl.tz";
connectAttr "TestChSet.lv[11]" "|World_Root2_chSet|Spine_Ctrl|L_Wrist_Ctrl.ty";
connectAttr "TestChSet.lv[12]" "|World_Root2_chSet|Spine_Ctrl|L_Wrist_Ctrl.tx";
connectAttr "TestChSet.lv[7]" "|World_Root2_chSet|Spine_Ctrl|R_Wrist_Ctrl.tz";
connectAttr "TestChSet.lv[8]" "|World_Root2_chSet|Spine_Ctrl|R_Wrist_Ctrl.ty";
connectAttr "TestChSet.lv[9]" "|World_Root2_chSet|Spine_Ctrl|R_Wrist_Ctrl.tx";
connectAttr "TestChSet.lv[4]" "|World_Root2_chSet|Spine_Ctrl|R_Pole_Ctrl.tz";
connectAttr "TestChSet.lv[5]" "|World_Root2_chSet|Spine_Ctrl|R_Pole_Ctrl.ty";
connectAttr "TestChSet.lv[6]" "|World_Root2_chSet|Spine_Ctrl|R_Pole_Ctrl.tx";
connectAttr "TestChSet.lv[1]" "|World_Root2_chSet|Spine_Ctrl|L_Pole_Ctrl.tz";
connectAttr "TestChSet.lv[2]" "|World_Root2_chSet|Spine_Ctrl|L_Pole_Ctrl.ty";
connectAttr "TestChSet.lv[3]" "|World_Root2_chSet|Spine_Ctrl|L_Pole_Ctrl.tx";
connectAttr "NewBlend.og[0]" "pCubeShape6.i";
connectAttr "NewBlendGroupId.id" "pCubeShape6.iog.og[2].gid";
connectAttr "NewBlendSet.mwc" "pCubeShape6.iog.og[2].gco";
connectAttr "groupId4.id" "pCubeShape6.iog.og[3].gid";
connectAttr "tweakSet2.mwc" "pCubeShape6.iog.og[3].gco";
connectAttr "tweak2.vl[0].vt[0]" "pCubeShape6.twl";
connectAttr "TestChSet.lv[22]" "pCube4_AttrMarked_Bingo.tz";
connectAttr "TestChSet.lv[23]" "pCube4_AttrMarked_Bingo.ty";
connectAttr "TestChSet.lv[24]" "pCube4_AttrMarked_Bingo.tx";
relationship "link" ":lightLinker1" ":initialShadingGroup.message" ":defaultLightSet.message";
relationship "link" ":lightLinker1" ":initialParticleSE.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" ":initialShadingGroup.message" ":defaultLightSet.message";
relationship "shadowLink" ":lightLinker1" ":initialParticleSE.message" ":defaultLightSet.message";
connectAttr "layerManager.dli[0]" "defaultLayer.id";
connectAttr "renderLayerManager.rlmi[0]" "defaultRenderLayer.rlid";
connectAttr "|World_Root2_chSet|Spine_Ctrl|L_Pole_Ctrl.tz" "TestChSet.dnsm[0]";
connectAttr "|World_Root2_chSet|Spine_Ctrl|L_Pole_Ctrl.ty" "TestChSet.dnsm[1]";
connectAttr "|World_Root2_chSet|Spine_Ctrl|L_Pole_Ctrl.tx" "TestChSet.dnsm[2]";
connectAttr "|World_Root2_chSet|Spine_Ctrl|R_Pole_Ctrl.tz" "TestChSet.dnsm[3]";
connectAttr "|World_Root2_chSet|Spine_Ctrl|R_Pole_Ctrl.ty" "TestChSet.dnsm[4]";
connectAttr "|World_Root2_chSet|Spine_Ctrl|R_Pole_Ctrl.tx" "TestChSet.dnsm[5]";
connectAttr "|World_Root2_chSet|Spine_Ctrl|R_Wrist_Ctrl.tz" "TestChSet.dnsm[6]";
connectAttr "|World_Root2_chSet|Spine_Ctrl|R_Wrist_Ctrl.ty" "TestChSet.dnsm[7]";
connectAttr "|World_Root2_chSet|Spine_Ctrl|R_Wrist_Ctrl.tx" "TestChSet.dnsm[8]";
connectAttr "|World_Root2_chSet|Spine_Ctrl|L_Wrist_Ctrl.tz" "TestChSet.dnsm[9]";
connectAttr "|World_Root2_chSet|Spine_Ctrl|L_Wrist_Ctrl.ty" "TestChSet.dnsm[10]"
		;
connectAttr "|World_Root2_chSet|Spine_Ctrl|L_Wrist_Ctrl.tx" "TestChSet.dnsm[11]"
		;
connectAttr "|World_Root2_chSet|Spine_Ctrl|L_Foot_MarkerAttr_Ctrl.tz" "TestChSet.dnsm[12]"
		;
connectAttr "|World_Root2_chSet|Spine_Ctrl|L_Foot_MarkerAttr_Ctrl.ty" "TestChSet.dnsm[13]"
		;
connectAttr "|World_Root2_chSet|Spine_Ctrl|L_Foot_MarkerAttr_Ctrl.tx" "TestChSet.dnsm[14]"
		;
connectAttr "|World_Root2_chSet|joint1|joint2_Ctrl.tz" "TestChSet.dnsm[15]";
connectAttr "|World_Root2_chSet|joint1|joint2_Ctrl.ty" "TestChSet.dnsm[16]";
connectAttr "|World_Root2_chSet|joint1|joint2_Ctrl.tx" "TestChSet.dnsm[17]";
connectAttr "|World_Root2_chSet|joint4|joint5_AttrMarked.tz" "TestChSet.dnsm[18]"
		;
connectAttr "|World_Root2_chSet|joint4|joint5_AttrMarked.ty" "TestChSet.dnsm[19]"
		;
connectAttr "|World_Root2_chSet|joint4|joint5_AttrMarked.tx" "TestChSet.dnsm[20]"
		;
connectAttr "pCube4_AttrMarked_Bingo.tz" "TestChSet.dnsm[21]";
connectAttr "pCube4_AttrMarked_Bingo.ty" "TestChSet.dnsm[22]";
connectAttr "pCube4_AttrMarked_Bingo.tx" "TestChSet.dnsm[23]";
connectAttr "|World_Root2_chSet|Spine_Ctrl.tz" "TestChSet.dnsm[24]";
connectAttr "|World_Root2_chSet|Spine_Ctrl.ty" "TestChSet.dnsm[25]";
connectAttr "|World_Root2_chSet|Spine_Ctrl.tx" "TestChSet.dnsm[26]";
connectAttr "|World_Root2_chSet|nurbsCircle1.tz" "TestChSet.dnsm[27]";
connectAttr "|World_Root2_chSet|nurbsCircle1.ty" "TestChSet.dnsm[28]";
connectAttr "|World_Root2_chSet|nurbsCircle1.tx" "TestChSet.dnsm[29]";
connectAttr "ffffGroupParts.og" "ffff.ip[0].ig";
connectAttr "ffffGroupId.id" "ffff.ip[0].gi";
connectAttr "groupParts2.og" "tweak1.ip[0].ig";
connectAttr "groupId2.id" "tweak1.ip[0].gi";
connectAttr "ffffGroupId.msg" "ffffSet.gn" -na;
connectAttr "|World_Root|Spine_Ctrl|R_Wrist_Ctrl|R_Pole_AttrMarked_Ctrl|pCube1|pCubeShape1.iog.og[0]" "ffffSet.dsm"
		 -na;
connectAttr "ffff.msg" "ffffSet.ub[0]";
connectAttr "tweak1.og[0]" "ffffGroupParts.ig";
connectAttr "ffffGroupId.id" "ffffGroupParts.gi";
connectAttr "groupId2.msg" "tweakSet1.gn" -na;
connectAttr "|World_Root|Spine_Ctrl|R_Wrist_Ctrl|R_Pole_AttrMarked_Ctrl|pCube1|pCubeShape1.iog.og[1]" "tweakSet1.dsm"
		 -na;
connectAttr "tweak1.msg" "tweakSet1.ub[0]";
connectAttr "pCubeShape1Orig.w" "groupParts2.ig";
connectAttr "groupId2.id" "groupParts2.gi";
connectAttr "NewBlendGroupParts.og" "NewBlend.ip[0].ig";
connectAttr "NewBlendGroupId.id" "NewBlend.ip[0].gi";
connectAttr "groupParts4.og" "tweak2.ip[0].ig";
connectAttr "groupId4.id" "tweak2.ip[0].gi";
connectAttr "NewBlendGroupId.msg" "NewBlendSet.gn" -na;
connectAttr "pCubeShape6.iog.og[2]" "NewBlendSet.dsm" -na;
connectAttr "NewBlend.msg" "NewBlendSet.ub[0]";
connectAttr "tweak2.og[0]" "NewBlendGroupParts.ig";
connectAttr "NewBlendGroupId.id" "NewBlendGroupParts.gi";
connectAttr "groupId4.msg" "tweakSet2.gn" -na;
connectAttr "pCubeShape6.iog.og[3]" "tweakSet2.dsm" -na;
connectAttr "tweak2.msg" "tweakSet2.ub[0]";
connectAttr "pCubeShape6Orig.w" "groupParts4.ig";
connectAttr "groupId4.id" "groupParts4.gi";
connectAttr "|World_Root|nurbsSphere1|nurbsSphereShape1.iog" ":initialShadingGroup.dsm"
		 -na;
connectAttr "|World_Root|Spine_Ctrl|R_Wrist_Ctrl|R_Pole_AttrMarked_Ctrl|pCube1|pCubeShape1.iog" ":initialShadingGroup.dsm"
		 -na;
connectAttr "|World_Root|Spine_Ctrl|L_Foot_MarkerAttr_Ctrl|pCube2|pCubeShape2.iog" ":initialShadingGroup.dsm"
		 -na;
connectAttr "|World_Root|joint4|joint5_AttrMarked|joint6_Ctrl|pCube3|pCubeShape3.iog" ":initialShadingGroup.dsm"
		 -na;
connectAttr "pCube4_AttrMarkedShape.iog" ":initialShadingGroup.dsm" -na;
connectAttr "|World_Root|pCube4_AttrMarked|pCube5|pCubeShape5.iog" ":initialShadingGroup.dsm"
		 -na;
connectAttr "|World_Root2_chSet|joint4|joint5_AttrMarked|joint6_Ctrl|pCube3|pCubeShape3.iog" ":initialShadingGroup.dsm"
		 -na;
connectAttr "|World_Root2_chSet|Spine_Ctrl|L_Foot_MarkerAttr_Ctrl|pCube2|pCubeShape2.iog" ":initialShadingGroup.dsm"
		 -na;
connectAttr "|World_Root2_chSet|Spine_Ctrl|R_Wrist_Ctrl|R_Pole_AttrMarked_Ctrl|pCube1|pCubeShape1.iog" ":initialShadingGroup.dsm"
		 -na;
connectAttr "|World_Root2_chSet|nurbsSphere1|nurbsSphereShape1.iog" ":initialShadingGroup.dsm"
		 -na;
connectAttr "pCube4_AttrMarked_BingoShape.iog" ":initialShadingGroup.dsm" -na;
connectAttr "|World_Root2_chSet|pCube4_AttrMarked_Bingo|pCube5|pCubeShape5.iog" ":initialShadingGroup.dsm"
		 -na;
connectAttr "pCubeShape6.iog" ":initialShadingGroup.dsm" -na;
connectAttr "|World_Root|pointLight1|pointLightShape1.ltd" ":lightList1.l" -na;
connectAttr "|World_Root|pointLight2|pointLightShape2.ltd" ":lightList1.l" -na;
connectAttr "pointLightShape3.ltd" ":lightList1.l" -na;
connectAttr "pointLightShape4.ltd" ":lightList1.l" -na;
connectAttr "|World_Root2_chSet|pointLight1|pointLightShape1.ltd" ":lightList1.l"
		 -na;
connectAttr "|World_Root2_chSet|pointLight2|pointLightShape2.ltd" ":lightList1.l"
		 -na;
connectAttr "defaultRenderLayer.msg" ":defaultRenderingList1.r" -na;
connectAttr "|World_Root|pointLight1.iog" ":defaultLightSet.dsm" -na;
connectAttr "|World_Root|pointLight2.iog" ":defaultLightSet.dsm" -na;
connectAttr "pointLight3.iog" ":defaultLightSet.dsm" -na;
connectAttr "pointLight4.iog" ":defaultLightSet.dsm" -na;
connectAttr "|World_Root2_chSet|pointLight1.iog" ":defaultLightSet.dsm" -na;
connectAttr "|World_Root2_chSet|pointLight2.iog" ":defaultLightSet.dsm" -na;
connectAttr "TestChSet.pa" ":characterPartition.st" -na;
connectAttr "ikRPsolver.msg" ":ikSystem.sol" -na;
// End of FilterNode_baseTests.ma
