# Final Report

**Due Monday, December 21, 2026, before class.** One report per team, committed to your fork at
`docs/course/reports/vehicle<n>.md`.

The report is where the [Team deliverable](grading.md#team-deliverable-25) and the
[Final demo](grading.md#final-demo-presentation-20) rubrics find their evidence. It has five
sections, inherited from the [M8 capstone](../learn/m8-capstone.md#report-structure), and the
fourth is the one that matters most.

| Section | Length | What it is for |
|---|---|---|
| 1. Approach | ~1 page | What your team set out to build, and what you gave up |
| 2. Implementation | ~1–2 pages | What you actually built, per track. What differs from the design documents, and why |
| 3. Results | ~2 pages | The acceptance gates: number, procedure, conditions, trials |
| 4. Failure analysis | ~2 pages | **The heart of the report.** What broke, which subsystem, what evidence |
| 5. Reproduction | ~1 page | How another team repeats your result from your fork |

> [!NOTE]
> **Length is a guide, evidence is the requirement**
>
> A short report in which every number has a procedure and a file behind it outscores a long one
> that describes. Write it from your notes, bags and commit history. If you find yourself
> describing a result you no longer have the data for, say that it is unverified.

---

## What makes each section work

**Approach.** Say what your team set out to build, track by track, against the
[track tables](teams.md#the-four-tracks), and what you gave up along the way and why. No charter is
collected, so this section is where that plan is written down. A plan that never changed means
nobody was checking it against the vehicle.

**Implementation.** Name people. *Who built what* is read from here and from the commit history
together, and work that left no commit (measurement, debugging, review) is real work that only this
section and the peer evaluation can show.

**Results.** One row per [acceptance gate](../design/software.md#8-semester-1-scope-and-software-acceptance-gates).
A gate you did not reach has a row with the number you did reach. A gate you did not measure has a
row that says why.

**Failure analysis.** For each significant failure: what was observed, which subsystem, what
evidence localised it there, what you changed, and whether that worked. Include the failures you
did **not** fix. See [Week 14](weeks/w14.md#2-how-to-write-a-failure-analysis).

**Reproduction.** Commits, files, commands. Have someone outside the track follow it before you
submit, and write down where they got stuck.

---

## Skeleton

Copy this into `docs/course/reports/vehicle<n>.md` in your fork and fill it in.

````markdown
# Vehicle <n> — Final Report

| | |
|---|---|
| Team | <name> |
| Members and tracks | <name — track>, ... |
| Fork | <URL> |
| Fork commit this report describes | <hash> |
| Firmware commit on the vehicle | <hash> |
| Bring-up stage passed | <0–5>, on <date> |

## 1. Approach

What the team set out to build, per track, and what changed since.

## 2. Implementation

### Electrical & Firmware
### Chassis & Measurement
### Simulation & Validation
### Software & Autonomy

For each: what exists in the fork, who built it, and what differs from the design documents.

## 3. Results

| Gate | Target | Measured | Trials | Procedure and conditions | Raw data |
|---|---|---|---|---|---|
| `colcon build && colcon test` | clean, non-linter tests | | | | |
| `/mitt/dbw/status` rate | ≥ 50 Hz | | | | |
| USB session dropouts | 0 over ≥ 30 min | | | | |
| Joystick to wheel latency | ≤ 100 ms p95 | | | | |
| Same launch, sim and hardware | plugin only | | | | |
| Twin vs vehicle | within 10% | | | | |
| Odometry drift, 20 m straight | ≤ 2% | | | | |
| Heading after 20 m figure-8 | ≤ 5° | | | | |
| SLAM loop | ≥ 30 m, walls within 10 cm | | | | |

Merge ladder, as it happened:

| Merge | Date | Shown | Not shown, and why |
|---|---|---|---|
| 1 — Electrical + Chassis | 11/23 | | |
| 2 — Simulation + Software | 11/30 | | |
| 3 — the ADR-SW4 gate | 12/07 | | |
| 4 — full integration | 12/14 | | |

## 4. Failure analysis

### <Failure 1, named by what was observed>

- **Observed:**
- **Subsystem:**
- **Evidence:**
- **Change:**
- **Outcome:**

### Failures we did not fix

## 5. Reproduction

1. Clone <fork> at <commit>.
2. ...

What is set outside the repository (udev rules, exported variables, firmware build options):

What a reader outside the track got stuck on when they followed this:

## AI assistance

What tool, for what. `none` is a complete answer if it is true.
````

---

## See also

- [Grading & Rubrics](grading.md) — the two rubrics this report feeds
- [Week 14](weeks/w14.md) — gates, failure analysis and reproducibility
- [Week 15](weeks/w15.md) — the demo day
