# Running the Digital Twin

**Goal:** bring up the simulated MITT, map an indoor world with SLAM, and send it a
navigation goal — with no hardware at all.

This is **Track A** of the semester roadmap
([software.md §8](design/software.md#8-semester-1-scope-and-software-acceptance-gates)). It
runs on a laptop while the vehicle is still being procured, and the controller stack it
launches is the *same* one the real vehicle will use — only the `ros2_control` hardware
plugin differs ([ADR-SW4](design/software.md#7-software-adr-summary)).

!!! success "Verified working"

    Every command here has been run end to end: both controllers activate, `slam_toolbox`
    maps the depot world, and Nav2 drives a ~13 m goal to completion. Where something is
    known to be broken it says so explicitly rather than being left out.

---

## 0. Prerequisites

A built workspace. If you have not built yet, see
[build/05 — Software Install](build/05-software.md).

```bash
cd ~/projects/mrider/ros2_ws
colcon build
```

---

## 1. Source the environment — in *every* terminal

```bash
cd /path/to/mrider/ros2_ws
source setup_env.sh
```

You should see:

```
MITT env: RMW=rmw_fastrtps_cpp, GZ_VERSION=harmonic, user-site disabled
```

!!! danger "This is the step that costs people an afternoon"

    `setup_env.sh` forces `RMW_IMPLEMENTATION=rmw_fastrtps_cpp`, overriding the CycloneDDS
    default in `~/.bashrc`
    ([why](design/software.md#621-rmw-use-fastrtps-not-cyclonedds-open-issue)).

    The failure mode if you forget it in **one** terminal is nasty precisely because nothing
    errors: two DDS implementations do not see each other, so `ros2 topic list` comes back
    almost empty and the simulator looks **dead** while it is running perfectly. You will
    debug the simulator instead of the shell.

    Source it everywhere, every time.

---

## 2. Launch, in order

Four terminals. The order matters: SLAM needs the simulator's clock and scan, and Nav2 needs
SLAM's `map → odom`.

=== "1. Simulator"

    ```bash
    ros2 launch mitt_bringup sim.launch.py
    ```

    **Wait ~80 s.** Ready when the log shows:

    ```
    Configured and activated joint_state_broadcaster
    Configured and activated ackermann_steering_controller
    ```

    Add `gz_args:="-r -s"` to run headless — faster, and the configuration the SLAM results
    were validated against.

=== "2. SLAM"

    ```bash
    ros2 launch mitt_navigation slam.launch.py
    ```

    Starts `slam_toolbox` in mapping mode. It owns `map → odom`; the EKF owns
    `odom → base_link`.

=== "3. Nav2"

    ```bash
    ros2 launch mitt_navigation nav2.launch.py
    ```

    **Wait ~45 s.** Ready when the log shows `Managed nodes are active`.

=== "4. RViz"

    ```bash
    rviz2 -d /opt/ros/humble/share/nav2_bringup/rviz/nav2_default_view.rviz \
      --ros-args -p use_sim_time:=true
    ```

    The repo ships no RViz config of its own yet, so this borrows Nav2's stock view.

!!! note "Two harmless things RViz will show you"

    **`Localization: inactive`** in the Navigation 2 panel is correct. That panel watches
    AMCL; we run `slam_toolbox` instead. `Navigation: active` is the one that matters.

    **Three displays never populate** — Amcl Particle Swarm, RealsenseCamera, Bumper Hit.
    They belong to Nav2's example robot, not this one.

---

## 3. Drive first — SLAM starts with a blank map

This is the step that is easy to skip and guarantees confusion if you do. `slam_toolbox`
begins with **nothing mapped**, so Nav2 has no free space to plan through and every goal
fails to plan. Drive a lap or two before asking it to navigate.

=== "With a gamepad"

    ```bash
    ros2 launch mitt_control teleop.launch.py
    ```

    **Hold LB (button 4) as a deadman** — nothing moves without it, deliberately mirroring
    the real vehicle's philosophy that motion requires a human actively holding something
    ([safety.md §1.2](design/safety.md#12-live-override-inside-dbw-mode-two-layers)).

    | Control | Action |
    |---|---|
    | **LB** (button 4) | deadman — hold to enable |
    | **RB** (button 5) | turbo (0.5 → 1.0 m/s) |
    | Left stick ↑↓ (axis 1) | throttle |
    | Right stick ←→ (axis 3) | steering |

    Mapping assumes an Xbox-style layout. For a different pad, read `ros2 topic echo /joy`
    and override the `*_button` / `axis_*` parameters.

=== "Without a gamepad"

    Publish to the same topic the joystick uses — it enters `twist_mux` at joystick priority,
    so it outranks Nav2 exactly as a human would:

    ```bash
    # forward-left arc; Ctrl-C to stop
    ros2 topic pub -r 20 /cmd_vel_joy geometry_msgs/msg/Twist \
      "{linear: {x: 0.6}, angular: {z: 0.25}}"
    ```

    Always send a zero afterwards, or the last command persists:

    ```bash
    ros2 topic pub -r 20 /cmd_vel_joy geometry_msgs/msg/Twist \
      "{linear: {x: 0.0}, angular: {z: 0.0}}"
    ```

Watch the map fill in RViz. **50–60 % coverage is plenty** to navigate in.

---

## 4. Send a goal

Click **2D Goal Pose** in the RViz toolbar, then click and drag to set position and heading.

Or from the command line:

```bash
timeout 12 ros2 topic pub -r 2 /goal_pose geometry_msgs/msg/PoseStamped \
  "{header: {frame_id: map}, pose: {position: {x: 7.9, y: 1.2, z: 0.0},
    orientation: {w: 1.0}}}"
```

Success looks like this in the Nav2 terminal:

```
[bt_navigator]: Goal succeeded
```

!!! warning "`--once` does not work here, and fails silently"

    `ros2 topic pub --once /goal_pose ...` publishes and exits before DDS discovery
    completes, so the goal is **dropped with no error, no warning, and no log line** — the
    vehicle simply sits there. Use `-r 2` under a `timeout`, or the RViz button.

    Related: **`ros2 action send_goal /navigate_to_pose` hangs**, with the server never
    logging receipt. Unresolved, possibly sharing a root cause with the RMW issue above.
    `/goal_pose` is the supported path.

!!! note "It stops ~0.5 m short and calls that success"

    `xy_goal_tolerance` is **0.6 m**, which looks sloppy and is not. At a 1.52 m minimum
    turning radius, with no in-place rotation, a tighter tolerance is physically unreachable:
    the vehicle can only loop past the goal and try again. Tightening it does not improve
    accuracy, it produces an infinite orbit — which is exactly what the first test did
    ([software.md §4.4](design/software.md#44-nav2-bring-up-in-the-twin-result-2026-08-08)).

---

## 5. Save the map

```bash
ros2 run nav2_map_server map_saver_cli \
  -f src/mitt_navigation/maps/depot --ros-args -p use_sim_time:=true
```

Writes `depot.pgm` + `depot.yaml`. When reading the PGM, note the thresholds:
**254 = free, 205 = unknown, 0 = occupied** — counting 205 as free reports a suspiciously
well-explored map.

---

## 6. Shutting down

`Ctrl-C` each terminal in reverse order (Nav2 → SLAM → sim). Then confirm nothing survived:

```bash
pgrep -af "gz sim|ros2 launch"
```

!!! danger "Never leave two simulators running"

    Orphaned instances are the single most confusing failure in this stack. Each publishes
    its own `/clock` and `/scan`, so subscribers receive **interleaved clocks from different
    simulations**. The symptom is `Detected jump back in time`, frozen TF, and controllers
    that will not activate — all of which look like bugs in the twin.

    If anything behaves strangely, check this first:

    ```bash
    pgrep -af "gz sim" | wc -l     # must be 1 while running, 0 when stopped
    ros2 topic info /clock         # Publisher count must be 1
    ```

    Clean up with `pkill -f "gz sim"` and start again.

---

## What this cannot tell you

The twin is a software development vehicle. It deliberately does **not** model backlash in
the steering gearbox, encoder noise and quantisation, USB latency and jitter, motor stall, or
tyre slip on a real floor. Those belong to Track B and the
[bench tests](build/06-bench-test.md).

A policy that works here is not validated. It is *ready to be tested* on hardware.
