# defnote note format

A note is one immutable markdown file. Filename: **`YYYYMMDD_HHMMSS_<snake_case>.md`**
(time-sortable, unique, auto-generatable). **Cite a note by its short `id`, never by the
filename** — the id is what edges and citations point at, and it must stay stable.

`status` is **derived by the engine** (`scripts/defnote.py`) — never hand-set it.
Keep a note **≤ 200 lines**; if you go over, move raw data/tables/logs into a linked
file and keep the note's reasoning tight.

## `kind: experiment` (or `assumption`) — the light template

A recorded observation or premise. It just holds (`go`) until superseded. No ceremony.

```markdown
---
id: e-boostmeas
kind: experiment
title: boost is a runtime sysfs toggle (measured on/off, no reboot)
supersedes: []
status: go
---
What was run, on what, and the numbers. Link to raw output if long.
```

## `kind: claim` — the full template (ADR-style, five sections)

Only conclusions earn this. A claim with no rejected alternative and no stated cost is
not a claim worth recording — it is a data point (use `experiment`).

```markdown
---
id: c-turbooff
kind: claim
title: turbo-off is applied online with no downtime
justified_by: [e-boostmeas]   # all must be 'go' for this to be 'go'
refuted_by: []                # if any becomes 'go', this flips to 'no-go'
supersedes: []
status: go
---

## 1. What we tested
The concrete run/inputs that led here.

## 2. What was believed before (name names)
The prior state or assumption this replaces or contradicts — the actual claim,
tool, or person, so it is checkable.

## 3. What we now conclude
The claim and its mechanism.

## 4. What would defeat it (the defeasible cost)
The experiment result that would force this to no-go, and what the claim forecloses.
This is the section that makes it a *defeasible* note, not an assertion.

## 5. Status
`go` / `no-go` / `open`, derived. Note which experiments justify or refute it.
```

## The rules the engine enforces / reports
- `status` recomputed on every run from `justified_by` / `refuted_by` / `supersedes`.
- A claim is **no-go** the moment a justification collapses or a refuter goes live —
  and every downstream note that leaned on it is listed for re-check.
- A defeated note is **never edited away**; it stays as the negative record. Overturn by
  adding a new note that `supersedes` it.
- Notes over 200 lines get a warning, not a hard failure.
