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
r"""The three things every figure generator needs and none of them should own.

WHAT IS HERE, AND WHAT IS DELIBERATELY NOT
-------------------------------------------
Here: escaping, and the bold markup that goes with it. Nine generators, five
private copies of `esc` and two of `rich`, all the same.

NOT here: `txt`, `rect`, `panel`, `box`. They look like duplicates and are
not. gen_carrier's txt takes a font style, gen_grub's registers a width for a
fit check, gen_hub's is a method on a flowing column, and the two board
generators' `panel` have genuinely diverged - 66 lines of diff. Merging them
would mean giving every caller the union of four signatures, and the figure
that needed the fifth option would get it added for everyone. Placement is
each figure's own argument; escaping is not.

WHY `rich` RATHER THAN WRITING THE TSPANS
------------------------------------------
Its docstring in gen_relay_board_figure carried the reason, and it is worth
keeping where the function now lives: the first draft of that figure
interpolated tspan constants into every line, two lines were missing their
f-prefix, and the figure shipped a literal `{B}`. Marking the text and
converting it in one place removes the whole class.

Both assertions earn their keep for the same reason - an unbalanced `**` or a
stray brace is invisible in a rendered SVG and obvious here.
"""

#: Opening and closing tags for a bold run inside an SVG <text>.
BOLD = '<tspan font-weight="bold">'
EB = "</tspan>"


def esc(s):
    """XML-escape text destined for an SVG <text> body.

    `&` first, or the ampersands introduced by the later two get escaped
    again. Equivalent to html.escape(s, quote=False), which is what
    gen_authority_tap_figure used before this module existed; attribute
    values are not escaped because nothing here puts user text in one.
    """
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def rich(line):
    """`**bold**` -> tspans. Callers write plain strings, never f-string markup."""
    assert line.count("**") % 2 == 0, f"unbalanced bold: {line}"
    assert "{" not in line and "}" not in line, \
        f"stray brace, missing f-prefix?: {line}"
    return "".join(f"{BOLD}{p}{EB}" if i % 2 else p
                   for i, p in enumerate(line.split("**")) if p)
