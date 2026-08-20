# Lab 5 — How Tightly Can It Turn?

**Week 5 · 10/05 · self-study · due before Week 6 (10/12)**

!!! info "No class on 10/5 — 개천절 대체공휴일"

    This lab is self-paced. Everything you need is on this page, including the theory. Work through
    it alongside [Lab 4](lab4.md); both are due 10/12.

    Stuck? Post in the course channel. Do not sit on a problem for a week.

You will derive the minimum turning radius of a car-like robot, then measure it in simulation and
find that theory and measurement **disagree by about 2%**. Explaining that gap is the lab.

| | |
|---|---|
| **Time** | ~90 minutes |
| **Prerequisite** | Lab 4 (or do them together) |
| **Reading** | This page · [M6 §the non-holonomic constraint](../../learn/m6-nav2.md) |

---

## Part 1 — The bicycle model

MRider has four wheels, but for planning purposes it is a **bicycle**: the two front wheels collapse
to one steered wheel at the centre of the front axle, the two rear wheels to one driven wheel at the
centre of the rear axle.

```
            ↑ x (forward)
            |
    ┌───────────────┐
    │       ⊙ ← front wheel, steered by δ
    │       ┆       │
    │       ┆ L     │      L = wheelbase = 0.63 m
    │       ┆       │      δ = steering angle
    │       ⊗ ← rear wheel (base_link is here)
    └───────────────┘
```

The vehicle cannot move sideways. That single fact — the **non-holonomic constraint** — is what makes
a car harder to plan for than a differential-drive robot, and it is why several later weeks of this
course exist.

When the front wheel is held at angle δ, the vehicle traces a circle. The turn centre lies on the
extension of the rear axle, at distance *R*:

$$ \tan\delta = \frac{L}{R} \qquad\Longrightarrow\qquad R = \frac{L}{\tan\delta} $$

The relation between forward speed *v*, yaw rate *ω*, and steering angle follows:

$$ \omega = \frac{v}{R} = \frac{v\tan\delta}{L} $$

**Read that second equation carefully.** If *v* = 0, then ω = 0 **for any δ whatsoever**. A car
cannot rotate while stationary. This is why your Lab 2 square driver had to keep `linear.x` non-zero
during its turns.

### The number that shapes this course

MRider's front wheels are mechanically limited to **δ_max = 22.5°**. So:

$$ R_{min} = \frac{L}{\tan\delta_{max}} = \frac{0.63}{\tan 22.5°} = \frac{0.63}{0.4142} = 1.52\ \text{m} $$

**The vehicle cannot turn inside a 1.52 m radius.** Not "prefers not to" — cannot. Its wheels do not
point that far.

!!! quote "Where this number actually shows up"

    Open `ros2_ws/src/mitt_navigation/config/nav2_params.yaml` and search for `1.6`. You will find it
    **twice** — as `minimum_turning_radius` on the planner and `min_turning_radius` on the controller.
    Both are R_min with a small safety margin.

    It is also why `xy_goal_tolerance` is 0.6 m rather than the more usual 0.25 m. A vehicle with a
    1.52 m turning circle physically cannot make fine positional corrections near a goal; ask it to
    and it orbits. That tolerance is geometry, not laziness.

---

## Part 2 — Predict before you measure

Fill in this table **before** running anything. Use `R = v/ω` for the requested radius, and
`δ = arctan(L·ω/v)` for the steering angle it implies.

| commanded *v* | commanded *ω* | requested *R* = v/ω | implied δ | Is δ ≤ 22.5°? | predicted actual *R* |
|---|---|---|---|---|---|
| 0.5 m/s | 0.30 rad/s | | | | |
| 0.5 m/s | 1.00 rad/s | | | | |
| 0.5 m/s | 2.00 rad/s | | | | |

Write your predictions down and commit them before Part 3. Predicting first is the whole point —
otherwise you will read the measurement and feel like you knew it all along.

---

## Part 3 — Measure it

Launch the simulator. Then write a node that commands a constant `(v, ω)`, records
`/ackermann_steering_controller/odometry` positions, and fits a circle to them.

You have already written both halves: Lab 2 publishes `Twist` on a timer, and Lab 2 Part 3 subscribes
to that odometry topic. Combine them.

For the circle fit, this algebraic least-squares fit is enough:

```python
import math


def fit_circle(pts):
    """Least-squares circle fit. Returns radius."""
    n = len(pts)
    mx = sum(p[0] for p in pts) / n
    my = sum(p[1] for p in pts) / n
    u = [(p[0] - mx, p[1] - my) for p in pts]

    Suu = sum(a * a for a, b in u)
    Svv = sum(b * b for a, b in u)
    Suv = sum(a * b for a, b in u)
    Suuu = sum(a ** 3 for a, b in u)
    Svvv = sum(b ** 3 for a, b in u)
    Suvv = sum(a * b * b for a, b in u)
    Svuu = sum(b * a * a for a, b in u)

    d = 2 * (Suu * Svv - Suv * Suv)
    if abs(d) < 1e-12:
        return float('inf')            # straight line, infinite radius

    uc = (Svv * (Suuu + Suvv) - Suv * (Svvv + Svuu)) / d
    vc = (Suu * (Svvv + Svuu) - Suv * (Suuu + Suvv)) / d
    return math.sqrt(uc * uc + vc * vc + (Suu + Svv) / n)
```

Run each case for **at least 20 seconds** so the vehicle completes more than a full circle, and
**discard the first third of the samples** — the start is a transient while the steering slews to
angle, and including it biases the fit.

**Expected output**, close to this:

```
commanded w=0.30 rad/s -> v/w= 1.67 m   MEASURED radius= 1.71 m
commanded w=1.00 rad/s -> v/w= 0.50 m   MEASURED radius= 1.49 m
commanded w=2.00 rad/s -> v/w= 0.25 m   MEASURED radius= 1.49 m
```

Your numbers will differ slightly. The **pattern** must match.

---

## Part 4 — Explain what you found

Three things happened. Account for each.

**7.** At ω = 0.30 the vehicle roughly followed the request (1.67 requested, 1.71 measured). At
ω = 1.00 and ω = 2.00 it did **not** — both gave the same 1.49 m. Why do those two cases produce an
identical result despite commanding radii that differ by a factor of two?

**8.** The vehicle **silently ignored** your command. You asked for a 0.25 m radius and got 1.49 m,
with no error, no warning, and no indication that the command was not honoured. Relate this to the
silent failures in Labs 1, 3, and 4. What should a planner do about it?

**9.** Theory says 1.52 m. Measurement says 1.49 m — about 2% low. Propose **at least two** distinct
explanations, and state how you would test each one. Some directions worth considering:

- `base_link` sits at the rear axle centre. Where is the fitted circle's centre relative to it?
- Real Ackermann steering points the inner and outer wheels at *different* angles. The bicycle model
  uses one. Which one does the mechanism's 22.5° limit actually apply to?
- The odometry you measured with is itself computed from a kinematic model. Does that make this test
  partly circular, and if so, what would break the circularity?
- Circle-fit error, and sampling over less than a full revolution.

!!! success "There is no single expected answer to question 9"

    This is graded on the quality of the reasoning and whether your proposed tests would actually
    distinguish between your hypotheses. A well-argued wrong answer scores above a right answer with
    no argument behind it.

    **"Honest failure outscores a lucky success"** applies to analysis, not just hardware.

---

## Part 5 — Break it on purpose

Everything above assumed `wheelbase = 0.63 m`. That number has never been measured — the file it
lives in says so in capital letters.

Edit `config/mitt_dimensions.yaml`:

```yaml
wheelbase: 0.75          # was 0.63
```

Rebuild `mitt_description`, relaunch, and repeat **one** of your measurements.

```bash
colcon build --packages-select mitt_description --symlink-install
```

Answer:

**10.** What happened to the measured minimum radius? Does it match the new theoretical
`0.75/tan(22.5°)`?

**11.** Now suppose the *simulation* says 0.63 m and the *real vehicle* is 0.75 m. Nav2 plans a path
it believes is feasible. What happens when the real car tries to follow it — and at what point in the
process does anyone find out?

!!! danger "This is the exact failure the course is organised to prevent"

    [software.md §8](../../design/software.md) requires that the twin's wheelbase, steering range,
    rate limit, and command latency all match measured hardware **within 10%**. You just produced a
    19% error and watched the consequences.

    This is also why the Chassis track's very first deliverable is a **measured** `mitt_dimensions.yaml`
    — and why Merge 2 in Week 12 exists to prove the twin runs on measured numbers rather than
    plausible ones.

    The project's own design notes are blunt about the precedent: a predecessor's URDF carried
    `chassis_mass = 300 kg` for a ride-on car, and its controller config listed a wheelbase
    contradicting its own URDF. Nobody noticed, because in simulation nothing complains.

Restore `0.63` before submitting.

---

## Check yourself

- [ ] I derived `R = L/tan δ` and can explain why v = 0 means ω = 0
- [ ] I predicted all three cases before measuring
- [ ] My measurements show the clamp: two different commands, one identical radius
- [ ] I proposed at least two testable explanations for the ~2% gap
- [ ] I changed the wheelbase and confirmed the radius moved as theory predicts
- [ ] I can explain why a sim/real geometry mismatch is discovered late and expensively

---

## Deliverables

| | |
|---|---|
| `lab5_radius/` | Your measurement node |
| `lab5_predictions.md` | The Part 2 table, filled in **before** measuring |
| `lab5_results.txt` | Measured output for all three cases, plus the modified-wheelbase run |
| `lab5_answers.md` | Questions 7–11 |
| — | **AI-assistance declaration** |

---

## See also

- [M6 — Navigation (Nav2)](../../learn/m6-nav2.md) — where R_min becomes a planner parameter
- [software.md §4.5](../../design/software.md) — why this vehicle needs a planner that can reverse
