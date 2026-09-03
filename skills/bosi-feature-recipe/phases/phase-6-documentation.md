# Phase 6 — Documentation

The last phase. This one is terminal — it ends the recipe, not with a
session-break menu but with a plain close.

## 1. Ask if this needs documenting

Ask the user whether this feature is worth documenting for the team, and
respect a no — this step is optional. If yes, work out where this team
already keeps docs: notice it from the project's own conventions (a `docs/`
folder, a documented convention in a README or CONTRIBUTING file) if it's
evident, or ask if it isn't. Don't assume any particular destination and
don't force a choice between named systems — wherever this team's docs
already live is the right place.

## 2. Draft it there

Draft documentation covering what the feature does, how it works, and how
to use it, pulled from the recipe card's Problem and Solution sections plus
the PR link. Get the user's approval, then write it to wherever step 1
settled on.

## 3. Close out

Update the frontmatter — `phase: 'documentation'`, append to
`phasesCompleted`, `status: 'delivered'`, `lastTouched`. Append a final line
to `## Decisions`.

If the task came from a tracker, record there that it's done.

Present a short delivery summary: what was built, the PR link, where the
docs landed (if any), and the recipe card's own path as the full record of
how it got there.

Tell the user the recipe is done. Don't offer a New session / Continue menu —
there's no next phase to route to.
