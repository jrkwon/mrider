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
Check that every directory a package installs is actually in the repository.

    python3 scripts/check_packages.py

WHY THIS EXISTS
---------------
On 2026-09-14, the first day students cloned the repository, a fresh clone
could not build:

    CMake Error at cmake_install.cmake:46 (file):
      file INSTALL cannot find ".../src/mitt_sim/launch": No such file or
      directory.

mitt_sim, mitt_description and mitt_localization each named a `launch`
directory in install(DIRECTORY), and none of the three had ever contained a
launch file. Git does not track empty directories, so those folders existed for
whoever ran `ros2 pkg create` and for nobody else.

That is the worst shape a bug can take. It is invisible to everyone who already
has a working build - which is everyone who could have caught it - and it hits
every new clone at once. Nothing in the repository could have noticed, because
nothing ever built it from a clean checkout.

WHAT THIS CHECKS, AND WHAT IT DOES NOT
--------------------------------------
It reads install(DIRECTORY ...) out of every package's CMakeLists.txt and
asserts each named directory holds at least one git-tracked file. That is a
structural check, not a build: it runs in a second, anywhere, with no ROS
installed, which is what lets it sit in front of every push.

A real `colcon build` on a clean checkout would catch strictly more. This is
the cheap guard for the specific failure that shipped.
"""
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / 'ros2_ws' / 'src'

# gz_ros2_control is cloned separately by each student (environment.md section
# 6) and is not ours to police.
SKIP = {'gz_ros2_control'}

# install(DIRECTORY <dirs...> DESTINATION <path>) - capture the directory list.
INSTALL_DIRECTORY = re.compile(r'install\s*\(\s*DIRECTORY(.*?)\)', re.S | re.I)
# Strip CMake comments before parsing, so a commented-out entry is not read as
# a real one.
COMMENT = re.compile(r'#[^\n]*')


def tracked_files(path):
    """Git-tracked files under `path`. Empty means git does not have it."""
    r = subprocess.run(['git', 'ls-files', '--', str(path)],
                       cwd=str(REPO), capture_output=True, text=True)
    return [x for x in r.stdout.splitlines() if x.strip()]


def declared_dirs(cmakelists):
    """Directory names each install(DIRECTORY ...) block names."""
    text = COMMENT.sub('', cmakelists.read_text(errors='replace'))
    out = []
    for block in INSTALL_DIRECTORY.findall(text):
        # Everything before DESTINATION is a directory; after it is a path.
        head = re.split(r'\bDESTINATION\b', block, flags=re.I)[0]
        for tok in head.split():
            tok = tok.strip().strip('"')
            # Skip CMake options and variable references - not directories.
            if not tok or tok.startswith('$') or tok.isupper():
                continue
            out.append(tok)
    return out


def main():
    if not SRC.is_dir():
        print(f'no {SRC.relative_to(REPO)} - nothing to check')
        return 0

    problems, checked = [], 0
    for cmakelists in sorted(SRC.glob('*/CMakeLists.txt')):
        pkg = cmakelists.parent
        if pkg.name in SKIP:
            continue
        for name in declared_dirs(cmakelists):
            checked += 1
            target = pkg / name
            if not target.is_dir():
                problems.append(
                    f'{pkg.name}: install(DIRECTORY {name}) - no such directory')
            elif not tracked_files(target):
                problems.append(
                    f'{pkg.name}: install(DIRECTORY {name}) - the directory exists '
                    f'on this machine but git tracks nothing in it, so a fresh '
                    f'clone will not have it and CMake will fail')

    for p in problems:
        print(f'FAIL  {p}', file=sys.stderr)
    if problems:
        print(f'\n{len(problems)} package(s) install a directory a fresh clone '
              f'would not have.', file=sys.stderr)
        print('Either remove the entry, or add a file to the directory and '
              'commit it.', file=sys.stderr)
        return 1

    print(f'packages checked: {checked} installed directories, all present in git')
    return 0


if __name__ == '__main__':
    sys.exit(main())
