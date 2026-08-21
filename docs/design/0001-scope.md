# 0001 — What defnote is (scope & thesis)

- Status: **accepted** (scope), **planned** (implementation) — 2026-08-21
- Owning issue: none yet (project-level meta-decision; first issue opens with the engine)
- Supersedes: —

Written in the five-section form of the `decision-records` skill.

## 1. What hurts

A research log accumulates conclusions ("A30 seqcut is necessary", "boost off costs
~17% peak", "the writer fix cures test25/27"). Weeks later an experiment shows one was
wrong. In every tool available today the old conclusion just **sits there, still reading
as true**, and nothing tells you which *later* conclusions leaned on it. The notebook
becomes a pile of assertions of unknown current validity. The moment it bit (real, on a
project I worked on): an early run concluded X; a later run refuted X; three downstream
design choices had already been built on X and nobody re-checked them.

## 2. Status quo — name names

- **ADR** (Nygard 2011) + tools **Log4brains**, **adr-tools**, **adrs** (Rust): render a
  DAG of *design decisions* via `supersedes`/`relates-to`. Immutable, good — but they
  graph only the **accepted** nodes; the rejected branch lives as prose inside each file,
  and nothing **recomputes** validity when a premise changes. Built for decisions, not
  for empirical claims that get defeated.
- **DMN** (OMG, 2015) **Decision Requirements Graph**: decisions-as-graph, standardized —
  but models *operational* decisions that execute repeatedly, not one-time findings.
- **Kruchten 2004** decision ontology + **Zimmermann/SOAD JSS 2009** (dependency relations +
  production rules): typed decision-dependency graphs with propagation. The theory of
  "decisions as a graph with reasoning" is **already 20 years old** — do not claim it.
- **Electronic lab notebooks** — **eLabFTW**, **RSpace**: immutable, versioned, provenance.
  But they are record stores; they do **not** propagate belief. Refuting entry N does
  nothing to entries that cited N.
- **Truth Maintenance Systems** — **Doyle 1979 (JTMS)**, **de Kleer 1986 (ATMS)**: the exact
  mechanism for "retract a premise → flip dependents to OUT → propagate". Solid, 40 years
  old. No maintained Python/Rust library, but the algorithm is ~150 lines.
- **Stage-Gate** (Cooper, 1980s): owns the "go / no-go / kill" *vocabulary*, but as a
  linear project-management process, not a claim graph.

Nobody's ELN propagates belief; nobody's TMS is a notebook; nanopublications are
publishing infrastructure, not a lab log.

## 3. What we do instead

An **immutable markdown notebook** (ADR/nanopublication-shaped notes) **plus a JTMS-style
propagation engine**: each note declares what justifies/refutes it; a new experiment result
recomputes the whole graph's go/no-go and moves the defeated subtree into the **no-go**
record, kept navigable as the negative result. Sibling of `decision-records`: that skill
holds decisions that stand; defnote holds conclusions that can be defeated.

Mechanism: DAG label-propagation over `justified_by` / `refuted_by` (provenance is acyclic,
so full non-monotonic JTMS with backtracking is not needed — ATMS only if we later want
to hold competing hypotheses simultaneously).

## 4. Costs — what this does NOT do, what it forecloses

- **Not novel, and we do not claim it is.** "Decisions as a graph + reasoning" = Kruchten/
  Zimmermann; "retract-and-propagate" = Doyle/de Kleer; "immutable claim + provenance" =
  nanopub. **The ownable thing is the assembly** — a lab notebook where an experiment flips
  a prior conclusion's go/no-go and propagates, with the refuted subtree retained. That
  specific product is not on the shelf; the mechanisms all are. If challenged, the claim is
  **architectural** (an obligation inside the notebook), not a new algorithm.
- **DAG-only.** Cyclic / mutually-justifying beliefs are out of scope until proven needed.
- **Single timeline.** Competing simultaneous hypotheses (ATMS "worlds") are deferred.
- **Do not call it a "decision tree"** (collides with ML/OR) or "decisions as a graph"
  (collides with DMN/Log4brains). It is a **defeasible experiment notebook**.

## 5. Status

- Scope/positioning: **accepted**.
- Build shape: **Claude skill first** (Python, agent-maintained), engine as a pure I/O-free
  module so it can later be extracted to a standalone Rust tool if it proves out — **planned**.
- Engine, note schema, propagation: **planned** (not yet implemented).
