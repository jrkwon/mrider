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
"""
course_grade.py: the arithmetic of the course total.

Every number here is made up. The cases are the ones where a wrong answer
would be silent: a half-marked term read as a low grade, a peer multiplier
leaking onto a component it does not apply to, and a multiplier above 1
pushing the deliverable past its weight.
"""
import csv
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "scripts"))

import course_grade as cg                                     # noqa: E402
import lab_report as lr                                       # noqa: E402

TERM = lr.COURSE_TERM


def write(d, name, text):
    (d / f"scores-{TERM}-{name}.tsv").write_text(text, encoding="utf-8")


def table(d, capsys):
    out = d / "course.csv"
    assert cg.main(["--dir", str(d), "--csv", str(out)]) == 0
    capsys.readouterr()
    with open(out, newline="") as fh:
        return {r["uniqname"]: r for r in csv.DictReader(fh)}


def full_term(d, mult_b="."):
    for n in cg.LABS:
        # a: 10/10 on time.  b: 8/10, two days late on lab 1 only.
        late = 2 if n == 1 else 0
        write(d, f"lab{n}", f"a\t5\t3\t2\t0\t\nb\t5\t2\t1\t{late}\t\n")
    write(d, "mid", "1\t30\t25\t20\t15\t10\t\n2\t15\t15\t10\t5\t5\t\n")
    write(d, "deliverable", "1\t30\t25\t20\t15\t10\t\n2\t24\t20\t16\t12\t8\t\n")
    write(d, "final", "1\t25\t20\t20\t15\t10\t10\t\n2\t20\t10\t10\t5\t5\t0\t\n")
    write(d, "students", f"a\t1\tW\t1.15\t10\t\nb\t2\tE\t{mult_b}\t5\t\n")


def test_full_marks_is_100_and_a_bonus_cannot_exceed_the_weight(tmp_path, capsys):
    full_term(tmp_path)
    t = table(tmp_path, capsys)
    assert float(t["a"]["total"]) == pytest.approx(100.0)
    assert float(t["a"]["deliverable"]) == pytest.approx(25.0)   # 1.15 x 100% is capped
    assert t["a"]["out_of"] == "100"


def test_the_arithmetic_of_a_middling_student(tmp_path, capsys):
    full_term(tmp_path, mult_b="0.85")
    b = table(tmp_path, capsys)["b"]
    # labs: 8/10 x 6 four times, and 8 x 0.8 = 6.4/10 x 6 once
    assert float(b["labs"]) == pytest.approx(4 * 4.8 + 3.84)
    assert float(b["mid"]) == pytest.approx(0.50 * 15)
    assert float(b["deliverable"]) == pytest.approx(0.80 * 0.85 * 25)
    assert float(b["final"]) == pytest.approx(0.50 * 20)         # multiplier not applied
    assert float(b["participation"]) == pytest.approx(5.0)


def test_unmarked_components_leave_the_total_and_its_denominator(tmp_path, capsys):
    full_term(tmp_path)
    write(tmp_path, "final", "1\t.\t.\t.\t.\t.\t.\t\n2\t.\t.\t.\t.\t.\t.\t\n")
    write(tmp_path, "lab5", "a\t5\t.\t.\t0\t\nb\t5\t.\t.\t0\t\n")
    a = table(tmp_path, capsys)["a"]
    assert a["final"] == ""
    assert a["out_of"] == "74"                                   # 100 - 20 - 6
    assert float(a["total"]) == pytest.approx(74.0)


def test_init_creates_dotted_files_and_never_overwrites(tmp_path, capsys):
    write(tmp_path, "lab1", "b\t5\t3\t2\t0\t\na\t5\t3\t2\t0\t\n")
    assert cg.main(["--dir", str(tmp_path), "--init"]) == 0
    students = tmp_path / f"scores-{TERM}-students.tsv"
    assert [f[0] for _, f in cg.rows(students)] == ["a", "b"]
    assert cg.read_team(tmp_path / f"scores-{TERM}-mid.tsv",
                        cg.TEAM_RUBRICS["mid"][1]) == {"1": None, "2": None, "3": None}
    students.write_text("a\t1\tW\t.\t7\t\n", encoding="utf-8")
    cg.main(["--dir", str(tmp_path), "--init"])
    assert students.read_text(encoding="utf-8") == "a\t1\tW\t.\t7\t\n"


def test_a_mark_above_the_column_maximum_is_refused(tmp_path):
    full_term(tmp_path)
    write(tmp_path, "mid", "1\t31\t25\t20\t15\t10\t\n2\t15\t15\t10\t5\t5\t\n")
    with pytest.raises(SystemExit, match="demonstrated=31"):
        cg.main(["--dir", str(tmp_path)])


def test_rubric_columns_add_up_to_100_and_weights_to_the_course():
    for _w, cols in cg.TEAM_RUBRICS.values():
        assert sum(hi for _, hi in cols) == 100
    assert (len(cg.LABS) * cg.LAB_WEIGHT + cg.PARTICIPATION_WEIGHT
            + sum(w for w, _ in cg.TEAM_RUBRICS.values())) == 100
