"""Save a picture of the Houdini viewport to <kit>/captures/snapshot.png (frames the displayed geometry)."""
import os

import hou
import toolutils

KIT = os.path.join(os.path.expanduser("~"), "Documents", "Low-Poly-Nature-Kit").replace("\\", "/")
os.makedirs(KIT + "/captures", exist_ok=True)
path = KIT + "/captures/snapshot.png"

viewer = toolutils.sceneViewer()
viewport = viewer.curViewport()
viewport.changeType(hou.geometryViewportType.Perspective)
hou.clearAllSelected()
viewport.frameAll()
flip = viewer.flipbookSettings().stash()
flip.frameRange((hou.frame(), hou.frame()))
flip.output(path)
flip.outputToMPlay(False)
flip.resolution((1400, 700))
viewer.flipbook(viewport, flip)
print("saved", path)
