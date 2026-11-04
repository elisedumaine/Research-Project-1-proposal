"""Build the kit's rock generator HDA (lpk_rock) in the open Houdini.

Run from the kit folder, after build_style.py:
    python Tools/houdini.py -f scripts/build_rock.py

How a rock is made:
  1. A round ball is stretched into the rock type's proportions (pebble,
     boulder, flat slab, tall cliff piece) and turned to a random angle.
  2. A soft noise gives it big lumps.
  3. "Chisel" cuts: a few random flat planes slice it, like a sculptor's
     chisel, which gives the big flat faces of a low-poly rock.  The bottom
     is cut flat so it sits on the ground.
  4. PolyReduce brings it down to a small number of faces (Detail).
  5. Cluster copies the rock a few times, big and small, around one spot.
  6. Faces that look up can turn into moss; lpk_style paints and flattens.
Units are meters; the rock sits on y = 0.
"""
import os
import sys

import hou

KIT = os.path.join(os.path.expanduser("~"), "Documents", "Low-Poly-Nature-Kit").replace("\\", "/")
sys.path.insert(0, KIT + "/scripts")
import build_style  # noqa: E402

HDA_PATH = KIT + "/hda/lpk_rock.hda"
TYPES = ("Pebble", "Boulder", "Slab", "Cliff", "Cluster")

SHAPE_VEX = r"""
// Stretch the unit ball into the rock type's proportions, with a seeded variation.
int seed = chi("../seed");
int type = chi("../type");          // 0 pebble, 1 boulder, 2 slab, 3 cliff, 4 cluster (boulders)
vector prop = {1.0, 0.75, 0.9};
if (type == 0) prop = {1.0, 0.55, 0.8};
if (type == 2) prop = {1.0, 0.22, 0.85};
if (type == 3) prop = {0.5, 1.6, 0.42};
vector vary = set(fit01(rand(seed * 1.31 + 0.1), 0.85, 1.15),
                  fit01(rand(seed * 2.17 + 0.2), 0.85, 1.15) * chf("../tallness"),
                  fit01(rand(seed * 3.73 + 0.3), 0.85, 1.15));
@P *= prop * vary;
float yaw = rand(seed * 5.11 + 0.4) * 2.0 * PI;
@P = qrotate(quaternion(yaw, {0, 1, 0}), @P);
"""

CHISEL_VEX = r"""
// Random flat cuts: every point beyond a plane is pushed back onto it.
int seed = chi("../seed");
int cuts = chi("../chisel");
float depth = chf("../cut_depth");
vector c = getbbox_center(0);
vector size = getbbox_size(0);
vector p = (@P - c) / (size * 0.5);   // rock space, about -1..1
for (int i = 0; i < cuts; i++) {
    vector n = normalize(sample_direction_uniform(set(rand(set(seed, i, 1.0)), rand(set(seed, i, 2.0)))));
    float d = fit01(rand(set(seed, i, 3.0)), 1.0 - depth, 0.97);
    float over = dot(p, n) - d;
    if (over > 0) p -= over * n;
}
// Flat base, so the rock sits on the ground.
p.y = max(p.y, -0.7);
@P = c + p * size * 0.5;
"""

CLUSTER_VEX = r"""
// One big rock and a few smaller ones around it.
int seed = chi("../seed");
int count = chi("../cluster_count");
for (int i = 0; i < count; i++) {
    float a = i * 2.39996 + rand(set(seed, i, 1.0));
    float r = i == 0 ? 0.0 : fit01(rand(set(seed, i, 2.0)), 0.9, 1.5);
    float s = i == 0 ? 1.0 : fit01(rand(set(seed, i, 3.0)), 0.3, 0.6);
    int pt = addpoint(0, set(cos(a) * r, 0, sin(a) * r));
    setpointattrib(0, "pscale", pt, s);
    setpointattrib(0, "orient", pt, quaternion(rand(set(seed, i, 4.0)) * 2.0 * PI, {0, 1, 0}));
    setpointattrib(0, "clump", pt, i);
}
"""

PARTS_VEX = r"""
// Everything is rock; faces that look up turn into moss (part "grass").
s@part = "rock";
i@piece = i@clump;
float moss = chf("../moss");
vector n = prim_normal(0, @primnum, {0.5, 0.5});
float threshold = fit(moss, 0.0, 1.0, 1.01, 0.3);
float wobble = (rand(set(@primnum, chi("../seed"), 5.0)) - 0.5) * 0.25;
if (moss > 0.0 && n.y + wobble > threshold) s@part = "grass";
"""


def build():
    work = hou.node("/obj").createNode("geo", "lpk_rock_build")
    subnet = work.createNode("subnet", "lpk_rock")

    ball = subnet.createNode("sphere", "ball")
    ball.parm("type").set("polymesh")
    ball.parm("rows").set(24)
    ball.parm("cols").set(48)
    shape = subnet.createNode("attribwrangle", "proportions")
    shape.setInput(0, ball)
    shape.parm("class").set("point")
    shape.parm("snippet").set(SHAPE_VEX)
    lumps = subnet.createNode("mountain::2.0", "lumps")
    lumps.setInput(0, shape)
    lumps.parm("height").setExpression('ch("../roughness") * 0.5')
    lumps.parm("elementsize").set(1.4)
    lumps.parm("offsetx").setExpression('ch("../seed") * 13.37')
    lumps.parm("offsety").setExpression('ch("../seed") * 7.11')
    chisel = subnet.createNode("attribwrangle", "chisel")
    chisel.setInput(0, lumps)
    chisel.parm("class").set("point")
    chisel.parm("snippet").set(CHISEL_VEX)

    reduce = subnet.createNode("polyreduce::2.0", "facets")
    reduce.setInput(0, chisel)
    reduce.parm("target").set("poly_count")
    reduce.parm("finalcount").setExpression('pow(2, ch("../detail")) * 12 + 24')

    points = subnet.createNode("attribwrangle", "cluster_points")
    points.parm("class").set("detail")
    points.parm("snippet").set(CLUSTER_VEX)
    copy = subnet.createNode("copytopoints::2.0", "cluster")
    copy.setInput(0, reduce)
    copy.setInput(1, points)
    copy.parm("targetattribs").set(1)
    copy.parm("applyto1").set(2)
    copy.parm("applymethod1").set(0)
    copy.parm("applyattribs1").set("clump")
    switch = subnet.createNode("switch", "single_or_cluster")
    switch.setInput(0, reduce)
    switch.setInput(1, copy)
    switch.parm("input").setExpression('ch("../type") == 4')

    size = subnet.createNode("xform", "size")
    size.setInput(0, switch)
    # Each type has its own natural size; Size scales it.
    size.parm("scale").setExpression(
        'ch("../size") * if(ch("../type") == 0, 0.3, if(ch("../type") == 3, 2.5, 1.0))')
    ground = subnet.createNode("xform", "ground")
    ground.setInput(0, size)
    ground.parm("ty").setExpression('-$YMIN - ($YMAX - $YMIN) * 0.06')
    parts = subnet.createNode("attribwrangle", "parts")
    parts.setInput(0, ground)
    parts.parm("class").set("primitive")
    parts.parm("snippet").set(PARTS_VEX)
    clean = subnet.createNode("attribdelete", "clean")
    clean.setInput(0, parts)
    clean.parm("primdel").set("clump")
    clean.parm("ptdel").set("N")

    style = subnet.createNode("lpk_style", "style")
    style.setInput(0, clean)
    for name in ("seed", "palette", "bark_tone", "jitter"):
        style.parm(name).setExpression('ch("../%s")' % name)
    out = subnet.createNode("output", "out")
    out.setInput(0, style)
    out.setDisplayFlag(True)
    subnet.layoutChildren()

    asset = subnet.createDigitalAsset(name="lpk_rock", hda_file_name=HDA_PATH, description="LPK Rock",
                                      min_num_inputs=0, max_num_inputs=0)
    definition = asset.type().definition()
    group = definition.parmTemplateGroup()
    shape_folder = hou.FolderParmTemplate("shape_folder", "Rock", folder_type=hou.folderType.Simple)
    for template in (
        hou.IntParmTemplate("seed", "Seed", 1, default_value=(1,), min=0, max=1000),
        hou.MenuParmTemplate("type", "Type", menu_items=[str(i) for i in range(len(TYPES))],
                             menu_labels=TYPES, default_value=1),
        hou.FloatParmTemplate("size", "Size", 1, default_value=(1.0,), min=0.1, max=5.0),
        hou.FloatParmTemplate("tallness", "Tallness", 1, default_value=(1.0,), min=0.3, max=2.5),
        hou.FloatParmTemplate("roughness", "Roughness", 1, default_value=(0.5,), min=0.0, max=1.0),
        hou.IntParmTemplate("chisel", "Chisel Cuts", 1, default_value=(9,), min=0, max=16),
        hou.FloatParmTemplate("cut_depth", "Cut Depth", 1, default_value=(0.45,), min=0.05, max=0.6),
        hou.FloatParmTemplate("moss", "Moss", 1, default_value=(0.0,), min=0.0, max=1.0),
        hou.IntParmTemplate("cluster_count", "Cluster Rocks", 1, default_value=(4,), min=2, max=8),
        hou.IntParmTemplate("detail", "Detail", 1, default_value=(2,), min=1, max=5),
    ):
        shape_folder.addParmTemplate(template)
    look = hou.FolderParmTemplate("style_folder", "Style", folder_type=hou.folderType.Simple)
    for template in build_style.style_parm_templates():
        look.addParmTemplate(template)
    group.append(shape_folder)
    group.append(look)
    definition.setParmTemplateGroup(group)
    definition.save(HDA_PATH)
    work.destroy()
    print("HDA saved:", HDA_PATH)


if __name__ in ("__main__", "__iwb_bridge__"):
    build()
