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
The instructor half: grade a cohort at once, then record the marks.

    bash scripts/lab.sh grade  1 --zips ~/Downloads/lab1
    bash scripts/lab.sh grade  1 --roster course/roster-2026-fall.txt
    bash scripts/lab.sh scores 1

WHY THIS IS NOT IN lab_report.py
--------------------------------
scripts/export_student_bundle.sh copies the lab tooling into the zip students
unpack. Before this file existed, that shipped them the grader: read_roster,
the late-penalty table, where marks are stored, and every rule for turning an
archive into a row. None of it is secret - grading.md states the policy - but
none of it is theirs to run either, and it was the larger half of the file
they open when they want to know what `check` does.

The bundle now copies lab.sh, lab_report.py and lab_labs.py. It does not copy
this file, and `lab.sh grade` in a bundle says so in one sentence instead of
failing somewhere inside argparse.

WHY `R.REPO` AND NOT `from lab_report import REPO`
--------------------------------------------------
A from-import copies the value. Reading it through the module keeps one
definition, and lets a test point grading at a temporary tree by assigning
lab_report.REPO - which is exactly how scripts/tests/test_grading.py drives
cmd_grade without writing into this repository.

WHAT GOES WRONG HERE, AND HAS
-----------------------------
Every defect an external review found on 2026-11-07 was on this path, and
three were silent: a uniqname read from a student-written file became a
filename, "keep the last" kept the first download so a resubmission was
graded as the work it replaced, and one corrupt archive ended grading for
everyone behind it. scripts/tests/test_grading.py exists for those three.
"""
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

import lab_report as R

# --- grade -------------------------------------------------------------------

# A uniqname becomes a FILENAME in dist/grade/, and it is read out of a file a
# student wrote. Without this, "../../../docs/build/03-electrical" in the
# Uniqname cell of a submitted report overwrites a page of the build guide the
# next time anyone grades, and "/tmp/x" escapes by the other route entirely,
# because Path('/a/b') / '/tmp/x' is '/tmp/x' - an absolute right-hand side
# discards the left. Neither needs a malicious student; a paste accident is
# enough.
UNIQNAME_RE = re.compile(r'^[a-z][a-z0-9_-]{1,30}$', re.I)


def safe_who(who, where):
    """A uniqname that is safe to use as a path component, or a complaint."""
    if not UNIQNAME_RE.match(who or ''):
        return None, (f'{where}: {who!r} is not a usable uniqname - letters, '
                      f'digits, dash and underscore only')
    return who, None


def read_roster(path):
    """
    Parse the cohort roster into (uniqname, github_username, clone_url).

    ONE FILE, read by both scripts/provision_labs.sh and `grade --roster`, so a
    late registrant is added in exactly one place.

        # uniqname   github-username   [clone url, if not the standard one]
        jdoe         janedoe99

    The URL is derived from COURSE_ORG/R.COURSE_TERM unless a third column
    overrides it - which is the escape hatch for a student who, for whatever
    reason, is submitting from somewhere else.
    """
    out = []
    for lineno, raw in enumerate(Path(path).read_text().splitlines(), start=1):
        line = raw.split('#', 1)[0].strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) == 1:
            print(f'WARN  {path}:{lineno}: no github username, ignoring: {line}')
            continue
        who, github = parts[0], parts[1]
        url = parts[2] if len(parts) > 2 else R.student_repo_url(who)
        out.append((who, github, url))
    return out


def cmd_grade(args):
    n = args.lab
    if not args.zips and not args.roster:
        R.die('grade needs --zips DIR or --roster FILE')

    rows = []
    arrived = {}
    if args.zips:
        zips = sorted(Path(args.zips).glob(f'lab{n}_*.zip')) + \
               sorted(Path(args.zips).glob('*.zip'))
        seen = set()
        for z in zips:
            if z in seen:
                continue
            seen.add(z)
            # One unreadable archive is one student's problem, not the run's.
            # Without this, a truncated download ends grading for everybody
            # behind it in the directory listing.
            try:
                row = grade_zip(n, z)
            except (zipfile.BadZipFile, ValueError, OSError) as exc:
                print(f'SKIP  {z.name}: {exc}')
                rows.append((None, [f'{z.name}: {exc}'], [], ''))
                continue
            rows.append(row)
            # Arrival time, kept beside the row. For an LMS download the file
            # mtime is when it was fetched, which is the only ordering signal
            # the archive carries.
            arrived[id(row)] = z.stat().st_mtime
    if args.roster:
        for who, _github, url in read_roster(args.roster):
            rows.append(grade_remote(n, who, url))

    # Rejected identities never reach the output directory, and they are not
    # silently dropped either - an ungradeable submission is a thing a human
    # has to deal with, so it is printed and counted.
    rejected = [r for r in rows if r[0] is None]
    rows = [r for r in rows if r[0] is not None]
    for _who, fails, _warns, _detail in rejected:
        print(f'SKIP  {fails[0]}')

    # A duplicate LMS download is the same submission twice, not two students.
    # Identity comes from inside the archive, so they collapse - but WHICH copy
    # to keep was wrong, and wrong silently.
    #
    # It kept the last in SORTED FILENAME order, reasoning that a later file is
    # a resubmission. Filename order is not arrival order. The LMS appends "-1"
    # to a second copy and '-' (0x2D) sorts before '.' (0x2E):
    #
    #     sorted(['lab1_smith.zip', 'lab1_smith-1.zip'])
    #       -> ['lab1_smith-1.zip', 'lab1_smith.zip']
    #
    # so "keep the last" kept the FIRST download - the opposite of the comment.
    # Nobody would have noticed: the wrong archive grades cleanly and a student
    # is marked on work they replaced.
    if args.zips:
        by_who = {}
        for r in rows:
            who = r[0]
            prev = by_who.get(who)
            if prev is None:
                by_who[who] = r
                continue
            t_new, t_old = arrived.get(id(r), 0), arrived.get(id(prev), 0)
            if abs(t_new - t_old) < 1.0:
                print(f'note  {who}: two archives arrived together - the same '
                      f'submission fetched twice; keeping one')
            else:
                print(f'note  {who}: more than one archive; keeping the one '
                      f'that arrived later (by file mtime)')
            if t_new > t_old:
                by_who[who] = r
        rows = list(by_who.values())

    outdir = R.REPO / 'dist' / 'grade' / f'lab{n}'
    outdir.mkdir(parents=True, exist_ok=True)
    for who, fails, warns, detail in rows:
        out = outdir / f'{who}.md'
        # Belt and braces. safe_who() already refused anything with a path
        # separator in it, but this is the line that actually writes, and a
        # later code path that forgets to validate should fail here rather
        # than somewhere in the repository.
        assert out.resolve().parent == outdir.resolve(), \
            f'refusing to write outside {outdir}: {out}'
        out.write_text(detail)
    # The per-student .md is rewritten on every run and dist/ is git-ignored, so
    # neither is a place to keep a grade. This is the handoff to `scores`.
    (outdir / 'auto.tsv').write_text(
        ''.join(f'{who}\t{len(f)}\t{len(w)}\n' for who, f, w, _ in sorted(rows)))

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
    print(f'  Per-student detail: {outdir.relative_to(R.REPO)}/')
    print()
    return 0


def _grade_tree(n, who, root):
    fails, warns = R.validate(n, root)
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


# A lab archive is a few dozen text files. These ceilings are two orders of
# magnitude above that and still refuse a zip bomb, which decompresses to
# whatever it likes from a few hundred kilobytes on disk.
MAX_MEMBERS = 4000
MAX_UNPACKED = 256 * 1024 * 1024        # 256 MiB


def grade_zip(n, path):
    tmp = Path(tempfile.mkdtemp(prefix='grade-'))
    try:
        with zipfile.ZipFile(path) as z:
            infos = z.infolist()
            # Check the declared sizes BEFORE extracting. Reading first and
            # measuring afterwards is how the disk fills.
            if len(infos) > MAX_MEMBERS:
                raise ValueError(f'{len(infos)} members, limit {MAX_MEMBERS}')
            total = sum(i.file_size for i in infos)
            if total > MAX_UNPACKED:
                raise ValueError(f'unpacks to {total / 1e6:.0f} MB, limit '
                                 f'{MAX_UNPACKED / 1e6:.0f} MB')
            # zipfile.extractall sanitises member paths - leading separators
            # and .. components are stripped - so zip-slip is the stdlib's
            # problem and not ours. The identity inside the report is not,
            # which is what safe_who() is for.
            z.extractall(tmp)
        # git archive wrote a single top-level prefix directory.
        roots = [p for p in tmp.iterdir() if p.is_dir()]
        root = roots[0] if len(roots) == 1 else tmp
        # The LMS renames downloads - it prefixes student names, and appends
        # "-1" to a second copy of the same file. Trusting the filename turns a
        # duplicate download into a second student and a prefixed name into a
        # row that no longer matches the roster. The report states who wrote it;
        # read that, and keep the filename only as a fallback.
        who = None
        report = root / 'labs' / f'lab{n}' / 'REPORT.md'
        if report.exists():
            m = re.search(r'^\|\s*Uniqname\s*\|\s*(\S+?)\s*\|',
                          report.read_text(errors='replace'), re.M)
            if m:
                who = m.group(1)
        if not who:
            who = path.stem.replace(f'lab{n}_', '')
        who, complaint = safe_who(who, path.name)
        if complaint:
            # Do not guess a replacement. A submission whose identity cannot be
            # trusted is one a human has to look at.
            return None, [complaint], [], complaint + '\n'
        return _grade_tree(n, who, root)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def grade_remote(n, who, url):
    tmp = Path(tempfile.mkdtemp(prefix='grade-'))
    try:
        branch = f'student/{who}'
        # A clone with no limit is a grading run that one unreachable student
        # repository can stop for good, with thirteen more behind it.
        try:
            r = subprocess.run(['git', 'clone', '--depth', '1',
                                '--branch', branch, url, str(tmp / 'r')],
                               capture_output=True, text=True, timeout=120)
        except subprocess.TimeoutExpired:
            print(f'FAIL  {who}: clone of {branch} timed out after 120 s')
            return who, [f'clone of {branch} from {url} timed out after 120 s'], \
                [], (f'# Lab {n} - {who}\n\nCloning `{branch}` from `{url}` '
                     f'timed out. Graded as unfetched, not as unsubmitted.\n')
        if r.returncode != 0:
            print(f'FAIL  {who}: cannot clone {branch} from {url}')
            return who, [f'cannot clone {branch} from {url}: {r.stderr.strip()}'], [], \
                f'# Lab {n} - {who}\n\nCould not fetch `{branch}` from `{url}`.\n'
        return _grade_tree(n, who, tmp / 'r')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# --- scores ------------------------------------------------------------------
#
# WHERE A GRADE LIVES
#
# Not in dist/grade/lab<N>/*.md: those are regenerated by every `grade` run, and
# dist/ is git-ignored, so a number typed there is lost twice over.
#
# It lives in course/scores-<term>-lab<N>.tsv, which this command creates and
# never overwrites. That file is git-ignored on purpose - it is student grade
# data and this repository is public.

SCORE_HEADER = """\
# MRider lab {n} - marks. Git-ignored; this repository is public.
#
# Fill in EVIDENCE (0-3) and UNDERSTANDING (0-2). Leave a dot until you have
# read the report. `auto` is correctness+reproducibility, proposed from the
# automated checks - edit it if you disagree; it is a suggestion, not a verdict.
#
# late = whole days past the due date, from the LMS timestamp (not the commit).
#        -10%/day, floor 50%, zero after 7 days.
#
# uniqname\tauto\tevidence\tunderstanding\tlate\tnote
"""


def scores_path(n):
    return R.REPO / 'course' / f'scores-{R.COURSE_TERM}-lab{n}.tsv'


def late_multiplier(days):
    """The policy in grading.md, in one place."""
    if days <= 0:
        return 1.0
    if days > 7:
        return 0.0
    return max(0.5, 1.0 - 0.10 * days)


def cmd_scores(args):
    n = args.lab
    R.lab_spec(n)
    sp = scores_path(n)
    auto = R.REPO / 'dist' / 'grade' / f'lab{n}' / 'auto.tsv'

    if not sp.exists():
        if not auto.exists():
            R.die(f'run `bash scripts/lab.sh grade {n} ...` first - it is what '
                f'produces the list of submissions.')
        rows = []
        for line in auto.read_text().splitlines():
            who, fails, _warns = line.split('\t')
            rows.append(f'{who}\t{0 if int(fails) else 5}\t.\t.\t0\t')
        sp.write_text(SCORE_HEADER.format(n=n) + '\n'.join(rows) + '\n')
        print(f'created {sp.relative_to(R.REPO)} with {len(rows)} students')
        print(f'\nFill in the evidence and understanding columns, then re-run:')
        print(f'    bash scripts/lab.sh scores {n}')
        return 0

    marked, pending, out = [], [], []
    for lineno, raw in enumerate(sp.read_text().splitlines(), 1):
        line = raw.split('#', 1)[0].rstrip()
        if not line.strip():
            continue
        f = line.split('\t')
        if len(f) < 5:
            R.die(f'{sp.name}:{lineno}: expected 5 tab-separated columns, got {len(f)}')
        who, a, e, u, late = (x.strip() for x in f[:5])
        note = f[5].strip() if len(f) > 5 else ''
        if '.' in (a, e, u):
            pending.append(who)
            continue
        try:
            a, e, u, late = int(a), int(e), int(u), int(late)
        except ValueError:
            R.die(f'{sp.name}:{lineno}: auto/evidence/understanding/late must be whole numbers')
        for name, v, hi in (('auto', a, 5), ('evidence', e, 3), ('understanding', u, 2)):
            if not 0 <= v <= hi:
                R.die(f'{sp.name}:{lineno}: {name}={v} is outside 0-{hi}')
        raw_total = a + e + u
        final = round(raw_total * late_multiplier(late), 1)
        marked.append((who, a, e, u, late, raw_total, final, note))
        out.append(f'{who},{raw_total},{late},{final}')

    print(f'{"uniqname":<12} {"auto":>4} {"ev":>3} {"und":>4} {"late":>5} '
          f'{"raw":>4} {"final":>6}')
    print('-' * 46)
    for who, a, e, u, late, rawt, fin, note in marked:
        flag = '  <- late' if late else ''
        print(f'{who:<12} {a:>4} {e:>3} {u:>4} {late:>5} {rawt:>4} {fin:>6.1f}{flag}')
    if marked:
        avg = sum(m[6] for m in marked) / len(marked)
        print('-' * 46)
        print(f'{"mean":<12} {"":>4} {"":>3} {"":>4} {"":>5} {"":>4} {avg:>6.1f}')
    if pending:
        print(f'\n{len(pending)} not yet marked: {", ".join(pending)}')

    if marked:
        csv = R.REPO / 'dist' / 'grade' / f'lab{n}' / 'final.csv'
        csv.parent.mkdir(parents=True, exist_ok=True)
        csv.write_text('uniqname,raw,late_days,final\n' + '\n'.join(out) + '\n')
        print(f'\nLMS upload: {csv.relative_to(R.REPO)}')
    return 0

