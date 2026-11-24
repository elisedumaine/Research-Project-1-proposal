"""Lay out one rock of each type side by side in /obj/lpk_rocks_demo (and show only that), and report on them."""
import hou

obj = hou.node("/obj")
old = obj.node("lpk_rocks_demo")
if old:
    old.destroy()
demo = obj.createNode("geo", "lpk_rocks_demo")
merge = demo.createNode("merge", "all")
x = 0.0
for i, kind in enumerate(("Pebble", "Boulder", "Slab", "Cliff", "Cluster")):
    rock = demo.createNode("lpk_rock", kind.lower())
    rock.parm("type").set(i)
    rock.parm("seed").set(3 + i)
    rock.parm("moss").set(0.4 if kind in ("Boulder", "Cluster") else 0.0)
    move = demo.createNode("xform", "place_" + kind.lower())
    move.setInput(0, rock)
    move.parm("tx").set(x)
    merge.setNextInput(move)
    geo = rock.geometry()
    box = geo.boundingBox()
    x += box.sizevec()[0] + 1.5
    parts = sorted(set(geo.primStringAttribValues("part")))
    print("%-8s %4d faces  size %.2f x %.2f x %.2f m  parts %s %s" % (
        kind, len(geo.prims()), box.sizevec()[0], box.sizevec()[1], box.sizevec()[2], parts,
        rock.errors() + rock.warnings() or ""))
merge.setDisplayFlag(True)
merge.setRenderFlag(True)
demo.layoutChildren()
for node in obj.children():
    node.setDisplayFlag(node == demo)
