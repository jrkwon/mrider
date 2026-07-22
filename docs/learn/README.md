# MRider Learn Curriculum

A RoboRacer-style coursekit that teaches autonomous-vehicle fundamentals on the MRider
platform. The modules run **in order**: each builds on the previous one, from a first ROS 2
node to an autonomous lap. Every module lists its learning objectives, a hands-on lab, and
the design document that grounds the theory in the real vehicle.

> Status: **skeleton**. Lecture notes, slides, and lab handouts are `TODO` and will be
> authored during the build/teaching phase. The linked design documents are the technical
> reference each module draws on.

**Audience:** upper-year undergraduates and early graduate students, or self-learners with
some Python. **Format:** short lecture + guided lab per module. **Prerequisites for the
course:** basic Python and Linux; no robotics background assumed.

---

## M1 — Intro to MRider & ROS 2

**Learning objectives:**
- Explain what drive-by-wire is and how MRider is architected end to end.
- Navigate a ROS 2 Humble workspace; understand nodes, topics, and TF.
- Trace the command and feedback paths through the system block diagram.

**Lab idea:** write a ROS 2 node that publishes to `/mrider/cmd` and echoes
`/mrider/feedback`; visualize the TF tree in RViz.

**Reference:** [design/architecture.md](../../design/architecture.md)

`TODO:` lecture, slides, lab handout.

## M2 — Drive-by-wire & the smart-servo steering loop

**Learning objectives:**
- Understand closed-loop position control and why the steering loop lives on the Nano.
- Follow the pinned datapath: `MANUAL_CONTROL.roll` → PX4 servo-PWM → Nano → Sabertooth S1.
- Read an absolute angle sensor and convert sensor counts to steering degrees.

**Lab idea:** command the bench steering rig to a target angle and plot the closed-loop
step response; measure settling time and steady-state error.

**Reference:** [design/dbw.md](../../design/dbw.md)

`TODO:` lecture, slides, lab handout.

## M3 — Manual/teleop control & safety

**Learning objectives:**
- Reason about control authority, RC override, and the relay-MUX arbitration.
- Interpret a failsafe matrix and E-stop semantics.
- Run a safe wheels-off bring-up before any powered driving.

**Lab idea:** drive by joystick and RC; deliberately trigger heartbeat-loss and RC-loss
failsafes on the bench and confirm each specified behavior.

**Reference:** [design/safety.md](../../design/safety.md)

`TODO:` lecture, slides, lab handout.

## M4 — Perception (camera + 2D LiDAR)

**Learning objectives:**
- Understand camera and 2D LiDAR sensing: fields of view, rates, and coordinate frames.
- Bring up the sensor drivers in ROS 2 and inspect the data in RViz.
- Relate raw sensor data to the vehicle base frame via extrinsics.

**Lab idea:** record a rosbag while driving manually; replay it and overlay the LiDAR scan
and camera image; identify obstacles.

**Reference:** [design/sensors.md](../../design/sensors.md)

`TODO:` lecture, slides, lab handout.

## M5 — Localization & SLAM

**Learning objectives:**
- Explain odometry from wheel encoders and its fusion with IMU (EKF).
- Understand simultaneous localization and mapping with slam_toolbox.
- Diagnose drift and evaluate map quality.

**Lab idea:** drive a loop and build a map with slam_toolbox; compare odometry-only vs.
EKF-fused trajectories.

**Reference:** [design/calibration.md](../../design/calibration.md)

`TODO:` lecture, slides, lab handout.

## M6 — Navigation (Nav2)

**Learning objectives:**
- Understand the Nav2 stack: costmaps, planners, and controllers.
- Configure Ackermann-appropriate parameters (wheelbase, track, steer range).
- Send navigation goals and tune for a car-like platform.

**Lab idea:** set navigation goals on a saved map and have MRider drive to them; tune the
controller to reduce overshoot on turns.

**Reference:** [design/software.md](../../design/software.md)

`TODO:` lecture, slides, lab handout.

## M7 — Behavior cloning / end-to-end driving

**Learning objectives:**
- Understand imitation learning and end-to-end driving (mrover `neural_net/` lineage).
- Collect and curate a driving dataset; train and evaluate a model.
- Compare modular (Nav2) vs. learned (end-to-end) control.

**Lab idea:** collect data on a course, train a behavior-cloning model, and deploy it for
inference; measure lap completion.

**Reference:** [design/software.md](../../design/software.md)

`TODO:` lecture, slides, lab handout.

## M8 — Capstone: autonomous lap

**Learning objectives:**
- Integrate perception, localization, navigation, and/or learned control into one run.
- Plan, execute, and debug a full autonomous lap.
- Present results with metrics and a reproducible procedure.

**Lab idea:** complete an autonomous lap of a test course using the stack of your choice;
document configuration, failures, and lap time.

**Reference:** [design/architecture.md](../../design/architecture.md)

`TODO:` capstone brief, rubric, demo-day checklist.

---

## See also

- [Design overview & document index](../../design/overview.md)
- [Build guide](../build/README.md)
