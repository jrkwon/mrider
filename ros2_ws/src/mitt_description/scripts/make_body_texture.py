# Copyright 2026 Jaerock Kwon
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

r"""
Generate the MITT body texture from the mesh's own geometry.

    python3 scripts/make_body_texture.py meshes/mitt_body.obj \\
                                         meshes/mitt_body_texture.png

WHY GENERATED RATHER THAN PAINTED
---------------------------------
The upstream Fuel model ships a 736 kB photographic texture, but it is a
photographic HUMMER H2 skin - grille, badges, chrome - and this mesh only
stands in for a Land Rover Defender-style 12 V ride-on. Painting one real
vehicle's bodywork onto a proxy for a different vehicle asserts something that
is not true, which is the one thing this repository tries hard not to do.

WHY PER-TEXEL AND NOT PER-FACE
------------------------------
Each texel's 3D position and normal are recovered by barycentric interpolation
across the face that owns it, and the colour follows from those. Registration
is therefore exact by construction, and boundaries land mid-face instead of
being quantised to whole triangles.

That is not gold-plating. This is a 1210-face proxy with NO lamp geometry:
upstream painted the headlights into its photographic texture rather than
modelling them, so the entire front is one flat fascia. A per-face rule cannot
put a lamp on part of a slab - the first attempt here painted the whole front
cream and the whole rear red, which looked absurd. Per-texel places them
properly.

HOW THE THRESHOLDS WERE CHOSEN
------------------------------
Not guessed. Surface area was profiled by height band and normal direction
across all 1210 faces, and the body's structure fell out of the numbers:

    z band   side-facing   up-facing     reads as
    1.0         0.045        0.486       roof
    0.8-0.9     0.759        0.009       greenhouse (glass)
    0.6-0.7     0.396        0.243       beltline / bonnet
    0.3-0.5     1.426        0.061       body paint
    0.1-0.2     0.653        0.052       lower trim, bumpers, arches

The cut points below sit in the gaps between those bands. Lamp boxes were sized
against the measured fascia extents, quoted at their definition.

KNOWN SIMPLIFICATION
--------------------
A- and B-pillars sit inside the glass band and are painted AS glass. Separating
them needs UV-island analysis rather than a height threshold, and at the scale
this vehicle is viewed the band still reads correctly as a greenhouse. Recorded
here and in README.md rather than left to be discovered.
"""
import sys

import numpy as np
from PIL import Image, ImageFilter

# Texture is square; the UV atlas is normalised to [0,1].
SIZE = 1024
# Pixels of edge bleed, so bilinear filtering cannot sample background through
# a seam at grazing angles.
DILATE = 6

# --- Classification cut points, from the area profile in the docstring -------
Z_ROOF = 0.95        # above this, and facing up
Z_GLASS_LO = 0.72    # greenhouse floor
Z_GLASS_HI = 0.95
Z_TRIM = 0.28        # below this is bumper / sill / arch
N_VERTICAL = 0.5     # |n_z| under this counts as a wall rather than a surface

# Lamp boxes, in mesh space. +X IS FORWARD: the upstream -90 deg Z rotation is
# baked into the mesh (see extract_body.py), so this is safe to rely on.
# Without lamps the vehicle has no readable orientation, which is the single
# most useful thing this texture buys a student staring at RViz.
#
# Bounds measured from the fascia rather than invented: front-facing geometry
# spans |y| <= 0.412 with z in [0.113, 0.586]; rear-facing spans |y| <= 0.430.
# The lamps sit outboard so the grille centre stays body colour, and above
# Z_TRIM so they are not half-buried in the black bumper.
N_ALONG_X = 0.70     # |n_x| above this counts as facing fore/aft
HEADLIGHT = dict(x_min=0.44, y_lo=0.20, y_hi=0.40, z_lo=0.31, z_hi=0.41)
TAILLIGHT = dict(x_min=0.44, y_lo=0.20, y_hi=0.42, z_lo=0.31, z_hi=0.43)

PALETTE = {
    'body': (198, 202, 208),        # light grey-blue paint
    'roof': (208, 212, 218),        # lighter, so the roof reads separately
    'glass': (44, 54, 68),          # dark blue-grey
    'trim': (32, 34, 38),           # near-black bumpers and arches
    'headlight': (245, 240, 215),   # warm white, front
    'taillight': (170, 38, 38),     # red, rear
}
# Unmapped atlas space. Never sampled in practice, but a body-coloured
# background fails safe if a seam ever reaches it.
BACKGROUND = PALETTE['body']


def load_obj(path):
    """Return (vertices, uvs, faces) where each face is a list of (vi, ti)."""
    verts, uvs, faces = [], [], []
    for line in open(path):
        parts = line.split()
        if not parts:
            continue
        if parts[0] == 'v':
            verts.append(tuple(float(x) for x in parts[1:4]))
        elif parts[0] == 'vt':
            uvs.append(tuple(float(x) for x in parts[1:3]))
        elif parts[0] == 'f':
            face = []
            for chunk in parts[1:]:
                bits = chunk.split('/')
                vi = int(bits[0])
                ti = int(bits[1]) if len(bits) > 1 and bits[1] else 0
                face.append((vi, ti))
            faces.append(face)
    return verts, uvs, faces


def face_normal(verts, face):
    a, b, c = (np.array(verts[i - 1]) for i, _ in face[:3])
    n = np.cross(b - a, c - a)
    length = np.linalg.norm(n)
    return n / length if length else np.array([0.0, 0.0, 1.0])


def classify(x, y, z, nx, nz):
    """
    Palette key for ONE POINT on the surface, from its position and normal.

    Vectorised: x/y/z/nx/nz are arrays, and the return is an integer index
    array into PALETTE_ORDER.
    """
    out = np.full(x.shape, KIND_INDEX['body'], dtype=np.uint8)

    # Painted in precedence order, least specific first.
    out[z <= Z_TRIM] = KIND_INDEX['trim']
    glass = (z > Z_GLASS_LO) & (z <= Z_GLASS_HI) & (np.abs(nz) < N_VERTICAL)
    out[glass] = KIND_INDEX['glass']
    out[(z > Z_ROOF) & (nz > N_VERTICAL)] = KIND_INDEX['roof']

    # Lamps last: a small specific region the body default would swallow.
    facing = np.abs(nx) > N_ALONG_X
    for kind, box, side in (('headlight', HEADLIGHT, x > 0),
                            ('taillight', TAILLIGHT, x < 0)):
        hit = (facing & side
               & (np.abs(x) > box['x_min'])
               & (np.abs(y) >= box['y_lo']) & (np.abs(y) <= box['y_hi'])
               & (z >= box['z_lo']) & (z <= box['z_hi']))
        out[hit] = KIND_INDEX[kind]
    return out


PALETTE_ORDER = ['body', 'roof', 'glass', 'trim', 'headlight', 'taillight']
KIND_INDEX = {k: i for i, k in enumerate(PALETTE_ORDER)}
PALETTE_RGB = np.array([PALETTE[k] for k in PALETTE_ORDER], dtype=np.uint8)


def rasterise(verts, uvs, faces):
    """Rasterise every face's UV triangle, classifying per texel."""
    idx = np.full((SIZE, SIZE), KIND_INDEX['body'], dtype=np.uint8)
    covered = np.zeros((SIZE, SIZE), dtype=bool)
    counts = np.zeros(len(PALETTE_ORDER), dtype=np.int64)

    for face in faces:
        if any(ti == 0 for _, ti in face):
            continue
        # Fan-triangulate: these are triangles already, but be tolerant.
        for k in range(1, len(face) - 1):
            tri = [face[0], face[k], face[k + 1]]
            p3 = np.array([verts[vi - 1] for vi, _ in tri])       # 3x3
            # OBJ v runs bottom-up; image rows run top-down.
            p2 = np.array([[uvs[ti - 1][0] * (SIZE - 1),
                            (1.0 - uvs[ti - 1][1]) * (SIZE - 1)] for _, ti in tri])
            n = face_normal(verts, tri)

            lo = np.floor(p2.min(axis=0)).astype(int)
            hi = np.ceil(p2.max(axis=0)).astype(int)
            lo = np.clip(lo, 0, SIZE - 1)
            hi = np.clip(hi, 0, SIZE - 1)
            if hi[0] < lo[0] or hi[1] < lo[1]:
                continue

            xs = np.arange(lo[0], hi[0] + 1)
            ys = np.arange(lo[1], hi[1] + 1)
            gx, gy = np.meshgrid(xs, ys)

            # Barycentric coordinates in UV space.
            (x1, y1), (x2, y2), (x3, y3) = p2
            det = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3)
            if abs(det) < 1e-12:
                continue
            l1 = ((y2 - y3) * (gx - x3) + (x3 - x2) * (gy - y3)) / det
            l2 = ((y3 - y1) * (gx - x3) + (x1 - x3) * (gy - y3)) / det
            l3 = 1.0 - l1 - l2
            eps = -1e-9
            inside = (l1 >= eps) & (l2 >= eps) & (l3 >= eps)
            if not inside.any():
                continue

            # Interpolate the 3D surface point for every covered texel.
            px = l1 * p3[0, 0] + l2 * p3[1, 0] + l3 * p3[2, 0]
            py = l1 * p3[0, 1] + l2 * p3[1, 1] + l3 * p3[2, 1]
            pz = l1 * p3[0, 2] + l2 * p3[1, 2] + l3 * p3[2, 2]

            kinds = classify(px[inside], py[inside], pz[inside],
                             np.full(inside.sum(), n[0]),
                             np.full(inside.sum(), n[2]))
            rows = gy[inside]
            cols = gx[inside]
            idx[rows, cols] = kinds
            covered[rows, cols] = True
            np.add.at(counts, kinds, 1)

    return idx, covered, counts


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else 'meshes/mitt_body.obj'
    dst = sys.argv[2] if len(sys.argv) > 2 else 'meshes/mitt_body_texture.png'

    verts, uvs, faces = load_obj(src)
    if not uvs:
        sys.exit(f'error: {src} carries no UV coordinates; cannot texture it')

    idx, covered, counts = rasterise(verts, uvs, faces)
    rgb = PALETTE_RGB[idx]
    rgb[~covered] = BACKGROUND

    img = Image.fromarray(rgb, mode='RGB')

    # Dilate: grow the painted islands outward so a seam samples paint rather
    # than background. Composite so island interiors stay exactly as drawn.
    mask = Image.fromarray((covered * 255).astype(np.uint8), mode='L')
    grown = img.filter(ImageFilter.MaxFilter(2 * DILATE + 1))
    grown_mask = mask.filter(ImageFilter.MaxFilter(2 * DILATE + 1))
    out = Image.composite(img, Image.composite(grown, img, grown_mask), mask)

    out.save(dst, optimize=True)

    total = int(counts.sum())
    print(f'{dst}: {SIZE}x{SIZE}, {len(faces)} faces, '
          f'{covered.sum()} texels covered ({100 * covered.mean():.1f}%)')
    for i in np.argsort(-counts):
        if counts[i]:
            kind = PALETTE_ORDER[i]
            print(f'  {kind:10s} {100 * counts[i] / total:5.1f}% of surface  '
                  f'rgb{PALETTE[kind]}')


if __name__ == '__main__':
    main()
