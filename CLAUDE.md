# CLAUDE.md — rules for agents working on defnote

## What this repo is
This repo root **is a Claude skill** (`SKILL.md` at root, `name: defnote`). Keep it that
way: clone into `~/.claude/skills/defnote` must Just Work → `name` field == folder name.

## Decision discipline (this project eats its own dog food)
- Design decisions go in `docs/design/NNNN-*.md`, immutable, five-section form
  (What hurts / Status quo name names / What we do instead / Costs / Status). Overturn by
  writing a new ADR that supersedes — never edit an old one.
- Do NOT overclaim novelty. The positioning is **architectural**, not a new algorithm
  (see 0001 §4). Any "nobody does X" needs a real scan first.

## Naming (official rules that bit us)
- Skill `name`: lowercase + digits + hyphens, ≤64, **no reserved words `claude`/`anthropic`**,
  must equal the directory name. Prefer gerund/descriptive; discovery rides on `description`.

## Language
- Skill + engine in **Python** for now. Keep `scripts/defnote.py` a **pure, I/O-free**
  propagation module (read/write happens at the edges) so it can later be extracted to a
  standalone Rust tool without a rewrite of the core.

## Model
- Notes are immutable markdown + frontmatter. `status` (go/no-go/open) is **derived** by the
  engine, never hand-set. Provenance graph is a **DAG** — no full non-monotonic JTMS.
