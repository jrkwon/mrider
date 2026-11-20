#!/usr/bin/env python3
"""
peer_eval.py - turn one team's peer-evaluation responses into a multiplier.

    python3 scripts/peer_eval.py responses-team1.csv
    python3 scripts/peer_eval.py responses-team1.csv --text     # + the free text

Instructor tool. The rule it applies is the one published in
docs/course/teams.md ("Peer evaluation"); the form it reads is described in
docs/course/grading-workflow.md. Change the rule there first, then here.

INPUT: the CSV a Google Form exports ("Download responses (.csv)"), ONE FORM
PER TEAM. The columns it looks for, by header text:

    Who are you?                       the rater, one of the member labels
    Contribution [<member>]            1-5, one column per member
    Reliability [<member>]             1-5
    Collaboration [<member>]           1-5
    <anything> [<member>]              free text, shown by --text

<member> is whatever label the form's grid rows carry. It must be identical in
the "Who are you?" choices and in every grid, because that is the only thing
that says which rows are a rater's view of themself.

THE RULE
    received  = mean, over the OTHER raters, of the mean of the three scores
    ratio     = received / (mean of `received` over the team)
    multiplier= 1.00                        if LOW <= ratio <= HIGH  (dead zone)
                ratio clamped to [MIN, MAX]  otherwise

A self-rating never enters `received`. It is printed, because the gap between
how someone rates themself and how the team rates them is worth a look.

The dead zone exists because a team is four or five people: three or four
raters cannot resolve a 5% difference, and a rule that pretends they can
turns noise into grades.

OUTPUT goes to stdout only. It is grade data, and this repository is public:
paste what you need into course/records-<term>-merges.md, which is git-ignored.
"""
import argparse
import csv
import re
import statistics
import sys

CRITERIA = ('Contribution', 'Reliability', 'Collaboration')
GRID = re.compile(r'^\s*(.+?)\s*\[(.+?)\]\s*$')


def die(msg):
    sys.exit(f'peer_eval: {msg}')


def read_responses(path):
    """-> (members, scores, texts); scores[rater][ratee][criterion] = int."""
    with open(path, newline='', encoding='utf-8-sig') as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        die(f'{path}: no responses')
    headers = list(rows[0].keys())
    who_col = next((h for h in headers if h and 'who are you' in h.lower()), None)
    if who_col is None:
        die(f'{path}: no "Who are you?" column. Columns are: {headers}')

    score_cols, text_cols, members = {}, {}, []
    for h in headers:
        m = GRID.match(h or '')
        if not m:
            continue
        # Stripped: a label typed by hand into a question title picks up spaces.
        question, member = m.group(1), m.group(2).strip()
        crit = next((c for c in CRITERIA if question.lower().startswith(c.lower())), None)
        if crit:
            score_cols[h] = (crit, member)
            if member not in members:
                members.append(member)
        else:
            text_cols[h] = member
    if not members:
        die(f'{path}: no "Contribution [<member>]" style columns')
    for crit in CRITERIA:
        missing = [m for m in members
                   if (crit, m) not in score_cols.values()]
        if missing:
            die(f'{path}: no "{crit} [...]" column for {missing}')

    scores, texts = {}, {}
    for lineno, row in enumerate(rows, 2):
        rater = (row[who_col] or '').strip()
        if rater not in members:
            die(f'{path}:{lineno}: rater "{rater}" is not one of {members}. '
                f'The "Who are you?" choices must match the grid rows exactly.')
        if rater in scores:
            print(f'note: {rater} responded more than once; the last response is used')
        mine = {}
        for h, (crit, member) in score_cols.items():
            raw = (row[h] or '').strip()
            if not raw:
                continue
            try:
                v = int(raw.split()[0])
            except ValueError:
                die(f'{path}:{lineno}: "{h}" is "{raw}", not a number')
            if not 1 <= v <= 5:
                die(f'{path}:{lineno}: "{h}" is {v}, outside 1-5')
            mine.setdefault(member, {})[crit] = v
        scores[rater] = mine
        texts[rater] = {member: (row[h] or '').strip()
                        for h, member in text_cols.items() if (row[h] or '').strip()}
    return members, scores, texts


def multiplier(ratio, a):
    if a.dead_low <= ratio <= a.dead_high:
        return 1.0
    return min(a.max_mult, max(a.min_mult, ratio))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('csv')
    ap.add_argument('--text', action='store_true', help='also print the free-text answers')
    ap.add_argument('--dead-low', type=float, default=0.90)
    ap.add_argument('--dead-high', type=float, default=1.10)
    ap.add_argument('--min-mult', type=float, default=0.85)
    ap.add_argument('--max-mult', type=float, default=1.15)
    ap.add_argument('--flag-received', type=float, default=3.0,
                    help='flag a member whose received mean is below this')
    ap.add_argument('--flag-ratio', type=float, default=0.80)
    ap.add_argument('--flag-self-gap', type=float, default=1.0)
    ap.add_argument('--flag-spread', type=float, default=2.0,
                    help='flag when two raters differ by this much on one member')
    a = ap.parse_args()

    members, scores, texts = read_responses(a.csv)

    def view(rater, ratee):
        """One rater's mean over the three criteria for one member, or None."""
        got = scores.get(rater, {}).get(ratee, {})
        return statistics.mean(got.values()) if len(got) == len(CRITERIA) else None

    received, selfs, per_rater = {}, {}, {}
    for m in members:
        others = {r: view(r, m) for r in scores if r != m}
        others = {r: v for r, v in others.items() if v is not None}
        per_rater[m] = others
        received[m] = statistics.mean(others.values()) if others else None
        selfs[m] = view(m, m)

    have = [v for v in received.values() if v is not None]
    if not have:
        die('nobody was rated by anybody else')
    team = statistics.mean(have)

    silent = [m for m in members if m not in scores]
    print(f'{len(scores)} of {len(members)} members responded; '
          f'team mean of received scores = {team:.2f}')
    if silent:
        print(f'NOT RESPONDED: {", ".join(silent)}')
    print()
    print(f'{"member":<24} {"recv":>5} {"n":>2} {"self":>5} {"ratio":>6} {"mult":>5}  flags')
    print('-' * 72)
    for m in members:
        r = received[m]
        if r is None:
            print(f'{m:<24} {"-":>5} {0:>2} {"-":>5} {"-":>6} {"-":>5}  no ratings from others')
            continue
        ratio = r / team
        flags = []
        if r < a.flag_received:
            flags.append(f'received < {a.flag_received:g}')
        if ratio < a.flag_ratio:
            flags.append(f'ratio < {a.flag_ratio:g}')
        if selfs[m] is not None and selfs[m] - r >= a.flag_self_gap:
            flags.append(f'self is {selfs[m] - r:.1f} above received')
        vals = list(per_rater[m].values())
        if len(vals) > 1 and max(vals) - min(vals) >= a.flag_spread:
            lo = min(per_rater[m], key=per_rater[m].get)
            flags.append(f'raters disagree ({min(vals):.1f}..{max(vals):.1f}; lowest from {lo})')
        s = f'{selfs[m]:.2f}' if selfs[m] is not None else '-'
        print(f'{m:<24} {r:>5.2f} {len(vals):>2} {s:>5} {ratio:>6.2f} '
              f'{multiplier(ratio, a):>5.2f}  {"; ".join(flags)}')

    flat = [r for r in scores
            if len({v for got in scores[r].values() for v in got.values()}) == 1
            and len(scores[r]) > 1]
    if flat:
        print(f'\nGave every member the same score on everything: {", ".join(flat)}')
    print(f'\nRule: multiplier is 1.00 for {a.dead_low:g} <= ratio <= {a.dead_high:g}, '
          f'otherwise the ratio clamped to [{a.min_mult:g}, {a.max_mult:g}].')
    print('It applies to the Team deliverable (25%) only, and only peer evaluation 2 is applied.')
    print('Read the flags and the free text before using any multiplier other than 1.00.')

    if a.text:
        print('\n' + '=' * 72)
        for m in members:
            print(f'\nAbout {m}:')
            said = [(r, texts[r][m]) for r in texts if m in texts[r]]
            if not said:
                print('  (nothing written)')
            for r, t in said:
                tag = 'self' if r == m else r
                print(f'  [{tag}] {t}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
