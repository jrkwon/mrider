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
r"""The lab tooling is three files now. Keep the layering, and keep the bundle
able to run.

    python3 scripts/check_lab_modules.py

WHY THIS EXISTS
---------------
scripts/lab_report.py was one 1,494-line file until 2026-11-07. Splitting it
into lab_labs (what a lab asks for), lab_report (the student's half) and
lab_grading (the instructor's) bought two things, and both are the kind that
rot without a check.

The first is that the student bundle no longer ships the grader.
scripts/export_student_bundle.sh names the files it copies. Add a sibling
import to lab_report and forget that line, and the bundle still builds, still
zips, still looks right - and `bash scripts/lab.sh new 1` dies with
ModuleNotFoundError on thirteen machines, at whatever hour they open it. There
is no earlier symptom. So: every sibling module the student half imports must
be in the copy list, and lab_grading must not be.

The second is the direction. lab_labs imports nothing, lab_report imports
lab_labs, lab_grading imports lab_report, and nothing imports upwards. One
top-level `import lab_grading` in lab_report would make that a cycle, undo the
bundle property above, and still run fine here - where all three files exist.

WHAT IT DELIBERATELY DOES NOT CHECK
-----------------------------------
It reads the import statements, not the behaviour. `lab_report selftest`,
scripts/tests/test_grading.py and check 5 cover what the code does. This
covers only the shape, which is the part a passing test suite cannot see.
"""
import ast
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / 'scripts'
BUNDLE = SCRIPTS / 'export_student_bundle.sh'

#: The layering, as the module docstrings claim it. Each entry is the exact set
#: of sibling lab_* modules that file may import at the top level.
LAYERS = {
    'lab_labs.py': set(),
    'lab_report.py': {'lab_labs'},
    'lab_grading.py': {'lab_report'},
}

#: What a student unpacks and runs. lab_grading is not here, and that is the
#: point of the split - see export_student_bundle.sh.
STUDENT = {'lab_report.py', 'lab_labs.py'}
INSTRUCTOR_ONLY = {'lab_grading.py'}


def top_level_imports(path):
    """Sibling lab_* modules imported from module scope, and from inside a def.

    The distinction is the whole check: lab_report reaches lab_grading through
    a lazy import inside main(), which is a dependency a bundle without the
    file can survive. The same import at module scope is not.
    """
    tree = ast.parse(path.read_text())
    outer, inner = set(), set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        names = ([a.name for a in node.names] if isinstance(node, ast.Import)
                 else [node.module or ''])
        names = {n.split('.')[0] for n in names if n.startswith('lab_')}
        if not names:
            continue
        # Module scope means no enclosing function. ast does not record a
        # parent, so ask the other way round: is this node inside any def?
        in_func = any(node in ast.walk(f)
                      for f in ast.walk(tree)
                      if isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef)))
        (inner if in_func else outer).update(names)
    return outer, inner


def copied_by_bundle():
    """The scripts/ files export_student_bundle.sh copies into the bundle."""
    text = BUNDLE.read_text()
    return set(re.findall(r'\$\{REPO\}/scripts/([A-Za-z0-9_.-]+)', text))


def main():
    bad = []

    # --- the layering ------------------------------------------------------
    for name, allowed in LAYERS.items():
        path = SCRIPTS / name
        if not path.exists():
            bad.append(f'{name} is missing; the lab tooling is three files')
            continue
        outer, inner = top_level_imports(path)
        extra = outer - allowed
        if extra:
            bad.append(f'{name} imports {sorted(extra)} at module scope; '
                       f'allowed: {sorted(allowed) or "nothing"}. '
                       f'The layering runs lab_labs <- lab_report <- lab_grading')
        missing = allowed - outer
        if missing:
            bad.append(f'{name} no longer imports {sorted(missing)}')
        if name == 'lab_report.py' and 'lab_grading' in outer:
            bad.append('lab_report imports lab_grading at module scope. That is '
                       'a cycle, and it puts the grader back in the bundle')
        print(f'  {name:16s} imports {sorted(outer) or "nothing"}'
              + (f', lazily {sorted(inner)}' if inner else ''))

    # --- the bundle --------------------------------------------------------
    copied = copied_by_bundle()
    needed = set()
    for name in STUDENT:
        outer, _ = top_level_imports(SCRIPTS / name)
        needed |= {f'{m}.py' for m in outer}
    needed |= STUDENT

    absent = sorted(needed - copied)
    if absent:
        bad.append(f'export_student_bundle.sh does not copy {absent}, which the '
                   f'student half imports. `lab.sh new` in a bundle would die '
                   f'with ModuleNotFoundError')
    shipped = sorted(INSTRUCTOR_ONLY & copied)
    if shipped:
        bad.append(f'export_student_bundle.sh copies {shipped} into the student '
                   f'bundle. That is the grader - the roster reader, the late '
                   f'penalty table, where marks live')
    print(f'  bundle copies    {sorted(copied)}')
    print(f'  student half needs {sorted(needed)}')

    if bad:
        print()
        for b in bad:
            print(f'FAIL  {b}', file=sys.stderr)
        return 1
    print(f'\nok - {len(LAYERS)} modules, one-way layering, bundle complete '
          f'and grader-free.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
