# Lab 4 — Describe the Robot

**Week 4 · 9/28 · due before Week 6 (10/12)**

URDF, Xacro, and TF2 — how a robot knows the shape of itself, and what goes wrong when it is wrong
about that.

You will add a sensor to MRider's description, watch it appear in the transform tree and in RViz, and
then move it a few centimetres and see how thoroughly that ruins everything downstream.

!!! note "Two weeks for this one"

    Week 5 (10/5) has no class — 개천절 대체공휴일. Lab 4 and [Lab 5](lab5.md) are both due 10/12, and
    you have the intervening two weeks for them.

| | |
|---|---|
| **Time** | ~90 minutes |
| **Prerequisite** | Lab 3 complete |
| **Reading** | *Zero to Robot* ch. 4–6 · [calibration.md §4](../../design/calibration.md) |

---

## Part 1 — Read the description you already have

```bash
cd ~/mrider/ros2_ws/src/mitt_description
ls urdf/ config/
```

Five xacro files, and one YAML. Open `config/mitt_dimensions.yaml` and read its header:

```
NOTHING IN THIS FILE HAS BEEN MEASURED.
Every value is an ESTIMATE derived from the vendor's published overall dimensions...
```

That is not an apology. It is a **design decision**, and it is why the URDF contains no literal
numbers: every dimension is read from this one file, so measured values can drop in without anyone
touching geometry. The Chassis track will replace these numbers in November, and nothing else will
need to change.

Expand the description to plain URDF and look at what xacro produced:

```bash
cd ~/mrider/ros2_ws && source setup_env.sh
xacro src/mitt_description/urdf/mitt.urdf.xacro > /tmp/mitt.urdf
wc -l /tmp/mitt.urdf src/mitt_description/urdf/*.xacro
```

**Expected output:** the expanded URDF is several times longer than the xacro sources. That ratio is
what xacro buys you.

Answer in your submission:

1. `wheelbase` appears in `mitt_dimensions.yaml`. Find **every** place it influences the expanded
   URDF. (`grep` the expanded file for the value.)
2. `base_link_height` is `0.09`, and so is `wheel_radius`. Read the comment. Why is that not a
   coincidence, and where is `base_link` physically located on the vehicle?

---

## Part 2 — Look at the transform tree

Launch the simulator, then:

```bash
ros2 run tf2_tools view_frames
```

This writes `frames.pdf` in your current directory. Open it.

```bash
ros2 run tf2_ros tf2_echo base_link laser_link --ros-args -p use_sim_time:=true
```

!!! warning "`use_sim_time:=true` is not optional here"

    Without it, `tf2_echo` uses wall-clock time while every transform in the system is stamped with
    *simulation* time. The two never line up and you get a stream of extrapolation errors that look
    like a broken TF tree. This costs people an hour the first time.

Record the translation and rotation from `base_link` to `laser_link`.

Answer:

3. Which node publishes the `base_link → laser_link` transform, and which publishes
   `odom → base_link`? Why are those two different nodes?
4. Is `base_link → laser_link` static or dynamic? How can you tell from the data alone?

---

## Part 3 — Add a rear-facing camera

MRider has one forward camera on the mast. Add a second, rear-facing one — the kind of thing you
would want for reversing, which this vehicle does a lot of.

Edit `urdf/mitt_sensors.xacro`. Follow the pattern the forward camera already uses:

```xml
<!-- ==== Rear camera (Lab 4) ============================================ -->
<link name="rear_camera_link">
  <visual>
    <geometry><box size="0.025 0.09 0.025"/></geometry>
    <material name="mast_grey"/>
  </visual>
</link>

<joint name="rear_camera_joint" type="fixed">
  <parent link="base_link"/>
  <child link="rear_camera_link"/>
  <!-- Behind the rear axle, at roofline height, looking backwards -->
  <origin xyz="-0.15 0 ${wheel_rr + body_hh*0.9}" rpy="0 0 ${pi}"/>
</joint>
```

Rebuild and relaunch:

```bash
colcon build --packages-select mitt_description --symlink-install
source setup_env.sh
ros2 launch mitt_bringup sim.launch.py
```

**Expected output:** `rear_camera_link` appears in `view_frames`, and a small box is visible at the
back of the vehicle in RViz's RobotModel display.

```bash
ros2 run tf2_ros tf2_echo base_link rear_camera_link --ros-args -p use_sim_time:=true
```

The rotation should show a yaw of π — it is pointing backwards.

!!! tip "If the link does not appear"

    Check `ros2 topic echo /robot_description --once | head -40`. If your link is not in there, xacro
    did not pick up your edit — you probably did not rebuild, or `--symlink-install` is not in effect.
    If it *is* there but not in TF, `robot_state_publisher` did not restart.

---

## Part 4 — Where sensor frames come from in reality

In simulation you typed the numbers and they became true. On the real vehicle it runs the other way:
the sensor is bolted somewhere, and you have to **measure** where.

Read [calibration.md §4](../../design/calibration.md), on camera and LiDAR extrinsics to `base_link`.

Answer:

5. What is the procedure for determining the real LiDAR's transform to `base_link`? How accurate can
   you expect to be?
6. If your measured LiDAR position is off by 3 cm in *x*, what specifically goes wrong downstream?
   Name the affected subsystem, not just "things get worse."

---

## Part 5 — Break it on purpose

Change the LiDAR's mounting position by 5 cm. In `mitt_sensors.xacro`, find the joint that parents
`laser_link` and shift its `x` origin by `+0.05`.

Rebuild, relaunch, and this time bring up mapping too:

```bash
# Terminal 2
ros2 launch mitt_navigation slam.launch.py
```

Drive the vehicle around with your Lab 2 square driver, or by publishing to `/cmd_vel_joy`. Watch the
map build in RViz.

**Expected output:** the map degrades. Walls observed from different headings no longer land on top
of each other; you get doubled or smeared walls, and the effect grows the more you turn.

Capture a screenshot of the bad map next to a good one.

Write down:

- What the failure looked like, specifically.
- Why a **constant** offset produces a **heading-dependent** error. (Think about where that 5 cm
  points as the vehicle rotates.)
- Why this is much harder to diagnose than a sensor that has simply stopped publishing.

!!! danger "This is the third silent failure, and the worst of the three"

    Nothing errors. The LiDAR publishes, TF is complete, SLAM runs, and the map is *wrong*. Every
    component reports healthy because every component **is** healthy — the system is faithfully
    computing the consequences of one bad number.

    | Lab | Failure | Symptom |
    |---|---|---|
    | 1 | `ROS_DOMAIN_ID` mismatch | Nothing visible at all |
    | 3 | QoS incompatibility | Connection silently never forms |
    | 4 | Wrong extrinsic | Everything runs, and the output is quietly wrong |

    The MRider acceptance gate for mapping is that repeated observations of the same wall agree
    within **10 cm** over a 30 m loop. Now you know what that number is defending against — and why
    the Chassis track measuring the real vehicle is not busywork.

Restore the original value before submitting.

---

## Check yourself

- [ ] I can trace `wheelbase` from the YAML into the expanded URDF
- [ ] I know where `base_link` sits on the vehicle and why
- [ ] My rear camera appears in TF and in RViz, pointing backwards
- [ ] I know why `tf2_echo` needs `use_sim_time:=true`
- [ ] I produced a visibly degraded map from a 5 cm extrinsic error
- [ ] I can explain why a constant offset causes a heading-dependent error

---

## Deliverables

| | |
|---|---|
| `mitt_sensors.xacro` | Your version with the rear camera (LiDAR restored to original) |
| `frames.pdf` | TF tree showing `rear_camera_link` |
| `lab4_tf.txt` | `tf2_echo` output for both `laser_link` and `rear_camera_link` |
| `map_good.png`, `map_broken.png` | Before and after the 5 cm error |
| `lab4_answers.md` | Questions 1–6 and the Part 5 write-up |
| — | **AI-assistance declaration** |

---

## See also

- [Lab 5 — How Tightly Can It Turn?](lab5.md) — also due 10/12
- [calibration.md](../../design/calibration.md) — the real extrinsics procedure
- [M4 — Perception](../../learn/m4-perception.md)
