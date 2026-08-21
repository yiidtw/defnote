---
name: defnote
description: Defeasible experiment notebook — records empirical conclusions as immutable notes in a justification graph, and when a later experiment refutes a prior conclusion it flips that note to no-go and propagates through everything that depended on it (JTMS-style). Use when keeping a lab/experiment log whose conclusions must stay honest as new evidence arrives, when a result overturns an earlier belief, or when you need to see which downstream conclusions a refuted result invalidates. Sibling of the decision-records (ADR) skill: ADR = "why I decided X" (design, permanent); defnote = "what I concluded from experiment X" (empirical, defeasible).
metadata:
  type: reference
  status: active
---

# defnote — defeasible experiment notebook

> ADR records a decision that stands. A defnote records a **conclusion that can be defeated** by later evidence. When it is, it does not get edited away — it moves to a **no-go** subtree, and everything justified by it is re-checked.

Engine: `scripts/defnote.py` — pure JTMS DAG propagation, no external deps. Full thesis
and prior-art map: [docs/design/0001-scope.md](docs/design/0001-scope.md); note format:
[docs/design/TEMPLATE.md](docs/design/TEMPLATE.md).

## The model (what a note is)

Each note is one markdown file with frontmatter:

```yaml
---
id: n0007
claim: "shield stage A30 (seqcut) is necessary — removing it lets test33 through"
kind: claim          # claim | experiment | assumption
justified_by: [e0012, e0019]   # experiments/notes that must hold for this to be go
refuted_by: []                 # experiments that, if they hold, force this to no-go
supersedes: []                 # older note ids this replaces
status: go           # derived, not hand-set: go | no-go | open
---
body: the reasoning, data pointers, what would defeat it
```

- **go** = has a live justification and nothing refuting it.
- **no-go** = lost all justifications, or a `refuted_by` experiment now holds.
- Notes are **immutable** (git-carried); you overturn by adding a new note that
  `supersedes` the old one — never by editing the conclusion out.

## The move that makes it "adaptive"

Log an experiment whose result refutes conclusion C → the engine recomputes the
justification graph, marks C **no-go**, and cascades to every note that had C in
its `justified_by`. The refuted subtree stays navigable as the **negative record**
(why we stopped believing it), which is the point.

## Workflow

Notes live in a `notes/` dir, one markdown file each (see
[docs/design/TEMPLATE.md](docs/design/TEMPLATE.md)). Commands use
`${CLAUDE_SKILL_DIR}/scripts/defnote.py` so they run from any working directory.

**Add a note** (auto-names the file `YYYYMMDD_HHMMSS_<slug>.md`):

```bash
python ${CLAUDE_SKILL_DIR}/scripts/defnote.py new experiment "what I ran and measured" --dir notes
python ${CLAUDE_SKILL_DIR}/scripts/defnote.py new claim "what I now conclude" --justified-by e-boostmeas --dir notes
```

Then fill the body per the template — `experiment`/`assumption` for data (light),
`claim` for conclusions (full five sections). Cite other notes by their short `id`.

**Recompute go/no-go** — run after adding a note, or whenever a result changes:

```bash
python ${CLAUDE_SKILL_DIR}/scripts/defnote.py notes
```

Rewrites each note's derived `status` and lists anything that flipped plus its
downstream. Add `--check` to preview without writing.

**Overturn a prior conclusion** — never edit the old note. Add a new one that
`supersedes` it (or an experiment listed in the old note's `refuted_by`), then
recompute: the old note flips to no-go and stays as the negative record.

**Blast radius before refuting:**

```bash
python ${CLAUDE_SKILL_DIR}/scripts/defnote.py notes --impact <id>   # what falls if <id> goes?
```

### When to reach for this (agent maintaining a log)
- A run concludes something worth keeping → `new claim` justified by the run's `experiment` note.
- A new result contradicts an existing note → `new` claim that supersedes it, then recompute.
- "Is X still true?" → recompute, read the note's `status` + reason.
