# Lab 1 — Bring Up the Twin

**Week 1 · 9/14 · due before Week 2 (9/21)**

Your first encounter with a working ROS 2 system. You will not write code today. You will bring up a
robot, find out what is running inside it, make it move, and then deliberately break it in the way
that will otherwise waste an evening of your time later in the semester.

| | |
|---|---|
| **Time** | ~90 minutes |
| **Prerequisite** | [Environment Setup](../environment.md) complete, `check_env.sh` reports `FAIL: 0` |
| **Reading** | [M1 — Intro to MRider & ROS 2](../../learn/m1-ros2-intro.md) |
| **Reference** | [Running the Digital Twin](../../run-the-twin.md) |

> [!TIP]
> **Open four terminals now**
>
> You will need them. In **every single one**, before anything else:
>
> ```bash
> cd ~/mrider/ros2_ws && source setup_env.sh
> ```
>
> Every terminal. Every time. Part 5 shows you what happens when you forget.

---

## Part 1 — Prove your environment

```bash
cd ~/mrider
bash scripts/check_env.sh | tee ~/lab1_env_check.txt
```

**Expected output:** a summary line ending in `FAIL: 0`.

```
================================================================
 OK: 31   WARN: 3   FAIL: 0
================================================================
```

Warnings are fine. Failures are not — fix them before continuing, using the `fix:` line the script
prints. Keep `~/lab1_env_check.txt`; you submit it.

---

## Part 2 — Bring up the twin

**Terminal 1:**

```bash
ros2 launch mitt_bringup sim.launch.py
```

This takes about **80 seconds**. Gazebo downloads the warehouse world on first run, so the very first
launch may take longer. Be patient — a long silence here is normal, not a hang.

**Expected output:** a Gazebo window showing a warehouse, with a small white vehicle in it. In the
terminal, near the end:

```
[spawner-x] Configured and activated joint_state_broadcaster
[spawner-x] Configured and activated ackermann_steering_controller
```

**Terminal 2** — confirm the controllers:

```bash
ros2 control list_controllers
```

Both `joint_state_broadcaster` and `ackermann_steering_controller` must report **`active`**.

If `ros2 control` reports `invalid choice: 'control'`, you are missing
`ros-humble-ros2controlcli`. Install it, or query the service directly:

```bash
ros2 service call /controller_manager/list_controllers \
  controller_manager_msgs/srv/ListControllers "{}" | grep -o "name='[a-z_]*', state='[a-z]*'"
```

```
name='joint_state_broadcaster', state='active'
name='ackermann_steering_controller', state='active'
```

Both must say `active`. If they do not, see [§10 of the setup guide](../environment.md#10-troubleshooting)
— the two usual causes are CycloneDDS and the Fortress/Harmonic package mix-up.

> [!WARNING]
> **One simulator at a time**
>
> If you launch a second `sim.launch.py` without stopping the first, both publish `/clock` and
> `/scan`, and the two interleave. The result looks like a physics bug and is not one. Always
> `Ctrl-C` Terminal 1 before relaunching, and check with `pgrep -a "gz sim"`.

---

## Part 3 — Map the computation graph

This is the actual content of the lab. A ROS 2 system is a graph of processes exchanging typed
messages. Before you can debug one, you have to be able to see it.

**Terminal 2:**

```bash
ros2 node list
ros2 topic list
```

Now look at one topic properly:

```bash
ros2 topic info /ackermann_steering_controller/reference_unstamped --verbose
ros2 topic hz /joint_states
ros2 topic echo /ackermann_steering_controller/odometry --once
```

And view the whole graph:

```bash
rqt_graph
```

**Expected output:** roughly a dozen nodes. `/joint_states` publishing at about **100 Hz** — not by
accident: the controller manager is configured at `update_rate: 100` so that it is never the
bottleneck in the timing contract.

Answer these in your submission, from what you observed — not from guessing:

1. Which node publishes `/scan`, and which one publishes `/joint_states`?
2. `/cmd_vel_joy` and `/cmd_vel` both exist. What subscribes to **both**, and what does that node
   publish?
3. What is the message *type* on `/ackermann_steering_controller/reference_unstamped`?

> [!NOTE]
> **The answer to question 2 is the interesting one**
>
> That node is `twist_mux`, and it arbitrates. `/cmd_vel_joy` has priority **100**; `/cmd_vel`,
> which is where the navigation stack's output arrives, has priority **10**. A human at the sticks
> outranks the autonomy.
>
> Read the comment at the top of `ros2_ws/src/mitt_control/config/twist_mux.yaml`. It is careful to
> say that this is **not** the safety authority on the real vehicle — that authority is electrical
> and layered, and three of its four layers work with the software completely dead. Software that
> presents itself as a safety system when it is not is worse than no software.

---

## Part 4 — Make it move

You have no gamepad yet, so command the vehicle the way the joystick would — by publishing to the
mux's high-priority input.

**Terminal 3:**

```bash
ros2 topic pub -r 10 /cmd_vel_joy geometry_msgs/msg/Twist \
  '{linear: {x: 0.5}, angular: {z: 0.3}}'
```

**Expected output:** the vehicle drives forward in a gentle left arc. `Ctrl-C` to stop.

Watch what happens when you stop publishing: the vehicle halts within about half a second, without
you commanding zero. That is `reference_timeout: 0.5` in the controller configuration — a stale
command is treated as no command. On the real vehicle, the same idea is implemented three more times,
in hardware.

Now watch the odometry while you drive. **Terminal 4:**

```bash
ros2 topic echo /ackermann_steering_controller/odometry --field pose.pose.position
```

Try `angular.z: 2.0`. The vehicle does **not** spin in place — it cannot. Its front wheels are limited
to ±22.5°, which is why turning it around takes a wide arc. That single constraint drives a
surprising amount of this course.

---

## Part 5 — Break it on purpose

Every lab in this course ends here, and this step is worth more of the grade than the happy path.
The happy path you can copy from a classmate. The diagnosis you cannot.

Leave the simulator running in Terminal 1. Open a **new** terminal and — this is the whole point —
**do not source `setup_env.sh`**. Source only ROS itself, exactly as someone in a hurry would:

```bash
source /opt/ros/humble/setup.bash
ros2 topic list --no-daemon | wc -l
ros2 node list --no-daemon
```

**Expected output:** about **7** topics, and exactly **one** node — `/twist_mux`.

A correctly sourced terminal sees **21** topics and the whole graph you mapped in Part 3.

Now check how the failure reported itself:

```bash
ros2 topic list --no-daemon > /dev/null 2>/tmp/err.txt ; echo "exit code: $?"
wc -c /tmp/err.txt
```

**Expected output:** `exit code: 0`, and `0` bytes of error output.

Fix it in the same terminal:

```bash
cd ~/mrider/ros2_ws && source setup_env.sh
ros2 topic list --no-daemon | wc -l
```

All 21 are back.

Write down, in your own words:

- What you observed, exactly: both topic counts, the node list, the exit code, the stderr size.
- Which setting caused it. `setup_env.sh` prints what it sets — compare `echo $ROS_LOCALHOST_ONLY`
  before and after.
- **Why partial visibility is worse than seeing nothing at all.**

> [!CAUTION]
> **Why this specific break, in week one**
>
> `setup_env.sh` sets `ROS_LOCALHOST_ONLY=1`, which confines your ROS traffic to your own machine.
> The simulator started with it. Your new terminal did not. Two ROS processes that disagree about
> that setting largely **cannot see each other**, even side by side on one laptop as the same user.
>
> There is **no error**. Exit code zero. Nothing on stderr. Nothing in any log.
>
> And look closely at what you got, because this is the part worth remembering: **you did not see
> nothing. You saw 7 topics and one node.** A system that shows you nothing at least looks broken.
> A system that shows you *most of a graph* looks like a working system with one node crashed — so
> you go hunting for that node, restart it, read its source, and the whole time the fault is in a
> shell variable you never thought to check.
>
> A crash hands you a stack trace and a line number. This hands you a plausible wrong answer.
> **When something is invisible rather than broken, suspect the environment before you suspect the
> code.**
>
> This is the most common mistake in this course, and you will make it again. The goal is that next
> time you recognise it in thirty seconds instead of losing an evening.

> [!NOTE]
> **The same signature, a different cause: `ROS_DOMAIN_ID`**
>
> Worth one minute, from a *correctly sourced* terminal:
>
> ```bash
> ROS_DOMAIN_ID=42 ros2 topic list --no-daemon
> ROS_DOMAIN_ID=42 ros2 node list --no-daemon
> ```
>
> This time: **2 topics and 0 nodes** — total blindness rather than partial. Exit 0 and empty stderr
> again. A different variable, a different severity, an identical *report*.
>
> `ROS_DOMAIN_ID` partitions which ROS processes can see each other. This course does not rely on it
> — `ROS_LOCALHOST_ONLY=1` is the stronger guarantee, and cannot be defeated by two people picking
> the same number — but it is how you separate robots the moment ROS runs on more than one machine,
> which is most real deployments.
>
> The lesson is not either variable. It is that **several unrelated mistakes all present as
> silence**, and silence is the one symptom that tells you nothing about its own cause.

> [!NOTE]
> **Why `--no-daemon` matters here**
>
> Without it, the `ros2` CLI asks a long-running background daemon that was started under your
> *original* environment, so it happily answers from a cached graph and the break appears not to
> happen. `--no-daemon` forces a fresh discovery in the current environment.
>
> Worth remembering as a debugging habit in its own right: if `ros2 topic list` disagrees with what
> you believe is running, add `--no-daemon` before you believe either of them.

---

## Check yourself

- [ ] `check_env.sh` reports `FAIL: 0`
- [ ] Both controllers report `active`
- [ ] I can name what publishes `/scan` and what subscribes to `/cmd_vel_joy`
- [ ] I made the vehicle drive an arc, and saw it stop on its own when commands stopped
- [ ] I reproduced the silent failure from an unsourced terminal — exit code 0, empty stderr
- [ ] I can name the setting responsible, and say why silence is worse than a crash
- [ ] I can explain why `twist_mux` is *not* a safety system

---

## Deliverables

Submit as a single archive or repository folder:

| | |
|---|---|
| `lab1_env_check.txt` | Output of `check_env.sh` |
| `lab1_graph.txt` | Output of `ros2 node list` and `ros2 topic list` |
| `lab1_topic_info.txt` | Output of the three `ros2 topic` commands in Part 3 |
| `rqt_graph.png` | Screenshot of the node graph |
| `lab1_answers.md` | Answers to the three Part 3 questions, and the Part 5 write-up |
| — | **AI-assistance declaration** — what tool you used and for what, or "none" |

**Grading:** correctness 4 · evidence 3 · understanding 2 · reproducibility 1. See
[Grading](../grading.md#individual-labs-30).

---

## See also

- [Week 1 notes](../weeks/w01.md)
- [Running the Digital Twin](../../run-the-twin.md) — the full procedure, including SLAM and Nav2
- [M1 — Intro to MRider & ROS 2](../../learn/m1-ros2-intro.md)
