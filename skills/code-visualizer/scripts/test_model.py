"""Checks on the model side of render_graph.py: validation and normalisation.

    python3 scripts/test_model.py

It imports the renderer as a module and calls it directly, so what it proves is
what `--check` would say and what `render` would receive.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import render_graph as rg  # noqa: E402

FAIL = 0


def ok(label, cond, extra=""):
    global FAIL
    print(("PASS  " if cond else "FAIL  ") + label + ("  :: " + extra if extra else ""))
    if not cond:
        FAIL += 1


def model(**over):
    base = {
        "nodes": [
            {"id": "a.ts", "kind": "file", "status": "modified"},
            {"id": "b.ts", "kind": "file", "status": "related"},
        ],
        "edges": [],
        "patterns": [],
    }
    base.update(over)
    return json.loads(json.dumps(base))


# ---- hunks normalise into the evidence shape
m = model()
m["nodes"][0]["hunks"] = ["@@ -1,2 +1,3 @@\n+one"]
errs = rg.validate(m)
h = m["nodes"][0]["hunks"][0]
ok("a bare string is accepted as a hunk", not errs, "; ".join(errs))
ok("a bare string becomes a diff", isinstance(h, dict) and h.get("diff", "").endswith("+one"))
ok("a hunk with no ref falls back to the node id", h.get("ref") == "a.ts")

m = model()
m["nodes"][0]["hunks"] = [{"ref": "a.ts:40-52", "diff": "@@\n+x", "explanation": "why"}]
ok("a full hunk validates", not rg.validate(m))
ok("a given ref is kept", m["nodes"][0]["hunks"][0]["ref"] == "a.ts:40-52")

m = model()
m["nodes"][0]["hunks"] = [{"ref": "a.ts:40", "note": "old field name"}]
rg.validate(m)
ok("note is read as an alias for explanation",
   m["nodes"][0]["hunks"][0].get("explanation") == "old field name")

# ---- a hunk with nothing to show is an error, not a silent empty page
m = model()
m["nodes"][0]["hunks"] = [{"ref": "a.ts:40"}]
errs = rg.validate(m)
ok("a hunk with no diff fails validation", any("diff" in e for e in errs), "; ".join(errs))
ok("the error names the node", any("a.ts" in e for e in errs), "; ".join(errs))

m = model()
m["nodes"][0]["hunks"] = "@@ -1 +1 @@"
errs = rg.validate(m)
ok("hunks must be a list", any("list" in e for e in errs), "; ".join(errs))

# ---- warnings: editorial nudges that must not fail the run
m = model()
warns = rg.warnings(m)
ok("a changed file with no hunk is warned about", any("a.ts" in w for w in warns), "; ".join(warns))
ok("an untouched related node is not warned about", not any("b.ts" in w for w in warns))

m = model()
m["nodes"][0]["hunks"] = ["@@\n+x"]
ok("a changed file with a hunk is quiet", not rg.warnings(m), "; ".join(rg.warnings(m)))

# ---- the registry the page reads
m = model(patterns=[{
    "name": "Strategy",
    "evidence": [{"ref": "a.ts:1", "diff": "@@\n+p", "explanation": "e"}],
}])
m["nodes"][0]["hunks"] = [{"ref": "a.ts:9", "diff": "@@\n+h"}]
rg.validate(m)
reg = rg.evidence_index(m["patterns"], m["nodes"])
ok("the registry holds both kinds", len(reg) == 2, str(len(reg)))
ok("pattern evidence comes first", reg[0]["kind"] == "pattern")
ok("hunks come after", reg[1]["kind"] == "hunk")
ok("the hunk entry carries its node", reg[1]["node"] == "a.ts")
ok("the hunk entry carries a label for the header", reg[1]["nodeLabel"] == "a.ts")
idx = rg.hunk_index(reg)
ok("hunk_index maps the node to its registry slot", idx == {"a.ts": [1]}, str(idx))

# ---- the example model still passes, and demonstrates the field
path = os.path.join(HERE, "..", "references", "example-model.json")
with open(path) as fh:
    ex = json.load(fh)
errs = rg.validate(ex)
ok("the bundled example validates", not errs, "; ".join(errs))
ok("the bundled example demonstrates hunks",
   any(n.get("hunks") for n in ex["nodes"]))
ok("the bundled example leaves no changed file without a diff",
   not rg.warnings(ex), "; ".join(rg.warnings(ex)))

print("\n%d FAILED" % FAIL if FAIL else "\nall green")
sys.exit(1 if FAIL else 0)
