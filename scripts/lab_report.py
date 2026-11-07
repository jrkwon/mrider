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
The earlier deliverable lists asked for four to six loose files per lab. At 13
students x 5 labs that is over 300 files, in 13 different layouts, with
colliding names once unpacked, and with every objective fact - `FAIL: 0`, both
controllers `active`, 2 topics versus 21 - checked by eye.

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

WHERE THE REST OF IT IS
-----------------------
This file is the student's half and the entry point: generate a report,
validate one, submit one.

    lab_labs.py     what each lab asks for and what counts as right. Imports
                    nothing, so a lab definition cannot reach the filesystem.
    lab_grading.py  the instructor's half - grade a cohort, record the marks.
                    NOT shipped in the student bundle, which is why it moved.

The dependency runs one way only: lab_labs <- lab_report <- lab_grading. The
single upward reference is the lazy import in main(), which is also what lets
`grade` be absent from a bundle and say so in a sentence.
"""
import argparse
import configparser
import os
import platform
import re
import socket
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# lab_labs sits beside this file. Python puts a script's own directory on
# sys.path, and the two callers that import this module (scripts/check_docs.sh
# and scripts/provision_labs.sh) already insert `scripts`, so this line is only
# needed for a third kind of caller: one that loads this file BY PATH, with
# importlib. Two lines here means such a caller keeps working.
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from lab_labs import LABS, SELFTEST                            # noqa: E402

REPO = Path(__file__).resolve().parent.parent
CONFIG = REPO / '.labconfig'
FORMAT_VERSION = 1

# --- where student repositories live -----------------------------------------
#
# One private repository per student, created by the instructor with
# scripts/provision_labs.sh before term starts. Students are collaborators with
# push access: they commit freely and cannot change visibility or delete it.
#
# WHY THE INSTRUCTOR CREATES THEM, AND NOT THE STUDENTS
# GitHub Classroom did exactly this underneath, and was retired on 2026-08-28.
# Doing it by hand is thirty lines of `gh api`, and it removes 13 chances for a
# repository to end up public - which would publish this course's lab solutions
# to the next cohort - or to be created without the instructor on it, which
# makes the work ungradeable at the moment it is due.
#
# WHY NOT THE `bimilab` ORG
# bimilab is on the Team plan, where every outside collaborator on a private
# repository consumes a paid seat regardless of permission level. 13 students
# there is ~13 seats. GitHub Free for organizations gives unlimited private
# repositories and unlimited collaborators, which is all this needs.
COURSE_ORG = 'bimi-courses'     # change to move orgs
COURSE_TERM = '2026-fall'       # change once a year
REPO_PREFIX = 'mrider-labs'


def student_repo(uniqname):
    """Repository name for one student. The term keeps cohorts from colliding."""
    return f'{REPO_PREFIX}-{COURSE_TERM}-{uniqname}'


def student_repo_url(uniqname):
    return f'https://github.com/{COURSE_ORG}/{student_repo(uniqname)}.git'


# Placeholder tokens the generator writes and the validator refuses to accept
# back. Distinct prefixes so the error message can say what kind of thing is
# missing rather than just "a placeholder".
TODO = 'TODO'
PASTE = 'PASTE'


# --- small helpers -----------------------------------------------------------

def die(msg):
    print(f'error: {msg}', file=sys.stderr)
    sys.exit(1)


def git(*args, cwd=None, check=True, timeout=None):
    """Run git. `timeout` is REQUIRED of anything that touches the network:
    subprocess.run raises TimeoutExpired, and check=False does not suppress it,
    so a caller that wants to survive a dead network has to catch it."""
    r = subprocess.run(['git', *args], cwd=str(cwd or REPO),
                       capture_output=True, text=True, timeout=timeout)
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


def commits_behind(fetch=False):
    """
    How many commits origin/main is ahead of HEAD, or None if unknowable.

    WHY THIS IS CHECKED AT ALL
    `submit` commits the student's lab on top of their working tree, so their
    branch carries whatever course repository they last pulled - lab
    instructions, check_env.sh, setup_env.sh, this file. A clone taken in Week 0
    and never pulled is a clone that predates the submission tooling entirely.
    Nothing about that announces itself: the labs still open, the twin still
    runs, and the page they are reading on the website is the current one while
    the file in front of them is not.
    """
    if fetch:
        # Network, so keep it short and never fatal - a student working offline
        # is still allowed to write their report. `timeout=` ALONE does not
        # deliver that: subprocess.run RAISES TimeoutExpired, and check=False
        # does nothing about it, so the promise in the sentence above was not
        # kept by the code under it. A dead network does not just make this
        # unknowable, it killed the whole report. Caught since 2026-11-07.
        try:
            subprocess.run(['git', 'fetch', '--quiet', 'origin', 'main'],
                           cwd=str(REPO), capture_output=True, timeout=20,
                           check=False)
        except (subprocess.TimeoutExpired, OSError):
            return None          # unknowable, which is what the caller prints
    try:
        out = git('rev-list', '--count', 'HEAD..origin/main', check=False,
                  timeout=20)
    except (subprocess.TimeoutExpired, OSError):
        return None
    try:
        return int(out)
    except ValueError:
        return None


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
    notes = []
    if git('status', '--porcelain', check=False):
        notes.append('uncommitted changes present')
    # Recorded in the report so the grader sees it too, not only the student.
    behind = commits_behind()
    if behind:
        notes.append(f'{behind} commits behind origin/main')
    dirty = f' ({"; ".join(notes)})' if notes else ''

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
    uniqname = ask('uniqname', 'Your student ID (학번) - exactly as you gave it on the form')

    if not name or not uniqname:
        die('name and student ID are both required.')
    # Your repository is named from this, so a different answer here derives a
    # URL for a repository that does not exist - and the failure does not
    # surface until the push at the end of `submit`.
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', uniqname):
        die(f'student ID {uniqname!r} should be letters, digits, . _ or -')

    # Your repository already exists and its name follows from your uniqname, so
    # the answer here is almost always Enter. Typing a URL is the escape hatch,
    # not the path.
    derived = student_repo_url(uniqname)
    print(f'\nYour lab repository is\n    {derived}')
    remote = input('Push URL [Enter to accept]: ').strip() or cur.get('remote') or derived

    cp['student'] = {'name': name, 'uniqname': uniqname, 'remote': remote}
    with open(CONFIG, 'w') as f:
        cp.write(f)
    print(f'\nwrote {CONFIG.relative_to(REPO)}')

    branch = f'student/{uniqname}'
    existing = git('remote', 'get-url', 'mine', check=False)
    if existing != remote:
        git('remote', 'remove', 'mine', check=False)
        git('remote', 'add', 'mine', remote)
    print(f'\n  origin  {git("remote", "get-url", "origin", check=False) or "(none)"}')
    print(f'  mine    {remote}')
    print(f'  branch  {branch}')
    print('\nIf you have not accepted the repository invitation yet, do that now:')
    print('    https://github.com/notifications')
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

    # Before generating, not after: a stale clone means stale lab instructions,
    # and that is cheap to fix now and expensive to discover at the deadline.
    behind = commits_behind(fetch=True)
    if behind:
        print(f'WARN  your course repository is {behind} commits behind origin/main.')
        print('WARN  the lab instructions, check_env.sh and this tooling may all be old.')
        print('WARN  fix it first:   git pull origin main\n')

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
    m = re.search(r'^\|\s*Course commit\s*\|\s*(.*?)\s*\|', text, re.M)
    if m and 'behind origin/main' in m.group(1):
        warns.append(f'generated from a stale clone - {m.group(1)}. The lab instructions '
                     f'this was written against may not be the current ones.')
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
            # By far the most likely cause, and it gives a bare 403 that says
            # nothing about invitations. The repository exists; you are simply
            # not on it yet.
            print('WARN  if that mentions permission or 403: you may not have '
                  'accepted the\n      repository invitation yet. One click at '
                  'https://github.com/notifications')
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

# --- selftest ---------------------------------------------------------------

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

def _grading():
    """lab_grading, imported only when an instructor command is actually run.

    Two reasons it is lazy rather than a top-level import. It is the one
    reference that points UP the dependency chain, and doing it inside a
    function keeps that from being a cycle. And the student bundle does not
    ship the file, so `grade` there has to fail in a sentence rather than
    in a traceback at import time, before argparse has even parsed.
    """
    try:
        import lab_grading
    except ImportError:
        die('grade and scores are instructor commands. scripts/lab_grading.py '
            'is not in this bundle;\n'
            '       run them from a clone of the course repository.')
    return lab_grading


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
    s.add_argument('--roster', metavar='FILE', help='lines of "uniqname  github-username"')
    s.set_defaults(fn=lambda a: _grading().cmd_grade(a))

    s = sub.add_parser('scores', help='instructor: record marks and export for the LMS')
    s.add_argument('lab', type=int)
    s.set_defaults(fn=lambda a: _grading().cmd_scores(a))

    s = sub.add_parser('selftest', help='check the grading rules themselves')
    s.set_defaults(fn=cmd_selftest)

    args = p.parse_args()
    sys.exit(args.fn(args))


if __name__ == '__main__':
    # Running this file makes it `__main__`, so lab_grading's `import
    # lab_report` would load a SECOND copy of it - two REPO constants, two
    # die(). Registering this one under its own name first means both halves
    # read the same module object, which is also what lets a test point
    # grading at a temporary tree by assigning lab_report.REPO.
    sys.modules.setdefault('lab_report', sys.modules['__main__'])
    main()
