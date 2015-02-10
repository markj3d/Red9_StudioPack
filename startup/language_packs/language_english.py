# -*- coding: utf-8 -*-

'''
This is the main text language mapper for English, all other languages
should inherit from these to make sure that none of the entries are 
missed off!
'''

class Generic(object):
    
    contactme = 'Contact Me'
    tools = 'Tools'
    reset = 'Reset to Default'
    vimeo_menu = 'VimeoHelp'
    vimeo_help = "Open Vimeo Help File"
    
    hierarchy = 'Hierarchy'
    hierarchy_ann = 'Process Hierarchy'
    apply = 'Apply'
    set = 'set'
    clear_all = 'ClearAll'
    clear = 'Clear'
    attrs = 'attrs'
    transX = 'Translate X'
    transY = 'Translate Y'
    transZ = 'Translate Z'
    rotX = 'Rotate X'
    rotY = 'Rotate X'
    rotZ = 'Rotate X'
    tx = 'Tx'
    ty = 'Ty'
    tz = 'Tz'
    translates = 'Translates'
    rx = 'Rx'
    ry = 'Ry'
    rz = 'Rz'
    rotates = 'Rotates'
    sx = 'Sx'
    sy = 'Sy'
    sz = 'Sz'
    scales = 'Scales'
    vis = 'Vis'
    nurbs_curve = 'NurbsCurve'
    meshes = 'Meshes'
    joints = 'Joints'
    locators = 'Locators'
    cameras = 'Cameras'
    audio ='Audio'
    orient_constraint = 'OrientConstraint'
    point_constraint ='PointConstraint'
    parent_constraint = 'ParentConstraint'
    ik_handles = 'IKHandles'
    transforms = 'Transforms'
    right = 'Right'
    left = 'Left'
    centre = 'Centre'


# ======================================================================================
# CoreUtils Module
# ======================================================================================

    
class LockChannelsUI(object):
    title = 'LockChannels'
    user_defined = 'All User Defined Attrs'
    user_defined_ann='These are non-standard attributes added to the nodes. These are considered per node'
    all_attrs = 'ALL Attrs'
    specific_attrs = 'Specific Attrs'
    specific_attrs_ann = 'list of specific attributes to lock, comma separated: note : RMB Menu'
    add_chnbox_selection = 'Add ChnBox Selection'
    lock = 'Lock'
    unlock = 'unLock'
    hide = 'Hide'
    unhide = 'unHide'
    store_attrmap = 'Store attrMap'
    store_attrmap_ann = 'This saves the current "lock,keyable,hidden" status of all attributes in the channelBox to an attrMap file'
    load_attrmap = 'Load from attrMap'
    load_attrmap_ann = 'This restores the "lock,keyable,hidden" status of all attributes from the attrMap file'
    serialize_attrmap_to_node = 'Serialized attrMap to node'
    serialize_attrmap_to_node_ann = 'rather than saving the data to a file, serialize it to a given node so its stored internally in your systems'
    set_ann = 'Node for serializing the attrMap directly onto'

class SearchNodeUI(object):
    '''
    Main node Search UI, this is inherited by the AnimUI as they share the same filter options
    '''
    title = "Node Searcher"
    complex_node_search = 'Complex Node Search'
    complex_node_search_ann = 'nodeTypeSelectors'
    
    search_nodetypes = 'Specific NodeTypes'
    search_nodetypes_ann = 'Specific NodeTypes to look for - separated by ,'
    search_attributes = 'Search Attributes'
    search_attributes_ann = 'Search for specific Attributes on nodes, list separated by ","'
    search_pattern = 'Search Name Pattern'
    search_pattern_ann='Search for specific nodeName Patterns, list separated by "," - Note this is a Python.regularExpression - ^ clamps to the start, $ clamps to the end'
    
    from_selected = 'From Selected'
    from_selected_ann = 'Process Selected Hierarchies or all Scene Nodes'
    return_transforms = 'Return Transforms were applicable'
    return_transforms_ann='Clamp the filter to only return the Transform Nodes, by-passes any shapes or nodeTypes with Transforms as parents'
    include_roots = 'Include Roots'
    include_roots_ann = 'Include the originalRoots in the selection'
    intersection_search = 'Intersection Search - All Above Fields'
    simple_hierarchy ='Simple Hierarchy'
    

# ======================================================================================
# AnimationUtils Module
# ======================================================================================

class AnimationUI(SearchNodeUI):
    title = 'Red9 AnimationTools'
    tab_animlayout = 'Animation_Toolkit'
    tab_poselayout = 'PoseManager'
    tab_filterlayout = 'Hierarchy_Control'
    
    vimeo_walkthrough = 'Open Vimeo > WalkThrough v1.27'
    vimeo_update = 'Open Vimeo > Update v1.40'
    vimeo_hierarchy_control = 'Open Vimeo > HierarchyControl'
    vimeo_track_stab = 'Open Vimeo > Track or Stabilize'
    vimeo_copykeys = 'Open Vimeo > CopyKeys & TimeOffsets'
    vimeo_mirrorsetup = 'Open Vimeo > MirrorSetups'
    vimeo_posesaver_advanced = 'Open Vimeo > PoseSaver - Advanced Topics'
    vimeo_posesaver_blending = 'Open Vimeo > PoseSaver - Blending and maintain spaces'
    
    # Tab1 AnimFunctions =================================================================
    
    cbox_attrs = 'ChBox Attrs'
    copy_to_many = 'CopyToMany'
    timerange= 'TimeRange'
    cbox_attrs_ann = 'Copy only those channels selected in the channelBox'
    step = 'Step'
    
    copy_attrs_hierarchy_ann='Copy Attributes Hierarchy : Filter Hierarchies for transforms & joints then Match NodeNames'
    copy_attrs = 'Copy Attributes'
    copy_attrs_ann = '''CopyAttributes : Modes: -------------------
Default > Selected Object Pairs (Obj2 to Obj1), (Obj3 to Obj4)
Hierarchy > Uses Selection Filters on Hierarchy Tab
CopyToMany > Copy data from First selected to all Subsequent nodes
Note: This also handles CharacterSets and SelectionSets if selected, processing all members'''
    copy_attrs_to_many_ann = 'Copy Matching Attributes from First selected to all Subsequently selected nodes'
    
    copy_keys_hierarchy_ann = 'Copy Keys Hierarchy : Filter Hierarchies for transforms & joints then Match NodeNames'
    copy_keys = 'Copy Keys'
    copy_keys_ann = '''CopyKeys : Modes: -------------------------
Default > Selected Object Pairs (Obj2 to Obj1), (Obj3 to Obj4)
Hierarchy > Uses Selection Filters on Hierarchy Tab
CopyToMany > Copy data from First selected to all Subsequent nodes
Note: This also handles CharacterSets and SelectionSets if selected, processing all members'''
    copy_keys_to_many_ann = 'Copy Animation from First selected to all Subsequently selected nodes'
    copy_keys_timerange_ann = 'ONLY Copy Keys over PlaybackTimeRange or Selected TimeRange (highlighted in Red on the timeline)'
    copy_keys_merge_layers= 'MergeLayers'
    copy_keys_merge_layers_ann = 'If AnimLayers are found pre-compile the anim and copy the resulting data'
    paste_method_ann = 'Paste Method Used: Default = "replace", paste method used by the copy code internally'
    
    snaptransforms = 'Snap Transforms'
    snaptransforms_ann = '''Snap Selected Object Pairs (Obj2 to Obj1), (Obj4 to Obj3) or Snap Filtered Hierarchies\nNote: This also handles CharacterSets if selected, processing all members'''
    snaptransforms_timerange_ann = 'Process over PlaybackTimeRange or Selected TimeRange (in Red on the timeline)'
    snaptransforms_hierarchy_ann = 'Filter Hierarchies with given args - then Snap Transforms for matched nodes'
    trans = 'Trans'
    trans_ann = 'Track the Translation data'
    rots = 'Rots'
    rots_ann = 'Track the Rotation data'
    frmstep = 'FrmStep'
    frmstep_ann = 'Frames to advance the timeline after each Process Run'
    pre_copyattrs = 'PreCopyAttrs'
    pre_copyattrs_ann = 'Copy all Values for all channels prior to running the Snap'
    pre_copykeys = 'PreCopyKeys'
    pre_copykeys_ann = 'Copy all animation data for all channels prior to running the Snap over Time'
    iteration = 'Iteration'
    iteration_ann = 'This is the number of iterations over each hierarchy node during processing, if you get issues during snap then increase this'
    
    step = 'Step'
    step_ann = 'Frames to advance the timeline between Processing - accepts negative values'
    tracknstabilize = 'Track or Stabilize'
    track_process_back = '<< Process Back <<'
    track_process_ann = '''Stabilize Mode : Select a SINGLE Object - this will stabilize it in place over time
Track Object Mode : Select TWO Objects - first is source, second will track with offset
Track Component Mode :  Select a Component (poly,vert,edge) then an Object - second will track the component with offset'''
    track_process_forward = '>>  Process Fwd  >>'
    
    timeoffset = 'TimeOffset'
    offset = 'Offset'
    offset_ann = 'If processing at Scene Level then this will offset all appropriate: AnimCurves,Sound and Clips. If processing on selected it will deal with each node type as it finds'
    offset_hierarchy_ann = 'Offset Hierarchy'
    offset_fullscene = 'FullScene'
    offset_fullscene_ann = 'ON:Scene Level Processing: OFF:SelectedNode Processing - Offsets Animation, Sound and Clip data as appropriate'
    offset_timelines = 'OffsetTimelines'
    offset_timelines_ann = 'Offset the current playback timeranges'
    offset_timerange_ann = 'Offset nodes by range : PlaybackTimeRange or Selected TimeRange (in Red on the timeline)'
    offset_flocking = 'Flocking'
    offset_flocking_ann = 'Offset Selected Nodes by incremental amounts'
    offset_randomizer = 'Randomizer'
    offset_randomizer_ann = 'Randomize the offsets using the offset field as the max such that offsets are random(0,offset)'
    offset_ripple = 'RippleEdits'
    offset_ripple_ann = 'Ripple the edits to the upper bounds, keys, clips, audio etc will get pushed'
    offset_frms_ann = 'Frames to offset the data by'
    
    mirror_hierarchy_ann = 'Mirror Hierarchy, or Mirror Selected nodes if they have the Mirror Marker data'
    mirror_controls = 'Mirror Controls'
    mirror_animation = 'Mirror Animation'
    mirror_animation_ann = 'Mirror the Animation - NOTE Layers and Trax are NOT supported yet'
    mirror_pose = 'Mirror Pose'
    mirror_pose_ann = 'Mirror the Current Pose'
    symmetry_animation = 'Symmetry Animation'
    symmetry_animation_ann = 'Symmetry the Animation : L >> R - NOTE Layers and Trax are NOT supported yet'
    symmetry_pose = 'Symmetry Pose'
    symmetry_pose_ann = 'Symmetry the Current Pose : L >> R'
    
    
    # Tab2 Hierarchy =================================================================
    
    hierarchy_descriptor = '''Filter Settings : A Hierarchy search pattern
used by all the Hierarchy checkboxes on the main tabs
Particularly relevant for complex Animation Rigs
as it allows you to pin-point required controllers.\n
Note that if these are all blank then hierarchy
checkBoxes will process all children of the roots'''
                
    metarig = 'MetaRig'
    metarig_ann = 'Switch to MetaRig Sub Systems'
    specific_nodetypes_ann = 'RMB QuickSelector for Common Types : Search for "Specific NodeTypes" in the hierarchy, list separated by ","'
    
    nodetype_transform = 'nodeType : Transform'
    nodetype_nurbs_curves = 'nodeType : NurbsCurves'
    nodetype_nurbs_surfaces = 'nodeType : NurbsSurfaces'
    nodetype_joints = 'nodeType : Joints'
    nodetype_locators = 'nodeType : Locators'
    nodetype_meshes = 'nodeType : Meshes'
    nodetype_cameras = 'nodeType : Cameras'
    nodetype_hikeff = 'nodeType : hikIKEffector'
    nodetype_blendshape = 'nodeType : blendShape'
   
    priorities_clear = 'Clear Process Priorities'
    priorities_set = 'Set Priorities from Selected'
    priorities_append = 'Append Priorities from Selected'
    priorities_remove = 'Remove selected from list'
    priorities_use_snap = 'Use Priority as SnapList'
    move_up = 'Move Up'
    move_down = 'Move Down'
    
    presets_available = 'Available Presets:'
    presets_delete = 'DeletePreset'
    presets_opendir = 'OpenPresetDir'
    
    match_method = 'MatchMethod'
    match_method_ann = 'Method used to match nodes in different hierarchies, default="stripPrefix"'
    match_base = 'base'
    match_base_ann ='Exact shortName matching of nodes only, ignores namespaces : Fred:MainCtrl == Bert:MainCtrl'
    match_stripprefix = 'stripPrefix'
    match_stripprefix_ann = 'Allows one hierarchy to be prefixed when matching, ignores namespaces : Fred:New_MainCtrl == Bert:MainCtrl'
    match_index = 'index'
    match_index_ann = 'No matching logic at all, just matched in the order the nodes were found in the hierarchies'
    match_mirror = 'mirrorIndex'
    match_mirror_ann = 'Match nodes via their internal r9MirrorIndexes if found'
    
    filter_test = 'Test Filter'
    filter_test_ann = 'Test the Hierarchy Filter on the selected root node'
    filter_store = 'Store New Filter'
    filter_store_ann = 'Store this filterSetting Object'
        
    
    #Tab3 PoseSaver  ==================================================================================
    
    pose_path = 'PosePath'
    pose_local = 'Local Poses'
    pose_local_ann = 'local mode gives you full control to save,delete and load the library'
    pose_project = 'Project Poses'
    pose_project_ann = 'Project mode disables all but the load functionality of the library'
    pose_subfolders = 'SubFolders'
    pose_subfolders_ann = 'PosePath SubFolders'
    pose_clear = 'Clear'
    pose_clear_ann = 'Load Pose data for the given Hierarchy or Selections'
    search_filter = 'searchFilter : '
    search_filter_ann = 'Filter the folder, allows multiple filters separated by ","'
    sortby_name = 'sortBy Name'
    sortby_date = 'sortBy Date'
    pose_load = 'Load Pose'
    pose_load_ann = 'Load Pose data for the given Hierarchy or Selections'
    pose_save = 'Save Pose'
    pose_save_ann = 'Save Pose data for the given Hierarchy or Selections'
    pose_hierarchy_ann = "Hierarchy: if OFF during Load then the pose will load to the selected nodes IF they're in the pose file"
    pose_set_root = 'SetRootNode'
    pose_set_root_ann = 'Hierarchy Root Node for the Pose'
    pose_relative = 'RelativePose'
    pose_maintain_parents = 'Maintain ParentSpaces'
    
    pose_rel_rotmethod = 'Rotate Method'
    pose_rel_tranmethod = 'Translate Method'
    pose_rel_methods = 'Relative Offset Methods'
    pose_rel_projected = 'projected'
    pose_rel_absolute = 'absolute'
    
    pose_pp = 'Pose Point Cloud'
    pose_pp_make = 'Make PPC'
    pose_pp_make_ann = 'Make a Pose Point Cloud - have to use hierarchy for this! - optional second selected node is a reference mesh'
    pose_pp_delete = 'Delete PPC'
    pose_pp_delete_ann = 'Delete the current Pose Point Cloud'
    pose_pp_snap = 'Snap Pose'
    pose_pp_snap_ann='Snap the RIG to the PPC pose'
    pose_pp_update = 'Update PPC'
    pose_pp_update_ann = 'Update the PPC to the RIGS current pose'


    # POSE RMB Popup =============================================================

    pose_rmb_blender = 'PoseBlender'
    pose_rmb_delete = 'Delete Pose'
    pose_rmb_rename = 'Rename Pose'
    pose_rmb_selectinternal = 'Select IntenalPose Objects'
    pose_rmb_update_pose = 'Update : Pose Only'
    pose_rmb_update_pose_thumb = 'Update : Pose and Thumb'
    pose_rmb_update_thumb = 'Update : Thumb Only'
    pose_rmb_add_subfolder = 'Add Subfolder'
    pose_rmb_refresh = 'Refresh List'
    pose_rmb_openfile ='Open Pose File'
    pose_rmb_opendir = 'Open Pose Directory'
    pose_rmb_compare = 'Pro : PoseCompare'
    pose_rmb_compare_skel = 'Pro : Compare against - [skeletonData]'
    pose_rmb_compare_posedata = 'Pro : Compare against - [poseData]'
    pose_rmb_copyhandler = 'Pro : Copy poseHandler.py to folder'
    pose_rmb_copypose = 'Copy Pose >> Project Poses'
    pose_rmb_switchmode = 'Switch Pose Mode - Thumb/Text'
    pose_rmb_grid_small = 'Grid Size: Small'
    pose_rmb_grid_med = 'Grid Size: Medium'
    pose_rmb_grid_large = 'Grid Size: Large'
    
class Mirror_Setup(object):
    title = "MirrorSetup"
    side = 'MirrorSide:'
    index = 'MirrorIndex:'
    axis = 'MirrorAxis:'
    default_axis = 'Use Default Axis'
    no_inverse = 'No Inversing'
    no_inverse_ann = 'Set the marker so that data is copied over but NO inversing is done on the data, straight copy from left to right'

    refresh = 'Refresh from Selected'
    add_update = 'Add / Update Mirror Markers'
    add_update_ann = 'add mirrorMarkers - NOTE if multiple selected then the index will increment from the given value'
    print_debugs = 'Print Mirror Debugs'
    print_debugs_ann = 'print out the hierarchies current setup in the scriptEditor'
    delete = 'Delete from Selected'
    clear = 'clear all Existing'
    save_configs = 'Save MirrorConfigs'
    save_configs_ann = 'Save the current MirrorSetups'
    load_configs = 'Load MirrorConfigs'
    
class CameraTracker(object):
    title = 'CameraTracker'
    tracker_step = 'TrackerStep: '
    frames = 'frames'
    maintain_frame = 'MaintainCurrentFraming'
    pan = 'Pan'
    track = 'Track'
    