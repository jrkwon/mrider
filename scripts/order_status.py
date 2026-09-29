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

r"""
Read the order log's tracking tables and report where the money and parts are.

    python3 scripts/order_status.py

WHY A SCRIPT AND NOT JUST THE TABLE
-----------------------------------
The tables in docs/order-log.md are the record; a human edits them. But three
questions cannot be answered by looking at them, and all three are expensive to
get wrong:

  1. Has the approved amount been exceeded? 17 line items over 3 sets, paid on
     two cards, against a ceiling with 2.0% headroom.
  2. What was ordered and has not arrived? A part ordered and forgotten is
     indistinguishable from a part not yet needed.
  3. What arrived but is not CONFIRMED? Arrival is not acquisition. The
     Sabertooth listing that started this project's sourcing carries a 2x25 SKU
     on a 2x32 description - if the wrong one ships, the box still arrives.

So the three states are ordered / arrived / secured, and `secured` requires the
check in the Verify column to have actually been performed.

TABLE FORMAT
------------
Any markdown table row whose first cell is an integer is read as a line item:

    | # | Item | Qty | Vendor | Unit KRW | Ordered | Arrived | Secured | Paid KRW | Verify |

Dates are YYYY-MM-DD, or `.` for not yet. Secured is `n/N`. Paid is the total
actually charged for that row, blank until it is known.
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LOG = REPO / 'docs' / 'order-log.md'

# The approved figure is READ from the purchase request, not copied here. A
# second copy is a second thing to keep current, and the failure mode is silent:
# the log would reconcile happily against a number nobody approved.
REQUEST = REPO / 'docs' / 'purchase-request-2026-fall.md'
CEILING = 4_000_000


def approved():
    """The requested total, from the purchase request's summary table."""
    if not REQUEST.exists():
        return None
    m = re.search(r'\*\*Total\*\*\s*\|\s*\*\*₩([\d,]+)\*\*', REQUEST.read_text())
    return int(m.group(1).replace(',', '')) if m else None


DATE = re.compile(r'^\d{4}-\d{2}-\d{2}$')


def money(cell):
    """A KRW cell as int. Blank, '.', or '-' mean not yet known."""
    s = re.sub(r'[₩,\s]', '', cell)
    if not s or s in ('.', '-'):
        return None
    try:
        return int(s)
    except ValueError:
        return None


def parse():
    """Every line item in the log, as dicts. Order preserved."""
    rows = []
    batch = '?'
    for raw in LOG.read_text().splitlines():
        line = raw.strip()
        if line.startswith('## ') or line.startswith('### '):
            batch = line.lstrip('# ').strip()
            continue
        if not line.startswith('|'):
            continue
        cells = [c.strip() for c in line.strip('|').split('|')]
        if len(cells) < 9 or not cells[0].isdigit():
            continue
        rows.append(dict(
            bom=int(cells[0]), item=cells[1], qty=cells[2], vendor=cells[3],
            unit=money(cells[4]), ordered=cells[5], arrived=cells[6],
            secured=cells[7], paid=money(cells[8]),
            verify=cells[9] if len(cells) > 9 else '', batch=batch,
        ))
    return rows


def secured_count(cell):
    m = re.match(r'(\d+)\s*/\s*(\d+)', cell)
    return (int(m.group(1)), int(m.group(2))) if m else (0, 0)


def main():
    if not LOG.exists():
        print(f'no {LOG.relative_to(REPO)}', file=sys.stderr)
        return 1
    rows = parse()
    if not rows:
        print('no line items found - has the table format changed?', file=sys.stderr)
        return 1

    waiting, unverified, committed, paid_total = [], [], 0, 0
    for r in rows:
        have, need = secured_count(r['secured'])
        placed = bool(DATE.match(r['ordered']))
        landed = bool(DATE.match(r['arrived']))
        if r['paid'] is not None:
            paid_total += r['paid']
        elif r['unit'] is not None:
            try:
                committed += r['unit'] * int(re.sub(r'\D', '', r['qty']) or 0)
            except ValueError:
                pass
        if placed and not landed:
            waiting.append(r)
        if landed and have < need:
            unverified.append(r)

    print(f'{"#":>3}  {"item":<34} {"qty":>5}  {"ordered":<10} {"arrived":<10} '
          f'{"secured":>8}  {"paid":>10}')
    print('-' * 92)
    cur = None
    for r in rows:
        if r['batch'] != cur:
            cur = r['batch']
            print(f'\n  {cur}')
        have, need = secured_count(r['secured'])
        mark = '✓' if need and have >= need else ' '
        paid = f'{r["paid"]:,}' if r['paid'] is not None else '-'
        print(f'{r["bom"]:>3}  {r["item"][:34]:<34} {r["qty"]:>5}  '
              f'{r["ordered"]:<10} {r["arrived"]:<10} {r["secured"]:>7}{mark}  '
              f'{paid:>10}')

    print('\n' + '=' * 92)
    print(f'  paid so far          {paid_total:>12,}')
    print(f'  still to pay (est.)  {committed:>12,}')
    print(f'  projected total      {paid_total + committed:>12,}')
    app = approved()
    if app is None:
        print('  approved             (could not read the purchase request)')
    else:
        print(f'  approved             {app:>12,}')
        delta = paid_total + committed - app
        verdict = 'under' if delta <= 0 else 'OVER'
        print(f'  vs approved          {abs(delta):>12,}   {verdict}')
    if paid_total + committed > CEILING:
        print(f'  vs ceiling           {paid_total + committed - CEILING:>12,}   '
              f'OVER THE {CEILING:,} CEILING')
    print('=' * 92)

    if waiting:
        print(f'\nOrdered, not yet arrived ({len(waiting)}):')
        for r in waiting:
            print(f'  #{r["bom"]:<3} {r["item"][:40]:<40} ordered {r["ordered"]}')
    if unverified:
        print(f'\nArrived, NOT yet secured ({len(unverified)}) - '
              f'the check in the Verify column has not been done:')
        for r in unverified:
            print(f'  #{r["bom"]:<3} {r["item"][:34]:<34} {r["verify"][:38]}')
    if not waiting and not unverified:
        print('\nNothing outstanding.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
