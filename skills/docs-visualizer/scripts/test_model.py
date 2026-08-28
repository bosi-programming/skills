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
