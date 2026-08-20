# Lab 2 — Drive a Square

**Week 2 · 9/14 · due before Week 3 (9/21)**

Your first ROS 2 code. You will build a package, publish commands to a real controller, subscribe to
the feedback it produces, and discover that a rate is a contract rather than a preference.

| | |
|---|---|
| **Time** | ~90 minutes |
| **Prerequisite** | Lab 1 complete |
| **Reading** | [M1 §ROS 2 concepts](../../learn/m1-ros2-intro.md) · *Zero to Robot* ch. 2–3 |

---

## Part 1 — Create a package

**Terminal 1** — leave the simulator running from Lab 1, or relaunch it:

```bash
cd ~/mrider/ros2_ws && source setup_env.sh
ros2 launch mitt_bringup sim.launch.py
```

**Terminal 2:**

```bash
cd ~/mrider/ros2_ws/src
ros2 pkg create --build-type ament_python --dependencies rclpy geometry_msgs nav_msgs lab2_square
```

**Expected output:** a new `lab2_square/` directory containing `package.xml`, `setup.py`, and a
`lab2_square/` Python subdirectory.

!!! info "Why `ament_python` here when every MITT package is `ament_cmake`"

    The existing packages hold launch files, YAML, URDF, and message definitions — things CMake
    installs. They contain no nodes at all. You are writing a Python node, so `ament_python` is the
    lighter fit. Being able to say *why* you picked a build type is the point.

---

## Part 2 — Publish a square

Create `lab2_square/lab2_square/square_driver.py`:

```python
import math

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node


class SquareDriver(Node):
    """Drive a square by alternating straight legs and turns, open loop."""

    def __init__(self):
        super().__init__('square_driver')

        # cmd_vel_joy is twist_mux's highest-priority input (priority 100).
        # Publishing here is exactly what the joystick does.
        self.pub = self.create_publisher(Twist, '/cmd_vel_joy', 10)

        self.speed = 0.5          # m/s
        self.turn_rate = 0.4      # rad/s
        self.leg_seconds = 4.0
        self.turn_seconds = math.pi / 2 / self.turn_rate

        self.phase = 'straight'
        self.phase_start = self.get_clock().now()

        # 10 Hz. The controller drops to zero after 0.5 s without a command
        # (reference_timeout), so anything slower than 2 Hz stutters. See Part 5.
        self.timer = self.create_timer(0.1, self.tick)
        self.get_logger().info('square_driver started')

    def tick(self):
        elapsed = (self.get_clock().now() - self.phase_start).nanoseconds / 1e9
        msg = Twist()

        if self.phase == 'straight':
            msg.linear.x = self.speed
            if elapsed >= self.leg_seconds:
                self.phase, self.phase_start = 'turn', self.get_clock().now()
        else:
            msg.linear.x = self.speed * 0.6   # a car cannot turn while stopped
            msg.angular.z = self.turn_rate
            if elapsed >= self.turn_seconds:
                self.phase, self.phase_start = 'straight', self.get_clock().now()

        self.pub.publish(msg)


def main():
    rclpy.init()
    node = SquareDriver()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
```

Register it in `setup.py`:

```python
entry_points={
    'console_scripts': [
        'square_driver = lab2_square.square_driver:main',
    ],
},
```

Build and run:

```bash
cd ~/mrider/ros2_ws
colcon build --packages-select lab2_square --symlink-install
source setup_env.sh
ros2 run lab2_square square_driver
```

**Expected output:** the vehicle drives a rounded square. It will not close perfectly. That is not a
bug in your code — see Part 4.

!!! warning "`msg.linear.x` stays non-zero during the turn, deliberately"

    Set it to zero and the vehicle stops turning entirely. MRider is **Ackermann-steered**: the front
    wheels point, the rear wheels push. With no forward motion there is no rotation, no matter what
    `angular.z` says. A differential-drive robot would spin in place here; this one cannot, and every
    planner in this course has to respect that.

---

## Part 3 — Subscribe to the feedback

Open loop is guessing. Add a subscriber so you can see what the vehicle actually did.

Add to `SquareDriver.__init__`:

```python
from nav_msgs.msg import Odometry   # at the top of the file

self.start_pose = None
self.create_subscription(
    Odometry, '/ackermann_steering_controller/odometry', self.on_odom, 10)
```

And a callback:

```python
def on_odom(self, msg):
    p = msg.pose.pose.position
    if self.start_pose is None:
        self.start_pose = (p.x, p.y)
    dx = p.x - self.start_pose[0]
    dy = p.y - self.start_pose[1]
    self.get_logger().info(
        f'{self.phase:8s}  x={p.x:+.2f} y={p.y:+.2f}  '
        f'drift from start={math.hypot(dx, dy):.2f} m',
        throttle_duration_sec=1.0)
```

Rebuild and run. Record the drift-from-start value after **one complete square**.

---

## Part 4 — Why the square does not close

Let it run two or three full squares and watch the drift grow.

Answer in your submission:

1. What was your drift from start after one square? After three?
2. Name **two** distinct reasons an open-loop square does not close on this vehicle.
3. The odometry you subscribed to reports a position. Where does that number physically come
   from, and what can it not possibly know?

!!! quote "The answer to question 3 is a design decision, not an accident"

    On the real vehicle, both rear motors are wired in parallel to a **single** driver channel, and
    only **one** of them carries an encoder ([ADR C](../../design/dbw.md)). So the measurement is
    taken at one motor shaft — upstream of the gearbox backlash, upstream of tyre slip, and blind to
    the fact that in a turn the two rear wheels travel different distances.

    See the diagram in [M5](../../learn/m5-slam.md). This is exactly why odometry gets fused with an
    IMU in an EKF rather than trusted raw, and it is why Week 6 exists.

---

## Part 5 — Break it on purpose

Change the timer period from `0.1` to `1.0` — publishing once per second instead of ten times.

```python
self.timer = self.create_timer(1.0, self.tick)
```

Rebuild, run, and watch the vehicle.

**Expected output:** it lurches and stalls, repeatedly. It moves for about half a second, stops for
half a second, moves again.

Now find the cause. In `ros2_ws/src/mitt_control/config/mitt_controllers.yaml`:

```yaml
reference_timeout: 0.5
```

Write down:

- What you observed.
- Which parameter caused it, and what it does.
- Why this behaviour is **correct** — why a controller that keeps executing the last command it
  received would be a serious defect on a real vehicle.

!!! danger "This is a safety mechanism, not a limitation"

    A stale command is not a command. If the process sending steering and throttle dies, freezes, or
    loses its connection, a controller that holds the last value drives a vehicle at its last
    commanded speed into whatever is in front of it.

    `reference_timeout: 0.5` is the software layer of that protection. The real vehicle implements
    the same idea three more times in hardware, because — as `twist_mux.yaml` puts it — a software
    mux cannot do that job. Three of the four real authority layers work with the controller
    firmware completely dead.

Set the timer back to `0.1` before submitting.

---

## Check yourself

- [ ] My package builds with `colcon build` and runs with `ros2 run`
- [ ] The vehicle drives a recognisable square
- [ ] I can explain why `linear.x` must stay non-zero during the turn
- [ ] I recorded drift after one and three squares
- [ ] I can name where the odometry number physically comes from, and what it cannot see
- [ ] I reproduced the stale-command stall and can explain why the behaviour is correct

---

## Deliverables

| | |
|---|---|
| `lab2_square/` | Your complete package |
| `lab2_odom.txt` | Logged output showing drift after one and three squares |
| `lab2_answers.md` | Part 4 questions and the Part 5 write-up |
| — | **AI-assistance declaration** |

**Grading:** correctness 4 · evidence 3 · understanding 2 · reproducibility 1.

---

## See also

- [Week 2 notes](../weeks/w02.md)
- [Lab 3 — Parameters, Services, and QoS](lab3.md)
- [M5 — Localization & SLAM](../../learn/m5-slam.md) — why odometry drifts
