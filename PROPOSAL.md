# Research Project 1 proposal: Low-Poly Nature Kit

**Houdini 22 (Digital Assets, VEX, Python) → Houdini Engine → Unreal Engine 5.8**

## The project in one sentence

I will build a **Low-Poly Nature Kit** in Houdini: a family of procedural asset generators (trees, rocks, plants, mushrooms, and handmade props such as lanterns and fences) plus a **Low-Polify** tool that turns any imported 3D model into the same style. All of them share one style system, and I will connect the kit to my Unreal **Interactive World Builder** through Houdini Engine, so my game worlds are filled with my own consistent assets instead of fixed downloaded meshes.

## Why this one

My midterm tool does all of its procedural work in Unreal Python, and every tree and rock in it is the same handful of downloaded meshes. I have only touched Houdini briefly: a first river and a first rock asset. This project takes me somewhere unfamiliar and connects two programs. Afterward I will be able to:

- build real procedural assets in Houdini with SOP networks, VEX, and exposed HDA parameters;
- design a **shared style system**: one set of controls (seed, facet size, color palette, level of detail) that every generator follows, so a whole asset family stays consistent;
- **restyle existing models**: take any mesh (a chair, a statue, a downloaded asset), reduce it to clean facets, and paint it with my palette, so assets from anywhere fit my game;
- run a Houdini → Unreal pipeline: cook assets with Houdini Engine, bake variations into static meshes with collision and LODs, and have a game tool place them.

## What I'll show

Both the tool and the work:

- **In Houdini:** each generator, with its sliders changing the asset live. Changing the palette or the seed once restyles the whole kit. Next to it, a few imported models before and after Low-Polify.
- **In Unreal:** a library of generated and low-polified assets, and several worlds built by the World Builder with them, walkable in Play mode.
- A short demo video, and a README that explains the kit and how to use it.

## The three weeks

- **By Nov 10: style system and first two generators.** A shared style setup (seed, facet size, palette colors written as vertex colors). A **tree** generator (trunk and branches from curves, faceted foliage clusters; height, branchiness, crown shape) and a **rock** generator (pebbles, boulders, cliff pieces). Both load in Unreal through Houdini Engine.
- **By Nov 17: plants, Low-Polify, and the Unreal pipeline.** A **plant** generator (bushes, ferns, grass tufts, flowers) and species presets that match my seasons (pine, round broadleaf, birch, dead tree). The **Low-Polify** tool: import any model, reduce it to facets, recolor it with the palette, and keep it clean enough for collision. A script bakes about 10–20 variations per type into static meshes with collision and LODs. The World Builder uses this library in place of its old meshes.
- **By Nov 23: extend and polish.** **Mushroom** and **prop** generators (lanterns, fences, a small bridge). A "level of detail" slider, from very faceted to softer, still stylized. A "Kit assets" choice in the World Builder panel. Then the demo video, the documentation, and the presentation.
- **Bonus if time allows:** photo → 3D. Send a photo to an AI image-to-3D service, then run the result through Low-Polify so it fits the kit.

## The smallest version that still counts

The shared style system plus **two working generators (trees and rocks)** in Houdini, with their variations baked by hand and imported into Unreal, and one forest built by the World Builder that uses them. Even if the live Houdini Engine link fails, this still shows procedural assets made in Houdini and used in a game world.

## The riskiest part

- **Automating Houdini Engine from my Unreal Python tool:** cooking the HDAs with different seeds and baking the results without clicking by hand, on an Education license. If this fails, the fallback is to export the variations from Houdini as files and import them into Unreal with a script.
- **Low-Polify on messy models:** downloaded meshes often have holes, many separate parts, or millions of triangles, and a simple reduction can break their shape. I will test it on several kinds of models early.
- **Making the assets look good, not just procedural:** getting branches, foliage, and rocks that read well in my soft low-poly style takes many rounds of looking and adjusting.

## Next: Research Project 2

A customizable low-poly **player character** (body shape, head, hair, clothes, colors) built in Houdini on a skeleton that works with Unreal's animations, so the hero matches the world. It needs rigging and animation, so it gets its own month.
