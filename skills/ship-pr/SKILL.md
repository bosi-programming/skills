---
name: ship-pr
description: >-
  Commit, push, and open a GitHub PR using the repo's .github template — the
  full ship workflow for Acme. Use this WHENEVER the user wants to turn
  working-tree changes into a pull request, even if they only say part of it:
  "commit, push and open a PR", "open a PR following the template on .github",
  "commit the changes and create a PR", "ship this", "one commit per fix then
  open a PR", "change the PR description to follow the template", or "create PRs
  for these changes" (multi-repo). Handles the worktree layout (apps +
  services), Conventional Commit messages with verbose bodies, ticket-key
  derivation, per-repo PR templates (including services' revert.md), and
  auto-fills the PR body from the diff and the Linear ticket. Do NOT use this
  for writing a PR description in isolation without committing (that's
  pr-description), or for posting an existing PR to Slack.
---

# Ship PR

Turn working-tree changes into one or more pull requests, following Acme's
conventions exactly. The user reaches for this when the coding is done and they
want it shipped — so the goal is to do the mechanical git/gh work correctly and
fill the PR template thoughtfully, while pausing once for approval before
anything leaves the machine.

## The contract that matters

Pushing a branch and opening a PR are outward-facing and awkward to undo, so
**this skill always pauses for approval after building the plan and before
running any `git push` or `gh pr create`.** Everything before that point
(inspecting, staging, even committing locally) is reversible and needs no
gate. Don't ask permission to start — the user already asked you to ship.

One earlier stop sits in front of that one: **Step 3 runs the code review and
waits for the user to say what to fix before anything is committed.**

## Step 1 — Detect what there is to ship

Run the bundled detector from the user's current location (a ticket dir, or a
standalone checkout like `partners`/`engineering-docs`):

```bash
bash "${CLAUDE_SKILL_DIR}/scripts/detect_context.sh"
```

It prints one JSON line per git repo with: `path`, `branch`, derived `ticket`,
GitHub `slug`, `default_branch`, `local_changes`, `unpushed`, and available
`templates`. A Acme ticket worktree usually surfaces two repos — `apps`
(frontend, `acme/apps`) and `services` (backend, `acme/core`).

Decide scope from the output:

- Ship **only repos with `local_changes: true`** (or `unpushed: true` if the
  user already committed and just wants the PR). If a repo is clean, skip it
  silently — don't open an empty PR.
- If both repos have changes, you'll produce **two independent PRs**, each with
  its own commits and its own repo's template. Mention the cross-repo coupling
  in each checklist ("can be deployed independent of changes in other
  services/applications").
- If `branch` is empty (detached HEAD) or equals `default_branch`, you're not on
  a feature branch yet — create `feature/<ticket-lowercased>` before committing
  (e.g. `feature/TICK-000`). Never commit straight onto `main`.
- If `ticket` looks wrong or empty, ask the user for the key rather than
  guessing — it goes in every commit and the PR title.

## Step 2 — Understand the change and pull ticket context

Read the diff per repo (`git -C <path> diff` for unstaged, plus `git -C <path>
diff --cached` and untracked files) so commit messages and the PR body describe
what actually changed, not what you assume.

Load the Linear ticket for the derived key via the `linear-server` MCP
(`get_issue`) to ground the PR's "what is the problem" section in the real
requirement and to confirm the ticket key. If the MCP isn't available or the
ticket can't be found, fall back to describing the problem from the diff and say
so in the plan rather than inventing a backstory.

## Step 3 — Review the change before you commit it

Run this repo's own code review over the change and let the user act on it.
Nothing gets committed until they have seen the page and said what to fix.

- **Invoke the `bosi-code-review` skill with the Skill tool**, once per repo in
  scope. Do not paraphrase it from memory and do not substitute your own read of
  the diff — the skill runs a Standards axis and a Spec axis as parallel
  sub-agents and gates both, which an inline read does not.
- Skill name: `bosi-code-review`. From a plugin install the sibling is
  namespaced, so use `bosi-programming-skills:bosi-code-review` and fall back to
  the bare name if that one is not listed.
- Fixed point: the repo's `default_branch` from Step 1 (`origin/main` on most
  Acme repos).
- Say in the same call that the change is **still in the working tree**, so the
  review has to diff `git diff <fixed-point>` plus `git diff --cached` and the
  untracked files, not `<fixed-point>...HEAD`. At this point HEAD carries none
  of the change.
- Pass the Linear ticket from Step 2 as the spec source, so the Spec axis has
  something to check the diff against.

When the page is built, give the user the `file://` URL and the per-axis
tallies, then **stop**. This is the earlier of the two gates:

1. Wait for the user to say what to fix. "Nothing" is a valid answer.
2. Fix only what they name. Don't fold in findings they passed over, and don't
   re-argue the ones they dropped.
3. Re-run the review only if they ask for it.

Then continue to Step 4. If fixes landed, re-read the diff first so the commit
plan describes the code you are shipping rather than the code you reviewed.

## Step 4 — Plan the commits (granular, per-stage)

Group the diff into **separate Conventional Commits by stage**, following the
user's breakdown protocol — but only emit the stages that actually have changes.
Don't manufacture a `docs` or `test` commit if the diff has none.

| Stage prefix | Holds |
|---|---|
| `chore(types)` | TS interfaces, types, validation schemas |
| `test(fixtures)` | mock data, factories, fixtures |
| `feat(shell)` / `feat(ui)` | structural components / boilerplate, no logic |
| `feat(logic)` / `feat(<scope>)` | business logic, hooks, state, API integration |
| `docs(comments)` | TSDoc/JSDoc on touched files |
| `test(unit)` | unit/integration/e2e tests |

If the change is one cohesive thing, a single commit is fine — don't split for
the sake of splitting. If the user said "one commit per fix," group by distinct
fix instead of by stage.

Each commit message follows the format in
`references/conventions.md` — a `type(scope): subject [TICKET-KEY]` header and a
verbose body explaining **context, trade-offs considered, and architectural
reasoning**, with a `Resolves:`/`See-also:` footer. Read that file now for the
exact shape and worked examples.

The bracketed `[TICKET-KEY]` is always the **current work item** — the ticket
this branch exists to deliver, derived in Step 1 from the branch name. When the
change references *another* ticket (most often a revert: "revert the TICK-000
sync"), that other key belongs in the body ("this reverts the work from
TICK-000"), not in the header. Don't let the reverted ticket displace the
current one. If the branch genuinely carries no key of its own and the only
ticket in play is the one being reverted, say so and confirm with the user
rather than silently tagging the header with the reverted key.

## Step 5 — Build the PR title and body

**Title:** `type(scope): subject [TICKET-KEY]` — same shape as the lead commit,
matching the user's squash-merged history (e.g.
`fix(identity): correct 401/403 misuse on identity endpoints [TICK-000]`).

**Body:** start from the repo's template (see selection rules below), then fill
every prose section from the diff + Linear context and tick the checklist items
you can verify:

- Pick the template per repo: prefer `.github/pull_request_template/default.md`
  if present, else `.github/pull_request_template.md`. For a **revert-only**
  change in `services`, use `.github/pull_request_template/revert.md`.
- Fill *What is the problem?* / *How this PR solves the problem?* / *How to
  test?* with real content. Replace italic placeholder prose; don't leave the
  template's `_describe..._` hints in.
- Check boxes only when true: tests present in the diff → tick the tests box;
  a feature toggle string appears → tick it and fill `TOGGLE_NAME_HERE`; no
  removed/renamed API field → tick "no breaking change". If you can't verify an
  item, leave it unchecked and add a one-line "didn't check X because…" under
  the checklist, which the template explicitly invites.
- For `apps` PRs, leave the Figma/Loom lines present but empty unless the user
  provided links — they fill those manually.

## Step 6 — Present the plan and STOP [ONLY IF ASKED BY THE USER}

If asked by the user, show the user, per repo:
 
1. The branch (and whether you'll create it).
2. Each planned commit message (header + body).
3. The PR title and the fully rendered PR body.

Then ask for approval to push and open. Do not run `git push` or
`gh pr create` until they say go. This is the second gate, after the review stop
in Step 3; honor it.

If not asked, consider the push and open approved.

## Step 7 — Execute

On approval, for each repo in scope:

```bash
# create branch only if needed
git -C <path> switch -c feature/<ticket-lowercased>   # skip if already on it
# stage + commit each planned group
git -C <path> add <paths-for-this-commit>
git -C <path> commit -m "<header>" -m "<body>"
# push and open
git -C <path> push -u origin <branch>
gh pr create --repo <slug> --base <default_branch> \
  --title "<title>" --body-file <tmp-body-file>
```

Notes that save grief:

- Write the PR body to a temp file and use `--body-file`; inline `--body` mangles
  multi-line markdown and checklists.
- **If a PR already exists** for the branch (`gh pr view --repo <slug>` succeeds),
  don't create a second one — push the new commits and, if the user asked to fix
  the description, update it with `gh pr edit --body-file`.
- Open **ready for review** (no `--draft`) unless the user asked for a draft.
- After each PR, report the URL. End with a one-line summary listing every PR
  opened so the user has the links together.

## Guardrails

- `partners/` changes must pass `validate_config.py` + `validate.sh` locally
  before you commit — run them and abort the commit if they fail.
- Never `git add -A` blindly across a repo you don't understand; stage the paths
  that belong to each commit so the granular split is real.
- If tests or lint are obviously broken in the diff, surface that in the plan —
  shipping is the user's call, but they should see it before approving.
