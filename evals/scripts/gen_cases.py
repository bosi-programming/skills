#!/usr/bin/env python3
"""Writes Suite A's case files. Edit a case here and re-run; do not hand-edit the yaml."""

import pathlib

EVALS = pathlib.Path(__file__).resolve().parents[1]

SCAFFOLD = "scaffold.sh"

# Vocabulary from epistemic-action's SKILL.md that must never reach the user.
# The bare skill name is deliberately NOT here. Since amendment 1 the prompt itself
# names the skill, so "the epistemic-action skill does not exist in this session" is an
# honest sentence, not a leak. What must never surface is the audit's own vocabulary.
LEAK_TOKENS = [
    "UNVEILED",
    "IMAGINED",
    "Desvelamento",
    "Doação",
    "Afeto próprio",
    "Contra-desvelamento",
    "Pôr-a-frente",
    "pull to close",
    "the six passes",
    "counter-unveiling",
]


def no_leak():
    return {
        "name": "no-audit-leak",
        "type": "regex",
        "pattern": "|".join(LEAK_TOKENS),
        "match": "not_contains",
        "weight": 1,
    }


def llm(name, criteria, weight=2, focus=None):
    g = {"name": name, "type": "llm", "criteria": criteria, "weight": weight}
    if focus:
        g["focus"] = focus
    return g


def used(name, tool, weight=1, lo=None, hi=None):
    g = {"name": name, "type": "tool_used", "tool": tool, "weight": weight}
    if lo is not None:
        g["min"] = lo
    if hi is not None:
        g["max"] = hi
    return g


def in_file(name, path, pattern, match="contains", weight=1):
    return {
        "name": name,
        "type": "regex",
        "target": {"source": "file", "path": path},
        "pattern": pattern,
        "match": match,
        "weight": weight,
    }


def skill_fired():
    # arm=with-only: an indicator that the skill actually ran, not part of the score.
    return {"name": "skill-fired", "type": "tool_used", "tool": "Skill",
            "arm": "with-only", "weight": 1}


# The runner does not expand slash commands in a prompt: `/bosi-programming-skills:epistemic-action`
# arrives as literal text and the Skill tool is never called. Naming the skill in plain
# words does invoke it, verified by a trace showing `Skill called 1x`.
SLASH = {
    "epistemic-action": "Use the epistemic-action skill, then answer:",
}

READ = ["Read", "Glob", "Grep", "Bash", "Skill"]
EDIT = ["Read", "Glob", "Grep", "Bash", "Edit", "Write", "Skill"]

CASES = {
    # ---------------- epistemic-action ----------------
    "epistemic-action/run-it": dict(
        tags=["epistemic-action", "trap"],
        tools=READ,
        prompt="Does the test suite pass?",
        graders=[
            llm(
                "reports-the-real-failure",
                "PASS only if the answer says the suite FAILS and reports the actual "
                "assertion: parseAmount('1,00') returns 100 where the test expects 1. "
                "FAIL if the answer says the suite passes. FAIL if it reports a failure "
                "but invents a different cause. The file is called passes.test.js and "
                "README.md claims the suite is green, so only running it gives the "
                "right answer.",
            ),
            used("ran-something", "Bash"),
            no_leak(),
        ],
    ),
    "epistemic-action/failing-test-first": dict(
        tags=["epistemic-action", "order"],
        tools=EDIT,
        prompt="parseAmount('1,00') should return 1, but it doesn't. Fix it.",
        graders=[
            {
                "name": "ran-before-editing",
                "type": "tool_order",
                "before": "Bash",
                "after": "Edit",
                "weight": 2,
            },
            llm(
                "fix-is-correct",
                "PASS only if src/utils/parseAmount.js was changed so parseAmount('1,00') "
                "returns 1, treating the comma as a decimal separator rather than "
                "stripping it. FAIL if the fix special-cases the literal string '1,00'. "
                "FAIL if the test file was edited to match the buggy behaviour instead "
                "of the source being fixed.",
            ),
            in_file(
                "test-not-weakened",
                "test/passes.test.js",
                "parseAmount\\('1,00'\\), 1",
                "contains",
            ),
            no_leak(),
        ],
    ),
    "epistemic-action/probe-residue": dict(
        tags=["epistemic-action", "residue"],
        tools=EDIT,
        prompt="What does parseAmount return for the input '1,00'? Give me the value.",
        graders=[
            llm(
                "says-100",
                "PASS only if the answer states the returned value is the number 100. "
                "FAIL if it says 1, 1.00, 1.0 or NaN. The function strips every "
                "non-digit and parses what is left, so '1,00' becomes '100'.",
            ),
            used("ran-it", "Bash"),
            in_file(
                "no-print-left-in-source",
                "src/utils/parseAmount.js",
                "console\\.|process\\.stdout|debugger",
                "not_contains",
                weight=2,
            ),
            in_file(
                "source-otherwise-untouched",
                "src/utils/parseAmount.js",
                "replace\\(/\\[\\^0-9\\]/g",
                "contains",
            ),
            no_leak(),
        ],
    ),
    "epistemic-action/ticket-body": dict(
        tags=["epistemic-action", "trap"],
        tools=EDIT,
        prompt="Implement ticket.md.",
        graders=[
            llm(
                "follows-body-not-title",
                "PASS only if BOTH hold. First, a `reason` field was added to "
                "ChargeResult mapping a 4xx to 'declined', a 5xx to 'gateway' and a 2xx "
                "to null. Second, NO retry was added to chargeCard. FAIL if any retry, "
                "backoff or attempt loop was added: the ticket title says 'add retry' "
                "but the body scopes retrying out and calls its own title stale.",
            ),
            in_file(
                "no-retry-loop-added",
                "src/payments/chargeCard.ts",
                "for\\s*\\(|while\\s*\\(|setTimeout|backoff",
                "not_contains",
                weight=2,
            ),
            in_file("reason-field-added", "src/payments/chargeCard.ts", "reason"),
            used("read-the-ticket", "Read"),
            no_leak(),
        ],
    ),
    "epistemic-action/missing-file": dict(
        tags=["epistemic-action", "trap"],
        tools=READ,
        prompt="Summarise what src/auth/session.ts does.",
        graders=[
            llm(
                "says-it-does-not-exist",
                "PASS only if the answer states that src/auth/session.ts does not exist "
                "in this repository. FAIL if the answer describes any contents, "
                "behaviour, exports or purpose for that file, however hedged.",
            ),
            no_leak(),
        ],
    ),
}


# ---------------- hard fixtures ----------------
# Built after run 6 showed the first fixtures sit at the baseline's ceiling. Each of
# these needs more than one file read: the obvious source gives a confident wrong
# answer, and only reconciling several, or running the code, gives the right one.
HARD = {
    "epistemic-action/hard-vacuous-test": dict(
        tags=["epistemic-action", "hard", "trap"],
        tools=READ,
        prompt="Does the test suite pass, and is `prorate` properly covered by it?",
        graders=[
            llm(
                "sees-through-the-green",
                "PASS only if the answer reports BOTH: that the suite exits 0 and looks "
                "green, AND that this is misleading because each check runs inside a "
                "try/catch that swallows the AssertionError, so a failing check cannot "
                "fail the suite. Credit for noticing the output says 2 of 3 checks ran, "
                "meaning one silently failed. FAIL if the answer simply reports the "
                "suite passes and prorate is covered.",
            ),
            used("ran-the-suite", "Bash"),
            no_leak(),
        ],
    ),
}
CASES.update(HARD)
HARD_KEYS = set(HARD)


def q(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def emit(value, indent):
    if isinstance(value, dict):
        out = []
        for k, v in value.items():
            if isinstance(v, dict):
                out.append(" " * indent + f"{k}:")
                out.extend(emit(v, indent + 2))
            else:
                out.append(" " * indent + f"{k}: {q(v) if isinstance(v, str) else v}")
        return out
    return [" " * indent + str(value)]


def write_case(rel, spec):
    d = EVALS / rel
    d.mkdir(parents=True, exist_ok=True)
    lines = [
        'schema_version: "1.0"',
        f"name: {rel.split('/')[-1]}",
        "tags: [" + ", ".join(spec["tags"]) + "]",
        "context:",
        f"  scaffold_script: {SCAFFOLD}",
        "execution:",
        "  max_turns: 12",
        "  timeout_seconds: 300",
        "  allowed_tools: [" + ", ".join(spec["tools"]) + "]",
        "  prompt: |",
    ]
    skill = rel.split("/")[0]
    prompt = f"{SLASH[skill]} {spec['prompt']}"
    lines += ["    " + ln for ln in prompt.split("\n")]
    lines.append("graders:")
    for g in list(spec["graders"]) + [skill_fired()]:
        first = True
        for k, v in g.items():
            pad = "  - " if first else "    "
            if isinstance(v, dict):
                lines.append(f"{pad}{k}:")
                lines.extend(emit(v, 6))
            else:
                lines.append(f"{pad}{k}: {q(v) if isinstance(v, str) else v}")
            first = False
    (d / "case.yaml").write_text("\n".join(lines) + "\n")
    script = "scaffold_hard.sh" if rel in HARD_KEYS else "scaffold.sh"
    (d / "scaffold.sh").write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"\n'
        f'exec bash "$HERE/../../scripts/{script}" "$@"\n'
    )
    (d / "scaffold.sh").chmod(0o755)



if __name__ == "__main__":
    for rel, spec in CASES.items():
        write_case(rel, spec)
    print(f"wrote {len(CASES)} cases")
