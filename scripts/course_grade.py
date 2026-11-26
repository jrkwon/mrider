#!/usr/bin/env python3
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
"""
course_grade.py - the team rubrics and the course total, from the marks files.

    python3 scripts/course_grade.py --init      # create the empty marks files
    python3 scripts/course_grade.py             # the table, as far as it is marked
    python3 scripts/course_grade.py --csv dist/grade/course.csv

Instructor tool. The weights and rubrics are the ones published in
docs/course/grading.md; the peer rule is the one in docs/course/teams.md.
Change them there first, then here.

WHAT IT READS, all in course/ and all git-ignored (`/course/scores-*.tsv`):

    scores-<term>-lab<N>.tsv       per student; written by `lab.sh scores N`
    scores-<term>-mid.tsv          per team; mid-semester presentation
    scores-<term>-deliverable.tsv  per team; team deliverable
    scores-<term>-final.tsv        per team; final demo and presentation
    scores-<term>-students.tsv     per student; team, track, peer multiplier,
                                   participation

A dot means "not marked yet". A component with a dot anywhere in its row is
left out of that student's total, and the total is printed with the weight
it is out of, so a half-marked term never reads as a low grade.

THE ARITHMETIC
    labs         30 = 5 labs x 6, each (auto+evidence+understanding)/10 with
                      the late multiplier from lab_grading.py
    mid          15 = team rubric /100
    deliverable  25 = team rubric /100 x the student's peer multiplier,
                      limited to the full 25
    final        20 = team rubric /100
    participation 10 = the student's mark /10

The peer multiplier is typed in by hand, after scripts/peer_eval.py has
printed a suggestion and the instructor has read it against the free text,
the commits and the standups. This script never computes one.

OUTPUT is grade data and this repository is public: stdout, or a path you
name under dist/, which is git-ignored.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lab_grading as G  # noqa: E402
import lab_report as R  # noqa: E402

LABS = (1, 2, 3, 4, 5)
LAB_WEIGHT = 6.0

# name -> (weight in the course, ((column, max points), ...)); grading.md
TEAM_RUBRICS = {
    'mid': (15.0, (('demonstrated', 30), ('evidence', 25), ('interface', 20),
                   ('risk', 15), ('delivery', 10))),
    'deliverable': (25.0, (('functionality', 30), ('evidence', 25), ('quality', 20),
                           ('integration', 15), ('failure', 10))),
    'final': (20.0, (('autonomous', 25), ('depth', 20), ('failure', 20),
                     ('reproducibility', 15), ('safety', 10), ('presentation', 10))),
}
PARTICIPATION_WEIGHT = 10.0
STUDENT_COLS = ('uniqname', 'team', 'track', 'peer_mult', 'participation', 'note')
# teams.md: the multiplier a peer evaluation alone can give
PEER_MIN, PEER_MAX = 0.85, 1.15

TEAM_HEADER = """\
# MRider {what} - marks, one row per team. Git-ignored; this repository is public.
#
# Rubric in docs/course/grading.md. Maximum per column:
#   {maxes}
# Leave a dot until the team has been marked.
#
# {cols}
"""
STUDENT_HEADER = """\
# MRider - per-student rows. Git-ignored; this repository is public.
#
# team          1-3, the vehicle number
# track         E, C, S or W (free text; it is only printed)
# peer_mult     the multiplier on the Team deliverable. A dot means 1.00.
#               scripts/peer_eval.py suggests 0.85-1.15 from peer evaluation 2;
#               type it here only after reading the free text and the commits.
# participation 0-10. A dot until marked.
#
# {cols}
"""


def die(msg):
    sys.exit(f'course_grade: {msg}')


def rows(path):
    """Yield (lineno, [fields]) for the data lines of a marks file."""
    for lineno, raw in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        line = raw.split('#', 1)[0].rstrip()
        if line.strip():
            yield lineno, [x.strip() for x in line.split('\t')]


def number(path, lineno, name, text, lo, hi):
    try:
        v = float(text)
    except ValueError:
        die(f'{path.name}:{lineno}: {name} is "{text}", not a number or a dot')
    if not lo <= v <= hi:
        die(f'{path.name}:{lineno}: {name}={text} is outside {lo:g}-{hi:g}')
    return v


def read_lab(path):
    """-> {uniqname: points out of 10, or None while unmarked}"""
    out = {}
    for lineno, f in rows(path):
        if len(f) < 5:
            die(f'{path.name}:{lineno}: expected 5 tab-separated columns, got {len(f)}')
        who, a, e, u, late = f[:5]
        if '.' in (a, e, u):
            out[who] = None
            continue
        total = (number(path, lineno, 'auto', a, 0, 5)
                 + number(path, lineno, 'evidence', e, 0, 3)
                 + number(path, lineno, 'understanding', u, 0, 2))
        days = int(number(path, lineno, 'late', late, 0, 365))
        out[who] = total * G.late_multiplier(days)
    return out


def read_team(path, cols):
    """-> {team: points out of 100, or None while any column is a dot}"""
    out = {}
    for lineno, f in rows(path):
        if len(f) < 1 + len(cols):
            die(f'{path.name}:{lineno}: expected team + {len(cols)} columns, got {len(f)}')
        team, marks = f[0], f[1:1 + len(cols)]
        if team in out:
            die(f'{path.name}:{lineno}: team {team} appears twice')
        if '.' in marks:
            out[team] = None
            continue
        out[team] = sum(number(path, lineno, name, m, 0, hi)
                        for (name, hi), m in zip(cols, marks))
    return out


def read_students(path):
    """-> [(uniqname, team, track, multiplier, participation or None)]"""
    out, seen = [], set()
    for lineno, f in rows(path):
        f += [''] * (5 - len(f))
        who, team, track, mult, part = f[:5]
        if who in seen:
            die(f'{path.name}:{lineno}: {who} appears twice')
        seen.add(who)
        m = 1.0 if mult in ('.', '') else number(path, lineno, 'peer_mult', mult, 0, PEER_MAX)
        if m < PEER_MIN:
            print(f'note: {who} has peer_mult {m:g}, below the {PEER_MIN:g} a peer '
                  f'evaluation alone can give. teams.md allows it for evidenced '
                  f'under-contribution; make sure the note column says what the evidence is.')
        p = None if part in ('.', '') else number(path, lineno, 'participation', part, 0, 10)
        out.append((who, team, track, m, p))
    return out


def paths(course):
    term = R.COURSE_TERM
    p = {k: course / f'scores-{term}-{k}.tsv' for k in TEAM_RUBRICS}
    p['students'] = course / f'scores-{term}-students.tsv'
    for n in LABS:
        p[f'lab{n}'] = course / f'scores-{term}-lab{n}.tsv'
    return p


def cmd_init(course, teams):
    p = paths(course)
    made = []
    for k, (_w, cols) in TEAM_RUBRICS.items():
        if p[k].exists():
            continue
        names = [c for c, _ in cols]
        head = TEAM_HEADER.format(
            what=k, maxes='  '.join(f'{c} {hi}' for c, hi in cols),
            cols='\t'.join(['team'] + names + ['note']))
        body = ''.join('\t'.join([str(t)] + ['.'] * len(cols) + ['']) + '\n'
                       for t in range(1, teams + 1))
        p[k].write_text(head + body, encoding='utf-8')
        made.append(p[k])
    if not p['students'].exists():
        who = []
        for n in LABS:
            if p[f'lab{n}'].exists():
                who = [f[0] for _, f in rows(p[f'lab{n}'])]
                break
        if not who:
            die('no lab marks file to take the student list from; '
                'run `bash scripts/lab.sh scores 1` first')
        body = ''.join(f'{w}\t.\t.\t.\t.\t\n' for w in sorted(who))
        p['students'].write_text(
            STUDENT_HEADER.format(cols='\t'.join(STUDENT_COLS)) + body, encoding='utf-8')
        made.append(p['students'])
    for m in made:
        print(f'created {m}')
    if not made:
        print('nothing to create: every marks file already exists')
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('--dir', type=Path, default=R.REPO / 'course',
                    help='where the marks files are (default: course/)')
    ap.add_argument('--init', action='store_true',
                    help='create the team and student marks files that do not exist yet')
    ap.add_argument('--teams', type=int, default=3, help='number of teams, for --init')
    ap.add_argument('--csv', type=Path, help='also write the table here (keep it under dist/)')
    a = ap.parse_args(argv)

    if a.init:
        return cmd_init(a.dir, a.teams)

    p = paths(a.dir)
    if not p['students'].exists():
        die(f'{p["students"]} does not exist; run with --init first')
    students = read_students(p['students'])
    labs = {n: read_lab(p[f'lab{n}']) if p[f'lab{n}'].exists() else {} for n in LABS}
    team = {k: read_team(p[k], cols) if p[k].exists() else {}
            for k, (_w, cols) in TEAM_RUBRICS.items()}

    head = (f'{"uniqname":<12} {"team":>4} {"trk":>3} {"labs":>5} {"mid":>5} {"deliv":>6} '
            f'{"mult":>5} {"final":>5} {"part":>5} {"total":>6} {"of":>4} {"pct":>6}')
    print(head)
    print('-' * len(head))
    out, unassigned = [], []
    for who, t, track, mult, part in students:
        got, of = {}, 0.0

        lab_marks = [labs[n].get(who) for n in LABS]
        done = [m for m in lab_marks if m is not None]
        if done:
            got['labs'] = sum(m / 10 * LAB_WEIGHT for m in done)
            of += LAB_WEIGHT * len(done)

        if t in ('.', ''):
            unassigned.append(who)
        for k, (w, _cols) in TEAM_RUBRICS.items():
            score = team[k].get(t)
            if score is None:
                continue
            frac = score / 100
            if k == 'deliverable':
                frac = min(1.0, frac * mult)
            got[k] = frac * w
            of += w
        if part is not None:
            got['part'] = part / 10 * PARTICIPATION_WEIGHT
            of += PARTICIPATION_WEIGHT

        total = sum(got.values())
        pct = 100 * total / of if of else None

        def cell(k, width):
            return f'{got[k]:>{width}.1f}' if k in got else f'{"-":>{width}}'
        print(f'{who:<12} {t:>4} {track[:3]:>3} {cell("labs", 5)} {cell("mid", 5)} '
              f'{cell("deliverable", 6)} {mult:>5.2f} {cell("final", 5)} {cell("part", 5)} '
              f'{total:>6.1f} {of:>4.0f} ' + (f'{pct:>5.1f}%' if pct is not None else f'{"-":>6}'))
        out.append((who, t, track, got, mult, total, of, pct))

    missing = sorted({w for n in LABS for w in labs[n]} - {s[0] for s in students})
    if missing:
        print(f'\nIn a lab marks file but not in {p["students"].name}: {", ".join(missing)}')
    if unassigned:
        print(f'\nNo team yet, so no team marks: {", ".join(unassigned)}')
    pending = [f'lab {n}' for n in LABS
               if not labs[n] or any(v is None for v in labs[n].values())]
    pending += [k for k in TEAM_RUBRICS if not team[k] or None in team[k].values()]
    if any(s[4] is None for s in students):
        pending.append('participation')
    if pending:
        print(f'\nNot fully marked: {", ".join(pending)}. '
              f'"of" is the weight each total is out of.')
    else:
        print('\nEvery component is marked: "total" is the course grade out of 100.')

    if a.csv:
        a.csv.parent.mkdir(parents=True, exist_ok=True)
        lines = ['uniqname,team,track,labs,mid,deliverable,peer_mult,final,participation,total,out_of']
        for who, t, track, got, mult, total, of, _pct in out:
            c = [f'{got[k]:.2f}' if k in got else '' for k in
                 ('labs', 'mid', 'deliverable')]
            lines.append(','.join([who, t, track, *c, f'{mult:.2f}',
                                   f'{got["final"]:.2f}' if 'final' in got else '',
                                   f'{got["part"]:.2f}' if 'part' in got else '',
                                   f'{total:.2f}', f'{of:.0f}']))
        a.csv.write_text('\n'.join(lines) + '\n', encoding='utf-8')
        print(f'\nwrote {a.csv}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
