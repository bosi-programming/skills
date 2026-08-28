#!/usr/bin/env bash
# Detect which repos under the current location have work to ship.
# Emits one JSON object per candidate repo to stdout (JSON Lines).
#
# Usage: detect_context.sh [base_dir]   (base_dir defaults to $PWD)
#
# For each git repo it reports: path, branch, derived ticket key, GitHub
# "owner/name" slug, default branch, whether there are local changes,
# whether there are commits not yet on the remote tracking branch, and the
# available PR template paths. The skill uses this to decide what to commit
# and which template(s) to fill.

set -euo pipefail

base="${1:-$PWD}"

json_escape() { printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'; }

derive_ticket() {
  # feature/TICK-000 -> TICK-000 ; falls back to the worktree dir name
  local branch="$1" repo_path="$2" key=""
  key=$(printf '%s' "$branch" | sed -E 's#^[a-z]+/##; s/-+$//' | tr 'a-z' 'A-Z')
  if printf '%s' "$key" | grep -qiE '^[A-Z]+-[0-9]+$'; then
    printf '%s' "$key"; return
  fi
  # try the ticket worktree dir: .../tickets/<TICKET-ID>/{apps,services}
  printf '%s' "$repo_path" | grep -oE 'tickets/[^/]+' | head -1 | sed 's#tickets/##' | tr 'a-z' 'A-Z'
}

inspect_repo() {
  local dir="$1"
  git -C "$dir" rev-parse --git-dir >/dev/null 2>&1 || return 0

  local branch default_branch slug ticket changes unpushed templates upstream
  branch=$(git -C "$dir" branch --show-current 2>/dev/null || echo "")
  slug=$(git -C "$dir" remote get-url origin 2>/dev/null \
    | sed -E 's#^git@github.com:##; s#^https://github.com/##; s/\.git$//' || echo "")
  default_branch=$(git -C "$dir" symbolic-ref --quiet refs/remotes/origin/HEAD 2>/dev/null \
    | sed 's#refs/remotes/origin/##' || true)
  [ -z "$default_branch" ] && default_branch="main"
  ticket=$(derive_ticket "$branch" "$dir")

  if [ -n "$(git -C "$dir" status --porcelain 2>/dev/null)" ]; then changes="true"; else changes="false"; fi

  upstream=$(git -C "$dir" rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || echo "")
  if [ -n "$upstream" ]; then
    if [ "$(git -C "$dir" rev-list --count "${upstream}..HEAD" 2>/dev/null || echo 0)" -gt 0 ]; then
      unpushed="true"; else unpushed="false"; fi
  else
    unpushed="no-upstream"
  fi

  templates=""
  for t in \
    "$dir/.github/pull_request_template.md" \
    "$dir/.github/PULL_REQUEST_TEMPLATE.md" \
    "$dir/.github/pull_request_template/default.md" \
    "$dir/.github/pull_request_template/revert.md"; do
    [ -f "$t" ] && templates="${templates}${templates:+,}$t"
  done

  printf '{"path":"%s","branch":"%s","ticket":"%s","slug":"%s","default_branch":"%s","local_changes":%s,"unpushed":"%s","templates":"%s"}\n' \
    "$(json_escape "$dir")" "$(json_escape "$branch")" "$(json_escape "$ticket")" \
    "$(json_escape "$slug")" "$(json_escape "$default_branch")" \
    "$changes" "$unpushed" "$(json_escape "$templates")"
}

# Candidate repos: the base dir itself, plus apps/ and services/ worktrees.
inspect_repo "$base"
for sub in apps services; do
  [ -d "$base/$sub" ] && inspect_repo "$base/$sub"
done
