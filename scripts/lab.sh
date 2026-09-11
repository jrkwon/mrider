#!/usr/bin/env bash
# Lab submission tooling. See docs/course/submission.md.
#
#   bash scripts/lab.sh init          once, per student
#   bash scripts/lab.sh new    1      generate labs/lab1/REPORT.md
#   bash scripts/lab.sh check  1      validate without submitting
#   bash scripts/lab.sh submit 1      validate, commit, push, build the archive
#
# Instructor:
#   bash scripts/lab.sh grade 1 --zips ~/Downloads/lab1
#   bash scripts/lab.sh grade 1 --roster course/roster.txt
#
# A thin wrapper so the command a student types every week stays short, in the
# same shape as check_env.sh. All the logic is in lab_report.py.
set -eu

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# setup_env.sh exports PYTHONNOUSERSITE=1 to keep ~/.local out of colcon builds.
# This script is stdlib-only, so it is unaffected either way - but be explicit
# rather than inheriting whatever the shell happened to have.
exec python3 "${here}/lab_report.py" "$@"
