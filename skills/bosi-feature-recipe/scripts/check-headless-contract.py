#!/usr/bin/env python3
"""Falsify the mechanical claims bosi-feature-recipe's headless mode makes.

Offline, stdlib only. Checks that the routing line has exactly one dialect
across the contract and every phase that emits one, that the interactive
endings survived the change, that an earlier contradictory phase-end footer
has not crept back, and that the README still describes the skills that
exist. Exits non-zero if any check fails.
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

ROUTING_KEYS = ["phase", "status", "next", "card"]
STATUSES = ["done", "needs-input", "blocked", "terminal"]
# phase number -> its own phase token, for the phases that may run headless
HEADLESS = {3: "cooking", 4: "tasting", 5: "plating", 6: "documentation"}
# phase number -> the routing line's `next` when the run is not blocked
EXPECTED_NEXT = {
    3: ["phase-4-tasting.md"],
    4: ["phase-5-plating.md"],
    5: ["phase-5-plating.md", "phase-6-documentation.md"],
    6: ["none"],
}
FORBIDDEN = [
    "nextStepFile",
    "tech spec",
    "CRITICAL STEP COMPLETION NOTE",
    "Menu Handling Logic",
    "EXECUTION RULES",
]
INTERACTIVE_ENDINGS = {
    0: r"New session / Continue",
    1: r"New session \(recommended\)",
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


def parse_routing(line):
    tokens = line.strip().split()
    if not tokens or tokens[0] != "RECIPE":
        return None
    pairs = []
    for token in tokens[1:]:
        if "=" not in token:
            return None
        pairs.append(tuple(token.split("=", 1)))
    return pairs


def routing_lines(path):
    if path is None or not path.exists():
        return []
    return [line for line in path.read_text().splitlines() if line.startswith("RECIPE ")]


# --- T1: one dialect for the routing line ---------------------------------

check("contract-exists", CONTRACT.exists(), f"{CONTRACT} missing")

if CONTRACT.exists():
    contract_text = CONTRACT.read_text()
    grammar = [parse_routing(line) for line in routing_lines(CONTRACT)]
    grammar = [line for line in grammar if line]
    keys_ok = grammar and all(
        [k for k, _ in line][: len(ROUTING_KEYS)] == ROUTING_KEYS for line in grammar
    )
    check("contract-declares-grammar", keys_ok, "key order phase/status/next/card")
    missing = [s for s in STATUSES if s not in contract_text]
    check("contract-declares-statuses", not missing, f"undocumented: {missing}")

ok, detail = True, []
for number, token in HEADLESS.items():
    path = phase_path(number)
    lines = routing_lines(path)
    if not lines:
        ok, detail = False, detail + [f"phase-{number}: no routing line"]
        continue
    for line in lines:
        pairs = parse_routing(line)
        if pairs is None:
            ok, detail = False, detail + [f"phase-{number}: unparseable {line!r}"]
            continue
        keys = [k for k, _ in pairs]
        if keys[: len(ROUTING_KEYS)] != ROUTING_KEYS or any(
            k not in ROUTING_KEYS + ["question"] for k in keys
        ):
            ok, detail = False, detail + [f"phase-{number}: key order {keys}"]
        values = dict(pairs)
        if values.get("phase") != token:
            ok, detail = False, detail + [f"phase-{number}: phase={values.get('phase')}"]
        if values.get("status") not in STATUSES:
            ok, detail = False, detail + [f"phase-{number}: status={values.get('status')}"]
        if values.get("status") in ("needs-input", "blocked") and "question" not in values:
            ok, detail = False, detail + [
                f"phase-{number}: {values.get('status')} with no question id"
            ]
        nxt = values.get("next")
        if nxt != "none" and not (PHASES / nxt).exists():
            ok, detail = False, detail + [f"phase-{number}: next={nxt} is not a phase file"]
check("phase-routing-lines", ok, "; ".join(detail))

ok, detail = True, []
for number, allowed in EXPECTED_NEXT.items():
    lines = routing_lines(phase_path(number))
    seen = [dict(parse_routing(line)).get("next") for line in lines if parse_routing(line)]
    if not any(value in allowed for value in seen):
        ok, detail = False, detail + [f"phase-{number}: no routing line with next in {allowed}"]
check("phase-routing-next", ok, "; ".join(detail))

# --- T2: the earlier contradictory footer stays gone ----------------------

offenders = []
for path in sorted(PHASES.glob("*.md")) + [SKILL_MD]:
    text = path.read_text()
    for needle in FORBIDDEN:
        if needle in text:
            offenders.append(f"{path.name}: {needle!r}")
check("stale-footer-gone", not offenders, "; ".join(offenders))

# --- T3: interactive endings survived -------------------------------------

offenders = []
for number, pattern in INTERACTIVE_ENDINGS.items():
    path = phase_path(number) if number else PHASES / "phase-0-start.md"
    if path is None or not re.search(pattern, path.read_text()):
        offenders.append(f"phase-{number}: /{pattern}/")
check("interactive-endings-intact", not offenders, "; ".join(offenders))

# --- headless surface exists where the card says it does ------------------

ok, detail = True, []
for number in HEADLESS:
    path = phase_path(number)
    if path is None or not re.search(r"^#+ .*headless", path.read_text(), re.M | re.I):
        ok, detail = False, detail + [f"phase-{number}: no Headless heading"]
check("headless-sections", ok, "; ".join(detail))

skill_text = SKILL_MD.read_text() if SKILL_MD.exists() else ""
check(
    "skill-points-at-contract",
    "--headless" in skill_text and "references/headless.md" in skill_text,
    "SKILL.md must name the flag and the contract file",
)

ok, detail = True, []
for number, needles in ((0, ["--headless", "runMode"]), (1, ["headless", "blocked"]), (2, ["headless", "blocked"])):
    text = (phase_path(number) or Path()).read_text() if phase_path(number) else ""
    for needle in needles:
        if needle not in text:
            ok, detail = False, detail + [f"phase-{number}: missing {needle!r}"]
check("headless-bailouts", ok, "; ".join(detail))

template_text = TEMPLATE.read_text() if TEMPLATE.exists() else ""
check(
    "template-carries-contract",
    "runMode:" in template_text and "## Open Questions" in template_text,
    "template needs runMode and ## Open Questions",
)

# --- T5: the README describes the repo that exists ------------------------

readme = README.read_text() if README.exists() else ""
names = sorted(p.parent.name for p in (REPO / "skills").glob("*/SKILL.md"))
absent = [name for name in names if name not in readme]
check("readme-names-every-skill", not absent, f"missing from README: {absent}")

match = re.search(r"\b([A-Za-z]+) Claude Code skills\b", readme)
if not match:
    check("readme-skill-count", False, "no '<Word> Claude Code skills' sentence")
else:
    counted = NUMBER_WORDS.get(match.group(1).lower())
    check("readme-skill-count", counted == len(names), f"README says {match.group(1)}, repo has {len(names)}")

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
