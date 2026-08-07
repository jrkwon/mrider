# Getting Started

MRider is a kids ride-on electric vehicle converted into a drive-by-wire, self-driving-ready
research platform. This page points you at the right entry point — pick the row that
matches what you came here to do.

| If you want to… | Start here | Then |
|---|---|---|
| **Understand the system** before committing to anything | [Design → Overview](design/overview.md) | [Architecture](design/architecture.md), then [Drive-by-Wire](design/dbw.md) |
| **Build a vehicle** | [Build Guide](build/index.md) | Work steps 1 → 8 **in order**; do not skip the bench test |
| **Teach or take the course** | [Learn](learn/index.md) | Modules M1 → M8, each with a lecture, a lab, and a slide outline |
| **Know what it costs** | [Bill of Materials](design/bom.md) | ~$1.4k minimum tier / ~$1.9k full tier |
| **Reuse the software only** | [Software](design/software.md) | The ROS 2 Humble stack and its `jrkwon/mrover` reuse map |

## Read the design documents first

The nine documents under [Design](design/overview.md) are the **authoritative
specification**. The Build Guide and the Learn curriculum are both derived from them: when
a build step and a design document disagree, the design document is correct and the build
step is a bug — please [open an issue](https://github.com/jrkwon/mrider/issues).

The single most important one to read before touching hardware is
[Safety](design/safety.md). It defines who is allowed to drive the motors, what happens on
every failure mode, and the staged bring-up protocol that keeps the vehicle on a stand
until it has earned the right to be on the floor.

!!! danger "Every powered test before *Manual drive* is performed wheels-off, on a stand."

    This is not a formality. The vehicle is a 24 V two-seater with enough torque to injure
    someone. Read [Safety](design/safety.md) before applying power.

## What state is this project in?

Design phase complete and consensus-reviewed. Hardware sourcing and the physical build are
next. Concretely:

- **Design documents** — complete and authoritative. Read them as-is.
- **Build Guide** — written from the designs, **not yet performed on a vehicle**. Procedures
  are sound in principle; dimensions, torques, and measured values are marked
  *(measure during bring-up)* rather than guessed.
- **Learn curriculum** — modules M1 and M4–M8 are largely hardware-independent and usable
  now. M2 and M3 include bench-rig labs that have not been run.

Pages in an unvalidated state open with a **Draft** banner. If you build the vehicle and
find that a procedure is wrong, the edit link at the top of every page goes straight to
that file on GitHub.

## Prerequisites

**To build:** basic hand tools, a soldering iron, a multimeter, and a bench power supply;
comfort with ROS 2 on Ubuntu 22.04 and flashing an Arduino.

**To learn:** basic Python and Linux. No robotics background assumed.

**Software environment:** Ubuntu 22.04 + ROS 2 Humble on the onboard laptop. See
[Software](design/software.md) for the full stack and
[Sensors](design/sensors.md#6-onboard-computer-laptop-selection-criteria) for laptop
selection criteria.

## Building this documentation locally

The site is MkDocs + Material, built from the `docs/` directory of the same repository:

```bash
git clone https://github.com/jrkwon/mrider.git
cd mrider
pip install -r requirements-docs.txt
mkdocs serve      # http://127.0.0.1:8000
```

`mkdocs build --strict` is what CI runs — it fails on any broken internal link, so run it
before opening a pull request.
