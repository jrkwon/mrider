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

# ros2_ws/setup_env.sh exports PYTHONNOUSERSITE=1 to keep ~/.local off the ROS
# build path. mkdocs lives in ~/.local, so running this script from a
# ROS-sourced shell otherwise dies with "No module named 'mkdocs'" - a
# confusing failure that says nothing about the docs. Drop the variable for
# this script only.
unset PYTHONNOUSERSITE

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

printf "%s2. portable Markdown%s\n" "$B" "$N"
# The source uses GitHub alert syntax so it reads correctly outside the site
# (hooks/github_alerts.py converts it back for Material). A `!!!` or `???` block
# would render as a literal marker over a code block in any generic viewer -
# which is the exact defect this convention exists to prevent.
BADSYNTAX="$(grep -rnE '^[[:space:]]*(!!!|\?\?\?)[[:space:]]' docs/ --include='*.md' || true)"
if [ -n "$BADSYNTAX" ]; then
    printf "   MkDocs-only admonition syntax found:\n%s\n" "$BADSYNTAX" >&2
    printf "   Use GitHub alerts instead:  > [!NOTE]\\n> **Title**\\n>\\n> body\n" >&2
    printf "   Types: NOTE TIP IMPORTANT WARNING CAUTION  (see hooks/github_alerts.py)\n" >&2
    fail "non-portable Markdown in docs/"
fi
printf "   %sok%s\n\n" "$G" "$N"

printf "%s3. slide decks up to date%s\n" "$B" "$N"
# The site publishes docs/course/slides/*.pdf, but nothing rebuilds them: they
# are committed artifacts of course/slides/*.md. Edit a deck source, forget
# course/build.sh, and the site serves the old slides indefinitely. That is not
# hypothetical - on 2026-09-11 the published W9 deck read "Merge 1 is 11/16"
# while every other document said 11/23, because a schedule-wide date shift
# updated the sources and only some PDFs were rebuilt. The Markdown pages
# deployed correctly, so nothing else noticed.
#
# Compared by COMMIT TIME, not file mtime: a fresh clone gives every file the
# checkout time, so an mtime test would fire at random in CI.
STALE=""
for src in course/slides/*.md; do
    [ -e "$src" ] || continue
    deck="$(basename "$src" .md)"
    pdf="docs/course/slides/${deck}.pdf"
    if [ ! -e "$pdf" ]; then
        STALE="${STALE} ${deck}"
        continue
    fi
    src_t="$(git log -1 --format=%ct -- "$src" 2>/dev/null)"
    pdf_t="$(git log -1 --format=%ct -- "$pdf" 2>/dev/null)"
    # Uncommitted working-tree edits are newer than anything committed. This
    # has to apply to BOTH sides: after a rebuild the PDF is modified but not
    # yet committed, and judging it by its old commit time would report it
    # stale forever.
    NOW="$(date +%s)"
    if ! git diff --quiet -- "$src" 2>/dev/null; then src_t="$NOW"; fi
    if ! git diff --quiet -- "$pdf" 2>/dev/null; then pdf_t="$NOW"; fi
    if [ -n "$src_t" ] && [ -n "$pdf_t" ] && [ "$src_t" -gt "$pdf_t" ]; then
        STALE="${STALE} ${deck}"
    fi
done
if [ -n "$STALE" ]; then
    printf "   published slides are older than their sources:%s\n" "$STALE" >&2
    printf "   Rebuild:  bash course/build.sh%s\n" "$STALE" >&2
    fail "published slides do not match their sources"
fi
printf "   %sok%s\n\n" "$G" "$N"

printf "%s4. anchors%s\n" "$B" "$N"
python3 scripts/check_anchors.py site || fail "broken anchors (see above)"
printf "   %sok%s\n\n" "$G" "$N"

printf "%sDocs are publishable.%s\n" "$G" "$N"
