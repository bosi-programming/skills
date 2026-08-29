#!/usr/bin/env python3
"""Checks whether a review's findings cite places that exist.

This is the sharpest test in the suite and it needs no judge. `objectum` says
nothing ships carrying a claim still marked IMAGINED. A finding that points at
`foo.ts:470` in a file of 200 lines is exactly such a claim, and arithmetic settles
it.

A citation is counted valid when the file exists at the PR head and the line number
falls inside it. When the finding also quotes code, the quote must appear near the
cited line; `--context` sets how near.

Verify the checker against Macroscope's own findings before trusting it on ours. If
it cannot confirm a citation known to be good, it cannot judge anything.
"""

import argparse
import json
import pathlib
import re
import subprocess
import sys

# `path/to/file.ts:470`, with or without backticks, optionally :col
CITATION = re.compile(r"`?([\w./@-]+\.[A-Za-z0-9]+):(\d+)(?::\d+)?`?")
FENCE = re.compile(r"```([a-zA-Z0-9+#-]*)\n(.*?)```", re.S)
# Only a fence tagged with a code language is a quote of the file. Reviewers also
# fence prose — Macroscope ships an untagged "AI Prompt" block restating the finding
# in English — and holding that against the source would fail good citations.
CODE_LANGS = {
    "ts", "tsx", "js", "jsx", "typescript", "javascript", "py", "python", "go",
    "rb", "ruby", "java", "kt", "rs", "c", "cpp", "cs", "php", "sh", "bash",
    "sql", "json", "yaml", "yml", "html", "css", "scss", "diff", "patch",
}


_tree_cache = {}


def tree(repo_dir, sha):
    if sha not in _tree_cache:
        r = subprocess.run(
            ["git", "-C", str(repo_dir), "ls-tree", "-r", "--name-only", sha],
            capture_output=True, text=True,
        )
        _tree_cache[sha] = r.stdout.splitlines() if r.returncode == 0 else []
    return _tree_cache[sha]


def resolve(repo_dir, sha, path):
    """A cited path may be truncated for display. Accept it if exactly one file at
    the head ends with it; an ambiguous suffix is not a citation anyone could follow."""
    files = tree(repo_dir, sha)
    if path in files:
        return path
    matches = [f for f in files if f.endswith("/" + path.lstrip("/"))]
    return matches[0] if len(matches) == 1 else None


def file_at(repo_dir, sha, path):
    real = resolve(repo_dir, sha, path)
    if real is None:
        return None
    r = subprocess.run(
        ["git", "-C", str(repo_dir), "show", f"{sha}:{real}"],
        capture_output=True, text=True,
    )
    return r.stdout.splitlines() if r.returncode == 0 else None


def citations(body):
    seen, out = set(), []
    for m in CITATION.finditer(body):
        key = (m.group(1), int(m.group(2)))
        if key not in seen:
            seen.add(key)
            out.append(key)
    return out


def quoted(body):
    return [
        ln.strip()
        for lang, block in FENCE.findall(body)
        if lang.lower() in CODE_LANGS
        for ln in block.splitlines()
        if len(ln.strip()) > 12
    ]


def check(finding, repo_dir, sha, context):
    body = finding.get("body") or ""
    # A review-comment finding carries its anchor in structured fields; the path
    # printed in the body is often truncated for display. Prefer the real one.
    if finding.get("path") and finding.get("line"):
        cited = [(finding["path"], int(finding["line"]))]
    else:
        cited = citations(body)
    results = []
    for path, line in cited:
        lines = file_at(repo_dir, sha, path)
        if lines is None:
            results.append({"path": path, "line": line, "ok": False,
                            "why": "file not found at head"})
            continue
        if not (1 <= line <= len(lines)):
            results.append({"path": path, "line": line, "ok": False,
                            "why": f"line {line} outside file of {len(lines)}"})
            continue
        quotes = quoted(body)
        if quotes:
            lo, hi = max(0, line - 1 - context), min(len(lines), line + context)
            window = "\n".join(lines[lo:hi])
            if not any(q in window for q in quotes):
                results.append({"path": path, "line": line, "ok": False,
                                "why": "quoted code absent near the cited line"})
                continue
        results.append({"path": path, "line": line, "ok": True, "why": None})
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("findings", help="JSON: [{repo, pr, head_sha, findings:[{body}]}]")
    ap.add_argument("--repo-dir", required=True, help="local clone or worktree")
    ap.add_argument("--context", type=int, default=6, help="lines of slack for a quote")
    ap.add_argument("--label", default="arm", help="name for this arm in the report")
    args = ap.parse_args()

    data = json.loads(pathlib.Path(args.findings).read_text())
    total = valid = uncited = 0
    failures = []

    for rec in data:
        sha = rec.get("head_sha")
        for f in rec.get("findings", []):
            rows = check(f, args.repo_dir, sha, args.context)
            if not rows:
                uncited += 1
                continue
            for row in rows:
                total += 1
                if row["ok"]:
                    valid += 1
                else:
                    failures.append({"repo": rec.get("repo"), "pr": rec.get("pr"), **row})

    rate = valid / total if total else 0.0
    print(f"arm: {args.label}")
    print(f"  citations checked : {total}")
    print(f"  valid             : {valid}")
    print(f"  citation validity : {rate:.3f}")
    print(f"  findings with no file:line at all : {uncited}")
    if failures:
        print("\n  bad citations:")
        for x in failures[:40]:
            print(f"    {x['repo']}#{x['pr']} {x['path']}:{x['line']} — {x['why']}")

    # Aggregate only. Paths and PR numbers stay out of anything published.
    print(json.dumps({"label": args.label, "checked": total, "valid": valid,
                      "validity": round(rate, 4), "uncited": uncited},
                     indent=2), file=sys.stderr)


if __name__ == "__main__":
    main()
