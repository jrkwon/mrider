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

  1. Has the CEILING been exceeded? 17 line items over 3 sets, paid on two
     cards, against a 4,000,000 ceiling. The university approved a total,
     not a line-item schedule: individual prices may move without further
     approval, and only the total is binding. The request's own 3,921,480
     is therefore a plan to compare against, not the bar.
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
import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LOG = REPO / 'docs' / 'order-log.md'

# The approved figure is READ from the purchase request, not copied here. A
# second copy is a second thing to keep current, and the failure mode is silent:
# the log would reconcile happily against a number nobody approved.
REQUEST = REPO / 'docs' / 'purchase-request-2026-fall.md'
CEILING = 4_000_000
SETS = 3


def approved():
    """The requested total, from the purchase request's summary table."""
    if not REQUEST.exists():
        return None
    m = re.search(r'\*\*Total\*\*\s*\|\s*\*\*₩([\d,]+)\*\*', REQUEST.read_text())
    return int(m.group(1).replace(',', '')) if m else None


def request_is_consistent():
    """
    Does the purchase request still add up?

    The approved total is read from that document, so an edit to it silently
    moves the bar this log is measured against, and nobody would notice: the
    log would keep reporting "under approved" against a number nobody approved.

    This does not pin the figure - a pinned copy here is just a second thing to
    keep current. It checks the document against ITSELF: the per-set subtotals
    times three must equal the stated total. A hand-edit to a line item, or to
    the total, breaks that equality.
    """
    if not REQUEST.exists():
        return True, ''
    text = REQUEST.read_text()
    subs = [int(x.replace(',', '')) for x in
            re.findall(r'\*\*Tier [12] subtotal\*\*\s*\|\s*\*\*([\d,]+)\*\*', text)]
    total = approved()
    if len(subs) != 2 or total is None:
        return True, 'purchase request: could not read its subtotals; consistency not checked'
    want = sum(subs) * SETS
    if want != total:
        return False, (f'purchase request does not add up: ({subs[0]:,} + {subs[1]:,}) '
                       f'x {SETS} = {want:,}, but its Total says {total:,}')
    return True, ''


DATE = re.compile(r'^\d{4}-\d{2}-\d{2}$')


def money(cell):
    """
    A KRW cell as int. Blank, '.', or '-' mean not yet known.

    A leading '~' or '약' is accepted and treated as the number: "approximately
    135,000" is a legitimate thing to write before an invoice exists, and
    refusing to parse it would drop the row out of the total - which reads as
    the budget being healthier than it is.
    """
    s = re.sub(r'^[~약≈]\s*', '', cell.strip())
    s = re.sub(r'[₩,\s]', '', s)
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


# --- writing back --------------------------------------------------------------
#
# The tables are the record and a human may always edit them by hand. But the
# three state transitions are the things that happen often, under time pressure,
# on a phone, months apart - and hand-editing a markdown cell is how a row gets
# mangled or a column shifted. These do it in place and leave the table valid.

COL = dict(ordered=5, arrived=6, secured=7, paid=8)


def set_cell(bom, column, value):
    """Set one cell of one line item, in place. Returns the row's item name."""
    lines = LOG.read_text().split('\n')
    for i, raw in enumerate(lines):
        line = raw.strip()
        if not line.startswith('|'):
            continue
        cells = line.strip('|').split('|')
        if len(cells) < 9 or cells[0].strip() != str(bom):
            continue
        # Preserve each cell's padding style by writing a single-space pad; the
        # table stays valid markdown and the parser does not care about width.
        cells[COL[column]] = f' {value} '
        lines[i] = '|' + '|'.join(cells) + '|'
        LOG.write_text('\n'.join(lines))
        return cells[1].strip()
    die(f'no line item #{bom} in {LOG.relative_to(REPO)}')


def die(msg):
    print(f'error: {msg}', file=sys.stderr)
    sys.exit(1)


def main():
    ap = argparse.ArgumentParser(
        description='Report or update procurement status in docs/order-log.md')
    ap.add_argument('--order', type=int, metavar='BOM#',
                    help='mark ordered: needs --date, and --paid if known')
    ap.add_argument('--arrive', type=int, metavar='BOM#', help='mark arrived: needs --date')
    ap.add_argument('--secure', type=int, metavar='BOM#',
                    help='raise the secured count: needs --count')
    ap.add_argument('--date', help='YYYY-MM-DD (default: today)')
    ap.add_argument('--paid', help='total KRW charged for that row')
    ap.add_argument('--count', type=int, help='how many units are now secured')
    args = ap.parse_args()

    acted = False
    if args.order is not None:
        d = args.date or datetime.now().strftime('%Y-%m-%d')
        if not DATE.match(d):
            die(f'--date {d!r} is not YYYY-MM-DD')
        name = set_cell(args.order, 'ordered', d)
        print(f'#{args.order} {name}: ordered {d}')
        if args.paid:
            v = re.sub(r'[^\d]', '', args.paid)
            set_cell(args.order, 'paid', f'{int(v):,}')
            print(f'{"":>{len(str(args.order)) + 2}} paid {int(v):,}')
        else:
            print('      (no --paid given; fill Paid KRW in when the charge is known)')
        acted = True
    if args.arrive is not None:
        d = args.date or datetime.now().strftime('%Y-%m-%d')
        if not DATE.match(d):
            die(f'--date {d!r} is not YYYY-MM-DD')
        name = set_cell(args.arrive, 'arrived', d)
        print(f'#{args.arrive} {name}: arrived {d}')
        print('      NOT yet secured - run the Verify check, then --secure')
        acted = True
    if args.secure is not None:
        if args.count is None:
            die('--secure needs --count (how many units are confirmed good)')
        rows = {r['bom']: r for r in parse()}
        if args.secure not in rows:
            die(f'no line item #{args.secure}')
        _have, need = secured_count(rows[args.secure]['secured'])
        if args.count > need:
            die(f'--count {args.count} exceeds the {need} on order for #{args.secure}')
        name = set_cell(args.secure, 'secured', f'{args.count}/{need}')
        print(f'#{args.secure} {name}: secured {args.count}/{need}')
        acted = True
    if acted:
        print()

    if not LOG.exists():
        print(f'no {LOG.relative_to(REPO)}', file=sys.stderr)
        return 1
    rows = parse()
    if not rows:
        print('no line items found - has the table format changed?', file=sys.stderr)
        return 1

    waiting, unverified, unpriced, mismatch = [], [], [], []
    committed, paid_total = 0, 0
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
        else:
            # Neither paid nor priced. Counting this as zero would quietly
            # under-report the projection and make the budget look healthier
            # than it is - the exact failure this script exists to prevent.
            unpriced.append(r)
        # Paid should be unit x qty. When it is not, say so rather than letting
        # the row sit there looking settled.
        #
        # This catches the VAT trap, which has now bitten twice: Korean vendors
        # show 상품금액 EX-VAT in an order summary while the quoted unit price
        # was VAT-inclusive, so `paid` comes out at exactly 1/1.1 of unit x qty
        # and the log silently understates what the card was charged. It also
        # catches the honest cases - a discount, a price that moved - which
        # deserve a note either way.
        if r['paid'] is not None and r['unit'] is not None:
            try:
                q = int(re.sub(r'\D', '', r['qty']) or 0)
            except ValueError:
                q = 0
            if q:
                want = r['unit'] * q
                if abs(r['paid'] - want) > 1:
                    ratio = want / r['paid'] if r['paid'] else 0
                    why = '  <- looks like VAT was omitted' if abs(ratio - 1.1) < 0.01 else ''
                    mismatch.append((r, want, why))
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
    ok, msg = request_is_consistent()
    if msg:
        print(f'  {msg}')
    if not ok:
        print('  The approved figure below cannot be trusted until that is resolved.')
    app = approved()
    if app is None:
        print('  approved             (could not read the purchase request)')
    else:
        # The CEILING is the real constraint. The university approved a total
        # of 4,000,000 and does NOT require separate approval for individual
        # line items moving, so the request's own 3,921,480 is a plan, not a
        # bar - printing it with an under/OVER verdict made the wrong number
        # look binding.
        proj = paid_total + committed
        head = CEILING - proj
        print(f'  ceiling              {CEILING:>12,}')
        if head >= 0:
            print(f'  headroom             {head:>12,}')
        else:
            print(f'  OVER THE CEILING BY  {-head:>12,}   <<<')
        delta = proj - app
        print(f'  (vs {app:,} requested: {abs(delta):,} '
              f'{"under" if delta <= 0 else "over"} - informational;')
        print('   per-item variation needs no re-approval)')
    if mismatch:
        print(f'  CHECK: {len(mismatch)} row(s) where paid does not equal unit x qty:')
        for r, want, why in mismatch:
            print(f'      #{r["bom"]} {r["item"][:30]:<30} paid {r["paid"]:>9,} '
                  f'vs {want:>9,}{why}')
    if unpriced:
        print(f'  NOT IN THE TOTAL: {len(unpriced)} row(s) have no unit price and are not paid.')
        for r in unpriced:
            print(f'      #{r["bom"]} {r["item"][:44]}')
        print('  The projection above is therefore a FLOOR, not an estimate.')
    print('=' * 92)

    if waiting:
        print(f'\nOrdered, not yet arrived ({len(waiting)}):')
        for r in waiting:
            print(f'  #{r["bom"]:<3} {r["item"][:40]:<40} ordered {r["ordered"]}')
    if unverified:
        print(f'\nArrived, NOT yet secured ({len(unverified)}) - '
              f'the check in the Verify column has not been done:')
        for r in unverified:
            have, need = secured_count(r['secured'])
            # Show the count, because arrivals are routinely partial: a row can
            # be part-delivered and part-outstanding at the same time, and
            # "arrived" alone reads as though every unit is on the shelf.
            print(f'  #{r["bom"]:<3} {r["item"][:30]:<30} {have}/{need} secured  '
                  f'{r["verify"][:34]}')
    if not waiting and not unverified:
        print('\nNothing outstanding.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
