# Environment Setup

**Do this before the first class.** Week 1 opens with Lab 1, which assumes a working machine. If you
arrive on **September 7** without one, you lose the lab.

Budget **2–4 hours**, most of it unattended downloading. Do not leave it to the night before: the one
step that can genuinely fail — graphics drivers — is also the one you cannot fix in five minutes.

!!! tip "The fastest path"

    1. Install Ubuntu 22.04 (§2) — the long one, do it first
    2. Run the ROS 2 install (§3) and the package install (§4)
    3. Clone and build (§6, §7)
    4. Run `bash scripts/check_env.sh` (§8) until it says **Ready**
    5. Smoke-test the simulator (§9)

---

## 1. What you need

| | Minimum | Recommended |
|---|---|---|
| OS | Ubuntu 22.04 LTS, **installed natively** | same |
| CPU | 4 cores | 8+ cores |
| RAM | 8 GB | 16 GB |
| Free disk | 25 GB | 50 GB |
| Graphics | A real GPU with working drivers | dedicated NVIDIA/AMD GPU |
| Gamepad | — | Any XInput controller (Xbox-style). Shared units available in class |

!!! danger "Not WSL. Not a virtual machine."

    You will run Gazebo, a 3D physics simulator, for most of this course. It needs
    **GPU-accelerated OpenGL**.

    - **WSL2** — GPU passthrough for OpenGL is unreliable and debugging it will cost you more time
      than the dual-boot would have.
    - **VirtualBox / VMware** — falls back to software rendering. Gazebo runs at roughly 1 frame per
      second. Technically it starts; practically you cannot work.
    - **macOS** — no supported path. Use a lab machine.

    **Dual-boot is fine** and is what most students should do. If your laptop cannot dual-boot, talk
    to the instructor in the first week about lab machine access — do not silently struggle.

### Why Ubuntu 22.04 specifically

ROS 2 releases are pinned to Ubuntu releases. This course uses **ROS 2 Humble**, which is the
distribution paired with 22.04, and which is what the MRider vehicle itself runs. Ubuntu 24.04 gives
you ROS 2 Jazzy, where roughly a third of the commands in this course differ. Install 22.04.

---

## 2. Install Ubuntu 22.04 LTS

Download **Ubuntu 22.04.x LTS Desktop** from [ubuntu.com/download/desktop](https://ubuntu.com/download/desktop),
write it to a USB stick with [Rufus](https://rufus.ie) (Windows) or
[balenaEtcher](https://etcher.balena.io) (any OS), and install it alongside your existing system.

Give the Ubuntu partition **at least 60 GB**. It fills faster than you expect: ROS, Gazebo, and
`colcon` build artifacts together are around 40 GB.

!!! warning "Back up first"

    Repartitioning a disk can lose data if something goes wrong. Back up anything you care about
    before you start. This is the only genuinely irreversible step in this document.

After first boot:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y build-essential git curl wget vim mesa-utils net-tools
```

### Check your graphics driver now

```bash
glxinfo -B | grep -i "OpenGL renderer"
```

You want to see your actual GPU. If you see **`llvmpipe`**, you are on software rendering and Gazebo
will be unusable. Open **Software & Updates → Additional Drivers** and select the proprietary NVIDIA
or AMD driver, then reboot and check again.

Fix this now. It is the one problem in this document that cannot be solved quickly on the morning of
the first class.

---

## 3. Install ROS 2 Humble

Follow the official steps, which are reproduced here for convenience:

```bash
# Locale
sudo apt update && sudo apt install -y locales
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8

# Repository
sudo apt install -y software-properties-common
sudo add-apt-repository -y universe
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
     -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
  | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

# ROS 2 Humble, desktop variant (includes RViz)
sudo apt update
sudo apt install -y ros-humble-desktop ros-dev-tools

# Build tooling
sudo apt install -y python3-colcon-common-extensions python3-rosdep python3-vcstool
sudo rosdep init 2>/dev/null || true
rosdep update
```

Then verify:

```bash
source /opt/ros/humble/setup.bash
ros2 --help          # should print the ros2 CLI help
```

!!! tip "Do not put `source /opt/ros/humble/setup.bash` in `~/.bashrc` yet"

    You will source a project-specific script instead (§7), which sources ROS for you *and* fixes two
    environment problems that otherwise look like project bugs. Sourcing ROS globally in `~/.bashrc`
    is a habit that will confuse you later in this course.

---

## 4. Install the course packages

```bash
sudo apt install -y \
  ros-humble-ackermann-steering-controller \
  ros-humble-joint-state-broadcaster \
  ros-humble-controller-manager \
  ros-humble-ros2controlcli \
  ros-humble-robot-localization \
  ros-humble-slam-toolbox \
  ros-humble-nav2-bringup \
  ros-humble-nav2-smac-planner \
  ros-humble-twist-mux \
  ros-humble-teleop-twist-joy \
  ros-humble-joy \
  ros-humble-xacro \
  ros-humble-robot-state-publisher
```

These are the real dependency set of the MRider stack, not a teaching subset. You are installing
exactly what the vehicle runs.

---

## 5. Install Gazebo Harmonic

!!! danger "The single most common wrong turn in this setup"

    Humble's *default* paired simulator is Gazebo **Fortress**. This course uses Gazebo
    **Harmonic**, and the ROS bridge for it is published under a **different package name**.

    - `ros-humble-ros-gz-*` → built against **Fortress**. Wrong.
    - `ros-humble-ros-gzharmonic` → built against **Harmonic**. This is the one you want.

    If you install the wrong one, the simulator starts, the robot spawns, and *nothing moves* — with
    no error message that points at the cause. `check_env.sh` checks this explicitly for that reason.

```bash
# Gazebo Harmonic repository
sudo curl -sSL https://packages.osrfoundation.org/gazebo.gpg \
     -o /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] \
http://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" \
  | sudo tee /etc/apt/sources.list.d/gazebo-stable.list > /dev/null

sudo apt update
sudo apt install -y gz-harmonic libgz-sim8-dev libgz-plugin2-dev libgz-transport13-dev

# The Harmonic-paired ROS bridge - note the package name
sudo apt install -y ros-humble-ros-gzharmonic
```

Verify:

```bash
gz sim --version     # must report 8.x
```

---

## 6. Clone the repository and build `gz_ros2_control`

```bash
git clone https://github.com/jrkwon/mrider.git ~/mrider
cd ~/mrider/ros2_ws/src
git clone -b humble https://github.com/ros-controls/gz_ros2_control.git
```

`gz_ros2_control` is the piece that lets the *same* controller configuration drive both the simulated
and the real vehicle. There is **no Harmonic build of it in apt for Humble** — apt only offers 0.7.x,
which targets Fortress — so it must be built from source, with `GZ_VERSION` set:

```bash
cd ~/mrider/ros2_ws
source /opt/ros/humble/setup.bash
GZ_VERSION=harmonic colcon build --packages-select gz_ros2_control
```

This takes several minutes. It is expected to succeed cleanly; if it does not, see §10.

---

## 7. Build the workspace

```bash
cd ~/mrider/ros2_ws
source setup_env.sh
colcon build --symlink-install
```

!!! info "`setup_env.sh` — source it in **every** terminal"

    Not `/opt/ros/humble/setup.bash`. This script sources ROS *and* sets three things that each cause
    a failure looking like a project bug:

    - **`RMW_IMPLEMENTATION=rmw_fastrtps_cpp`** — under CycloneDDS the simulator comes up but the
      controllers never activate, because service *responses* from inside the Gazebo process never
      arrive. The simulator looks dead while running fine.
    - **`PYTHONNOUSERSITE=1`** — stops a `~/.local` version conflict from killing the build with a
      confusing `canonicalize_version()` error.
    - **`GZ_VERSION=harmonic`** — for the source build above.

    It must be consistent across all terminals in a session. Source it in one but not another and
    your `ros2 topic list` will show nothing while the simulator runs perfectly.

You will open four terminals per lab. Source it in all four, every time.

---

## 8. Verify

```bash
cd ~/mrider
bash scripts/check_env.sh
```

The script checks every item above and tells you the exact command to fix anything that fails. Run it
until it prints **Ready**.

```
================================================================
 OK: 31   WARN: 3   FAIL: 0
================================================================
```

`FAIL: 0` is what matters. Warnings are advisory — read them, because they predict what will be slow
or surprising later, but they do not block you.

!!! warning "Set a `ROS_DOMAIN_ID`"

    ROS 2 nodes discover each other over the network automatically. In a classroom of 24 people on
    one Wi-Fi network, **your nodes will see everyone else's**, and your robot will receive their
    commands. Pick a number 0–101 (the instructor will assign one) and add it to `~/.bashrc`:

    ```bash
    echo "export ROS_DOMAIN_ID=<your assigned number>" >> ~/.bashrc
    ```

---

## 9. Smoke test — run the simulator

The real proof. Four terminals, `source setup_env.sh` in each.

```bash
# Terminal 1 - simulator (takes ~80 s to fully start)
cd ~/mrider/ros2_ws && source setup_env.sh
ros2 launch mitt_bringup sim.launch.py
```

Wait until Gazebo shows a warehouse with a small white vehicle in it, then:

```bash
# Terminal 2 - confirm both controllers are active
cd ~/mrider/ros2_ws && source setup_env.sh
ros2 control list_controllers
```

Both `joint_state_broadcaster` and `ackermann_steering_controller` must report **`active`**.

!!! tip "If `ros2 control` reports `invalid choice: 'control'`"

    You are missing `ros-humble-ros2controlcli` (§4). It is **not** pulled in by `ros-humble-desktop`
    or by `ros-humble-controller-manager`, which is a genuinely easy thing to miss. Install it, or
    use the service directly - this needs no extra package:

    ```bash
    ros2 service call /controller_manager/list_controllers \
      controller_manager_msgs/srv/ListControllers "{}" | grep -o "name='[a-z_]*', state='[a-z]*'"
    ```

    ```
    name='joint_state_broadcaster', state='active'
    name='ackermann_steering_controller', state='active'
    ```

If both say `active`, your environment is correct and you are ready for Lab 1.

The full four-terminal procedure, including SLAM and navigation, is in
[Running the Digital Twin](../run-the-twin.md). You do not need to complete it before class — Lab 1
walks you through it.

---

## 10. Troubleshooting

??? failure "`gz sim` opens a black window, or crashes immediately"
    Almost always graphics drivers. Re-run `glxinfo -B | grep -i "OpenGL renderer"`. If it reports
    `llvmpipe`, install a proper GPU driver via **Software & Updates → Additional Drivers** and
    reboot. On a hybrid-graphics laptop you may need to force the discrete GPU.

??? failure "`colcon build` fails with `canonicalize_version() got an unexpected keyword argument`"
    You did not source `setup_env.sh` — it sets `PYTHONNOUSERSITE=1`. This is a version conflict
    between a `~/.local` package and the system one. Source the script and build again.

??? failure "Controllers never activate; spawner reports `Failed getting a result from calling /controller_manager/list_controllers`"
    You are running CycloneDDS. Check with `echo $RMW_IMPLEMENTATION`. Source `setup_env.sh`, which
    forces FastRTPS, **and make sure every terminal in the session has it sourced.**

??? failure "`ros2 topic list` shows nothing while the simulator is clearly running"
    Almost always a **`ROS_DOMAIN_ID` mismatch** between terminals. It fails completely silently:
    exit code 0, nothing on stderr. Run `echo $ROS_DOMAIN_ID` in both terminals and confirm they
    match.

    Add `--no-daemon` when checking. Otherwise the `ros2` CLI answers from a background daemon
    started under a different environment and shows you a cached graph.

??? failure "Robot spawns but does not move when commanded"
    Usually the Fortress/Harmonic package mix-up in §5. Run `bash scripts/check_env.sh` and read
    section 6 of its output.

??? failure "`GZ_VERSION=harmonic colcon build --packages-select gz_ros2_control` fails"
    Confirm the Gazebo dev headers are present: `dpkg -l | grep libgz-sim8-dev`. If missing, re-run
    the `apt install` in §5. If it still fails, bring the **full error output** to the setup clinic.

??? failure "Everything is just very slow"
    Check RAM in `check_env.sh` output. With 8 GB, close your browser before launching the simulator
    — Gazebo, RViz, and Nav2 together will otherwise swap.

!!! tip "Do not lose an evening to this"

    If you are stuck for more than **30 minutes** on one error, stop. Save the full terminal output
    to a file and bring it to the setup clinic or post it. Debugging an install alone at 2 a.m. is
    the least productive form of learning available to you, and there is a lot of real work waiting.

---

## Before the first class

- [ ] Ubuntu 22.04 installed natively
- [ ] `glxinfo -B` reports a real GPU, not `llvmpipe`
- [ ] `bash scripts/check_env.sh` reports **`FAIL: 0`**
- [ ] `ros2 control list_controllers` shows both controllers `active`
- [ ] `ROS_DOMAIN_ID` set in `~/.bashrc`
- [ ] Terminal output of `check_env.sh` saved — you submit it with Lab 1

---

## See also

- [Syllabus](syllabus.md) — the 16-week schedule
- [Running the Digital Twin](../run-the-twin.md) — the full four-terminal procedure
- [M1 — Intro to MRider & ROS 2](../learn/m1-ros2-intro.md) — Week 1 assigned reading
- [Build guide §5 — Software Install](../build/05-software.md) — the vehicle-side version of this
  document, for when the hardware exists
