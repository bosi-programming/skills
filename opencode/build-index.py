#!/usr/bin/env python3
"""Write the skill index opencode's `skills.urls` fetches, or check it is current.

opencode reads a skill list from `<url>/index.json` and downloads every file of
every entry relative to `<url>/<name>/`, so the index has to name each file a
skill carries and carry a version that changes when those files do — otherwise a
published skill goes stale without saying so. This walks `skills/` and writes
`skills/index.json`, which is what
https://raw.githubusercontent.com/bosi-programming/skills/main/skills/index.json
serves. Offline, stdlib only. Exits non-zero under `--check` when the index no
longer matches the tree, and prints which skills drifted.
"""

import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SKILLS = REPO / "skills"
INDEX = SKILLS / "index.json"
SKILL_MD = "SKILL.md"


def skill_dirs():
    """Every directory under `skills/` that is a skill, in name order."""
    return sorted((d for d in SKILLS.iterdir() if (d / SKILL_MD).is_file()), key=lambda d: d.name)


def files_of(directory):
    """Every file the skill carries, SKILL.md first, then paths in name order."""
    relative = sorted(p.relative_to(directory).as_posix()
                      for p in directory.rglob("*") if p.is_file())
    return [SKILL_MD] + [path for path in relative if path != SKILL_MD]


def version_of(directory):
    """A short digest over the skill's paths and bytes, so any edit moves it."""
    digest = hashlib.sha256()
    for path in files_of(directory):
        digest.update(path.encode())
        digest.update(b"\0")
        digest.update((directory / path).read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()[:12]


def build():
    return {"skills": [
        {"name": directory.name, "files": files_of(directory), "version": version_of(directory)}
        for directory in skill_dirs()
    ]}


def write(index):
    INDEX.write_text(json.dumps(index, indent=2) + "\n")


def main():
    index = build()
    current = json.dumps(index, indent=2) + "\n"

    if "--check" not in sys.argv[1:]:
        write(index)
        print(f"wrote {INDEX.relative_to(REPO)}: {len(index['skills'])} skills")
        return 0

    if not INDEX.exists():
        print("FAIL  index-exists  skills/index.json is missing; run opencode/build-index.py")
        return 1
    if INDEX.read_text() == current:
        print(f"PASS  index-current  {len(index['skills'])} skills match skills/index.json")
        return 0

    served = {entry["name"]: entry for entry in json.loads(INDEX.read_text()).get("skills", [])}
    tree = {entry["name"]: entry for entry in index["skills"]}
    for name in sorted(set(served) | set(tree)):
        if name not in served:
            print(f"FAIL  index-current  {name} is in the tree but missing from the index")
        elif name not in tree:
            print(f"FAIL  index-current  {name} is in the index but not in the tree")
        elif served[name] != tree[name]:
            print(f"FAIL  index-current  {name} changed since the index was written")
    print("\nrun opencode/build-index.py to rewrite it")
    return 1


if __name__ == "__main__":
    sys.exit(main())
