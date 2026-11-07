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
What each lab asks for, and what counts as a right answer.

This is data and arithmetic: the block types a report is made of, the five
per-lab measurement checks, the LABS table, and the self-test cases that pin
the checks to known-good and known-bad measurements.

WHY IT IS ITS OWN FILE
----------------------
It imports nothing. Not re, not Path, not subprocess - a lab definition has no
business touching the filesystem, the network or git, and keeping it in a file
that cannot reach them makes that a property rather than a habit.

That is also what makes it the bottom of the stack: lab_report imports this,
lab_grading imports lab_report, and nothing imports upwards. The thing that
changes most often - a due date, a band, a new question - changes here, where
there is nothing to break.

WHAT A CHECK MAY AND MAY NOT DO
-------------------------------
Each check takes the parsed `key = value` measurements and returns a list of
(level, message). FAIL means the submission contradicts the lab's physics -
drift that shrinks, a governor that did not govern, a rear camera pointing
forwards. WARN means a number is outside the band the 2026 cohort produced,
which is a legitimate difference between machines often enough that it must
not cost a mark.

A check never reads a file and never prints. It is handed numbers and returns
sentences, which is why SELFTEST can exercise all of it in a dict literal.
"""

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
    _band(out, m, 'topics_unsourced', 1, 12, 'the whole 2026 cohort measured 2')
    _band(out, m, 'topics_sourced', 15, 30, 'the whole 2026 cohort measured 21')
    # 0 is the expected answer. A non-zero count means a SECOND mismatch as well
    # (usually RMW_IMPLEMENTATION differing between the shell and the simulator),
    # which is a different and more misleading failure - worth looking at, not
    # worth failing.
    if nodes is not None and nodes > 0:
        out.append(('WARN', f'nodes_unsourced = {nodes:g}; the 2026 cohort all measured 0. '
                            f'A partial graph usually means RMW_IMPLEMENTATION differs too'))
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


# --- selftest ----------------------------------------------------------------
#
# These rules decide part of a grade, so they get a guard of their own. Run by
# scripts/check_docs.sh. Each case is (name, lab, measurements, expected FAIL
# count) - a case that starts silently passing is as much a regression as one
# that starts failing.

SELFTEST = [
    # What the 2026 cohort actually produced, all twelve of them.
    ('lab1 nominal', 1, dict(topics_unsourced='2', topics_sourced='21', nodes_unsourced='0',
                             exit_code='0', stderr_bytes='0'), 0),
    # A partial graph is legal but means a second mismatch; warn, never fail.
    ('lab1 partial graph', 1, dict(topics_unsourced='7', topics_sourced='21',
                                   nodes_unsourced='1', exit_code='0', stderr_bytes='0'), 0),
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
