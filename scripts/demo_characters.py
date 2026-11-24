"""Six sample characters side by side in /obj/lpk_character_demo (shown alone), facing the camera."""
import hou

LOOKS = (
    {"hair": 0, "top": 0, "bottom": 0},
    {"hair": 2, "hair_color": 3, "top": 4, "top_color": 2, "bottom": 2, "bottom_color": 1, "skin": 1, "hat": 4},
    {"hair": 5, "hair_color": 6, "top": 3, "top_color": 8, "bottom": 1, "shoes": 1, "skin": 3, "extra": 1, "head_size": 1},
    {"hair": 8, "facial_hair": 4, "hair_color": 5, "top": 1, "top_color": 3, "body": 2, "skin": 4, "hat": 3, "accent_color": 5},
    {"hair": 3, "hair_color": 4, "top": 2, "top_color": 9, "bottom": 1, "shoes": 2, "head_size": 2, "extra": 3},
    {"hair": 7, "hair_color": 1, "top": 0, "top_color": 10, "skin": 5, "body": 1, "hat": 1, "facial_hair": 1, "extra": 2},
)
obj = hou.node("/obj")
old = obj.node("lpk_character_demo")
if old:
    old.destroy()
demo = obj.createNode("geo", "lpk_character_demo")
merge = demo.createNode("merge", "all")
for i, look in enumerate(LOOKS):
    person = demo.createNode("lpk_character", "character_%d" % (i + 1))
    for key, value in look.items():
        person.parm(key).set(value)
    move = demo.createNode("xform", "place_%d" % (i + 1))
    move.setInput(0, person)
    move.parm("tx").set((i - 2.5) * 0.9)
    merge.setNextInput(move)
    geo = person.geometry()
    print("character %d: %d faces, bones %s %s" % (i + 1, len(geo.prims()), len(set(geo.primStringAttribValues("bone"))),
                                                  person.errors() or ""))
merge.setDisplayFlag(True)
demo.layoutChildren()
for node in obj.children():
    node.setDisplayFlag(node == demo)
