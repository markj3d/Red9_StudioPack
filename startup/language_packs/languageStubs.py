
contactme = 'Contact Me'
tools = 'Tools'
reset = 'Reset to Default'

class AnimationUI(object):
    
    vimeo_walkthrough = u'Open Vimeo > WalkThrough v1.27'
    vimeo_update = u'Open Vimeo > Update v1.40'
    vimeo_hierarchy_control = u'Open Vimeo > HierarchyControl'
    vimeo_track_stab = u'Open Vimeo > Track or Stabilize'
    vimeo_copykeys = u'Open Vimeo > CopyKeys & TimeOffsets'
    vimeo_mirrorsetup = u'Open Vimeo > MirrorSetups'
    vimeo_posesaver_advanced = u'Open Vimeo > PoseSaver - Advanced Topics'
    vimeo_posesaver_blending = u'Open Vimeo > PoseSaver - Blending and maintain spaces'
    
    
    # Tab1 =================================================================
    
    hierarchy = 'Hierarchy'
    timerange= 'TimeRange'
    cbox_attrs = 'ChBox Attrs'
    copy_to_many = 'CopyToMany'
    copy_attrs = 'Copy Attributes'
    copy_keys = 'Copy Keys'
    merge_layers= 'MergeLayers'
    
    snaptransforms = 'Snap Transforms'
    trans = 'Trans'
    rots = 'Rots'
    frmstep = 'FrmStep'
    pre_copyattrs = 'PreCopyAttrs'
    pre_copykeys = 'PreCopyKeys'
    iteration = 'Iteration'
    step = 'Step'
    tracknstabilize = 'Track or Stabilize'
    
    process_back = '<< Process Back <<'
    process_forward = '>>  Process Fwd  >>'
    timeoffset = 'TimeOffset'
    fullscene = 'FullScene'
    offset = 'Offset'
    offset_timelines = 'OffsetTimelines'
    flocking = 'Flocking'
    randomizer = 'Randomizer'
    ripple_edits = 'RippleEdits'
    
    mirror_controls = 'Mirror Controls'
    mirror_animation = 'Mirror Animation'
    mirror_pose = 'Mirror Pose'
    symmetry_animation = 'Symmetry Animation'
    symmetry_pose = 'Symmetry Pose'
    
    
    # Tab2 =================================================================
    
    hierarchy_descriptor = '''Filter Settings : A Hierarchy search pattern
used by all the Hierarchy checkboxes on the main tabs
Particularly relevant for complex Animation Rigs
as it allows you to pin-point required controllers.\n
Note that if these are all blank then hierarchy
checkBoxes will process all children of the roots'''
                
    metarig = 'MetaRig'
    specific_nodetypes = 'Specific NodeTypes'
    
    clear_all = 'ClearAll'
    nodetype_transform = 'nodeType : Transform'
    nodetype_nurbs_curves = 'nodeType : NurbsCurves'
    nodetype_nurbs_surfaces = 'nodeType : NurbsSurfaces'
    nodetype_joints = 'nodeType : Joints'
    nodetype_locators = 'nodeType : Locators'
    nodetype_meshes = 'nodeType : Meshes'
    nodetype_cameras = 'nodeType : Cameras'
    nodetype_hikeff = 'nodeType : hikIKEffector'
    nodetype_blendshape = 'nodeType : blendShape'
    search_attributes = 'Search Attributes'
    search_name_pattern = 'Search Name Pattern'
    
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
    include_roots = 'Include Roots'
    
    match_method = 'MatchMethod'
    match_base = 'base'
    match_stripprefix = 'stripPrefix'
    match_index = 'index'
    match_mirror = 'mirrorIndex'
    
    filter_test = 'Test Filter'
    filter_store = 'Store New Filter'
        
    
    #Tab 3 ==================================================================================
    
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


    # POP RMB Popup =============================================================

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
    
    
    