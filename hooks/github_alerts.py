"""MkDocs hook: render GitHub alert blockquotes as Material admonitions.

The documentation source uses GitHub's alert syntax:

    > [!CAUTION]
    > **Why this specific break, in week one**
    >
    > ROS 2 nodes find each other automatically...

That is a plain blockquote, so it degrades gracefully in every Markdown viewer
(VS Code, Obsidian, `cat`), and GitHub renders it as a native coloured callout.
Material for MkDocs does not understand it, so this hook rewrites it into the
admonition syntax Material *does* understand, before any extension runs:

    !!! danger "Why this specific break, in week one"

        ROS 2 nodes find each other automatically...

WHY THE SOURCE IS NOT JUST WRITTEN AS `!!!`
-------------------------------------------
Admonition bodies are indented four spaces, which in plain CommonMark is a
*code block*. Outside this site, 12% of the documentation therefore rendered as
unwrapped monospace under a literal `!!! danger "..."` line. The source is the
portable form; this hook is what the site needs, not the other way round.

The mapping is lossy on purpose. GitHub defines exactly five alert types, and a
non-standard marker such as `[!DANGER]` renders as literal text everywhere,
which would defeat the point of the exercise.
"""

from __future__ import annotations

import re

# GitHub alert type -> Material admonition type.
#
# Five in, five out. The source vocabulary was deliberately collapsed to
# GitHub's set: `info`/`note`/`question` were never a load-bearing distinction,
# nor were `tip`/`success`, nor `danger`/`failure`/`bug`.
ALERT_TO_ADMONITION = {
    "NOTE": "note",
    "TIP": "tip",
    "IMPORTANT": "info",
    "WARNING": "warning",
    "CAUTION": "danger",
}

ALERT_RE = re.compile(r"^(\s*)>\s*\[!([A-Za-z]+)\]\s*$")
# A body line that is *only* bold text becomes the admonition title.
TITLE_RE = re.compile(r"^\*\*(.+)\*\*$")
FENCE_RE = re.compile(r"^\s*(```|~~~)")


def _strip_quote(line: str) -> str:
    """Remove one level of blockquote marker from a line."""
    s = line.lstrip()
    if not s.startswith(">"):
        return line
    s = s[1:]
    # A single space after '>' is the marker's own padding, not indentation.
    return s[1:] if s.startswith(" ") else s


def on_page_markdown(markdown: str, page=None, config=None, files=None) -> str:
    lines = markdown.split("\n")
    out: list[str] = []
    i = 0
    in_fence = False
    fence_marker = ""

    while i < len(lines):
        line = lines[i]

        # Never interpret anything inside a fenced code block. A doc that shows
        # this very syntax as an example would otherwise be rewritten.
        fence = FENCE_RE.match(line)
        if fence:
            if not in_fence:
                in_fence, fence_marker = True, fence.group(1)
            elif line.strip().startswith(fence_marker):
                in_fence, fence_marker = False, ""
            out.append(line)
            i += 1
            continue
        if in_fence:
            out.append(line)
            i += 1
            continue

        m = ALERT_RE.match(line)
        if not m:
            out.append(line)
            i += 1
            continue

        indent, alert = m.group(1), m.group(2).upper()
        if alert not in ALERT_TO_ADMONITION:
            # Unknown marker: leave it alone rather than guess. It still renders
            # as an ordinary blockquote, which is a survivable outcome.
            out.append(line)
            i += 1
            continue

        # Gather the contiguous blockquote that follows the marker.
        body: list[str] = []
        i += 1
        while i < len(lines):
            nxt = lines[i]
            if nxt.strip() == ">" or nxt.lstrip().startswith(">"):
                body.append(_strip_quote(nxt))
                i += 1
            else:
                break

        # Drop blank padding at either end so the emitted block is tidy.
        while body and not body[0].strip():
            body.pop(0)
        while body and not body[-1].strip():
            body.pop()

        title = ""
        if body:
            t = TITLE_RE.match(body[0].strip())
            if t:
                title = t.group(1).replace('"', "'")
                body.pop(0)
                while body and not body[0].strip():
                    body.pop(0)

        adm = ALERT_TO_ADMONITION[alert]
        out.append(f'{indent}!!! {adm} "{title}"' if title else f"{indent}!!! {adm}")
        out.append("")
        for b in body:
            # Blank lines stay blank; content is indented four spaces, which is
            # what the admonition extension expects.
            out.append(f"{indent}    {b}" if b.strip() else "")
        out.append("")

    return "\n".join(out)
