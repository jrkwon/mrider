# Copyright 2026 Jaerock Kwon
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

r"""
Lab submission tooling: generate, validate, submit, and batch-grade lab reports.

Driven through ``scripts/lab.sh``; run that rather than this file directly.

    bash scripts/lab.sh init          # once, per student
    bash scripts/lab.sh new    1      # generate labs/lab1/REPORT.md
    bash scripts/lab.sh check  1      # validate without submitting
    bash scripts/lab.sh submit 1      # validate, commit, push, build the zip
    bash scripts/lab.sh grade  1 ...  # instructor: check a whole cohort at once

WHY ONE REPORT FILE RATHER THAN A FOLDER OF .txt
------------------------------------------------
The earlier deliverable lists asked for four to six loose files per lab. At 24
students x 5 labs that is roughly 600 files, in 24 different layouts, with
colliding names once unpacked, and with every objective fact - `FAIL: 0`, both
controllers `active`, 7 topics versus 21 - checked by eye.

One REPORT.md per lab, with fixed headings in rubric order, puts each claim next
to the evidence for it. Fenced code blocks still satisfy "terminal output as
text, not a photo of your screen".

WHY A MEASUREMENTS BLOCK
------------------------
Pasted terminal output is for a human to read; regexing it for grading is
brittle. Each report therefore carries a small `key = value` block of the
numbers the lab actually produced. Those are checked automatically, which is
what turns Correctness (4 points) and Reproducibility (1) from 120 manual
readings into a report.

The checks below assert RELATIONS the lab's physics guarantees - drift grows,
two different yaw commands clamp to one radius, a rear camera's yaw is pi - and
only warn on absolute values, which legitimately vary between machines. A FAIL
means the submission contradicts itself; a WARN means look closer.

WHY PROVENANCE IS GENERATED, NOT TYPED
--------------------------------------
Host, OS, RMW, isolation variables and the course commit are stamped in by the
generator. A student cannot forget them, and a report produced on a machine
whose environment was never correct says so in its own header.
"""
import argparse
import configparser
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONFIG = REPO / '.labconfig'
FORMAT_VERSION = 1

# Placeholder tokens the generator writes and the validator refuses to accept
# back. Distinct prefixes so the error message can say what kind of thing is
# missing rather than just "a placeholder".
TODO = 'TODO'
PASTE = 'PASTE'


# --- report block types ------------------------------------------------------
#
# A lab's report is a flat list of these. Keeping it flat keeps the generator,
# the validator and the grader reading the same structure.

def h2(title):
    return ('h2', title, None, None)


def evidence(key, title, command, lang='text'):
    """A fenced block the student pastes real terminal output into."""
    return ('evidence', title, f'{key}|{lang}', command)


def question(key, prompt):
    """A numbered question from the lab, answered in prose."""
    return ('question', key, prompt, None)


def prose(key, title, prompt):
    """A free-form write-up section, typically the 'break it' diagnosis."""
    return ('prose', key, title, prompt)


def image(key, title, filename, prompt):
    """An image deliverable, referenced from the report so it cannot be orphaned."""
    return ('image', key, f'{title}|{filename}', prompt)


# --- per-lab measurement checks ----------------------------------------------
#
# Each returns a list of (level, message). Levels: 'FAIL' contradicts the lab,
# 'WARN' is outside the expected band but could be a legitimate difference.

def _num(m, key):
    """Measurement as float, or None if absent or not a number."""
    try:
        return float(str(m.get(key, '')).strip())
    except ValueError:
        return None


def _band(out, m, key, lo, hi, what):
    v = _num(m, key)
    if v is not None and not (lo <= v <= hi):
        out.append(('WARN', f'{key} = {v:g}; expected roughly {lo:g}-{hi:g} ({what})'))


def check_lab1(m):
    out = []
    unsourced, sourced = _num(m, 'topics_unsourced'), _num(m, 'topics_sourced')
    nodes = _num(m, 'nodes_unsourced')
    if unsourced is not None and sourced is not None and unsourced >= sourced:
        out.append(('FAIL', f'topics_unsourced ({unsourced:g}) is not fewer than '
                            f'topics_sourced ({sourced:g}) - the whole point of Part 5 '
                            f'is that the unsourced terminal sees less of the graph'))
    if _num(m, 'exit_code') not in (None, 0):
        out.append(('FAIL', 'exit_code is not 0; Part 5 turns on the failure being silent'))
    if _num(m, 'stderr_bytes') not in (None, 0):
        out.append(('FAIL', 'stderr_bytes is not 0; Part 5 turns on the failure being silent'))
    _band(out, m, 'topics_unsourced', 2, 12, 'measured 7 on the reference machine')
    _band(out, m, 'topics_sourced', 15, 30, 'measured 21 on the reference machine')
    if nodes is not None and nodes > 3:
        out.append(('WARN', f'nodes_unsourced = {nodes:g}; measured 1 (/twist_mux) on '
                            f'the reference machine'))
    return out


def check_lab2(m):
    out = []
    one, three = _num(m, 'drift_after_1_square_m'), _num(m, 'drift_after_3_squares_m')
    if one is not None and three is not None and three <= one:
        out.append(('FAIL', f'drift_after_3_squares_m ({three:g}) is not greater than '
                            f'drift_after_1_square_m ({one:g}) - open-loop drift '
                            f'accumulates; this pair says it did not'))
    for key in ('drift_after_1_square_m', 'drift_after_3_squares_m'):
        v = _num(m, key)
        if v is not None and v < 0:
            out.append(('FAIL', f'{key} is negative; it is a distance'))
    _band(out, m, 'stall_period_s', 0.4, 0.6,
          'reference_timeout is 0.5 s in mitt_controllers.yaml')
    return out


def check_lab3(m):
    out = []
    clamp_to = _num(m, 'clamped_to_mps')
    clamp_from = _num(m, 'clamped_from_mps')
    limit = _num(m, 'max_speed_param_mps')
    if clamp_to is not None and limit is not None and clamp_to > limit + 1e-6:
        out.append(('FAIL', f'clamped_to_mps ({clamp_to:g}) exceeds max_speed_param_mps '
                            f'({limit:g}) - the governor did not govern'))
    if clamp_from is not None and clamp_to is not None and clamp_from <= clamp_to:
        out.append(('WARN', 'clamped_from_mps is not above clamped_to_mps; nothing was clamped'))
    rel = str(m.get('scan_reliability', '')).strip().upper()
    if rel and rel not in ('RELIABLE', 'BEST_EFFORT', 'BEST EFFORT', 'BESTEFFORT'):
        out.append(('FAIL', f'scan_reliability = {rel!r}; expected RELIABLE or BEST_EFFORT '
                            f'as printed by `ros2 topic info --verbose`'))
    return out


def check_lab4(m):
    """
    Lab 4's finding is the steering clamp: at w=1.0 and w=2.0 the vehicle is
    already at its mechanical limit, so two commanded radii differing by a
    factor of two produce ONE measured radius. That equality is the lab.
    """
    out = []
    r100, r200 = _num(m, 'measured_R_w100_m'), _num(m, 'measured_R_w200_m')
    r030 = _num(m, 'measured_R_w030_m')
    r075 = _num(m, 'measured_R_wheelbase_075_m')

    if r100 is not None and r200 is not None:
        if abs(r100 - r200) > 0.15:
            out.append(('FAIL', f'measured_R_w100_m ({r100:g}) and measured_R_w200_m '
                                f'({r200:g}) differ by {abs(r100 - r200):.2f} m. Both '
                                f'commands are past the 22.5 deg limit, so both should '
                                f'clamp to the same radius'))
    if r200 is not None and r200 < 1.0:
        out.append(('FAIL', f'measured_R_w200_m = {r200:g} m. The vehicle cannot turn '
                            f'inside R_min = 0.63/tan(22.5 deg) = 1.52 m'))
    if r030 is not None and r100 is not None and r030 <= r100:
        out.append(('WARN', 'measured_R_w030_m is not larger than measured_R_w100_m; '
                            'w = 0.30 requests 1.67 m, which is inside the achievable range'))
    if r075 is not None and r200 is not None and r075 <= r200:
        out.append(('FAIL', f'measured_R_wheelbase_075_m ({r075:g}) is not greater than '
                            f'measured_R_w200_m ({r200:g}). R = L/tan(d): a longer '
                            f'wheelbase at the same steering limit must turn wider'))
    _band(out, m, 'measured_R_w200_m', 1.35, 1.70, 'theory 1.52 m, measured 1.49 m')
    _band(out, m, 'measured_R_wheelbase_075_m', 1.60, 2.05, 'theory 0.75/tan(22.5 deg) = 1.81 m')
    return out


def check_lab5(m):
    out = []
    yaw = _num(m, 'rear_camera_yaw_rad')
    if yaw is not None and abs(abs(yaw) - 3.14159265) > 0.02:
        out.append(('FAIL', f'rear_camera_yaw_rad = {yaw:g}; a rear-facing camera is at '
                            f'yaw = +/-pi. This one is not pointing backwards'))
    _band(out, m, 'rear_camera_x_m', -0.30, -0.05, 'the joint origin places it behind base_link')
    return out


# --- lab definitions ---------------------------------------------------------

LABS = {
    1: dict(
        title='Bring Up the Twin',
        week=1, due='2026-09-21',
        # Repo paths, beyond labs/lab1/, that belong in this submission.
        paths=[],
        measurements=[
            ('topics_unsourced', 'Part 5: `ros2 topic list --no-daemon | wc -l` before sourcing'),
            ('topics_sourced', 'Part 5: the same count after sourcing setup_env.sh'),
            ('nodes_unsourced', 'Part 5: how many nodes `ros2 node list --no-daemon` showed'),
            ('exit_code', 'Part 5: the exit code the failing command returned'),
            ('stderr_bytes', 'Part 5: bytes it wrote to stderr'),
            ('joint_states_hz', 'Part 3: `ros2 topic hz /joint_states`, averaged'),
        ],
        checks=check_lab1,
        blocks=[
            h2('Part 1 - Prove your environment'),
            evidence('env_check', 'Evidence', 'bash scripts/check_env.sh'),
            h2('Part 2 - Bring up the twin'),
            evidence('controllers', 'Evidence', 'ros2 control list_controllers'),
            h2('Part 3 - Map the computation graph'),
            evidence('graph', 'Evidence', 'ros2 node list && ros2 topic list'),
            evidence('topic_info', 'Evidence',
                     'the three `ros2 topic` commands in Part 3'),
            image('rqt', 'Evidence', 'rqt_graph.png', 'Screenshot of `rqt_graph`.'),
            question('q1', 'Which node publishes `/scan`, and which one publishes '
                           '`/joint_states`?'),
            question('q2', '`/cmd_vel_joy` and `/cmd_vel` both exist. What subscribes to '
                           '**both**, and what does that node publish?'),
            question('q3', 'What is the message *type* on '
                           '`/ackermann_steering_controller/reference_unstamped`?'),
            h2('Part 5 - Break it on purpose'),
            evidence('break', 'Evidence', 'the unsourced terminal, and the same commands '
                                          'after sourcing'),
            prose('diagnosis', 'Diagnosis',
                  'What you observed, exactly: both topic counts, the node list, the exit '
                  'code, the stderr size. Which setting caused it. And why partial '
                  'visibility is worse than seeing nothing at all.'),
        ],
    ),
    2: dict(
        title='Drive a Square',
        week=2, due='2026-09-28',
        paths=['ros2_ws/src/lab2_square'],
        measurements=[
            ('drift_after_1_square_m', 'Part 3: drift from start after one square'),
            ('drift_after_3_squares_m', 'Part 3: drift from start after three squares'),
            ('stall_period_s', 'Part 5: how long the vehicle stopped for, each cycle'),
        ],
        checks=check_lab2,
        blocks=[
            h2('Part 2 - Publish a square'),
            evidence('build', 'Evidence', 'colcon build --packages-select lab2_square'),
            h2('Part 3 - Subscribe to the feedback'),
            evidence('odom', 'Evidence',
                     'the logged drift, covering one square through three'),
            h2('Part 4 - Why the square does not close'),
            question('q1', 'What was your drift from start after one square? After three?'),
            question('q2', 'Name **two** distinct reasons an open-loop square does not close '
                           'on this vehicle.'),
            question('q3', 'The odometry you subscribed to reports a position. Where does '
                           'that number physically come from, and what can it not possibly '
                           'know?'),
            h2('Part 5 - Break it on purpose'),
            evidence('stall', 'Evidence', 'the node running at 1 Hz'),
            prose('diagnosis', 'Diagnosis',
                  'What you observed. Which parameter caused it and what it does. And why '
                  'this behaviour is **correct** - why a controller that kept executing the '
                  'last command it received would be a serious defect on a real vehicle.'),
        ],
    ),
    3: dict(
        title='A Speed Governor',
        week=3, due='2026-10-05',
        paths=['ros2_ws/src/lab3_governor'],
        measurements=[
            ('max_speed_param_mps', 'Part 1: the `max_speed` parameter in effect'),
            ('clamped_from_mps', 'Part 1: the speed you commanded'),
            ('clamped_to_mps', 'Part 1: the speed the governor passed through'),
            ('scan_reliability', 'Part 3: `/scan` Reliability, as printed'),
            ('scan_durability', 'Part 3: `/scan` Durability, as printed'),
        ],
        checks=check_lab3,
        blocks=[
            h2('Part 1 - A node with parameters'),
            evidence('clamp', 'Evidence', 'the governor clamping, and `ros2 param set` '
                                          'changing the limit live'),
            h2('Part 2 - A service to disable it'),
            evidence('service', 'Evidence', 'ros2 service call /governor/enable ...'),
            question('q1', 'What is the difference between a **parameter** and a **service** '
                           'here? Both change the node\'s behaviour at runtime - why would '
                           'you choose one over the other?'),
            question('q2', 'You just built something that can disable a safety limit over the '
                           'network, with no authentication. Name two reasons this pattern is '
                           'unacceptable as a real safety mechanism on a vehicle.'),
            h2('Part 3 - QoS: the silent one'),
            evidence('qos_scan', 'Evidence', 'ros2 topic info /scan --verbose'),
            question('q3', 'Record `/scan`\'s Reliability and Durability. Was that what you '
                           'expected for a sensor topic, and why?'),
            h2('Part 4 - Reflect on the failure mode'),
            prose('reflection', 'Reflection',
                  'What the two silent failures you have now met have in common. Why "it '
                  'isn\'t working and there\'s no error" should push you toward a specific '
                  'class of hypothesis before you start reading your own code. And one thing '
                  'you could add to a node so this class of failure is not silent.'),
            h2('Part 5 - Break it on purpose'),
            evidence('qos_break', 'Evidence',
                     'ros2 topic info /cmd_vel_joy --verbose, with the best-effort publisher'),
            prose('diagnosis', 'Diagnosis',
                  'What you saw, and how you would have found this if you had **not** been '
                  'told the cause. That last part is the one worth the marks.'),
        ],
    ),
    4: dict(
        title='How Tightly Can It Turn?',
        week=4, due='2026-10-12',
        paths=['ros2_ws/src/lab4_radius',
               'ros2_ws/src/mitt_description/config/mitt_dimensions.yaml'],
        measurements=[
            ('predicted_R_w030_m', 'Part 2: requested R = v/w at w = 0.30, predicted actual'),
            ('predicted_R_w100_m', 'Part 2: predicted actual R at w = 1.00'),
            ('predicted_R_w200_m', 'Part 2: predicted actual R at w = 2.00'),
            ('measured_R_w030_m', 'Part 3: fitted radius at w = 0.30 rad/s'),
            ('measured_R_w100_m', 'Part 3: fitted radius at w = 1.00 rad/s'),
            ('measured_R_w200_m', 'Part 3: fitted radius at w = 2.00 rad/s'),
            ('measured_R_wheelbase_075_m', 'Part 5: fitted radius with wheelbase = 0.75'),
        ],
        checks=check_lab4,
        blocks=[
            h2('Part 2 - Predict before you measure'),
            prose('predictions', 'Predictions',
                  'The Part 2 table, filled in BEFORE you measured. Reproduce all six '
                  'columns. Your predicted values also go in the Measurements block above.'),
            h2('Part 3 - Measure it'),
            evidence('results', 'Evidence', 'your measurement node, all three cases'),
            h2('Part 4 - Explain what you found'),
            question('q7', 'Why do w = 1.00 and w = 2.00 produce an identical measured '
                           'radius despite commanding radii that differ by a factor of two?'),
            question('q8', 'The vehicle silently ignored your command. Relate this to the '
                           'silent failures in Labs 1 and 3. What should a planner do '
                           'about it?'),
            question('q9', 'Theory says 1.52 m, measurement says about 1.49 m. Propose at '
                           'least two distinct explanations, and state how you would test '
                           'each one.'),
            h2('Part 5 - Break it on purpose'),
            evidence('wheelbase', 'Evidence', 'the repeated measurement at wheelbase = 0.75'),
            question('q10', 'What happened to the measured minimum radius? Does it match the '
                            'new theoretical `0.75/tan(22.5 deg)`?'),
            question('q11', 'Suppose the *simulation* says 0.63 m and the *real vehicle* is '
                            '0.75 m. Nav2 plans a path it believes is feasible. What happens '
                            'when the real car tries to follow it - and at what point in the '
                            'process does anyone find out?'),
        ],
    ),
    5: dict(
        title='Describe the Robot',
        week=5, due='2026-10-19',
        paths=['ros2_ws/src/mitt_description/urdf/mitt_sensors.xacro'],
        measurements=[
            ('rear_camera_x_m', 'Part 3: base_link -> rear_camera_link translation x'),
            ('rear_camera_z_m', 'Part 3: the same translation z'),
            ('rear_camera_yaw_rad', 'Part 3: the yaw of that transform'),
            ('laser_x_m', 'Part 2: base_link -> laser_link translation x'),
        ],
        checks=check_lab5,
        blocks=[
            h2('Part 1 - Read the description you already have'),
            evidence('xacro', 'Evidence', 'wc -l on the expanded URDF and the xacro sources'),
            question('q1', 'Find **every** place `wheelbase` influences the expanded URDF.'),
            question('q2', '`base_link_height` is `0.09`, and so is `wheel_radius`. Why is '
                           'that not a coincidence, and where is `base_link` physically '
                           'located on the vehicle?'),
            h2('Part 2 - Look at the transform tree'),
            evidence('tf_laser', 'Evidence', 'tf2_echo base_link laser_link'),
            image('frames', 'Evidence', 'frames.pdf',
                  'The TF tree from `view_frames`, showing `rear_camera_link`.'),
            question('q3', 'Which node publishes the `base_link -> laser_link` transform, and '
                           'which publishes `odom -> base_link`? Why are those two '
                           'different nodes?'),
            question('q4', 'Is `base_link -> laser_link` static or dynamic? How can you tell '
                           'from the data alone?'),
            h2('Part 3 - Add a rear-facing camera'),
            evidence('tf_camera', 'Evidence', 'tf2_echo base_link rear_camera_link'),
            h2('Part 4 - Where sensor frames come from in reality'),
            question('q5', 'What is the procedure for determining the real LiDAR\'s transform '
                           'to `base_link`? How accurate can you expect to be?'),
            question('q6', 'If your measured LiDAR position is off by 3 cm in *x*, what '
                           'specifically goes wrong downstream? Name the affected subsystem.'),
            h2('Part 5 - Break it on purpose'),
            image('map_good', 'Evidence', 'map_good.png', 'The map before the 5 cm error.'),
            image('map_broken', 'Evidence', 'map_broken.png', 'The map after it.'),
            prose('diagnosis', 'Diagnosis',
                  'What the failure looked like, specifically. Why a **constant** offset '
                  'produces a **heading-dependent** error. And why this is much harder to '
                  'diagnose than a sensor that has simply stopped publishing.'),
        ],
    ),
}


# --- small helpers -----------------------------------------------------------

def die(msg):
    print(f'error: {msg}', file=sys.stderr)
    sys.exit(1)


def git(*args, cwd=None, check=True):
    r = subprocess.run(['git', *args], cwd=str(cwd or REPO),
                       capture_output=True, text=True)
    if check and r.returncode != 0:
        die(f'git {" ".join(args)} failed:\n{r.stderr.strip()}')
    return r.stdout.strip()


def read_config():
    if not CONFIG.exists():
        die('no .labconfig found. Run `bash scripts/lab.sh init` first.')
    cp = configparser.ConfigParser()
    cp.read(CONFIG)
    if 'student' not in cp:
        die('.labconfig has no [student] section. Delete it and re-run '
            '`bash scripts/lab.sh init`.')
    return cp['student']


def lab_spec(n):
    if n not in LABS:
        die(f'no such lab: {n}. Labs are 1-5.')
    return LABS[n]


def lab_dir(n):
    return REPO / 'labs' / f'lab{n}'


def env_or(name, default='(not set)'):
    return os.environ.get(name) or default


def os_release():
    try:
        for line in open('/etc/os-release'):
            if line.startswith('PRETTY_NAME='):
                return line.split('=', 1)[1].strip().strip('"')
    except OSError:
        pass
    return platform.platform()


# --- generate ----------------------------------------------------------------

def render_report(n, cfg):
    spec = lab_spec(n)
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds')
    commit = git('rev-parse', '--short', 'HEAD', check=False) or '(unknown)'
    dirty = ' (uncommitted changes present)' if git('status', '--porcelain', check=False) else ''

    out = []
    w = out.append
    w(f'# Lab {n} - {spec["title"]}')
    w('')
    w(f'<!-- lab-report v{FORMAT_VERSION} - generated by `bash scripts/lab.sh new {n}`.')
    w('     Keep every heading and the two tables below. Replace every line that')
    w(f'     begins with {TODO} or {PASTE}. -->')
    w('')
    w('## Submission')
    w('')
    w('| | |')
    w('|---|---|')
    w(f'| Student | {cfg.get("name", TODO)} |')
    w(f'| Uniqname | {cfg.get("uniqname", TODO)} |')
    w(f'| Lab | {n} - {spec["title"]} |')
    w(f'| Due | {spec["due"]} |')
    w(f'| Generated | {now} |')
    w(f'| Host | {socket.gethostname()} |')
    w(f'| OS | {os_release()} |')
    w(f'| ROS distro | {env_or("ROS_DISTRO")} |')
    w(f'| RMW_IMPLEMENTATION | {env_or("RMW_IMPLEMENTATION")} |')
    w(f'| ROS_LOCALHOST_ONLY | {env_or("ROS_LOCALHOST_ONLY")} |')
    w(f'| GZ_IP | {env_or("GZ_IP")} |')
    w(f'| Course commit | {commit}{dirty} |')
    w('')
    w('## AI assistance')
    w('')
    w('<!-- Required. Name the tool and say what you used it for, or write `none`.')
    w('     See the syllabus: declare it, own it, and never submit what you cannot')
    w('     explain. -->')
    w('')
    w(f'{TODO} - what tool, and for what. Write `none` if you used none.')
    w('')
    w('## Measurements')
    w('')
    w('<!-- Numbers only, one per line, keys exactly as generated. These are checked')
    w('     automatically, so a typo in a key reads as a missing measurement. -->')
    w('')
    w('```ini')
    width = max(len(k) for k, _ in spec['measurements'])
    for key, hint in spec['measurements']:
        w(f'{key.ljust(width)} = {TODO}    # {hint}')
    w('```')
    w('')

    for kind, a, b, c in spec['blocks']:
        if kind == 'h2':
            w(f'## {a}')
            w('')
        elif kind == 'evidence':
            key, lang = b.split('|')
            w(f'### {a} - `{key}`')
            w('')
            w(f'```{lang}')
            w(f'{PASTE} - {c}')
            w('```')
            w('')
        elif kind == 'question':
            w(f'### {a.upper()}. {b}')
            w('')
            w(f'{TODO} - your answer, in your own words.')
            w('')
        elif kind == 'prose':
            w(f'### {b}')
            w('')
            w(f'<!-- {c} -->')
            w('')
            w(f'{TODO} - your write-up.')
            w('')
        elif kind == 'image':
            title, filename = b.split('|')
            w(f'### {title} - `{filename}`')
            w('')
            w(f'![{filename}](evidence/{filename})')
            w('')
            w(f'<!-- {c} Save it as `labs/lab{n}/evidence/{filename}`. -->')
            w('')

    w('---')
    w('')
    w(f'Checked with `bash scripts/lab.sh check {n}`.')
    w('')
    return '\n'.join(out)


def required_images(n):
    return [b.split('|')[1] for kind, _, b, _ in lab_spec(n)['blocks'] if kind == 'image']


def cmd_init(args):
    cp = configparser.ConfigParser()
    if CONFIG.exists():
        cp.read(CONFIG)
    cur = cp['student'] if 'student' in cp else {}

    def ask(key, prompt):
        default = cur.get(key, '')
        suffix = f' [{default}]' if default else ''
        val = input(f'{prompt}{suffix}: ').strip()
        return val or default

    print('Lab submission setup. Stored in .labconfig, which is git-ignored.\n')
    name = ask('name', 'Your full name')
    uniqname = ask('uniqname', 'Your uniqname (the part before @umich.edu)')
    remote = ask('remote', 'Push URL of your private lab repo (blank to set later)')

    if not name or not uniqname:
        die('name and uniqname are both required.')
    if not re.fullmatch(r'[a-z0-9][a-z0-9._-]*', uniqname):
        die(f'uniqname {uniqname!r} should be lowercase letters, digits, . _ or -')

    cp['student'] = {'name': name, 'uniqname': uniqname, 'remote': remote}
    with open(CONFIG, 'w') as f:
        cp.write(f)
    print(f'\nwrote {CONFIG.relative_to(REPO)}')

    branch = f'student/{uniqname}'
    print(f'\nYour work goes on branch  {branch}')
    if remote:
        existing = git('remote', 'get-url', 'mine', check=False)
        if existing != remote:
            git('remote', 'remove', 'mine', check=False)
            git('remote', 'add', 'mine', remote)
            print(f'added remote  mine -> {remote}')
    else:
        print('\nNo remote yet. Create a PRIVATE repo, then:\n'
              '    git remote add mine <your push URL>\n'
              '    bash scripts/lab.sh init      # re-run to record it')
    return 0


def cmd_new(args):
    n = args.lab
    spec = lab_spec(n)
    cfg = read_config()
    d = lab_dir(n)
    report = d / 'REPORT.md'

    if report.exists() and not args.force:
        die(f'{report.relative_to(REPO)} already exists. Use --force to overwrite it '
            f'(your answers will be lost).')

    (d / 'evidence').mkdir(parents=True, exist_ok=True)
    report.write_text(render_report(n, cfg))

    print(f'created {report.relative_to(REPO)}')
    imgs = required_images(n)
    if imgs:
        print(f'        {(d / "evidence").relative_to(REPO)}/ - save {", ".join(imgs)} here')
    for p in spec['paths']:
        print(f'        also submitted from this lab: {p}')
    print(f'\nFill it in as you work, then:  bash scripts/lab.sh check {n}')
    return 0


# --- validate ----------------------------------------------------------------

FENCE = re.compile(r'^\s*```')


def split_fences(lines):
    """Yield (line, in_fence) so placeholder scanning can ignore fence markers."""
    inside = False
    for line in lines:
        if FENCE.match(line):
            inside = not inside
            yield line, 'fence'
        else:
            yield line, 'in' if inside else 'out'


def parse_report(text):
    """Return (headings, measurements, blocks) from a rendered report."""
    headings, measurements, blocks = [], {}, {}
    cur_key, cur_body, in_meas = None, [], False

    for line, where in split_fences(text.splitlines()):
        if where == 'fence':
            if cur_key is not None:
                blocks[cur_key] = cur_body
                cur_key, cur_body = None, []
            elif headings and headings[-1].startswith('### ') and '`' in headings[-1]:
                cur_key = headings[-1].split('`')[1]
                cur_body = []
            in_meas = bool(headings) and headings[-1] == '## Measurements'
            continue
        if where == 'in':
            if cur_key is not None:
                cur_body.append(line)
            if in_meas and '=' in line:
                k, v = line.split('=', 1)
                measurements[k.strip()] = v.split('#', 1)[0].strip()
            continue
        if line.startswith('## ') or line.startswith('### '):
            headings.append(line.rstrip())
    return headings, measurements, blocks


def validate(n, root, label=None):
    """
    Check one submission. `root` is the directory holding labs/labN.
    Returns (fails, warns) as lists of strings.
    """
    spec = lab_spec(n)
    fails, warns = [], []
    d = root / 'labs' / f'lab{n}'
    report = d / 'REPORT.md'

    if not report.exists():
        return ([f'{report} is missing. Generate it with `bash scripts/lab.sh new {n}`.'], [])

    text = report.read_text(errors='replace')
    headings, measurements, blocks = parse_report(text)

    # 1. Placeholders. The single most common incomplete submission.
    for i, (line, where) in enumerate(split_fences(text.splitlines()), start=1):
        if where == 'fence':
            continue
        s = line.strip()
        if s.startswith(TODO):
            fails.append(f'REPORT.md:{i}: still a {TODO} placeholder - "{s[:60]}"')
        elif s.startswith(PASTE):
            fails.append(f'REPORT.md:{i}: no output pasted here - "{s[:60]}"')

    # 2. Provenance filled in, and the environment that produced it.
    for field in ('Student', 'Uniqname'):
        m = re.search(rf'^\|\s*{field}\s*\|\s*(.*?)\s*\|', text, re.M)
        if not m or not m.group(1) or m.group(1).startswith(TODO):
            fails.append(f'REPORT.md: the {field} row of the Submission table is empty')
    for var, want in (('RMW_IMPLEMENTATION', 'rmw_fastrtps_cpp'), ('ROS_LOCALHOST_ONLY', '1')):
        m = re.search(rf'^\|\s*{var}\s*\|\s*(.*?)\s*\|', text, re.M)
        if m and m.group(1) != want:
            warns.append(f'{var} was {m.group(1)!r} when this report was generated, not '
                         f'{want!r} - the report was written from a shell that had not '
                         f'sourced setup_env.sh')

    # 3. AI declaration present and said something.
    m = re.search(r'^## AI assistance\s*$(.*?)^## ', text, re.M | re.S)
    body = re.sub(r'<!--.*?-->', '', m.group(1), flags=re.S).strip() if m else ''
    if not body:
        fails.append('REPORT.md: the AI assistance section is empty. Name the tool and what '
                     'you used it for, or write `none`.')

    # 4. Every generated heading still present, in order.
    want = []
    for kind, a, b, _ in spec['blocks']:
        if kind == 'h2':
            want.append(f'## {a}')
        elif kind == 'evidence':
            want.append(f'### {a} - `{b.split("|")[0]}`')
        elif kind == 'question':
            want.append(f'### {a.upper()}.')
        elif kind == 'prose':
            # Without this, deleting the heading AND its TODO together would
            # pass silently - the placeholder scan has nothing left to find.
            want.append(f'### {b}')
        elif kind == 'image':
            t, f = b.split('|')
            want.append(f'### {t} - `{f}`')
    got = '\n'.join(headings)
    for h in want:
        if h not in got:
            fails.append(f'REPORT.md: missing section "{h}" - do not delete generated headings')

    # 5. Evidence blocks carry something.
    for kind, _, b, _ in spec['blocks']:
        if kind != 'evidence':
            continue
        key = b.split('|')[0]
        lines = [x for x in blocks.get(key, []) if x.strip()]
        if any(x.strip().startswith(PASTE) for x in lines):
            continue        # already reported as a placeholder; do not say it twice
        if not lines:
            fails.append(f'REPORT.md: evidence block `{key}` is empty')
        elif len(lines) < 2:
            warns.append(f'REPORT.md: evidence block `{key}` is one line; paste the real '
                         f'output, not a summary of it')

    # 6. Measurements: present, and consistent with what the lab guarantees.
    for key, _ in spec['measurements']:
        if key not in measurements:
            fails.append(f'REPORT.md: measurement `{key}` is missing from the Measurements '
                         f'block')
        elif not measurements[key] or measurements[key].startswith(TODO):
            fails.append(f'REPORT.md: measurement `{key}` has no value')
    for level, msg in spec['checks'](measurements):
        (fails if level == 'FAIL' else warns).append(msg)

    # 7. Image deliverables exist and are not empty.
    for filename in required_images(n):
        p = d / 'evidence' / filename
        if not p.exists():
            fails.append(f'labs/lab{n}/evidence/{filename} is missing')
        elif p.stat().st_size == 0:
            fails.append(f'labs/lab{n}/evidence/{filename} is empty')

    # 8. Code and files the lab asked you to produce or restore.
    for rel in spec['paths']:
        p = root / rel
        if not p.exists():
            fails.append(f'{rel} is missing from the submission')

    # 9. "Restore it before submitting" - the step everyone forgets.
    fails.extend(check_restored(n, root))

    if label:
        fails = [f'{label}: {x}' for x in fails]
        warns = [f'{label}: {x}' for x in warns]
    return fails, warns


def check_restored(n, root):
    """
    Labs 4 and 5 end by telling you to put a value back. Both are invisible in
    the report and expensive later: a wheelbase of 0.75 or a shifted LiDAR
    silently poisons every subsequent lab on that clone.
    """
    out = []
    if n == 4:
        p = root / 'ros2_ws/src/mitt_description/config/mitt_dimensions.yaml'
        if p.exists():
            m = re.search(r'^\s*wheelbase\s*:\s*([0-9.]+)', p.read_text(), re.M)
            if m and abs(float(m.group(1)) - 0.63) > 1e-9:
                out.append(f'mitt_dimensions.yaml still has wheelbase: {m.group(1)} - '
                           f'Part 5 says to restore 0.63 before submitting')
    if n == 5:
        p = root / 'ros2_ws/src/mitt_description/urdf/mitt_sensors.xacro'
        if p.exists():
            text = p.read_text()
            if 'rear_camera_link' not in text:
                out.append('mitt_sensors.xacro has no rear_camera_link - Part 3 was not done, '
                           'or was not saved')
            pristine = git('show', f'origin/main:{p.relative_to(root)}', check=False)
            if pristine:
                def laser_origin(s):
                    m = re.search(r'laser_joint.*?<origin[^>]*>', s, re.S)
                    return m.group(0).split('<origin')[-1] if m else None
                a, b = laser_origin(text), laser_origin(pristine)
                if a and b and a != b:
                    out.append('the laser_joint origin differs from origin/main - Part 5 says '
                               'to restore the original value before submitting')
    return out


def report_results(fails, warns, n, what):
    for w in warns:
        print(f'WARN  {w}')
    for f in fails:
        print(f'FAIL  {f}')
    print()
    if fails:
        print(f'{len(fails)} problem{"s" if len(fails) != 1 else ""} '
              f'({len(warns)} warning{"s" if len(warns) != 1 else ""}). {what}')
        return 1
    print(f'Lab {n} OK - {len(warns)} warning{"s" if len(warns) != 1 else ""}.')
    return 0


def cmd_check(args):
    fails, warns = validate(args.lab, REPO)
    return report_results(fails, warns, args.lab, 'Nothing submitted.')


# --- submit ------------------------------------------------------------------

def cmd_submit(args):
    n = args.lab
    spec = lab_spec(n)
    cfg = read_config()
    uniqname = cfg['uniqname']
    branch = f'student/{uniqname}'

    # The offline bundle is a zip, not a clone. `new` and `check` work there;
    # `submit` cannot, and should say which of the two it is.
    if not subprocess.run(['git', 'rev-parse', '--git-dir'], cwd=str(REPO),
                          capture_output=True).returncode == 0:
        die(f'{REPO} is not a git repository, so there is nothing to commit to.\n'
            f'       Clone the course repository as environment.md section 6 describes, '
            f'and work there.')

    fails, warns = validate(n, REPO)
    if fails:
        return report_results(fails, warns, n, 'Nothing submitted.')
    for w in warns:
        print(f'WARN  {w}')

    current = git('rev-parse', '--abbrev-ref', 'HEAD')
    if current != branch:
        if git('rev-parse', '--verify', branch, check=False):
            git('checkout', branch)
        else:
            git('checkout', '-b', branch)
        print(f'switched to {branch}')

    paths = [f'labs/lab{n}', *spec['paths']]
    existing = [p for p in paths if (REPO / p).exists()]
    git('add', '--', *existing)
    if git('diff', '--cached', '--name-only'):
        git('commit', '-m', f'lab{n}: {uniqname}')
    sha = git('rev-parse', '--short', 'HEAD')

    pushed = False
    if git('remote', 'get-url', 'mine', check=False):
        r = subprocess.run(['git', 'push', '-u', 'mine', branch],
                           cwd=str(REPO), capture_output=True, text=True)
        pushed = r.returncode == 0
        if not pushed:
            print(f'WARN  push to `mine` failed:\n{r.stderr.strip()}')
    else:
        print('WARN  no `mine` remote configured; the commit is local only. '
              'Run `bash scripts/lab.sh init`.')

    # The zip is cut from the commit, so it cannot disagree with the SHA.
    dist = REPO / 'dist'
    dist.mkdir(exist_ok=True)
    out = dist / f'lab{n}_{uniqname}.zip'
    with open(out, 'wb') as f:
        r = subprocess.run(['git', 'archive', '--format=zip', f'--prefix=lab{n}_{uniqname}/',
                            'HEAD', '--', *existing],
                           cwd=str(REPO), stdout=f, stderr=subprocess.PIPE, text=False)
    if r.returncode != 0:
        die(f'git archive failed: {r.stderr.decode(errors="replace").strip()}')

    size = out.stat().st_size
    print()
    print('=' * 64)
    print(f' Lab {n} ready to submit')
    print('=' * 64)
    print(f'  Branch    {branch}')
    print(f'  Commit    {sha}' + ('' if pushed else '   (NOT pushed)'))
    print(f'  Archive   {out.relative_to(REPO)}  ({size / 1024:.0f} kB)')
    print(f'  Due       {spec["due"]}')
    print()
    print('  Upload the archive, and paste this line, into the course LMS:')
    print()
    print(f'      lab{n}  {uniqname}  {sha}')
    print()
    return 0


# --- grade -------------------------------------------------------------------

def cmd_grade(args):
    n = args.lab
    if not args.zips and not args.roster:
        die('grade needs --zips DIR or --roster FILE')

    rows = []
    if args.zips:
        zips = sorted(Path(args.zips).glob(f'lab{n}_*.zip')) + \
               sorted(Path(args.zips).glob('*.zip'))
        seen = set()
        for z in zips:
            if z in seen:
                continue
            seen.add(z)
            rows.append(grade_zip(n, z))
    if args.roster:
        for line in Path(args.roster).read_text().splitlines():
            line = line.split('#', 1)[0].strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) < 2:
                print(f'WARN  roster line ignored (want "uniqname url"): {line}')
                continue
            rows.append(grade_remote(n, parts[0], parts[1]))

    outdir = REPO / 'dist' / 'grade' / f'lab{n}'
    outdir.mkdir(parents=True, exist_ok=True)
    for who, fails, warns, detail in rows:
        (outdir / f'{who}.md').write_text(detail)

    print()
    print('=' * 64)
    print(f' Lab {n} - {len(rows)} submission{"s" if len(rows) != 1 else ""}')
    print('=' * 64)
    width = max([len(r[0]) for r in rows], default=8)
    for who, fails, warns, _ in sorted(rows):
        status = 'OK  ' if not fails else 'FAIL'
        print(f'  {status}  {who.ljust(width)}  {len(fails)} fail  {len(warns)} warn')
    clean = sum(1 for r in rows if not r[1])
    print()
    print(f'  {clean}/{len(rows)} pass the automated checks.')
    print(f'  Per-student detail: {outdir.relative_to(REPO)}/')
    print()
    return 0


def _grade_tree(n, who, root):
    fails, warns = validate(n, root)
    lines = [f'# Lab {n} - {who}', '']
    report = root / 'labs' / f'lab{n}' / 'REPORT.md'
    if report.exists():
        m = re.search(r'^## Submission\s*$(.*?)^## ', report.read_text(errors='replace'),
                      re.M | re.S)
        if m:
            lines += [m.group(1).strip(), '']
    lines += ['## Automated checks', '']
    if not fails and not warns:
        lines.append('All automated checks pass.')
    for f in fails:
        lines.append(f'- **FAIL** {f}')
    for w in warns:
        lines.append(f'- WARN {w}')
    lines += ['', '## Still to read by hand', '',
              '- Evidence quality (3) - is the pasted output real, and does it show what it '
              'claims?',
              '- Understanding (2) - are the answers in their own words?',
              '- The "break it on purpose" diagnosis, which is worth more than the happy path.']
    status = 'OK  ' if not fails else 'FAIL'
    print(f'{status}  {who}: {len(fails)} fail, {len(warns)} warn')
    return who, fails, warns, '\n'.join(lines) + '\n'


def grade_zip(n, path):
    tmp = Path(tempfile.mkdtemp(prefix='grade-'))
    try:
        with zipfile.ZipFile(path) as z:
            z.extractall(tmp)
        # git archive wrote a single top-level prefix directory.
        roots = [p for p in tmp.iterdir() if p.is_dir()]
        root = roots[0] if len(roots) == 1 else tmp
        who = path.stem.replace(f'lab{n}_', '')
        return _grade_tree(n, who, root)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def grade_remote(n, who, url):
    tmp = Path(tempfile.mkdtemp(prefix='grade-'))
    try:
        branch = f'student/{who}'
        r = subprocess.run(['git', 'clone', '--depth', '1', '--branch', branch,
                            url, str(tmp / 'r')], capture_output=True, text=True)
        if r.returncode != 0:
            print(f'FAIL  {who}: cannot clone {branch} from {url}')
            return who, [f'cannot clone {branch} from {url}: {r.stderr.strip()}'], [], \
                f'# Lab {n} - {who}\n\nCould not fetch `{branch}` from `{url}`.\n'
        return _grade_tree(n, who, tmp / 'r')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# --- selftest ----------------------------------------------------------------
#
# These rules decide part of a grade, so they get a guard of their own. Run by
# scripts/check_docs.sh. Each case is (name, lab, measurements, expected FAIL
# count) - a case that starts silently passing is as much a regression as one
# that starts failing.

SELFTEST = [
    ('lab1 nominal', 1, dict(topics_unsourced='7', topics_sourced='21', nodes_unsourced='1',
                             exit_code='0', stderr_bytes='0'), 0),
    ('lab1 unsourced sees more', 1, dict(topics_unsourced='25', topics_sourced='21'), 1),
    ('lab1 not silent', 1, dict(exit_code='1', stderr_bytes='40'), 2),
    ('lab2 nominal', 2, dict(drift_after_1_square_m='0.4',
                             drift_after_3_squares_m='1.3', stall_period_s='0.5'), 0),
    ('lab2 drift shrinks', 2, dict(drift_after_1_square_m='1.2',
                                   drift_after_3_squares_m='0.4'), 1),
    ('lab3 nominal', 3, dict(max_speed_param_mps='0.5', clamped_from_mps='3.0',
                             clamped_to_mps='0.5', scan_reliability='BEST_EFFORT'), 0),
    ('lab3 did not govern', 3, dict(max_speed_param_mps='0.5', clamped_from_mps='3.0',
                                    clamped_to_mps='3.0'), 1),
    ('lab4 nominal', 4, dict(measured_R_w030_m='1.71', measured_R_w100_m='1.49',
                             measured_R_w200_m='1.49',
                             measured_R_wheelbase_075_m='1.78'), 0),
    ('lab4 no clamp', 4, dict(measured_R_w100_m='0.50', measured_R_w200_m='0.25'), 2),
    ('lab4 wheelbase wrong way', 4, dict(measured_R_w200_m='1.49',
                                         measured_R_wheelbase_075_m='1.20'), 1),
    ('lab5 nominal', 5, dict(rear_camera_yaw_rad='3.142', rear_camera_x_m='-0.15'), 0),
    ('lab5 camera faces forward', 5, dict(rear_camera_yaw_rad='0.0'), 1),
    # A report with nothing filled in must not trip a numeric check - the
    # missing-measurement check reports that, and saying it twice is noise.
    *[(f'lab{n} empty', n, {}, 0) for n in LABS],
]


def cmd_selftest(args):
    bad = 0
    for name, n, m, want in SELFTEST:
        got = sum(1 for level, _ in LABS[n]['checks'](m) if level == 'FAIL')
        if got != want:
            print(f'FAIL  {name}: expected {want} FAIL, got {got}')
            bad += 1
    # Every report must render and then validate its own placeholders as errors.
    cfg = {'name': 'Selftest', 'uniqname': 'selftest'}
    for n in LABS:
        text = render_report(n, cfg)
        _, meas, _ = parse_report(text)
        missing = [k for k, _ in LABS[n]['measurements'] if k not in meas]
        if missing:
            print(f'FAIL  lab{n} template: measurements not parseable: {missing}')
            bad += 1
    if bad:
        print(f'\n{bad} selftest failure(s).')
        return 1
    print(f'lab_report selftest OK - {len(SELFTEST)} cases, {len(LABS)} templates.')
    return 0


# --- entry point -------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(prog='lab.sh', description=__doc__.split('\n')[1])
    sub = p.add_subparsers(dest='cmd', required=True)

    s = sub.add_parser('init', help='record your name, uniqname and lab repo')
    s.set_defaults(fn=cmd_init)

    s = sub.add_parser('new', help='generate a report skeleton for a lab')
    s.add_argument('lab', type=int)
    s.add_argument('--force', action='store_true', help='overwrite an existing report')
    s.set_defaults(fn=cmd_new)

    s = sub.add_parser('check', help='validate a report without submitting')
    s.add_argument('lab', type=int)
    s.set_defaults(fn=cmd_check)

    s = sub.add_parser('submit', help='validate, commit, push, and build the archive')
    s.add_argument('lab', type=int)
    s.set_defaults(fn=cmd_submit)

    s = sub.add_parser('grade', help='instructor: check a whole cohort at once')
    s.add_argument('lab', type=int)
    s.add_argument('--zips', metavar='DIR', help='directory of submitted .zip files')
    s.add_argument('--roster', metavar='FILE', help='lines of "uniqname  clone-url"')
    s.set_defaults(fn=cmd_grade)

    s = sub.add_parser('selftest', help='check the grading rules themselves')
    s.set_defaults(fn=cmd_selftest)

    args = p.parse_args()
    sys.exit(args.fn(args))


if __name__ == '__main__':
    main()
