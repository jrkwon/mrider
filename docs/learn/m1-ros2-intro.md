# M1 — Intro to MRider & ROS 2

**Learning objectives:**

- Explain what drive-by-wire is and how MRider is architected end to end.
- Navigate a ROS 2 Humble workspace; understand nodes, topics, and TF.
- Trace the command and feedback paths through the system block diagram.

**Reference:** [design/architecture.md](../design/architecture.md)

!!! tip "Prerequisites, and what this module assumes"

    There is **no autopilot to learn first**. The path from ROS 2 concepts to a moving vehicle
    is short: nodes and topics → micro-ROS → drive. If you have seen an older version of this
    course that opened with PX4, MAVLink, and XRCE-DDS, that layer is gone — and *why* it went
    is one of the things this module teaches.

---

## Lecture

### What drive-by-wire actually means

A stock ride-on car has a mechanical link from the steering wheel to the road wheels, and a
throttle switch wired to the motors. A human closes every loop. **Drive-by-wire** replaces
those mechanical and electrical links with a computed command: software decides an angle and
a throttle, and actuators realize them.

Three things must exist for that to work, and each is a place where the design could have
gone differently:

1. **An actuator** that can move the steering column with enough torque — and a way to know
   how much torque is "enough" without guessing.
2. **A sensor** that reports the *actual* steering angle, so the command can be checked
   against reality rather than assumed.
3. **An authority scheme** that decides who is allowed to command the motors at any instant,
   and what happens when a link dies.

The third is the one students underestimate. A vehicle that steers correctly 99% of the time
and has no defined behavior for the other 1% is not a research platform, it is a hazard.

### MRider end to end

The system has **two computers that make decisions**, plus a power stage. Being precise about
what each owns is most of the architecture:

| Where | What it owns | Why there |
|---|---|---|
| **Laptop** (ROS 2 Humble) | Perception, SLAM, Nav2, the learned policy — everything that needs a GPU or a filesystem | Runs on its own battery, so traction sag cannot reset it |
| **Teensy 4.1** (micro-ROS) | The steering position loop at ≥ 200 Hz, throttle shaping, encoder reading, SBUS decode, and the safety supervisor | A dedicated MCU has deterministic, direct access to the sensors and the motor driver |
| **Sabertooth 2x32** | Raw H-bridge power to the motors | A dumb, fast power stage — deliberately not smart |

!!! info "It used to be four computers. That is the interesting part."

    An earlier design put a **Pixhawk running PX4** between the laptop and an **Arduino Nano**
    that closed the steering loop. It was a defensible choice: PX4 is a field-tested autopilot
    that supplies RC override, failsafes, and arming for free.

    It was replaced ([D3](../design/adr-dbw-architecture-review.md#46-decision-adopted-2026-08-07))
    because a command had to cross **four boards and two protocols** to reach a wheel, and the
    feedback came back a different way entirely. A symptom you saw in ROS could have originated
    in any of four places, and no single log contained both sides of the loop.

    **The lesson is worth more than the architecture:** a design can be individually reasonable
    at every step and still be unmaintainable in aggregate. Count your interfaces, not just your
    components.

!!! info "Why the steering loop lives on the MCU"

    This is [ADR E](../design/dbw.md#3-adr-e-steering-control-loop-location-the-key-dbw-decision),
    the key design decision of the project, and M2 covers it properly. The one-sentence version:
    the loop is placed in the layer that can close it deterministically, off a USB link whose
    latency varies with laptop load.

### The command path

Exactly one path exists. There is no alternate route, and that is deliberate:

```
laptop:  Nav2 / policy / teleop
   → ros2_control (ackermann_steering_controller)
   → mitt_hardware  →  /mitt/dbw/command   (DbwCommand: steering_angle rad, speed m/s)
   → micro-ROS over USB
   → Teensy 4.1: closes the position loop at >= 200 Hz against the measured angle
   → Sabertooth (packetized serial) → M1 → steering gearmotor
```

Throttle rides the **same** message and the **same** serial link: `DbwCommand.speed` → Teensy
shaping (ramp, cap, direction interlock) → Sabertooth M2 → the paralleled rear drive motors.

**The payoff of a single pinned path** is not architectural tidiness — it is that every
consumer uses it. Teleop, Nav2, and the learned policy all drive the same
`ackermann_steering_controller`, so none of them can develop a private shortcut to the motors.
And because the sim and the vehicle differ only in one plugin, the same path works in
simulation.

### The feedback path

Feedback returns on **the same link, in the same message domain**, at ≥ 50 Hz — a typed
`DbwStatus` carrying the measured angle, the setpoint the loop is currently tracking, wheel
speed, cumulative ticks, the mode, and a fault bitfield.

There is nothing to parse. No ASCII frame, no register map, no protocol translation. mrover
carried encoder data up through PX4 as MAVLink `WHEEL_DISTANCE`; MRider retired that entire
path ([ADR-SW1](../design/software.md#adr-sw1-one-transport-one-clock-typed-messages)).

!!! note "Command and feedback share one road — and that is the point"

    Because both travel the same transport with the same clock, `ros2 topic echo
    /mitt/dbw/status` shows you **both sides of the control loop at once**, and `ros2 bag`
    captures a complete record. Under the old design they shared neither, which is what made
    latency and dropout faults so hard to localize.

    **The tradeoff is real and you should know it.** That link now carries the setpoint too, so
    unplugging USB no longer just blinds odometry — it removes the setpoint, and the vehicle
    goes to `ESTOP`: steering centered, throttle zero. That is
    [row 2 of the failsafe matrix](../design/safety.md#2-failsafe-matrix), and it is a
    deliberate trade: a stale setpoint driving a live actuator is more dangerous than a stop.
    M3 tests it.

### ROS 2 concepts you need

- **Node** — a process that does one thing. Note the Teensy itself is a ROS 2 node: micro-ROS
  means it publishes and subscribes native topics, so it appears in `ros2 node list`.
- **Topic** — a named, typed stream. `/mitt/dbw/command` in, `/mitt/dbw/status` out.
- **Message** — the type on a topic.
- **TF** — the transform tree relating coordinate frames over time. MRider follows REP-105:
  `map` → `odom` → `base_link` → sensor frames.

**`base_link` is pinned** at the center of the rear axle, on the ground plane, X forward, Z
up, Y left ([calibration.md §4.1](../design/calibration.md#41-base_link-definition)). Every
sensor position and every kinematic parameter is measured from that origin. Getting this wrong
is the single most common source of confusing errors later, because nothing crashes — the map
just comes out subtly wrong.

### Rates are a contract, not a suggestion

| Link | Rate | What happens if it is missed |
|---|---|---|
| Command stream (laptop → Teensy) | ≥ 50 Hz | Staleness > 500 ms → `ESTOP`: throttle 0, steering centered |
| Steering position loop (Teensy) | ≥ 200 Hz | Sluggish, hunting steering |
| Actuation frame (Teensy → Sabertooth) | ≥ 200 Hz | **Caps closed-loop performance regardless of loop rate** — see below |
| Status feedback (Teensy → laptop) | ≥ 50 Hz | `/mitt/dbw/status` stale; EKF coasts on IMU; Nav2 halts |
| IMU | ≥ 100 Hz | EKF degrades; Nav2 slows or stops |

These come from the [timing contract](../design/architecture.md#6-timing-heartbeat-contract).

!!! warning "The third row is a trap worth understanding"

    The earlier design pinned a ≥ 100 Hz control loop but never pinned the **output** frame
    rate to the motor driver. Using the standard Arduino `Servo` library, effort commands
    actually reached the driver at ~50 Hz — so *actuation bandwidth*, not loop rate, set the
    real performance ceiling. The loop was running twice as fast as anything could act on.

    A rate you never measured is a rate you do not have. This is why the contract now pins the
    output frame rate explicitly.
Note that a missed rate rarely fails loudly — it degrades, and surfaces later as bad odometry
or a spurious failsafe. Learning to *check* rates is a real skill this course is teaching.

---

## Lab

**Goal:** publish a command, read back feedback, and see the TF tree — the whole system in
miniature.

**You need:** a laptop with ROS 2 Humble, and either a bring-up-capable MRider, a shared demo
rig, or a recorded rosbag.

### Setup

```bash
source /opt/ros/humble/setup.bash
cd ~/mrider_ws && source install/setup.bash
export ROS_DOMAIN_ID=10     # must match agent_config.xml, or you will see nothing

ros2 launch mrider bringup.launch.py
# no vehicle? replay instead:
#   ros2 bag play <course_bag> --loop
```

### Steps

**1. Look around.** Before writing anything, find out what exists.

```bash
ros2 node list                              # the Teensy appears here too
ros2 topic list
ros2 topic info /mitt/dbw/status --verbose
ros2 interface show mitt_msgs/msg/DbwStatus
```

**2. Watch the feedback.** Turn the steering by hand (or let the bag play) and observe.

```bash
ros2 topic echo /mitt/dbw/status
ros2 topic hz   /mitt/dbw/status     # is it meeting the >= 50 Hz contract?
```

**3. Write a node** that publishes `DbwCommand` and subscribes to `DbwStatus`, printing
commanded-vs-measured steering angle side by side.

```python title="mrider_hello.py"
import rclpy
from rclpy.node import Node

class HelloMRider(Node):
    def __init__(self):
        super().__init__('hello_mrider')
        # TODO: create a publisher on /mitt/dbw/command
        # TODO: create a subscription on /mitt/dbw/status
        # Publish at >= 50 Hz -- staleness > 500 ms drops the vehicle to ESTOP.
        self.timer = self.create_timer(0.02, self.tick)   # 50 Hz

    def tick(self):
        # TODO: publish a gentle sinusoidal steering command in RADIANS,
        #       well inside +/-0.3927 rad (+/-22.5 deg)
        pass

    def on_feedback(self, msg):
        # TODO: print commanded vs measured, and the elapsed lag between them
        pass

def main():
    rclpy.init()
    rclpy.spin(HelloMRider())

if __name__ == '__main__':
    main()
```

!!! danger "Wheels off the ground for any lab that commands motion"

    If you are on a real vehicle rather than a bag, the vehicle is on stands. A first ROS 2
    node is exactly the kind of code that publishes NaN at 3 a.m.

**4. Visualize TF.**

```bash
ros2 run tf2_tools view_frames        # writes frames.pdf
ros2 run tf2_ros tf2_echo odom base_link
rviz2                                 # add TF, LaserScan, Image displays
```

**5. Trace one command end to end.** Publish a step change and follow it through:
`/mitt/dbw/command` → `DbwStatus.steering_setpoint` → `DbwStatus.steering_angle` converging.

Record the whole thing in one bag and plot both fields against a single time axis:

```bash
ros2 bag record /mitt/dbw/command /mitt/dbw/status
```

**Notice what you can do here that you could not before.** Both sides of the loop are in one
bag, on one clock. Under the four-board design the setpoint crossed a PWM wire that ROS could
not see at all, which is why that firmware had to echo the decoded setpoint back just so a
human could check it.

### Expected output

- `ros2 topic hz /mitt/dbw/status` reports ≥ 50 Hz
- Your node prints commanded and measured angles that track each other with a visible lag
- `frames.pdf` shows one connected tree rooted at `map`, with no orphaned frames
- Your bag plot shows setpoint and measurement on one time axis, and you can read the lag off it

### Check yourself

- [ ] What happens if your node publishes at 1 Hz instead of 50? Predict, then try it.
- [ ] Where is `base_link` physically located on the vehicle, and why there?
- [ ] Unplug the Teensy's USB. What stops, and what does the vehicle do? Now argue whether that
      is safer or less safe than the old behaviour, where steering kept tracking.
- [ ] The Teensy shows up in `ros2 node list`. What does that tell you about where the
      ROS 2 graph ends and "firmware" begins?
- [ ] One MCU now holds the loop, throttle, override, and arming. What stops the vehicle if its
      firmware hangs? Name every layer you can (M3 has the full answer).
- [ ] `ROS_DOMAIN_ID` is wrong. What symptom do you see, and how is it different from a dead link?

---

## Slide outline

1. **Hook** — a stock kids' ride-on, and the question: what has to change for software to drive it?
2. **Drive-by-wire in three requirements** — actuator, sensor, authority
3. **Two computers and a power stage** — laptop / Teensy / Sabertooth, and what each owns
4. **It used to be four** — why that was reasonable, and why counting interfaces killed it
5. **The command path** — one diagram, traced left to right
6. **The feedback path** — same link, same clock, and the tradeoff that buys
7. **ROS 2 vocabulary** — node, topic, message, TF
8. **`base_link` and REP-105** — where the origin is and why it matters
9. **The timing contract** — four rates, and what breaks when each is missed
10. **Lab brief** — publish, subscribe, visualize, trace
11. **Looking ahead** — M2 opens up the one box we treated as magic today: the position loop

---

**Next:** [M2 — Drive-by-wire & the smart-servo steering loop](m2-dbw-steering.md)
