# Acme commit & PR conventions

Derived from the user's own merged PRs and global CLAUDE.md rules. Follow these
verbatim — they're what reviewers and the squash-merge history expect.

## Commit / PR title format

```
[TICKET-KEY] <type>(<scope>): <subject>
```

- **type**: `feat`, `fix`, `chore`, `refactor`, `perf`, `ci`, `docs`, `test`,
  `build`, `style`, `revert`.
- **scope**: the domain area, lowercase — `checkout-flow`, `form-builder`,
  `identity`, `authorization`, `fraud-check`, `migrations`, etc.
- **subject**: imperative mood, no trailing period, concise.
- **[TICKET-KEY]**: bracketed at the end, uppercase — `[TICK-000]`,
  `[TICK-000]`. Some historical commits use a `TICKET-123:` prefix instead;
  prefer the bracketed-suffix form for new work.

Real examples from history:

```
[TICK-000] fix(identity): correct 401/403 misuse on identity endpoints 
[TICK-000] feat(checkout-flow): sync BusinessProfile.businessName on BAO edits + Datadog event 
[TICK-000] perf(checkout-flow): index DisclosureConsents for findLatestTCPAByCustomerId 
refactor(form-builder): show entity full name before name on trust/estate forms
chore: remove opencode config
```

## Commit body (verbose — required)

The global rule asks for a detailed, multi-line body on every commit explaining
the *context*, the *trade-offs considered*, and the *architectural reasoning*.
Don't just restate the subject. Shape:

```
[TICKET-KEY] <type>(<scope>): <subject> 

Context: why this change is needed — the situation/bug/requirement, grounded in
the ticket. What was happening before.

Change: what this commit does at a design level (not a line-by-line restatement
of the diff). If you split commits by stage, scope the body to this stage.

Trade-offs: alternatives considered and why this approach won. Any follow-up
debt knowingly taken on (e.g. "flag defaults off; flip to default after the
form template is updated — see ticket").

Resolves: <TICKET-KEY>
See-also: <related files, PRs, or sibling repo PR>
```

Keep it honest and useful, not padded. If a stage commit is trivial (a types-only
change), a two-line body is fine — the point is reasoning, not word count.

## Branch naming

```
feature/<ticket-lowercased>
```

e.g. `feature/TICK-000`, `feature/TICK-000`. The detector derives the ticket
key back out of this. Never commit onto `main`/`master`.

## PR body checklist semantics

Tick a box only when you've verified it from the diff:

- **covered by tests** — tick if the diff adds/updates `*.spec.ts`,
  `*.int-spec.ts`, `*.e2e-spec.ts`, or frontend tests. If not, leave unticked
  and explain under the checklist.
- **feature toggle** — if the code reads a ConfigCat flag, tick and replace
  `TOGGLE_NAME_HERE` with the real flag name. If there's genuinely no flag,
  leave unticked.
- **no breaking change** — tick only if no API field/response shape was removed
  or renamed. A removed/renamed field means leave it unticked and note it.
- **deployable independently** — for multi-repo tickets, be truthful: if the
  frontend PR needs the backend PR merged first, say so here rather than ticking
  it.

The templates end with "If you didn't check all those items, explain why:" —
use that line; an unchecked box with a one-line reason is correct and expected,
not a failure.

## Reverts

The header's `[TICKET-KEY]` is the ticket for *this* revert work (from the
branch, e.g. a `feature/TICK-000` revert branch → `[TICK-000]`). The ticket
being undone is named in the body and the "What is being reverted?" section, not
the header — e.g. `revert(checkout-flow): undo business-name sync [TICK-000]`
with a body line "this reverts the work shipped under TICK-000 (#23871)". Use
`git revert <sha>` so the inverse diff is exact, then rewrite the auto-generated
message into this shape. In `services`, a revert uses `revert.md`, not
`default.md`.

## Multi-repo tickets

A ticket touching both `apps` and `services` produces two PRs sharing the ticket
key. Cross-link them: put the sibling PR URL in each PR body's `See-also` or in
the "how to test" section so reviewers can find both halves.
