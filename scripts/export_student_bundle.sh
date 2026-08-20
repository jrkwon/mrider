#!/usr/bin/env bash
#
# export_student_bundle.sh - assemble the student-facing subset of this repo.
#
#     bash scripts/export_student_bundle.sh              # -> dist/mrider-course-<date>.zip
#     bash scripts/export_student_bundle.sh --site       # also build the HTML site
#     bash scripts/export_student_bundle.sh --out DIR    # write somewhere else
#
# Produces an offline snapshot: course material, the learn modules, the full
# design record, the build guide, the slide PDFs, and the ROS 2 workspace.
#
# EXCLUSIONS ARE A POLICY DECISION, NOT A TECHNICAL ONE, so the list lives in one
# obvious place below and ships EMPTY. The design record IS the teaching
# material; hiding pages from a site that is already public buys nothing and
# breaks links. See the comment on EXCLUDE_DOCS before adding anything.

set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="${REPO}/dist"
WANT_SITE=0

# ---------------------------------------------------------------------------
# What students do NOT get. EMPTY BY DEFAULT, on purpose.
#
# Nothing in this repository is confidential - the whole site is already
# published at jrkwon.github.io/mrider. Excluding a page from the bundle hides
# it from students while leaving it one search away, and breaks any link that
# points at it. That trade is rarely worth making.
#
# The design record in particular ships in full, including
# adr-dbw-architecture-review.md and the two reversals in vehicle.md. A decision
# recorded with its alternatives and then overturned with reasons is the single
# most valuable thing here for a student to read.
#
# The one plausible candidate, if you want it out:
#
#   "order-log.md"   Supplier names, prices, and the lab's purchasing record.
#                    NOTE: two pages link to it and would 404 in the bundle -
#                    docs/design/vehicle.md and docs/build/01-bom-sourcing.md.
#                    Fix those links first; the check below will remind you.
EXCLUDE_DOCS=()
# ---------------------------------------------------------------------------

while [ $# -gt 0 ]; do
    case "$1" in
        --site) WANT_SITE=1; shift ;;
        --out)  OUT_DIR="$2"; shift 2 ;;
        -h|--help) sed -n '3,10p' "${BASH_SOURCE[0]}"; exit 0 ;;
        *) echo "unknown option: $1" >&2; exit 1 ;;
    esac
done

# Date comes from git, not `date`, so the same commit always produces the same
# bundle name - a bundle you cannot reproduce is not much of an artifact.
STAMP="$(git -C "$REPO" log -1 --format=%cd --date=format:%Y%m%d 2>/dev/null || echo undated)"
SHA="$(git -C "$REPO" rev-parse --short HEAD 2>/dev/null || echo nogit)"
NAME="mrider-course-${STAMP}-${SHA}"
STAGE="${OUT_DIR}/${NAME}"

rm -rf "$STAGE"
mkdir -p "$STAGE"

echo "Staging student bundle: ${NAME}"

# --- documentation ---------------------------------------------------------
mkdir -p "${STAGE}/docs"
cp -r "${REPO}/docs/course"  "${STAGE}/docs/"
cp -r "${REPO}/docs/learn"   "${STAGE}/docs/"
cp -r "${REPO}/docs/build"   "${STAGE}/docs/"
cp -r "${REPO}/docs/design"  "${STAGE}/docs/"
cp -r "${REPO}/docs/images"  "${STAGE}/docs/"
cp    "${REPO}/docs/index.md"           "${STAGE}/docs/"
cp    "${REPO}/docs/getting-started.md" "${STAGE}/docs/"
cp    "${REPO}/docs/run-the-twin.md"    "${STAGE}/docs/"

for f in ${EXCLUDE_DOCS[@]+"${EXCLUDE_DOCS[@]}"}; do
    if [ -e "${STAGE}/docs/${f}" ]; then
        rm -rf "${STAGE}/docs/${f}"
        echo "  excluded: docs/${f}"
    fi
done

# Any surviving link to an excluded page would 404 for students. Catch it here
# rather than letting them find it.
BROKEN=0
for f in ${EXCLUDE_DOCS[@]+"${EXCLUDE_DOCS[@]}"}; do
    base="$(basename "$f" .md)"
    if grep -rl "(\.\./${base}\.md\|(${base}\.md\|(\.\./\.\./${base}\.md" "${STAGE}/docs" >/dev/null 2>&1; then
        echo "  WARNING: pages still link to the excluded '${base}':" >&2
        grep -rln "${base}\.md" "${STAGE}/docs" | sed 's|^|    |' >&2
        BROKEN=1
    fi
done

# --- slides ----------------------------------------------------------------
if compgen -G "${REPO}/docs/course/slides/*.pdf" > /dev/null; then
    echo "  slides: $(ls -1 "${REPO}"/docs/course/slides/*.pdf | wc -l) PDF(s)"
else
    echo "  NOTE: no slide PDFs found. Run 'bash course/build.sh' first." >&2
fi

# --- the things students actually run --------------------------------------
mkdir -p "${STAGE}/scripts"
cp "${REPO}/scripts/check_env.sh" "${STAGE}/scripts/"
cp -r "${REPO}/ros2_ws" "${STAGE}/"
rm -rf "${STAGE}/ros2_ws/build" "${STAGE}/ros2_ws/install" \
       "${STAGE}/ros2_ws/log"   "${STAGE}/ros2_ws/src/gz_ros2_control"

cp "${REPO}/README.md" "${REPO}/LICENSE" "${STAGE}/" 2>/dev/null || true

cat > "${STAGE}/START-HERE.md" <<EOF
# 자율주행미들웨어응용 — Student Bundle

Built from commit \`${SHA}\` (${STAMP}).

## Before the first class (September 7)

1. Read \`docs/course/environment.md\` and follow it end to end.
2. Run \`bash scripts/check_env.sh\` until it reports **FAIL: 0**.
3. Bring that output to class — you submit it with Lab 1.

Budget 2–4 hours. Start early: the one step that can genuinely fail is graphics
drivers, and that is not fixable in five minutes on the morning of class.

## What is in here

| | |
|---|---|
| \`docs/course/\` | Syllabus, labs, weekly notes, grading, team tracks |
| \`docs/course/slides/\` | Lecture slides as PDF |
| \`docs/learn/\` | Topic modules M1–M8, assigned as weekly reading |
| \`docs/design/\` | The engineering record. Authoritative. Read the reversals |
| \`docs/build/\` | The eight-step hardware build guide |
| \`ros2_ws/\` | The ROS 2 workspace you will build on |

The same material is published at <https://jrkwon.github.io/mrider/>, which is
kept current. This bundle is a snapshot for offline use.

Note that \`gz_ros2_control\` is **not** included — it is cloned from upstream
during setup. \`environment.md\` §6 covers it.
EOF

# --- optional built site ---------------------------------------------------
if [ "$WANT_SITE" = "1" ]; then
    echo "  building HTML site..."
    ( cd "$REPO" && python3 -m mkdocs build --site-dir "${STAGE}/site" --quiet ) \
        && echo "  site -> ${STAGE}/site" \
        || echo "  WARNING: mkdocs build failed; bundle has no HTML site" >&2
fi

# --- package ---------------------------------------------------------------
( cd "$OUT_DIR" && zip -qr "${NAME}.zip" "${NAME}" )
SIZE="$(du -h "${OUT_DIR}/${NAME}.zip" | cut -f1)"

echo
echo "  bundle -> ${OUT_DIR}/${NAME}.zip  (${SIZE})"
echo "  staging kept at ${STAGE} for inspection"

if [ "$BROKEN" = "1" ]; then
    echo
    echo "  Bundle built, but it contains links to excluded pages (see above)." >&2
    echo "  Fix those links or narrow EXCLUDE_DOCS before distributing." >&2
    exit 1
fi
