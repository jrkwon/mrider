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
r"""Draw the whole vehicle on one page: every box, and what joins it to what.

    python3 scripts/gen_system_figure.py        # -> docs/images/system-overview.svg

WHY THIS FIGURE EXISTS WHEN architecture.md ALREADY HAS A BLOCK DIAGRAM
-----------------------------------------------------------------------
That one is deliberately abstract - "traction battery pack", "motor driver" -
because it is the page that must not go stale when a part changes. This is the
opposite document: it names the actual parts, the actual pins and the actual
taps, so a builder can trace one wire end to end without opening six pages.

The two are allowed to look different. They are not allowed to disagree about
what connects to what.

WHAT IS CHECKED, BECAUSE A PICTURE CANNOT BE PROOFREAD
-------------------------------------------------------
1. Every edge names nodes that exist. A typo in a graph is an orphan node that
   silently renders as an extra box.
2. Every "#n" in a label is a real line in the order log. A figure that cites
   procurement is a figure that can drift from it - and this project has shipped
   that drift before, with pages still naming a board that was cancelled.
3. Every cluster has nodes, and every node is in exactly one cluster.
"""
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "docs" / "images" / "system-overview.svg"
ORDER_LOG = REPO / "docs" / "order-log.md"

# ---- palette, by what the wire carries -------------------------------------
TRACTION = "#b91c1c"   # thick, the 25 A branch
LOGICPWR = "#b45309"   # the 5 V / coil supply
SIGNAL = "#1d4ed8"     # low-level, information
AUTH = "#7e22ce"       # the authority path through the MUX
USB = "#475569"
STOCKC = "#64748b"

# ---- nodes -----------------------------------------------------------------
# cluster -> (title, fill, edge, [(id, label, bom-or-None)])
CLUSTERS = [
    ("stock", "THE VEHICLE, UNMODIFIED", "#f8fafc", STOCKC, [
        ("pack", "Traction pack\\n12 V, sealed, in the trunk", "#1"),
        ("prot", "Stock inline protector\\n10 A, AUTO-RESETTING", None),
        ("ecu", "Stock ECU  JR1630RX-12V\\nP1 power - M2M3 steering - M1 drive\\n"
                "J1 dash + lights (NOT a tap)", None),
        ("smot", "Steering gearmotor", "#4"),
        ("dmot", "Two rear motors\\nparalleled inside the stock plug", None),
    ]),
    ("power", "POWER BOX", "#fef2f2", TRACTION, [
        ("fuse25", "25 A ATO fuse\\nat the pack", "#12"),
        ("xt60", "XT60\\nthe defined dead point", "#12"),
        ("k0", "E-stop contactor\\n40 A SPST-NO", "#8a"),
        ("estop", "E-stop button\\nlatching, ISO 13850", "#8b"),
        ("tee", "Barrier block JOTB 30-4P\\n30 A, M4", "#12d"),
        ("mux", "Relay MUX  4x SPDT 70 A\\n87a = STOCK (coil off)\\n87 = DBW", "#7"),
        ("drv", "Motor driver MDDS30\\nM1 steering - M2 drive\\nR/C mode", "#3"),
    ]),
    ("logic", "LOGIC BOX - isolated rail", "#fffbeb", LOGICPWR, [
        ("lpack", "Logic pack LiFePO4\\n+ 5 A fuse", "#11a"),
        ("ubec", "UBEC 5 V 3 A  x2", "#11b"),
        ("teensy", "Teensy 4.1  on the signal perfboard\\n"
                   "I2C 18/19 - encoder 0/1 - E-stop sense 20\\n"
                   "i-BUS on Serial3 RX 15", "#2"),
        ("smux", "RC servo MUX\\nhardware override, Layer B", "#9"),
        ("rx", "RC receiver FS-iA6B", "#10"),
    ]),
    ("sense", "SENSORS", "#f0fdf4", "#15803d", [
        ("as5600", "AS5600 absolute angle\\nat the kingpin, load side", "#5"),
        ("hall", "2x DRV5013 Hall latch\\n18 magnets - 36 counts/rev", "#6a"),
        ("imu", "IMU BNO085", "#18"),
        ("lidar", "2D LiDAR RPLIDAR A1M8", "#16"),
        ("cam", "USB camera 1080p 120deg", "#17"),
    ]),
    ("host", "AUTONOMY", "#eff6ff", SIGNAL, [
        ("laptop", "Laptop  ROS 2 Humble\\nmicro-ROS agent, Nav2", None),
        ("pad", "USB gamepad", "#15"),
    ]),
]

# ---- edges -----------------------------------------------------------------
# (from, to, colour, label, penwidth, style)
EDGES = [
    # traction supply -- every tap is an interception, nothing is cut
    ("pack", "fuse25", TRACTION, ".250 tap", 3.0, "solid"),
    ("fuse25", "xt60", TRACTION, "AWG 14", 3.0, "solid"),
    ("xt60", "k0", TRACTION, "", 3.0, "solid"),
    ("k0", "tee", TRACTION, "", 3.0, "solid"),
    ("tee", "prot", TRACTION, ".250 tap, back to stock", 3.0, "solid"),
    ("prot", "ecu", TRACTION, "", 3.0, "solid"),
    ("tee", "drv", TRACTION, "B+ / B-", 3.0, "solid"),
    ("estop", "k0", TRACTION, "coil", 1.6, "dashed"),

    # authority: the two taps, in on 87a and out on 30
    ("ecu", "mux", AUTH, "M2M3 Micro-Fit tap -> 87a\\nM1 .250 tap -> 87a", 2.4, "solid"),
    ("drv", "mux", AUTH, "M1, M2 -> 87", 2.4, "solid"),
    ("mux", "smot", AUTH, "30", 2.4, "solid"),
    ("mux", "dmot", AUTH, "30", 2.4, "solid"),

    # logic rail
    ("lpack", "ubec", LOGICPWR, "5 A fuse", 2.0, "solid"),
    ("ubec", "teensy", LOGICPWR, "5 V -> VIN", 2.0, "solid"),
    ("ubec", "smux", LOGICPWR, "5 V", 2.0, "solid"),
    ("ubec", "rx", LOGICPWR, "5 V", 2.0, "solid"),
    ("lpack", "mux", LOGICPWR, "direct tap -> relay coils", 2.0, "solid"),

    # signal
    ("teensy", "mux", SIGNAL, "gate -> IRLZ44N", 1.6, "solid"),
    ("teensy", "smux", SIGNAL, "PWM x2", 1.6, "solid"),
    ("smux", "drv", SIGNAL, "RC1 / RC2", 1.6, "solid"),
    ("rx", "smux", SIGNAL, "select + PWM", 1.6, "solid"),
    ("rx", "teensy", SIGNAL, "i-BUS -> Serial3", 1.6, "dashed"),
    ("k0", "teensy", SIGNAL, "E-stop sense -> pin 20", 1.6, "dashed"),
    ("as5600", "teensy", SIGNAL, "I2C 18/19", 1.6, "solid"),
    ("hall", "teensy", SIGNAL, "A/B -> pins 0/1", 1.6, "solid"),

    # host
    ("teensy", "laptop", USB, "USB - micro-ROS\\ncommand AND feedback", 2.0, "solid"),
    ("imu", "laptop", USB, "USB", 1.4, "solid"),
    ("lidar", "laptop", USB, "USB", 1.4, "solid"),
    ("cam", "laptop", USB, "USB", 1.4, "solid"),
    ("pad", "laptop", USB, "USB", 1.4, "solid"),
]

LEGEND = [
    (TRACTION, "traction, 25 A branch"),
    (AUTH, "authority through the MUX"),
    (LOGICPWR, "logic rail, isolated"),
    (SIGNAL, "signal"),
    (USB, "USB"),
]


def build():
    nodes = {}
    for cid, _title, _fill, _edge, items in CLUSTERS:
        for nid, label, bom in items:
            assert nid not in nodes, f"duplicate node {nid}"
            nodes[nid] = (cid, label, bom)

    out = [
        'digraph mrider {',
        '  graph [rankdir=TB, fontname="DejaVu Sans", nodesep=0.4, ranksep=0.7,'
        '         bgcolor="#ffffff", compound=true, labelloc=t, fontsize=20,'
        '         label="MRider \u2014 the whole vehicle, and what joins it to what\\n'
        'Grey is the vehicle as delivered. Nothing grey is cut; every tap is an unplug.\\n "];',
        '  node [shape=box, style="filled,rounded", fontname="DejaVu Sans",'
        '        fontsize=11, margin="0.16,0.10"];',
        '  edge [fontname="DejaVu Sans", fontsize=9.5];',
    ]

    for cid, title, fill, edge, items in CLUSTERS:
        out.append(f'  subgraph cluster_{cid} {{')
        out.append(f'    label="{title}"; fontsize=13; fontname="DejaVu Sans";')
        out.append(f'    style="filled,rounded"; fillcolor="{fill}";')
        out.append(f'    color="{edge}"; penwidth=2; fontcolor="{edge}";')
        for nid, label, bom in items:
            tag = f"\\n[{bom}]" if bom else ""
            out.append(f'    {nid} [label="{label}{tag}", fillcolor="#ffffff",'
                       f' color="{edge}"];')
        out.append('  }')

    for a, b, col, lab, pw, style in EDGES:
        assert a in nodes, f"edge from unknown node {a!r}"
        assert b in nodes, f"edge to unknown node {b!r}"
        l = f', label="{lab}", fontcolor="{col}"' if lab else ""
        out.append(f'  {a} -> {b} [color="{col}", penwidth={pw},'
                   f' style={style}, arrowsize=0.7{l}];')

    out.append('  subgraph cluster_legend {')
    out.append('    label="what the colours mean"; fontsize=12; style=rounded;')
    out.append('    color="#cbd5e1"; fontcolor="#64748b";')
    prev = None
    for i, (col, text) in enumerate(LEGEND):
        nid = f"lg{i}"
        out.append(f'    {nid} [label="{text}", shape=plaintext, style="",'
                   f' fontcolor="{col}", fontsize=10.5];')
        if prev:
            out.append(f'    {prev} -> {nid} [color="{col}", penwidth=2.4,'
                       f' arrowhead=none];')
        prev = nid
    out.append('  }')
    out.append('}')
    return "\n".join(out), nodes


def check(dot, nodes):
    # 2. every #n cited is a real order-log line
    log = ORDER_LOG.read_text(encoding="utf-8")
    cited = sorted({b for _c, _l, b in nodes.values() if b})
    missing = []
    for bom in cited:
        n = bom.lstrip("#")
        # the log writes them as **#12d** or as a bare Row cell
        if not re.search(r"\*\*#%s\*\*" % re.escape(n), log) and \
           not re.search(r"\|\s*%s\s*\|\s*<a id=" % re.escape(n), log):
            missing.append(bom)
    assert not missing, f"figure cites BOM lines not in the order log: {missing}"

    # 4. no unexpanded escape reached the DOT. Writing \\u2014 inside an
    #    ordinary Python string emits a literal backslash-u, and graphviz
    #    renders it as the text "u2014" in the title - which is what the first
    #    version of this figure shipped with.
    stray = re.findall(r"\\u[0-9a-fA-F]{4}|(?<![\w\\])u[0-9a-fA-F]{4}\b", dot)
    assert not stray, f"unexpanded escapes in the DOT: {sorted(set(stray))}"

    # 3. every node is in exactly one cluster, and no cluster is empty
    for cid, _t, _f, _e, items in CLUSTERS:
        assert items, f"cluster {cid} is empty"

    # 1. is enforced in build(); re-assert on the emitted text
    for nid in nodes:
        assert re.search(r"\b%s \[label=" % nid, dot), f"{nid} declared but not drawn"
    return len(cited)


def main():
    dot, nodes = build()
    cited = check(dot, nodes)
    gv = REPO / "docs" / "images" / ".system-overview.gv"
    gv.write_text(dot, encoding="utf-8")
    try:
        subprocess.run(["dot", "-Tsvg", "-o", str(OUT), str(gv)], check=True)
    except FileNotFoundError:
        print("graphviz 'dot' not found: apt install graphviz", file=sys.stderr)
        return 1
    finally:
        gv.unlink(missing_ok=True)
    print(f"wrote {OUT.relative_to(REPO)}  "
          f"({len(nodes)} boxes, {len(EDGES)} links, {cited} BOM lines cited)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
