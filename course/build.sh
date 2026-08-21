#!/usr/bin/env bash
#
# build.sh - render the Marp slide sources to PDF and PPTX.
#
#     bash course/build.sh            # build every deck
#     bash course/build.sh w01 w02    # build only these
#     bash course/build.sh --html     # also emit standalone HTML
#
# PDFs land in docs/course/slides/ so MkDocs publishes them alongside the notes.
# PPTX lands in course/dist/ - those are for editing and for upload to Google
# Slides, not for the site.
#
# Requires: npx (Node 18+). Marp CLI is fetched on first run if absent.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "${HERE}/.." && pwd)"
SRC="${HERE}/slides"
THEME="${HERE}/theme/mrider.css"
PDF_OUT="${REPO}/docs/course/slides"
PPTX_OUT="${HERE}/dist"

WANT_HTML=0
DECKS=()
for arg in "$@"; do
    case "$arg" in
        --html) WANT_HTML=1 ;;
        -h|--help) sed -n '3,12p' "${BASH_SOURCE[0]}"; exit 0 ;;
        *) DECKS+=("$arg") ;;
    esac
done

command -v npx >/dev/null 2>&1 || {
    echo "error: npx not found. Install Node 18+ (sudo apt install -y nodejs npm)." >&2
    exit 1
}

mkdir -p "$PDF_OUT" "$PPTX_OUT"

# No decks named -> build them all.
if [ ${#DECKS[@]} -eq 0 ]; then
    while IFS= read -r f; do DECKS+=("$(basename "$f" .md)"); done \
        < <(find "$SRC" -maxdepth 1 -name '*.md' | sort)
fi

if [ ${#DECKS[@]} -eq 0 ]; then
    echo "error: no slide sources found in ${SRC}" >&2
    exit 1
fi

# Chromium runs sandboxed by default and fails inside containers and some CI
# images. Only relax that when we are actually root, where the sandbox cannot
# initialise anyway - never on a normal desktop session.
MARP_ENV=()
if [ "$(id -u)" = "0" ]; then
    MARP_ENV=(env CHROME_PATH="${CHROME_PATH:-}" MARP_USER=root:root:root)
    export PUPPETEER_ARGS='["--no-sandbox","--disable-setuid-sandbox"]'
fi

# Marp drives a headless Chromium via puppeteer, and it sometimes hangs at 0%
# CPU without ever launching a browser - observed twice, both times while a
# normal Chrome session was running. A hang is indistinguishable from a slow
# render until you go looking, so cap it: 180 s is ~4x the slowest good run.
# Override with MARP_TIMEOUT=<seconds> if a deck genuinely needs longer.
MARP_TIMEOUT="${MARP_TIMEOUT:-180}"

marp_run() {
    timeout --kill-after=10s "$MARP_TIMEOUT" \
        npx --yes @marp-team/marp-cli@4 "$@"
}

FAILED=()
for deck in "${DECKS[@]}"; do
    src="${SRC}/${deck}.md"
    if [ ! -f "$src" ]; then
        echo "  SKIP  ${deck} (no such file: ${src})" >&2
        FAILED+=("$deck")
        continue
    fi

    printf '  %-6s ' "$deck"

    if ! marp_run --theme "$THEME" --allow-local-files \
                  --pdf --output "${PDF_OUT}/${deck}.pdf" "$src" >/dev/null 2>&1; then
        rc=$?
        [ "$rc" -ge 124 ] && echo "TIMED OUT after ${MARP_TIMEOUT}s (pdf)" \
                          || echo "FAILED (pdf)"
        FAILED+=("$deck"); continue
    fi
    printf 'pdf '

    if ! marp_run --theme "$THEME" --allow-local-files \
                  --pptx --output "${PPTX_OUT}/${deck}.pptx" "$src" >/dev/null 2>&1; then
        rc=$?
        [ "$rc" -ge 124 ] && echo "TIMED OUT after ${MARP_TIMEOUT}s (pptx)" \
                          || echo "FAILED (pptx)"
        FAILED+=("$deck"); continue
    fi
    printf 'pptx '

    if [ "$WANT_HTML" = "1" ]; then
        marp_run --theme "$THEME" --allow-local-files \
                 --html --output "${PPTX_OUT}/${deck}.html" "$src" >/dev/null 2>&1 \
            && printf 'html '
    fi

    echo "ok"
done

echo
echo "  PDF  -> ${PDF_OUT}"
echo "  PPTX -> ${PPTX_OUT}"

if [ ${#FAILED[@]} -gt 0 ]; then
    echo
    echo "  ${#FAILED[@]} deck(s) failed: ${FAILED[*]}" >&2
    echo "  A timeout usually means marp could not start headless Chromium." >&2
    echo "  Re-run one without output suppression to see why:" >&2
    echo "    npx @marp-team/marp-cli@4 --theme ${THEME} --pdf ${SRC}/${FAILED[0]}.md" >&2
    exit 1
fi

echo "  all ${#DECKS[@]} deck(s) built"
