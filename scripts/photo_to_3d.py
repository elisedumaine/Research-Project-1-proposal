"""Photo -> 3D model with TripoSR (local AI, runs on the NVIDIA card).

    photo3d/venv/Scripts/python.exe scripts/photo_to_3d.py photo.jpg out.obj

Removes the photo's background, lets TripoSR guess the object's 3D shape and
colors, and writes an OBJ with vertex colors.  Low-Polify then turns it into
the kit's style.  The first run downloads the TripoSR weights (~1.7 GB) and
the background-removal model (~170 MB) into the user's cache.
"""
import argparse
import os
import sys
import time

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KIT, "photo3d", "TripoSR"))

import numpy as np  # noqa: E402
import rembg  # noqa: E402
import torch  # noqa: E402
from PIL import Image  # noqa: E402

from tsr.system import TSR  # noqa: E402
from tsr.utils import remove_background, resize_foreground  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("image")
    parser.add_argument("output")
    parser.add_argument("--resolution", type=int, default=256, help="marching cubes grid (detail of the raw shape)")
    parser.add_argument("--keep-background", action="store_true", help="the photo already has a plain background")
    args = parser.parse_args()

    start = time.time()
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    print("device:", device, flush=True)
    model = TSR.from_pretrained("stabilityai/TripoSR", config_name="config.yaml", weight_name="model.ckpt")
    model.renderer.set_chunk_size(8192)
    model.to(device)

    image = Image.open(args.image)
    if args.keep_background:
        image = image.convert("RGB")
    else:
        image = remove_background(image, rembg.new_session())
        image = resize_foreground(image, 0.85)
        pixels = np.array(image).astype(np.float32) / 255.0
        pixels = pixels[:, :, :3] * pixels[:, :, 3:4] + (1 - pixels[:, :, 3:4]) * 0.5
        image = Image.fromarray((pixels * 255.0).astype(np.uint8))
    image.save(os.path.splitext(args.output)[0] + "_input.png")

    with torch.no_grad():
        codes = model([image], device=device)
    mesh = model.extract_mesh(codes, True, resolution=args.resolution)[0]
    # TripoSR builds the object Z up; the kit (Houdini, Low-Polify) is Y up.
    mesh.apply_transform(np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0], [0, 0, 0, 1]], dtype=float))
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    mesh.export(args.output)
    print("saved %s: %d faces in %.1fs" % (args.output, len(mesh.faces), time.time() - start), flush=True)


if __name__ == "__main__":
    main()
