#!/usr/bin/env python3
"""
Check that translated document pairs quote the same numbers.

    python3 scripts/check_translations.py

WHY
---
The Fall 2026 purchase request exists in English and Korean because it is read
by two audiences: the lab, and the university's purchasing office. Both were
generated from one table, so they agree today.

They will not stay that way. A price gets corrected in one language, the other
is not touched, and the two documents now request different amounts from
different people - a discrepancy nobody sees until an approval is questioned.
Prose can diverge; money cannot.

This compares every comma-formatted figure in each pair and fails on any that
appears in one document and not the other. It is deliberately dumb: it does not
know what the numbers mean, only that both versions must quote the same set.
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# (document, its translation)
PAIRS = [
    ('docs/purchase-request-2026-fall.md', 'docs/purchase-request-2026-fall-ko.md'),
]

FIGURE = re.compile(r'\d{1,3}(?:,\d{3})+')


def main():
    bad = 0
    for en, ko in PAIRS:
        pe, pk = REPO / en, REPO / ko
        for p in (pe, pk):
            if not p.exists():
                print(f'FAIL  {p.relative_to(REPO)} is missing', file=sys.stderr)
                bad += 1
        if bad:
            continue
        a = set(FIGURE.findall(pe.read_text()))
        b = set(FIGURE.findall(pk.read_text()))
        only_a, only_b = sorted(a - b), sorted(b - a)
        if only_a or only_b:
            print(f'FAIL  {en} and {ko} do not quote the same figures:', file=sys.stderr)
            for x in only_a:
                print(f'        {x}  appears only in {Path(en).name}', file=sys.stderr)
            for x in only_b:
                print(f'        {x}  appears only in {Path(ko).name}', file=sys.stderr)
            bad += 1
        else:
            print(f'{Path(en).name} / {Path(ko).name}: {len(a)} figures, identical')
    if bad:
        print('\nUpdate both languages, or the two audiences are given different '
              'numbers.', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
