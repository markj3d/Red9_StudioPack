# -*- coding: utf-8 -*-

'''
This is the main text language mapper for English, all other languages
should inherit from these to make sure that none of the entries are 
missed off!
'''

class _MainMenus_(object):

    animation_toolkit = "AnimationToolkit"
    animation_toolkit_ann = 'Main Red9 Animation Toolkit - Note: CTRL+click opens this non-docked'
    simple_snap = 'Simple Snap'
    simple_snap_ann = 'Simple Snap transforms'
    searchui = 'SearchUI'
    searchui_ann = 'Main Red9 Search toolkit'
    lockchannels = 'LockChannels'
    lockchannels_ann = "Manage Channel States"
    metanodeui = "MetaNodeUI"
    metanodeui_ann = "MetaNode Scene Searcher"
    scene_reviewer = "Scene Reviewer"
    scene_reviewer_ann = "Launch the Scene Review Reporter"
    mouse_mocap = "MouseMoCap"
    mouse_mocap_ann = "Record the Mouse Input to selected object"
    randomize_keyframes = "Randomize Keyframes"
    randomize_keyframes_ann = "Randomize selected Keys - also available in the GraphEditor>curve menu"
    interactive_curve_filter = "Interactive Curve Filter"
    interactive_curve_filter_ann = "Interactive Curve Filter - also available in the GraphEditor>curve menu"
    mirror_setup = "MirrorSetup"
    mirror_setup_ann = "Temp UI to help setup the Mirror Markers on a rig"
    camera_tracker = 'CameraTracker'
    camera_tracker_pan = "CameraTracker > panning"
    camera_tracker_pan_ann = "Panning Camera : CameraTrack the current view with the current camera"
    tracker_tighness_ann = "setup the tracker step and tightness"
    camera_tracker_track = "CameraTracker > tracking"
    camera_tracker_track_ann = "Tracking Camera : CameraTrack the current view with the current camera"
    animation_binder = "Animation Binder"
    animation_binder_ann = "Siggraph Autodesk MasterClass 2011 - Toolset"

    red9_homepage = "Red9_HomePage"
    red9_homepage_ann = "Open Red9Consultancy HomePage"
    red9_blog = "Red9_News : Latest Tools!"
    red9_blog_ann = "Open Red9 News Feed"
    red9_vimeo = "Red9_Vimeo Channel"
    red9_vimeo_ann = "Open Red9Vimeo Channel"
    red9_facebook = "Red9_Facebook"
    red9_facebook_ann = "Open Red9Facebook page"
    red9_twitter = "Red9_Twitter"
    red9_twitter_ann = "Open Red9Twitter Feed"
    red9_api_docs = "Red9_API Docs"
    red9_api_docs_ann = "Open Red9 API code reference page"
    red9_details = "Red9_Details"
    red9_debugger = 'Red9 Debugger'
    reconnect_anim = "Reconnect Lost Anim"
    reconnect_anim_ann = "Reconnect lost animation data via a chSet - see my blog post for more details"
    open_last_crash = "Open last CrashFile"
    open_last_crash_ann = "Open the last Maya crash file from your temp dir"
    systems_debug = "systems: DEBUG"
    systems_debug_ann = "Turn all the logging to Debug"
    systems_info = "systems: INFO"
    systems_info_ann = "Turn all the logging to Info only"
    individual_debug = 'Individual DEBUG'
    individual_debug_ann = "Turn the individual modules logging to Debug only"
    individual_info = 'Individual INFO'
    individual_info_ann = "Turn the individual modules logging to Info only"
    debug = "Debug"
    info = 'Info'
    systems_reload = "systems: reload()"
    systems_reload_ann = "Force a complete reload on the core of Red9"
    language = "Language"

    # additional menu stubs
    open_in_explorer = "Red9: Open in Explorer"
    open_in_explorer_ann = "Open the folder containing the current Maya Scene"
    copy_to_clipboard = 'Red9: Copy to Clipboard'
    copy_to_clipboard_ann = 'Copy the current Maya filepath to the OS:Clipboard'
    open_r9anim = 'Red9 PRO: Import r9Anim Direct'
    open_r9anim_ann = 'Import an r9Anim file direct IF it has internal reference file pointers (mRig Only)'
    import_r9anim = 'Red9 PRO: Import r9Anim to Current mRig'
    import_r9anim_ann = 'Import an r9Anim file direct to the currently selected mRig (mRig Only)'

    # TimeSlider menu additions
    collapse_time = 'Red9: Collapse Time'
    collapse_time_ann = 'Collapse Time, cutting keys from a given range and rippling remaining keys. Also deals with clips, audio and supported MetaData'
    collapse_selected = 'Collapse : Selected Only'
    collapse_selected_ann = 'Collapse the keys in the selected TimeRange (Red highlighted)'
    collapse_full = 'Collapse : Full Scene'
    collapse_full_ann = 'Collapse the keys in the selected TimeRange (Red highlighted)'
    collapse_mrig = 'Collapse : Selected mRigs'
    collapse_mrig_ann = 'ONLY Applicable for Meta based mRig systems\nCollapse the keys in the selected TimeRange (Red highlighted)'

    insert_padding = 'Red9: Insert Padding'
    pad_selected = 'Pad : Selected Objects Only'
    pad_selected_ann = 'Insert time in the selected TimeRange (Red highlighted)'
    pad_full_scene = 'Pad : Full Scene'
    pad_full_scene_ann = 'Insert time in the selected TimeRange (Red highlighted)'
    pad_mrigs = 'Pad : Selected mRigs'
    pad_mrigs_ann = 'ONLY Applicable for Meta based mRig systems\nInsert time in the selected TimeRange (Red highlighted)'

    inverse_anim = 'Red9: Reverse Animation'
    inverse_selected = 'Reverse: Selected Objects Only'
    inverse_selected_ann = 'ONLY Applicable for Meta based mRig systems\nReverse the animation data over the selected timeRange'
    inverse_mrigs = 'Reverse: Selected mRigs'
    inverse_mrigs_ann = 'ONLY Applicable for Meta based mRig systems\nReverse the animation data over the selected timeRange for the entire mRig'

    range_submenu = 'Red9: Range'
    selectkeys_timerange = 'Keys : Select from Range'
    selectkeys_timerange_ann = 'Select all keys from the selected Objects within the given TimeRange or selected TimeRange(Red highlighted)'
    setrangetoo = 'Set Range to : Animated Bounds'
    setrangetoo_ann = 'Set the timerange to the bounds of all animation found on the selected objects, (first and last keys)'
    setrangetoo_internal = 'Set Range to : Animation No Statics'
    setrangetoo_internal_ann = 'Set the timerange to the extent of all animation found on the selected objects LESS STATIC KEYS at start and end of curves'

    # audio sub_menu
    sound_red9_sound = "Red9_Sound"
    sound_offset_manager = "Offset Manager"
    sound_offset_manager_ann = "offset / nudge multiple audio nodes in one go"
    sound_activate_selected_audio = "Activate Selected Audio"
    sound_activate_selected_audio_ann = "set the current selected audio node to be active in the timeline"
    sound_set_timeline_to_selected = "Set Timeline to Selected"
    sound_set_timeline_to_selected_ann = "set the timeline to the extents of the selected, or all audio nodes"
    sound_focus_on_selected = "Focus on Selected"
    sound_focus_on_selected_ann = "Runs the setActive then the setTimelines in one go for speed"
    sound_mute_selected = "Mute Selected"
    sound_unmute_selected = "UnMute Selected"
    sound_lock_selected = "Lock Selected"
    sound_lock_selected_ann = "Locks the time inputs for the selected audio nodes, stopping them being accidentally dragged in time"
    sound_unlock_selected = "UnLock Selected"
    sound_unlock_selected_ann = "UnLock the time inputs for the selected audio nodes, allowing them to be moved in time"
    sound_delete_selected = "Delete Selected Audio"
    sound_delete_selected_ann = "Mainly for Maya2013 where the delete of audio nodes was broken!"
    sound_combine_audio = "Combine Audio"
    sound_combine_audio_ann = "Combine either selected, or ALL wavs into a single audio track - perfect for playblasting multiple audios"
    sound_open_audio_path = "Open Audio Path"
    sound_open_audio_path_ann = "show the path in an OS Explorer"
    sound_format_soundnode_name = "Format SoundNode Names"
    sound_format_soundnode_name_ann = "rename the sound nodes to their respective short file name for consistency"
    sound_inspect_wav = "Inspect Wav Format"
    sound_inspect_wav_ann = "open up the inspector and show internal details about wav formats"


class _Generic_(object):
    '''
    Used by many of the UI's, general non-specific text
    '''
    contactme = 'Contact Me'
    tools = 'Tools'
    reset = 'Reset to Default'
    refresh = 'Refresh'
    vimeo_menu = 'VimeoHelp'
    vimeo_help = "Open Vimeo Help File"

    hierarchy = 'Hierarchy'
    hierarchy_ann = 'Process Hierarchy'
    name = 'Name'
    apply = 'Apply'
    cancel = 'Cancel'
    set = 'set'
    clear_all = 'ClearAll'
    clear = 'Clear'

    attrs = 'attrs'
    transX = 'Translate X'
    transY = 'Translate Y'
    transZ = 'Translate Z'
    rotX = 'Rotate X'
    rotY = 'Rotate Y'
    rotZ = 'Rotate Z'
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
    audio = 'Audio'
    orient_constraint = 'OrientConstraint'
    point_constraint = 'PointConstraint'
    parent_constraint = 'ParentConstraint'
    ik_handles = 'IKHandles'
    transforms = 'Transforms'

    right = 'Right'
    left = 'Left'
    centre = 'Centre'

    debug = 'Debug'
    yes = 'Yes'
    no = 'No'
    min = 'Min'
    max = 'Max'



# ======================================================================================
# CoreUtils.py Module ---
# ======================================================================================


class _LockChannelsUI_(object):
    title = 'LockChannels'
    user_defined = 'All User Defined Attrs'
    user_defined_ann = 'These are non-standard attributes added to the nodes. These are considered per node'
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

class _SearchNodeUI_(object):
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
    search_pattern_ann = 'Search for specific nodeName Patterns, list separated by "," - Note this is a Python.regularExpression - ^ clamps to the start, $ clamps to the end'

    from_selected = 'From Selected'
    from_selected_ann = 'Process Selected Hierarchies or all Scene Nodes'
    return_transforms = 'Return Transforms were applicable'
    return_transforms_ann = 'Clamp the filter to only return the Transform Nodes, by-passes any shapes or nodeTypes with Transforms as parents'
    include_roots = 'Include Roots'
    include_roots_ann = 'Include the originalRoots in the selection'
    intersection_search = 'Intersection Search - All Above Fields'
    simple_hierarchy = 'Simple Hierarchy'


# ======================================================================================
# AnimationUtils.py Module ---
# ======================================================================================

class _AnimationUI_(_SearchNodeUI_):
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
    timerange = 'TimeRange'
    cbox_attrs_ann = 'Copy only those channels selected in the channelBox'
    step = 'Step'

    copy_attrs_hierarchy_ann = 'Copy Attributes Hierarchy : Filter Hierarchies for transforms & joints then Match NodeNames'
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
    copy_keys_merge_layers = 'MergeLayers'
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
    offsetby = 'Offset By'
    offset = 'Offset'
    offset_ann = 'If processing at Scene Level then this will offset all appropriate: AnimCurves,Sound and Clips. If processing on selected it will deal with each node type as it finds'
    offset_start = 'Offset Start Frame To'
    offset_start_ann = 'If processing at Scene Level then this will offset all appropriate: AnimCurves,Sound and Clips. If processing on selected it will deal with each node type as it finds'

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
    offset_startfrm = 'To Start At'
    offset_startfrm_ann = 'Switches the offset mode such that the offset passed in is the new start frame for the range, moving the animation accordingly'


    mirror_hierarchy_ann = 'Mirror Hierarchy, or Mirror Selected nodes if they have the Mirror Marker data'
    mirror_controls = 'Mirror Controls'
    mirror_animation = 'Mirror Animation'
    mirror_animation_ann = 'Mirror the Animation - NOTE Layers and Trax are NOT supported yet'
    mirror_pose = 'Mirror Pose'
    mirror_pose_ann = 'Mirror the Current Pose'
    symmetry_animation = 'Symmetry Anim'
    symmetry_animation_ann = 'Symmetry the Animation : NOTE Layers and Trax are NOT supported yet'
    symmetry_pose = 'Symmetry Pose'
    symmetry_pose_ann = 'Symmetry the Current Pose'


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
    match_base_ann = 'Exact shortName matching of nodes only, ignores namespaces : Fred:MainCtrl == Bert:MainCtrl'
    match_stripprefix = 'stripPrefix'
    match_stripprefix_ann = 'Allows one hierarchy to be prefixed when matching, ignores namespaces : Fred:New_MainCtrl == Bert:MainCtrl'
    match_index = 'index'
    match_index_ann = 'No matching logic at all, just matched in the order the nodes were found in the hierarchies'
    match_mirror = 'mirrorIndex'
    match_mirror_ann = 'Match nodes via their internal r9MirrorIndexes if found'
    match_metadata = 'metaData'
    match_metadata_ann = 'Match nodes based on their wiring in the MetaData framework'

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
    search_filter_ann = 'Filter the folder, allows multiple filters separated by "," spaces can be used as wildcards as well as ".*"'
    sortby_name = 'sortBy Name'
    sortby_date = 'sortBy Date'
    pose_load = 'Load Pose'
    pose_load_ann = 'Load Pose data for the given Hierarchy or Selections'
    pose_save = 'Save Pose'
    pose_save_ann = 'Save Pose data for the given Hierarchy or Selections'
    pose_blend = 'Blend Pose'
    pose_blend_ann = 'blend the selected pose with the current objects transforms'
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
    pose_pp_snap_ann = 'Snap the RIG to the PPC pose'
    pose_pp_update = 'Update PPC'
    pose_pp_update_ann = 'Update the PPC to the RIGS current pose'

    pose_blend_select_members = 'Select Members'
    pose_blend_key_members = 'Key Members'
    
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
    pose_rmb_openfile = 'Open Pose File'
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

class _Mirror_Setup_(object):

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
    clear = 'Clear all Existing'
    save_configs = 'Save MirrorConfigs'
    save_configs_ann = 'Save the current MirrorSetups'
    load_configs = 'Load MirrorConfigs'
    custom_axis = 'Custom Axis:'
    custom_axis_ann = ' add custom attributes to include in the axis calculations, this is a comma separated string of attributes'
    grab_channel_box = 'Grab selected attrs from ChannelBox'
    channelbox = 'ChnBox'

class _CameraTracker_(object):

    title = 'CameraTracker'
    tracker_step = 'TrackerStep: '
    frames = 'frames'
    maintain_frame = 'MaintainCurrentFraming'
    pan = 'Pan'
    track = 'Track'

class _CurveFilters_(object):

    title = 'interactiveCurveFilter'
    vimeo_randomize_ann = 'simple demo showing the functionality of Simplify curve and Randomizer'
    curve_resampler = 'Curve Resampler'
    resample = 'Resample'
    curve_simplifier = 'Curve Simplfier'
    time_tolerance = 'Time tolerance'
    value_tolerance = 'Value tolerance'
    snap_to_frame = "Snap to Frame"
    snap_to_frame_ann = "on exit of the sliders snap the keys to whole frames"
    delete_redundants = 'Delete Redundants'
    delete_redundants_ann = 'on selected nodes delete redundant animCurves - these are curves whos value never change, the curve will be deleted'
    single_process = 'Single Process'
    single_process_ann = 'Single process using the value sliders above'
    reset_all = 'Reset All'
    toggle_buffers = 'ToggleBuffers'

class _Randomizer_(object):

    title = 'KeyRandomizer'
    vimeo_randomizer_ann = 'simple demo showing the functionality of Simplify curve and Randomizer'
    strength_value = 'strength : value'
    frame_step = 'frameStep'
    current_keys_only = 'Current Keys Only'
    current_keys_only_ann = 'ONLY randomize selected keys, if OFF the core will add keys to the curve at the frameStep incremenet'
    pre_normalize = 'Pre-Normalize Curves'
    pre_normalize_ann = 'Pre-Normalize: process based on value percentage range auto-calculated from curves'
    interactive_mode = "Interactive Mode"
    interactive_mode_ann = "Turn on the interactiveMode - ONLY supported in CurrentKeys mode"
    save_pref = 'SavePref'
    toggle_buffers = 'ToggleBuffers'



# ======================================================================================
# Meta.py Module ---
# ======================================================================================


class _MetaNodeUI_(object):

    vimeo_dev_part1 = "Vimeo Help: Develop Conference MetaData-Part1"
    vimeo_dev_part1_ann = 'Develop Conference 2014 - MetaData in a Production Pipeline Video1'
    vimeo_dev_part2 = "Vimeo Help: Develop Conference MetaData-Part2"
    vimeo_dev_part2_ann = 'Develop Conference 2014 - MetaData in a Production Pipeline Video2'
    vimeo_dev_part3 = "Vimeo Help: Develop Conference MetaData-Part3"
    vimeo_dev_part3_ann = 'Develop Conference 2014 - MetaData in a Production Pipeline Video3'
    vimeo_meta_part1 = "Vimeo Help: MetaData-Part1"
    vimeo_meta_part1_ann = 'Part1 goes through the main attribute handling inside Meta'
    vimeo_meta_part2 = "Vimeo Help: MetaData-Part2"
    vimeo_meta_part2_ann = 'Part2 goes through the class structures and the basic factory aspect of Meta'
    vimeo_meta_part3 = "Vimeo Help: MetaData-Part3"
    vimeo_meta_part3_ann = 'Part3 shows how to add metaRig to your systems, all the connectChild and addRigCtrl calls'
    vimeo_meta_part4 = "Vimeo Help: MetaData-Part4"
    vimeo_meta_part4_ann = 'Part4 goes through subclassing Meta and using it in your own systems'

    print_registered_nodetypes = "Print :Registered NodeTypes"
    print_registered_nodetypes_ann = 'Prints the currently registered nodeTypes from the Meta Registry'
    print_registered_metaclasses = "Print :Registered MetaClasses"
    print_registered_metaclasses_ann = 'Prints the currently registered MetaClasses from the Meta Registry'
    print_metacached_node = "Print :MetaCached Nodes"
    print_metacached_nodes_ann = 'Prints all currently cached nodes in the MetaCache'
    clear_cache = "Clear Cache"
    clear_cache_ann = 'Clear all currently cached nodes from the registry'
    update_to_uuids = "Upgrade mNodes to UUIDs"
    update_to_uuids_ann = 'Upgrades any current mNodes in the scene to the new UIID system for caching'

    mtypes_filter = 'mTypes filter : '
    minstances_filter = 'mInstances filter : '
    registered_metaclasses_ann = 'Registered MetaCalsses to use as filters'
    all = 'all'
    valids = 'valids'
    invalids = 'inValids'
    unregistered = 'unRegistered'

    ui_launch_mtypes = 'UI launch with filter MetaNodes: mTypes'
    ui_launch_minstances = 'UI launch with filter MetaNodes: mInstances'

    graph_selected = 'Graph Selected Networks'
    select_children = 'Select Children'
    select_children_ann = 'NOTE doubleClick on the UI also runs the selectChildren call"'
    delete_selected = 'Delete Selected mNodes'
    delete_selected_ann = 'call self.delete() on the selected nModes'
    rename_mNode = 'Rename Node'
    rename_mNode_ann = 'Rename Selected mNode'
    sort_by_classname = 'SortBy : ClassName'
    sort_by_nodename = 'SortBy : NodeName'
    class_all_registered = 'Class : All Registered'
    class_print_inheritance = 'Class : Print Inheritance Map'
    pro_connect_node = 'Pro: Connect Node to System'
    pro_disconnect_node = 'Pro: Disconnect Nodes from System'
    pro_addchild_metanode = 'Pro: Add Child MetaNode System'
    filter_by_name = 'filter by name : '
    shortname = 'shortname'
    stripnamespace = 'strip_Nspace'

    # confirms and other messages
    confirm_delete = 'Confirm metaNode Delete',
    confirm_delete_message = 'Confirm deletion of metaNode\nare you absolutely\n\nSURE\n\nyou meant to do this?'


# ======================================================================================
# Tools.py Module ---
# ======================================================================================

class _SceneReviewerUI_(object):

    title = 'SceneReviewTracker'
    author = 'Author'
    date = 'Date'
    scene_name = 'SceneName'
    comment = 'Comment'
    new_comment = 'New Comment'
    history = 'History'
    activate_live_review = 'Activate Live Review'
    disable_live_review = 'Disable Live Review'

