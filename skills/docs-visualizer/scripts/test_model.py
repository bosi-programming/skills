"""Checks on the model side of render_docs_graph.py.

    python3 scripts/test_model.py

It imports the renderer as a module and calls it directly, so what it proves is
what `--check` would say and what `render` would receive. The render test cannot
cover these: it only sees a page built from the bundled example, and the inputs
worth guarding against are the ones nobody would put in an example.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import render_docs_graph as rg  # noqa: E402

FAIL = 0


def ok(label, cond, extra=""):
    global FAIL
    print(("PASS  " if cond else "FAIL  ") + label + ("  :: " + extra if extra else ""))
    if not cond:
        FAIL += 1


# ---- a model reference only becomes a link when the page will follow it
ok("an https reference survives",
   rg.safe_url("https://diataxis.fr/how-to-guides/") == "https://diataxis.fr/how-to-guides/")
ok("an http reference survives", rg.safe_url("http://example.test") != "")
for bad in ("javascript:alert(1)", "JavaScript:alert(1)", "data:text/html,x",
            "  javascript:alert(1)", "file:///etc/passwd", None, ""):
    ok("a %r reference is dropped rather than escaped into an href" % bad,
       rg.safe_url(bad) == "")

name = sorted(rg.REFERENCE)[0]
ok("an unsafe reference falls back to the catalog rather than losing the link",
   rg.reference_for({"name": name, "reference": "javascript:alert(1)"})
   == rg.REFERENCE[name])
ok("a safe reference still wins over the catalog",
   rg.reference_for({"name": name, "reference": "https://example.test/x"})
   == "https://example.test/x")


# ---- validate returns errors, never a traceback
# A traceback names a Python line instead of the field the author has to fix, so
# every malformed shape below has to come back as a message.
def model(**over):
    base = {"nodes": [{"id": "a.md", "kind": "doc"}], "edges": [], "patterns": [],
            "moves": []}
    base.update(over)
    return json.loads(json.dumps(base))


BAD = [{}, [], {"a": 1}, ["x"], 3, 3.5, True, None, "", "nope"]
SHAPES = {
    "moves[].node": lambda v: model(moves=[{"kind": "cut", "ref": "a.md:1", "node": v}]),
    "participant node": lambda v: model(
        patterns=[{"name": "X", "evidence": [{"ref": "a.md:1"}],
                   "participants": [{"node": v}]}]),
    "edges[].from": lambda v: model(edges=[{"from": v, "to": "a.md"}]),
    "a node id": lambda v: model(nodes=[{"id": "a.md"}, {"id": v}]),
    "node scalars": lambda v: model(
        nodes=[{"id": "a.md", "status": v, "kind": v, "layer": v}]),
    "top-level scalars": lambda v: model(stats=v, summary=v, title=v),
    "the containers": lambda v: model(edges=v, patterns=v, moves=v),
    "the whole model": lambda v: v,
}
crashes = []
for label, shape in SHAPES.items():
    for v in BAD:
        try:
            rg.validate(shape(v))
        except Exception as exc:
            crashes.append("%s = %r -> %s" % (label, v, type(exc).__name__))
ok("no malformed model raises instead of reporting", not crashes,
   "; ".join(crashes[:4]))
ok("and the probe covered every container that names a node",
   len(SHAPES) * len(BAD) == 80, str(len(SHAPES) * len(BAD)))

errs = rg.validate([])
ok("a model that is not an object says so", any("JSON object" in e for e in errs),
   "; ".join(errs))


# ---- NaN and Infinity never reach the page
errs = rg.validate(model(stats={"words_added": float("nan")}))
ok("NaN fails, because JSON has no such number",
   any("NaN or Infinity" in e for e in errs), "; ".join(errs))
ok("and the error names the field",
   any("stats.words_added" in e for e in errs), "; ".join(errs))
errs = rg.validate(model(nodes=[{"id": "a.md", "words_added": float("inf")}]))
ok("Infinity fails the same way", any("NaN or Infinity" in e for e in errs),
   "; ".join(errs))


# ---- a ref has to be reachable, not merely present
for good in ("a.md:12", "docs/a.md:12", "a.md:12-19", "a.md:12,19"):
    ok("%r is a usable ref" % good, not rg.bad_ref(good))
for bad in ("somewhere", "a.md", "a.md:", ":12", "", None, "a.md:x"):
    ok("%r is not a ref a reader can follow" % bad, rg.bad_ref(bad))

errs = rg.validate(model(moves=[{"kind": "cut", "node": "a.md", "ref": "somewhere"}]))
ok("a move with an unreachable ref fails rather than rendering a dead link",
   any("path:line" in e for e in errs), "; ".join(errs))

errs = rg.validate(model(patterns=[{"name": "X", "evidence": [{}]}]))
ok("evidence with no ref fails, the same as a pattern with no evidence",
   any("path:line" in e for e in errs), "; ".join(errs))


# ---- nodes is required and has to hold something, as the schema now says
errs = rg.validate({"nodes": []})
ok("an empty nodes list fails, matching references/model-schema.md",
   any("non-empty" in e for e in errs), "; ".join(errs))

with open(os.path.join(HERE, "..", "references", "example-model.json")) as fh:
    ex = json.load(fh)
errs = rg.validate(ex)
ok("the bundled example validates", not errs, "; ".join(errs))

print("\n%d FAILED" % FAIL if FAIL else "\nall green")
sys.exit(1 if FAIL else 0)
