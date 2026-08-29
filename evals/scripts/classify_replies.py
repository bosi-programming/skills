#!/usr/bin/env python3
"""Classifies the human reply to each Macroscope finding.

The keyword heuristic in mine_macroscope.py was measurably wrong. On a six-reply
spot check it filed "Confirmed, this is a real gap" under needs_read, filed a
stale-review dismissal under needs_read, and filed a deferral ("second PR where the
full process will be validated") under confirmed. Roughly half the sample was wrong,
so keywords cannot carry Suite B's labels.

This asks a model instead, one reply at a time, for one of four verdicts. It writes
the verdict beside the raw reply text it was given, so a person can audit every call
without re-running anything. The labels remain model-assigned until someone does.
"""

import argparse
import json
import pathlib
import subprocess
import sys

PROMPT = """You are labelling one reply that a software engineer wrote underneath an \
automated code-review finding on a pull request.

Answer with exactly one word, nothing else:

confirmed      - the engineer agrees the finding is a real problem in this change.
                 This INCLUDES every reply saying they fixed it, removed it, resolved
                 it, or naming a commit that addresses it. A reply that reports the
                 flagged code is now gone is agreeing, not disputing.
false_positive - the engineer disputes the finding itself: it is wrong, it misreads the
                 code, it is by design, or the code it points at no longer exists
                 because the whole area was deleted or rebased away. Choose this only
                 when the engineer rejects the finding's validity, never when they
                 accept it and fix it.
deferred       - the engineer agrees it is real but declines to act now, or says it is
                 pre-existing rather than introduced here, or defers it to another PR
unclear        - the reply does not take a position on whether the finding is valid

The single most common mistake is filing a fix under false_positive. "Confirmed, this
is gone as of <sha>" is confirmed.

THE FINDING:
{finding}

THE ENGINEER'S REPLY:
{reply}

One word:"""

VALID = {"confirmed", "false_positive", "deferred", "unclear"}


def classify(finding_body, reply_text, model):
    prompt = PROMPT.format(
        finding=finding_body[:1500].strip(),
        reply=reply_text[:1500].strip(),
    )
    r = subprocess.run(
        ["claude", "-p", prompt, "--model", model],
        capture_output=True, text=True, timeout=180,
    )
    if r.returncode != 0:
        return "error", r.stderr.strip()[:200]
    word = r.stdout.strip().split()[-1].strip(".,'\"").lower() if r.stdout.strip() else ""
    return (word, None) if word in VALID else ("unclear", f"unparsed: {r.stdout.strip()[:80]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="claude-haiku-4-5-20251001")
    ap.add_argument("--limit", type=int, default=0, help="0 means all")
    args = ap.parse_args()

    path = pathlib.Path(__file__).resolve().parents[1] / ".local" / "macroscope" / "findings.json"
    data = json.loads(path.read_text())

    todo = [(r, f) for r in data for f in r["findings"] if f["replies"]]
    if args.limit:
        todo = todo[: args.limit]

    counts = {}
    for i, (rec, f) in enumerate(todo, 1):
        reply = "\n\n".join((c["body"] or "") for c in f["replies"])
        label, note = classify(f.get("body") or "", reply, args.model)
        f["label"] = label
        f["label_source"] = f"model:{args.model}"
        if note:
            f["label_note"] = note
        counts[label] = counts.get(label, 0) + 1
        print(f"  {i}/{len(todo)} {rec['repo']}#{rec['pr']} -> {label}", file=sys.stderr)

    path.write_text(json.dumps(data, indent=2))

    print("\nlabels:")
    for k, v in sorted(counts.items()):
        print(f"  {k}: {v}")
    print(f"\nlabelled {len(todo)} replies; raw text kept alongside each verdict")
    print("These are model-assigned. Read them before treating them as ground truth.")


if __name__ == "__main__":
    main()
