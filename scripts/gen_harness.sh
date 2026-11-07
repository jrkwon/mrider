#!/usr/bin/env bash
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
#
# Build every harness in harness/*.yml into a figure and a BOM.
#
#     bash scripts/gen_harness.sh
#
# WHY THIS WRAPPER EXISTS RATHER THAN A BARE wireviz CALL
# --------------------------------------------------------
# WireViz lays harnesses out left to right, which is right for a printed
# harness drawing and wrong for a documentation page: the traction supply came
# out 14.8:1, which scales to an unreadable strip at page width. WireViz has no
# option for this, but it will emit its graphviz source, so this rewrites the
# rank direction and re-renders. Same data, 1.4:1.
#
# WHAT THE BOM IS FOR
# -------------------
# Connectors the VEHICLE already owns carry `ignore_in_bom: true`, so the
# generated BOM is a shopping list and not an inventory. That matters more here
# than it sounds: at every tap MRider's two halves are the opposite gender to
# the thing they are named after, and counting them by hand is exactly how
# twelve wrong parts get ordered.

set -euo pipefail
cd "$(dirname "$0")/.."

command -v wireviz >/dev/null 2>&1 || {
    echo "wireviz not found. pip install --user wireviz" >&2
    exit 1
}
command -v dot >/dev/null 2>&1 || {
    echo "graphviz 'dot' not found. apt install graphviz" >&2
    exit 1
}

shopt -s nullglob
for yml in harness/*.yml; do
    base="$(basename "$yml" .yml)"
    echo "  $base"

    # g = graphviz source, t = BOM tsv, h = a browsable page with the BOM in it
    wireviz -f ght "$yml" >/dev/null

    # The one thing WireViz will not let us set.
    sed 's/rankdir=LR ranksep=2/rankdir=TB ranksep=0.6 nodesep=0.25/' \
        "harness/$base.gv" > "harness/$base.tb.gv"

    dot -Tsvg -o "docs/images/$base.svg" "harness/$base.tb.gv"
    rm -f "harness/$base.tb.gv"
done

echo
echo "figures -> docs/images/*.svg      BOMs -> harness/*.bom.tsv"
echo "Edit the YAML, never the SVG."
