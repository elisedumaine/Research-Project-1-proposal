"""Lay out the special tree species side by side in /obj/lpk_species_demo (and show only that)."""
import hou

SPECIES = (("Palm", 4), ("Cherry", 5), ("Willow", 6), ("Cactus", 7), ("Giant Mushroom", 8), ("Bamboo", 9))

obj = hou.node("/obj")
old = obj.node("lpk_species_demo")
if old:
    old.destroy()
demo = obj.createNode("geo", "lpk_species_demo")
merge = demo.createNode("merge", "all")
for i, (name, index) in enumerate(SPECIES):
    tree = demo.createNode("lpk_tree", name.lower().replace(" ", "_"))
    tree.parm("species").set(index)
    tree.parm("seed").set(11 + i)
    move = demo.createNode("xform", "place_" + tree.name())
    move.setInput(0, tree)
    move.parm("tx").set(i * 8.0)
    merge.setNextInput(move)
    geo = tree.geometry()
    print("%-15s %4d faces  parts %s %s" % (name, len(geo.prims()), sorted(set(geo.primStringAttribValues("part"))),
                                           tree.errors() or ""))
merge.setDisplayFlag(True)
demo.layoutChildren()
for node in obj.children():
    node.setDisplayFlag(node == demo)
