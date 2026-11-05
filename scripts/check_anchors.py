#!/usr/bin/env python3
"""Validate every internal anchor link in a built MkDocs site.

    python3 scripts/check_anchors.py [site_dir]

WHY THIS EXISTS
---------------
`mkdocs build --strict` fails on a link to a missing *file*, but a link to a
missing *heading* is only logged at INFO level and the build still exits 0.
So a dead anchor passes CI and deploys silently.

That has happened three times in this repository:

    #112-hardware-rc-signal-mux--the-d3-condition   (doubled hyphen)
    #7-fmea-summary                                 (heading renamed to #7-fmea-lightweight)
    #45-planner-swap-to-smacplannerhybrid--resolved-2026-08-09

All three came from hand-writing a slug instead of copying the generated one -
the em dash in a heading collapses to a single hyphen, not two, which is easy
to get wrong and impossible to notice by reading.

This checker closes that gap. Stdlib only, so it adds nothing to
requirements-docs.txt and runs anywhere Python 3 does.

IT ALSO FAILS A BARE `href="#"`
------------------------------
A link to `#` renders as a link, invites a click and goes nowhere. This checker
used to skip those as no-ops, and 49 accumulated in the order log - every
cross-reference in the file, `[#8a](#)` and the rest, written as if the row
keys were anchors when no anchor existed. The reader cannot tell one from a
working link without clicking it, which is worse than plain text would have
been. The Material theme emits no bare `#`, so every one found is ours.

WHAT IT DELIBERATELY DOES NOT DO
--------------------------------
It ignores links whose *target page* does not exist. `--strict` already fails
on those, and reporting them here too would produce two messages for one fault.
This tool has exactly one job: the fragment after the '#'.
"""

from __future__ import annotations

import html
import posixpath
import re
import sys
from pathlib import Path

ID_RE = re.compile(r'\sid="([^"]+)"')
HREF_RE = re.compile(r"<a\b[^>]*?\bhref=\"([^\"]+)\"", re.IGNORECASE)
SKIP_SCHEMES = ("http://", "https://", "mailto:", "tel:", "data:", "javascript:")


def page_key(html_file: Path, site: Path) -> str:
    """URL path of a built page, e.g. 'design/software/' or '' for the home page."""
    rel = html_file.parent.relative_to(site).as_posix()
    return "" if rel == "." else rel + "/"


def collect_ids(site: Path) -> dict[str, set[str]]:
    """Every anchor id present on each built page."""
    return {
        page_key(f, site): set(ID_RE.findall(f.read_text(errors="ignore")))
        for f in site.rglob("*.html")
        if f.name == "index.html"
    }


def resolve(source: str, href_path: str) -> str:
    """Resolve a link target to a page key, relative to the linking page."""
    if href_path in ("", "./"):
        return source
    joined = posixpath.normpath(posixpath.join("/" + source, href_path)).lstrip("/")
    # MkDocs serves directory-style URLs; normalise both spellings to one key.
    if joined.endswith("/index.html"):
        joined = joined[: -len("index.html")]
    elif joined.endswith(".html"):
        joined = joined[: -len(".html")] + "/"
    if joined and not joined.endswith("/"):
        joined += "/"
    return "" if joined == "./" else joined


def main() -> int:
    site = Path(sys.argv[1] if len(sys.argv) > 1 else "site")

    if not site.is_dir():
        print(f"error: no such directory: {site}", file=sys.stderr)
        print("       run `mkdocs build` first, or pass the site directory.", file=sys.stderr)
        return 2

    ids = collect_ids(site)
    if not ids:
        print(f"error: {site} contains no built pages", file=sys.stderr)
        return 2

    checked = 0
    broken: dict[tuple[str, str, str], int] = {}
    dangling: dict[tuple[str, str, str], int] = {}

    for f in sorted(site.rglob("*.html")):
        if f.name != "index.html":
            continue
        source = page_key(f, site)
        for raw in HREF_RE.findall(f.read_text(errors="ignore")):
            href = html.unescape(raw)
            if href.startswith(SKIP_SCHEMES) or "#" not in href:
                continue
            path, _, frag = href.partition("#")
            if not frag:
                # A bare '#' is a link that renders, invites a click and goes
                # nowhere. This used to be skipped as "a no-op link", and 49 of
                # them accumulated in the order log's cross-references - every
                # [#8a](#) in the file. A reader cannot tell one from a working
                # link until they click it, which is strictly worse than no
                # link at all. The Material theme emits none, so every one is
                # ours.
                key = (source or "<home>", href, "")
                dangling[key] = dangling.get(key, 0) + 1
                continue

            target = resolve(source, path)
            if target not in ids:
                # Missing target page: --strict owns this. Not our job.
                continue

            checked += 1
            if frag not in ids[target]:
                key = (source or "<home>", href, target)
                broken[key] = broken.get(key, 0) + 1

    print(f"anchors checked: {checked} across {len(ids)} pages")

    if dangling:
        total = sum(dangling.values())
        print(f'dangling: {total} link{"s" if total != 1 else ""} with href="#"')
        sys.stdout.flush()
        print('\nLINKS THAT GO NOWHERE (href="#")\n', file=sys.stderr)
        for source, href, _ in sorted(dangling):
            count = dangling[(source, href, "")]
            print(f"  {source}  ({count} link{'s' if count != 1 else ''})",
                  file=sys.stderr)
        print("\n  Give each one a real target, or make it plain text.\n",
              file=sys.stderr)

    if not broken and not dangling:
        print("no broken anchors")
        return 0

    if not broken:
        return 1

    total = sum(broken.values())
    print(f"broken: {len(broken)} distinct "
          f"({total} occurrence{'s' if total != 1 else ''})")
    sys.stdout.flush()

    print("\nBROKEN ANCHORS\n", file=sys.stderr)
    for source, href, target in sorted(broken):
        count = broken[(source, href, target)]
        where = f"  {source}" + (f"  ({count} links)" if count > 1 else "")
        print(where, file=sys.stderr)
        print(f"    -> {href}", file=sys.stderr)
        frag = href.partition("#")[2]
        # Near-miss suggestions catch the common cause: a hand-typed slug that
        # differs from the generated one by a hyphen or a renamed word.
        near = [i for i in ids[target] if i.replace("-", "") == frag.replace("-", "")]
        if not near:
            stem = frag.split("-")[0]
            near = sorted(i for i in ids[target] if stem and i.startswith(stem))[:3]
        if near:
            print(f"       did you mean: {', '.join('#' + n for n in near)}", file=sys.stderr)
        print(file=sys.stderr)

    print("Copy the generated slug from the built page rather than "
          "hand-writing it.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
