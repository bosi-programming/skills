#!/usr/bin/env python3
"""Prints a random sample of classified replies so a person can check the labels.

The labels Suite B leans on are assigned by a model. This prints the finding, the
engineer's reply and the verdict side by side, with a fixed seed so the same sample
comes back every time and a disagreement can be recorded against it.
"""

import argparse
import json
import pathlib
import random
import textwrap

LOCAL = pathlib.Path(__file__).resolve().parents[1] / ".local" / "macroscope"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", type=int, default=10)
    ap.add_argument("--seed", type=int, default=11)
    args = ap.parse_args()

    data = json.loads((LOCAL / "findings.json").read_text())
    rows = [
        (r["repo"], r["pr"], f)
        for r in data for f in r["findings"]
        if f["replies"] and str(f.get("label_source", "")).startswith("model:")
    ]
    random.seed(args.seed)
    sample = random.sample(rows, min(args.n, len(rows)))

    for i, (repo, pr, f) in enumerate(sample, 1):
        body = " ".join((f.get("body") or "").split())
        # Macroscope appends a collapsed prompt block; the finding is the part above it.
        body = body.split("<details>")[0]
        reply = " ".join(
            " ".join((c["body"] or "").split()) for c in f["replies"]
        ).split("<!--")[0]
        print(f"\n{'=' * 78}")
        print(f"{i}. {repo}#{pr}   label: {f['label']}")
        print("-" * 78)
        print("FINDING:")
        print(textwrap.fill(body[:600], 76, initial_indent="  ", subsequent_indent="  "))
        print("REPLY:")
        print(textwrap.fill(reply[:600], 76, initial_indent="  ", subsequent_indent="  "))

    print(f"\n{'=' * 78}")
    print(f"{len(sample)} of {len(rows)} model-assigned labels shown (seed {args.seed}).")


if __name__ == "__main__":
    main()
