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
r"""Every published photograph is dated, placed, and used.

    python3 scripts/check_photo_manifest.py

WHY THIS EXISTS
---------------
A drawing in docs/images/ carries its date implicitly: re-run its generator and
you get the committed file back, which is what check 17 verifies. **A photograph
cannot do that.** It is one vehicle, on one day, in one state, and nothing in the
file says which - so a photograph of a part that was later replaced reads exactly
like a photograph of the part on the vehicle today.

That is the absence-claim failure wearing different clothes, and none of the
checks that would catch it in prose can see it:

    check 12  traction voltage      reads text
    check 20  motor driver          reads text
    check 21  absence claims        reads text

A photograph of the Sabertooth that was never fitted would pass all three. So
would a photograph of a 24 V pack. The only defence available is a written row
per file, which is what docs/images/photos/MANIFEST.md is for.

WHAT IT ENFORCES
----------------
  1. Every file in docs/images/photos/ has a row in MANIFEST.md.
  2. Every row names a file that exists.
  3. Every row carries an ISO date - the day the photograph was taken, or the
     day it entered the record. Same argument as check 21: the date does not
     make the photograph current, it makes the reader able to judge it.
  4. Every photograph is linked from a page outside docs/images/photos/. A
     photograph nobody links to is a file, exactly as check 14 says of figures.
  5. Every `images/photos/...` reference in docs resolves to a file.

THE GAP THIS FILLS
------------------
Check 14 already does 4 and 5 for figures - and cannot do them here. It globs
`docs/images/*.svg` and `docs/images/*.png`, which does not descend into the
subdirectory, and its reference regex stops at the first `/` after `images/`,
so `../images/photos/foo.jpg` matches nothing at all. On 2026-11-09 it cheerfully
reported "34 live" while three photographs sat beside it, unlinked as far as it
knew and unchecked in every direction.

WHAT IT DOES NOT DO
-------------------
Judge the photograph. It cannot tell a current part from a superseded one, and
no script can. What it guarantees is that somebody wrote down which it was, on a
row a reader can find, before the image was published.
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PHOTOS = REPO / 'docs' / 'images' / 'photos'
MANIFEST = PHOTOS / 'MANIFEST.md'

#: What counts as a published photograph. Deliberately short: the house format
#: is JPEG, and anything else should be a deliberate decision with a reason.
EXTS = {'.jpg', '.jpeg', '.png', '.webp'}

#: An ISO date, as every other dated statement in this repository is written.
DATED = re.compile(r'\b20\d{2}-\d{2}-\d{2}\b')

#: Where a photograph may be linked from.
GLOBS = ('docs/**/*.md', 'course/**/*.md', 'README.md')


def main():
    if not PHOTOS.is_dir():
        print('ok - no photographs published.')
        return 0
    if not MANIFEST.is_file():
        print(f'FAIL  {MANIFEST.relative_to(REPO)} is missing, but '
              f'{PHOTOS.relative_to(REPO)} holds files. Every published '
              f'photograph needs a row saying what it is and when.',
              file=sys.stderr)
        return 1

    bad = []
    files = sorted(p for p in PHOTOS.iterdir()
                   if p.is_file() and p.suffix.lower() in EXTS)
    text = MANIFEST.read_text()
    rows = [ln for ln in text.splitlines() if ln.lstrip().startswith('|')]

    # 1 + 3: a row per file, and the row is dated.
    for p in files:
        hits = [r for r in rows if f'`{p.name}`' in r or p.name in r]
        if not hits:
            bad.append(f'{p.relative_to(REPO)}: no row in MANIFEST.md. A '
                       f'photograph with no written date and no stated vehicle '
                       f'cannot be told from one of a superseded part')
            continue
        if not any(DATED.search(r) for r in hits):
            bad.append(f'{p.relative_to(REPO)}: its MANIFEST.md row carries no '
                       f'ISO date. The date does not make the photograph '
                       f'current; it lets a reader judge whether it is')

    # 2: no row for a file that is gone.
    names = {p.name for p in files}
    for r in rows:
        for m in re.finditer(r'`([A-Za-z0-9._-]+\.(?:jpg|jpeg|png|webp))`', r):
            if m.group(1) not in names:
                bad.append(f'MANIFEST.md names `{m.group(1)}`, which is not in '
                           f'docs/images/photos/. Remove the row, or restore '
                           f'the file')

    # 4 + 5: linkage, both directions. check 14 can do neither here.
    pages = sorted({q for g in GLOBS for q in REPO.glob(g)})
    bodies = {}
    for q in pages:
        rel = str(q.relative_to(REPO))
        if rel.startswith('docs/images/photos/'):
            continue
        bodies[rel] = q.read_text(errors='replace')

    for p in files:
        if not any(p.name in b for b in bodies.values()):
            bad.append(f'{p.relative_to(REPO)}: nothing links to it. Link it '
                       f'from the page whose claim it supports, or delete it - '
                       f'an unlinked photograph is a file, not a figure')

    ref = re.compile(r'images/photos/([A-Za-z0-9._-]+\.(?:jpg|jpeg|png|webp))')
    for rel, body in bodies.items():
        for m in ref.finditer(body):
            if m.group(1) not in names:
                bad.append(f'{rel}: links images/photos/{m.group(1)}, which '
                           f'does not exist')

    if bad:
        for b in sorted(set(bad)):
            print(f'FAIL  {b}', file=sys.stderr)
        return 1
    print(f'ok - {len(files)} photograph(s), each dated in MANIFEST.md, '
          f'each linked from a page.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
