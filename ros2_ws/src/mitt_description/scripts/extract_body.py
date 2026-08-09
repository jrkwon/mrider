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

"""
Extract the body of the Fuel SUV mesh into a normalised, ROS-oriented OBJ.

Three transformations happen here, all deliberate:

1. DROP THE WHEELS. The source mesh carries Wheel_Front_Left, Wheel_Front_Right
   and Wheel_Rear groups. MITT's URDF has its own four wheel links that steer
   and roll, so baked-in wheels would double-render and sit frozen while the
   real ones turned.

2. BAKE THE -90 deg Z ROTATION that the upstream model.sdf applies via <pose>.
   After baking, +X is forward, matching ROS convention. This must be baked
   rather than left to the URDF <origin rpy>, because URDF applies <scale> in
   the MESH frame before the origin transform - so with a rotation still
   pending, a non-uniform scale_x would stretch the vehicle's WIDTH, not its
   length. Baking removes that trap entirely.

3. NORMALISE TO A UNIT BOX: span 1.0 on each axis, centred on X/Y, resting on
   Z=0. The payoff is that the URDF <scale> then IS the vehicle's dimensions,
   so the mesh can be driven straight from mitt_dimensions.yaml and keeps
   tracking those values when they are finally measured. No geometric literals.
"""
import sys

SRC = sys.argv[1]
DST = sys.argv[2]
KEEP_GROUP = 'SUV'          # body only

verts, texs, norms = [], [], []
faces = []                  # (v,vt,vn) triples, 1-based into the lists above
keeping = False

for line in open(SRC):
    parts = line.split()
    if not parts:
        continue
    tag = parts[0]
    if tag == 'v':
        verts.append(tuple(float(x) for x in parts[1:4]))
    elif tag == 'vt':
        texs.append(tuple(float(x) for x in parts[1:3]))
    elif tag == 'vn':
        norms.append(tuple(float(x) for x in parts[1:4]))
    elif tag == 'g':
        keeping = (len(parts) > 1 and parts[1] == KEEP_GROUP)
    elif tag == 'f' and keeping:
        tri = []
        for tok in parts[1:]:
            bits = (tok.split('/') + ['', ''])[:3]
            tri.append(tuple(int(b) if b else 0 for b in bits))
        faces.append(tri)

print(f'source: {len(verts)} verts, kept {len(faces)} faces from group {KEEP_GROUP}')
if not faces:
    sys.exit('no faces kept - group name wrong?')

# --- 2. bake the -90 deg rotation about Z: (x, y) -> (y, -x) ----------------
rot = [(y, -x, z) for (x, y, z) in verts]
rotn = [(y, -x, z) for (x, y, z) in norms]

used_v = sorted({t[0] for f in faces for t in f if t[0]})
xs = [rot[i - 1][0] for i in used_v]
ys = [rot[i - 1][1] for i in used_v]
zs = [rot[i - 1][2] for i in used_v]
span = (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))
print(f'body bbox after rotation: L {span[0]:.3f}  W {span[1]:.3f}  H {span[2]:.3f}')
print(f'  proportions L:W:H = 1 : {span[1] / span[0]:.3f} : {span[2] / span[0]:.3f}')

cx = (max(xs) + min(xs)) / 2.0
cy = (max(ys) + min(ys)) / 2.0
z0 = min(zs)


def norm_v(p):
    """Centre on X/Y, rest on Z=0, then divide each axis by its own span."""
    return ((p[0] - cx) / span[0], (p[1] - cy) / span[1], (p[2] - z0) / span[2])


# --- remap to a compact index space ----------------------------------------
vmap, tmap, nmap = {}, {}, {}
out_v, out_t, out_n = [], [], []
for f in faces:
    for (vi, ti, ni) in f:
        if vi and vi not in vmap:
            out_v.append(norm_v(rot[vi - 1]))
            vmap[vi] = len(out_v)
        if ti and ti not in tmap:
            out_t.append(texs[ti - 1])
            tmap[ti] = len(out_t)
        if ni and ni not in nmap:
            out_n.append(rotn[ni - 1])
            nmap[ni] = len(out_n)

with open(DST, 'w') as fh:
    fh.write('# MITT body shell.\n')
    fh.write('# Derived from the Gazebo Fuel "SUV" model by Open Robotics (CC0 1.0,\n')
    fh.write('# public domain). Wheels removed, -90deg Z rotation baked in so +X is\n')
    fh.write('# forward, and normalised to a UNIT bounding box: the URDF <scale> is\n')
    fh.write('# therefore the vehicle size in metres, fed from mitt_dimensions.yaml.\n')
    fh.write('# Regenerate with scripts/extract_body.py - see mitt_description/meshes/README.md\n')
    fh.write('mtllib mitt_body.mtl\n')
    fh.write('o mitt_body\n')
    for p in out_v:
        fh.write(f'v {p[0]:.6f} {p[1]:.6f} {p[2]:.6f}\n')
    for t in out_t:
        fh.write(f'vt {t[0]:.6f} {t[1]:.6f}\n')
    for n in out_n:
        fh.write(f'vn {n[0]:.6f} {n[1]:.6f} {n[2]:.6f}\n')
    fh.write('usemtl mitt_body\n')
    for f in faces:
        toks = []
        for (vi, ti, ni) in f:
            toks.append(f'{vmap[vi]}/{tmap.get(ti, "")}/{nmap.get(ni, "")}'
                        .rstrip('/') if ni or ti else str(vmap[vi]))
        fh.write('f ' + ' '.join(toks) + '\n')

print(f'wrote {DST}: {len(out_v)} verts, {len(faces)} faces')
