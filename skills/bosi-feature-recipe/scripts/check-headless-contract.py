#!/usr/bin/env python3
"""Falsify the mechanical claims bosi-feature-recipe's headless mode makes.

Offline, stdlib only. Checks that the run record is documented once and carried
by every file that writes it, that a run is told to cross phase boundaries, that
the interactive endings survived, that the earlier stdout handoff and the
contradictory phase-end footer have not crept back, and that the README still
describes the skills that exist. Exits non-zero if any check fails.
"""

import re
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
REPO = SKILL.parents[1]
PHASES = SKILL / "phases"
CONTRACT = SKILL / "references" / "headless.md"
TEMPLATE = SKILL / "references" / "recipe-card-template.md"
SKILL_MD = SKILL / "SKILL.md"
README = REPO / "README.md"

RUN_FIELDS = ["runStatus", "runNext", "runQuestion"]
RUN_STATUSES = ["running", "terminal", "needs-input", "blocked"]
HEADLESS = {
    1: "reading-the-recipe",
    2: "mise-en-place",
    3: "cooking",
    4: "tasting",
    5: "plating",
    6: "documentation",
}
HANDOFF = {
    1: "phase-2-mise-en-place.md",
    2: "phase-3-cooking.md",
    3: "phase-4-tasting.md",
    4: "phase-5-plating.md",
    5: "phase-6-documentation.md",
}
# Strings that must not come back: the stdout routing line the card replaced,
# and the stale Claude Code footer b972f03 added to phases 2 and 4.
FORBIDDEN = [
    "RECIPE phase=",
    "nextStepFile",
    "tech spec",
    "CRITICAL STEP COMPLETION NOTE",
    "Menu Handling Logic",
    "EXECUTION RULES",
]
INTERACTIVE_ENDINGS = {
    0: r"New session / Continue",
    1: r"Continue here \(recommended\)",
    2: r"New session \(recommended\)",
    3: r"doesn't offer the New session",
    4: r"New session \(recommended\)",
    5: r"New session \(recommended\)",
    6: r"Don't offer a New session",
}
NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
}

results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))


def phase_path(number):
    hits = sorted(PHASES.glob(f"phase-{number}-*.md"))
    return hits[0] if len(hits) == 1 else None


def phase_text(number):
    path = phase_path(number)
    return path.read_text() if path else ""


# --- the contract says what the card says ---------------------------------

check("contract-exists", CONTRACT.exists(), f"{CONTRACT} missing")
contract_text = CONTRACT.read_text() if CONTRACT.exists() else ""

missing = [f for f in RUN_FIELDS if f not in contract_text]
check("contract-declares-record", not missing, f"undocumented fields: {missing}")

missing = [s for s in RUN_STATUSES if s not in contract_text]
check("contract-declares-run-statuses", not missing, f"undocumented: {missing}")

check(
    "contract-puts-record-on-card",
    "frontmatter" in contract_text and "prints" in contract_text,
    "the record lives in the frontmatter, not in what the run prints",
)

check(
    "contract-runs-to-the-end",
    "phase boundary" in contract_text and "unattended:" in contract_text,
    "a run crosses phase boundaries and logs the calls it took alone",
)

# --- nothing routes through stdout any more -------------------------------

offenders = []
for path in sorted(PHASES.glob("*.md")) + [SKILL_MD, CONTRACT, TEMPLATE]:
    text = path.read_text()
    for needle in FORBIDDEN:
        if needle in text:
            offenders.append(f"{path.name}: {needle!r}")
check("no-stdout-handoff", not offenders, "; ".join(offenders))

# --- the interactive path is untouched ------------------------------------

offenders = []
for number, pattern in INTERACTIVE_ENDINGS.items():
    path = phase_path(number) if number else PHASES / "phase-0-start.md"
    if path is None or not re.search(pattern, path.read_text()):
        offenders.append(f"phase-{number}: /{pattern}/")
check("interactive-endings-intact", not offenders, "; ".join(offenders))

# --- headless surface exists where the card says it does ------------------

ok, detail = True, []
for number in HEADLESS:
    text = phase_text(number)
    if not re.search(r"^#+ .*headless", text, re.M | re.I):
        ok, detail = False, detail + [f"phase-{number}: no Headless heading"]
    if "### Ending a run" not in text:
        ok, detail = False, detail + [f"phase-{number}: no ending rules"]
    if "runNext" not in text:
        ok, detail = False, detail + [f"phase-{number}: does not write the run record"]
check("headless-sections", ok, "; ".join(detail))

ok, detail = True, []
for number, handoff in HANDOFF.items():
    if handoff not in phase_text(number):
        ok, detail = False, detail + [f"phase-{number}: does not hand off to {handoff}"]
if "terminal" not in phase_text(6):
    ok, detail = False, detail + ["phase-6: does not end the run"]
check("phases-hand-off", ok, "; ".join(detail))

skill_text = SKILL_MD.read_text() if SKILL_MD.exists() else ""
check(
    "skill-points-at-contract",
    "--headless" in skill_text and "references/headless.md" in skill_text,
    "SKILL.md must name the flag and the contract file",
)

ok, detail = True, []
for needle in ["--headless", "runStatus"]:
    text = (PHASES / "phase-0-start.md").read_text()
    if needle not in text:
        ok, detail = False, detail + [f"phase-0: missing {needle!r}"]
check("phase0-headless-entry", ok, "; ".join(detail))

template_text = TEMPLATE.read_text() if TEMPLATE.exists() else ""
missing = [f for f in ["runMode:"] + [f + ":" for f in RUN_FIELDS] if f not in template_text]
check("template-carries-record", not missing and "## Open Questions" in template_text,
      f"template missing: {missing}")
check(
    "template-knows-waiting-states",
    "needs-input" in template_text and "blocked" in template_text,
    "runStatus must document the states a run stops in",
)

# --- the README describes the repo that exists ----------------------------

readme = README.read_text() if README.exists() else ""
names = sorted(p.parent.name for p in (REPO / "skills").glob("*/SKILL.md"))
absent = [name for name in names if name not in readme]
check("readme-names-every-skill", not absent, f"missing from README: {absent}")

match = re.search(r"\b([A-Za-z]+) Claude Code skills\b", readme)
if not match:
    check("readme-skill-count", False, "no '<Word> Claude Code skills' sentence")
else:
    counted = NUMBER_WORDS.get(match.group(1).lower())
    check("readme-skill-count", counted == len(names),
          f"README says {match.group(1)}, repo has {len(names)}")

check("readme-documents-headless", "headless" in readme.lower(), "README must mention headless mode")
check("readme-documents-checker", "check-headless-contract" in readme, "README must name the checker")

# --- report ---------------------------------------------------------------

width = max(len(name) for name, _, _ in results)
for name, ok, detail in results:
    line = f"{'PASS' if ok else 'FAIL'}  {name.ljust(width)}"
    if detail and not ok:
        line += f"  {detail}"
    print(line)

failed = [name for name, ok, _ in results if not ok]
print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
sys.exit(1 if failed else 0)
