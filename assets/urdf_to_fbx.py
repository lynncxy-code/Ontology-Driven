"""
GR1T2 URDF → Blender Armature + Skinned Meshes → FBX
Run via: blender --background --python urdf_to_fbx.py

Each STL link is rigidly skinned (100% weight) to its corresponding bone.
This produces a valid UE Skeletal Mesh FBX.
"""

import bpy
import xml.etree.ElementTree as ET
import os
from mathutils import Matrix, Vector, Euler

# ── Paths ─────────────────────────────────────────────────────────────────────
URDF_PATH  = r"C:\Users\ADMIN\Downloads\Wiki-GRx-Models-master\Wiki-GRx-Models-master\GR1_legacy\GR1\GR1T2\urdf\GR1T2.urdf"
MESH_DIR   = r"C:\Users\ADMIN\Downloads\Wiki-GRx-Models-master\Wiki-GRx-Models-master\GR1_legacy\GR1\GR1T2\meshes"
OUTPUT_FBX = r"D:\tmp\digital_twin_aircraft\assets\usd_cache\gr1t2\GR1T2_skinned.fbx"

# ── Parse URDF ─────────────────────────────────────────────────────────────────
def parse_vec(s, default=(0, 0, 0)):
    if not s: return default
    v = [float(x) for x in s.strip().split()]
    return tuple(v) if len(v) == 3 else default

tree = ET.parse(URDF_PATH)
root = tree.getroot()

# link → stl basename
link_mesh = {}
for link in root.findall("link"):
    name = link.get("name")
    vis = link.find("visual")
    if vis is None: continue
    geo = vis.find("geometry")
    if geo is None: continue
    m = geo.find("mesh")
    if m is None: continue
    link_mesh[name] = os.path.basename(m.get("filename", "").replace("\\", "/"))

# child → (parent, xyz, rpy)
joint_info = {}
for j in root.findall("joint"):
    parent = j.find("parent").get("link")
    child  = j.find("child").get("link")
    origin = j.find("origin")
    xyz = parse_vec(origin.get("xyz") if origin is not None else None)
    rpy = parse_vec(origin.get("rpy") if origin is not None else None)
    joint_info[child] = (parent, xyz, rpy)

all_links = [l.get("name") for l in root.findall("link")]

def world_matrix(link_name):
    """Cumulative world transform (meters) for a link."""
    if link_name not in joint_info:
        return Matrix.Identity(4)
    parent, xyz, rpy = joint_info[link_name]
    parent_mat = world_matrix(parent)
    loc = Matrix.Translation(Vector(xyz))
    rot = Euler(rpy, 'XYZ').to_matrix().to_4x4()
    return parent_mat @ loc @ rot

# ── Clean scene ───────────────────────────────────────────────────────────────
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ── Create armature ───────────────────────────────────────────────────────────
arm_data = bpy.data.armatures.new("GR1T2_Armature")
arm_obj  = bpy.data.objects.new("GR1T2", arm_data)
scene.collection.objects.link(arm_obj)
bpy.context.view_layer.objects.active = arm_obj

bpy.ops.object.mode_set(mode='EDIT')
eb = arm_data.edit_bones
BONE_LEN = 0.04

bone_heads = {}
for link_name in all_links:
    b = eb.new(link_name)
    head = world_matrix(link_name).to_translation()
    b.head = head
    b.tail = head + Vector((0, 0, BONE_LEN))
    bone_heads[link_name] = head

# Parent bones
for link_name in all_links:
    if link_name in joint_info:
        parent_link = joint_info[link_name][0]
        if parent_link in eb:
            eb[link_name].parent = eb[parent_link]

bpy.ops.object.mode_set(mode='OBJECT')

# ── Import STL meshes, skin each to its bone ──────────────────────────────────
all_mesh_objs = []

for link_name, stl_basename in link_mesh.items():
    stl_path = os.path.join(MESH_DIR, stl_basename)
    if not os.path.exists(stl_path):
        print(f"[WARN] Missing STL: {stl_path}")
        continue

    # Deselect all, then import
    bpy.ops.object.select_all(action='DESELECT')
    try:
        bpy.ops.wm.stl_import(filepath=stl_path)
    except AttributeError:
        bpy.ops.import_mesh.stl(filepath=stl_path)

    mesh_obj = bpy.context.selected_objects[0]
    mesh_obj.name = f"mesh_{link_name}"   # 加前缀避免与骨骼名冲突

    # Place mesh at link's world origin (STL is in link-local frame)
    mesh_obj.matrix_world = world_matrix(link_name)

    # ── Rigid skinning: vertex group = bone name, weight = 1.0 ──
    vg = mesh_obj.vertex_groups.new(name=link_name)  # 顶点组名仍用骨骼名
    vg.add(list(range(len(mesh_obj.data.vertices))), 1.0, 'REPLACE')

    # Add armature modifier
    mod = mesh_obj.modifiers.new(name="Armature", type='ARMATURE')
    mod.object = arm_obj
    mod.use_vertex_groups = True

    # Parent to armature object (not to bone — modifier handles deformation)
    mesh_obj.parent = arm_obj
    mesh_obj.parent_type = 'OBJECT'
    mesh_obj.matrix_parent_inverse = arm_obj.matrix_world.inverted()

    all_mesh_objs.append(mesh_obj)

print(f"[INFO] Imported {len(all_mesh_objs)} mesh links")

# ── Export FBX ────────────────────────────────────────────────────────────────
os.makedirs(os.path.dirname(OUTPUT_FBX), exist_ok=True)

# Select armature + all meshes
bpy.ops.object.select_all(action='DESELECT')
arm_obj.select_set(True)
for obj in all_mesh_objs:
    obj.select_set(True)
bpy.context.view_layer.objects.active = arm_obj

bpy.ops.export_scene.fbx(
    filepath=OUTPUT_FBX,
    use_selection=True,
    global_scale=100.0,           # meters → cm for UE
    apply_unit_scale=True,
    apply_scale_options='FBX_SCALE_ALL',
    bake_space_transform=True,
    object_types={'ARMATURE', 'MESH'},
    use_mesh_modifiers=True,
    add_leaf_bones=False,
    primary_bone_axis='Y',
    secondary_bone_axis='X',
    axis_forward='-Z',
    axis_up='Y',
    path_mode='COPY',
)

print(f"[DONE] Skinned FBX → {OUTPUT_FBX}")
