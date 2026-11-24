# Prototype (run in Unreal with Tools/ue.py -f): live preview actor + scene capture into a render target.
import time
import unreal
import importlib
import lowpoly_studio as s
importlib.reload(s)

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for actor in eas.get_all_level_actors():
    if "LPS_Test" in [str(t) for t in actor.tags] or "LPS_Booth" in [str(t) for t in actor.tags]:
        actor.destroy_actor()

BOOTH = unreal.Vector(0, 0, 100000)
t = time.time()
faces = s.cook("tree", {"species": 0, "seed": 7})
t1 = time.time()
actor = eas.spawn_actor_from_class(unreal.DynamicMeshActor, BOOTH)
actor.tags = ["LPS_Booth"]
actor.set_actor_label("LPS_Preview")
component = actor.get_editor_property("dynamic_mesh_component")
mesh = component.get_dynamic_mesh()
buffers, count = s.mesh_buffers(faces)
mesh.reset()
mesh.append_buffers_to_mesh(buffers)
component.set_material(0, s.vertex_color_material())
print("preview mesh: cook %.2fs, set %.2fs, %d tris" % (t1 - t, time.time() - t1, count))
print([p for p in dir(component) if "color" in p.lower()])

capture = eas.spawn_actor_from_class(unreal.SceneCapture2D, unreal.Vector(BOOTH.x - 1100, BOOTH.y, BOOTH.z + 350))
capture.tags = ["LPS_Booth"]
capture.set_actor_label("LPS_PreviewCamera")
capture.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(capture.get_actor_location(), unreal.Vector(BOOTH.x, BOOTH.y, BOOTH.z + 300)), False)
cc = capture.get_editor_property("capture_component2d")
rt = unreal.RenderingLibrary.create_render_target2d(unreal.EditorLevelLibrary.get_editor_world(), 512, 384, unreal.TextureRenderTargetFormat.RTF_RGBA8_SRGB)
cc.set_editor_property("texture_target", rt)
cc.set_editor_property("primitive_render_mode", unreal.SceneCapturePrimitiveRenderMode.PRM_USE_SHOW_ONLY_LIST)
cc.show_only_actor_components(actor)
cc.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
cc.capture_scene()
path = "C:/Users/lilis/Documents/Low-Poly-Nature-Kit/captures"
unreal.RenderingLibrary.export_render_target(unreal.EditorLevelLibrary.get_editor_world(), rt, path, "preview_test.png")
print("exported")
