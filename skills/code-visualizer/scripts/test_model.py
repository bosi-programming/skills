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
ok("a changed file with a hunk is still warned about its tests",
   any("test" in w for w in rg.warnings(m)), "; ".join(rg.warnings(m)))

m = model(surface=[], reading_order=["a.ts"], risks=[])
m["nodes"][0]["hunks"] = ["@@\n+x"]
m["nodes"][0]["tests"] = "none"
m["nodes"][0]["history"] = {"commits_90d": 4}
ok("a changed file that answers every nudge is quiet",
   not rg.warnings(m), "; ".join(rg.warnings(m)))

# ---- tests: the coverage answer, and the difference between none and unasked
m = model()
m["nodes"][0]["tests"] = {"status": "added", "refs": ["a.test.ts:12"]}
ok("a full tests object validates", not rg.validate(m), "; ".join(rg.validate(m)))

m = model()
m["nodes"][0]["tests"] = "none"
rg.validate(m)
ok("a bare status string becomes an object", m["nodes"][0]["tests"] == {"status": "none"},
   str(m["nodes"][0]["tests"]))

m = model()
m["nodes"][0]["tests"] = ["a.test.ts:12", "a.test.ts:40"]
rg.validate(m)
ok("a bare list of refs implies existing coverage",
   m["nodes"][0]["tests"] == {"status": "existing", "refs": ["a.test.ts:12", "a.test.ts:40"]},
   str(m["nodes"][0]["tests"]))

m = model()
m["nodes"][0]["tests"] = {"status": "covered"}
errs = rg.validate(m)
ok("an unknown status fails validation", any("status" in e for e in errs), "; ".join(errs))
ok("the status error names the node", any("a.ts" in e for e in errs), "; ".join(errs))

for st in ("added", "existing"):
    m = model()
    m["nodes"][0]["tests"] = {"status": st}
    errs = rg.validate(m)
    ok("claiming %s coverage with no refs fails" % st,
       any("refs" in e for e in errs), "; ".join(errs))

m = model()
m["nodes"][0]["tests"] = {"status": "none", "note": "type-only change"}
ok("none needs no refs", not rg.validate(m), "; ".join(rg.validate(m)))

m = model()
m["nodes"][0]["tests"] = {"status": "none", "refs": "a.test.ts:1"}
errs = rg.validate(m)
ok("refs must be a list", any("list" in e for e in errs), "; ".join(errs))

# ---- the coverage warning skips the nodes it makes no sense for
m = model()
m["nodes"][0]["hunks"] = ["@@\n+x"]
m["nodes"].append({"id": "a.test.ts", "kind": "test", "status": "added",
                   "hunks": ["@@\n+t"]})
warns = rg.warnings(m)
ok("a test file is not asked to have tests", not any("a.test.ts" in w for w in warns),
   "; ".join(warns))
ok("a source file with no coverage answer is asked",
   any("a.ts" in w and "test" in w for w in warns), "; ".join(warns))
ok("an untouched related node is not asked", not any("b.ts" in w for w in warns))

m = model()
m["nodes"][0]["hunks"] = ["@@\n+x"]
m["nodes"][0]["tests"] = {"status": "none"}
ok("untested_count counts a changed file with no coverage",
   rg.untested_count(m["nodes"]) == 1, str(rg.untested_count(m["nodes"])))
m["nodes"][0]["tests"] = {"status": "added", "refs": ["a.test.ts:1"]}
ok("untested_count ignores a covered file",
   rg.untested_count(m["nodes"]) == 0, str(rg.untested_count(m["nodes"])))

# ---- surface: what the change asks of callers
def with_surface(*entries):
    m = model(surface=list(entries))
    for n in m["nodes"][:1]:
        n["hunks"] = ["@@\n+x"]
        n["tests"] = "none"
    return m

entry = {"kind": "exported symbol", "name": "resolveThing", "change": "added",
         "ref": "a.ts:12"}
m = with_surface(dict(entry))
ok("a full surface entry validates", not rg.validate(m), "; ".join(rg.validate(m)))
ok("breaking defaults to false", m["surface"][0]["breaking"] is False)

m = with_surface({k: v for k, v in entry.items() if k != "name"})
errs = rg.validate(m)
ok("a surface entry with no name fails", any("name" in e for e in errs), "; ".join(errs))

m = with_surface({k: v for k, v in entry.items() if k != "ref"})
errs = rg.validate(m)
ok("a surface entry with no ref fails", any("ref" in e for e in errs), "; ".join(errs))

m = with_surface(dict(entry, change="moved"))
errs = rg.validate(m)
ok("an unknown change fails", any("change" in e for e in errs), "; ".join(errs))

m = with_surface(dict(entry, kind="grpc method"))
ok("an unknown kind is kept, not rejected", not rg.validate(m), "; ".join(rg.validate(m)))
ok("an unknown kind stays as written", m["surface"][0]["kind"] == "grpc method")

m = with_surface(dict(entry, breaking="yes"))
rg.validate(m)
ok("breaking coerces to a bool", m["surface"][0]["breaking"] is True)

m = model(surface="a.ts:1")
errs = rg.validate(m)
ok("surface must be a list", any("list" in e for e in errs), "; ".join(errs))

m = with_surface(dict(entry), dict(entry, name="oldThing", change="removed",
                                   breaking=True))
rg.validate(m)
ok("breaking_count counts only the breaking ones",
   rg.breaking_count(m) == 1, str(rg.breaking_count(m)))

# ---- an absent surface is not the same claim as an empty one
m = model()
m["nodes"][0]["hunks"] = ["@@\n+x"]
m["nodes"][0]["tests"] = "none"
warns = rg.warnings(m)
ok("a model with no surface key is nudged", any("surface" in w for w in warns),
   "; ".join(warns))
m["surface"] = []
m["reading_order"] = ["a.ts"]
m["risks"] = []
m["nodes"][0]["history"] = {"commits_90d": 4}
ok("an empty surface is a real answer and stays quiet",
   not rg.warnings(m), "; ".join(rg.warnings(m)))

# ---- history: churn and ownership, the context a diff cannot show
def with_history(h):
    m = model(surface=[], reading_order=["a.ts"], risks=[])
    m["nodes"][0]["hunks"] = ["@@\n+x"]
    m["nodes"][0]["tests"] = "none"
    m["nodes"][0]["history"] = h
    return m

m = with_history({"commits_90d": 31, "authors_90d": 5, "last_change": "2026-07-14",
                  "owners": ["@acme/checkout-flow"]})
ok("a full history validates", not rg.validate(m), "; ".join(rg.validate(m)))
ok("hotspot defaults to false", m["nodes"][0]["history"]["hotspot"] is False)
ok("a model with history is quiet", not rg.warnings(m), "; ".join(rg.warnings(m)))

m = with_history({"commits_90d": "many"})
errs = rg.validate(m)
ok("a count must be a number", any("commits_90d" in e for e in errs), "; ".join(errs))

m = with_history({"commits_90d": -2})
errs = rg.validate(m)
ok("a negative count fails", any("commits_90d" in e for e in errs), "; ".join(errs))

m = with_history({"authors_90d": 3, "owners": "@team"})
errs = rg.validate(m)
ok("owners must be a list", any("owners" in e for e in errs), "; ".join(errs))

m = with_history("hot")
errs = rg.validate(m)
ok("history must be an object", any("history" in e for e in errs), "; ".join(errs))

m = with_history({"commits_90d": 31, "hotspot": "yes"})
rg.validate(m)
ok("hotspot coerces to a bool", m["nodes"][0]["history"]["hotspot"] is True)
ok("hotspot_count counts the marked files", rg.hotspot_count(m["nodes"]) == 1,
   str(rg.hotspot_count(m["nodes"])))

m = with_history({"commits_90d": 31})
ok("hotspot_count ignores an unmarked file", rg.hotspot_count(m["nodes"]) == 0)

# ---- one nudge for the whole model, not one per file
m = model(surface=[])
m["nodes"][0]["hunks"] = ["@@\n+x"]
m["nodes"][0]["tests"] = "none"
warns = rg.warnings(m)
ok("a model with no history anywhere is nudged once",
   len([w for w in warns if "history" in w]) == 1, "; ".join(warns))

# ---- reading order: where to start, and what next
def with_order(order):
    m = model(surface=[], reading_order=order, risks=[])  # noqa: E501
    n = m["nodes"][0]
    n["hunks"] = ["@@\n+x"]
    n["tests"] = "none"
    n["history"] = {"commits_90d": 4}
    return m

m = with_order(["a.ts"])
ok("a bare id is accepted as a step", not rg.validate(m), "; ".join(rg.validate(m)))
ok("a bare id becomes an object", m["reading_order"][0] == {"node": "a.ts"},
   str(m["reading_order"][0]))

m = with_order([{"node": "a.ts", "why": "the entry point"}])
ok("a full step validates", not rg.validate(m), "; ".join(rg.validate(m)))

m = with_order(["nowhere.ts"])
errs = rg.validate(m)
ok("a step pointing at no node fails", any("nowhere.ts" in e for e in errs),
   "; ".join(errs))

m = with_order(["a.ts", "a.ts"])
errs = rg.validate(m)
ok("the same node twice fails", any("twice" in e or "duplicate" in e for e in errs),
   "; ".join(errs))

m = with_order("a.ts")
errs = rg.validate(m)
ok("reading_order must be a list", any("list" in e for e in errs), "; ".join(errs))

m = with_order([{"why": "no node named"}])
errs = rg.validate(m)
ok("a step with no node fails", any("node" in e for e in errs), "; ".join(errs))

m = with_order(["a.ts"])
ok("step_index numbers the steps from one",
   rg.step_index(m["reading_order"]) == {"a.ts": 1},
   str(rg.step_index(m["reading_order"])))

# ---- the nudges: one for a missing order, one for a changed file left out
m = model(surface=[], risks=[])
n = m["nodes"][0]
n["hunks"] = ["@@\n+x"]
n["tests"] = "none"
n["history"] = {"commits_90d": 4}
warns = rg.warnings(m)
ok("a model with no reading order is nudged once",
   len([w for w in warns if "reading" in w]) == 1, "; ".join(warns))

m["nodes"].append({"id": "c.ts", "kind": "file", "status": "added",
                   "hunks": ["@@\n+y"], "tests": "none"})
m["reading_order"] = ["a.ts"]
rg.validate(m)
warns = rg.warnings(m)
ok("a changed file left out of the order is named",
   any("c.ts" in w for w in warns), "; ".join(warns))

m["reading_order"] = ["a.ts", "c.ts"]
rg.validate(m)
ok("an order that covers every changed file is quiet",
   not rg.warnings(m), "; ".join(rg.warnings(m)))

# ---- risks: what a reviewer should check, and what to ask
def with_risks(*entries):
    m = model(surface=[], reading_order=["a.ts"], risks=list(entries))
    n = m["nodes"][0]
    n["hunks"] = ["@@\n+x"]
    n["tests"] = "none"
    n["history"] = {"commits_90d": 4}
    return m

risk = {"severity": "high", "statement": "the guard is gone", "ref": "a.ts:14",
        "question": "what happens when payload is null?"}

m = with_risks(dict(risk))
ok("a full risk validates", not rg.validate(m), "; ".join(rg.validate(m)))
ok("a model with an empty risks list is quiet",
   not rg.warnings(with_risks()), "; ".join(rg.warnings(with_risks())))

m = with_risks({k: v for k, v in risk.items() if k != "statement"})
errs = rg.validate(m)
ok("a risk with no statement fails", any("statement" in e for e in errs), "; ".join(errs))

m = with_risks({k: v for k, v in risk.items() if k != "ref"})
errs = rg.validate(m)
ok("a risk with no ref fails", any("ref" in e for e in errs), "; ".join(errs))

m = with_risks(dict(risk, severity="scary"))
errs = rg.validate(m)
ok("an unknown severity fails", any("severity" in e for e in errs), "; ".join(errs))

m = with_risks(dict(risk, severity="HIGH"))
rg.validate(m)
ok("severity is read case-insensitively", m["risks"][0]["severity"] == "high")

m = with_risks({k: v for k, v in risk.items() if k != "severity"})
rg.validate(m)
ok("a risk with no severity is medium", m["risks"][0]["severity"] == "medium")

m = model(surface=[], reading_order=["a.ts"], risks="a.ts:1")
errs = rg.validate(m)
ok("risks must be a list", any("list" in e for e in errs), "; ".join(errs))

m = with_risks(dict(risk), dict(risk, severity="low"))
rg.validate(m)
ok("high_risk_count counts only the high ones", rg.high_risk_count(m) == 1,
   str(rg.high_risk_count(m)))

m = with_risks(dict(risk, node="nowhere.ts"))
errs = rg.validate(m)
ok("a risk pointing at an unknown node fails",
   any("nowhere.ts" in e for e in errs), "; ".join(errs))

# ---- an absent risks key is not the same claim as an empty one
m = model(surface=[], reading_order=["a.ts"])
n = m["nodes"][0]
n["hunks"] = ["@@\n+x"]
n["tests"] = "none"
n["history"] = {"commits_90d": 4}
warns = rg.warnings(m)
ok("a model with no risks key is nudged", any("risks" in w for w in warns),
   "; ".join(warns))

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
ok("the bundled example demonstrates tests",
   any(n.get("tests") for n in ex["nodes"]))
ok("the bundled example shows one honest none, so the mark has something to draw",
   rg.untested_count(ex["nodes"]) > 0, str(rg.untested_count(ex["nodes"])))
ok("the bundled example lists its contract surface", bool(ex.get("surface")))
ok("the bundled example has something breaking to mark",
   rg.breaking_count(ex) > 0, str(rg.breaking_count(ex)))
ok("the bundled example carries churn on its changed files",
   sum(1 for n in ex["nodes"] if n.get("history")) >= 3,
   str(sum(1 for n in ex["nodes"] if n.get("history"))))
ok("the bundled example marks a hotspot", rg.hotspot_count(ex["nodes"]) > 0,
   str(rg.hotspot_count(ex["nodes"])))
ok("the bundled example says where to start", bool(ex.get("reading_order")))
ok("every step in the example says why it is there",
   all(x.get("why") for x in ex.get("reading_order") or []))
ok("the bundled example raises risks", bool(ex.get("risks")))
ok("every risk in the example carries a ref and a question",
   all(r.get("ref") and r.get("question") for r in ex.get("risks") or []))
ok("the bundled example has a high risk to mark", rg.high_risk_count(ex) > 0,
   str(rg.high_risk_count(ex)))
ok("the bundled example answers every nudge",
   not rg.warnings(ex), "; ".join(rg.warnings(ex)))

print("\n%d FAILED" % FAIL if FAIL else "\nall green")
sys.exit(1 if FAIL else 0)
