"""Build the kit's Low-Polify HDA (lpk_lowpolify) in the open Houdini.

Run from the kit folder, after build_style.py:
    python Tools/houdini.py -f scripts/build_lowpolify.py

Turns any 3D model (OBJ, FBX, glTF/GLB...) into the kit's style:
  1. Load the file, turn it upright (Y up or Z up), stand it on the ground
     and scale it to a chosen height.
  2. Solidify (optional): rebuild it as one closed surface through a voxel
     volume.  This repairs holes and merges many loose parts, which models
     made by an AI from a photo often have.
  3. PolyReduce down to a small number of faces (Facets).
  4. Color each facet:  Palette match picks, for every facet, the palette
     color nearest to the model's own color there; Original keeps that
     color, flattened per facet; Single paints everything one palette part.
  5. lpk_style adds the hand-painted variation and the flat facets.
Units are meters; the object sits on y = 0.
"""
import os
import sys

import hou

KIT = os.path.join(os.path.expanduser("~"), "Documents", "Low-Poly-Nature-Kit").replace("\\", "/")
sys.path.insert(0, KIT + "/scripts")
import build_style  # noqa: E402

HDA_PATH = KIT + "/hda/lpk_lowpolify.hda"
COLOR_MODES = ("Palette match", "Original colors", "Single color")
SINGLE_PARTS = ("rock", "wood", "leaf", "accent", "grass", "bark_dark", "bark_light", "flower_a", "flower_b", "glow")

FIT_VEX = r"""
// Stand the model on the ground, centered, at the chosen height (0 keeps its size).
vector lo = getbbox_min(0), hi = getbbox_max(0);
float target = chf("../height");
float scale = target > 0 ? target / max(hi.y - lo.y, 1e-6) : 1.0;
vector center = set((lo.x + hi.x) * 0.5, lo.y, (lo.z + hi.z) * 0.5);
@P = (@P - center) * scale;
"""

COLOR_VEX = r"""
// Each facet takes the model's color at its middle (from input 1, the
// original), then either keeps it, snaps it to the nearest palette color,
// or is painted one single palette part.
%(table)s
string parts[] = {%(parts)s};
int nparts = len(parts);
int mode = chi("../color_mode");
string single[] = {%(single)s};

vector c = {0.6, 0.6, 0.6};
int has_color = haspointattrib(1, "Cd") || hasvertexattrib(1, "Cd") || hasprimattrib(1, "Cd");
if (has_color) {
    int prim;
    vector uv;
    xyzdist(1, @P, prim, uv);
    c = primuv(1, "Cd", prim, uv);
}
i@piece = 0;
if (mode == 2 || !has_color) {
    s@part = single[chi("../single_part")];
} else if (mode == 1) {
    s@part = "keep";
    @Cd = c;
} else {
    // Nearest palette color, compared in a gamma space closer to how we see.
    int pal = chi("../palette");
    float best = 1e9;
    string pick = "rock";
    for (int i = 0; i < nparts; i++) {
        vector d = pow(table[pal * nparts + i], 0.4545) - pow(c, 0.4545);
        float dist = dot(d, d);
        if (dist < best) { best = dist; pick = parts[i]; }
    }
    s@part = pick;
}
""" % {"table": build_style.vex_table(), "parts": ", ".join('"%s"' % p for p in build_style.PARTS),
       "single": ", ".join('"%s"' % p for p in SINGLE_PARTS)}


def build():
    work = hou.node("/obj").createNode("geo", "lpk_lowpolify_build")
    subnet = work.createNode("subnet", "lpk_lowpolify")

    load = subnet.createNode("file", "load")
    load.parm("file").setExpression('chs("../file")', language=hou.exprLanguage.Hscript)
    load.parm("missingframe").set(1)          # empty instead of an error while no file is chosen
    # Z-up files (Blender, 3ds Max exports) are turned to Houdini's Y up.
    upright = subnet.createNode("xform", "upright")
    upright.setInput(0, load)
    upright.parm("rx").setExpression('if(ch("../up_axis") == 1, -90, 0)')
    upright.parm("ry").setExpression('ch("../turn")')
    clean = subnet.createNode("attribdelete", "drop_normals")
    clean.setInput(0, upright)
    clean.parm("ptdel").set("N")
    clean.parm("vtxdel").set("N")
    fit = subnet.createNode("attribwrangle", "fit")
    fit.setInput(0, clean)
    fit.parm("class").set("point")
    fit.parm("snippet").set(FIT_VEX)

    # Solidify: one closed watertight surface, rebuilt through a voxel volume.
    to_volume = subnet.createNode("vdbfrompolygons", "to_volume")
    to_volume.setInput(0, fit)
    to_volume.parm("voxelsize").setExpression(
        '(bbox("../fit", D_YSIZE) + bbox("../fit", D_XSIZE) + bbox("../fit", D_ZSIZE)) / (3 * ch("../voxel_detail"))')
    fill = to_volume.parm("fillinterior")
    if fill:
        fill.set(True)
    to_mesh = subnet.createNode("convertvdb", "to_mesh")
    to_mesh.setInput(0, to_volume)
    to_mesh.parm("conversion").set("poly")
    solid = subnet.createNode("switch", "solidify_or_not")
    solid.setInput(0, fit)
    solid.setInput(1, to_mesh)
    solid.parm("input").setExpression('ch("../solidify")')

    reduce = subnet.createNode("polyreduce::2.0", "facets")
    reduce.setInput(0, solid)
    reduce.parm("target").set("poly_count")
    reduce.parm("finalcount").setExpression('ch("../facets")')
    color = subnet.createNode("attribwrangle", "color")
    color.setInput(0, reduce)
    color.setInput(1, fit)
    color.parm("class").set("primitive")
    color.parm("snippet").set(COLOR_VEX)
    tidy = subnet.createNode("attribdelete", "tidy")
    tidy.setInput(0, color)
    tidy.parm("ptdel").set("* ^P")
    tidy.parm("vtxdel").set("*")
    tidy.parm("primdel").set("* ^part ^piece ^Cd")

    style = subnet.createNode("lpk_style", "style")
    style.setInput(0, tidy)
    for name in ("seed", "palette", "bark_tone", "jitter"):
        style.parm(name).setExpression('ch("../%s")' % name)
    out = subnet.createNode("output", "out")
    out.setInput(0, style)
    out.setDisplayFlag(True)
    subnet.layoutChildren()

    asset = subnet.createDigitalAsset(name="lpk_lowpolify", hda_file_name=HDA_PATH, description="LPK Low-Polify",
                                      min_num_inputs=0, max_num_inputs=0)
    definition = asset.type().definition()
    group = definition.parmTemplateGroup()
    model = hou.FolderParmTemplate("model_folder", "Model", folder_type=hou.folderType.Simple)
    for template in (
        hou.StringParmTemplate("file", "Model File", 1, string_type=hou.stringParmType.FileReference,
                               file_type=hou.fileType.Geometry),
        hou.MenuParmTemplate("up_axis", "Up Axis", menu_items=("0", "1"), menu_labels=("Y up", "Z up"), default_value=0),
        hou.FloatParmTemplate("turn", "Turn", 1, default_value=(0.0,), min=-180.0, max=180.0),
        hou.FloatParmTemplate("height", "Height (m, 0 = keep)", 1, default_value=(1.0,), min=0.0, max=20.0),
        hou.ToggleParmTemplate("solidify", "Solidify (repair holes, merge parts)", default_value=True),
        hou.IntParmTemplate("voxel_detail", "Solidify Detail", 1, default_value=(60,), min=20, max=200),
        hou.IntParmTemplate("facets", "Facets", 1, default_value=(300,), min=20, max=3000),
        hou.MenuParmTemplate("color_mode", "Colors", menu_items=[str(i) for i in range(len(COLOR_MODES))],
                             menu_labels=COLOR_MODES, default_value=0),
        hou.MenuParmTemplate("single_part", "Single Color", menu_items=[str(i) for i in range(len(SINGLE_PARTS))],
                             menu_labels=[p.replace("_", " ").title() for p in SINGLE_PARTS], default_value=0),
        hou.IntParmTemplate("seed", "Seed", 1, default_value=(1,), min=0, max=1000),
    ):
        model.addParmTemplate(template)
    look = hou.FolderParmTemplate("style_folder", "Style", folder_type=hou.folderType.Simple)
    for template in build_style.style_parm_templates():
        look.addParmTemplate(template)
    group.append(model)
    group.append(look)
    definition.setParmTemplateGroup(group)
    definition.save(HDA_PATH)
    work.destroy()
    print("HDA saved:", HDA_PATH)


if __name__ in ("__main__", "__iwb_bridge__"):
    build()
