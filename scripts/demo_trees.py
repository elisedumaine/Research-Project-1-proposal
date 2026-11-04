"""Lay out one tree of each species side by side in /obj/lpk_demo, and report on them."""
import hou

obj = hou.node("/obj")
old = obj.node("lpk_demo")
if old:
    old.destroy()
demo = obj.createNode("geo", "lpk_demo")
merge = demo.createNode("merge", "all")
for i, species in enumerate(("Broadleaf", "Pine", "Birch", "Dead")):
    tree = demo.createNode("lpk_tree", species.lower())
    tree.parm("species").set(i)
    tree.parm("seed").set(7 + i)
    move = demo.createNode("xform", "place_" + species.lower())
    move.setInput(0, tree)
    move.parm("tx").set(i * 7.0)
    merge.setNextInput(move)
    errors = tree.errors() + tree.warnings()
    geo = tree.geometry()
    parts = sorted(set(geo.primStringAttribValues("part")))
    # Winding check: on a closed mesh, normals pointing outward give positive volume.
    measure = geo.boundingBox()
    print("%-9s %5d faces  size %.1f x %.1f m  parts %s %s" % (
        species, len(geo.prims()), measure.sizevec()[0], measure.sizevec()[1], parts, errors or ""))
merge.setDisplayFlag(True)
merge.setRenderFlag(True)
demo.layoutChildren()

# Winding check: trunk faces should point away from the trunk axis.
geo = demo.node("broadleaf").geometry()
dots = []
for prim in geo.prims()[:20]:
    c = prim.positionAtInterior(0.5, 0.5)
    dots.append(prim.normal().dot(hou.Vector3(c[0], 0, c[2]).normalized()))
print("trunk faces pointing outward:", sum(d > 0 for d in dots), "of", len(dots))
