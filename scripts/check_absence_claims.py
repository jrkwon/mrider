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
r"""Saying a thing is unrecorded is a claim. Date it.

    python3 scripts/check_absence_claims.py

WHY THIS EXISTS
---------------
On 2026-11-09 this sentence was found in two documents:

    "No document in this repository records the traction pack's chemistry."

It had been false since **2026-11-05**, when the label was read and written
into 03-electrical's switch table. The prose four rows BELOW that same table
still said it, and from there it was copied into dbw.md as an open question
that was already closed.

An absence claim is the one kind that tells a reader to **stop looking**. It
is therefore the kind that should be hardest to believe, and it is the kind
that goes stale silently: nothing happens when someone records the fact, and
the sentence saying otherwise keeps reading as current forever.

A date does not make the claim true. It makes it **checkable by the reader**,
which is the next best thing and costs six characters. "No document records
the pack's chemistry (2026-11-01)" sitting next to a table dated 2026-11-05
is a contradiction anyone can see. Without the date it is invisible.

EXTENDED 2026-11-09 TO COVER PHOTOGRAPHS
----------------------------------------
Publishing the first eleven photographs produced two more absence claims of
exactly this shape, and the patterns above caught neither:

    "No teardown photographs were kept."          (02-mechanical, written true)
    "check the steering motor, which has not
     been photographed yet"                       (01-bom-sourcing, long false)

The first went stale the same afternoon - the photographs were recovered from
the build log hours later. The second had been false since 2026-11-06, when
that tap was measured and photographed, and the table two rows below it in the
same block already said so.

Both are about the record, not about the hardware, which is why they belong
here. The reason they were missed is that the earlier list named the verbs for
writing things down - recorded, measured, written - and a photograph is none of
them. "Kept" was missed for the same reason: it is what you do with a
photograph, not with a figure.

WHAT IT DOES NOT DO
-------------------
Verify the claim. It cannot - the claim is about everything that is not
written down. What it enforces is that the claim carries the one piece of
context that lets a reader judge it, and that nobody writes a new one without
pausing long enough to date it.
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

#: Phrasings that assert something is not written down anywhere. Deliberately
#: narrow: this is about claims of ABSENCE FROM THE RECORD, not about any
#: sentence containing "no".
CLAIMS = [
    re.compile(p, re.I) for p in (
        r'no\s+(?:other\s+)?document\b[^.]{0,60}\brecord',
        r'\bnothing\b[^.]{0,40}\brecords\b',
        r'\brecorded\s+nowhere\b',
        r'\bnowhere\s+recorded\b',
        r'\bis\s+not\s+recorded\b',
        r'\bare\s+not\s+recorded\b',
        r'\bno\s+record\s+of\b',
        r'\bhas\s+never\s+been\s+(?:recorded|measured|written|photographed)\b',
        r'\bnever\s+been\s+(?:recorded|measured|photographed)\b',
        r'\bnot\s+been\s+photographed\b',
        r'\bno\s+(?:\w+\s+){0,3}(?:photograph|record|note|measurement)s?\s+(?:were|was)\s+kept\b',
        r'\bnone\s+(?:were|was)\s+kept\b',
        r'\bno\s+(?:\w+\s+){0,3}(?:figure|number|value|spec)\b[^.]{0,40}\bexists\b',
    )
]

#: An ISO date, which is how every other dated statement in this repo is
#: written. A bare year is not enough to be useful.
DATED = re.compile(r'\b20\d{2}-\d{2}-\d{2}\b')

#: This file quotes the claim it bans.
SKIP = {'scripts/check_absence_claims.py'}

GLOBS = ('docs/**/*.md', 'course/**/*.md', 'README.md', 'scripts/*.py')


def blocks(lines):
    """(first, last, text) per Markdown block; a `>` run stays whole."""
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


def main():
    bad, seen = [], 0
    files = sorted({p for g in GLOBS for p in REPO.glob(g)})

    for path in files:
        rel = str(path.relative_to(REPO))
        if rel in SKIP:
            continue
        lines = path.read_text(errors='replace').splitlines()
        for first, last, body in blocks(lines):
            hit = next((c.search(body) for c in CLAIMS if c.search(body)), None)
            if not hit:
                continue
            seen += 1
            if DATED.search(body):
                continue
            bad.append(f'{rel}:{first}-{last}: "{hit.group(0).strip()}" claims '
                       f'something is unrecorded, with no date. That claim goes '
                       f'stale the moment anyone records it, and silently - put '
                       f'the date it was last true beside it')

    if bad:
        for b in bad:
            print(f'FAIL  {b}', file=sys.stderr)
        return 1
    print(f'ok - {seen} absence claim(s) across {len(files)} files, all dated.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
