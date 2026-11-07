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
r"""Every generated figure is the one its generator produces today.

    python3 scripts/check_figures_current.py

THE GAP THIS CLOSES
-------------------
Sixteen of this repository's figures are generated, and the convention printed
under each one is "edit the script and re-run it; do not edit the SVG". Nothing
enforced the second half of that sentence. Edit a generator, forget to run it,
commit: the script and the committed SVG disagree, and every reader is looking
at the stale one while every reviewer is reading the current source.

That is the same defect class as a figure quoting a number the model does not
compute, which is what three of these turned out to be doing. The difference is
that this one is mechanical to catch.

WHY IT COULD NOT BE WRITTEN BEFORE
----------------------------------
Four generators wrote their SVG from top-level code, so merely importing one
rewrote the documentation. A check that regenerates everything and compares has
to be able to run the generators without the comparison's own setup disturbing
what it is measuring. The writes moved under `if __name__ == "__main__"` on
2026-11-07 and this became possible.

WHAT IT DOES NOT DO
-------------------
It does not run WireViz. Those figures come from harness/*.yml through
scripts/gen_harness.sh and need wireviz and graphviz installed; the YAML is the
source and is reviewed as source. Nor does it run OpenSCAD - carrier_params
cross-checks against it when available and says so when it is not.
"""
import hashlib
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
IMAGES = REPO / "docs" / "images"

# Generators that need a tool that may not be installed. Skipped with a word,
# never silently: a check that quietly tests less than it claims is worse than
# one that fails.
OPTIONAL = {"gen_carrier_figure.py": "openscad",
            "gen_grub_screw_figure.py": "openscad",
            "gen_hub_bore_figure.py": "openscad",
            "gen_system_figure.py": "dot"}


def have(tool):
    return any((Path(p) / tool).exists()
               for p in os.environ.get("PATH", "").split(os.pathsep) if p)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    gens = sorted((REPO / "scripts").glob("gen_*.py"))
    if not gens:
        print("   no generators found", file=sys.stderr)
        return 1

    before = {f: digest(f) for f in sorted(IMAGES.glob("*.svg"))}
    ran, skipped, failed = [], [], []

    for g in gens:
        need = OPTIONAL.get(g.name)
        if need and not have(need):
            skipped.append(f"{g.name} (needs {need})")
            continue
        r = subprocess.run([sys.executable, str(g)], cwd=str(REPO),
                           capture_output=True, text=True, timeout=600)
        if r.returncode != 0:
            failed.append(f"{g.name}: {(r.stderr or r.stdout).strip()[-300:]}")
        else:
            ran.append(g.name)

    after = {f: digest(f) for f in sorted(IMAGES.glob("*.svg"))}
    stale = sorted(f.name for f in before if f in after and before[f] != after[f])
    new = sorted(f.name for f in after if f not in before)

    if failed or stale or new:
        print("generated figures are not current:", file=sys.stderr)
        for f in failed:
            print(f"   generator FAILED  {f}", file=sys.stderr)
        for f in stale:
            print(f"   committed SVG differs from its generator: {f}",
                  file=sys.stderr)
        for f in new:
            print(f"   generator produced an uncommitted figure: {f}",
                  file=sys.stderr)
        print("   Re-run the generator and commit the SVG with the script.",
              file=sys.stderr)
        return 1

    note = f", {len(skipped)} skipped" if skipped else ""
    print(f"   ok  ({len(ran)} generators re-run, output identical{note})")
    for s in skipped:
        print(f"       skipped: {s}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
