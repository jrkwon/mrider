#!/usr/bin/env bash
#
# check_docs.sh - everything that must pass before pushing documentation.
#
#     bash scripts/check_docs.sh
#
# Push is publish: the site deploys to jrkwon.github.io/mrider automatically on
# push to main, and during term 24 students are reading it. Run this first.
#
# Two checks, because one is not enough:
#
#   1. mkdocs build --strict   - broken file links, bad nav entries, config errors
#   2. check_anchors.py        - broken *heading* anchors, which --strict logs at
#                                INFO and then exits 0 on. See that file for the
#                                three times this repository has shipped one.
#
# CI runs the same two checks (.github/workflows/docs.yml), and because the
# deploy job has `needs: build`, a failure here stops the publish rather than
# putting a dead link in front of students.

set -uo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"

if [ -t 1 ]; then
    G=$'\033[32m'; R=$'\033[31m'; B=$'\033[1m'; N=$'\033[0m'
else
    G=""; R=""; B=""; N=""
fi

fail() { printf "\n%sFAILED%s  %s\n" "$R" "$N" "$1" >&2; exit 1; }

# mkdocs is sometimes only importable as a module, depending how it was installed.
if command -v mkdocs >/dev/null 2>&1; then
    MKDOCS=(mkdocs)
elif python3 -c "import mkdocs" >/dev/null 2>&1; then
    MKDOCS=(python3 -m mkdocs)
else
    fail "mkdocs not found. pip install -r requirements-docs.txt"
fi

printf "%s1. mkdocs build --strict%s\n" "$B" "$N"
BUILD_LOG="$(mktemp)"
trap 'rm -f "$BUILD_LOG"' EXIT

if ! "${MKDOCS[@]}" build --strict > "$BUILD_LOG" 2>&1; then
    grep -viE "^\s*$|Material for MkDocs team|git-revision-date" "$BUILD_LOG" >&2 || cat "$BUILD_LOG" >&2
    fail "mkdocs build --strict"
fi

# The git-revision plugin warns on every uncommitted page. That is expected
# while writing and says nothing about correctness, so it is filtered out -
# but anything else that reached WARNING is worth seeing.
OTHER="$(grep -i "warning" "$BUILD_LOG" | grep -viE "git-revision-date|Material for MkDocs team" || true)"
if [ -n "$OTHER" ]; then
    printf "   build warnings:\n%s\n" "$OTHER"
fi
printf "   %sok%s\n\n" "$G" "$N"

printf "%s2. anchors%s\n" "$B" "$N"
python3 scripts/check_anchors.py site || fail "broken anchors (see above)"
printf "   %sok%s\n\n" "$G" "$N"

printf "%sDocs are publishable.%s\n" "$G" "$N"
