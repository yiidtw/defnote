#!/usr/bin/env python3
"""defnote — defeasible experiment notebook engine.

Reads a directory of note files (YYYYMMDD_HHMMSS_<slug>.md), builds the
justification graph, and computes each note's go/no-go by JTMS-style propagation
over a DAG. The core (`propagate`) is pure — I/O only at the edges — so it can be
ported to Rust later without touching the logic.

Frontmatter schema (see docs/design/TEMPLATE.md):
    id: c-turbooff            # short, stable, immutable — cite by THIS, not the filename
    kind: claim              # claim | experiment | assumption
    title: ...
    justified_by: [id, ...]  # a claim is 'go' only if all of these are 'go'
    refuted_by:  [id, ...]   # if any of these is 'go', the claim is 'no-go'
    supersedes:  [id, ...]   # ids this note replaces -> they become 'no-go: superseded'
    status: go               # DERIVED by the engine; never hand-set

Commands:
    python defnote.py NOTES_DIR                 # compute, write status back, print report
    python defnote.py NOTES_DIR --check         # compute + report only, do not write
    python defnote.py NOTES_DIR --impact ID     # what-if: if ID fell, which notes flip?
    python defnote.py new KIND "TITLE" [opts]   # scaffold a new note with a correct filename
        opts: --id X  --justified-by a,b  --refuted-by c  --supersedes d  --dir notes
"""
import sys, os, re, glob
from datetime import datetime

LIST_FIELDS = ("justified_by", "refuted_by", "supersedes")
KINDS = ("claim", "experiment", "assumption")
LINE_CAP = 200  # soft: over this, split raw data into a linked file

CLAIM_BODY = """
## 1. What we tested
The concrete run/inputs that led here.

## 2. What was believed before (name names)
The prior state/tool/claim this replaces or contradicts, so it is checkable.

## 3. What we now conclude
The claim and its mechanism.

## 4. What would defeat it (the defeasible cost)
The experiment result that would force this to no-go, and what the claim forecloses.

## 5. Status
Derived. Which experiments justify or refute it.
"""
LEAF_BODY = "What was run, on what, and the numbers. Link to raw output if long.\n"


# ---------- I/O edge: parsing ----------

def parse_frontmatter(text):
    """Dependency-free reader for defnote's fixed, flat schema."""
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.S)
    if not m:
        return None, text
    fm = {}
    for line in m.group(1).splitlines():
        line = line.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        km = re.match(r"^(\w+)\s*:\s*(.*)$", line)
        if not km:
            continue
        k, v = km.group(1), km.group(2).strip()
        if k in LIST_FIELDS:
            inner = v.strip().lstrip("[").rstrip("]")
            fm[k] = [x.strip().strip("\"'") for x in inner.split(",") if x.strip()]
        else:
            fm[k] = v.strip().strip("\"'")
    return fm, m.group(2)


def load_notes(notes_dir):
    notes = {}
    for path in sorted(glob.glob(os.path.join(notes_dir, "*.md"))):
        with open(path, encoding="utf-8") as f:
            fm, _ = parse_frontmatter(f.read())
        if not fm or "id" not in fm:
            print(f"  ! skipped (no id/frontmatter): {os.path.basename(path)}", file=sys.stderr)
            continue
        fm.setdefault("kind", "claim")
        for k in LIST_FIELDS:
            fm.setdefault(k, [])
        fm["_path"] = path
        notes[fm["id"]] = fm
    return notes


# ---------- pure core ----------

def propagate(notes, forced_nogo=frozenset()):
    """PURE. notes: {id: {...}}. forced_nogo: ids pinned no-go (for --impact what-if).
    Returns {id: (status, reason)} with status in {'go', 'no-go', 'open'}."""
    superseded_by = {i: [] for i in notes}
    for i, n in notes.items():
        for s in n["supersedes"]:
            if s in notes:
                superseded_by[s].append(i)
    memo, visiting = {}, set()

    def st(i):
        if i in memo:
            return memo[i]
        if i in forced_nogo:
            memo[i] = ("no-go", "forced (--impact)"); return memo[i]
        if i not in notes:
            return ("go", "external")
        if i in visiting:
            memo[i] = ("no-go", "cycle"); return memo[i]
        visiting.add(i)
        n = notes[i]
        res = None
        for b in superseded_by[i]:
            if st(b)[0] == "go":
                res = ("no-go", f"superseded by {b}"); break
        if res is None:
            if n["kind"] in ("experiment", "assumption"):
                res = ("go", n["kind"])
            elif not n["justified_by"]:
                res = ("open", "no justification")
            else:
                live_ref = [r for r in n["refuted_by"] if st(r)[0] == "go"]
                if live_ref:
                    res = ("no-go", "refuted by " + ", ".join(live_ref))
                else:
                    dead = [j for j in n["justified_by"] if st(j)[0] != "go"]
                    res = ("go", "justified") if not dead else ("no-go", "lost support: " + ", ".join(dead))
        visiting.discard(i)
        memo[i] = res
        return res

    return {i: st(i) for i in notes}


def affected_subtree(notes, root):
    """Everything that (transitively) has `root` in justified_by — who falls if root falls."""
    dependents = {i: [] for i in notes}
    for i, n in notes.items():
        for j in n["justified_by"]:
            if j in dependents:
                dependents[j].append(i)
    seen, stack = set(), [root]
    while stack:
        for d in dependents.get(stack.pop(), []):
            if d not in seen:
                seen.add(d); stack.append(d)
    return seen


# ---------- I/O edge: write / lint ----------

def write_status(note, status):
    with open(note["_path"], encoding="utf-8") as f:
        text = f.read()
    new, n = re.subn(r"(?m)^status\s*:.*$", f"status: {status}", text)
    if n == 0:
        new = re.sub(r"\n---\s*\n", f"\nstatus: {status}\n---\n", text, count=1)
    if new != text:
        with open(note["_path"], "w", encoding="utf-8") as f:
            f.write(new)


def lint(notes):
    warns = []
    ids = set(notes)
    for i, n in notes.items():
        if n["kind"] not in KINDS:
            warns.append(f"{i}: unknown kind '{n['kind']}' (expected {'/'.join(KINDS)})")
        for field in LIST_FIELDS:
            for ref in n[field]:
                if ref not in ids:
                    warns.append(f"{i}: {field} -> '{ref}' does not exist (typo? treated as go)")
        with open(n["_path"], encoding="utf-8") as f:
            ln = sum(1 for _ in f)
        if ln > LINE_CAP:
            warns.append(f"{i}: {ln} lines (>{LINE_CAP}) — split raw data into a linked file")
    return warns


# ---------- commands ----------

def cmd_run(argv):
    args = [a for a in argv if not a.startswith("-")]
    check = "--check" in argv
    impact = None
    if "--impact" in argv:
        idx = argv.index("--impact")
        impact = argv[idx + 1] if idx + 1 < len(argv) else None
    if not args:
        print("usage: defnote.py NOTES_DIR [--check] [--impact ID]"); sys.exit(2)
    notes = load_notes(args[0])
    if not notes:
        print("no notes found"); sys.exit(1)

    if impact:
        if impact not in notes:
            print(f"no such id: {impact}"); sys.exit(2)
        base = propagate(notes)
        hyp = propagate(notes, forced_nogo={impact})
        flipped = [i for i in notes if base[i][0] == "go" and hyp[i][0] != "go"]
        print(f"what-if: if {impact} were refuted...")
        if flipped:
            for i in sorted(flipped):
                print(f"  ✗ {i:14} {notes[i].get('title','')[:56]}  ({hyp[i][1]})")
            print(f"\n{len(flipped)} note(s) would flip to no-go.")
        else:
            print("  nothing downstream depends on it — no cascade.")
        return

    result = propagate(notes)
    mark = {"go": "✓ go   ", "no-go": "✗ no-go", "open": "· open "}
    changed = []
    print(f"defnote — {len(notes)} notes\n")
    for i in sorted(notes, key=lambda x: notes[x]["_path"]):
        status, reason = result[i]
        old = notes[i].get("status", "")
        flag = f"  (was {old})" if old and old != status else ""
        if flag or not old:
            changed.append(i)
        print(f"  {mark[status]}  {i:14} {notes[i].get('title', '')[:56]}  [{reason}]{flag}")
        if not check:
            write_status(notes[i], status)
    for r in [i for i in changed if result[i][0] == "no-go"]:
        aff = affected_subtree(notes, r)
        if aff:
            print(f"\n  ⚠ {r} → no-go; downstream to re-check: {', '.join(sorted(aff))}")
    for w in lint(notes):
        print(f"  ⚠ {w}", file=sys.stderr)
    print("\n" + ("(--check: nothing written)" if check else "status written back to frontmatter"))


def cmd_new(argv):
    opts = {"dir": "notes", "id": None, "justified_by": [], "refuted_by": [], "supersedes": []}
    pos, i = [], 0
    while i < len(argv):
        a = argv[i]
        if a in ("--dir", "--id"):
            opts[a[2:]] = argv[i + 1]; i += 2
        elif a in ("--justified-by", "--refuted-by", "--supersedes"):
            opts[a[2:].replace("-", "_")] = [x.strip() for x in argv[i + 1].split(",") if x.strip()]; i += 2
        else:
            pos.append(a); i += 1
    if len(pos) < 2:
        print('usage: defnote.py new KIND "TITLE" [--id X] [--justified-by a,b] [--refuted-by c] [--supersedes d] [--dir notes]'); sys.exit(2)
    kind, title = pos[0], pos[1]
    if kind not in KINDS:
        print(f"kind must be {'/'.join(KINDS)}, got '{kind}'"); sys.exit(2)
    slug = (re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_") or "note")[:60]
    nid = opts["id"] or f"{kind[0]}-{'-'.join(slug.split('_')[:2])}"
    os.makedirs(opts["dir"], exist_ok=True)
    existing = set(load_notes(opts["dir"]))
    base, k = nid, 2
    while nid in existing:
        nid = f"{base}-{k}"; k += 1
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(opts["dir"], f"{ts}_{slug}.md")
    fm = [
        "---",
        f"id: {nid}",
        f"kind: {kind}",
        f"title: {title}",
        f"justified_by: [{', '.join(opts['justified_by'])}]",
        f"refuted_by: [{', '.join(opts['refuted_by'])}]",
        f"supersedes: [{', '.join(opts['supersedes'])}]",
        "status: open",
        "---",
    ]
    body = CLAIM_BODY if kind == "claim" else LEAF_BODY
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(fm) + "\n" + body)
    print(f"created {path}  (id: {nid})")
    print(f"then recompute: python {os.path.basename(__file__)} {opts['dir']}")


def cmd_graph(argv):
    """Emit the graph: GraphViz DOT (default) or Mermaid (--mermaid, renders on GitHub).
    DOT:      defnote.py graph NOTES_DIR | dot -Tsvg > g.svg
    Mermaid:  defnote.py graph NOTES_DIR --mermaid   (paste into a ```mermaid fence)"""
    args = [a for a in argv if not a.startswith("-")]
    if not args:
        print("usage: defnote.py graph NOTES_DIR [--mermaid]"); sys.exit(2)
    notes = load_notes(args[0])
    result = propagate(notes)

    if "--mermaid" in argv:
        cls = {"go": "go", "no-go": "nogo", "open": "open"}
        out = ["flowchart BT"]
        for i, n in notes.items():
            lbl = (n.get("title", "") or i).replace('"', "'")[:40]
            out.append(f'  {i}["{i}: {lbl}"]:::{cls[result[i][0]]}')
        for i, n in notes.items():
            for j in n["justified_by"]:
                out.append(f"  {j} --> {i}")
            for r in n["refuted_by"]:
                out.append(f"  {r} -. refutes .-> {i}")
            for s in n["supersedes"]:
                out.append(f"  {i} -. supersedes .-> {s}")
        out += ["  classDef go fill:#dafbe1,stroke:#1a7f37;",
                "  classDef nogo fill:#ffebe9,stroke:#cf222e,color:#8b949e;",
                "  classDef open fill:#eaeef2,stroke:#57606a;"]
        print("\n".join(out))
        return

    edge = {"go": "#1a7f37", "no-go": "#cf222e", "open": "#57606a"}   # green / red / grey
    fill = {"go": "#dafbe1", "no-go": "#ffebe9", "open": "#eaeef2"}
    shape = {"experiment": "box", "claim": "ellipse", "assumption": "diamond"}

    def esc(s):
        return s.replace("\\", "").replace('"', "'")

    out = ["digraph defnote {", "  rankdir=BT;",
           '  node [style="filled,rounded", fontname="Helvetica", fontsize=10];',
           '  edge [fontname="Helvetica", fontsize=8];']
    for i, n in notes.items():
        st = result[i][0]
        strike = ' fontcolor="#8b949e"' if st == "no-go" else ""
        out.append(f'  "{i}" [label="{esc(i)}\\n{esc(n.get("title",""))[:38]}", '
                   f'shape={shape.get(n["kind"], "ellipse")}, color="{edge[st]}", '
                   f'fillcolor="{fill[st]}"{strike}];')
    for i, n in notes.items():
        for j in n["justified_by"]:
            out.append(f'  "{j}" -> "{i}" [color="#1a7f37"];')
        for r in n["refuted_by"]:
            out.append(f'  "{r}" -> "{i}" [color="#cf222e", style=dashed, label="refutes"];')
        for s in n["supersedes"]:
            out.append(f'  "{i}" -> "{s}" [color="#8b949e", style=dotted, label="supersedes"];')
    out.append("}")
    print("\n".join(out))


def main():
    cmd = sys.argv[1] if len(sys.argv) >= 2 else ""
    if cmd == "new":
        cmd_new(sys.argv[2:])
    elif cmd == "graph":
        cmd_graph(sys.argv[2:])
    else:
        cmd_run(sys.argv[1:])


if __name__ == "__main__":
    main()
