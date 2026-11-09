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
r"""The motor driver in these documents is the one that was actually bought.

    python3 scripts/check_motor_driver.py

WHY THIS EXISTS
---------------
A Sabertooth 2x32 was specified from a listing in July 2026 and **never
fitted**. A Cytron MDDS30 was bought instead on 2026-09-29 and confirmed on
2026-10-08. For six weeks the documents carried both: recent pages said MDDS30,
older ones said Sabertooth, and nobody reading one page could tell which was
the vehicle.

The numbers were not interchangeable, and that is the point of checking:

    32 A continuous      the Sabertooth, and the acceptance gate everywhere -
                         so the gate was PERMISSIVE BY 2 A against the board
                         actually on the vehicle
    30 A continuous      the MDDS30, 80 A peak, thermally derated
    a settable limit     the Sabertooth had one. The MDDS30 does not, and the
                         no-fuse argument on the motor branches rested on it
    S1 / S2              Sabertooth terminal names. The board says RC1 / RC2

So a stray "Sabertooth" in a live page is not a cosmetic slip. It is a reader
being told the rating of hardware this project does not own.

WHAT COUNTS AS ALLOWED
----------------------
History. The part really was specified, really was sourced, and really was
cancelled, and erasing that would make the record dishonest - this repository
keeps reversals rather than rewriting them, exactly as ADR D-R does for the
chassis. So the name is allowed:

  * anywhere in the procurement and decision records listed in HISTORICAL
  * in a LINK, including an anchor that contains the word, because a link is
    not a claim
  * in a sentence that marks it as superseded - "never fitted", "cancelled",
    "replaced", a ~~strikethrough~~, or a pointer to dbw.md 4.1

Everything else fails, and so does a live page still asserting 32 A.
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

#: Records of what was decided, sourced and spent. The name belongs in these.
HISTORICAL = {
    'docs/order-log.md',
    'docs/purchase-request-2026-fall.md',
    'docs/purchase-request-2026-fall-ko.md',
    'docs/design/adr-dbw-architecture-review.md',
    'scripts/order_status.py',
    'scripts/check_motor_driver.py',
}

#: A block of a live document that is itself a dated record. Marked in the
#: source with these HTML comments, so the boundary is visible to a reader of
#: the Markdown and not only to this script.
OPEN_HIST = '<!-- historical: '
END_HIST = '<!-- /historical -->'

#: Headings that open a historical section, by path.
HISTORICAL_SECTIONS = {
    'docs/design/vehicle.md': ('## ADR D', '## ADR D-R'),
    'docs/design/dbw.md': ('### 4.1',),
}

#: The old board may be named on a live line only alongside the new one, or
#: alongside a pointer to the substitution record. "If you name it, say what
#: replaced it" is a rule a reader can apply, which a list of allowed phrasings
#: is not - the first version of this check had eight such phrases and still
#: produced nine false alarms.
TOGETHER = ('mdds30', '4.1', 'never fitted', 'cancelled')

#: 32 A is only a defect when the line is CLAIMING it of the driver. The first
#: version banned the string, and flagged "25-32 A" twice - the ampacity of
#: 14 AWG wire, which has nothing to do with any motor driver. A number is not
#: a claim until something is predicated of it.
RATING = re.compile(r'(?<![\w.\u2013-])32\s*A(?![\w])')
ABOUT_DRIVER = ('channel', 'stall', 'driver', 'sabertooth', 'mdds', 'motor')
NOT_A_RATING = re.compile(r'\d\s*[\u2013-]\s*32\s*A|awg|mm\u00b2|ampacity|gauge')

#: Where live documentation lives. The firmware and ROS sources are swept too:
#: a terminal name in a comment is read by the person wiring the board.
GLOBS = ('docs/**/*.md', 'course/**/*.md', 'README.md',
         'ros2_ws/**/*.yaml', 'firmware/**/*.cpp', 'firmware/**/*.ini',
         'scripts/*.py')


def blocks(lines):
    """Yield (first_line, last_line, text) per Markdown block.

    A block ends at a blank line, and a quoted run (`>`) is kept whole even
    where it contains blank `>` lines, because a callout is one thought.
    """
    buf, start = [], None
    for i, line in enumerate(lines, start=1):
        quoted = line.lstrip().startswith('>')
        blank = not line.strip() or line.strip() == '>'
        if blank and not (quoted and buf):
            if buf:
                yield start, i - 1, '\n'.join(buf)
                buf, start = [], None
            continue
        if not buf:
            start = i
        buf.append(line)
    if buf:
        yield start, len(lines), '\n'.join(buf)


def section_of(lines, i, prefixes):
    """The most recent heading at or above line i that opens a section."""
    for j in range(i, -1, -1):
        s = lines[j]
        if s.startswith('#'):
            return any(s.startswith(p) for p in prefixes)
    return False


def main():
    bad = []
    files = sorted({p for g in GLOBS for p in REPO.glob(g)})

    for path in files:
        rel = str(path.relative_to(REPO))
        if rel in HISTORICAL:
            continue
        lines = path.read_text(errors='replace').splitlines()
        hist = HISTORICAL_SECTIONS.get(rel, ())
        in_block = False

        # Blocks, not lines. Markdown wraps a sentence over several lines, so
        # "the MDDS30" routinely sits one line away from "the Sabertooth" it
        # is replacing. The first two versions of this check compared lines
        # and produced fourteen false alarms between them, every one of them
        # a correct sentence split by a line break.
        for first, last, body in blocks(lines):
            if OPEN_HIST in body:
                in_block = True
            if END_HIST in body:
                in_block = False
                continue
            if in_block:
                continue
            if hist and section_of(lines, first - 1, hist):
                continue

            low = body.lower()
            if 'sabertooth' in low:
                bare = re.sub(r'\]\([^)]*\)', ']()', body)
                bare = re.sub(r'#[\w-]*sabertooth[\w-]*', '#', bare).lower()
                if 'sabertooth' in bare and not any(k in bare for k in TOGETHER):
                    bad.append(f'{rel}:{first}-{last}: names the Sabertooth without '
                               f'saying what replaced it. It was never fitted - name '
                               f'the MDDS30 in the same block, link dbw.md 4.1, or '
                               f'mark the block historical')

            if (RATING.search(body) and 'mdds30' not in low
                    and any(k in low for k in ABOUT_DRIVER)
                    and not NOT_A_RATING.search(low)
                    and '4.1' not in low and 'until 2026-11-09' not in low):
                bad.append(f'{rel}:{first}-{last}: claims 32 A of the driver. That '
                           f'is the Sabertooth, never fitted; the MDDS30 is 30 A '
                           f'continuous / 80 A peak')

    if bad:
        for b in bad:
            print(f'FAIL  {b}', file=sys.stderr)
        return 1
    print(f'ok - {len(files)} files; the driver is the MDDS30 everywhere live, '
          f'{len(HISTORICAL)} records keep the history.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
