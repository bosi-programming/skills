# Phase 5 — Plating

Get the change ready to hand off for review. This phase opens **at most one
PR per run**, in line with the standing rule to never stack PRs and to only
start the next after the previous one merges. A chunked delivery revisits
this phase multiple times — once per chunk.

## 1. Decide the PR delivery strategy

Only runs the first time this phase is entered for this card (`## PR
Delivery Strategy` is still empty) — otherwise skip to section 1a.

Measure the whole accumulated diff's size (files + lines changed) against
the base branch. If it's within roughly 500 lines and 10 files, record that
it's a single PR and move to section 2.

Otherwise, propose split points from the diff, grouping into PR-sized
chunks at or under that size, each with a single clear purpose, each
independently reviewable. Present the chunks, get the user's confirmation or
adjust and re-present, then write the confirmed chunks to
`## PR Delivery Strategy`, every chunk starting `pending`.

If splitting genuinely isn't feasible — an atomic migration, an indivisible
refactor — ask the user to say why, record that justification in
`## PR Delivery Strategy`, and proceed as a single PR anyway.

## 1a. Pick up the next chunk

Only runs when `## PR Delivery Strategy` already lists chunks from a prior
run of this phase.

Find the most recent chunk marked `opened` and check whether its PR has
merged. If it hasn't, say so and stop — there's nothing to do until it does.
If it has, mark it `merged`, then move to section 2 scoped to the next
`pending` chunk only — branched from the now-updated base branch, not
stacked on the merged one.

## 2. Self-review the diff

Read through the diff for the active chunk (or the whole diff, for an
unsplit delivery) against the base branch: code quality and consistency with
the codebase's own patterns, leftover debug code or TODOs, error handling,
anything worth documenting inline. Fix small things now rather than carrying
them into review.

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
there. If this is a chunked delivery, mark the active chunk `opened` in
`## PR Delivery Strategy`.

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

Append the PR link and delivery notes for this run's chunk to `## PR` —
append, don't overwrite; a chunked delivery accumulates one entry per chunk
across multiple runs of this phase. Append one line to `## Decisions`.
Update the frontmatter — `phase: 'plating'`, append to `phasesCompleted`,
`status: 'pr-created'`, `prUrl` (the latest chunk's, or the only PR's),
`lastTouched`.

## 8. Phase done

If `## PR Delivery Strategy` still has a `pending` chunk, there's nothing
further to do in this session — the next chunk can't open until this one
merges. Tell the user that, and end here regardless of what they'd normally
pick; resuming later (same trigger phrase, new session) will pick up the
next chunk automatically via Phase 0.

Otherwise, every chunk (or the single PR) is open — show the usual menu:

> **Phase done. [N] New session (recommended) — resume next phase fresh. [C] Continue here.**

**N:** confirm the card is saved, tell the user to resume with the same
trigger phrase in a new session. End the session.

**C:** load, read completely, and execute `phase-6-documentation.md`.
