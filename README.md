# defnote

**A defeasible experiment notebook.** Record empirical conclusions as immutable notes in a
justification graph. When a later experiment refutes a prior conclusion, that note flips to
**no-go** and the change propagates (JTMS-style) through everything that depended on it — the
defeated subtree stays as the negative record, never edited away.

A [Claude skill](https://code.claude.com/docs/en/skills) (this repo root *is* the skill).
Sibling of the ADR pattern:

- **ADR** = *why I decided X* — design, permanent.
- **defnote** = *what I concluded from experiment X* — empirical, **defeasible**.

## What it looks like

Worked example ([`examples/cache-study/`](examples/cache-study)) — does a cache help? An early
benchmark says yes (`c-win` → go). A later benchmark shows it thrashes under memory pressure,
which **refutes** `c-win` and **cascades** to `c-default` (which only existed because the cache
was "always a win"). `c-refined` supersedes the too-strong claim; `c-warmup` has no experiment
yet, so it stays **open**.

```mermaid
flowchart BT
  e-bench1["e-bench1: cache cuts p99 800ms -> 120ms"]:::go
  c-win["c-win: the cache is always a net win"]:::nogo
  c-default["c-default: enable the cache by default"]:::nogo
  e-bench2["e-bench2: cache thrashes under memory pressure"]:::go
  c-eviction["c-eviction: add an eviction policy"]:::go
  c-refined["c-refined: net win only when headroom > 20%"]:::go
  c-warmup["c-warmup: the cache warms in under 1s"]:::open
  e-bench1 --> c-win
  e-bench2 -. refutes .-> c-win
  c-win --> c-default
  e-bench1 --> c-eviction
  e-bench2 --> c-eviction
  e-bench1 --> c-refined
  e-bench2 --> c-refined
  c-refined -. supersedes .-> c-win
  classDef go fill:#dafbe1,stroke:#1a7f37;
  classDef nogo fill:#ffebe9,stroke:#cf222e,color:#8b949e;
  classDef open fill:#eaeef2,stroke:#57606a;
```

Green = go, red = no-go (refuted / superseded / cascaded), grey = open. Solid = justifies,
dashed = refutes, dotted = supersedes.

## Quickstart

```bash
# add a note (auto-names the file YYYYMMDD_HHMMSS_<slug>.md)
python scripts/defnote.py new experiment "cache cuts p99 800ms -> 120ms" --dir notes
python scripts/defnote.py new claim "the cache is a net win" --justified-by e-bench1 --dir notes

# recompute go/no-go — writes status back, lists what flipped + its downstream
python scripts/defnote.py notes

# what would fall if a result were refuted?
python scripts/defnote.py notes --impact e-bench1

# visualize
python scripts/defnote.py graph notes | dot -Tsvg > graph.svg   # GraphViz
python scripts/defnote.py graph notes --mermaid                 # Mermaid (renders on GitHub)
```

## How it works

- Notes are immutable markdown + frontmatter (`id`, `kind`, `justified_by`, `refuted_by`,
  `supersedes`); `status` is **derived**, never hand-set. Cite by short `id`, not the filename.
- A claim is **go** iff every `justified_by` is go and no `refuted_by` is go. The moment a
  justification collapses or a refuter goes live it flips to **no-go** and its dependents are
  re-checked. Overturn by adding a note that `supersedes` — never edit the old one.
- Engine: [`scripts/defnote.py`](scripts/defnote.py) — pure JTMS DAG propagation, no deps.

## More

- Thesis, prior-art map, ownable boundary: [`docs/design/0001-scope.md`](docs/design/0001-scope.md)
- Note format: [`docs/design/TEMPLATE.md`](docs/design/TEMPLATE.md)

Background: [Truth Maintenance Systems](https://en.wikipedia.org/wiki/Reason_maintenance)
(Doyle 1979 / de Kleer 1986) for the propagation; ADRs (Nygard 2011) for the note shape.
