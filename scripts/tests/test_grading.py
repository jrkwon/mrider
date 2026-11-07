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
r"""Tests for the grading path in scripts/lab_report.py.

    python3 -m pytest scripts/tests -q

WHY THESE AND NOT OTHERS
------------------------
`lab_report selftest` already covers the per-lab check functions and that
every report template renders and parses. What had no coverage at all was the
path between a submitted .zip and a file in dist/grade - which is where every
defect an external review found on 2026-11-07 lived, and three of them were
silent:

    identity    a uniqname read from a student-written file became a FILENAME
    ordering    "keep the last" kept the FIRST download, so a resubmission
                was graded as the work it replaced
    robustness  one corrupt archive ended grading for everyone behind it

Every test here is one of those, written so it fails on the old behaviour.

WHAT THEY DELIBERATELY DO NOT ASSERT
------------------------------------
Scores. A test that pins "this submission scores 3 fails" breaks every time a
lab's checks are tightened, which is a thing that should be easy. These assert
IDENTITY, ORDERING, CONTAINMENT and FAILURE ISOLATION - the properties that
must hold whatever the checks say.
"""
import importlib.util
import re
import subprocess
import time
import types
import zipfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent


def load():
    """Import lab_report without running it."""
    spec = importlib.util.spec_from_file_location(
        "lab_report", REPO / "scripts" / "lab_report.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


lr = load()


def make_zip(path, uniqname, lab=1, prefix="mrider-main", mark=None):
    """A minimally plausible submission: a top-level prefix dir, as git
    archive produces, with a REPORT.md carrying an identity.

    `mark` goes in the `## Submission` section, because that is the part
    _grade_tree copies into its output - which is how a test can tell WHICH
    archive was graded. A marker anywhere else is invisible to the caller,
    which is what made the first version of the resubmission test fail
    against correct code.
    """
    body = ("| Field | Value |\n|---|---|\n"
            f"| Uniqname | {uniqname} |\n")
    if mark:
        body += f"\n## Submission\n\nMARKER={mark}\n\n## Notes\n\n-\n"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(f"{prefix}/labs/lab{lab}/REPORT.md", body)
    return path


# --------------------------------------------------------------- identity --
@pytest.mark.parametrize("value", [
    "jaerock", "ab", "ok-name_2", "A1",
])
def test_safe_who_accepts_plausible_uniqnames(value):
    who, complaint = lr.safe_who(value, "t")
    assert who == value and complaint is None


@pytest.mark.parametrize("value", [
    "../../../etc/passwd",          # traversal
    "/tmp/absolute",                # absolute: Path('/a') / '/tmp/x' == '/tmp/x'
    "a/b",                          # any separator at all
    "has space",
    "",
    "x",                            # one character is not a uniqname
    "a" * 40,
    "../../../docs/build/03-electrical",
])
def test_safe_who_refuses_anything_that_could_be_a_path(value):
    who, complaint = lr.safe_who(value, "t")
    assert who is None and complaint


def test_identity_comes_from_the_report_not_the_filename(tmp_path):
    """The LMS prefixes student names onto downloads. Trusting the filename
    turns a renamed file into a row that no longer matches the roster."""
    z = make_zip(tmp_path / "SmithJohn_12345_lab1_whatever.zip", "jsmith")
    who, *_ = lr.grade_zip(1, z)
    assert who == "jsmith"


def test_filename_is_the_fallback_when_the_report_has_no_identity(tmp_path):
    p = tmp_path / "lab1_fallback.zip"
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("mrider-main/labs/lab1/REPORT.md", "no identity table here\n")
    who, *_ = lr.grade_zip(1, p)
    assert who == "fallback"


def test_a_uniqname_that_escapes_the_output_dir_is_refused(tmp_path):
    """The P1. Before 2026-11-07 this wrote outside dist/grade - including
    over files in this repository."""
    z = make_zip(tmp_path / "evil.zip", "../../../docs/build/03-electrical")
    who, fails, _warns, _detail = lr.grade_zip(1, z)
    assert who is None
    assert "not a usable uniqname" in fails[0]


# ------------------------------------------------------------- robustness --
def test_a_corrupt_archive_raises_rather_than_corrupting_the_run(tmp_path):
    p = tmp_path / "lab1_broken.zip"
    p.write_bytes(b"PK\x03\x04 definitely not a zip")
    with pytest.raises(zipfile.BadZipFile):
        lr.grade_zip(1, p)


def test_too_many_members_is_refused_before_extraction(tmp_path):
    p = tmp_path / "lab1_many.zip"
    with zipfile.ZipFile(p, "w") as z:
        for i in range(lr.MAX_MEMBERS + 1):
            z.writestr(f"mrider-main/f{i}.txt", "x")
    with pytest.raises(ValueError, match="members"):
        lr.grade_zip(1, p)


def test_a_zip_bomb_is_refused_on_its_DECLARED_size(tmp_path):
    """Checked before extracting. Reading first and measuring after is how
    the disk fills."""
    p = tmp_path / "lab1_bomb.zip"
    with zipfile.ZipFile(p, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("mrider-main/big.bin", b"\0" * (lr.MAX_UNPACKED + 1))
    assert p.stat().st_size < 2 * 1024 * 1024, "the fixture should be small on disk"
    with pytest.raises(ValueError, match="unpacks to"):
        lr.grade_zip(1, p)


def test_one_bad_archive_does_not_stop_the_ones_after_it(tmp_path, capsys):
    """The property that matters more than any individual check."""
    (tmp_path / "lab1_aaa_broken.zip").write_bytes(b"not a zip")
    make_zip(tmp_path / "lab1_zzz_good.zip", "zoe")
    out = tmp_path / "out"
    rows = run_grade(tmp_path, out)
    names = {r[0] for r in rows}
    assert "zoe" in names, "a good submission after a broken one must still grade"


# ---------------------------------------------------------------- ordering --
def test_a_resubmission_is_chosen_by_arrival_not_by_filename(tmp_path):
    """The LMS appends "-1" to a second copy, and '-' (0x2D) sorts before
    '.' (0x2E), so sorted() puts the SECOND download first. Picking the last
    sorted name therefore picked the FIRST download."""
    first = make_zip(tmp_path / "lab1_smith.zip", "smith", mark="original")
    time.sleep(1.1)
    second = make_zip(tmp_path / "lab1_smith-1.zip", "smith",
                      mark="resubmission")

    assert sorted([first.name, second.name])[-1] == first.name, \
        "if this ever changes, the bug this test guards has moved"
    assert first.stat().st_mtime < second.stat().st_mtime

    out = tmp_path / "out"
    rows = run_grade(tmp_path, out)
    assert len(rows) == 1, "two archives from one student must collapse to one"
    chosen = _mark_of(rows[0])
    assert chosen == "resubmission", \
        f"graded the {chosen}; arrival order must win over filename order"


# -------------------------------------------------------------- containment --
def test_every_written_report_lands_inside_the_output_directory(tmp_path):
    make_zip(tmp_path / "lab1_a.zip", "alpha")
    make_zip(tmp_path / "lab1_b.zip", "bravo")
    out = tmp_path / "out"
    run_grade(tmp_path, out)
    written = sorted(p.name for p in out.rglob("*.md"))
    assert written == ["alpha.md", "bravo.md"]
    for p in out.rglob("*"):
        assert out.resolve() in p.resolve().parents


# ----------------------------------------------------------------- network --
def test_commits_behind_survives_a_dead_network(monkeypatch):
    """Its comment promises "never fatal - a student working offline is still
    allowed to write their report". subprocess.run RAISES TimeoutExpired and
    check=False does nothing about it, so the promise was not kept."""
    real = subprocess.run

    def times_out(*a, **k):
        if a and a[0][:2] == ["git", "fetch"]:
            raise subprocess.TimeoutExpired(a[0], 20)
        return real(*a, **k)

    monkeypatch.setattr(lr.subprocess, "run", times_out)
    assert lr.commits_behind(fetch=True) is None


# ------------------------------------------------------------------ helpers --
def run_grade(zipdir, outdir, lab=1):
    """Drive cmd_grade with dist/ pointed at a temporary directory."""
    rows = {}
    real_write = Path.write_text

    monkey = types.SimpleNamespace(lab=lab, zips=str(zipdir), roster=None)
    old_repo = lr.REPO
    try:
        lr.REPO = outdir.parent / "fakerepo"
        (lr.REPO / "dist").mkdir(parents=True, exist_ok=True)
        lr.cmd_grade(monkey)
        graded = lr.REPO / "dist" / "grade" / f"lab{lab}"
        for p in sorted(graded.glob("*.md")):
            rows[p.stem] = (p.stem, p.read_text())
        # mirror into the caller's outdir so assertions can look at one place
        outdir.mkdir(parents=True, exist_ok=True)
        for p in sorted(graded.glob("*.md")):
            (outdir / p.name).write_text(p.read_text())
    finally:
        lr.REPO = old_repo
    return list(rows.values())


def _mark_of(row):
    """Which archive was graded, read out of the `## Submission` marker."""
    _who, text = row
    m = re.search(r"MARKER=(\w+)", text)
    assert m, f"no marker in the graded report:\n{text[:300]}"
    return m.group(1)
