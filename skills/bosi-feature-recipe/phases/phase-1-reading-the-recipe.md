# Phase 1 — Reading the Recipe

Understand the task and the code it lands on before anything gets designed.

## 1. Load the task

Read whatever the recipe card's `task` field points at. If it names something
a tool already in this session can fetch (an issue tracker link, a document),
fetch it and present the real title, description, and any acceptance
criteria already stated. Otherwise take the user's description as given.

## 2. Visualize the code as it stands today

The `code-visualizer` skill draws a diff, and there's no diff yet on a fresh task —
so point it at a stand-in: a recent commit range scoped to the paths the task
will likely touch (find them by searching the codebase for the area the task
describes, then take the last handful of commits that touched them).

Skip this and say why when the task is a genuinely new module or file with
no existing code to show the shape of — don't invoke the skill and lean on
its own empty-diff fallback.

## 3. Close every gap with `grill-me` secondary skill

Check what the loaded task already states before seeding anything — a
ticket that already gives a stated benefit, scope, or acceptance criteria
has answered that dimension; don't reopen it from scratch. Seed the design
tree with only the dimensions still open, drawn from the standard
completeness set for a task like this one: the problem it solves, who
benefits and how, what's in and out of scope, testable acceptance criteria,
edge cases and error scenarios, and any external dependencies. Invoke the
`grill-me` secondary skill that is on `../dependencies/grill-me.md` against
that tree until its frontier is empty — this replaces asking one or two
clarifying questions at a time; the round-based frontier questioning gets to
the same place faster and more completely.

## 4. Write the Problem section

Once the design tree is settled, write the `## Problem` section of the
recipe card: the problem statement, the acceptance criteria, edge cases, and
dependencies — whichever the task already stated outright, plus whatever the
grilling settled for the rest. Nothing that answered a dimension gets
dropped just because it didn't come from a question.

If the task came from a tracker with validated, agreed content, record that
validated version back there too — as an outcome ("update the ticket with
what we settled on"), not by naming a specific tool; use whatever's already
available in this session for that tracker.

Append one line to `## Decisions`: what was settled and why. Update the
frontmatter — `phase: 'reading-the-recipe'`, append to `phasesCompleted`,
`lastTouched`.

## 5. Phase done

> **Phase done. [C] Continue here (recommended) — straight into Mise en Place; both phases are still pre-code. [N] New session — resume next phase fresh.**

**N:** confirm the card is saved, tell the user to resume with the same
trigger phrase in a new session — Phase 0 will pick up here. End the session.

**C:** load, read completely, and execute `phase-2-mise-en-place.md`.

## Headless

Read `../references/headless.md`. In a headless run:

- Set `runNext: phase-1-reading-the-recipe.md` as you start, so a run that
  dies here can be picked up from the card.
- Section 3's grilling still builds the design tree, but takes the
  recommended answer at each frontier question instead of asking and
  waiting — there's nobody to answer. Log the settled tree to
  `## Decisions` prefixed `unattended:`, one line per dimension rather than
  one per question.
- Sections 1, 2 and 4 are unchanged: load the task, visualize the code,
  write `## Problem` from the tree's settled answers, record back to the
  tracker if one is available.
- Section 5 does not apply. This phase does not stop at its own boundary: it
  loads, reads completely and executes `phase-2-mise-en-place.md`, and the
  run continues through Mise en Place and on into Cooking, Tasting, Plating
  and Documentation. A run stops at the recipe's end or at a one-way door,
  never at a phase boundary.

### Ending a run

Only if this phase is where the run stops — a frontier question with no
reasonable default, such as conflicting requirements in the source ticket
or a fact no tool in this session can find:

1. Set `runStatus: blocked` and `runQuestion` to the id of the entry you
   wrote in `## Open Questions`. Leave `runNext` as this phase: that is what
   a resume re-runs.
2. Log the stop to `## Decisions`.
