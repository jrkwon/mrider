# MITT meshes

## `mitt_body.obj` — vehicle body shell

**Provenance.** Derived from the **"SUV"** model by **Open Robotics** on Gazebo Fuel,
<https://app.gazebosim.org/OpenRobotics/fuel/models/SUV>, released under
**CC0 1.0 Universal** (public domain dedication). CC0 requires no attribution; it is
recorded anyway, and it is why this model was chosen over better-looking alternatives with
`NonCommercial` or `NoDerivatives` terms — the same reasoning that picked the Depot world
(see `mitt_sim/worlds/depot.sdf`).

**Why this model.** The source is a Hummer H2: boxy, upright, flat-roofed, with squared
wheel arches. The MITT donor vehicle is a Land Rover Defender–style 12 V ride-on, which has
the same silhouette. Body proportions are L : W : H = 1 : 0.52 : 0.37 against the donor's
1 : 0.57 : 0.48, so it scales down without looking stretched.

**It is a visual proxy, not a scan.** It is not the donor vehicle, and no dimension in the
project is derived from it. All geometry still comes from `config/mitt_dimensions.yaml`.

### What was changed, and why

Regenerate with:

```bash
python3 scripts/extract_body.py <fuel-cache>/suv/4/meshes/suv.obj meshes/mitt_body.obj
```

1. **Wheels removed.** The source carries `Wheel_Front_Left`, `Wheel_Front_Right` and
   `Wheel_Rear` groups. MITT's URDF has its own four wheel links that steer and roll; baked-in
   wheels would double-render and sit frozen while the real ones turned.

2. **The upstream −90° Z rotation is baked in** so +X is forward (ROS convention). This has to
   be baked rather than left to the URDF `<origin rpy>`: URDF applies `<scale>` in the *mesh*
   frame, before the origin transform, so with a rotation still pending a non-uniform
   `scale` on X would stretch the vehicle's **width** instead of its length. Baking removes
   that trap.

3. **Normalised to a unit bounding box** — span 1.0 per axis, centred on X/Y, resting on
   Z = 0. This is the useful part: the URDF `<scale>` is then literally the vehicle's size in
   metres, fed straight from `mitt_dimensions.yaml`. The mesh keeps tracking those numbers
   when they are finally *measured*, with no geometric literals anywhere.

### Collision is still a box

The mesh is used for **visual only**. Collision and inertia remain the primitive box in
`mitt_base.xacro`. Mesh collision would cost physics time for no benefit — and worse, it
would silently change the vehicle's collision envelope whenever the mesh was swapped,
decoupling physics from the documented dimensions.

### No texture — flat colour instead

The upstream model ships a 753 kB photographic body texture. It was tried both beside the
mesh and under `materials/textures/` (the gz convention), and **rendered in neither**: gz-sim
loads the mesh without any warning and simply draws it untextured. Rather than carry a
three-quarter-megabyte asset that does not draw, the body is a flat colour defined in
`mitt_body.mtl` and restated as a `<material>` in the URDF, so Gazebo and RViz agree.

That is also the more honest picture. The texture is a photographic *Hummer* skin, and this
mesh only stands in for a Defender-style ride-on — grille and badge detail would have been
actively misleading on a vehicle that is not that. The whole package is now 124 kB.
