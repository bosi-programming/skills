---
name: ship-pr
description: >-
  Commit, push, and open a GitHub PR using the repo's own PR template — the full
  ship workflow. Use this WHENEVER the user wants to turn working-tree changes
  into a pull request, even if they only say part of it: "commit, push and open
  a PR", "open a PR following the template", "commit the changes and create a
  PR", "ship this", "one commit per fix then open a PR", "change the PR
  description to follow the template", or "create PRs for these changes"
  (multi-repo). Handles a folder of several repos, Conventional Commit messages
  with verbose bodies, ticket-key derivation from the branch name, per-repo PR
  templates (including a revert template), and fills the PR body from the diff
  and the ticket. Do NOT use this for writing a PR description in isolation
  without committing, or for posting an existing PR to chat.
---

# Ship PR

Turn working-tree changes into one or more pull requests. The user reaches for
this when the coding is done and they want it shipped, so do the mechanical
git and `gh` work correctly and fill the PR template thoughtfully.

## Settings

Read these keys as `../setup/references/config.md` describes:

- `ship-pr.titleFormat`, default `type(scope): subject [KEY]`. The shape of
  every commit header and PR title.
- `ship-pr.approvalGate`, default `true`. Pause for approval before any push or
  PR.
- `ship-pr.draft`, default `false`. Open PRs as drafts.
- `ship-pr.validateCommands`, default `[]`. Commands run from each repo's root
  before its commits, such as lint or tests.
- `ship-pr.trackerServer`, default `''`. MCP server that reads tickets.

A request that says "ask me first" or "just push it" overrides
`ship-pr.approvalGate`. A request that says "draft" overrides `ship-pr.draft`.
The `## ship-pr` section of the settings file is guidance on top of these rules.

## The contract that matters

Pushing a branch and opening a PR are outward-facing and awkward to undo. When
`ship-pr.approvalGate` is `true`, pause for approval after building the plan and
before any `git push` or `gh pr create`. When it is `false`, treat the push and
the PR as approved.

Everything before that point (inspecting, staging, committing locally) is
reversible and needs no gate. Do not ask permission to start: the user already
asked you to ship.

## Step 1 — Detect what there is to ship

Run the bundled detector from the user's current location. It is a shell
command, so it runs from the repository under work, and `$SKILL_DIR` is this
skill's folder:

```bash
bash "$SKILL_DIR/scripts/detect_context.sh"
```

It prints one JSON line per git repo, for the current folder and each git repo
one level below it, with: `path`, `branch`, derived `ticket`, GitHub `slug`,
`default_branch`, `local_changes`, `unpushed`, and available `templates`.

Decide scope from the output:

- Ship **only repos with `local_changes: true`** (or `unpushed: true` if the
  user already committed and just wants the PR). Skip a clean repo silently;
  never open an empty PR.
- If several repos have changes, produce **one independent PR per repo**, each
  with its own commits and its own repo's template. Name the coupling in each
  checklist, such as which PR must merge first.
- If `branch` is empty (detached HEAD) or equals `default_branch`, create
  `feature/<ticket-lowercased>` before committing. Never commit onto the
  default branch.
- If `ticket` looks wrong or empty, ask the user for the key rather than
  guessing. It goes in every commit and the PR title.

## Step 2 — Understand the change and pull ticket context

Read the diff per repo (`git -C <path> diff`, plus `git -C <path> diff --cached`
and untracked files) so commit messages and the PR body describe what changed,
not what you assume.

If `ship-pr.trackerServer` is set, load the ticket for the derived key from that
server to ground the PR's problem section in the real requirement. If it is
empty, the server is missing, or the ticket cannot be found, describe the
problem from the diff and say so in the plan. Do not invent a backstory.

## Step 3 — Plan the commits

Group the diff into **separate Conventional Commits by stage**, and emit only
the stages that have changes. Do not manufacture a `docs` or `test` commit when
the diff has none.

| Stage prefix | Holds |
|---|---|
| `chore(types)` | interfaces, types, validation schemas |
| `test(fixtures)` | mock data, factories, fixtures |
| `feat(shell)` / `feat(ui)` | structural components, no logic |
| `feat(logic)` / `feat(<scope>)` | business logic, hooks, state, API integration |
| `docs(comments)` | doc comments on touched files |
| `test(unit)` | unit, integration and e2e tests |

If the change is one cohesive thing, one commit is fine. If the user said "one
commit per fix", group by fix instead of by stage.

Each commit message follows `./references/conventions.md`: a header in the
`ship-pr.titleFormat` shape and a verbose body of context, trade-offs and
reasoning, with a `Resolves:` and `See-also:` footer. Read it now.

The `KEY` in the header is always the **current work item**, the ticket this
branch exists to deliver, derived in Step 1 from the branch name. When the
change references *another* ticket, most often a revert, that key goes in the
body, not the header. If the branch carries no key of its own and the only
ticket in play is the one being reverted, say so and confirm with the user
before tagging the header with it.

## Step 4 — Build the PR title and body

**Title:** the same shape as the lead commit header.

**Body:** start from the repo's template, then fill every prose section from the
diff and ticket, and tick the checklist items you can verify:

- Pick the template per repo: `.github/pull_request_template/default.md` if
  present, else `.github/pull_request_template.md`. For a **revert-only**
  change, use `.github/pull_request_template/revert.md` when the repo has one.
- Fill each prose section with real content. Replace placeholder hints; do not
  leave the template's `_describe..._` lines in.
- Tick a box only when the diff proves it. If you cannot verify an item, leave
  it unchecked and add a one-line "didn't check X because…" under the
  checklist.
- Leave design-link or video lines empty unless the user gave links.

## Step 5 — Validate, then present the plan

For each repo, run every command in `ship-pr.validateCommands` from its root
before the first commit. If one fails, stop and report it; do not commit.

When `ship-pr.approvalGate` is `true`, show the user, per repo:

1. The branch, and whether you will create it.
2. Each planned commit message, header and body.
3. The PR title and the fully rendered PR body.

Then ask for approval to push and open. Run no `git push` or `gh pr create`
until they say go. When it is `false`, go straight to Step 6.

## Step 6 — Execute

For each repo in scope, run each of these as its own Bash call, so a timeout
never loses the message file:

1. Create the branch, unless you are already on it:
   `git -C <path> switch -c feature/<ticket-lowercased>`.
2. Stage the paths of one planned commit: `git -C <path> add <paths>`.
3. Write that commit's message to a temp file with the file-writing tool.
4. Commit: `git -C <path> commit -F <message-file>`.
5. Repeat 2 to 4 for each planned commit.
6. Push: `git -C <path> push -u origin <branch>`.
7. Write the PR body to a temp file, then open the PR:

```bash
gh pr create --repo <slug> --base <default_branch> \
  --title "<title>" --body-file <body-file>
```

Add `--draft` when `ship-pr.draft` is `true`.

Notes that save grief:

- Use `--body-file`; inline `--body` mangles multi-line markdown and checklists.
- If a PR already exists for the branch (`gh pr view --repo <slug>` succeeds),
  do not create a second one. Push the new commits and, if the user asked to fix
  the description, run `gh pr edit --body-file`.
- After each PR, report the URL. End with one line listing every PR opened.

## Guardrails

- Never open stacked PRs. Ship one PR per repo, and start the next change only
  after the previous PR merged or the user says otherwise.
- Never `git add -A` across a repo you do not understand. Stage the paths that
  belong to each commit so the split is real.
- If tests or lint are visibly broken in the diff, say so in the plan. Shipping
  is the user's call, but they should see it before approving.
