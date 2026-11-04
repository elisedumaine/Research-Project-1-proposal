"""Build the kit's shared style HDA (lpk_style) in the open Houdini.

Run from the kit folder:  python Tools/houdini.py -f scripts/build_style.py

Every generator in the kit ends with this node.  It reads a primitive string
attribute `part` (bark, leaf, accent, rock, ...) and an int `piece`, then:
  - paints each face with the chosen palette's color for its part,
  - varies the color a little per piece and per facet (hand-painted look),
  - gives every face hard normals, so it reads as a flat low-poly facet.
"""
import os

import hou

KIT = os.path.join(os.path.expanduser("~"), "Documents", "Low-Poly-Nature-Kit").replace("\\", "/")
HDA_PATH = KIT + "/hda/lpk_style.hda"

# Parts every generator may use.  "bark" is resolved to bark_light or
# bark_dark by the Bark tone parameter.
PARTS = ("bark_light", "bark_dark", "leaf", "accent", "rock", "grass", "flower_a", "flower_b", "wood", "glow")

# Linear RGB, the same palettes as the Interactive World Builder.
PALETTES = {
    "Soft Dusk": {
        "bark_light": (0.88, 0.84, 0.76), "bark_dark": (0.16, 0.13, 0.12), "leaf": (0.78, 0.46, 0.26),
        "accent": (0.62, 0.36, 0.34), "rock": (0.48, 0.46, 0.42), "grass": (0.34, 0.40, 0.24),
        "flower_a": (0.95, 0.88, 0.72), "flower_b": (0.90, 0.60, 0.58), "wood": (0.50, 0.44, 0.34),
        "glow": (1.0, 0.70, 0.45)},
    "Emberwild": {
        "bark_light": (0.98, 0.92, 0.78), "bark_dark": (0.012, 0.006, 0.028), "leaf": (1.0, 0.18, 0.025),
        "accent": (0.96, 0.055, 0.22), "rock": (0.075, 0.27, 0.43), "grass": (0.78, 0.025, 0.10),
        "flower_a": (0.05, 0.84, 0.74), "flower_b": (1.0, 0.73, 0.17), "wood": (0.31, 0.035, 0.09),
        "glow": (1.0, 0.45, 0.22)},
    "Candy Cloud": {
        "bark_light": (1.0, 0.96, 0.90), "bark_dark": (0.36, 0.16, 0.42), "leaf": (1.0, 0.36, 0.62),
        "accent": (0.36, 0.92, 0.74), "rock": (0.80, 0.78, 0.98), "grass": (0.95, 0.62, 0.86),
        "flower_a": (1.0, 0.93, 0.40), "flower_b": (0.40, 0.80, 1.0), "wood": (0.98, 0.84, 0.66),
        "glow": (1.0, 0.84, 0.90)},
    "Neon Night": {
        "bark_light": (0.92, 0.95, 1.0), "bark_dark": (0.0, 0.0, 0.0), "leaf": (0.0, 0.90, 1.0),
        "accent": (1.0, 0.0, 0.55), "rock": (0.12, 0.0, 0.30), "grass": (0.38, 0.0, 1.0),
        "flower_a": (0.85, 1.0, 0.0), "flower_b": (1.0, 0.36, 0.0), "wood": (0.26, 0.0, 0.36),
        "glow": (0.55, 0.42, 1.0)},
    "Coral Lagoon": {
        "bark_light": (1.0, 0.95, 0.86), "bark_dark": (0.10, 0.05, 0.16), "leaf": (1.0, 0.34, 0.28),
        "accent": (1.0, 0.72, 0.18), "rock": (0.92, 0.80, 0.62), "grass": (0.04, 0.70, 0.72),
        "flower_a": (1.0, 0.22, 0.55), "flower_b": (0.58, 0.38, 1.0), "wood": (0.90, 0.74, 0.48),
        "glow": (1.0, 0.90, 0.74)},
    "Golden Hour": {
        "bark_light": (0.98, 0.92, 0.80), "bark_dark": (0.08, 0.03, 0.02), "leaf": (1.0, 0.68, 0.04),
        "accent": (0.82, 0.10, 0.04), "rock": (0.58, 0.22, 0.13), "grass": (0.96, 0.52, 0.12),
        "flower_a": (1.0, 0.98, 0.84), "flower_b": (0.62, 0.04, 0.34), "wood": (0.84, 0.62, 0.32),
        "glow": (1.0, 0.60, 0.30)},
    "Frost Violet": {
        "bark_light": (0.95, 0.97, 1.0), "bark_dark": (0.05, 0.03, 0.12), "leaf": (0.52, 0.26, 0.95),
        "accent": (0.26, 0.84, 1.0), "rock": (0.84, 0.90, 1.0), "grass": (0.74, 0.80, 1.0),
        "flower_a": (1.0, 0.52, 0.84), "flower_b": (0.96, 0.94, 0.52), "wood": (0.50, 0.44, 0.70),
        "glow": (0.72, 0.76, 1.0)},
    "Natural": {
        "bark_light": (0.62, 0.58, 0.50), "bark_dark": (0.20, 0.12, 0.07), "leaf": (0.12, 0.30, 0.06),
        "accent": (0.30, 0.40, 0.08), "rock": (0.40, 0.38, 0.35), "grass": (0.18, 0.38, 0.08),
        "flower_a": (0.95, 0.90, 0.70), "flower_b": (0.85, 0.30, 0.40), "wood": (0.36, 0.22, 0.12),
        "glow": (1.0, 0.75, 0.40)},
}
PALETTE_NAMES = tuple(PALETTES)


def vex_table():
    rows = []
    for name in PALETTE_NAMES:
        rows.append(", ".join("{%g, %g, %g}" % PALETTES[name][part] for part in PARTS))
    return "vector table[] = {\n    " + ",\n    ".join(rows) + "};"


PAINT_VEX = r"""
// Palette table: one row per palette, one column per part.
%(table)s
string parts[] = {%(parts)s};
int nparts = len(parts);

int seed = chi("../seed");
int pal = chi("../palette");
float jitter = chf("../jitter");

string part = s@part;
if (part == "bark") {
    int tone = chi("../bark_tone");          // 0 light, 1 dark, 2 seeded mix
    if (tone == 2) tone = rand(seed * 3.17 + 0.5) < 0.5 ? 0 : 1;
    part = tone == 0 ? "bark_light" : "bark_dark";
}
int idx = find(parts, part);
if (idx < 0) idx = find(parts, "rock");
vector c = table[pal * nparts + idx];

// Hand-painted variation: a little per piece, a little less per facet.
float per_piece = rand(set(i@piece, seed, 3.1)) - 0.5;
float per_face = rand(set(@primnum, seed, 9.7)) - 0.5;
c *= 1.0 + per_piece * 2.0 * jitter + per_face * jitter;
@Cd = clamp(c, 0.0, 1.0);
""" % {"table": vex_table(), "parts": ", ".join('"%s"' % p for p in PARTS)}


def style_parm_templates():
    """The style controls; generators copy these onto their own interface."""
    return (
        hou.MenuParmTemplate("palette", "Palette", menu_items=[str(i) for i in range(len(PALETTE_NAMES))],
                             menu_labels=PALETTE_NAMES, default_value=0),
        hou.MenuParmTemplate("bark_tone", "Bark Tone", menu_items=("0", "1", "2"),
                             menu_labels=("Light", "Dark", "Seeded mix"), default_value=1),
        hou.FloatParmTemplate("jitter", "Color Variation", 1, default_value=(0.12,), min=0.0, max=0.4),
    )


def build():
    work = hou.node("/obj").createNode("geo", "lpk_style_build")
    subnet = work.createNode("subnet", "lpk_style")
    paint = subnet.createNode("attribwrangle", "paint")
    paint.setInput(0, subnet.indirectInputs()[0])
    paint.parm("class").set("primitive")
    paint.parm("snippet").set(PAINT_VEX)
    facets = subnet.createNode("normal", "facets")
    facets.setInput(0, paint)
    facets.parm("cuspangle").set(0.0)
    out = subnet.createNode("output", "out")
    out.setInput(0, facets)
    out.setDisplayFlag(True)
    subnet.layoutChildren()

    asset = subnet.createDigitalAsset(name="lpk_style", hda_file_name=HDA_PATH, description="LPK Style",
                                      min_num_inputs=1, max_num_inputs=1)
    definition = asset.type().definition()
    group = definition.parmTemplateGroup()
    group.append(hou.IntParmTemplate("seed", "Seed", 1, default_value=(1,), min=0, max=1000))
    for template in style_parm_templates():
        group.append(template)
    definition.setParmTemplateGroup(group)
    definition.save(HDA_PATH)
    work.destroy()
    print("HDA saved:", HDA_PATH)


# Run by the bridge (or directly); stays quiet when imported by another build script.
if __name__ in ("__main__", "__iwb_bridge__"):
    build()
