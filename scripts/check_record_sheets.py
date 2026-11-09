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
r"""Every record sheet either carries a reference, or says why it cannot.

    python3 scripts/check_record_sheets.py

WHY THIS EXISTS
---------------
Until 2026-11-09 every record sheet in docs/build/ had one blank column and
rows reading *(measure during bring-up)*. That is indistinguishable from an
oversight, and it threw away what little had been measured: vehicle #1's
teardown on 2026-11-06 produced real numbers that lived in a sentence
somewhere rather than beside the blank they belonged to.

The sheets now take one of two shapes, and the distinction is not cosmetic:

  a REFERENCE sheet  rows are QUANTITIES with one right answer, so each row
                     carries what vehicle #1 measured or the limit the value
                     must clear, and a blank for yours.
  a WORKSHEET        rows are SAMPLES - five calibration points, three
                     odometry runs, four lap attempts, one pose per sensor.
                     A per-row reference is a category error; acceptance is
                     on the whole table and sits above it.

Both are fine. What is not fine is a third shape appearing by default when
someone adds a table, which is exactly how the old one spread to fifteen
tables across five pages.

WHAT IT DELIBERATELY DOES NOT CHECK
-----------------------------------
Whether a reference VALUE is right. Check 16 does that for the vehicle
dimensions and check 15 for the carrier; the drive stall current is openly
disputed in two cells on purpose - 32 A is the Sabertooth that was never
fitted and the MDDS30 is 30 A - and a checker that demanded one number would
have to pick a side this script has no business picking.
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BUILD = REPO / 'docs' / 'build'

#: A heading that introduces a record sheet.
SHEET = re.compile(r'^\*\*Record sheet[^*]*\*\*(.*)$', re.M)

#: Column headers that count as carrying a reference. The name may be the
#: source rather than the word - the Nav2 table says "B-MROVER value" because
#: knowing the number came from the small rover is the reason not to copy it.
REFERENCE_COLS = ('reference', 'expected', 'b-mrover value')

#: How a worksheet declares itself, in the text right after its heading.
WORKSHEET = ('worksheet', 'no reference column')

#: The old shape. If this comes back, the restructure is being undone.
BANNED = '(measure during bring-up)'


def tables(text, start):
    """The header row of the first markdown table at or after `start`."""
    for line in text[start:].splitlines():
        s = line.strip()
        if s.startswith('|'):
            return [c.strip().lower() for c in s.strip('|').split('|')]
        if s.startswith('**Record sheet') or s.startswith('## '):
            break
    return None


def main():
    bad, refs, works = [], 0, 0

    for md in sorted(BUILD.glob('*.md')):
        text = md.read_text()
        rel = md.relative_to(REPO)

        if BANNED in text:
            n = text.count(BANNED)
            bad.append(f'{rel}: {n}x "{BANNED}" - the shape the Reference '
                       f'column replaced. See docs/build/index.md '
                       f'#reference-and-yours')

        for m in SHEET.finditer(text):
            # The declaration may ride on the heading line or the two after it.
            tail = text[m.start():m.start() + 400].lower()
            header = tables(text, m.end())
            label = m.group(0).split('**')[1]

            if any(w in tail for w in WORKSHEET):
                works += 1
                continue
            if header and any(c in REFERENCE_COLS for c in header):
                refs += 1
                continue
            if header is None:
                bad.append(f'{rel}: "{label}" is not followed by a table')
                continue
            bad.append(
                f'{rel}: "{label}" has neither a reference column '
                f'{list(REFERENCE_COLS)} nor a worksheet declaration. '
                f'Columns are {header}. Pick one - index.md '
                f'#reference-and-yours says which applies')

    if bad:
        for b in bad:
            print(f'FAIL  {b}', file=sys.stderr)
        return 1
    print(f'ok - {refs} reference sheets, {works} worksheets, '
          f'0 undeclared')
    return 0


if __name__ == '__main__':
    sys.exit(main())
