#!/usr/bin/env python3
"""One-shot migration: MkDocs admonitions -> GitHub alert syntax.

    python3 scripts/convert_admonitions.py --dry-run     # report, change nothing
    python3 scripts/convert_admonitions.py               # rewrite docs/**/*.md

Run once, on 2026-08-31, across 52 files and 257 blocks. Kept in the repository
so a reviewer can confirm that change was mechanical rather than hand-edited,
and can re-run it against the pre-migration tree to reproduce the result.

WHAT AND WHY
------------
`!!! danger "Title"` bodies are indented four spaces, which in plain CommonMark
is a *code block*. Outside jrkwon.github.io, 12% of the documentation rendered
as unwrapped monospace beneath a literal `!!! danger "..."` line. The source is
now GitHub alert syntax, which is an ordinary blockquote and therefore readable
everywhere; hooks/github_alerts.py converts it back for the site.

TRANSFORMATIONS
---------------
  !!! danger "T"   ->  > [!CAUTION]
      body             > **T**
                       >
                       > body

  !!! quote "T"    ->  > **T**          (a quote IS a blockquote; no marker)
      body             >
                       > body

  ??? failure "T"  ->  <details class="failure" markdown>
      body             <summary>T</summary>
                       body
                       </details>

That last one is deliberate rather than lazy. Material styles `details.failure`
and `.failure>summary` directly, so the raw HTML keeps its colour and icon on
the site; GitHub renders <details> natively and ignores the class; and the
`markdown` attribute (md_in_html) is what lets the body still be Markdown.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys

# Material admonition type -> GitHub alert marker. Collapsing 11 types into
# GitHub's 5 is the point, not a compromise: a non-standard marker such as
# [!DANGER] renders as literal text in every viewer.
TO_ALERT = {
    "danger": "CAUTION", "failure": "CAUTION", "bug": "CAUTION",
    "warning": "WARNING",
    "note": "NOTE", "info": "NOTE", "question": "NOTE", "abstract": "NOTE",
    "tip": "TIP", "success": "TIP", "example": "TIP",
    "attention": "IMPORTANT",
    # `quote` is intentionally absent: it becomes a bare blockquote.
}

OPEN_RE = re.compile(r'^(\s*)(!!!|\?\?\?\+?)\s+([a-z]+)(?:\s+"(.*)")?\s*$')


def convert_file(text: str) -> tuple[str, int, int]:
    lines = text.split("\n")
    out: list[str] = []
    i = 0
    n_alert = n_details = 0

    while i < len(lines):
        m = OPEN_RE.match(lines[i])
        if not m:
            out.append(lines[i])
            i += 1
            continue

        indent, marker, kind, title = m.group(1), m.group(2), m.group(3), m.group(4) or ""
        collapsible = marker.startswith("?")

        # Collect the four-space-indented body, keeping interior blank lines.
        i += 1
        body: list[str] = []
        while i < len(lines):
            ln = lines[i]
            if ln.strip() == "":
                body.append("")
                i += 1
                continue
            if ln.startswith(indent + "    "):
                body.append(ln[len(indent) + 4:])
                i += 1
                continue
            break
        while body and not body[0].strip():
            body.pop(0)
        while body and not body[-1].strip():
            body.pop()

        if collapsible:
            n_details += 1
            out.append(f'{indent}<details class="{kind}" markdown>')
            out.append(f"{indent}<summary>{title}</summary>")
            out.append("")
            out.extend(f"{indent}{b}" if b.strip() else "" for b in body)
            out.append("")
            out.append(f"{indent}</details>")
            out.append("")
            continue

        n_alert += 1
        alert = TO_ALERT.get(kind)
        if alert:
            out.append(f"{indent}> [!{alert}]")
            if title:
                out.append(f"{indent}> **{title}**")
                if body:
                    out.append(f"{indent}>")
        else:
            # `quote` and anything unmapped: a plain blockquote, which is the
            # honest representation and needs no hook to render.
            if title:
                out.append(f"{indent}> **{title}**")
                if body:
                    out.append(f"{indent}>")

        for b in body:
            # A blank line inside the body must become a bare '>' or the
            # blockquote splits in two and the second half loses its callout.
            out.append(f"{indent}> {b}" if b.strip() else f"{indent}>")
        out.append("")

    # Collapse runs of blank lines introduced by the rewrite - but NEVER inside
    # a fenced code block. Python samples use two blank lines between top-level
    # definitions (PEP 8), and silently reflowing code that students copy would
    # be a far worse defect than the one this migration set out to fix.
    cleaned: list[str] = []
    in_fence = False
    fence_marker = ""
    for ln in out:
        stripped = ln.lstrip()
        if stripped.startswith(("```", "~~~")):
            marker = stripped[:3]
            if not in_fence:
                in_fence, fence_marker = True, marker
            elif marker == fence_marker:
                in_fence, fence_marker = False, ""
            cleaned.append(ln)
            continue
        if not in_fence and not ln.strip() and cleaned and not cleaned[-1].strip():
            continue
        cleaned.append(ln)
    return "\n".join(cleaned), n_alert, n_details


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dry-run", action="store_true", help="report without writing")
    ap.add_argument("root", nargs="?", default="docs", help="directory to convert")
    args = ap.parse_args()

    root = pathlib.Path(args.root)
    if not root.is_dir():
        print(f"error: no such directory: {root}", file=sys.stderr)
        return 2

    files = alerts = details = 0
    for f in sorted(root.rglob("*.md")):
        original = f.read_text()
        new, a, d = convert_file(original)
        if new == original:
            continue
        files += 1
        alerts += a
        details += d
        print(f"  {f}  ({a} alerts, {d} details)")
        if not args.dry_run:
            f.write_text(new)

    verb = "would convert" if args.dry_run else "converted"
    print(f"\n{verb}: {alerts} alerts + {details} details across {files} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
