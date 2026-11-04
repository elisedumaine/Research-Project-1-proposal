"""Build the kit's tree generator HDA (lpk_tree) in the open Houdini.

Run from the kit folder, after build_style.py:
    python Tools/houdini.py -f scripts/build_tree.py

How a tree is made:
  1. A VEX wrangle grows the skeleton: a bent, tapering trunk and branches,
     built as low-sided tubes (part "bark"), plus foliage points at the
     branch tips (with size, rotation and squash).
  2. Low-poly foliage shapes are copied onto those points: faceted balls for
     broadleaf and birch, stacked cones for pine.  Dead trees get none.
  3. A noise makes every foliage clump lumpy and unique.
  4. lpk_style paints everything with the palette and makes the facets flat.
Units are meters; the tree stands on y = 0.
"""
import os
import sys

import hou

KIT = os.path.join(os.path.expanduser("~"), "Documents", "Low-Poly-Nature-Kit").replace("\\", "/")
sys.path.insert(0, KIT + "/scripts")
import build_style  # noqa: E402  (style parameters shared by every generator)

HDA_PATH = KIT + "/hda/lpk_tree.hda"
SPECIES = ("Broadleaf", "Pine", "Birch", "Dead")

SKELETON_VEX = r"""
// ---------- helpers ----------
// A tube along pts with one radius per point, `sides` faces around, capped at the end.
void tube(vector pts[]; float rads[]; int sides; string part; int piece) {
    int n = len(pts);
    int first[];
    for (int i = 0; i < n; i++) {
        vector dir;
        if (i == 0) dir = pts[1] - pts[0];
        else if (i == n - 1) dir = pts[i] - pts[i - 1];
        else dir = pts[i + 1] - pts[i - 1];
        dir = normalize(dir);
        vector up = abs(dir.y) < 0.9 ? set(0, 1, 0) : set(1, 0, 0);
        vector a = normalize(cross(up, dir));
        vector b = normalize(cross(dir, a));
        for (int s = 0; s < sides; s++) {
            float ang = 2.0 * PI * s / sides;
            int pt = addpoint(0, pts[i] + rads[i] * (cos(ang) * a + sin(ang) * b));
            if (s == 0) append(first, pt);
        }
    }
    for (int j = 0; j < n - 1; j++) {
        for (int s = 0; s < sides; s++) {
            int s2 = (s + 1) % sides;
            int pr = addprim(0, "poly", first[j] + s, first[j + 1] + s, first[j + 1] + s2, first[j] + s2);
            setprimattrib(0, "part", pr, part);
            setprimattrib(0, "piece", pr, piece);
        }
    }
    int cap[];
    for (int s = sides - 1; s >= 0; s--) append(cap, first[n - 1] + s);
    int pc = addprim(0, "poly", cap);
    setprimattrib(0, "part", pc, part);
    setprimattrib(0, "piece", pc, piece);
}

// Position and radius along the trunk, t in 0..1.
vector along(vector pts[]; float t) {
    float f = clamp(t, 0.0, 1.0) * (len(pts) - 1);
    int k = min(int(f), len(pts) - 2);
    return lerp(pts[k], pts[k + 1], f - k);
}
float along_r(float rads[]; float t) {
    float f = clamp(t, 0.0, 1.0) * (len(rads) - 1);
    int k = min(int(f), len(rads) - 2);
    return lerp(rads[k], rads[k + 1], f - k);
}

// A foliage point: shape 0 = ball, 1 = cone.
void leaf(vector p; float size; int shape; int seed; int id; float accent_chance) {
    int pt = addpoint(0, p);
    setpointattrib(0, "pscale", pt, size);
    setpointattrib(0, "shape", pt, shape);
    setpointattrib(0, "clump", pt, id);
    float yaw = rand(set(seed, id, 11.0)) * 2.0 * PI;
    float tilt = shape == 0 ? (rand(set(seed, id, 12.0)) - 0.5) * 0.6 : 0.0;
    vector4 q = qmultiply(quaternion(yaw, {0, 1, 0}), quaternion(tilt, {1, 0, 0}));
    setpointattrib(0, "orient", pt, q);
    float squash = shape == 0 ? fit01(rand(set(seed, id, 13.0)), 0.7, 0.9) : 1.7;
    setpointattrib(0, "scale", pt, set(1.0, squash, 1.0));
    string part = rand(set(seed, id, 14.0)) < accent_chance ? "accent" : "leaf";
    setpointattrib(0, "leafpart", pt, part);
}

// ---------- parameters ----------
int seed = chi("../seed");
int species = chi("../species");          // 0 broadleaf, 1 pine, 2 birch, 3 dead
float H = chf("../height");
float R = chf("../trunk_width") * 0.5;
float lean = chf("../lean");
int nb = chi("../branches");
float blen = chf("../branch_length");
float crown = chf("../crown_size");
float accent = chf("../accent_amount");
int detail = chi("../detail");
int sides = 3 + detail;                   // detail 1..5 -> 4..8 sides

addprimattrib(0, "part", "");
addprimattrib(0, "piece", 0);
addpointattrib(0, "pscale", 0.0);
addpointattrib(0, "shape", -1);
addpointattrib(0, "clump", 0);
addpointattrib(0, "orient", {0, 0, 0, 1});
addpointattrib(0, "scale", {1, 1, 1});
addpointattrib(0, "leafpart", "");

// ---------- species shape ----------
float trunk_top = 0.78;    // how far up the trunk goes (fraction of height)
float taper = 0.35;
float bstart = 0.35;       // where branches start on the trunk
if (species == 1) { trunk_top = 0.92; taper = 0.12; }
if (species == 2) { R *= 0.65; trunk_top = 0.88; taper = 0.45; bstart = 0.45; }
if (species == 3) { trunk_top = 0.85; taper = 0.25; bstart = 0.3; }

// ---------- trunk ----------
int ns = 6;
vector tp[];
float tr[];
vector bend = set(rand(seed * 1.13 + 0.1) - 0.5, 0, rand(seed * 2.71 + 0.2) - 0.5) * lean * H * 0.5;
for (int k = 0; k <= ns; k++) {
    float t = float(k) / ns;
    vector wob = set(noise(set(t * 2.3, seed * 0.37, 0.1)) - 0.5, 0,
                     noise(set(t * 2.3, seed * 0.37, 7.7)) - 0.5) * lean * H * 0.25;
    append(tp, set(0, t * H * trunk_top, 0) + bend * t * t + wob * t);
    append(tr, R * lerp(1.0, taper, t));
}
tp[0].y = -R * 0.3;        // sink the base a little into the ground
tr[0] *= 1.35;             // root flare
tube(tp, tr, sides, species == 2 ? "bark_light" : "bark", 0);
vector top = tp[ns];

// ---------- branches and foliage ----------
int clump = 0;
if (species == 1) {
    // Pine: stacked cones around the trunk, wide at the bottom.
    int layers = clamp(nb / 2 + 2, 3, 8);
    for (int l = 0; l < layers; l++) {
        float u = fit(float(l), 0, layers - 1, 0.38, 0.92);
        float size = crown * H * 0.3 * (1.0 - u * 0.72) * fit01(rand(set(seed, l, 5.0)), 0.9, 1.1);
        leaf(along(tp, u) - set(0, size * 0.55, 0), size, 1, seed, clump++, accent * 0.5);
    }
    leaf(top, crown * H * 0.08, 1, seed, clump++, 0.0);
} else {
    float golden = 2.39996;
    for (int b = 0; b < nb; b++) {
        float u = fit01(rand(set(seed, b, 1.0)), bstart, 0.95);
        vector base = along(tp, u);
        float rb = along_r(tr, u) * (species == 3 ? 0.6 : 0.5);
        float az = b * golden + rand(set(seed, b, 2.0)) * 0.8;
        float elev = radians(species == 3 ? fit01(rand(set(seed, b, 3.0)), 5, 40)
                                          : fit01(rand(set(seed, b, 3.0)), 25, 55));
        vector dir = set(cos(az) * cos(elev), sin(elev), sin(az) * cos(elev));
        float L = blen * H * fit01(rand(set(seed, b, 4.0)), 0.7, 1.1) * (1.15 - u * 0.5);
        vector p1 = base + dir * L * 0.55 + set(0, L * 0.06, 0);
        vector p2 = base + dir * L + set(0, L * 0.2, 0);
        string bark = species == 2 ? "bark_light" : "bark";
        tube(array(base, p1, p2), array(rb, rb * 0.7, rb * 0.35), max(sides - 1, 3), bark, 1 + b);
        if (species == 3) {
            // Dead trees fork once instead of carrying leaves.
            vector fdir = normalize(dir + set(sin(az + 1.7), 0.5, cos(az + 1.7)) * 0.8);
            tube(array(p1, p1 + fdir * L * 0.45), array(rb * 0.6, rb * 0.2), 3, bark, 100 + b);
        } else {
            float size = crown * H * (species == 2 ? 0.11 : 0.16) * fit01(rand(set(seed, b, 6.0)), 0.75, 1.25);
            leaf(p2, size, 0, seed, clump++, accent);
            if (species == 0 && rand(set(seed, b, 7.0)) < 0.5)
                leaf(p1 + set(0, size * 0.4, 0), size * 0.7, 0, seed, clump++, accent);
        }
    }
    if (species != 3) {
        // The crown: one big clump on top and a few around it.
        float big = crown * H * (species == 2 ? 0.15 : 0.24);
        leaf(top + set(0, big * 0.3, 0), big, 0, seed, clump++, accent);
        int extra = species == 2 ? 2 : 4;
        for (int e = 0; e < extra; e++) {
            float a = e * 2.0 * PI / extra + rand(set(seed, e, 8.0));
            vector off = set(cos(a), fit01(rand(set(seed, e, 9.0)), -0.5, 0.3), sin(a)) * big * 0.75;
            leaf(top + off, big * fit01(rand(set(seed, e, 10.0)), 0.6, 0.85), 0, seed, clump++, accent);
        }
    }
}
"""

# After copying, turn the foliage attributes into the ones lpk_style reads.
FOLIAGE_PARTS_VEX = r"""
s@part = s@leafpart;
i@piece = 1000 + i@clump;
"""


def build():
    work = hou.node("/obj").createNode("geo", "lpk_tree_build")
    subnet = work.createNode("subnet", "lpk_tree")

    skeleton = subnet.createNode("attribwrangle", "skeleton")
    skeleton.parm("class").set("detail")
    skeleton.parm("snippet").set(SKELETON_VEX)

    bark = subnet.createNode("blast", "bark_only")
    bark.setInput(0, skeleton)
    bark.parm("group").set("@shape>=0")
    bark.parm("grouptype").set("points")
    tips_ball = subnet.createNode("blast", "ball_points")
    tips_ball.setInput(0, skeleton)
    tips_ball.parm("group").set("@shape=0")
    tips_ball.parm("grouptype").set("points")
    tips_ball.parm("negate").set(True)
    tips_cone = subnet.createNode("blast", "cone_points")
    tips_cone.setInput(0, skeleton)
    tips_cone.parm("group").set("@shape=1")
    tips_cone.parm("grouptype").set("points")
    tips_cone.parm("negate").set(True)

    # Foliage shapes, unit size.  Detail picks how round they are.
    ball = subnet.createNode("sphere", "ball")
    ball.parm("type").set("polymesh")
    ball.parm("rows").setExpression('ch("../detail") + 3')
    ball.parm("cols").setExpression('ch("../detail") * 2 + 4')
    cone = subnet.createNode("tube", "cone")
    cone.parm("type").set("poly")
    cone.parm("cap").set(True)
    cone.parm("rad1").set(0.0)
    cone.parm("rad2").set(1.0)
    cone.parm("height").set(1.1)
    cone.parm("ty").set(0.55)
    cone.parm("cols").setExpression('ch("../detail") + 4')
    cone.parm("rows").set(2)

    copy_ball = subnet.createNode("copytopoints::2.0", "copy_balls")
    copy_ball.setInput(0, ball)
    copy_ball.setInput(1, tips_ball)
    copy_cone = subnet.createNode("copytopoints::2.0", "copy_cones")
    copy_cone.setInput(0, cone)
    copy_cone.setInput(1, tips_cone)
    for copy in (copy_ball, copy_cone):
        # Each copied clump keeps its leaf part and clump number, on its faces.
        copy.parm("targetattribs").set(1)
        copy.parm("applyto1").set(2)
        copy.parm("applymethod1").set(0)
        copy.parm("applyattribs1").set("leafpart clump")
    foliage = subnet.createNode("merge", "foliage")
    foliage.setInput(0, copy_ball)
    foliage.setInput(1, copy_cone)

    lumpy = subnet.createNode("mountain::2.0", "lumpy")
    lumpy.setInput(0, foliage)
    lumpy.parm("height").setExpression('ch("../lumpiness") * ch("../height") * 0.08')
    lumpy.parm("elementsize").setExpression('ch("../height") * 0.12')
    lumpy.parm("offsetx").setExpression('ch("../seed") * 13.37')
    lumpy.parm("offsety").setExpression('ch("../seed") * 7.11')
    parts = subnet.createNode("attribwrangle", "foliage_parts")
    parts.setInput(0, lumpy)
    parts.parm("class").set("primitive")
    parts.parm("snippet").set(FOLIAGE_PARTS_VEX)

    merge = subnet.createNode("merge", "tree")
    merge.setInput(0, bark)
    merge.setInput(1, parts)
    clean = subnet.createNode("attribdelete", "clean")
    clean.setInput(0, merge)
    clean.parm("ptdel").set("pscale shape clump orient scale leafpart")
    clean.parm("primdel").set("leafpart clump")

    style = subnet.createNode("lpk_style", "style")
    style.setInput(0, clean)
    for name in ("seed", "palette", "bark_tone", "jitter"):
        style.parm(name).setExpression('ch("../%s")' % name)
    out = subnet.createNode("output", "out")
    out.setInput(0, style)
    out.setDisplayFlag(True)
    subnet.layoutChildren()

    asset = subnet.createDigitalAsset(name="lpk_tree", hda_file_name=HDA_PATH, description="LPK Tree",
                                      min_num_inputs=0, max_num_inputs=0)
    definition = asset.type().definition()
    group = definition.parmTemplateGroup()
    shape = hou.FolderParmTemplate("shape_folder", "Tree", folder_type=hou.folderType.Simple)
    for template in (
        hou.IntParmTemplate("seed", "Seed", 1, default_value=(1,), min=0, max=1000),
        hou.MenuParmTemplate("species", "Species", menu_items=[str(i) for i in range(len(SPECIES))],
                             menu_labels=SPECIES, default_value=0),
        hou.FloatParmTemplate("height", "Height (m)", 1, default_value=(6.0,), min=1.0, max=20.0),
        hou.FloatParmTemplate("trunk_width", "Trunk Width (m)", 1, default_value=(0.45,), min=0.05, max=2.0),
        hou.FloatParmTemplate("lean", "Lean", 1, default_value=(0.25,), min=0.0, max=1.0),
        hou.IntParmTemplate("branches", "Branches", 1, default_value=(7,), min=0, max=20),
        hou.FloatParmTemplate("branch_length", "Branch Length", 1, default_value=(0.35,), min=0.05, max=0.8),
        hou.FloatParmTemplate("crown_size", "Crown Size", 1, default_value=(1.0,), min=0.3, max=2.0),
        hou.FloatParmTemplate("lumpiness", "Lumpiness", 1, default_value=(0.35,), min=0.0, max=1.0),
        hou.FloatParmTemplate("accent_amount", "Accent Clumps", 1, default_value=(0.15,), min=0.0, max=1.0),
        hou.IntParmTemplate("detail", "Detail", 1, default_value=(2,), min=1, max=5),
    ):
        shape.addParmTemplate(template)
    look = hou.FolderParmTemplate("style_folder", "Style", folder_type=hou.folderType.Simple)
    for template in build_style.style_parm_templates():
        look.addParmTemplate(template)
    group.append(shape)
    group.append(look)
    definition.setParmTemplateGroup(group)
    definition.save(HDA_PATH)
    work.destroy()
    print("HDA saved:", HDA_PATH)


if __name__ in ("__main__", "__iwb_bridge__"):
    build()
