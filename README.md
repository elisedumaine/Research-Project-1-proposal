# Low-Poly Nature Kit — Research Project 1

Elise Dumaine · Nov 2026

**Video (1–3 min):** _link coming — recording of the Studio and the forest in Play_

The Unreal side lives in my midterm repo:
[Midterm-a-tool-you-d-actually-use](https://github.com/elisedumaine/Midterm-a-tool-you-d-actually-use)
(`Content/Python/lowpoly_*.py`, `Source/ForestGame/`).

## What I set out to do

My proposal ([PROPOSAL.md](PROPOSAL.md)):
a Houdini kit of low-poly asset generators (trees, rocks...) sharing one style,
plus a "Low-Polify" tool for any imported model, feeding the Interactive World
Builder I made for the midterm. Smallest version: style + trees + rocks, baked
and growing in one Unreal forest.

## What I made

- **Houdini HDAs** (`hda/`, built by the scripts in `scripts/`):
  - `lpk_style` — one shared look: faceted faces painted from a palette, per part (trunk, leaves, moss...).
  - `lpk_tree` — 10 species (broadleaf, pine, birch, dead, palm, cherry, willow, cactus, giant mushroom, bamboo) and silhouettes (baobab, giant, slender, bonsai...).
  - `lpk_rock` — pebble, boulder, slab, cliff, cluster, with chisel cuts and moss.
  - `lpk_lowpolify` — any imported model → cleaned, reduced, recolored in the kit's style.
  - `lpk_character` — a simple customizable player character.
- **Photo → 3D** (`scripts/photo_to_3d.py`): TripoSR runs locally on my GPU, then Low-Polify.
- **Low-Poly Studio in Unreal** (midterm repo): a game-style panel with ◀ ▶ arrows,
  sliders and a live 3D preview. "Add to forest" bakes 6 variations into the
  World Builder's population, so the generator grows my designs everywhere
  (never hand placement). Tabs: Trees, Rocks, Import, Character.
- **Living climate** (added along the way, C++ `AForestSky`): in Play, time passes
  (a day = 12 min), the weather changes by itself (clear, cloudy, drizzle, rain,
  storm, sun shower, mist, snow), stars and moon at night, rainbow in sun showers,
  lightning + thunder in storms, wind swaying plants, blowing leaves, valley mist.
- **Title screen + wake-up intro**, English / French choice.

## How it changed, and why

- I did **not** use the Houdini Engine plugin: I wrote a small local socket bridge
  (Houdini open with a startup script, Unreal talks to it). The Education license
  doesn't allow background hython, and the bridge let me test vertex colors early.
- Mushrooms/props tabs were dropped for the character tab, which I found more useful.
- The climate wasn't in the proposal: once the forest worked I wanted it to feel alive.

## How to run it

1. Houdini 22 open with the bridge (`Documents/houdini22.0/python3.13libs/uiready.py`).
2. Build the HDAs: run `scripts/build_*.py` through the bridge (`Tools/houdini.py -f ...`).
3. Open the midterm project in Unreal 5.8 → the Low-Poly Studio opens by itself.
   Pick a design, press **Add to forest**, then **Grow forest now**.
4. Press **Play**: choose English/Français, press PLAY.

Without Houdini the Studio shows "Open Houdini to see the preview"; the forest still
works with the meshes already baked.

## What I learned

- Houdini: VEX on primitives, copy-to-points, PolyReduce, how an HDA exposes parameters.
- Unreal: vertex-color materials, Material Parameter Collections (one value changes
  every material: snow, wet, wind), Editor Utility Widgets driven from Python, C++ actors.
- Debugging: inside-out character faces (normals/winding), a preview that crashed
  Unreal out of memory (capturing every frame), a rainbow whose material color was
  silently zero (wrong pin name).
- Working with an agent: I asked for things, judged the result on screen, and
  learned to explain each part. I fixed the inward faces bug by hand in Houdini.

## What doesn't work yet

- Classmates can't use it straight from GitHub: the HDAs and population file use my local paths.
- Not verified on screen yet: blowing leaves, valley mist at dawn, the wake-up intro
  and the language switch (they compile; I need to restart Unreal and test).
- Low-Polify was only tested on a few models; photo → 3D is slow (~75 s) and messy on some photos.
- No LODs.

## What I'd do next

Make the repo work for classmates (project-relative paths, baked meshes committed,
setup `.bat`), aurora / shooting stars / fireflies, LODs, and a sandbox mode
(pick up apples and berries, feed animals).
