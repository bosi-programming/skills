# Phase 4 — Tasting

Verify before anything leaves the kitchen. This is a hard gate: no PR gets
opened in Phase 5 until everything here passes.

## 1. Run the review

Invoke the `bosi-code-review` skill (Skill tool) against the change, then
triage its findings by axis without waiting for the user:

- **Standards** — bosi-code-review already separates hard violations
  (documented-standard breaches) from judgement calls (baseline-smell
  heuristics). Fix the hard violations; log judgement calls to
  `## Quality Gate Results` rather than acting on them.
- **Spec** — fix "missing requirement" and "implemented but wrong" findings
  autonomously. Never auto-remove code for a "scope creep" finding —
  deleting work that was deliberately written is a one-way door; log those
  to `## Quality Gate Results` for the user instead.

## 2. Detect this project's own checks

Don't assume a specific test runner, linter, or scoping convention — read
what this repo actually has: `package.json` scripts, CI workflow files, any
project-specific "test changed files" or "lint changed files" target. Use
whatever the project already provides for scoping to what changed, rather
than running its full suite from a standing start.

## 3. Determine what changed

List the changed files against the base branch. Filter to source and test
files — everything cooked so far; the PR-chunking decision hasn't been made
yet at this point (Plating decides it in the next phase).

## 4. Run tests scoped to the change

Use the project's own scoped-test mechanism if it has one. If it doesn't,
and there's no reasonable way to scope locally (no per-file test runner, a
type system that needs full-project context, etc.), don't fall back to
running the whole suite from here — say plainly that full verification for
this piece will happen once a PR opens and CI runs it, and note that in
`## Quality Gate Results` rather than pretending it ran locally.

## 5. Run lint and type-check scoped to the change

Same rule: scoped to the changed files where the project supports that,
deferred to CI and noted as such where it doesn't. Never fall back to a
full-project lint or type-check run — that's what freezes machines.

## 6. Fix and retry

For every failure: diagnose it, propose a fix, get it applied, re-run just
that check. Once everything's been touched, re-run the whole set from
section 4 again. Loop until every check that could run locally passes, or
is honestly marked deferred to CI.

## 7. Close the phase

Write the results — what passed, what's deferred to CI and why — to
`## Quality Gate Results`. Append one line to `## Decisions`. Update the
frontmatter — `phase: 'tasting'`, append to `phasesCompleted`, `lastTouched`.

## 8. Phase done

This menu only appears once every local check passes or is honestly marked
deferred — not before.

> **Phase done. [N] New session (recommended) — resume next phase fresh. [C] Continue here.**

**N:** confirm the card is saved, tell the user to resume with the same
trigger phrase in a new session. End the session.

**C:** load, read completely, and execute `phase-5-plating.md`.
#### EXECUTION RULES:

- ALWAYS halt and wait for user input after presenting menu
- Present the recommendation clearly but respect the user's choice

#### Menu Handling Logic:

- IF N: "**Great choice.** Your progress is saved. When you're ready, start this workflow again — it will detect your tech spec and pick up at implementation. See you in the next session!"
  - End the workflow session gracefully. Do NOT load the next step.
- IF C: "**Understood.** Let's continue with implementation in this session."
  - Load, read entire file, then execute {nextStepFile}
- IF Any other comments or queries: help user respond then [Redisplay Menu Options](#3-present-menu-options)

## CRITICAL STEP COMPLETION NOTE

IF user selects N: The workflow ends here. State is saved. User will resume where the current ticket stoped.
