# M8 — Capstone: Autonomous Lap

**Learning objectives:**

- Integrate perception, localization, navigation, and/or learned control into one run.
- Plan, execute, and debug a full autonomous lap.
- Present results with metrics and a reproducible procedure.

**Reference:** [design/architecture.md](../design/architecture.md)

---

## Capstone brief

### The task

**Complete an autonomous lap of a test course using the stack of your choice, and document
configuration, failures, and lap time so that someone else can reproduce your result.**

You may use:

- **Modular** — SLAM + Nav2 (M5, M6)
- **End-to-end** — a behavior-cloning policy (M7)
- **Hybrid** — for example, Nav2 for global routing with a learned policy for lane-keeping, or
  a learned policy with Nav2's costmap as a safety veto

The choice is yours, and **defending it is part of the assessment**. A well-argued modular
solution beats a hybrid that was chosen because it sounded impressive.

### Deliverables

| # | Deliverable | Form |
|---|---|---|
| 1 | **Working demo** — an autonomous lap, live, in front of the class | Demo day |
| 2 | **Technical report** — approach, configuration, results, failure analysis | 4–6 pages |
| 3 | **Reproduction package** — configs, launch files, weights, map, README | Repository or archive |
| 4 | **Presentation** — 10 minutes + questions | Slides |

### Success criteria

**Baseline (passing):** one full lap completed with **zero interventions**, repeated on at
least **three consecutive attempts**. One lucky lap is not a working system, and saying so is
part of the lesson.

**Beyond baseline**, pick at least one:

- Robustness — same policy works under changed lighting, or with an added obstacle
- Repeatability — lap-time variance across ten laps
- Comparison — both stacks implemented and quantitatively compared
- Recovery — the vehicle detects a failure and does something sensible about it
- Efficiency — a measurably faster lap without a loss of reliability

### Constraints

!!! danger "Non-negotiable, all of them"

    - **≤ walking speed.** The entire [safety analysis](../design/safety.md#43-why-traction-cut-freewheel-steering-is-acceptable)
      is conditional on it. Raising the cap invalidates the safety case, and "we went faster"
      is not a result.
    - **Operator on the RC transmitter, thumbs on the sticks**, for every powered run.
    - **Spotter on the E-stop**, doing nothing else.
    - **Clear area** sized by the coast-down distance you measured in M3.
    - **Abort on the first surprise.** An aborted run that you understood is worth more than a
      completed run that confused you.

---

## Phase plan

Two to three weeks, depending on your course calendar.

### Phase 1 — Propose (before you touch the vehicle)

Write a one-page proposal:

- Which stack, and **why** — in terms of the course's own trade-offs, not preference
- Your course layout, with the **minimum turning radius** from M6 checked against it
- What you will measure, and how
- Your top three predicted failure modes, and what you would do about each

!!! note "The turning-radius check is not a formality"

    `R_min ≈ 2.4 × wheelbase`. Teams routinely design a course their vehicle geometrically
    cannot drive, then spend a week tuning a controller to solve a problem that is not a
    controller problem. Do the arithmetic in the proposal.

### Phase 2 — Build and iterate

Standing up your stack is the easy part. The work is in the loop:
**run → observe a failure → form a hypothesis → change one thing → re-run.**

**Keep a lab log.** Date, configuration change, observed result, one line of interpretation.
This is the raw material for the failure analysis in your report, and it is impossible to
reconstruct afterwards.

```
2026-09-14 14:20  robot_radius 0.14 -> 0.55   Stopped clipping the left corner. Now refuses
                                              the narrow gate -- expected, gate is 0.9 m.
2026-09-14 15:05  swapped DWB -> RPP          Cross-track error 0.42 -> 0.11 m on corner 2.
                                              ADR-SW2 trigger had fired (infeasible commands).
```

### Phase 3 — Characterize

Do not stop at the first success. Run enough trials to say something quantitative.

| Metric | How to measure | Your result |
|---|---|---|
| Lap completion rate | successes / attempts, ≥ 10 attempts | |
| Lap time, mean ± σ | timed from a marked line | |
| Interventions per lap | operator takeovers | |
| Worst deviation from the intended line | measured or from odometry | |
| Time to recover after a deliberate perturbation | e.g. a placed cone | |

### Phase 4 — Demo day

See the checklist below.

---

## Rubric

| Criterion | Weight | Excellent | Adequate | Insufficient |
|---|---|---|---|---|
| **Autonomous performance** | 25% | ≥ 3 consecutive clean laps, plus a robustness result | 3 consecutive clean laps | Cannot complete a lap unaided |
| **Technical depth** | 20% | Design choices argued against real alternatives, citing the design docs | Choices explained | Defaults accepted without comment |
| **Failure analysis** | 20% | Failures diagnosed to a subsystem with evidence; at least one surprising finding | Failures listed and plausibly explained | "It didn't work" |
| **Reproducibility** | 15% | Another team reproduces the result from your package alone | Configs and README present | Undocumented local state |
| **Safety discipline** | 10% | Protocol followed unprompted; abort criteria exercised correctly | Protocol followed | Any protocol violation |
| **Presentation** | 10% | Clear, honest about limitations, handles questions | Covers the work | Unclear or overclaims |

!!! info "Honest failure outscores a lucky success"

    A team that completes two of ten laps and can explain **precisely why the other eight
    failed**, with evidence pointing at a subsystem, has demonstrated more engineering than a
    team that completed ten and cannot say why. Report what happened.

    Overclaiming is penalized in the presentation criterion. "Our policy generalizes" after
    testing one course in one lighting condition is not a finding.

---

## Report structure

**1. Approach and justification (~1 page).** Which stack and why. Reference the trade-offs from
M6 and M7. State what you gave up.

**2. Implementation (~1 page).** Configuration that differs from the defaults, and why each
change was made. Every parameter you changed from the inherited B-MROVER values, with its
measured basis.

**3. Results (~1–2 pages).** The metrics table. Plots: trajectory vs. intended line, lap-time
distribution. State the number of trials.

**4. Failure analysis (~1–2 pages).** The heart of the report. For each significant failure:
what was observed, which subsystem was responsible, what evidence localized it, what you
changed, whether it worked. Include failures you **did not** fix, and say why.

**5. Reproduction.** How to re-run your result from the package.

---

## Demo-day checklist

**The day before**

- [ ] Full dry run, end to end, on the actual course
- [ ] Batteries charged: vehicle pack, laptop, **RC transmitter**
- [ ] Reproduction package committed and pushed
- [ ] Slides done
- [ ] Someone else has run your package from the README alone

**Setup (30 minutes before)**

- [ ] Course laid out and measured
- [ ] Clear area confirmed ≥ coast-down distance; spectators behind a marked line
- [ ] E-stop tested — press it, confirm traction cut and STOCK revert, reset it
- [ ] RC override tested — take the sticks under command, confirm preemption on both axes
- [ ] Map loaded / weights loaded; localization converged
- [ ] All telemetry rates checked against the [timing contract](../design/architecture.md#6-timing-heartbeat-contract)
- [ ] Roles assigned: operator, spotter, engineer

**Before each run**

- [ ] Course clear, announced aloud
- [ ] Operator: thumbs on sticks. Spotter: hand on E-stop
- [ ] Call-and-response: *"Commanding autonomous lap." / "Ready." / "Clear." / "Go."*

**After each run**

- [ ] Log the outcome immediately — time, interventions, anomalies
- [ ] Vehicle to STOCK mode between runs
- [ ] Battery voltage checked (a sagging pack changes behavior and will confuse your results)

**Teardown**

- [ ] E-stop latched, MUX de-energized, pack disconnected
- [ ] Bags and logs copied off the laptop **before** it leaves the room

---

## Closing the loop: update the documentation

Your build and your runs are evidence that this documentation was written *before* anyone had
done it. If you found something wrong, fix it — the edit link at the top of every page goes
straight to the source file.

- [ ] Replace *(measure during bring-up)* placeholders you filled in with your real values
- [ ] Remove the **Draft** banner from any page you have now validated on hardware
- [ ] Correct any procedure that was wrong, and say what actually happened
- [ ] Add the failure modes you hit that are not documented

A build guide written from designs is a hypothesis. Yours is evidence — and contributing it
back is the most durable thing you will produce in this course.

---

## Check yourself

- [ ] Can another team reproduce your lap from your package, without asking you a question?
- [ ] For your worst failure: which subsystem, and what evidence localized it there?
- [ ] What would break first if the speed cap were doubled?
- [ ] Which design decision from M2, M3, or M6 did you most rely on? What if it had gone the
      other way?
- [ ] What is the most honest limitation of your result?

---

**Previous:** [M7 — Behavior cloning](m7-behavior-cloning.md) · **Back to:** [Learn overview](index.md) · **See also:** [Build guide](../build/index.md)
