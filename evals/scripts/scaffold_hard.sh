#!/usr/bin/env bash
# Copies the hard trap fixture into the case sandbox as a real git repo.
set -euo pipefail
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/../fixtures/trap-repo-hard" && pwd)"
DEST="${1:-.}"
cp -R "$SRC/." "$DEST/"
cd "$DEST"
rm -rf .git
git init -q
git config user.email eval@example.com
git config user.name eval
git add -A
git commit -qm "hard at 2.0.0"
