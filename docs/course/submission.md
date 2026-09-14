# Submitting Labs

Every lab is submitted the same way: **one report file, one commit, one archive.** The tooling
generates the report, checks it, commits it, and prints the line you paste into the LMS.

```bash
bash scripts/lab.sh init          # once, at the start of term
bash scripts/lab.sh new    1      # start Lab 1
bash scripts/lab.sh check  1      # validate, as often as you like
bash scripts/lab.sh submit 1      # commit, push, and build the archive
```

---

## Why it works this way

You are submitting evidence, not files. A claim is only worth reading next to the thing that proves
it, so each lab produces **one `REPORT.md`** with fixed headings in rubric order: the terminal output
you actually saw, then the answer you drew from it.

Fenced code blocks satisfy the rule that terminal output is submitted **as text, not as a photo of
your screen**. Screenshots, PDFs and maps — the things that genuinely cannot be text — go in
`evidence/`.

> [!NOTE]
> **The second reason is the one that matters after Week 5**
>
> From Week 6 your track's work lives in this repository, your commits are 10% of your grade, and
> your charter is a committed file. Labs 1–5 are where you learn that workflow while the stakes are
> one lab rather than a semester.

---

## Once, at the start of term

Ten minutes, and you never think about it again.

### 1. Accept your repository invitation

**Your lab repository already exists** — it was created for you, it is **private**, and only you and
the instructor can read it. You do not create anything.

Give GitHub your username in the first class, then go to **[github.com/notifications](https://github.com/notifications)**
and accept the invitation to:

```
bimi-courses/mrider-labs-2026-fall-<uniqname>
```

> [!IMPORTANT]
> **This is the one step that fails silently**
>
> Until you accept, your account has no access, and `submit` will fail at the very end with a bare
> permission error that says nothing about invitations. Accept it now, not on the evening Lab 1 is
> due.

You have **push** access: you can commit whatever you like, and you cannot make the repository
public or delete it. That is deliberate — a lab repository that goes public publishes this course's
solutions to next year's class.

### 2. Record it

```bash
cd ~/mrider
git pull origin main       # do this first — see below
bash scripts/lab.sh init
```

> [!WARNING]
> **Pull before you start, especially if you cloned in Week 0**
>
> This repository is updated as the course is taught. A clone taken during Week 0 predates the
> submission tooling entirely — `scripts/lab.sh` is not in it, and neither are the current lab
> instructions.
>
> `lab.sh new` checks this for you and says how far behind you are, but it cannot fix it: only
> `git pull origin main` can.

It asks for your name and uniqname, works out your repository URL from them, and shows it to you.
Press **Enter** to accept it. It writes `.labconfig`, which is git-ignored — it never leaves your
machine.

Your work goes on a branch named `student/<uniqname>`. `origin` stays pointed at the course
repository, so you keep receiving course updates with `git pull origin main`; your own commits go to
`mine`.

```
origin  https://github.com/jrkwon/mrider.git                     course updates, read-only to you
mine    https://github.com/bimi-courses/mrider-labs-2026-fall-…  your branch, private
```

---

## Each lab

### `new` — start the report

```bash
bash scripts/lab.sh new 3
```

Creates `labs/lab3/REPORT.md` and `labs/lab3/evidence/`. Run it **from a terminal that has sourced
`setup_env.sh`**: the generator stamps your host, OS, ROS distro, `RMW_IMPLEMENTATION`,
`ROS_LOCALHOST_ONLY`, `GZ_IP` and the course commit into the report's header. Those are not
decoration. A report generated in a shell that had not sourced `setup_env.sh` says so in its own
header, and `check` will tell you.

The file arrives with every heading the lab needs and two kinds of blank to fill:

| | |
|---|---|
| `PASTE - <command>` | inside a fenced block — paste what that command actually printed |
| `TODO - ...` | a question or a write-up, in your own words |

**Do not delete or rename the generated headings.** They are what makes 24 submissions readable in
one pass, and `check` will refuse a report that is missing one.

### The Measurements block

Near the top of every report is a short `key = value` block:

```ini
topics_unsourced = 7     # Part 5: `ros2 topic list --no-daemon | wc -l` before sourcing
topics_sourced   = 21    # Part 5: the same count after sourcing setup_env.sh
```

These are read **automatically**. Keep the keys exactly as generated — a typo in a key reads as a
missing measurement, not as a wrong one.

The checks test what the lab's physics guarantees, not whether you matched a reference machine.
Drift must grow between one square and three. Two steering commands past the 22.5° limit must clamp
to one radius. A rear-facing camera must be at yaw ±π. A number outside the expected band is a
**warning** — machines differ, and an unusual result you can explain is exactly what this course
rewards. A number that contradicts the lab is a **failure**.

### `check` — validate without submitting

```bash
bash scripts/lab.sh check 3
```

Run it whenever. It reports:

- placeholders you have not replaced, by line number
- generated headings you deleted
- evidence blocks with nothing in them
- missing measurements, and measurements that contradict each other
- missing screenshots or PDFs
- code the lab asked you to write
- **values the lab told you to restore before submitting** — the wheelbase in Lab 4, the LiDAR
  origin in Lab 5

That last one is worth saying plainly. Leaving `wheelbase: 0.75` in place does not break Lab 4; it
quietly poisons every lab you run afterwards on that clone, and you will spend an evening on it in
November.

### `submit` — commit, push, archive

```bash
bash scripts/lab.sh submit 3
```

`submit` runs `check` first and **stops if anything fails**. Nothing is committed and nothing is
pushed. The output names each problem and where it is.

When it passes, it switches to your branch, commits your lab directory and any code the lab asked
for, pushes to `mine`, and writes `dist/lab3_<uniqname>.zip` — cut from the commit with
`git archive`, so the archive and the commit cannot disagree.

`submit` **does not pull.** It commits your work on top of the course repository you already have,
so your branch carries whatever you last pulled. That is why your report's header records the
course commit it was generated from, and how far behind it was.

```
================================================================
 Lab 3 ready to submit
================================================================
  Branch    student/jdoe
  Commit    a9227ed
  Archive   dist/lab3_jdoe.zip  (41 kB)
  Due       2026-10-05

  Upload the archive, and paste this line, into the course LMS:

      lab3  jdoe  a9227ed
```

**Upload the archive to the LMS and paste that line.** The LMS timestamp is what the late policy is
read from, so a pushed commit alone is not a submission.

---

## What is due, and when

| Lab | Report | Also submitted | Due |
|---|---|---|---|
| [1](labs/lab1.md) | `labs/lab1/REPORT.md` | `evidence/rqt_graph.png` | 9/21 |
| [2](labs/lab2.md) | `labs/lab2/REPORT.md` | `ros2_ws/src/lab2_square/` | 9/28 |
| [3](labs/lab3.md) | `labs/lab3/REPORT.md` | `ros2_ws/src/lab3_governor/` | 10/05 |
| [4](labs/lab4.md) | `labs/lab4/REPORT.md` | `ros2_ws/src/lab4_radius/`, `mitt_dimensions.yaml` | 10/12 |
| [5](labs/lab5.md) | `labs/lab5/REPORT.md` | `mitt_sensors.xacro`, `evidence/frames.pdf`, both maps | 10/19 |

Late: −10%/day, floor 50%, up to one week; zero after that. See [Grading](grading.md).

---

## The AI-assistance declaration

Every report has an `## AI assistance` section, and `check` refuses a report where it is empty.
Name the tool and say what you used it for, or write `none`.

This is not a trap. The [syllabus policy](syllabus.md) is *declare it, own it* — you are responsible
for every line you submit, and "the AI wrote it" is not a defence for something you cannot explain.
An honest declaration costs you nothing. An undeclared one is an integrity matter.

---

## Troubleshooting

**`lab.sh: No such file or directory`** — your clone predates the tooling. `git pull origin main`.

**`your course repository is N commits behind origin/main`** — exactly what it says.
`git pull origin main`, then regenerate the report so its header records the current commit.

**`no .labconfig found`** — run `bash scripts/lab.sh init`.

**`already exists. Use --force`** — `new` will not overwrite a report you have written in. If you
really want a fresh skeleton, copy your answers out first.

**`RMW_IMPLEMENTATION was 'rmw_cyclonedds_cpp' ... not 'rmw_fastrtps_cpp'`** — you generated the
report from a shell that had not sourced `setup_env.sh`. Source it and regenerate, or fix the header
row by hand if the work itself was done correctly.

**`push to 'mine' failed`**, mentioning permission or `403` — you have almost certainly not
accepted the repository invitation. One click at
[github.com/notifications](https://github.com/notifications), then re-run `submit`. Your commit is
already safe locally; only the push failed.

**`push to 'mine' failed`** for any other reason — check `git remote -v` points at
`bimi-courses/mrider-labs-2026-fall-<uniqname>`. `bash scripts/lab.sh init` re-derives and re-sets
it.

**`missing section "..."`** — a generated heading was deleted or edited. Compare against a fresh
skeleton: `bash scripts/lab.sh new <n> --force` in a scratch clone.

---

## See also

- [Grading & Rubrics](grading.md) — what the ten points per lab are for
- [Syllabus](syllabus.md) — the academic-integrity and AI policy
- [Environment Setup](environment.md) — `setup_env.sh` and what it sets
