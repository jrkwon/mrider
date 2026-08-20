# Grading & Rubrics

| Component | Weight | When |
|---|---:|---|
| [Individual labs 1–5](#individual-labs-30) | **30%** | W1–W5, due weekly |
| [Mid-semester presentation](#mid-semester-presentation-15) | **15%** | W8 — 10/26 |
| [Team deliverable](#team-deliverable-25) | **25%** | W16 — 12/21 |
| [Final demo & presentation](#final-demo-presentation-20) | **20%** | W16 — 12/21 |
| [Participation & documentation](#participation-documentation-10) | **10%** | Continuous |

---

## The standard everything is graded against

This project holds itself to one rule, and so does this course:

!!! quote

    **"Honest failure outscores a lucky success."** — [M8 capstone rubric](../learn/m8-capstone.md)

A subsystem that does not work, accompanied by a correct, evidenced diagnosis of why, scores **above**
one that works for reasons you cannot explain.

That is not generosity. It is the actual professional standard. A result you cannot explain is a
result you cannot reproduce, extend, or trust — and this vehicle's three predecessor generations
failed on exactly that. The design documents record those failures by name. Yours will be read the
same way.

**Concretely, in every rubric below:** evidence outranks outcome. Measured numbers outrank
screenshots. "It worked when we demoed it" is not a claim; it is an anecdote.

---

## Individual labs (30%)

Five labs, 6% each, Weeks 1–5. Graded individually — **your** work, **your** submission.

### Rubric (per lab, 10 points)

| | Points | |
|---|---:|---|
| **Correctness** | 4 | The task works, and the expected output is actually observed |
| **Evidence** | 3 | Terminal output, plots, or recordings that show it working — not assertions that it did |
| **Understanding** | 2 | Written answers to the lab's "Check yourself" questions, in your own words |
| **Reproducibility** | 1 | Someone else can follow your submission and get your result |

### What each grade looks like

| | |
|---|---|
| **9–10** | Works, evidenced, explained. The "break it on purpose" step was done and the failure correctly diagnosed |
| **7–8** | Works and is evidenced. Explanations are thin or one step was skipped |
| **5–6** | Partially works, or works with no evidence that it did |
| **3–4** | Substantial attempt with a documented, correctly-diagnosed blocker |
| **0–2** | Not attempted, or submitted without evidence of having run anything |

!!! tip "The 'break it on purpose' step is not optional"

    Every lab ends by deliberately breaking something and diagnosing the result. That step is worth
    more of the grade than getting the happy path working, because the happy path is the part you can
    copy from a classmate and the diagnosis is not.

### Submission

Each lab specifies its own deliverables. Universally required:

- **Terminal output**, as text. Not a photo of your screen.
- **Your code**, if the lab asked for any.
- **Written answers** to the "Check yourself" questions.
- **An AI-assistance declaration** — what tool, for what. See the syllabus.

Due before the next class. Late: −10%/day, floor 50%, up to one week; zero after that.

---

## Mid-semester presentation (15%)

**Week 8, 10/26.** Each team presents for 12 minutes plus 5 minutes of questions.

This is the first checkpoint where the four tracks have to explain themselves to each other — and
that is its real purpose. Present to your classmates, not to me.

### Rubric (100 points)

| | Points | |
|---|---:|---|
| **Subsystem demonstrated** | 30 | Something works, live or recorded. Partial is fine and expected at Week 8 |
| **Evidence quality** | 25 | Numbers, plots, logs. Measured, not asserted |
| **Interface clarity** | 20 | What you need from other tracks and what you will give them, concretely and with dates |
| **Risk honesty** | 15 | What is going wrong, what you will do about it |
| **Delivery** | 10 | Clear, on time, everyone speaks |

!!! warning "The most common way to lose points here"

    Presenting a plan instead of a result. At Week 8 you are five weeks into track work. "We
    researched the options" is a Week 6 answer. Show what you built, even if it is small and broken.

    The second most common: a team that has not talked to the track it depends on. Interface clarity
    is 20 points precisely because it is the thing that fails silently until Week 13.

---

## Team deliverable (25%)

**Due Week 16.** The subsystem your track owns, in the repository, with its evidence.

### Rubric (100 points)

| | Points | |
|---|---:|---|
| **Functionality** | 30 | Does it do what your charter said it would? |
| **Acceptance evidence** | 25 | The gates your track owns, measured, with numbers recorded in `docs/build/` |
| **Code & documentation quality** | 20 | Readable, tested where testable, documented so the next cohort can build on it |
| **Integration** | 15 | It merged. It works with the other tracks' work, not only alone |
| **Failure analysis** | 10 | What did not work, why, and what you would do differently |

**Adjusted by peer evaluation, up to ±15%** on your individual share.

### On acceptance evidence

Your track's gates are named in [software.md §8](../design/software.md) and in
[Teams & Tracks](teams.md). "The gate passes" is not evidence. Evidence is:

- the number you measured
- the procedure you used to measure it
- the raw data, committed
- the conditions it was measured under

Recorded in `docs/build/`, because — as the design documents put it — **the report *is* the
replication claim**.

---

## Final demo & presentation (20%)

**Week 16, 12/21.** 15 minutes of presentation, 5 of questions, plus the live vehicle demo.

### Rubric (100 points)

| | Points | |
|---|---:|---|
| **Autonomous performance** | 25 | What the integrated vehicle actually does on demo day |
| **Technical depth** | 20 | Do you understand the system you built, under questioning? |
| **Failure analysis** | 20 | The heart of it. What broke, what you learned, what the evidence says |
| **Reproducibility** | 15 | Could another team rebuild this from what you wrote down? |
| **Safety discipline** | 10 | Staged bring-up followed; failsafes demonstrated, not assumed |
| **Presentation** | 10 | Clear, well-structured, within time |

These weights are inherited deliberately from the
[M8 capstone rubric](../learn/m8-capstone.md) — the same standard the project applies to itself.

!!! danger "Safety discipline is a hard gate, not just 10 points"

    The [staged bring-up protocol](../design/safety.md) is: **bench before vehicle; wheels-off before
    wheels-on; walking pace before anything faster.** No stage begins until the previous one passes.

    A team that skips a stage does not lose 10 points. It does not demo. This vehicle is heavy enough
    to hurt someone, and the protocol exists so that a class can work on it safely without an
    instructor watching every single action.

### Final report

Submitted with the demo. Structure — again inherited from M8:

1. **Approach** — what you set out to build and why
2. **Implementation** — what you actually built
3. **Results** — measured, with the conditions stated
4. **Failure analysis** — *the heart of the report*
5. **Reproduction** — how someone else repeats your result

---

## Participation & documentation (10%)

Not attendance. Assessed from evidence:

| | |
|---|---|
| **Standups** | Did you report honestly, including blockers? Did you flag a slip early? |
| **Git history** | Commits that show sustained work, with messages someone can read |
| **Documentation** | Design notes, measurements recorded, build pages updated |
| **Helping** | Debugging someone else's problem, answering questions, reviewing a teammate's work |

!!! note "Work with no commits still counts"

    Measurement, debugging, documentation review, and asking the question that saved the team a week
    are all real work that leaves little git trace. That is exactly what the free-text section of the
    [peer evaluation](teams.md#peer-evaluation) is for — tell me what your teammates did that I
    cannot see.

---

## Grade scale

| | |
|---|---|
| **A** | The vehicle works, the evidence is real, and you can explain every part you touched |
| **B** | Solid subsystem, decent evidence, some gaps in depth or integration |
| **C** | Subsystem partially delivered; understanding is present but thin |
| **D** | Minimal contribution, or claims that the evidence does not support |
| **F** | Did not participate, or submitted work that is not yours |

!!! success "The vehicle does not have to fully work for the class to earn A grades"

    Full autonomy on real hardware in one semester, with a car that has not been ordered yet, is
    genuinely ambitious. It may not happen.

    What is graded is **engineering**: measured, evidenced, honestly reported, and reproducible by
    the next cohort. A track that documents exactly why the steering loop could not hold 1° — with
    data — has done better work than one that got a lucky demo and cannot say why it worked.

---

## See also

- [Syllabus](syllabus.md) — schedule, policies, academic integrity
- [Teams & Tracks](teams.md) — track deliverables and peer evaluation
- [M8 — Capstone](../learn/m8-capstone.md) — the rubric this course inherits
