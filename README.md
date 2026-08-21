# defnote

A **defeasible experiment notebook**: empirical conclusions recorded as immutable
markdown notes in a justification graph. When a later experiment refutes a prior
conclusion, that note flips to **no-go** and the change propagates to everything that
depended on it (JTMS-style) — the defeated subtree is kept as the negative record, not
edited away.

Sibling of the `decision-records` (ADR) skill:
- **ADR** = *why I decided X* — design, permanent.
- **defnote** = *what I concluded from experiment X* — empirical, **defeasible**.

Shipped as a Claude skill (this repo root **is** the skill: `SKILL.md` + `scripts/`).
Clone it into `~/.claude/skills/defnote` and it works — the folder name must equal the
`name` field (`defnote`).

- Scope & thesis, prior-art map, ownable boundary: [`docs/design/0001-scope.md`](docs/design/0001-scope.md)
- Not novel by design — the value is the assembly (ELN + JTMS + immutable claims). See ADR-0001 §4.

Status: **scaffold** — engine (`scripts/defnote.py`) not yet written.
