#!/usr/bin/env python3
import json
import os
import re
import signal
import subprocess
import sys

USAGE = "usage: prove-red.py <spec.json>"
DEFAULT_TIMEOUT = 300
RESULT = re.compile(r"^\s*(not )?ok \d+(.*)$")
DESCRIPTION = re.compile(r"^\s*-\s?(.*)$")
DIRECTIVE = re.compile(r"\s*#\s*(skip|todo)\b.*$", re.IGNORECASE)
SUITE = re.compile(r"^\s*type:\s*['\"]?suite['\"]?\s*$")


class Refused(Exception):
    pass


def parse_tap(output):
    lines = output.splitlines()
    results = []
    index = 0
    while index < len(lines):
        match = RESULT.match(lines[index])
        index += 1
        if not match:
            continue
        rest = match.group(2)
        directive = DIRECTIVE.search(rest) is not None
        described = DESCRIPTION.match(DIRECTIVE.sub("", rest))
        name = described.group(1).strip() if described else ""
        suite = False
        if index < len(lines) and lines[index].strip() == "---":
            cursor = index + 1
            while cursor < len(lines) and lines[cursor].strip() != "...":
                if SUITE.match(lines[cursor]):
                    suite = True
                cursor += 1
        if directive or suite:
            continue
        results.append({"name": name, "ok": match.group(1) is None})
    return results


def git(repo, *args):
    return subprocess.run(
        ["git", "-C", repo, *args],
        capture_output=True,
        text=True,
    )


def load_spec(path):
    try:
        with open(path, encoding="utf-8") as handle:
            spec = json.load(handle)
    except (OSError, ValueError) as error:
        raise Refused(f"cannot read spec {path}: {error}")
    if not isinstance(spec, dict):
        raise Refused("spec must be a JSON object")
    for key in ("repo", "base", "tests"):
        if key not in spec:
            raise Refused(f"spec is missing {key}")
    if not isinstance(spec["repo"], str) or not isinstance(spec["base"], str):
        raise Refused("repo and base must be strings")
    if not isinstance(spec["tests"], list):
        raise Refused("tests must be a list")
    for test in spec["tests"]:
        if (
            not isinstance(test, dict)
            or not isinstance(test.get("path"), str)
            or not isinstance(test.get("command"), str)
        ):
            raise Refused("each test needs a path and a command")
    exclude = spec.get("exclude", [])
    if not isinstance(exclude, list) or not all(isinstance(item, str) for item in exclude):
        raise Refused("exclude must be a list of paths")
    timeout = spec.get("timeout", DEFAULT_TIMEOUT)
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or timeout <= 0:
        raise Refused("timeout must be a positive number")
    return spec["repo"], spec["base"], spec["tests"], exclude, timeout


def exists_at(repo, rev, path):
    return git(repo, "cat-file", "-e", f"{rev}:{path}").returncode == 0


def dirty_paths(repo, paths):
    if not paths:
        return []
    out = git(repo, "status", "--porcelain", "--", *paths).stdout
    return [line for line in out.splitlines() if line.strip()]


def check_and_collect(repo, base, tests, exclude):
    if not os.path.isdir(repo):
        raise Refused(f"repo {repo} is not a directory")
    if git(repo, "rev-parse", "--git-dir").returncode != 0:
        raise Refused(f"{repo} is not a git repo")
    if git(repo, "merge-base", "--is-ancestor", base, "HEAD").returncode != 0:
        raise Refused(f"base {base} is not an ancestor of HEAD")
    for test in tests:
        if not exists_at(repo, "HEAD", test["path"]):
            raise Refused(f"test path {test['path']} is missing at HEAD")
    diff = git(repo, "diff", "--name-only", base, "HEAD")
    if diff.returncode != 0:
        raise Refused(f"git diff failed: {diff.stderr.strip()}")
    skip = {test["path"] for test in tests} | set(exclude)
    code = sorted(path for path in diff.stdout.splitlines() if path and path not in skip)
    dirty = dirty_paths(repo, code)
    if dirty:
        raise Refused("uncommitted change on a code path: " + "; ".join(dirty))
    head = git(repo, "rev-parse", "HEAD").stdout.strip()
    return code, head


def remove(repo, path):
    try:
        os.remove(os.path.join(repo, path))
    except FileNotFoundError:
        pass


def revert(repo, base, code):
    for path in code:
        if exists_at(repo, base, path):
            git(repo, "checkout", base, "--", path)
        else:
            remove(repo, path)


def restore(repo, code):
    for path in code:
        try:
            if exists_at(repo, "HEAD", path):
                git(repo, "checkout", "HEAD", "--", path)
            else:
                git(repo, "rm", "-q", "-f", "--cached", "--ignore-unmatch", "--", path)
                remove(repo, path)
        except OSError:
            pass


def run_command(repo, command, timeout):
    process = subprocess.Popen(
        command,
        shell=True,
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        start_new_session=True,
    )
    try:
        output, _ = process.communicate(timeout=timeout)
        return process.returncode, False, output
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except OSError:
            pass
        try:
            output, _ = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            output = ""
        return None, True, output or ""


def prove(repo, base, tests, code, timeout):
    results = []
    weak = []
    for test in tests:
        exit_code, timed_out, output = run_command(repo, test["command"], timeout)
        verdict = "red" if timed_out or exit_code != 0 else "weak"
        entries = [
            {"name": item["name"], "verdict": "weak" if item["ok"] else "red"}
            for item in parse_tap(output)
        ]
        results.append(
            {
                "path": test["path"],
                "command": test["command"],
                "exit": exit_code,
                "timedOut": timed_out,
                "verdict": verdict,
                "tests": entries,
            }
        )
        if entries:
            weak.extend(f"{test['path']} :: {item['name']}" for item in entries if item["verdict"] == "weak")
        elif verdict == "weak":
            weak.append(test["path"])
    return results, weak


def main(argv):
    if len(argv) != 2:
        print(json.dumps({"error": USAGE}))
        return 2
    try:
        repo, base, tests, exclude, timeout = load_spec(argv[1])
        code, head = check_and_collect(repo, base, tests, exclude)
    except Refused as error:
        print(json.dumps({"error": str(error)}))
        return 2
    results = []
    weak = []
    try:
        revert(repo, base, code)
        results, weak = prove(repo, base, tests, code, timeout)
    finally:
        restore(repo, code)
    left = dirty_paths(repo, code)
    restored = not left
    error = None
    if not restored:
        error = "code paths still differ from HEAD: " + ", ".join(
            line[3:] if len(line) > 3 else line for line in left
        )
    print(
        json.dumps(
            {
                "repo": repo,
                "base": base,
                "head": head,
                "code": code,
                "results": results,
                "weak": weak,
                "restored": restored,
                "error": error,
            },
            indent=2,
        )
    )
    return 0 if restored else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
