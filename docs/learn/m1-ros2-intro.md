# M1 — Intro to MRider & ROS 2

**Learning objectives:**

- Explain what drive-by-wire is and how MRider is architected end to end.
- Navigate a ROS 2 Humble workspace; understand nodes, topics, and TF.
- Trace the command and feedback paths through the system block diagram.

**Reference:** [design/architecture.md](../design/architecture.md)

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

The system has four computers, and it is worth being precise about what each one owns:

| Where | What it owns | Why there |
|---|---|---|
| **Laptop** (ROS 2 Humble) | Perception, SLAM, Nav2, the learned policy — everything that needs a GPU or a filesystem | Runs on its own battery, so traction sag cannot reset it |
| **Pixhawk 6C** (PX4 rover) | The IMU/EKF, RC receiver, and the conversion of a normalized steering command into a servo-PWM output | Validated flight-controller stack, reused nearly verbatim from mrover |
| **Arduino Nano** | The steering position loop at ≥100 Hz, and encoder aggregation | A dedicated MCU has deterministic, direct access to the sensor and the motor driver |
| **Sabertooth 2x32** | Raw H-bridge power to the motors | A dumb, fast power stage — deliberately not smart |

!!! info "Why the steering loop lives on the Nano"

    This is [ADR E](../design/dbw.md#3-adr-e-steering-control-loop-location-the-key-dbw-decision),
    the key design decision of the whole project, and M2 covers it properly. The one-sentence
    version: the loop is placed in the layer that can close it deterministically, off the
    laptop↔USB↔MAVLink chain whose latency varies with laptop load.

### The command path

Exactly one path exists. There is no alternate route, and that is deliberate:

```
laptop /mrider/cmd
   → command shim → ManualControlSetpoint (roll = STEER, throttle = THROTTLE)
   → Micro-XRCE-DDS → PX4
   → PX4 rover: roll → servo PWM (1000–2000 µs, 1500 µs = 0°)
   → Arduino Nano: reads the pulse like a hobby servo, closes the position loop
   → Sabertooth S1 → M1 → steering gearmotor
```

Throttle takes a shorter route: `MANUAL_CONTROL.throttle` → PX4 PWM → Sabertooth **S2** →
M2 → the paralleled rear drive motors. No Nano involvement.

**The payoff of a single pinned path** is not architectural tidiness. Because steering flows
*through* PX4, an RC transmitter bound to the Pixhawk overrides steering *and* throttle using
PX4's standard RC override — with no extra wiring to the Nano. One design choice bought a
safety property for free.

### The feedback path

Feedback comes back a different way than mrover did it. The Nano emits an ASCII frame over
USB at ≥20 Hz:

```
F,<steer_deg>,<steer_counts>,<drive_ticks>,<drive_rpm>,<setpoint_deg>,<status>\n
```

A ROS 2 driver parses it and publishes `/mrider/feedback`. mrover instead carried encoder data
up through PX4 as MAVLink `WHEEL_DISTANCE`; MRider retired that path
([ADR-SW1](../design/software.md#adr-sw1-reroute-feedback-off-mavlink)) because once the Nano
owns the servo loop it already aggregates every sensor — a direct USB link removes a round
trip and gives one teachable serial contract.

!!! note "Command and feedback travel different roads — and that matters"

    Steering **setpoints** arrive via PX4 servo PWM. Steering **measurements** leave via USB.
    So unplugging the USB cable blinds odometry but leaves the steering tracking. That is not
    a bug; it is a consequence of the topology, and it is
    [row 2 of the failsafe matrix](../design/safety.md#2-failsafe-matrix). M3 tests it
    deliberately.

### ROS 2 concepts you need

- **Node** — a process that does one thing. MRider adds exactly two new ones: the feedback
  driver and the command shim.
- **Topic** — a named, typed stream. `/mrider/cmd` in, `/mrider/feedback` out.
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
| Setpoint stream (laptop → PX4) | ≥ 10 Hz | PX4 offboard-loss failsafe: throttle → 0, hold |
| Steering servo loop (Nano) | ≥ 100 Hz | Sluggish, hunting steering |
| Feedback (Nano → laptop) | ≥ 20 Hz | `/mrider/feedback` stale; EKF coasts on IMU; Nav2 halts |
| PX4 IMU | ≥ 100 Hz | EKF degrades; Nav2 slows or stops |

These come from the [timing contract](../design/architecture.md#6-timing-heartbeat-contract).
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
ros2 node list
ros2 topic list
ros2 topic info /mrider/feedback --verbose
ros2 interface show <the type printed above>
```

**2. Watch the feedback.** Turn the steering by hand (or let the bag play) and observe.

```bash
ros2 topic echo /mrider/feedback
ros2 topic hz   /mrider/feedback     # is it meeting the >= 20 Hz contract?
```

**3. Write a node** that publishes to `/mrider/cmd` and subscribes to `/mrider/feedback`,
printing commanded-vs-measured steering angle side by side.

```python title="mrider_hello.py"
import rclpy
from rclpy.node import Node

class HelloMRider(Node):
    def __init__(self):
        super().__init__('hello_mrider')
        # TODO: create a publisher on /mrider/cmd
        # TODO: create a subscription on /mrider/feedback
        # Publish at >= 10 Hz -- below that, PX4 will failsafe.
        self.timer = self.create_timer(0.05, self.tick)   # 20 Hz

    def tick(self):
        # TODO: publish a gentle sinusoidal steering command, well inside +/-22.5 deg
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
`/mrider/cmd` → `/fmu/in/manual_control_setpoint` → (servo PWM, not visible in ROS) →
`setpoint_deg` in the feedback frame → `steer_deg` converging. Note **where you lose
visibility** — the servo-PWM hop is invisible from ROS, which is why the Nano echoes
`setpoint_deg` back in its frame at all.

### Expected output

- `ros2 topic hz /mrider/feedback` reports ≥ 20 Hz
- Your node prints commanded and measured angles that track each other with a visible lag
- `frames.pdf` shows one connected tree rooted at `map`, with no orphaned frames
- You can name the point in the chain where ROS-level introspection stops

### Check yourself

- [ ] Why does the steering setpoint go through PX4 instead of straight to the Nano over USB?
- [ ] What happens if your node publishes at 5 Hz instead of 20? Predict, then try it.
- [ ] Where is `base_link` physically located on the vehicle, and why there?
- [ ] Unplug the Nano's USB (or stop the driver). Which of steering / odometry stops? Why?
- [ ] `ROS_DOMAIN_ID` is wrong. What symptom do you see, and how is it different from a dead link?

---

## Slide outline

1. **Hook** — a stock kids' ride-on, and the question: what has to change for software to drive it?
2. **Drive-by-wire in three requirements** — actuator, sensor, authority
3. **The four computers** — laptop / Pixhawk / Nano / Sabertooth, and what each owns
4. **The command path** — one diagram, traced left to right
5. **The single-path payoff** — RC override covers steering for free
6. **The feedback path** — and why it deliberately goes a different way
7. **ROS 2 vocabulary** — node, topic, message, TF
8. **`base_link` and REP-105** — where the origin is and why it matters
9. **The timing contract** — four rates, and what breaks when each is missed
10. **Lab brief** — publish, subscribe, visualize, trace
11. **Looking ahead** — M2 opens up the one box we treated as magic today: the Nano's loop

---

**Next:** [M2 — Drive-by-wire & the smart-servo steering loop](m2-dbw-steering.md)
