# Phase 5 — Plating

Get the change ready to hand off for review.

## 1. Self-review the diff

Read through the full diff against the base branch: code quality and
consistency with the codebase's own patterns, leftover debug code or TODOs,
error handling, anything worth documenting inline. Fix small things now
rather than carrying them into review.

## 2. Check the PR size

Measure files changed and lines changed against the base branch. If it's
within roughly 500 lines and 10 files, continue. If it's over:

- If the `## PR Delivery Strategy` from Cooking already accounts for this
  as one chunk of a larger plan, proceed — the size was already accepted
  when that strategy was confirmed.
- Otherwise, propose split points from the diff and ask the user whether to
  split, record a justification and proceed as one PR anyway, or continue
  as-is. Record whichever the user picks in the PR description under a
  size-exception note.

## 3. Draft the description

Use the `pr-description` skill (Skill tool) if it's available in this session to generate a draft
from the diff, the commits, and whatever the task came from, then round it
out with the acceptance criteria and testing steps from the recipe card.
Otherwise draft it manually from the recipe card: what changed and why, the
acceptance criteria it satisfies, how to test it, links back to wherever the
task lives. Get the user's approval before opening anything.

## 4. Open the PR

Open the pull request with the approved title and description. If Phase 4
deferred any verification to CI, open it as a draft so the full suite runs
there.

## 5. Wait for CI

This is a hard gate — the PR isn't ready for review until CI is green.
Monitor the checks; if any fail, diagnose, propose a fix, apply it once
approved, push, and re-monitor. Repeat until everything's green. Once it is,
promote a draft PR to ready.

## 6. Get it in front of reviewers

Record the PR link wherever the task's source lives, if it has one, marking
the task as in review. Then get the PR in front of the right reviewers
however this team normally does that — if a tool already in this session
handles that (an owners-based routing skill, a review-request command,
whatever), use it; otherwise ask the user who should review it.

## 7. Close the phase

Write the PR link and delivery notes to `## PR`. Append one line to
`## Decisions`. Update the frontmatter — `phase: 'plating'`, append to
`phasesCompleted`, `status: 'pr-created'`, `prUrl`, `lastTouched`.

## 8. Phase done

> **Phase done. [N] New session (recommended) — resume next phase fresh. [C] Continue here.**

**N:** confirm the card is saved, tell the user to resume with the same
trigger phrase in a new session. End the session.

**C:** load, read completely, and execute `phase-6-documentation.md`.
