# Research Project 1 proposal: Low-Poly Nature Kit

**Houdini 22 (Digital Assets, VEX, Python) → Houdini Engine → Unreal Engine 5.8**

## The project in one sentence

I will build a **Low-Poly Nature Kit** in Houdini: a family of procedural asset generators (trees, rocks, plants, mushrooms, and handmade props such as lanterns and fences) that share one style system, and I will connect it to my Unreal **Interactive World Builder** through Houdini Engine, so the forests it builds are filled with my own generated assets instead of fixed imported meshes.

## Why this one

My midterm tool does all of its procedural work in Unreal Python, and every tree and rock in it is the same handful of downloaded meshes. I have only touched Houdini briefly: a first river and a first rock asset. This project takes me somewhere unfamiliar and connects two programs. Afterward I will be able to:

- build real procedural assets in Houdini with SOP networks, VEX, and exposed HDA parameters;
- design a **shared style system**: one set of controls (seed, facet size, color palette, level of detail) that every generator follows, so a whole asset family stays consistent;
- run a Houdini → Unreal pipeline: cook assets with Houdini Engine, bake variations into static meshes with collision and LODs, and have a game tool place them.

## What I'll show

Both the tool and the work:

- **In Houdini:** each generator, with its sliders changing the asset live. Changing the palette or the seed once restyles the whole kit.
- **In Unreal:** a variation library of generated assets, and several forests built by the World Builder with them, walkable in Play mode.
- A short demo video, and a README that explains the kit and how to use it.

## The three weeks

- **By Nov 10: style system and first two generators.** A shared style setup (seed, facet size, palette colors written as vertex colors). A **tree** generator (trunk and branches from curves, faceted foliage clusters; height, branchiness, crown shape) and a **rock** generator (pebbles, boulders, cliff pieces). Both load in Unreal through Houdini Engine.
- **By Nov 17: plants and the Unreal pipeline.** A **plant** generator (bushes, ferns, grass tufts, flowers). Species presets that match my seasons (pine, round broadleaf, birch, dead tree). A script that bakes about 10–20 variations per type into static meshes with collision and LODs. The World Builder uses this library in place of its old meshes.
- **By Nov 23: extend and polish.** **Mushroom** and **prop** generators (lanterns, fences, a small bridge). A "level of detail" slider, from very faceted to softer, still stylized. A "Kit assets" choice in the World Builder panel. Then the demo video, the documentation, and the presentation.

## The smallest version that still counts

The shared style system plus **two working generators (trees and rocks)** in Houdini, with their variations baked by hand and imported into Unreal, and one forest built by the World Builder that uses them. Even if the live Houdini Engine link fails, this still shows procedural assets made in Houdini and used in a game world.

## The riskiest part

- **Automating Houdini Engine from my Unreal Python tool:** cooking the HDAs with different seeds and baking the results without clicking by hand, on an Education license. If this fails, the fallback is to export the variations from Houdini as files and import them into Unreal with a script.
- **Making the assets look good, not just procedural:** getting branches, foliage, and rocks that read well in my soft low-poly style takes many rounds of looking and adjusting.
