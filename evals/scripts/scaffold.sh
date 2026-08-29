#!/usr/bin/env bash
# Copies the trap fixture into the case sandbox and makes it a real git repo, so a
# residue check has something to compare against. Run from the sandbox cwd with no
# arguments; each case dir holds a shim that calls this.
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/../fixtures/trap-repo" && pwd)"
DEST="${1:-.}"

cp -R "$SRC/." "$DEST/"

cd "$DEST"
rm -rf .git
git init -q
git config user.email eval@example.com
git config user.name eval
git add -A
git commit -qm "checkout at 0.4.1"
