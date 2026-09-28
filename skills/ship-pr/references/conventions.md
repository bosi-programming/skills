# Commit and PR conventions

Follow these as written; reviewers and the squash-merge history expect them.

## Commit header and PR title

The header takes the shape in `ship-pr.titleFormat`. The default is:

```
<type>(<scope>): <subject> [KEY]
```

The other common shape is `[KEY] <type>(<scope>): <subject>`. Use one shape for
every commit and title in a run.

- **type**: `feat`, `fix`, `chore`, `refactor`, `perf`, `ci`, `docs`, `test`,
  `build`, `style`, `revert`.
- **scope**: the domain area, lowercase, such as `billing`, `auth`, `search`.
- **subject**: imperative mood, no trailing period, concise.
- **KEY**: the ticket key in brackets, uppercase, such as `PROJ-123`.

Examples with the default format:

```
fix(auth): correct 401/403 misuse on session endpoints [PROJ-101]
feat(billing): sync invoice name on edits and emit an event [PROJ-204]
perf(search): index documents for lookup by owner [PROJ-318]
refactor(forms): show the full name before the short name
chore: remove unused config
```

## Commit body

Every commit gets a multi-line body that explains the context, the trade-offs
considered, and the reasoning. Do not restate the subject. Shape:

```
<type>(<scope>): <subject> [KEY]

Context: why this change is needed. The situation, bug or requirement,
grounded in the ticket. What was happening before.

Change: what this commit does at design level, not line by line. When commits
are split by stage, scope the body to this stage.

Trade-offs: alternatives considered and why this one won. Any follow-up debt
taken on knowingly, such as a flag that defaults off until a later change.

Resolves: <KEY>
See-also: <related files, PRs, or the sibling repo's PR>
```

Keep it honest, not padded. A trivial stage commit, such as a types-only change,
can have a two-line body.

The message goes to a file and is committed with `git commit -F <file>`.

## Branch naming

```
feature/<ticket-lowercased>
```

For example `feature/proj-21`. The detector reads the ticket key back out of the
branch name. Never commit onto the default branch.

## PR body checklist

Tick a box only when the diff proves it:

- **covered by tests**: the diff adds or updates test files. If not, leave it
  unchecked and say why under the checklist.
- **feature toggle**: the code reads a flag. Tick it and fill in the real flag
  name. If there is no flag, leave it unchecked.
- **no breaking change**: no API field or response shape was removed or
  renamed. If one was, leave it unchecked and note it.
- **deployable independently**: for multi-repo work, be truthful. If one PR
  needs the other merged first, say so here instead of ticking it.

When a template ends with a line such as "If you didn't check all those items,
explain why", use it. An unchecked box with a one-line reason is correct.

## Reverts

The header's `KEY` is the ticket for *this* revert work, taken from the branch,
such as `feature/proj-999` giving `[PROJ-999]`. The ticket being undone goes in
the body and in the template's "what is being reverted" section:

```
revert(billing): undo invoice name sync [PROJ-999]
```

with a body line "this reverts the work shipped under PROJ-204 (#231)". Run
`git revert <sha>` so the inverse diff is exact, then rewrite the generated
message into this shape. When the repo has `.github/pull_request_template/revert.md`,
use it instead of `default.md`.

## Several repos

Work that touches more than one repo produces one PR per repo, all sharing the
ticket key. Cross-link them: put the sibling PR's URL in each body's `See-also`
or in its "how to test" section, so reviewers find both halves.
