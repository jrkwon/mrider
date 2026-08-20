# Lab 3 — A Speed Governor

**Week 3 · 9/21 · due before Week 4 (9/28)**

Parameters, services, and Quality of Service — the three mechanisms that let a ROS 2 system be
configured, commanded, and silently broken.

You will build a **speed governor**: a node that sits between a command source and the vehicle and
enforces a limit. This is a real pattern. It is roughly what the software layer of MRider's authority
ladder does, and building one forces you to think about what happens when the thing in the middle
fails.

| | |
|---|---|
| **Time** | ~90 minutes |
| **Prerequisite** | Lab 2 complete |
| **Reading** | *Zero to Robot* ch. 3 and ch. 19 (QoS) |

---

## Part 1 — A node with parameters

Create the package:

```bash
cd ~/mrider/ros2_ws/src
ros2 pkg create --build-type ament_python --dependencies rclpy geometry_msgs std_srvs lab3_governor
```

Create `lab3_governor/lab3_governor/governor.py`:

```python
import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node


class Governor(Node):
    """Clamp incoming velocity commands to a configurable limit."""

    def __init__(self):
        super().__init__('governor')

        self.declare_parameter('max_speed', 0.5)      # m/s
        self.declare_parameter('max_yaw_rate', 1.0)   # rad/s

        self.pub = self.create_publisher(Twist, '/cmd_vel_joy', 10)
        self.create_subscription(Twist, '/cmd_vel_raw', self.on_cmd, 10)

        self.get_logger().info(
            f'governor up: max_speed={self.max_speed:.2f} m/s')

    @property
    def max_speed(self):
        return self.get_parameter('max_speed').value

    @property
    def max_yaw_rate(self):
        return self.get_parameter('max_yaw_rate').value

    def on_cmd(self, msg):
        out = Twist()
        out.linear.x = max(-self.max_speed, min(self.max_speed, msg.linear.x))
        out.angular.z = max(-self.max_yaw_rate, min(self.max_yaw_rate, msg.angular.z))

        if out.linear.x != msg.linear.x:
            self.get_logger().warn(
                f'clamped {msg.linear.x:.2f} -> {out.linear.x:.2f} m/s',
                throttle_duration_sec=2.0)

        self.pub.publish(out)


def main():
    rclpy.init()
    node = Governor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
```

Register the entry point in `setup.py`, build, and run it. Then, with the simulator up:

```bash
# Terminal 3 - command through the governor
ros2 topic pub -r 10 /cmd_vel_raw geometry_msgs/msg/Twist '{linear: {x: 3.0}}'
```

**Expected output:** the governor logs `clamped 3.00 -> 0.50 m/s` and the vehicle moves at 0.5 m/s,
not 3.0.

Now change the limit **without restarting anything**:

```bash
ros2 param get /governor max_speed
ros2 param set /governor max_speed 1.5
ros2 param list /governor
```

The vehicle speeds up immediately. Parameters are live state, not startup configuration.

---

## Part 2 — A service to disable it

A governor you cannot turn off is not much use in a lab. Add a service.

```python
from std_srvs.srv import SetBool   # at the top

# in __init__:
self.enabled = True
self.create_service(SetBool, '~/enable', self.on_enable)

# a new method:
def on_enable(self, request, response):
    self.enabled = request.data
    response.success = True
    response.message = f'governor {"enabled" if request.data else "DISABLED"}'
    self.get_logger().warn(response.message)
    return response
```

And make `on_cmd` respect it — when disabled, pass the command through unchanged.

Test:

```bash
ros2 service list | grep governor
ros2 service call /governor/enable std_srvs/srv/SetBool '{data: false}'
```

**Expected output:** `success=True`, and the vehicle now accepts the full 3.0 m/s.

Answer in your submission:

1. What is the difference between a **parameter** and a **service** here? Both change the node's
   behaviour at runtime — why would you choose one over the other?
2. You just built something that can disable a safety limit over the network, with no
   authentication. Name two reasons this pattern is unacceptable as a real safety mechanism on a
   vehicle.

!!! danger "Why question 2 matters more than the code"

    This node looks like a safety system. It is not one, for the same reason `twist_mux` is not one —
    and the MRider design documents are careful to say so out loud.

    Read the comment at the top of `mitt_control/config/twist_mux.yaml`: real authority on this
    vehicle is **electrical and layered** — a hardware E-stop, a relay MUX that defaults to stock
    steering, a hardware RC signal MUX, and SBUS override. **Three of those four work with the
    software completely dead.**

    Software that presents itself as a safety system, and then fails silently when its process dies,
    is worse than no software at all — because people trust it.

---

## Part 3 — QoS: the silent one

Every publisher and subscriber carries a **Quality of Service** profile. If a publisher's profile and
a subscriber's profile are incompatible, they simply do not connect.

Set up a demonstration. **Terminal 3:**

```bash
ros2 topic pub --qos-reliability best_effort -r 5 /qos_demo std_msgs/msg/String '{data: hello}'
```

**Terminal 4** — a subscriber that demands reliable delivery:

```bash
ros2 topic echo /qos_demo --qos-reliability reliable
```

**Expected output:** nothing. Not an error, not a warning — nothing at all. It sits there.

Now make it compatible:

```bash
ros2 topic echo /qos_demo --qos-reliability best_effort
```

```
data: hello
---
data: hello
---
```

Both nodes were running the whole time, on the correct topic, with the correct message type.

!!! danger "The rule, and why it is not symmetric"

    A **RELIABLE** publisher can satisfy a **BEST_EFFORT** subscriber — reliable delivery is a
    stronger promise than best-effort requires. The reverse is not true: a best-effort publisher
    cannot satisfy a subscriber that demands reliability, so they never connect.

    Sensor streams are typically best-effort: a dropped LiDAR scan is less harmful than a delayed
    one. Commands and state are typically reliable.

Check what the real system uses:

```bash
ros2 topic info /scan --verbose
```

Record its `Reliability` and `Durability`. Was it what you expected for a sensor topic?

---

## Part 4 — Reflect on the failure mode

You have now met **two** silent failures in three weeks:

| Lab | Failure | How it reported itself |
|---|---|---|
| 1 | `ROS_DOMAIN_ID` mismatch | Exit code 0, empty stderr, 2 topics instead of 21 |
| 3 | QoS incompatibility | Nothing at all |

Write, in your own words:

- What these two have in common.
- Why "it isn't working and there's no error" should now push you toward a **specific** class of
  hypothesis before you start reading your own code.
- One thing you could add to a node so this class of failure is *not* silent. (Hint:
  `ros2 topic info --verbose` tells you the subscription count. What could a node do with that?)

---

## Part 5 — Break it on purpose

Change your governor's publisher to best-effort:

```python
from rclpy.qos import QoSProfile, ReliabilityPolicy

qos = QoSProfile(depth=10, reliability=ReliabilityPolicy.BEST_EFFORT)
self.pub = self.create_publisher(Twist, '/cmd_vel_joy', qos)
```

Rebuild and run. Publish to `/cmd_vel_raw` as before.

**Expected output:** the governor logs that it is clamping and publishing — and the vehicle **does not
move.** `twist_mux` subscribes reliably; your publisher no longer satisfies it.

Confirm the diagnosis rather than assuming it:

```bash
ros2 topic info /cmd_vel_joy --verbose
```

Look at the publisher and subscriber QoS profiles side by side, and at the subscription count.

Write down what you saw, and how you would have found this if you had **not** been told the cause.
That last question is the one worth the marks.

---

## Check yourself

- [ ] My governor clamps, and `ros2 param set` changes the limit live
- [ ] The service enables and disables it
- [ ] I can explain when to use a parameter and when to use a service
- [ ] I can state the reliability compatibility rule and why it is not symmetric
- [ ] I reproduced a QoS mismatch and diagnosed it from `ros2 topic info --verbose`
- [ ] I can explain why neither my governor nor `twist_mux` is a safety system

---

## Deliverables

| | |
|---|---|
| `lab3_governor/` | Your complete package |
| `lab3_qos.txt` | `ros2 topic info --verbose` for `/scan` and for the broken `/cmd_vel_joy` |
| `lab3_answers.md` | Part 2 questions, Part 3 observations, Part 4 reflection, Part 5 write-up |
| — | **AI-assistance declaration** |

---

## See also

- [Week 3 notes](../weeks/w03.md)
- [safety.md](../../design/safety.md) — what real authority looks like
- [M3 — Teleop Control & Safety](../../learn/m3-teleop-safety.md)
